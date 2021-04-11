env = 'ap-southeast-2 771795544492 liveelement-scale'

import json, boto3, base64


def main(event, context):
    '''
    - triggered at the edge to transform the websocket url
    '''
    request = event['Records'][0]['cf']['request']
    uri = request['uri']
    if 'websocket' in uri:
        connection_id = request['uri'].replace('connection', '').replace('websocket', '').replace('_', '').strip('/')
        connection_context = 'websocket'
    elif 'tunnel' in uri:
        connection_id = uri.replace('connection', '').replace('_', '').strip('/').split('/tunnel/')[0]
        connection_context = 'tunnel'
    elif 'channel' in uri:
        channel_id, key = uri.replace('channel', '').replace('_', '').strip('/').split('/')
        method = request['method']
        if method in ['OPTIONS', 'POST'] and key:
            retval = {
                'status': 200, 
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
            if method == 'OPTIONS':
                return retval
            elif method == 'POST' and request.get('body'):
                body = request['body'] 
                data = body.get('data') 
                encoding = body.get('encoding') 
                if data and encoding:
                    if encoding == 'base64':
                        message = base64.b64decode(bytes(data, 'utf-8'))
                    else:
                        message = bytes(data, 'utf-8')
                    if message:
                        core_region, account_id, lambda_namespace = env.split(' ')
                        processor = 'arn:aws:lambda:{core_region}:{account_id}:function:{lambda_namespace}-core-channel'.format(core_region=core_region, account_id=account_id, lambda_namespace=lambda_namespace)
                        try:
                            lambda_client.invoke(FunctionName=processor, Payload=bytes(json.dumps({'channel': channel_id, 'message': base64.b64encode(message).decode('utf-8')}), 'utf-8'), InvocationType='Event')
                        except:
                            return {**retval, 'status': 500}
                    else:
                        return {**retval, 'status': 400}
                else:
                    return {**retval, 'status': 400}
            else:
                return {**retval, 'status': 400}
        connection_context = 'channel'
    request['uri'] = '/websocket'
    if connection_context == 'channel' and key:
        request['querystring'] = 'connection={channel_id}&context={connection_context}&key={key}'.format(channel_id=channel_id, connection_context=connection_context, key=key)
    else:
        request['querystring'] = 'connection={connection_id}&context={connection_context}'.format(connection_id=connection_id, connection_context=connection_context)
    return request