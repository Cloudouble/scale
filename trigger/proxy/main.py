import json, boto3, base64, re

env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "liveelementscale"}

triggers = {
    
}

def main(event_data, context):
    '''
    - triggered by all write events in bucket
    - invokes other trigger functions according to their capturing path
    '''
    counter = 0
    keys = []
    for entry in event_data['Records']:
        if entry.get('s3', {}).get('object', {}).get('key'):
            keys.append(entry['s3']['object']['key'].strip('/?'))
    if keys:
        trigger_re_compiled = {k: re.compile(k) for k in triggers}
        lambda_client = boto3.client('lambda')
    for key in keys:
        if env['shared']:
           key_split = key.split('/')
           if key_split[1] == env['system_root']:
               env['data_root'] = key_split[0]
           else:
               continue
        else:
           env['data_root'] = env['system_root']
        for key_re, trigger_processors in triggers.items():
            if trigger_re_compiled[key_re].fullmatch(key):
                for trigger_processor in trigger_processors:
                    lambda_client.invoke(FunctionName=context.function_name.replace('-proxy', '-{}'.format(trigger_processor)), Payload=bytes(json.dumps({
                        'key': key, 
                        '_env': env
                    }), 'utf-8'), InvocationType='Event')
        counter = counter + 1
    return counter
