import json, boto3, base64

def getpath(p, env=None):
    p = p.strip('/?')
    if env and env.get('data_root'):
        p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def build_env(record_event, context):
    temp_path = getpath(record_event['s3']['object']['key'])
    if len(temp_path) in [5, 6]:
        shared = len(temp_path) == 6
        return {
            'bucket': record_event['s3']['bucket']['name'], 
            'lambda_namespace': context.function_name.replace('-core-react-version', ''), 
            'system_root': temp_path[-5],
            'data_root': '{}/{}'.format(temp_path[-6], temp_path[-5]) if shared else temp_path[-5], 
            'shared': 1 if shared else 0
        }
    else:
        return {}

def process_record(key_obj, lambda_client, record, env, client_context):
    entity_path = getpath(key_obj['Key'], env)
    class_name, record_id, connection_id = entity_path[1:4]
    mask_payload = {
        'entity_type': 'record', 
        'method': 'GET', 
        'class_name': class_name,
        'entity_id': record_id, 
        'entity': record, 
        'write': True
    }
    mask_payload['_env'] = {'connection_id': connection_id, **env}
    lambda_client.invoke(FunctionName='{lambda_namespace}-core-mask'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps(mask_payload), 'utf-8'))

def main(event, context):
    '''
    - triggered by new objects at /version/{class_name}/{record_id}/{version_id}.json
    - uses /vector/{class_name}/{field_name}.json to find affected queries 
    - triggers query with the full record for each affected query
    - lists /subscription/{class_name}/{record_id}/* to find affected connections
    - triggers mask for each affected connection
    '''
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for record_event in event['Records']:
        env = build_env(record_event, context)
        if not env:
            continue
        env['path'] = getpath(record_event['s3']['object']['key'], env)
        client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
        if len(env['path']) == 4:
            class_name, record_id, record_version = env['path'][1:]
            updated_fields = sorted(json.loads(s3_client.get_object(Bucket=env['bucket'], Key=record_event['s3']['object']['key'])['Body'].read().decode('utf-8')))
            query_list = []
            for field_name in updated_fields:
                try:
                    query_list.extend(json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/vector/{class_name}/{field_name}.json'.format(data_root=env['data_root'], class_name=class_name, field_name=field_name))['Body'].read().decode('utf-8')))
                except:
                    pass
            query_list = sorted(list(set(query_list)))
            for query_id in query_list:
                lambda_client.invoke(
                    FunctionName='{lambda_namespace}-core-query'.format(lambda_namespace=env['lambda_namespace']), 
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
                for key_obj in subscription_list_response.get('Contents', []):
                    process_record(key_obj, lambda_client, record_data, env, client_context)
                c = 1000000000
                while c and subscription_list_response.get('IsTruncated') and subscription_list_response.get('NextContinuationToken'):
                    subscription_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=subscription_list_key, ContinuationToken=subscription_list_response.get('NextContinuationToken'))
                    for key_obj in subscription_list_response.get('Contents', []):
                        process_record(key_obj, lambda_client, record_data, env, client_context)
                        c = c - 1
            counter = counter + 1
    return counter
