import json, boto3, base64, time

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
            'lambda_namespace': context.function_name.replace('-core-react-index', ''), 
            'system_root': temp_path[-5],
            'data_root': '{}/{}'.format(temp_path[-6], temp_path[-5]) if shared else temp_path[-5], 
            'shared': 1 if shared else 0
        }
    else:
        return {}


def main(event, context):
    '''
    - triggered by new/updated objects at /query/{class_name}/{query_id}/{record_initial}.json
    - uses /feed/{class_name}/{query_id}/{connection_id}/* to find affected connections
    - triggers index.py for each affected connection
    '''
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    affected_connections = set()
    for record_event in event['Records']:
        env = build_env(record_event, context)
        if not env:
            continue
        env['path'] = getpath(record_event['s3']['object']['key'], env)
        client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
        index_record_ids = set(json.loads(s3_client.get_object(Bucket=env['bucket'], Key=record_event['s3']['object']['key'])['Body'].read().decode('utf-8')))
        if len(env['path']) == 4:
            class_name, query_id, index = env['path'][1:]
            feed_base_key = '{data_root}/feed/{class_name}/{query_id}/'.format(data_root=env['data_root'], class_name=class_name, query_id=query_id)
            feed_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=feed_base_key)
            for feed_entry in feed_list_response.get('Contents', []):
                affected_connections.add(getpath(feed_entry['Key'])[-2])
            c = 1000000000
            while c and feed_list_response.get('IsTruncated') and feed_list_response.get('NextContinuationToken'):
                feed_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=feed_base_key, ContinuationToken=feed_list_response.get('NextContinuationToken'))
                for key_obj in feed_list_response.get('Contents', []):
                    affected_connections.add(getpath(feed_entry['Key'])[-2])
                    c = c - 1
            for affected_connection in affected_connections:
                lambda_client.invoke(FunctionName='{lambda_namespace}-core-index'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', 
                    Payload=bytes(json.dumps({'connection_id': affected_connection, 'class_name': class_name, 'query_id': query_id, 'index': index}), 'utf-8'), ClientContext=client_context)
            counter = counter + 1
    return counter
