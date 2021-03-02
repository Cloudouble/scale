import json, boto3, base64

def getpath(p, env=None):
    p = p.strip('/?')
    if env and env.get('data_root'):
        p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def get_env_context(event, context):
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    env['path'] = getpath(event['key'], env)
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    return env, client_context

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)


def main(event, context):
    '''
    - triggered by writes at _/query/{class_name}/{query_id}.json
    - for each field in _/vector/{class_name}/, remove the query_id if the field name is not in query->vector
    - for each query->vector, ensure that the query_id is present in _/vector/{class_name}.json
    - trigger query for every record in /record/{class_name}
    '''
    counter = 0
    vectors_to_update = {}
    s3_client = boto3.client('s3')
    if event.get('key'):
        s3 = boto3.resource('s3')
        lambda_client = boto3.client('lambda')
        env, client_context = get_env_context(event, context)    
        bucket = s3.Bucket(env['bucket'])
        class_name, query_id = env['path'][1:3]
        query_data = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8'))
        vector_base_key = '{data_root}/vector/{class_name}/'.format(data_root=env['data_root'], class_name=class_name)
        vector_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=vector_base_key)
        for vector_listing in vector_list_response.get('Contents', []):
            field_name = getpath(vector_listing['Key'], env)[2]
            if vector_listing['Key'] in vectors_to_update:
                vector_queries = vectors_to_update[vector_listing['Key']]
            else:
                vector_obj = bucket.Object(vector_listing['Key'])
                vector_queries = json.loads(vector_obj.get()['Body'].read().decode('utf-8'))
            if query_id in vector_queries and field_name not in query_data['vector']:
                vector_queries.remove(query_id)
                vector_queries.sort()
            elif query_id not in vector_queries and field_name in query_data['vector']:
                vector_queries.append(query_id)
                vector_queries.sort()
            vectors_to_update[vector_listing['Key']] = vector_queries
        for field_name in query_data.get('vector', []):
            vector_key = '{data_root}/vector/{class_name}/{field_name}.json'.format(data_root=env['data_root'], class_name=class_name, field_name=field_name)
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
    for key, vector_queries in vectors_to_update.items():
        s3_client.put_object(Bucket=env['bucket'], Key=key, Body=bytes(json.dumps(vector_queries), 'utf-8'), ContentType='application/json')
    if event.get('key'):
        record_base_key = '{data_root}/record/{class_name}/'.format(data_root=env['data_root'], class_name=class_name)
        record_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=record_base_key)
        for key_obj in record_list_response['Contents']:
            r_id = key_obj['Key'].replace(record_base_key, '')
            r_id = r_id[:-len('.json')] if r_id.endswith('.json') else r_id
            lambda_client.invoke(FunctionName=getprocessor(env, 'query'), InvocationType='Event', Payload=bytes(json.dumps({
                'query_id': query_id,
                'processor': query_data.get('processor'), 
                'options': query_data.get('options', {}), 
                'record': {'@type': class_name, '@id': r_id}, 
                '_env': env
            }), 'utf-8'))
        c = 1000000000
        while c and record_list_response.get('IsTruncated') and record_list_response.get('NextContinuationToken'):
            record_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix='{data_root}/record/{class_name}/'.format(data_root=env['data_root'], class_name=class_name), ContinuationToken=record_list_response.get('NextContinuationToken'))
            for key_obj in record_list_response['Contents']:
                record_id = key_obj['Key'].replace(record_base_key, '')
                if record_id.endswith('.json'):
                    record_id = record_id[0:-5]
                lambda_client.invoke(FunctionName=getprocessor(env, 'query'), InvocationType='Event', Payload=bytes(json.dumps({
                    'query_id': query_id,
                    'processor': query_data.get('processor'), 
                    'options': query_data.get('options', {}), 
                    'record': {'@type': class_name, '@id': record_id}, 
                    '_env': env
                }), 'utf-8'))
                c = c - 1
        counter = counter + 1
    return counter