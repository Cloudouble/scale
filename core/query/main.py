import json, boto3, base64

def main(event, context):
    '''
    - triggered by react-query.py, react-version.py
    - executes the given query using the given record 
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    query_id = event.get('query_id')
    query_processor = event.get('processor')
    query_options = event.get('options')
    record_stub = event.get('record', {})
    if query_id and query_processor and record_stub:
        class_name = record_stub.get('@type')
        record_id = record_stub.get('@id')
        record_data = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/record/{class_name}/{record_id}.json'.format(data_root=env['data_root'], class_name=class_name, record_id=record_id))['Body'].read().decode('utf-8'))
        query_payload = {'record': record_data, 'options': query_options}
        query_result = json.loads(lambda_client.invoke(FunctionName='{lambda_namespace}-extension-query-{query_processor}'.format(lambda_namespace=env['lambda_namespace'], query_processor=query_processor), InvocationType='RequestResponse', Payload=bytes(json.dumps(query_payload), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
        query_index_key = '{data_root}/query/{class_name}/{query_id}/{record_initial}.json'.format(data_root=env['data_root'], class_name=class_name, query_id=query_id, record_initial=record_id[0])
        try:
            query_index = json.loads(bucket.get_object(Key=query_index_key)['Body'].read().decode('utf-8'))
        except:
            query_index = []
        query_index_changed = False
        if query_result is True and record_id not in query_index:
            query_index.append(record_id)
            query_index.sort()
            query_index_changed = True
        elif query_result is False and record_id in query_index:
            query_index.remove(record_id)
            query_index.sort()
            query_index_changed = True
        if query_index_changed:
            bucket.put_object(Body=bytes(json.dumps(query_index), 'utf-8'), Key=query_index_key, ContentType='application/json')
            counter = counter + 1
    return counter
