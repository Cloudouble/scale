import json, boto3, os, time

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main(event, context):
    '''
    - triggered by react-feed.py, react-subscription.py, react-view.py, react-connection-record.py, react-connection-index.py
    - runs the given view with the given masked record/query results and writes the result to the relevant view path(s)
    event => {'connection_id': '', 'class_name': '', 'entity_type': '',  'entity_id': '' 'view_configuration': {view_id='', ?field_name, ?expires=0, ?sort_field='', ?sort_direction='', ?min_index=0, ?max_index=0}}
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    if event.get('connection_id') and event.get('class_name') and event.get('entity_type') and event.get('entity_id') and type(event.get('view_configuration')) is dict and event['view_configuration'].get('view_id'):
        connection_id, class_name, entity_type, entity_id, view_configuration = [event[k] for k in ['connection_id', 'class_name', 'entity_type', 'entity_id', 'view_configuration']]
        view_data = json.loads(bucket.Object('_/view/{}.json'.format(view_configuration['view_id'])).get()['Body'].read().decode('utf-8'))
        if view_data and type(view_data.get('processor')) is str:
            # {processor='', ?options={}, ?assets={alias: assetpath}, ?content_type='', ?suffix=''}
            suffix = view_data.get('suffix', 'json')
            field_name = view_data.get('field_name')
            if view_data.get('assets'):
                for asset_path in view_data['assets'].values():
                    if lambda_client.invoke(FunctionName='{lambda_namespace}-core-mask'.format(lambda_namespace=env['lambda_namespace']), Payload=bytes(json.dumps({'connection_id': connection_id, 'entity_type': 'asset', 'path': asset_path, 'method': 'GET'}), 'utf-8'))['Payload'].read().decode('utf-8'):
                        bucket.copy({'Bucket': env['bucket'], 'Key': '_/asset/{}'.format(asset_path)}, '/_connection/{connection_id}/asset/{asset_path}'.format(connection_id=connection_id, asset_path=asset_path))
            if entity_type == 'record':
                masked_record_data = json.loads(bucket.Object('_/connection/{connection_id}/record/{class_name}/{entity_id}.json'.format(connection_id=connection_id, class_name=class_name, entity_id=entity_id)).get()['Body'].read().decode('utf-8'))
                if field_name:
                    view_result_key = '/connection/{connection_id}/subscription/{class_name}/{entity_id}/{field_name}.{suffix}'.format(connection_id=connection_id, class_name=class_name, entity_id=entity_id, field_name=field_name, suffix=suffix)
                else:
                    view_result_key = '/connection/{connection_id}/subscription/{class_name}/{entity_id}.{suffix}'.format(connection_id=connection_id, class_name=class_name, entity_id=entity_id, suffix=suffix)
                bucket.put_object(Body=lambda_client.invoke(FunctionName=view_data['processor'], Payload=bytes(json.dumps({
                    'options': view_data.get('options', {}), 
                    'assets': view_data.get('assets', {}), 
                    'entity_type': 'record', 
                    'entity': masked_record_data, 
                    'field_name': field_name
                }), 'utf-8'))['Payload'].read(), Key=view_result_key, ContentType=view_data.get('content_type', 'application/json'))
                counter = counter + 1
            elif entity_type == 'query':
                query_base_key = '_/connection/{connection_id}/query/{class_name}/{entity_id}/'.format(connection_id=connection_id, class_name=class_name, entity_id=entity_id)
                query_index_list_response = s3_client.list_objects_v2(Bucket=os.environ['bucket'], Prefix=query_base_key)
                query_record_ids = []
                for query_index_entry in query_index_list_response['Contents']:
                    query_record_ids.extend(json.loads(bucket.get_object(Key=query_index_entry['Key'])['Body'].read().decode('utf-8')))
                query_record_ids.sort()
                query_record_data = []
                for record_id in query_record_ids:
                    query_record_data.append(json.loads(bucket.Object('_/connection/{connection_id}/record/{class_name}/{record_id}.json'.format(connection_id=connection_id, class_name=class_name, record_id=record_id)).get()['Body'].read().decode('utf-8')))
                sort_field = view_configuration.get('sort_field', '@id')
                query_record_data.sort(key=sort_field, reverse=True if view_configuration.get('sort_direction', 'ascending') == 'descending' else False)
                total_result_count = len(query_record_data) 
                query_record_data = query_record_data[view_configuration.get('min_index'):view_configuration.get('max_index')]
                view_result_count = len(query_record_data) 
                for page_name, page_results in {'{}-{}'.format(i*1000, i*1000+999) for i, p in enumerate(list(chunks(query_record_data, 1000)))}:
                    switches = {'connection_id': connection_id, 'class_name': class_name, 'entity_id': entity_id, 'field_name': field_name, 'sort_field': sort_field, 'page_name': page_name, 'suffix': suffix}
                    if field_name:
                        page_object_key = '_/connection/{connection_id}/feed/{class_name}/{entity_id}/{field_name}/{sort_field}/{sort_direction}/{page_name}.{suffix}'.format(**switches)
                    else:
                        page_object_key = '_/connection/{connection_id}/feed/{class_name}/{entity_id}/-/{sort_field}/{sort_direction}/{page_name}.{suffix}'.format(**switches)
                    bucket.put_object(Body=lambda_client.invoke(FunctionName=view_data['processor'], Payload=bytes(json.dumps({
                        'options': view_data.get('options', {}), 
                        'assets': view_data.get('assets', {}), 
                        'entity_type': 'query',
                        'switches': switches, 
                        'page': page_results, 
                        'total_result_count': total_result_count, 
                        'view_result_count': view_result_count
                    }), 'utf-8'))['Payload'].read(), Key=page_object_key, ContentType=view_data.get('content_type', 'application/json'))
                counter = counter + 1
    return counter
