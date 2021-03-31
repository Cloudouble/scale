import json, boto3


def main(event, context):
    '''
    - triggered at the edge to transform the websocket url
    '''
    connection_id = event['Records'][0]['cf']['request']['uri'].replace('connection', '').replace('websocket', '').replace('_', '').strip('/')
    request = event['Records'][0]['cf']['request']
    request['uri'] = '/websocket'
    request['querystring'] = 'connection={connection_id}'.format(connection_id=connection_id)
    return request