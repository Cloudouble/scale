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
    elif 'channel' in uri:
        channel_id, receive_key = uri.replace('channel', '').replace('_', '').strip('/').split('/')
        connection_context = 'channel'
    request['uri'] = '/websocket'
    if connection_context == 'channel':
        request['querystring'] = 'connection={channel_id}&context={connection_context}&key={key}'.format(channel_id=channel_id, connection_context=connection_context, key=receive_key)
    else:
        request['querystring'] = 'connection={connection_id}&context={connection_context}'.format(connection_id=connection_id, connection_context=connection_context)
    return request