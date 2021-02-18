import json, boto3

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')


def main(event, context):
    '''
    - triggered by writes at /subscription/{class_name}/{record_id}/{connection_id}/*
    - trigger view.py from the subscription
    '''
    env = context.client_context.env
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8'))
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for event_entry in event['Records']:
        path = getpath(event_entry['s3']['object']['key'])
        class_name, record_id, connection_id = path[1:4]
        view = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event_entry['s3']['object']['key'])['Body'].read().decode('utf-8'))
        lambda_client.invoke(FunctionName='{lambda_namespace}-core-view'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps({
            'connection_id': connection_id,
            'class_name': class_name, 
            'entity_type': 'record', 
            'entity_id': record_id, 
            'view': view
        }), 'utf-8'), ClientContext=client_context)
        counter = counter + 1
    return counter    