endpoint_url_region = 'https://<apiId>.execute-api.ap-southeast-2.amazonaws.com/websocket ap-southeast-2'

import json, boto3, base64


def main(event, context):
    request = event.get('Records', [{}])[0].get('cf', {}).get('request', {})
    uri = request.get('uri')
    status = 500
    if uri:
        body = request.get('body') 
        data = body.get('data') 
        encoding = body.get('encoding') 
        if encoding == 'base64':
            message = base64.b64decode(bytes(data, 'utf-8'))
        else:
            message = base64.b64encode(bytes(data, 'utf-8'))
        if message:
            tunnel_id = uri.split('/')[-1]
            if tunnel_id:
                try: 
                    endpoint_url_region_split = endpoint_url_region.split(' ')
                    region = endpoint_url_region_split[1]
                    endpoint_url = endpoint_url_region_split[0]
                    apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', region_name=region, endpoint_url=endpoint_url)
                    apigatewaymanagementapi.post_to_connection(ConnectionId=tunnel_id, Data=message)
                    status = 200
                except:
                    status = 410
            else:
                status = 400
        else:
            status = 400
    return {
        'status': status
    }

