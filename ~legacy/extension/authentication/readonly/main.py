import json, boto3, base64

def main(event, context):
    '''
    - triggered by core/authentication
    - event => {credentials: {}, options: {types: []}}
    - returns a connection object with (at least) a 'mask' property, which is overlaid onto _/connection/{connection_id}/connect.json to enable readonly access to the specified record types
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    connection_record = {'name': event['options'].get('name', 'public'), 'mask': {'record': {'GET': {}}}}
    connection_record['mask']['record']['GET'] = {t: '*' for t in event.get('options', {}).get('types', [])}
    return connection_record
