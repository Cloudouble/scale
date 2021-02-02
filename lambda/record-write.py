import json, boto3, os, 

def main(record, context):
    retval = None
    try:
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(os.environ['bucket'])
        bucket.put_object(Body=bytes(json.dumps(record), 'utf-8'), ContentType='application/json', Key='record/{type}/{id}.json'.format(type=record['@type'], id=record['@id']))
        retval = True
    except:
        retval = False
    return retval

