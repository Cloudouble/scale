import json, boto3, os, time


def trash_record(key_obj, bucket, lambda_client):
    record_path = key_obj['Key'].strip('/?').removeprefix('_/').removesuffix('.json').split('/')
    class_name, record_id = record_path[1:3]
    record_obj = bucket.Object(key_obj['Key'])
    record = json.loads(record_obj.get().read().decode('utf-8'))
    switches = {'entity_type': 'record', 'class_name': class_name, 'entity_id': record_id}
    validate_payload = {'entity': record, 'switches': switches}
    if not (record and type(record) is dict and record.get('@type') == class_name and record.get('@id') == 'record_id' and json.loads(lambda_client.invoke(FunctionName='{}-validate'.format(os.environ['lambda_namespace']), Payload=bytes(json.dumps({'entity': record, 'switches': switches}), 'utf-8'))['Payload'].read().decode('utf-8'))):
        bucket.put_object(Body=bytes(json.dumps(validate_payload), 'utf-8'), Key='_/trash/record/{class_name}/{record_id}.json'.format(class_name=class_name, record_id=record_id), ContentType='application/json')
        record_obj.delete()
        bucket.put_object(Body=bytes(json.dumps(sorted(list(record.keys()))), 'utf-8'), Key='_/record/{class_name}/{record_id}/deleted.json'.format(class_name=class_name, record_id=record_id), ContentType='application/json')
    
    
def remove_versions(key_obj, bucket, s3_client):
    version_path = key_obj['Key'].strip('/?').removeprefix('_/').removesuffix('.json').split('/')
    class_name, record_id = version_path[1:3]
    version_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/version/{class_name}/{record_id}/'.format(class_name=class_name, record_id=record_id))
    for key_obj in version_list_response['Contents']:
        version_obj = bucket.Object(key_obj['Key'])
        version_obj.delete()
    cc = 1000000000
    while cc and version_list_response.get('IsTruncated') and version_list_response.get('NextContinuationToken'):
        version_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/version/{class_name}/{record_id}/', ContinuationToken=version_list_response.get('NextContinuationToken'))
        for key_obj in version_list_response['Contents']:
            version_obj = bucket.Object(key_obj['Key'])
            version_obj.delete()
            cc = cc - 1
        



def main(event, context):
    '''
    - triggered on-demand by an administrator
    - schema-enforce: runs validation over every record in the system and moves them to /trash/record/{record_id}.json if found invalid
    - delete-marker-tidy: removes version objects related to deleted records
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    if event.get('schema-enforce'):
        counter = 0
        record_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/record/')
        for key_obj in record_list_response['Contents']:
            trash_record(key_obj, bucket, lambda_client)
        c = 1000000000
        while c and record_list_response.get('IsTruncated') and record_list_response.get('NextContinuationToken'):
            record_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/record/', ContinuationToken=record_list_response.get('NextContinuationToken'))
            for key_obj in record_list_response['Contents']:
                trash_record(key_obj, bucket, lambda_client)
            c = c - 1
        return counter
    elif event.get('delete-marker-tidy'):
        expire = time.time() - 3600
        counter = 0
        record_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/version/')
        for key_obj in [key_obj for key_obj in record_list_response['Contents'] if key_obj['Key'].endswith('/deleted.json') and key_obj['LastModified'].timestamp() < expire]:
            remove_versions(key_obj, bucket, s3_client)
            counter = counter + 1
        c = 1000000000
        while c and record_list_response.get('IsTruncated') and record_list_response.get('NextContinuationToken'):
            record_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix='_/version/', ContinuationToken=record_list_response.get('NextContinuationToken'))
            for key_obj in [key_obj for key_obj in record_list_response['Contents'] if key_obj['Key'].endswith('/deleted.json') and key_obj['LastModified'].timestamp() < expire]:
                remove_versions(key_obj, bucket, s3_client)
                counter = counter + 1
            c = c - 1
            

        
