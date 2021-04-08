env = '0 _ 771795544492 ap-southeast-2 liveelement-scale'

import json, boto3, base64, uuid

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True


def main(event, context):
    request = event.get('Records', [{}])[0].get('cf', {}).get('request', {})
    uri = request.get('uri')
    method = request.get('method', 'GET')
    is_options = request.get('method') == 'OPTIONS' 
    if not is_options:
        status = 500
        if uri:
            uri_split = uri.split('/')
            if len(uri_split) == 4:
                channel_id, send_key = uri_split[-2:]
                if uuid_valid(channel_id) and uuid_valid(send_key):
                    shared, system_root, account_id, core_region, lambda_namespace = env.split(' ')
                    data_root = '{host}/{system_root}'.format(host=request['headers'].get('host', ''), system_root=system_root) if shared != '0' else system_root
                    try:
                        bucket_name = buckets.get(context.invoked_function_arn.split(':')[3])
                    except:
                        bucket_name = None
                        status = 500
                    if bucket_name:
                        s3_client = boto3.client('s3')
                        try:
                            channel_config = json.loads(s3_client.get_object(Bucket=bucket_name, Key='{data_root}/channel/{channel_id}/connect.json'.format(data_root=data_root, channel_id=channel_id))['Body'].decode('utf-8'))
                        except: 
                            channel_config = {}
                            status = 404
                        if type(channel_config) is dict and channel_config.get('sendKey') == send_key:
                            body = request.get('body') 
                            data = body.get('data') 
                            encoding = body.get('encoding') 
                            if encoding == 'base64':
                                message = base64.b64decode(bytes(data, 'utf-8'))
                            else:
                                message = bytes(data, 'utf-8')
                            if message:
                                processor = 'arn:aws:lambda:{core_region}:{account_id}:function:{lambda_namespace}-core-channel'.format(core_region=core_region, account_id=account_id, lambda_namespace=lambda_namespace)
                                try:
                                    lambda_client.invoke(FunctionName=processor, Payload=bytes(json.dumps({'channel': channel_id, 'message': base64.b64encode(message).decode('utf-8')}), 'utf-8'), InvocationType='Event')
                                except:
                                    status = 500
                            else:
                                status = 400
                        else:
                            status = 404
                    else:
                        status = 500
                else:
                    status = 400
            else:
                status = 400
        else:
             status = 400           
    else:
        status = 200
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


