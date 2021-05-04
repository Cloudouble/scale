env = {"bucket": "scale.live-element.net", "system_proper_name": "LiveElementScale", "account_id": "771795544492", "core_region": "ap-southeast-2", "lambda_role": "LiveElementScale", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": "0", "authentication_namespace": "liveelementscale"}

import json, boto3, base64, re

triggers = {
    'channel/{uuid}/connect.json': ['connection'], 
    'channel/{uuid}/message/{uuid}': ['channel'], 
    'connection/{uuid}/connect.json': ['connection'], 
    'daemon/{uuid}/connect.json': ['connection'], 
    'query/{class_name}/{uuid}.json': ['query'], 
    'query/{class_name}/{uuid}/[a-z0-9].json': ['index'], 
    'connection/{uuid}/record/{class_name}/{uuid}.json': ['connection-record'], 
    'connection/{uuid}/query/{class_name}/{uuid}/[a-z0-9].json': ['connection-index'], 
    'daemon/{uuid}/record/{class_name}/{uuid}.json': ['connection-record'], 
    'daemon/{uuid}/query/{class_name}/{uuid}/[a-z0-9].json': ['connection-index'], 
    'feed/{class_name}/{uuid}/{uuid}/{uuid}.json': ['feed'], 
    'subscription/{class_name}/{uuid}/{uuid}/{uuid}.json': ['subscription'], 
    'version/{class_name}/{uuid}/[a-zA-Z0-9\._-]+.json': ['version'], 
    'system/[a-z0-9\-]+/[a-zA-Z0-9\._\-]+.json': ['system']
}


def main(event_data, context):
    '''
    - triggered by all write events in main bucket
    - invokes other trigger functions according to their capturing path
    '''
    uuid_pattern = '[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}'
    class_pattern = '[a-zA-Z0-9]+'
    counter = 0
    keys = []
    for entry in event_data['Records']:
        if entry.get('s3', {}).get('object', {}).get('key'):
            keys.append(entry['s3']['object']['key'].strip('/?'))
    if keys:
        lambda_client = boto3.client('lambda')
    for key in keys:
        if env['shared'] == '1':
           key_split = key.split('/')
           if key_split[1] == env['system_root']:
               env['data_root'] = key_split[0]
           else:
               continue
        else:
           env['data_root'] = env['system_root']
        trigger_re_compiled = {k: re.compile('{data_root}/{path}'.format(data_root=env['data_root'], path=k.strip('/').format(uuid=uuid_pattern, class_name=class_pattern))) for k in triggers}
        for key_re, trigger_processors in triggers.items():
            if trigger_re_compiled[key_re].fullmatch(key):
                for trigger_processor in trigger_processors:
                    lambda_client.invoke(FunctionName=context.function_name.replace('-proxy', '-{}'.format(trigger_processor)), Payload=bytes(json.dumps({
                        'key': key, 
                        '_env': env
                    }), 'utf-8'), InvocationType='Event')
        counter = counter + 1
    return counter
