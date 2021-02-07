import json, boto3, os

def main(event_data, context):
    # reacts to /_/query/{class_name}/{query_id}.json
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for event in event_data['Records']:
        path = event['s3']['object']['key'].strip('/?').removeprefix('_').removesuffix('.json').strip('/').split('/')
        class_name, query_id = path[1:3]
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