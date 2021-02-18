env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3, hashlib

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['system_root']):] if p.startswith(env['system_root']) else p
    p = p[:len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

 
def main(event, context):
    '''
    - triggered by administrator to initialise a new installation
    - event => {key: '', ?name: ''}
    - returns True when complete
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')

    if event.get('key'):
        sudo_module_path = '{system_root}/system/authentication/sudo.json'.format(system_root=env['system_root'])
        sudo_module_data = {'processor': '{}-extension-authentication-sudo'.format(env['lambda_namespace']), 'options': {
            'name': event.get('name', 'system'), 
            'key': hashlib.sha512(bytes(event.get('key'), 'utf-8')).hexdigest()
        }}
        bucket.put_object(Body=bytes(json.dumps(sudo_module_data), 'utf-8'), Key=sudo_module_path, ContentType='application/json')
        hashlib.sha512(bytes(event.get('key'), 'utf-8')).hexdigest()

    return True