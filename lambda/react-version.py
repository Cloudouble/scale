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
    - triggered by new objects at /version/{class_name}/{record_id}/{version_id}.json
    - uses /vector/{class_name}/{field_name}.json to find affected queries 
    - triggers query-record.py with the full record for each affected query
    - uses /subscription/{class_name}/{record_id}/{connection_id}.json to find affected connections
    - triggers mask.py for each affected connection
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for record in event['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        if len(path) == 4:
            class_name, record_id, record_version = path[1:]
            updated_fields = sorted(json.loads(bucket.get_object(Key=record['s3']['object']['key'])['Body'].read().decode('utf-8')))
            query_list = []
            for field_name in updated_fields:
                try:
                    query_list.entend(json.loads(bucket.get_object(Key='_/vector/{class_name}/{field_name}.json'.format(class_name=class_name, field_name=field_name))['Body'].read().decode('utf-8')))
                except:
                    pass
            query_list = sorted(list(set(query_list)))
            for query_id in query_list:
                lambda_client.invoke(FunctionName='query-record', InvocationType='Event', Payload=bytes(json.dumps({'query': query_id, 'record': {'@type': class_name, '@id': record_id}}), 'utf-8'))
            subscription_list_key = '_/subscription/{class_name}/{record_id}/'.format(class_name=class_name, record_id=record_id)
            subscription_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=subscription_list_key)
            for key_obj in subscription_list_response['Contents']:
                process_entity(key_obj, bucket, lambda_client, 'record')
            c = 1000000000
            while c and subscription_list_response.get('IsTruncated') and subscription_list_response.get('NextContinuationToken'):
                subscription_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=subscription_list_key, ContinuationToken=subscription_list_response.get('NextContinuationToken'))
                for key_obj in subscription_list_response['Contents']:
                    process_entity(key_obj, bucket, lambda_client, 'record')
                    c = c - 1
            counter = counter + 1
    return counter
