env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "LiveElementScale"}

import json, boto3, base64, uuid, hashlib, time

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
    
 
def main(event, context):
    '''
    - triggered by web socket connections
    '''
    statusCode = 500
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    lambda_client = boto3.client('lambda')
    host = event.get('headers', {}).get('Origin', '').replace('https://', '').strip('/') if env['shared'] else ''
    env['data_root'] = '{host}/{system_root}'.format(host=host, system_root=env['system_root']).strip('/')
    if event.get('requestContext'):
        requestContext = event['requestContext']
        socket_id = requestContext.get('connectionId')
        if socket_id and requestContext.get('domainName') and requestContext.get('stage') and requestContext.get('routeKey'):
            route_key = requestContext['routeKey']
            endpoint_url = 'https://{domainName}/{stage}'.format(domainName=requestContext['domainName'], stage=requestContext['stage'])
            connection_record = {}
            connection_context = 'websocket'
            if route_key in ['$connect', '$disconnect'] and event.get('queryStringParameters') and event['queryStringParameters'].get('connection'):
                connection_id = event['queryStringParameters']['connection']
                connection_context = event['queryStringParameters'].get('context', 'websocket')
                if connection_context == 'channel':
                    connection_object = bucket.Object('{data_root}/channel/{connection_id}/connect.json'.format(data_root=env['data_root'], connection_id=connection_id))
                    key = event['queryStringParameters'].get('key')
                    try:
                        connection_record = json.loads(connection_object.get()['Body'].read().decode('utf-8'))
                    except:
                        connection_record = {}
                else:
                    connection_object = bucket.Object('{data_root}/connection/{connection_id}/connect.json'.format(data_root=env['data_root'], connection_id=connection_id))
                    try:
                        connection_record = json.loads(connection_object.get()['Body'].read().decode('utf-8'))
                    except:
                        connection_record = {}
            if route_key == '$connect' and connection_record:
                if connection_context == 'channel':
                    index_object = bucket.Object('{data_root}/channel/{connection_id}/{index}.json'.format(data_root=env['data_root'], connection_id=connection_id, index=connection_id[0]))
                    try:
                        socket_list = json.loads(index_object.get()['Body'].read().decode('utf-8'))
                    except:
                        socket_list = []
                    socket_list.append(socket_id)
                    socket_list = sorted(list(set(socket_list)))
                    index_object.put(Body=bytes(json.dumps(socket_list), 'utf-8'), ContentType='application/json')
                else:
                    env['connection_id'] = connection_id
                    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
                    connection_record['socket_url'] = endpoint_url
                    connection_record['socket_id'] = socket_id
                    if connection_context == 'websocket':
                        lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': 'connection', 'entity': connection_record, 'method': 'PUT'}), 'utf-8'), ClientContext=client_context)
                    elif connection_context == 'tunnel':
                        lambda_client.invoke(FunctionName=getprocessor(env, 'tunnel'), InvocationType='Event', Payload=bytes(json.dumps({'socket_url': endpoint_url, 'socket_id': socket_id, '_env': {'connection_id': connection_id, 'connection_type': 'connection', **env}}), 'utf-8'))
                statusCode = 200
            else:
                statusCode = 405
    response = {'statusCode': statusCode}
    return response
