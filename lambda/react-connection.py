import boto3, os

def main(event_data, context):
    '''
    - triggered by writes at /connection/{connection_id}.json
    - deletes all objects under /connection/{connection_id}/
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    counter = 0
    for event in event_data['Records']:
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