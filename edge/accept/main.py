buckets = {'_': 'us-east-1.request.scale.live-element.net', 'ap-southeast-2': 'ap-southeast-2.request.scale.live-element.net'}

import json, boto3, base64, uuid
from urllib.parse import parse_qs


def main(event, context):
    '''
    - triggered as an endpoint for a CDN or API originated PUT / PATCH / POST / DELETE request, or a websocket $put/$post/$patch/$delete message
    - writes a request entry to a geo-optimised write bucket
    - request {method, uri, headers, content-type, body}
    - returns {status: '202'} on success or {status: '50x'} | {status: '40x'} on failure
    '''
    status = 202
    try:
        bucket_name = buckets.get(context.invoked_function_arn.split(':')[3], buckets['_'])
    except:
        status = 500
    s3_client = boto3.client('s3')
    if status == 202:
        try:
            for request_object in [r['cf']['request'] for r in event.get('Records', [])]:
                is_options = request_object.get('method') == 'OPTIONS' 
                if not is_options:
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
                                    s3_client.put_object(Bucket=bucket_name, Key='{}.json'.format(request_uuid), Body=bytes(json.dumps(request_entry), 'utf-8'), ContentType='application/json')
                                except: 
                                    status = 500
        except:
            status = 500
        status = 200 if is_options else status
    return {
        'status': status, 
        'headers': {
             'access-control-allow-origin': [{
                 'key': 'Access-Control-Allow-Origin',
                 'value': '*'
             }], 
             'access-control-allow-credentials': [{
                 'key': 'Access-Control-Allow-Credentials',
                 'value': 'true'
             }], 
             'access-control-allow-headers': [{
                 'key': 'Access-Control-Allow-Headers',
                 'value': '*'
             }], 
             'access-control-allow-methods': [{
                 'key': 'Access-Control-Allow-Methods',
                 'value': 'OPTIONS, GET, HEAD, PUT, POST, DELETE'
             }], 
             'access-control-max-age': [{
                 'key': 'Access-Control-Max-Age',
                 'value': '86400'
             }]
        }
    }
