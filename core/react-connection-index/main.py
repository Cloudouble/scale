import json, boto3, base64

def getpath(p, env=None):
    p = p.strip('/?')
    if env and env.get('data_root'):
        p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def build_env(entry, context):
    temp_path = getpath(entry['s3']['object']['key'])
    if len(temp_path) in [6, 7]:
        shared = len(temp_path) == 7
        return {
            'bucket': entry['s3']['bucket']['name'], 
            'lambda_namespace': context.function_name.replace('-core-react-connection-record', ''), 
            'system_root': temp_path[-6],
            'data_root': '{}/{}'.format(temp_path[-7], temp_path[-6]) if shared else temp_path[-6], 
            'shared': 1 if shared else 0
        }
    else:
        return {}


def main(event, context):
    '''
    - triggered by new/updated/deleted /connection/{connection_id}/query/{class_name}/{query_id}/{index_initial}.json
    - use /feed/{class_name}/{query_id}/{connection_id}/* to find affected views for this connection and query
    - trigger view for each affected feed view
    '''
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for entry in event['Records']:
        env = build_env(entry, context)
        if not env:
            continue
        env['path'] = getpath(entry['s3']['object']['key'], env)
        client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
        if len(env['path']) == 6:
            connection_id, entity_type, class_name, query_id, index = env['path'][1:]
            connection_feed_list_path = '{system_root}/feed/{class_name}/{query_id}/{connection_id}/'.format(system_root=env['system_root'], class_name=class_name, query_id=query_id, connection_id=connection_id)
            connection_feed_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=connection_feed_list_path)
            for key_obj in connection_feed_list_response.get('Contents', []):
                try:
                    view = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=key_obj['Key'])['Body'].read().decode('utf-8'))
                except:
                    view = {}
                if view:
                    lambda_client.invoke(FunctionName='{lambda_namespace}-core-view'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps({
                        'class_name': class_name, 
                        'entity_type': 'query', 
                        'entity_id': query_id, 
                        'view': view, 
                        '_env': {**env, 'connection_id': connection_id}
                    }), 'utf-8'))
            counter = counter + 1

    return counter
