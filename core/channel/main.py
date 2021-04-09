env = 'scale.liveelement.net 0 _ liveelement-scale'

import json, boto3, base64, time

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 
def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True


def main(event, context):
    '''
    - triggered by edge/channel 
    - lists each channel index and triggers core/channel-send for each index
    '''
    bucket_name, shared, system_root, lambda_namespace = env.split(' ')
    if uuid_valid(event.get('channel')) and event.get('message'):
        host = event.get('host')
        if shared == '1' and host:
            data_root = '{host}/{system_root}'.format(host=host, system_root=system_root)
        elif shared == '0':
            data_root = system_root
        else:
            data_root = None
        if data_root:
            lambda_client = boto3.client('lambda')
            s3_client = boto3.client('s3')
            channel_indexes = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='{data_root}/channel/{channel_id}/'.format(data_root=data_root, channel_id=event['channel']))['Contents']
            for channel_index in channel_indexes:
                lambda_client.invoke(FunctionName=getprocessor({'lambda_namespace': lambda_namespace}, 'send', 'core', 'channel'), Payload=bytes(json.dumps({'index': channel_index['Key'], 'message': event['message']}), 'utf-8'), InvocationType='Event')
                
