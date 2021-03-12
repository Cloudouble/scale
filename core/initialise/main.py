import json, boto3, base64, hashlib


def main(event, context):
    '''
    - triggered by administrator to initialise a new installation
    - event => {key: '', ?name: ''}
    - returns True when complete
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    if event.get('key'):
        sudo_module_path = '{data_root}/system/authentication/sudo.json'.format(data_root=env['data_root'])
        sudo_module_data = {'processor': 'sudo', 'options': {
            'name': event.get('name', 'system'), 
            'key': hashlib.sha512(bytes(event.get('key'), 'utf-8')).hexdigest()
        }}
        bucket.put_object(Body=bytes(json.dumps(sudo_module_data), 'utf-8'), Key=sudo_module_path, ContentType='application/json')
        hashlib.sha512(bytes(event.get('key'), 'utf-8')).hexdigest()
    return True