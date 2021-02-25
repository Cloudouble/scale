import json, boto3, base64

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
        
def write_view(view_result, result_key, bucket, s3_client, env):
    if type(view_result) is dict and view_result.get('body'):
        content_type = view_result.get('content_type', 'application/json')
        encoding = view_result.get('encoding', 'text')
        body = view_result.get('body', '')
        body = bytes(body, 'utf-8') if encoding == 'text' else base64.b64decode(body)
        try: 
            existing_view_bytes = s3_client.get_object(Bucket=env['bucket'], Key=result_key)['Body'].read()
        except:
            existing_view_bytes = bytes('', 'utf-8')
        if existing_view_bytes != body:
            bucket.put_object(Body=body, Key=result_key, ContentType=content_type)
        return True
    else: 
        return False
    

def main(event, context):
    '''
    - triggered by react-feed.py, react-subscription.py, react-view.py, react-connection-record.py, react-connection-index.py
    - event => {'class_name': '', 'entity_type': '',  'entity_id': '' 
        'view': {view='', processor='', ?options={}, ?assets={alias: assetpath}, ?field_name='', ?content_type='', ?suffix='', ?expires=0, ?sort_field='', ?sort_direction='', ?min_index=0, ?max_index=0}}
    - runs the given view with the given masked record/query results and writes the result to the relevant view path(s)
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    if all([event.get(k) for k in ['class_name', 'entity_type', 'entity_id']]) and type(event.get('view')) is dict:
        class_name, entity_type, entity_id, view_local = [event[k] for k in ['class_name', 'entity_type', 'entity_id', 'view']]
        if view_local.get('view'):
            view_system = json.loads(bucket.Object('{data_root}/view/{view_id}.json'.format(data_root=env['data_root'], view_id=view_local['view'])).get()['Body'].read().decode('utf-8'))
        else:
            view_system = {}
        assets = {**view_system.get('assets', {}), **view_local.get('assets', {})}
        options = {**view_system.get('options', {}), **view_local.get('options', {})}
        view = {**view_system, **view_local}
        view['assets'] = assets
        view['options'] = options
        if view and type(view.get('processor')) is str:
            suffix = view.get('suffix', 'json')
            field_name = view.get('field_name')
            if view.get('assets'):
                for asset_path in view['assets'].values():
                    if lambda_client.invoke(FunctionName='{lambda_namespace}-core-mask'.format(lambda_namespace=env['lambda_namespace']), Payload=bytes(json.dumps({'entity_type': 'asset', 'path': asset_path, 'method': 'GET'}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'):
                        bucket.copy({'Bucket': env['bucket'], 'Key': '{data_root}/asset/{asset_path}'.format(data_root=env['data_root'], asset_path=asset_path)}, 
                            '{data_root}/connection/{connection_id}/asset/{asset_path}'.format(connection_id=env['connection_id'], asset_path=asset_path))
            if entity_type == 'record':
                masked_record_data = json.loads(bucket.Object('{data_root}/connection/{connection_id}/record/{class_name}/{entity_id}.json'.format(data_root=env['data_root'], connection_id=env['connection_id'], class_name=class_name, entity_id=entity_id)).get()['Body'].read().decode('utf-8'))
                if field_name:
                    view_result_key = '{data_root}/connection/{connection_id}/subscription/{class_name}/{entity_id}/{field_name}.{suffix}'.format(data_root=env['data_root'], connection_id=env['connection_id'], class_name=class_name, entity_id=entity_id, field_name=field_name, suffix=suffix)
                else:
                    view_result_key = '{data_root}/connection/{connection_id}/subscription/{class_name}/{entity_id}.{suffix}'.format(data_root=env['data_root'], connection_id=env['connection_id'], class_name=class_name, entity_id=entity_id, suffix=suffix)
                try:
                    view_result = json.loads(lambda_client.invoke(FunctionName='{lambda_namespace}-extension-view-{processor}'.format(lambda_namespace=env['lambda_namespace'], processor=view['processor']), Payload=bytes(json.dumps({
                        'options': view['options'], 
                        'assets': view['assets'], 
                        'entity_type': 'record', 
                        'class_name': class_name, 
                        'entity_id': entity_id, 
                        'field_name': field_name, 
                        'suffix': suffix, 
                        'field_name': field_name, 
                        'entity': masked_record_data
                    }), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                except:
                    view_result = {}
                if write_view(view_result, view_result_key, bucket, s3_client, env):
                    counter = counter + 1
            elif entity_type == 'query':
                query_base_key = '{data_root}/connection/{connection_id}/query/{class_name}/{entity_id}/'.format(data_root=env['data_root'], connection_id=env['connection_id'], class_name=class_name, entity_id=entity_id)
                query_index_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=query_base_key)
                query_record_ids = []
                for query_index_entry in query_index_list_response.get('Contents', []):
                    query_record_ids.extend(json.loads(s3_client.get_object(Bucket=env['bucket'], Key=query_index_entry['Key'])['Body'].read().decode('utf-8')))
                query_record_ids.sort()
                query_record_data = []
                for record_id in query_record_ids:
                    query_record_data.append(json.loads(bucket.Object('{data_root}/connection/{connection_id}/record/{class_name}/{record_id}.json'.format(data_root=env['data_root'], connection_id=env['connection_id'], class_name=class_name, record_id=record_id)).get()['Body'].read().decode('utf-8')))
                sort_field = view.get('sort_field', '@id')
                sort_direction = view.get('sort_direction', 'ascending')
                query_record_data.sort(key=lambda r: r[sort_field], reverse=(True if sort_direction == 'descending' else False))
                total_result_count = len(query_record_data) 
                query_record_data = query_record_data[view.get('min_index'):view.get('max_index')]
                view_result_count = len(query_record_data) 
                for page_name, page_results in {'{}-{}'.format(i*1000, i*1000+999): p for i, p in enumerate(list(chunks(query_record_data, 1000)))}.items():
                    page_object_key = '{data_root}/connection/{connection_id}/feed/{class_name}/{entity_id}/{field_name}/{sort_field}/{sort_direction}/{page_name}.{suffix}'.format(
                        data_root=env['data_root'], connection_id=env['connection_id'], class_name=class_name, entity_id=entity_id, field_name=(field_name if field_name else '-'), 
                        sort_field=sort_field, sort_direction=sort_direction, page_name=page_name, suffix=suffix)
                    try:
                        view_result = json.loads(lambda_client.invoke(FunctionName='{lambda_namespace}-extension-view-{processor}'.format(lambda_namespace=env['lambda_namespace'], processor=view['processor']), Payload=bytes(json.dumps({
                            'options': view['options'], 
                            'assets': view['assets'], 
                            'entity_type': 'query',
                            'class_name': class_name, 
                            'entity_id': entity_id, 
                            'field_name': field_name, 
                            'sort_field': sort_field, 
                            'sort_direction': event.get('sort_direction', 'ascending'), 
                            'page_name': page_name, 
                            'suffix': suffix, 
                            'page': page_results, 
                            'total_result_count': total_result_count, 
                            'view_result_count': view_result_count
                        }), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                    except:
                        view_result = {}
                    if write_view(view_result, page_object_key, bucket, s3_client, env):
                        counter = counter + 1
    return counter
