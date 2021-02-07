import json, boto3, os, base64, uuid, time
from urllib.parse import parse_qs

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

 
def main(event_data, context):
    # reacts to writes to /_/connection/{connection_id}.json 
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    for event in event_data['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        if path and len(path) == 2 and path[0] == 'connection':
            connection_id = path[1]
            connection_feed_ledger_path = '_/connection/{}/feed.json'.format(connection_id)
            if event.get('eventName') == 'ObjectRemoved:Delete':
                # ** remove connection from feeds 
                connection_feed_ledger_object = bucket.Object(connection_feed_ledger_path)
                try:
                    connection_feed_ledger_data = connection_object.get()['Body'].read().decode('utf-8')
                except:
                    connection_feed_ledger_data = {}
                for class_name in connection_feed_ledger_data:
                    for entity_id in connection_feed_ledger_data[class_name]:
                        feed_ledger_path = '_/feed/{class_name}/{entity_id}/{connection_id}.json'.format(class_name=class_name, entity_id=entity_id, connection_id=connection_id)
                        feed_ledger_object = bucket.Object(connection_feed_ledger_path)
                        feed_ledger_object.delete()
                connection_feed_ledger_object.delete()
            s3_client = boto3.client('s3')
            list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/connection/{}/'.format(connection_id))
            delete_response = s3_client.delete_objects(Bucket='string', Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents'] if c['Key'] != connection_feed_ledger_path], 'Quiet': True})
            c = 1000
            while c and list_response.get('IsTruncated') and list_response.get('NextContinuationToken'):
                list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/connection/{}/'.format(connection_id), ContinuationToken=list_response.get('NextContinuationToken'))
                delete_response = s3_client.delete_objects(Bucket='string', Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents'] if c['Key'] != connection_feed_ledger_path], 'Quiet': True})
                c = c - 1
