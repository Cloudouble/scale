import json, boto3, os, time

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main(event, context):
    # called by other functions to generate views on given connections and queries {connection_id, class_name, query_id, views}
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    connection_object = bucket.Object('_/connection/{connection}.json'.format(connection=event['connection_id']))
    try:
        connection_record = connection_object.get()['Body'].read().decode('utf-8')
    except:
        connection_record = {'mask': {}}
    mask = connection_record.get('mask', {})
    mask = mask.get('query') if 'query' in mask else mask.get('*', {})
    mask = mask.get('GET') if 'GET' in mask else mask.get('*', {})
    mask = mask.get(event['class_name']) if event['class_name'] in mask else mask.get('*', {})
    
    default_view_base_key = '_/connection/{connection_id}/view/{class_name}/{query_id}/id/ascending/'.format(connection_id=event['connection_id'], class_name=event['class_name'], query_id=event['query_id'])
    query_index_base_key = '_/query/{class_name}/{query_id}/'
    
    query_index_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=query_index_base_key)
    query_record_ids = []
    for query_index_entry in query_index_list_response['Contents']:
        query_record_ids.extend(json.loads(bucket.get_object(Key=query_index_entry['Key'])['Body'].read().decode('utf-8')))
    query_record_ids.sort()
    for page_name, page_results in {'{}-{}'.format(i*1000, i*1000+999) for i, p in enumerate(list(chunks(query_record_ids, 1000)))}:
        masked_page_results = []
        for record_id in page_results:
            masked_page_results.append(json.loads(lambda_client.invoke(FunctionName='mask', Payload=bytes(json.dumps({
                'connection_id': event['connection_id'], 
                'entity_type': 'record', 
                'method': 'GET',
                'class_name': event['class_name'], 
                'entity_id': record_id, 
                'entity': json.loads(bucket.Object('_/record/{class_name}/{record_id}.json'.format(class_name=event['class_name'], record_id=record_id)).get()['Body'].read().decode('utf-8'))
            }), 'utf-8'))['Payload'].read().decode('utf-8')))
        page_object = bucket.Object('_/connection/{connection_id}/view/{class_name}/{query_id}/id/ascending/{}.json'.format(page_name))
        page_object.put(Body=bytes(json.dumps(masked_page_results), 'utf-8'), ContentType='application/json')

    
    
    
    

    
    
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
