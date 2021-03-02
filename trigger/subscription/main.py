import json, boto3, base64

def getpath(p, env=None):
    p = p.strip('/?')
    if env and env.get('data_root'):
        p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def get_env_context(event, context):
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    env['path'] = getpath(event['key'], env)
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    return env, client_context

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 

def main(event, context):
    '''
    - triggered by writes at _/subscription/{class_name}/{record_id}/{connection_id}/*
    - trigger core/view from the subscription
    '''
    counter = 0
    if event.get('key'):
        s3 = boto3.resource('s3')
        s3_client = boto3.client('s3')
        lambda_client = boto3.client('lambda')
        env, client_context = get_env_context(event, context)    
        class_name, record_id, connection_id = env['path'][1:4]
        view = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8'))
        lambda_client.invoke(FunctionName=getprocessor(env, 'view'), InvocationType='Event', Payload=bytes(json.dumps({
            'class_name': class_name, 
            'entity_type': 'record', 
            'entity_id': record_id, 
            'view': view, 
            '_env': {**env, 'connection_id': connection_id}
        }), 'utf-8'))
        counter = counter + 1
    return counter    