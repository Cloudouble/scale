import json, boto3, os

def process_entity(key_obj, bucket, lambda_client, entity_type):
    entity_path = key_obj['Key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
    class_name, entity_id, connection_id = entity_path[1:]
    lambda_client.invoke(FunctionName='mask', InvocationType='Event', Payload=bytes(json.dumps({
        'connection_id': connection_id,
        'class_name': class_name, 
        'entity_type': entity_type, 
        'entity_id': entity_id
    }), 'utf-8'))

def main(event, context):
    '''
    - triggered by new/updated/deleted /connection/{connection_id}/query/{class_name}/{query_id}/{index_initial}.json
    - uses /feed/{class_name}/{query_id}/{connection_id}.json to find affected views for this connection and query
    - trigger view.py for each affected feed view
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for record in event['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        if len(path) == 6:
            connection_id, entity_type, class_name, query_id, index = path[1:]
            feed_path = '_/feed/{class_name}/{query_id}/{connection_id}.json'.format(class_name=class_name, query_id=query_id, connection_id=connection_id)
            try:
                feed_data = json.loads(bucket.get_object(Key=feed_path)['Body'].read().decode('utf-8'))
            except:
                feed_data = {}
            for view_configuration in feed_data.get('view', []):
                lambda_client.invoke(FunctionName='view', InvocationType='Event', Payload=bytes(json.dumps({
                    'connection_id': connection_id,
                    'class_name': class_name, 
                    'entity_type': 'query', 
                    'query_id': query_id, 
                    'view_configuration': view_configuration
                }), 'utf-8'))
            counter = counter + 1
    return counter
