env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "LiveElementScale"}

import json, boto3, base64, time

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 

def main(event, context):
    '''
    - triggered by core/channel to send the message to all sockets in the given index
    '''
    if event.get('index') and event.get('index') and event.get('message'):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(env['bucket'])
        index_object = bucket.Object(event['index'])
        try:
            socket_map = json.loads(index_object.get()['Body'].read().decode('utf-8'))
        except:
            socket_map = {}
        sockets_to_remove = []
        for socket_id, socket_url in socket_map.items():
            try:
                apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=socket_url)
                apigatewaymanagementapi.post_to_connection(ConnectionId=socket_id, Data=bytes(event['message'], 'utf-8'))
            except:
                sockets_to_remove.append(socket_id)
        if sockets_to_remove:
            socket_map = json.loads(index_object.get()['Body'].read().decode('utf-8'))
            for socket_id in sockets_to_remove:
                if socket_id in socket_map:
                    del socket_map[socket_id]
            index_object.put(Body=bytes(json.dumps(socket_map), 'utf-8'), ContentType='application/json')
            

        
        
        
