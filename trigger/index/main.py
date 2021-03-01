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
    - triggered by new/updated objects at /query/{class_name}/{query_id}/{record_initial}.json
    - uses /feed/{class_name}/{query_id}/{connection_id}/* to find affected connections
    - triggers index.py for each affected connection
    '''
    counter = 0
    if event.get('key'):
        s3 = boto3.resource('s3')
        s3_client = boto3.client('s3')
        lambda_client = boto3.client('lambda')
        env, client_context = get_env_context(event, context)    
        index_record_ids = set(json.loads(s3_client.get_object(Bucket=env['bucket'], Key=record_event['s3']['object']['key'])['Body'].read().decode('utf-8')))
        affected_connections = set()
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
                lambda_client.invoke(FunctionName=getprocessor(env, 'index'), InvocationType='Event', 
                    Payload=bytes(json.dumps({'class_name': class_name, 'query_id': query_id, 'index': index, '_env': {**env, 'connection_id': affected_connection}}), 'utf-8'))
            counter = counter + 1
    return counter
