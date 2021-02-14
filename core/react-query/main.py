env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['system_root']):] if p.startswith(env['system_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')


def main(event_data, context):
    '''
    - triggered by writes at /query/{class_name}/{query_id}.json
    - for each field in /vector/{class_name}/, remove the query_id if the field name is not in query->vector
    - for each query->vector, ensure that the query_id is present in /vector/{class_name}.json
    - trigger query-record.py for every record in /record/{class_name}
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    vectors_to_update = {}
    for event in event_data['Records']:
        path = getpath(event['s3']['object']['key'])
        class_name, query_id = path[1:3]
        query_data = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['s3']['object']['key'])['Body'].read().decode('utf-8'))
        vector_base_key = '{system_root}/vector/{class_name}/'.format(system_root=env['system_root'], class_name=class_name)
        vector_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=vector_base_key)
        for vector_listing in vector_list_response.get('Contents', []):
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
        for field_name in query_data.get('vector', []):
            vector_key = '{system_root}/vector/{class_name}/{field_name}.json'.format(system_root=env['system_root'], class_name=class_name, field_name=field_name)
            if vector_key not in vectors_to_update:
                vector_obj = bucket.Object(vector_key)
                try:
                    vector_queries = json.loads(vector_obj.get()['Body'].read().decode('utf-8'))
                except:
                    vector_queries = []
                if query_id not in vector_queries:
                    vector_queries.append(query_id)
                    vector_queries.sort()
                    vectors_to_update[vector_key] = vector_queries
    for key, vectors_queries in vectors_to_update.items():
        vector_obj.put(Body=bytes(json.dumps(vector_queries), 'utf-8'), ContentType="application/json")
    for event in event_data['Records']:
        record_base_key = '{system_root}/record/{class_name}/'.format(system_root=env['system_root'], class_name=class_name)
        record_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=record_base_key)
        for key_obj in record_list_response['Contents']:
            lambda_client.invoke(FunctionName='{lambda_namespace}-core-query-record'.format(lambda_namespace=env['lambda_namespace']), Payload=bytes(json.dumps({
                'query_id': query_id,
                'record': {'@type': class_name, '@id': key_obj['Key'].replace(record_base_key, '').removesuffix('.json')}
            }), 'utf-8'))
        c = 1000000000
        while c and record_list_response.get('IsTruncated') and record_list_response.get('NextContinuationToken'):
            record_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix='{system_root}/record/{class_name}/'.format(system_root=env['system_root'], class_name=class_name), ContinuationToken=record_list_response.get('NextContinuationToken'))
            for key_obj in record_list_response['Contents']:
                lambda_client.invoke(FunctionName='{lambda_namespace}-core-query-record'.format(lambda_namespace=env['lambda_namespace']), Payload=bytes(json.dumps({
                    'query_id': query_id,
                    'record': {'@type': class_name, '@id': key_obj['Key'].replace(record_base_key, '').removesuffix('.json')}
                }), 'utf-8'))
                c = c - 1
        counter = counter + 1
    return counter