import json, boto3, base64

def main(event, context):
    '''
    - triggered by query
    - event => {'record': {}, 'options': {}}
    - an example query to return various slices of book records
    - returns True if the given record matches the query
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    result = False
    if type(event.get('record')) is dict and type(event.get('options', {})) is dict:
        book = event['record']
        options = event['options']
        if options.get('pagesFilter'):
            result = (book.get('numberOfPages', 0) >= options.get('minPages', 0)) and (book.get('numberOfPages', 0) <= options.get('maxPages', 1000))
    return result