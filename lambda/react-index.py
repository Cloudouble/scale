import json, boto3, os, time

def main(event, context):
    #reacts to updated record query indexes _/query/{class_name}/{query_id}/{index}.json
    # ** regenerate dependent views in all connections
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    for record in event['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        if len(path) == 4:
            class_name, query_id, index = path[1:]
            # '/_/feed/{class_name}/{query_id}/{connection_id}.json'
            feed_base_key = '_/feed/{class_name}/{query_id}/'.format(class_name=class_name, query_id=query_id)
            feed_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=feed_base_key)
            for feed_entry in feed_list_response['Contents']:
                feed_connection_id = feed_entry['Key'].removesuffix('.json').split('/')[-1]
                feed_data = json.loads(bucket.get_object(Key=feed_entry['Key'])['Body'].read().decode('utf-8'))
                # {expires, max, next, last, count, views=[{id, sort_field, sort_direction, min_index, max_index}]}
                active = True
                ready = True
                if (feed_data.get('expires') and feed_data['expires'] > now) or (feed_data.get('max') and feed_data.get('count') and feed_data['max'] > feed_data['count']):
                    active = False
                if feed_data.get('next') and feed_data.get('next') > now:
                    ready = False
                if active and ready and feed_data.get('views'):
                    lambda_client.invoke(FunctionName='view', InvocationType='Event', Payload=bytes(json.dumps({
                        'connection_id': feed_connection_id, 'class_name': class_name, 'query_id': query_id, 'views': feed_data['views']}), 'utf-8'))
                    counter = counter + 1
    return counter