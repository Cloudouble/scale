import json, boto3, base64

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

 
def main(event, context):
    '''
    - triggered by write.py
    - event => {authentication_channel_name: {credentials}}
    - takes care of authentication sub-processes
    - returns a connection object with (at least) a 'mask' property, which is overlaid onto _/connection/{connection_id}.json
    '''
    env = context.client_context.env
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8'))
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    connection_record = {'mask': {}}
    system_configuration = {'authentication': []}
    system_authentication_base_key = '{data_root}/system/authentication/'.format(data_root=env['data_root'])
    system_authentication_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=system_authentication_base_key)
    for authentication_module_entry in system_authentication_list_response['Contents']:
        module_name =  getpath(authentication_module_entry['Key'])[-1]
        system_configuration['authentication'].append({module_name: json.loads(bucket.Object(authentication_module_entry['Key']).get()['Body'].read().decode('utf-8'))})
    system_configuration['authentication'].sort(key=lambda a: a.get('priority', 1000))
    for authentication_channel in system_configuration['authentication']:
        authentication_channel_name, authentication_channel_config = list(authentication_channel.items())[0]
        if type(event.get(authentication_channel_name)) is dict and authentication_channel_config.get('processor'):
            authentication_payload = {'credentials': event[authentication_channel_name], 'options': authentication_channel_config.get('options', {})}
            authentication_channel_result = json.loads(lambda_client.invoke(FunctionName='{lambda_namespace}-extension-authentication-{processor}'.format(lambda_namespace=env['lambda_namespace'], processor=authentication_channel_config['processor']), InvocationType='RequestResponse', Payload=bytes(json.dumps(authentication_payload), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
            if authentication_channel_result and type(authentication_channel_result) is dict and type(authentication_channel_result.get('mask')) is dict:
                connection_record = authentication_channel_result
                break
    return connection_record
