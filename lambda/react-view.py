import json, boto3, os

def process_entity(key_obj, bucket, lambda_client, entity_type):
    entity_path = key_obj['Key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
    class_name, entity_id, connection_id = entity_path[1:]
    entity_data = json.loads(bucket.get_object(Key=key_obj['Key'])['Body'].read().decode('utf-8'))
    for view_configuration in entity_data.get('view', []):
        lambda_client.invoke(FunctionName='view', InvocationType='Event', Payload=bytes(json.dumps({
            'connection_id': connection_id,
            'class_name': class_name, 
            '{}_id'.format(entity_type): entity_id, 
            'view_configuration': view_configuration
        }), 'utf-8'))
    

def main(event_data, context):
    '''
    - triggered by writes at /view/{view_id}.json
    - use /subscription/{class_name}/{record_id}/{connection_id}.json to get all affected connection subscriptions
    - trigger view.py for each view configuration in each affected subscription->view of each affected connection
    - use /feed/{class_name}/{query_id}/{connection_id}.json to get all affected connection feeds
    - trigger view.py for each view configuration in each affected feed->view of each affected connection
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for event in event_data['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        view_id = path[1]
        subscription_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/subscription/')
        for key_obj in subscription_list_response['Contents']:
            process_entity(key_obj, bucket, lambda_client, 'record')
        c = 1000000000
        while c and subscription_list_response.get('IsTruncated') and subscription_list_response.get('NextContinuationToken'):
            subscription_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/subscription/', ContinuationToken=subscription_list_response.get('NextContinuationToken'))
            for key_obj in subscription_list_response['Contents']:
                process_entity(key_obj, bucket, lambda_client, 'record')
                c = c - 1
        feed_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/feed/')
        for key_obj in feed_list_response['Contents']:
            process_entity(key_obj, bucket, lambda_client, 'feed')
        c = 1000000000
        while c and feed_list_response.get('IsTruncated') and feed_list_response.get('NextContinuationToken'):
            feed_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/feed/', ContinuationToken=feed_list_response.get('NextContinuationToken'))
            for key_obj in feed_list_response['Contents']:
                process_entity(key_obj, bucket, lambda_client, 'feed')
                c = c - 1
        counter = counter + 1
    return counter