import boto3, os

def main(event_data, context):
    # reacts to /_/query/{class_name}/{query_id}.json
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for event in event_data['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        class_name, query_id = path[1:3]
        # async run query for all records of the class_name
        record_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/record/{class_name}/'.format(class_name=class_name))
        
        lambda_client.invoke(FunctionName='evaluate-record', Payload=bytes(json.dumps(mask_payload), 'utf-8'))
        
        c = 1000000000
        while c and list_response.get('IsTruncated') and list_response.get('NextContinuationToken'):
            record_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/record/{class_name}/'.format(class_name=class_name), ContinuationToken=list_response.get('NextContinuationToken'))
        
        
        
        
        
        
        
        
        
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        if path and len(path) == 2 and path[0] == 'connection':
            connection_id = path[1]
            s3_client = boto3.client('s3')
            list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/connection/{}/'.format(connection_id))
            delete_response = s3_client.delete_objects(Bucket='string', Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents']], 'Quiet': True})
            c = 1000
            while c and list_response.get('IsTruncated') and list_response.get('NextContinuationToken'):
                list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/connection/{}/'.format(connection_id), ContinuationToken=list_response.get('NextContinuationToken'))
                delete_response = s3_client.delete_objects(Bucket='string', Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents']], 'Quiet': True})
                c = c - 1
            counter = counter + 1
    return counter