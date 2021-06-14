import json, boto3, base64, time

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 

def main(event, context):
    '''
    - triggered by core/socket when it is a tunnel socket
    '''
    print(event)
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    if event.get('socket_url') and event.get('socket_id'):
        tunnel_id_sent = False
        count = 10
        while count and (not tunnel_id_sent):
            count = count - 1
            try:
                apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=event['socket_url'])
                postConnectionResponse = apigatewaymanagementapi.post_to_connection(ConnectionId=event['socket_id'], Data=bytes(json.dumps({'tunnel_id': event['socket_id']}), 'utf-8'))
                tunnel_id_sent = True
                break
            except:
                tunnel_id_sent = False

