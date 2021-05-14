import json, boto3, base64, time, uuid

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 
def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

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
    

def main(event, context):
    '''
    - triggered by writes at _/channel/{channel_id}/message/{message_id} 
    - lists each channel index and triggers edge/channel-send for each index
    '''
    counter = 0
    env, client_context = get_env_context(event, context)
    s3_client = boto3.client('s3')
    if event.get('key') and env['path'] and len(env['path']) == 4 and env['path'][0] == 'channel' and env['path'][2] == 'message':
        channel_id = env['path'][1]
        message_id = env['path'][3]
        if uuid_valid(channel_id) and uuid_valid(message_id):
            try: 
                message = s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8')
            except:
                message = None
            if message:
                lambda_client = boto3.client('lambda')
                channel_indexes = s3_client.list_objects_v2(Bucket=env['bucket'], MaxKeys=2000,  Prefix='{data_root}/channel/{channel_id}/index/'.format(data_root=env['data_root'], channel_id=channel_id))['Contents']
                for channel_index in channel_indexes:
                    lambda_client.invoke(FunctionName=getprocessor(env, 'send', 'core', 'channel'), Payload=bytes(json.dumps({'index': channel_index['Key'], 'message': message}), 'utf-8'), InvocationType='Event')
                    counter = counter + 1
                s3_client.delete_object(Bucket=env['bucket'], Key=event['key'])
