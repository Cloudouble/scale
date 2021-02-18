import json, boto3, hashlib

def main(event, context):
    '''
    - triggered by authentication
    - event => {credentials: {key: ''}, options: {key: ''}}
    - returns a connection object with (at least) a 'mask' property, which is overlaid onto _/connection/{connection_id}.json to enable administrator access
    - remove this function completely to disable administrator access
    '''
    connection_record = {'name': '', 'mask': {}}
    if event.get('credentials') and event.get('options'):
        if hashlib.sha512(bytes(event['credentials'].get('key', ''), 'utf-8')).hexdigest() == event['options'].get('key'):
            connection_record = {'name': event['options'].get('name', 'system'), 'mask': {'*': '*'}}
    return connection_record
