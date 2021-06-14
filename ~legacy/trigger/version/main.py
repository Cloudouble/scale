import json, boto3, base64

def getpath(p, env=None):
    p = p.strip('/?')
    if env and env.get('data_root'):
        p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def get_env_context(event, context):
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    env['path'] = getpath(event['key'], env)
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    return env, client_context

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)


def main(event, context):
    '''
    - triggered by new objects at _/version/{class_name}/{record_id}/{version_id}.json
    - uses _/vector/{class_name}/{field_name}.json to find affected queries 
    - triggers query with the full record for each affected query
    - lists _/subscription/{class_name}/{record_id}/* to find affected connections
    - triggers mask for each affected connection
    '''
    counter = 0
    if event.get('key'):
        s3_client = boto3.client('s3')
        lambda_client = boto3.client('lambda')
        env, client_context = get_env_context(event, context)    
        if len(env['path']) == 4:
            class_name, record_id, record_version = env['path'][1:]
            updated_fields = sorted(json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8')))
            query_list = []
            for field_name in updated_fields:
                try:
                    query_list.extend(json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/vector/{class_name}/{field_name}.json'.format(data_root=env['data_root'], class_name=class_name, field_name=field_name))['Body'].read().decode('utf-8')))
                except:
                    pass
            query_list = sorted(list(set(query_list)))
            for query_id in query_list:
                lambda_client.invoke(
                    FunctionName=getprocessor(env, 'query'), 
                    InvocationType='Event', 
                    Payload=bytes(json.dumps({'query_id': query_id, 'record': {'@type': class_name, '@id': record_id}, '_env':env}), 'utf-8')
                )
            subscription_list_key = '{data_root}/subscription/{class_name}/{record_id}/'.format(data_root=env['data_root'], class_name=class_name, record_id=record_id)
            subscription_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=subscription_list_key)
            if subscription_list_response.get('Contents', []):
                record_data = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/record/{class_name}/{record_id}.json'.format(data_root=env['data_root'], class_name=class_name, record_id=record_id))['Body'].read().decode('utf-8'))
            else:
                record_data = {}
            if record_data:
                process_connections = {}
                for key_obj in subscription_list_response.get('Contents', []):
                    subscription = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=key_obj['Key'])['Body'].read().decode('utf-8'))
                    process_connections[getpath(key_obj['Key'], env)[3]] = subscription.get('connection_type', 'connection')
                c = 1000000000
                while c and subscription_list_response.get('IsTruncated') and subscription_list_response.get('NextContinuationToken'):
                    subscription_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=subscription_list_key, ContinuationToken=subscription_list_response.get('NextContinuationToken'))
                    for key_obj in subscription_list_response.get('Contents', []):
                        subscription = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=key_obj['Key'])['Body'].read().decode('utf-8'))
                        process_connections[getpath(key_obj['Key'], env)[3]] = subscription.get('connection_type', 'connection')
                        c = c - 1
                for connection_id, connection_type in process_connections.items():
                    mask_payload = {
                        'entity_type': 'record', 
                        'method': 'GET', 
                        'class_name': class_name,
                        'entity_id': record_id, 
                        'entity': record_data, 
                        'write': True, 
                        '_env': {**env, 'connection_type': connection_type, 'connection_id': connection_id}
                    }
                    lambda_client.invoke(FunctionName=getprocessor(env, 'mask'), InvocationType='Event', Payload=bytes(json.dumps(mask_payload), 'utf-8'))
            counter = counter + 1
    return counter
