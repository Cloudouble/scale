import json, boto3, hashlib

def main(event, context):
    '''
    - triggered by authentication.py
    - takes care of authentication sub-processes
    - returns a connection object with (at least) a 'mask' property, which is overlaid onto _/connection/{connection_id}.json
    event => {authentication_channel_name: {credentials}}
    '''
    connection_record = {'name': '', 'mask': {}}
    if event.get('credentials') and event.get('options'):
        if hashlib.sha512(bytes(event['credentials'].get('key', ''), 'utf-8')).hexdigest() == event['options'].get('key'):
            connection_record = {'name': event['options'].get('user_name', 'system'), 'mask': {'*': '*'}}
    return connection_record
