endpoint_url_region_bucket = 'https://8pgxdglwp0.execute-api.ap-southeast-2.amazonaws.com/websocket ap-southeast-2 scale.liveelement.net'

import json, boto3, base64, time

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 

def main(event, context):
    '''
    - triggered by core/channel to send the message to all sockets in the given index
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    if event.get('index') and event.get('message'):
        endpoint_url, core_region, bucket_name = endpoint_url_region_bucket.split(' ')
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(env['bucket'])
        index_object = bucket.Object(event['index'])
        try:
            socket_list = json.loads(index_object.get()['Body'].read().decode('utf-8'))
        except:
            socket_list = []
        sockets_to_remove = []
        for socket_id in socket_list:
            try:
                apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
                postConnectionResponse = apigatewaymanagementapi.post_to_connection(ConnectionId=socket_id, Data=bytes(event['message'], 'utf-8'))
            except:
                sockets_to_remove.append(socket_id)
        if sockets_to_remove:
            socket_list = json.loads(index_object.get()['Body'].read().decode('utf-8'))
            socket_list = sorted(list(set(socket_list) - set(sockets_to_remove)))
            index_object.put(Body=bytes(json.dumps(socket_list), 'utf-8'), ContentType='application/json')
            

        
        
        
