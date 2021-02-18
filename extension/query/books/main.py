import json, boto3, hashlib

def main(event, context):
    '''
    - triggered by query
    - event => {'purpose': 'query', 'record': {}, 'options': {}}
    - an example query to return various slices of book records
    - returns True if the given record matches the query
    '''
    result = False
    if event.get('purpose') == 'query' and type(event.get('record')) is dict and type(event.get('options', {})) is dict:
        book = event['record']
        options = event['options']
        if options.get('pagesFilter'):
            result = (book.get('numberOfPages', 0) >= options.get('minPages', 0)) and (book.get('numberOfPages', 0) <= options.get('maxPages', 1000))
    return result