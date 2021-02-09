import json, boto3, os

def process_entity(key_obj, bucket, lambda_client, entity_type):
    entity_path = key_obj['Key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
    class_name, entity_id, connection_id = entity_path[1:]
    lambda_client.invoke(FunctionName='mask', InvocationType='Event', Payload=bytes(json.dumps({
        'connection_id': connection_id,
        'class_name': class_name, 
        '{}_id'.format(entity_type): entity_id, 
    }), 'utf-8'))

def main(event, context):
    '''
    - triggered by new/updated/deleted objects in /connection/{connection_id}/record/{class_name}/{record_id}.json
    - removes the relevant record_id from /connection/{connection_id}/query/{class_name}/{query_id}/{index_initial}.json if the masked value is empty
    - uses /subscription/{class_name}/{record_id}/{connection_id}.json to find affected views for this connection and record
    - trigger view.py for each affected subscription view 
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for record in event['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        if len(path) == 5:
            connection_id, entity_type, class_name, record_id = path[1:]
            index = record_id[0]
            try:
                masked_record_data = json.loads(bucket.get_object(Key=event['s3']['object']['key'])['Body'].read().decode('utf-8'))
            except:
                masked_record_data = {}
            if not masked_record_data:
                connection_query_list_key = '_/connection/{connection_id}/query/{class_name}/'.format(connection_id=connection_id, class_name=class_name)
                connection_query_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=connection_query_list_key)
                for key_obj in connection_query_list_response['Contents']:
                    connection_query_path = key_obj['Key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
                    connection_id, entity_type, class_name, query_id = path[1:]
                    connection_query_index_path = '_/connection/{connection_id}/query/{class_name}/{query_id}/{index}.json'.format(connection_id=connection_id, class_name=class_name, query_id=query_id, index=index)
                    connection_query_index_data = json.loads(bucket.get_object(Key=connection_query_index_path)['Body'].read().decode('utf-8'))
                    if record_id in connection_query_index_data:
                        connection_query_index_data.remove(record_id).sort()
                        bucket.put_object(Key=connection_query_index_path, Body=bytes(json.dumps(connection_query_index_data), 'utf-8'), ContentType='application/json')
            subscription_path = '_/subscription/{class_name}/{record_id}/{connection_id}.json'.format(class_name=class_name, record_id=record_id, connection_id=connection_id)
            try:
                subscription_data = json.loads(bucket.get_object(Key=subscription_path)['Body'].read().decode('utf-8'))
            except:
                subscription_data = {}
            for view_configuration in subscription_data.get('view', []):
                lambda_client.invoke(FunctionName='view', InvocationType='Event', Payload=bytes(json.dumps({
                    'connection_id': connection_id,
                    'class_name': class_name, 
                    'record_id': record_id, 
                    'view_configuration': view_configuration
                }), 'utf-8'))
            counter = counter + 1
    return counter
