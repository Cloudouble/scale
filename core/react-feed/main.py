import json, boto3, base64

def getpath(p, env=None):
    p = p.strip('/?')
    if env and env.get('data_root'):
        p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def build_env(record_event, context):
    temp_path = getpath(record_event['s3']['object']['key'])
    if len(temp_path) in [6, 7]:
        shared = len(temp_path) == 7
        return {
            'bucket': record_event['s3']['bucket']['name'], 
            'lambda_namespace': context.function_name.replace('-core-react-feed', ''), 
            'system_root': temp_path[-6],
            'data_root': '{}/{}'.format(temp_path[-7], temp_path[-6]) if shared else temp_path[-6], 
            'shared': 1 if shared else 0
        }
    else:
        return {}


def main(event, context):
    '''
    - triggered by writes at /feed/{class_name}/{query_id}/{connection_id}/*
    - trigger view for each view configuration in feed->view
    '''
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for event_entry in event['Records']:
        env = build_env(event_entry, context)
        if not env:
            continue
        env['path'] = getpath(event_entry['s3']['object']['key'], env)
        client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
        class_name, query_id, connection_id = env['path'][1:4]
        view = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event_entry['s3']['object']['key'])['Body'].read().decode('utf-8'))
        lambda_client.invoke(FunctionName='{lambda_namespace}-core-view'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps({
            'connection_id': connection_id,
            'class_name': class_name, 
            'entity_type': 'query', 
            'entity_id': query_id, 
            'view': view
        }), 'utf-8'))
        counter = counter + 1
    return counter