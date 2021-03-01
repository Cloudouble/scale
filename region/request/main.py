env = {"bucket": "scale.live-element.net", "core_request_bucket": "request.scale.live-element.net"}

import json, boto3, base64


def main(event, context):
    '''
    - triggered by request objects written to to a dedicated regional request bucket
    - writes valid request objects to the core request bucket 
    '''
    s3_client = boto3.client('s3')
    requests = {}
    for entry in [ent for ent in [{**r.get('s3', {}).get('bucket', {}), **r.get('s3', {}).get('object', {})} for r in event.get('Records', [])] if ent.get('key') and ent.get('name')]:
        try:
            request_data = json.loads(s3_client.get_object(Bucket=entry['name'], Key=entry['key'])['Body'].read().decode('utf-8'))
        except:
            request_data = {}
        if type(request_data) is dict and all([k in request_data for k in ['body', 'content-type', 'headers', 'method', 'uri']]):
            if request_data['content-type'] == 'application/json':
                try:
                    request_data['entity'] = json.loads(base64.b64decode(request_data['body']).decode('utf-8'))
                    requests[entry['key']] = request_data
                except:
                    pass
            else:
                requests[entry['key']] = request_data
    if not requests:
        return 0
    counter = 0
    for key, request in requests.items():
        try:
            s3_client.put_object(Bucket=env['core_request_bucket'], Body=bytes(json.dumps(request), 'utf-8'), Key=key, ContentType='application/json')
            counter = counter + 1
        except:
            pass
    return counter
