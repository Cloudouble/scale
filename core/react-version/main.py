import json, boto3

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def process_record(key_obj, bucket, lambda_client, record):
    entity_path = getpath(key_obj['Key'])
    class_name, record_id, connection_id = entity_path[1:4]
    mask_payload = {
        'connection_id': connection_id,
        'entity_type': 'record', 
        'method': 'GET', 
        'class_name': class_name,
        'entity_id': record_id, 
        'entity': record, 
        'write': True
    }
    lambda_client.invoke(FunctionName='{lambda_namespace}-core-mask'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps(mask_payload), 'utf-8'), ClientContext=client_context)

def main(event, context):
    '''
    - triggered by new objects at /version/{class_name}/{record_id}/{version_id}.json
    - uses /vector/{class_name}/{field_name}.json to find affected queries 
    - triggers query with the full record for each affected query
    - lists /subscription/{class_name}/{record_id}/* to find affected connections
    - triggers mask for each affected connection
    '''
    env = context.client_context.env
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8'))
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for record_event in event['Records']:
        path = getpath(record_event['s3']['object']['key'])
        if len(path) == 4:
            class_name, record_id, record_version = path[1:]
            updated_fields = sorted(json.loads(s3_client.get_object(Bucket=env['bucket'], Key=record_event['s3']['object']['key'])['Body'].read().decode('utf-8')))
            query_list = []
            for field_name in updated_fields:
                try:
                    query_list.extend(json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/vector/{class_name}/{field_name}.json'.format(data_root=env['data_root'], class_name=class_name, field_name=field_name))['Body'].read().decode('utf-8')))
                except:
                    pass
            query_list = sorted(list(set(query_list)))
            for query_id in query_list:
                lambda_client.invoke(FunctionName='{lambda_namespace}-core-query'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps({'query': query_id, 'record': {'@type': class_name, '@id': record_id}}), 'utf-8'), ClientContext=client_context)
            subscription_list_key = '{data_root}/subscription/{class_name}/{record_id}/'.format(data_root=env['data_root'], class_name=class_name, record_id=record_id)
            subscription_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=subscription_list_key)
            if subscription_list_response.get('Contents', []):
                record_data = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/record/{class_name}/{record_id}.json'.format(data_root=env['data_root'], class_name=class_name, record_id=record_id))['Body'].read().decode('utf-8'))
            else:
                record_data = {}
            if record_data:
                for key_obj in subscription_list_response.get('Contents', []):
                    process_record(key_obj, bucket, lambda_client, record_data)
                c = 1000000000
                while c and subscription_list_response.get('IsTruncated') and subscription_list_response.get('NextContinuationToken'):
                    subscription_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=subscription_list_key, ContinuationToken=subscription_list_response.get('NextContinuationToken'))
                    for key_obj in subscription_list_response.get('Contents', []):
                        process_record(key_obj, bucket, lambda_client, record_data)
                        c = c - 1
            counter = counter + 1
    return counter
