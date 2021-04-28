env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "LiveElementScale"}

import json, boto3, base64, time, uuid

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
    - triggered by edge/socket on a POST request
    - lists each channel index and triggers edge/channel-send for each index
    '''
    if uuid_valid(event.get('channel')) and event.get('message'):
        origin = event.get('origin')
        if env['shared'] == 1 and origin:
            data_root = '{origin}/{system_root}'.format(origin=origin, system_root=env['system_root'])
        elif str(env['shared']) == '0':
            data_root = env['system_root']
        else:
            data_root = None
        if data_root:
            lambda_client = boto3.client('lambda')
            s3_client = boto3.client('s3')
            channel_indexes = s3_client.list_objects_v2(Bucket=env['bucket'], MaxKeys=5000,  Prefix='{data_root}/channel/{channel_id}/'.format(data_root=data_root, channel_id=event['channel']))['Contents']
            for channel_index in channel_indexes:
                if not channel_index['Key'].endswith('/connect.json'):
                    lambda_client.invoke(FunctionName=getprocessor(env, 'send', 'edge', 'channel'), Payload=bytes(json.dumps({'index': channel_index['Key'], 'message': event['message']}), 'utf-8'), InvocationType='Event')
                
