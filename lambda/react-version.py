import json, boto3, os

def main(event, context):
    #reacts to updated record version objects _/version/{class_name}/{record_id}/{version_id}.json
    # ** build related index of queries that include this record
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    lambda_client = boto3.client('lambda')
    counter = 0
    for record in event['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        if len(path) == 4:
            check, record_type, record_id, record_version = path
            if check == 'version':
                record_object = json.loads(bucket.get_object(Key='_/record/{record_type}/{record_id}.json'.format(record_type=record_type, record_id=record_id))['Body'].read().decode('utf-8'))
                updated_fields = sorted(json.loads(bucket.get_object(Key=record['s3']['object']['key'])['Body'].read().decode('utf-8')))
                query_list = []
                for updated_field in updated_fields:
                    try:
                        query_list.entend(json.loads(bucket.get_object(Key='_/vector/{record_type}/{field_name}.json'.format(record_type=record_type, field_name=updated_field))['Body'].read().decode('utf-8')))
                    except:
                        pass
                query_list = sorted(list(set(query_list)))
                for query_id in query_list:
                    query_payload = {'purpose': 'query', 'record': record_object}
                    query_result = json.loads(lambda_client.invoke(FunctionName=query_id, InvocationType='RequestResponse', Payload=bytes(json.dumps(query_payload), 'utf-8'))['Payload'].read().decode('utf-8'))
                    query_index_key = 'query/{record_type}/{query_id}/{record_initial}.json'.format(query_id=query_id, record_initial=record_id[0])
                    try:
                        query_index = json.loads(bucket.get_object(Key=query_index_key)['Body'].read().decode('utf-8'))
                    except:
                        query_index = []
                    query_index_changed = False
                    if query_result is True and record_id not in query_result:
                        query_index.append(record_id).sort()
                        query_index_changed = True
                    elif query_result is False and record_id in query_result:
                        query_index.remove(record_id).sort()
                        query_index_changed = True
                    if query_index_changed:
                        bucket.put_object(Body=bytes(json.dumps(query_index), 'utf-8'), Key=query_index_key, ContentType='application/json')
                        counter = counter + 1
    return counter
    
    
