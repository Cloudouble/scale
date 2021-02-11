import json, boto3, os, time

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main(event, context):
    '''
    - triggered by react-feed.py, react-subscription.py, react-view.py, react-connection-record.py, react-connection-index.py
    - runs the given view with the given masked record/query results and writes the result to the relevant view path(s)
    event => {'connection_id': '', 'class_name': '', 'entity_type': '',  'entity_id': '' 'view_configuration': {view_id='', ?expires=0}}
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    if event.get('connection_id') and event.get('class_name') and event.get('entity_type') and event.get('entity_id') and type(event.get('view_configuration')) is dict and event['view_configuration'].get('view_id'):
        connection_id, class_name, entity_type, entity_id, view_configuration = [event[k] for k in ['connection_id', 'class_name', 'entity_type', 'entity_id', 'view_configuration']]
        view_data = json.loads(bucket.Object('_/view/{}.json'.format(view_configuration['view_id'])).get()['Body'].read().decode('utf-8'))
        if view_data and type(view_data.get('processor')) is str:
            # {processor='', ?options={}, ?assets={alias: assetpath}}
            if view_data.get('assets'):
                for asset_alias, asset_path in view_data['assets']:
                    if lambda_client.invoke(FunctionName='mask', Payload=bytes(json.dumps({'connection_id': connection_id, 'entity_type': 'asset', 'path': asset_path, 'method': 'GET'}), 'utf-8'))['Payload'].read().decode('utf-8'):
                        bucket.copy({'Bucket': os.environ['bucket'], 'Key': '_/asset/{}'.format(asset_path)}, '/_connection/{connection_id}/asset/{asset_path}'.format(connection_id=connection_id, asset_path=asset_path))
            if entity_type == 'record':
                masked_record_data = json.loads(bucket.Object('_/connection/{connection_id}/record/{class_name}/{entity_id}.json'.format(connection_id=connection_id, class_name=class_name, entity_id=entity_id)).get()['Body'].read().decode('utf-8'))
                field_name = None
                if view_data.get('field_name'):
                    field_name = view_data['field_name']
                    view_result_key = '/connection/{connection_id}/subscription/{class_name}/{entity_id}/{field_name}.{suffix}'.format(connection_id=connection_id, class_name=class_name, entity_id=entity_id, field_name=field_name, suffix=view_data.get('suffix', 'json'))
                else:
                    view_result_key = '/connection/{connection_id}/subscription/{class_name}/{entity_id}.{suffix}'.format(connection_id=connection_id, class_name=class_name, entity_id=entity_id, suffix=view_data.get('suffix', 'json'))
                bucket.put_object(Body=lambda_client.invoke(FunctionName=view_data['processor'], Payload=bytes(json.dumps({
                    'options': view_data.get('options', {}), 
                    'assets': view_data.get('assets', {}), 
                    'entity_type': 'record', 
                    'entity': masked_record_data, 
                    'field_name': field_name
                }), 'utf-8'))['Payload'].read(), Key=view_result_key, ContentType=view_data.get('content_type', 'application/json'))
                
            
    
    
    
    
    
    
    
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
