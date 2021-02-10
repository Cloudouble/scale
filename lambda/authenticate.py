import json, boto3, os


def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

 
def main(event, context):
    '''
    - triggered by write.py
    - takes care of authentication sub-processes
    - returns a connection object with (at least) a 'mask' property, which is overlaid onto _/connection/{connection_id}.json
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    lambda_client = boto3.client('lambda')
    connection_record = {'mask': {}}
    system_configuration = json.loads(bucket.Object('_/system/configuration.json').get()['Body'].read().decode('utf-8'))
    if system_configuration.get('authentication') and type(system_configuration['authentication']) is list and all([type(a) is dict and len(a) == 1 for a in system_configuration['authentication']]):
        for authentication_channel in system_configuration['authentication']:
            authentication_channel_name, authentication_channel_options = list(authentication_channel.items())[0]
            if type(event.get(authentication_channel_name)) is dict and event[authentication_channel_name] and event[authentication_channel_name].get('processor') and event.get(authentication_channel_name):
                authentication_payload = {'credentials': event[authentication_channel_name], 'options': event[authentication_channel_name].get('options', {})}
                authentication_channel_result = json.loads(lambda_client.invoke(FunctionName=event[authentication_channel_name]['processor'], InvocationType='RequestResponse', Payload=bytes(json.dumps(authentication_payload), 'utf-8'))['Payload'].read().decode('utf-8'))
                if authentication_channel_result and type(authentication_channel_result) is dict and type(authentication_channel_result.get('mask')) is dict:
                    connection_record = authentication_channel_result
                    break
    return connection_record
