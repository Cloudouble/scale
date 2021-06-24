import liveelement
import json, boto3, base64


def main(event, context):
    request = event.get('Records', [{}])[0].get('cf', {}).get('request', {})
    uri = request.get('uri')
    status = 500
    if uri:
        body = request.get('body') 
        data = body.get('data') 
        encoding = body.get('encoding') 
        is_options = request.get('method') == 'OPTIONS' 
        if not is_options:
            if encoding == 'base64':
                message = base64.b64decode(bytes(data, 'utf-8'))
            else:
                message = base64.b64encode(bytes(data, 'utf-8'))
            if message:
                tunnel_id = uri.split('/')[-1]
                if tunnel_id:
                    try: 
                        region = liveelement.module['region']
                        endpoint_url = liveelement.module['endpoint']
                        apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', region_name=region, endpoint_url=endpoint_url)
                        apigatewaymanagementapi.post_to_connection(ConnectionId=tunnel_id, Data=message)
                        status = 200
                    except:
                        status = 410
                else:
                    status = 400
            else:
                status = 400
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
