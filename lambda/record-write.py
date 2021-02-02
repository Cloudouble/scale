import json, boto3, os

def main(record, context):
    retval = None
    try:
        bucket = boto3.resource('s3').Bucket(os.environ['bucket'])
        record_key = 'record/{type}/{id}.json'.format(type=record['@type'], id=record['@id'])
        try:
            current_record = json.loads(bucket.get_object(Key=record_key).read().decode('utf-8'))
        except:
            current_record = {}
        updated_fields = [f for f in record if record[f] != current_record.get(f)]
        put_response = bucket.put_object(Body=bytes(json.dumps(record), 'utf-8'), Key=record_key, ContentType='application/json')
        record_versions_key = 'version/{type}/{id}/{version}.json'.format(type=record['@type'], id=record['@id'], version=put_response['VersionId'])
        bucket.put_object(Body=bytes(json.dumps(updated_fields), 'utf-8'), Key=record_versions_key, ContentType='application/json')
        retval = True
    except:
        retval = False
    return retval