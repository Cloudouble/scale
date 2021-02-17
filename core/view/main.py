env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3, time

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main(event, context):
    '''
    - triggered by react-feed.py, react-subscription.py, react-view.py, react-connection-record.py, react-connection-index.py
    - runs the given view with the given masked record/query results and writes the result to the relevant view path(s)
    event => {'connection_id': '', 'class_name': '', 'entity_type': '',  'entity_id': '' 
        'view': {view='', processor='', ?options={}, ?assets={alias: assetpath}, ?field_name='', ?content_type='', ?suffix='', ?expires=0, ?sort_field='', ?sort_direction='', ?min_index=0, ?max_index=0}}
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    if all([event.get(k) for k in ['connection_id', 'class_name', 'entity_type', 'entity_id']]) and type(event.get('view')) is dict:
        connection_id, class_name, entity_type, entity_id, view_local = [event[k] for k in ['connection_id', 'class_name', 'entity_type', 'entity_id', 'view']]
        if view_local.get('view'):
            view_system = json.loads(bucket.Object('{system_root}/view/{view_id}.json'.format(system_root=env['system_root'], view_id=view_local['view'])).get()['Body'].read().decode('utf-8'))
        else:
            view_system = {}
        assets = {**view_system.get('assets', {}), **view_local.get('assets', {})}
        options = {**view_system.get('options', {}), **view_local.get('options', {})}
        view = {**view_system, **view_local}
        view['assets'] = assets
        view['options'] = options
        
        # {processor='', ?options={}, ?assets={alias: assetpath}, ?field_name='', ?content_type='', ?suffix='', ?expires=0, 
        #                   ?sort_field='', ?sort_direction='', ?min_index=0, ?max_index=0}
            
        if view and type(view.get('processor')) is str:
            suffix = view.get('suffix', 'json')
            field_name = view.get('field_name')
            if view.get('assets'):
                for asset_path in view['assets'].values():
                    if lambda_client.invoke(FunctionName='{lambda_namespace}-core-mask'.format(lambda_namespace=env['lambda_namespace']), Payload=bytes(json.dumps({'connection_id': connection_id, 'entity_type': 'asset', 'path': asset_path, 'method': 'GET'}), 'utf-8'))['Payload'].read().decode('utf-8'):
                        bucket.copy({'Bucket': env['bucket'], 'Key': '{system_root}/asset/{asset_path}'.format(system_root=env['system_root'], asset_path=asset_path)}, 
                            '{system_root}/connection/{connection_id}/asset/{asset_path}'.format(connection_id=connection_id, asset_path=asset_path))
            if entity_type == 'record':
                masked_record_data = json.loads(bucket.Object('{system_root}/connection/{connection_id}/record/{class_name}/{entity_id}.json'.format(system_root=env['system_root'], connection_id=connection_id, class_name=class_name, entity_id=entity_id)).get()['Body'].read().decode('utf-8'))
                if field_name:
                    view_result_key = '{system_root}/connection/{connection_id}/subscription/{class_name}/{entity_id}/{field_name}.{suffix}'.format(system_root=env['system_root'], connection_id=connection_id, class_name=class_name, entity_id=entity_id, field_name=field_name, suffix=suffix)
                else:
                    view_result_key = '{system_root}/connection/{connection_id}/subscription/{class_name}/{entity_id}.{suffix}'.format(system_root=env['system_root'], connection_id=connection_id, class_name=class_name, entity_id=entity_id, suffix=suffix)
                bucket.put_object(Body=lambda_client.invoke(FunctionName='{lambda_namespace}-extension-view-{processor}'.format(lambda_namespace=env['lambda_namespace'], processor=view['processor']), Payload=bytes(json.dumps({
                    'options': view['options'], 
                    'assets': view['assets'], 
                    'entity_type': 'record', 
                    'entity': masked_record_data, 
                    'field_name': field_name
                }), 'utf-8'))['Payload'].read(), Key=view_result_key, ContentType=view.get('content_type', 'application/json'))
                counter = counter + 1
            elif entity_type == 'query':
                query_base_key = '{system_root}/connection/{connection_id}/query/{class_name}/{entity_id}/'.format(system_root=env['system_root'], connection_id=connection_id, class_name=class_name, entity_id=entity_id)
                query_index_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=query_base_key)
                query_record_ids = []
                for query_index_entry in query_index_list_response.get('Contents', []):
                    query_record_ids.extend(json.loads(s3_client.get_object(Bucket=env['bucket'], Key=query_index_entry['Key'])['Body'].read().decode('utf-8')))
                query_record_ids.sort()
                query_record_data = []
                for record_id in query_record_ids:
                    query_record_data.append(json.loads(bucket.Object('{system_root}/connection/{connection_id}/record/{class_name}/{record_id}.json'.format(system_root=env['system_root'], connection_id=connection_id, class_name=class_name, record_id=record_id)).get()['Body'].read().decode('utf-8')))
                sort_field = view.get('sort_field', '@id')
                query_record_data.sort(key=lambda r: r[sort_field], reverse=(True if view.get('sort_direction', 'ascending') == 'descending' else False))
                total_result_count = len(query_record_data) 
                query_record_data = query_record_data[view.get('min_index'):view.get('max_index')]
                view_result_count = len(query_record_data) 
                for page_name, page_results in {'{}-{}'.format(i*1000, i*1000+999): p for i, p in enumerate(list(chunks(query_record_data, 1000)))}.items():
                    switches = {'connection_id': connection_id, 'class_name': class_name, 'entity_id': entity_id, 'field_name': field_name, 
                        'sort_field': sort_field, 'sort_direction': event.get('sort_direction', 'ascending'), 'page_name': page_name, 'suffix': suffix}
                    if field_name:
                        page_object_key = '{system_root}/connection/{connection_id}/feed/{class_name}/{entity_id}/{field_name}/{sort_field}/{sort_direction}/{page_name}.{suffix}'.format(system_root=env['system_root'], **switches)
                    else:
                        page_object_key = '{system_root}/connection/{connection_id}/feed/{class_name}/{entity_id}/-/{sort_field}/{sort_direction}/{page_name}.{suffix}'.format(system_root=env['system_root'], **switches)
                    
                    view_return = lambda_client.invoke(FunctionName='{lambda_namespace}-extension-view-{processor}'.format(lambda_namespace=env['lambda_namespace'], processor=view['processor']), Payload=bytes(json.dumps({
                        'options': view['options'], 
                        'assets': view['assets'], 
                        'entity_type': 'query',
                        'switches': switches, 
                        'page': page_results, 
                        'total_result_count': total_result_count, 
                        'view_result_count': view_result_count
                    }), 'utf-8'))['Payload'].read().decode('utf-8')
                    bucket.put_object(Body=bytes(json.loads(view_return), 'utf-8'), Key=page_object_key, ContentType=view.get('content_type', 'application/json'))
                counter = counter + 1
    return counter
