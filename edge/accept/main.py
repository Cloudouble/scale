import json, boto3, base64, uuid
from urllib.parse import parse_qs


buckets = {
    '_': 'scale.live-element.net/_/request', 
    'ap-southeast-2': 'ap-southeast-2.scale.live-element.net'
}


def main(event, context):
    '''
    - triggered as an endpoint for a CDN or API originated PUT / PATCH / POST / DELETE request, or a websocket $put/$post/$patch/$delete message
    - writes a request entry to the _/write folder or geo-optimised write bucket
    - request {method, uri, headers, content-type, body}
    - returns {status: '202'} on success or {status: '50x'} | {status: '40x'} on failure
    '''
    status = 202
    try:
        bucket_name, path = [v.strip('/?') for v in (buckets.get(context.invoked_function_arn.split(':')[3], buckets['_']).strip('/') + '/').split('/', 1)]
    except:
        status = 500
    s3_client = boto3.client('s3')
    if status == 202:
        try:
            for request_object in [r['cf']['request'] for r in event.get('Records', [])]:
                request_entry = {}
                request_entry['uri'] = request_object.get('uri', '').strip('?/')
                request_entry['headers'] = {k: v[0]['value'] for k,v in request_object.get('headers', {}).items()}
                request_entry['content-type'] = request_entry['headers'].get('content-type', 'application/json')
                status = 202 if request_entry['uri'] and request_entry['headers'] and request_entry['content-type'] else 500
                if status == 202:
                    if request_object.get('body', {}).get('data', ''):
                        body_bytes = bytes(request_object['body']['data'], 'utf-8') if request_object['body']['encoding'] == 'text' else base64.b64decode(request_object['body']['data'])
                        if request_entry['content-type'] == 'application/x-www-form-urlencoded':
                            try: 
                                body_bytes = bytes(json.dumps({k: v[0] for k, v in parse_qs(body.decode('utf-8')).items()}), 'utf-8')
                            except: 
                                body_bytes = bytes(json.dumps({}), 'utf-8')
                                status = 400
                            request_entry['content-type'] = 'application/json'
                        request_entry['body'] = base64.b64encode(body_bytes).decode('utf-8')
                    request_entry['method'] = request_object.get('method', 'POST' if request_entry.get('body') else 'GET')
                    status = 202 if request_entry['method'] in ['DELETE', 'GET', 'PATCH', 'POST', 'PUT'] else 405
                    if status == 202:
                        request_uuid = str(uuid.uuid4())
                        status = 202 if request_uuid else 500
                        if status == 202:
                            try:
                                s3_client.put_object(Bucket=bucket_name, Key='{}/{}.json'.format(path, request_uuid).strip('/?'), Body=bytes(json.dumps(request_entry), 'utf-8'), ContentType='application/json')
                            except: 
                                status = 500
        except:
            status = 500
    return {'status': status}