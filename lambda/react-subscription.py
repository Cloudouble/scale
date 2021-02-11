import json, boto3, os

def main(event_data, context):
    '''
    - triggered by writes at /subscription/{class_name}/{record_id}/{connection_id}.json
    - trigger view.py for each view configuration in subscription->view
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for event in event_data['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        class_name, record_id, connection_id = path[1:4]
        subscription_data = json.loads(bucket.get_object(Key=event['s3']['object']['key'])['Body'].read().decode('utf-8'))
        for view_configuration in subscription_data.get('view', []):
            lambda_client.invoke(FunctionName='view', InvocationType='Event', Payload=bytes(json.dumps({
                'connection_id': connection_id,
                'class_name': class_name, 
                'entity_type': 'record', 
                'entity_id': record_id, 
                'view_configuration': view_configuration
            }), 'utf-8'))
            counter = counter + 1
    return counter