import json, boto3, os

def main(event, context):
    '''
    - triggered by react-query.py, react-version.py
    - executes the given query using the given record, returning True if matching
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    lambda_client = boto3.client('lambda')
    counter = 0
    query_id = event.get('query')
    record_stub = event.get('record', {})
    if query_id and record_stub:
        record_type = record_stub.get('@type')
        record_id = record_stub.get('@id')
        record_data = json.loads(bucket.get_object(Key='record/{record_type}/{record_id}.json'.format(record_type=record_type, record_id=record_id))['Body'].read().decode('utf-8'))
        query_payload = {'purpose': 'query', 'record': record_data}
        query_result = json.loads(lambda_client.invoke(FunctionName=query_id, InvocationType='RequestResponse', Payload=bytes(json.dumps(query_payload), 'utf-8'))['Payload'].read().decode('utf-8'))
        query_index_key = '_/query/{record_type}/{query_id}/{record_initial}.json'.format(query_id=query_id, record_initial=record_id[0])
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
