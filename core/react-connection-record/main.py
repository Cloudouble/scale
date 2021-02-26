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

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 
def process_query(key_obj, index, s3_client, env, record_id):
    connection_query_path = getpath(key_obj['Key'])
    connection_id, entity_type, class_name, query_id = env['path'][1:]
    connection_query_index_path = '{system_root}/connection/{connection_id}/query/{class_name}/{query_id}/{index}.json'.format(system_root=env['system_root'], connection_id=connection_id, class_name=class_name, query_id=query_id, index=index)
    connection_query_index_data = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=connection_query_index_path)['Body'].read().decode('utf-8'))
    if record_id in connection_query_index_data:
        connection_query_index_data.remove(record_id)
        connection_query_index_data.sort()
        s3_client.put_object(Bucket=env['bucket'], Key=connection_query_index_path, Body=bytes(json.dumps(connection_query_index_data), 'utf-8'), ContentType='application/json')
    

def main(event, context):
    '''
    - triggered by new/updated/deleted objects in /connection/{connection_id}/record/{class_name}/{record_id}.json
    - removes the relevant record_id from /connection/{connection_id}/query/{class_name}/{query_id}/{index_initial}.json if the masked value is empty
    - uses /subscription/{class_name}/{record_id}/{connection_id}/* to find affected views for this connection and record
    - trigger view for each affected subscription view 
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
        if len(env['path']) == 5:
            connection_id, entity_type, class_name, record_id = env['path'][1:]
            index = record_id[0]
            try:
                masked_record_data = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=entry['s3']['object']['key'])['Body'].read().decode('utf-8'))
            except:
                masked_record_data = {}
            if not masked_record_data:
                connection_query_list_key = '{system_root}/connection/{connection_id}/query/{class_name}/'.format(system_root=env['system_root'], connection_id=connection_id, class_name=class_name)
                connection_query_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=connection_query_list_key)
                for key_obj in connection_query_list_response.get('Contents', []):
                    process_query(key_obj, index, s3_client, env, record_id)
                c = 1000000000
                while c and connection_query_list_response.get('IsTruncated') and connection_query_list_response.get('NextContinuationToken'):
                    connection_query_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=connection_query_list_key, ContinuationToken=connection_query_list_response.get('NextContinuationToken'))
                    for key_obj in connection_query_list_response.get('Contents', []):
                        process_query(key_obj, index, s3_client, env, record_id)
                        c = c - 1
            connection_subscription_list_path = '{system_root}/subscription/{class_name}/{record_id}/{connection_id}/'.format(system_root=env['system_root'], class_name=class_name, record_id=record_id, connection_id=connection_id)
            connection_subscription_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=connection_subscription_list_path)
            for key_obj in connection_subscription_list_response.get('Contents', []):
                try:
                    subscription_data = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=key_obj['Key'])['Body'].read().decode('utf-8'))
                except:
                    subscription_data = {}
                if subscription_data:
                    lambda_client.invoke(FunctionName=getprocessor(env, 'view'), InvocationType='Event', Payload=bytes(json.dumps({
                        'class_name': class_name, 
                        'entity_type': 'record', 
                        'entity_id': record_id, 
                        'view': subscription_data, 
                        '_env': {**env, 'connection_id': connection_id}
                    }), 'utf-8'))
            counter = counter + 1
    return counter
