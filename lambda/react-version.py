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
            record_type, record_id, record_version = path[1:]
            record_data = json.loads(bucket.get_object(Key='_/record/{record_type}/{record_id}.json'.format(record_type=record_type, record_id=record_id))['Body'].read().decode('utf-8'))
            updated_fields = sorted(json.loads(bucket.get_object(Key=record['s3']['object']['key'])['Body'].read().decode('utf-8')))
            query_list = []
            for field_name in updated_fields:
                try:
                    query_list.entend(json.loads(bucket.get_object(Key='_/vector/{record_type}/{field_name}.json'.format(record_type=record_type, field_name=field_name))['Body'].read().decode('utf-8')))
                except:
                    pass
            query_list = sorted(list(set(query_list)))
            for query_id in query_list:
                lambda_client.invoke(FunctionName='query-record', InvocationType='Event', Payload=bytes(json.dumps({'query': query_id, 'record': record_data}), 'utf-8'))
    return counter
    
    
