import json, boto3, os, time

def main(event, context):
    # called by other functions to generate views on given connections and queries
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    
    default_view_key = '_/connection/{connection_id}/view/{class_name}/{query_id}/id/ascending/0-999.json'.format(
        connection_id=event['connection_id'], class_name=event['class_name'], query_id=event['query_id'])
    
    
    
    '''
    view['sort_field'] = view.get('sort_field', '@id')
    view['sort_direction'] = view['sort_direction'] if view.get('sort_direction') in ['ascending', 'descending'] else 'ascending'
    view['min_index'] = view.get('min_index', 0)
    try:
        view['min_index'] = int(view['min_index'])
    except:
        view['min_index'] = 0
    view['max_index'] = view.get('max_index', 1000)
    try:
        view['max_index'] = int(view['max_index'])
    except:
        view['max_index'] = 1000
    if view['max_index'] <= view['min_index']:
        view['max_index'] = view['min_index'] + 1
    view['view_id'] = view.get('view_id', 'json')
    '''
    
    view_key = '_/connection/{connection_id}/view/{class_name}/{query_id}/{sort_field}/{sort_direction}/{min_index}-{max_index}.{view_id}'.format(**event)
    
    
    return counter
