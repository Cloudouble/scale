import json, boto3, base64, hashlib

def main(event, context):
    '''
    - triggered by core/authentication
    - event => {credentials: {key: ''}, options: {key: ''}}
    - returns a connection object with (at least) a 'mask' property, which is overlaid onto _/connection/{connection_id}.json to enable administrator access
    - remove this function completely to disable administrator access
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    connection_record = {'name': '', 'mask': {}}
    if event.get('credentials') and event.get('options'):
        if hashlib.sha512(bytes(event['credentials'].get('key', ''), 'utf-8')).hexdigest() == event['options'].get('key'):
            connection_record = {'@name': event['options'].get('@name', 'system'), 'mask': {'*': '*'}}
    return connection_record
