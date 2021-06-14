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
    

def main(event, context):
    '''
    - triggered by writes at _/{connection_type}/{connection_id}/connect.json
    - deletes all objects under _/{connection_type}/{connection_id}/*
    '''
    counter = 0
    if event.get('key'):
        env, client_context = get_env_context(event, context)    
        s3_client = boto3.client('s3')
        if env['path'] and len(env['path']) == 3 and env['path'][0] in ['channel', 'connection', 'daemon']:
            connection_type, connection_id = env['path'][0:2]
            list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix='{data_root}/{connection_type}/{connection_id}/'.format(data_root=env['data_root'], connection_type=connection_type, connection_id=connection_id))
            delete_response = s3_client.delete_objects(Bucket=env['bucket'], Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents'] if c['Key'] != event['key']], 'Quiet': True})
            c = 1000
            while c and list_response.get('IsTruncated') and list_response.get('NextContinuationToken'):
                list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix='{data_root}/{connection_type}/{connection_id}/'.format(data_root=env['data_root'], connection_type=connection_type, connection_id=connection_id), ContinuationToken=list_response.get('NextContinuationToken'))
                delete_response = s3_client.delete_objects(Bucket=env['bucket'], Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents'] if c['Key'] != event['key']], 'Quiet': True})
                c = c - 1
            counter = counter + 1
    return counter