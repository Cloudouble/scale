import json, boto3, base64

def getpath(p, env=None):
    p = p.strip('/?')
    if env and env.get('data_root'):
        p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def build_env(entry, context):
    # host/_/connection/{connection_id}.json
    temp_path = getpath(entry['s3']['object']['key'])
    if len(temp_path) in [3, 4]:
        shared = len(temp_path) == 4
        return {
            'bucket': entry['s3']['bucket']['name'], 
            'lambda_namespace': context.function_name.replace('-core-react-connection-record', ''), 
            'system_root': temp_path[-3],
            'data_root': '{}/{}'.format(temp_path[-4], temp_path[-3]) if shared else temp_path[-3], 
            'shared': 1 if shared else 0
        }
    else:
        return {}


def main(event_data, context):
    '''
    - triggered by writes at _/connection/{connection_id}.json
    - deletes all objects under _/connection/{connection_id}/*
    '''
    s3 = boto3.resource('s3')
    counter = 0
    for entry in event_data['Records']:
        env = build_env(entry, context)
        if not env:
            continue
        env['path'] = getpath(entry['s3']['object']['key'], env)
        client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
        if env['path'] and len(env['path']) == 2 and env['path'][0] == 'connection':
            connection_id = env['path'][1]
            s3_client = boto3.client('s3')
            list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix='{system_root}/connection/{connection_id}/'.format(system_root=env['system_root'], connection_id=connection_id))
            delete_response = s3_client.delete_objects(Bucket=env['bucket'], Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents']], 'Quiet': True})
            c = 1000
            while c and list_response.get('IsTruncated') and list_response.get('NextContinuationToken'):
                list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix='{system_root}/connection/{connection_id}/'.format(system_root=env['system_root'], connection_id=connection_id), ContinuationToken=list_response.get('NextContinuationToken'))
                delete_response = s3_client.delete_objects(Bucket=env['bucket'], Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents']], 'Quiet': True})
                c = c - 1
            counter = counter + 1
    return counter