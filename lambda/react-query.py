import json, boto3, os

def main(event_data, context):
    '''
    - triggered by writes at /query/{class_name}/{query_id}.json
    - for each field in /vector/{class_name}/, remove the query_id if the field name is not in query->vector
    - for each query->vector, ensure that the query_id is present in /vector/{class_name}.json
    - trigger query-record.py for every record in /record/{class_name}
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    vectors_to_update = {}
    for event in event_data['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        class_name, query_id = path[1:3]
        query_data = json.loads(bucket.get_object(Key=event['s3']['object']['key'])['Body'].read().decode('utf-8'))
        vector_base_key = '_/vector/{class_name}/'.format(class_name=class_name)
        vector_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=vector_base_key)
        for vector_listing in vector_list_response['Contents']:
            field_name = vector_listing['Key'].strip('/').removeprefix('_').removesuffix('.json').strip('/').split()[2]
            if vector_listing['Key'] in vectors_to_update:
                vector_queries = vectors_to_update[vector_listing['Key']]
            else:
                vector_obj = bucket.Object(vector_listing['Key'])
                vector_queries = json.loads(vector_obj.get()['Body'].read().decode('utf-8'))
            if query_id in vector_queries and field_name not in query_data['vectors']:
                vector_queries.remove(query_id).sort()
            elif query_id not in vector_queries and field_name in query_data['vectors']:
                vector_queries.append(query_id).sort()
            vectors_to_update[vector_listing['Key']] = vector_queries
        for field_name in query_data.get('vectors', []):
            vector_key = '_/vector/{class_name}/{field_name}.json'.format(class_name=class_name, field_name=field_name)
            if vector_key not in vectors_to_update:
                vector_obj = bucket.Object(vector_key)
                vector_queries = json.loads(vector_obj.get()['Body'].read().decode('utf-8'))
                if query_id not in vector_queries:
                    vector_queries.append(query_id).sort()
                    vectors_to_update[vector_key] = vector_queries
    for key, vectors_queries in vectors_to_update.items():
        vector_obj.put(Body=bytes(json.dumps(vector_queries), 'utf-8'))
    for event in event_data['Records']:
        record_base_key = '_/record/{class_name}/'.format(class_name=class_name)
        record_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=record_base_key)
        for key_obj in record_list_response['Contents']:
            lambda_client.invoke(FunctionName='query-record', Payload=bytes(json.dumps({
                'query_id': query_id,
                'record': {'@type': class_name, '@id': key_obj['Key'].replace(record_base_key, '').removesuffix('.json')}
            }), 'utf-8'))
        c = 1000000000
        while c and record_list_response.get('IsTruncated') and record_list_response.get('NextContinuationToken'):
            record_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/record/{class_name}/'.format(class_name=class_name), ContinuationToken=record_list_response.get('NextContinuationToken'))
            for key_obj in record_list_response['Contents']:
                lambda_client.invoke(FunctionName='query-record', Payload=bytes(json.dumps({
                    'query_id': query_id,
                    'record': {'@type': class_name, '@id': key_obj['Key'].replace(record_base_key, '').removesuffix('.json')}
                }), 'utf-8'))
                c = c - 1
        counter = counter + 1
    return counter