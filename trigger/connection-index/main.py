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
    - triggered by new/updated/deleted /connection/{connection_id}/query/{class_name}/{query_id}/{index_initial}.json
    - use /feed/{class_name}/{query_id}/{connection_id}/* to find affected views for this connection and query
    - trigger view for each affected feed view
    '''
    counter = 0
    if event.get('key'):
        s3 = boto3.resource('s3')
        s3_client = boto3.client('s3')
        lambda_client = boto3.client('lambda')
        env, client_context = get_env_context(event, context)    
        if len(env['path']) == 6:
            connection_id, entity_type, class_name, query_id, index = env['path'][1:]
            connection_feed_list_path = '{data_root}/feed/{class_name}/{query_id}/{connection_id}/'.format(data_root=env['data_root'], class_name=class_name, query_id=query_id, connection_id=connection_id)
            connection_feed_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=connection_feed_list_path)
            for key_obj in connection_feed_list_response.get('Contents', []):
                try:
                    view = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=key_obj['Key'])['Body'].read().decode('utf-8'))
                except:
                    view = {}
                if view:
                    lambda_client.invoke(FunctionName=getprocessor(env, 'view'), InvocationType='Event', Payload=bytes(json.dumps({
                        'class_name': class_name, 
                        'entity_type': 'query', 
                        'entity_id': query_id, 
                        'view': view, 
                        '_env': {**env, 'connection_id': connection_id}
                    }), 'utf-8'))
            counter = counter + 1
    return counter
