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
    if event.get('requestContext'):
        requestContext = event['requestContext']
        connectionId = requestContext.get('connectionId')
        if connectionId and requestContext.get('domainName') and requestContext.get('stage') and requestContext.get('routeKey'):
            routeKey = requestContext['routeKey']
            endpointUrl = 'https://{domainName}/{stage}'.format(domainName=requestContext['domainName'], stage=requestContext['stage'])
            if routeKey == '$connect':
                statusCode = 200
            elif routeKey == '$default':
                print('line 30', connectionId)
                print('line 31', endpointUrl)
                apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=endpointUrl)
                postConnectionResponse = apigatewaymanagementapi.post_to_connection(
                    ConnectionId=connectionId, 
                    Data=bytes(json.dumps('test'), 'utf-8')
                )
                statusCode = 200
    response = {'statusCode': statusCode}
    return response

