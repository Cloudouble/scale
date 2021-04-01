import json, boto3


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
    request['uri'] = '/websocket'
    request['querystring'] = 'connection={connection_id}&context={connection_context}'.format(connection_id=connection_id, connection_context=connection_context)
    return request