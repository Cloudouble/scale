env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['system_root']):] if p.startswith(env['system_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def process_entity(key_obj, bucket, lambda_client, entity_type):
    entity_path = getpath(key_obj['Key'])
    class_name, entity_id, connection_id = entity_path[1:]
    lambda_client.invoke(FunctionName='{lambda_namespace}-core-mask'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps({
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
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for record_event in event['Records']:
        path = getpath(record_event['s3']['object']['key'])
        if len(path) == 6:
            connection_id, entity_type, class_name, query_id, index = path[1:]
            feed_path = '{system_root}/feed/{class_name}/{query_id}/{connection_id}.json'.format(system_root=env['system_root'], class_name=class_name, query_id=query_id, connection_id=connection_id)
            try:
                feed_data = json.loads(bucket.get_object(Key=feed_path)['Body'].read().decode('utf-8'))
            except:
                feed_data = {}
            for view_configuration in feed_data.get('view', []):
                lambda_client.invoke(FunctionName='{lambda_namespace}-core-view'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps({
                    'connection_id': connection_id,
                    'class_name': class_name, 
                    'entity_type': 'query', 
                    'query_id': query_id, 
                    'view_configuration': view_configuration
                }), 'utf-8'))
            counter = counter + 1
    return counter
