import json, boto3, os, time

def main(event, context):
    '''
    - triggered by new/updated objects at /query/{class_name}/{query_id}/{record_initial}.json
    - uses /feed/{class_name}/{query_id}/{connection_id}.json to find affected connections
    - triggers mask.py for each record_id in the index that doesn't already exist in the /connection/{connection_id}/record/{class_name}/{record_id}.json
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    affected_connections = set()
    for record in event['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        index_record_ids = set(json.loads(bucket.get_object(Key=event['s3']['object']['key'])['Body'].read().decode('utf-8')))
        if len(path) == 4:
            class_name, query_id, index = path[1:]
            # '/_/feed/{class_name}/{query_id}/{connection_id}.json'
            feed_base_key = '_/feed/{class_name}/{query_id}/'.format(class_name=class_name, query_id=query_id)
            feed_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=feed_base_key)
            for feed_entry in feed_list_response['Contents']:
                affected_connections.add(feed_entry['Key'].removesuffix('.json').split('/')[-1])
            c = 1000000000
            while c and feed_list_response.get('IsTruncated') and feed_list_response.get('NextContinuationToken'):
                feed_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=feed_base_key, ContinuationToken=feed_list_response.get('NextContinuationToken'))
                for key_obj in feed_list_response['Contents']:
                    affected_connections.add(feed_entry['Key'].removesuffix('.json').split('/')[-1])
                    c = c - 1
            for affected_connection in affected_connections:
                connection_records_base_key = '_/connection/{connection_id}/record/{class_name}/'.format(connection_id=affected_connection, class_name=class_name)
                class_name_record_ids = set()
                connection_records_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=connection_records_base_key)
                for record_entry in connection_records_list_response['Contents']:
                    class_name_record_ids.add(record_entry['Key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')[4])
                c = 1000000000
                while c and connection_records_list_response.get('IsTruncated') and connection_records_list_response.get('NextContinuationToken'):
                    connection_records_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=connection_records_base_key, ContinuationToken=feed_list_response.get('NextContinuationToken'))
                    for record_entry in connection_records_list_response['Contents']:
                        class_name_record_ids.add(record_entry['Key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')[4])
                for connection_record_id in index_record_ids.difference(class_name_record_ids):
                    lambda_client.invoke(FunctionName='mask', InvocationType='Event', Payload=bytes(json.dumps({
                        'connection_id': affected_connection,
                        'class_name': class_name, 
                        'record_id': connection_record_id, 
                    }), 'utf-8'))
            counter = counter + 1
    return counter
