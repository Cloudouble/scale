import json, boto3, hashlib, base64

def main(event, context):
    '''
    - triggered by administrator to initialise a new installation
    - event => {key: '', ?name: ''}
    - returns True when complete
    '''
    env = context.client_context.env
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8'))
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    if event.get('key'):
        sudo_module_path = '{data_root}/system/authentication/sudo.json'.format(data_root=env['data_root'])
        sudo_module_data = {'processor': '{}-extension-authentication-sudo'.format(env['lambda_namespace']), 'options': {
            'name': event.get('name', 'system'), 
            'key': hashlib.sha512(bytes(event.get('key'), 'utf-8')).hexdigest()
        }}
        bucket.put_object(Body=bytes(json.dumps(sudo_module_data), 'utf-8'), Key=sudo_module_path, ContentType='application/json')
        hashlib.sha512(bytes(event.get('key'), 'utf-8')).hexdigest()
    return True