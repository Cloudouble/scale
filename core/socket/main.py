env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "LiveElementScale"}

import json, boto3, base64, uuid, hashlib

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
    host = request.get('headers', {}).get('Host') if env['shared'] else ''
    env['data_root'] = '{host}/{system_root}'.format(host=host, system_root=env['system_root']).strip('/')
    if event.get('requestContext'):
        requestContext = event['requestContext']
        socket_id = requestContext.get('connectionId')
        if socket_id and requestContext.get('domainName') and requestContext.get('stage') and requestContext.get('routeKey'):
            route_key = requestContext['routeKey']
            endpoint_url = 'https://{domainName}/{stage}'.format(domainName=requestContext['domainName'], stage=requestContext['stage'])
            connection_record = {}
            if route_key in ['$connect', '$disconnect'] and event.get('queryStringParameters') and event['queryStringParameters'].get('connection'):
                connection_id = event['queryStringParameters']['connection']
                connection_object = bucket.Object('{data_root}/connection/{connection_id}/connect.json'.format(data_root=env['data_root'], connection_id=connection_id))
                try:
                    connection_record = json.loads(connection_object.get()['Body'].read().decode('utf-8'))
                except:
                    connection_record = {}
            if route_key == '$connect' and connection_record:
                env['connection_id'] = connection_id
                client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
                connection_record['socket_url'] = endpoint_url
                connection_record['socket_id'] = socket_id
                lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': 'connection', 'entity': connection_record, 'method': 'PUT'}), 'utf-8'), ClientContext=client_context)
                statusCode = 200
            else:
                statusCode = 405
    response = {'statusCode': statusCode}
    return response

