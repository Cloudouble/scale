env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "LiveElementScale"}

import json, boto3, base64, hashlib, time
from wsgiref.handlers import format_date_time

def run_test(test_path, test_field, test_value, start_time, s3_client):
    end_time = 0
    count = 1000
    retval = {'timing': None, 'confirmation': {}}
    while count and not end_time:
        try:
            if test_path.endswith('.json'):
                test_record = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/{test_path}'.format(data_root=env['data_root'], test_path=test_path))['Body'].read().decode('utf-8'))
            elif not test_field:
                test_record = s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/{test_path}'.format(data_root=env['data_root'], test_path=test_path))['Body'].read().decode('utf-8')
            else:
                test_record = {}
        except:
            test_record = {}
        if any([
            test_record and (test_field is None) and (not test_path.endswith('.json')) and test_value and (test_record == test_value), 
            test_record and (test_field is None) and test_path.endswith('.json'), 
            (not test_record) and (test_field is False), 
            test_field and type(test_record) is dict and test_record and type(test_field) is str and test_record.get(test_field) == test_value, 
            test_field and type(test_record) is dict and test_record and type(test_field) is str and type(test_value) is type and type(test_record.get(test_field)) == test_value, 
            test_field and type(test_record) is dict and test_record and type(test_field) is str and test_value is True and test_record.get(test_field), 
            test_field and type(test_record) is dict and test_record and type(test_field) is str and test_value is False and not test_record.get(test_field), 
            ]):
            end_time = time.time()
            retval['timing'] = int(end_time*1000 - start_time*1000)
            retval['confirmation'] = test_record
        count = count - 1
        time.sleep(0.1)
    return retval


def main(event, context):
    '''
    - triggered directly by the console client
    - event => {authentication_channel_name: {credentials}}
    '''
    #print(json.dumps(event))
    start_time = time.time()
    key = event.get('_key')
    env['data_root'] = '{host}/{system_root}'.format(host=event.get('host', ''), system_root=env['system_root']).strip('/')
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    retval = {'timing': None, 'confirmation': {}}
    if key:
        s3_client = boto3.client('s3')
        try:
            sudo_authmodule = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/system/authentication/sudo.json'.format(data_root=env['data_root']))['Body'].read().decode('utf-8'))
        except:
            sudo_authmodule = {}
        if hashlib.sha512(bytes(key, 'utf-8')).hexdigest() == sudo_authmodule.get('options', {}).get('key'):
            page = event.get('page')
            if page == 'system':
                table = event.get('table')
                if table == 'environment':
                    retval = env
            elif page == 'tests':
                test = event.get('test')
                result = event.get('result')
                context = event.get('context', {})
                if test == 'create-sudo-connection':
                    retval = run_test('connection/{connection_id}/connect.json'.format(connection_id=result), None, result, start_time, s3_client)
                elif test == 'create-websocket':
                    if context.get('create-sudo-connection'):
                        retval = run_test('connection/{connection_id}/connect.json'.format(connection_id=context['create-sudo-connection']), 'socket_url', str, start_time, s3_client)
                elif test == 'create-record-put':
                    retval = run_test('record/Book/{record_id}.json'.format(record_id=result), None, result, start_time, s3_client)
                elif test == 'delete-record':
                    retval = run_test('record/Book/{record_id}.json'.format(record_id=result), False, result, start_time, s3_client)
                elif test == 'create-view':
                    retval = run_test('view/{view_id}.json'.format(view_id=result), None, result, start_time, s3_client)
                elif test == 'create-query':
                    retval = run_test('query/Book/{query_id}.json'.format(query_id=result), None, result, start_time, s3_client)
                elif test == 'create-record-post':
                    retval = run_test('record/Book/{record_id}.json'.format(record_id=result), None, result, start_time, s3_client)
                elif test == 'create-subscription':
                    inputs = [context.get('create-record-post'), context.get('create-sudo-connection'), result]
                    if all(inputs):
                        retval = run_test('subscription/Book/{0}/{1}/{2}.json'.format(*inputs), None, result, start_time, s3_client)
                elif test == 'create-feed':
                    inputs = [context.get('create-query'), context.get('create-sudo-connection'), result]
                    if all(inputs):
                        retval = run_test('feed/Book/{0}/{1}/{2}.json'.format(*inputs), None, result, start_time, s3_client)
                elif test == 'update-record-field-put':
                    if context.get('create-record-post'):
                        retval = run_test('record/Book/{record_id}.json'.format(record_id=context['create-record-post']), 'numberOfPages', result, start_time, s3_client)
                elif test == 'create-bookreadonly-mask':
                    pass
                elif test == 'create-readonly-authentication-extension':
                    retval = run_test('system/authentication/{module_id}.json'.format(module_id=result), None, result, start_time, s3_client)
                elif test == 'create-bookreadonly-connection':
                    retval = run_test('connection/{connection_id}/connect.json'.format(connection_id=result), None, result, start_time, s3_client)
                elif test == 'delete-bookreadonly-connection':
                    retval = run_test('connection/{connection_id}/connect.json'.format(connection_id=result), False, result, start_time, s3_client)
                elif test == 'create-tunnel':
                    retval['confirmation'] = False
                elif test == 'send-tunnel':
                    retval['confirmation'] = False
                elif test == 'create-channel':
                    retval = run_test('channel/{channel_id}/connect.json'.format(channel_id=result), None, result, start_time, s3_client)
                elif test == 'subscribe-channel':
                    retval['confirmation'] = ' ---error--- '
                elif test == 'send-channel':
                    retval['confirmation'] = False
                elif test == 'delete-channel':
                    retval = run_test('channel/{channel_id}/connect.json'.format(channel_id=result), False, result, start_time, s3_client)
                elif test == 'create-daemon':
                    time.sleep(10)
                    retval = run_test('system/daemon/{module_id}.json'.format(module_id=result), 'state', 'installed', start_time, s3_client)
                elif test == 'run-daemon':
                    time.sleep(10)
                    retval = run_test('system/daemon/{module_id}.json'.format(module_id=context['create-daemon']), 'state', 'running', start_time, s3_client)
                elif test == 'pause-daemon':
                    time.sleep(10)
                    retval = run_test('system/daemon/{module_id}.json'.format(module_id=context['create-daemon']), 'state', 'paused', start_time, s3_client)
                elif test == 'remove-daemon':
                    time.sleep(10)
                    retval = run_test('system/daemon/{module_id}.json'.format(module_id=context['create-daemon']), 'state', 'removed', start_time, s3_client)
                elif test == 'create-418-error':
                    retval = run_test('error/418.html', None, result, start_time, s3_client)
                elif test == 'create-custom-class':
                    time.sleep(10)
                    retval = run_test('system/class/{class_name}.json'.format(class_name=result), 'label', result, start_time, s3_client)
                elif test == 'create-custom-record':
                    retval = run_test('record/Novel/{record_id}.json'.format(record_id=result), None, result, start_time, s3_client)
                elif test == 'install-schema':
                    retval = run_test('system/schema/{schema_id}.json'.format(schema_id=result), '@context', dict, start_time, s3_client)
                elif test == 'uninstall-schema':
                    retval = run_test('system/schema/{schema_id}.json'.format(schema_id=result), False, result, start_time, s3_client)
                elif test == 'install-package':
                    retval = run_test('system/package/{package_id}.json'.format(package_id=result), None, None, start_time, s3_client)
                elif test == 'uninstall-package':
                    retval = run_test('system/package/{package_id}.json'.format(package_id=result), False, result, start_time, s3_client)
                elif test == 'build-snapshot':
                    retval = run_test('system/snapshot/{snapshot_id}.json'.format(snapshot_id=result), None, None, start_time, s3_client)
            elif page == 'ide':
                retval = {}
                entity_type = event.get('entity_type')
                heading = event.get('heading')
                if entity_type == 'channel': 
                    if heading == 'search':
                        search = event.get('search')
                        input_name = event.get('input_name')
                        retval = {'search': search, 'result': {}}
                        if input_name == '@id':
                            channels = s3_client.list_objects_v2(Bucket=env['bucket'], MaxKeys=1000,  Prefix='{data_root}/channel/{search}'.format(data_root=env['data_root'], search=search))['Contents']
                            try:
                                channels = {c['Key'].split('/')[-2]: json.loads(s3_client.get_object(Bucket=env['bucket'], Key=c['Key'])['Body'].read().decode('utf-8')) for c in channels if c['Key'].endswith('/connect.json')}
                            except:
                                channels = {}
                            retval['result'] = channels
                        elif input_name == 'load':
                            channel_id = event.get('@id')
                            if channel_id:
                                try: 
                                    channel_obj = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/channel/{channel_id}/connect.json'.format(data_root=env['data_root'], channel_id=channel_id))['Body'].read().decode('utf-8'))
                                    retval = {'@id': channel_id, **channel_obj}
                                except:
                                    retval = {'@id': channel_id}
                                print(retval)
                elif entity_type in ['asset', 'static']: 
                    if heading == 'search':
                        search = event.get('search')
                        input_name = event.get('input_name')
                        retval = {'search': search, 'result': {}}
                        if input_name == 'path':
                            prefix = '{data_root}/asset/{search}'.format(data_root=env['data_root'], search=search) if entity_type == 'asset' else search
                            try:
                                assets = s3_client.list_objects_v2(Bucket=env['bucket'], MaxKeys=100,  Prefix=prefix)['Contents']
                                try:
                                    if entity_type == 'asset':
                                        assets = {a['Key'].replace('{}/{}'.format(env['data_root'], 'asset'), '', 1).strip('/'): {k: v.timestamp() if k == 'LastModified' else v for k, v in s3_client.head_object(Bucket=env['bucket'], Key=a['Key']).items() if k in ['ContentType', 'ContentLength', 'LastModified'] } for a in assets}
                                    elif entity_type == 'static':
                                        assets = {a['Key'].strip('/'): {k: format_date_time(v.timestamp()) if k == 'LastModified' else v for k, v in s3_client.head_object(Bucket=env['bucket'], Key=a['Key']).items() if k in ['ContentType', 'ContentLength', 'LastModified'] } for a in assets  if not a['Key'].startswith(env['system_root'])}
                                except:
                                    assets = {}
                            except:
                                assets = {}
                            retval['result'] = assets
                        elif input_name == 'load':
                            path = event.get('path')
                            if path:
                                try: 
                                    if entity_type == 'asset':
                                        asset_obj = s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/asset/{path}'.format(data_root=env['data_root'], path=path))
                                    elif entity_type == 'static' and not path.startswith(env['system_root']):
                                        asset_obj = s3_client.get_object(Bucket=env['bucket'], Key='{path}'.format(path=path))
                                    retval = {
                                        'path': path, 
                                        'Content-Type': asset_obj['ContentType'], 'Content-Length': asset_obj['ContentLength'], 'Last-Modified': format_date_time(asset_obj['LastModified'].timestamp()), 
                                        'body': base64.b64encode(asset_obj['Body'].read()).decode('utf-8')
                                    }
                                except:
                                    retval = {
                                        'path': path
                                    }
                elif entity_type == 'classes':
                    classes = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/system/class/index.json'.format(data_root=env['data_root']))['Body'].read().decode('utf-8'))
                    for class_name in classes:
                        classes[class_name]['label'] = classes[class_name].get('comment')
                        del classes[class_name]['comment']
                    retval = classes
                elif entity_type == 'record':
                    input_name = event.get('input_name')
                    class_name = event.get('@type')
                    if heading == 'search':
                        if class_name and input_name:
                            if input_name == '@id' and 'search' in event:
                                retval = {'search': event['search'], 'result': []} 
                                prefix = '{data_root}/record/{class_name}/{search}'.format(data_root=env['data_root'], class_name=class_name, search=event['search'])
                                try:
                                    retval['result'] = s3_client.list_objects_v2(Bucket=env['bucket'], MaxKeys=1000,  Prefix=prefix)['Contents']
                                except:
                                    retval['result'] = []
                                try:
                                    retval['result'] = [e['Key'].split('/')[-1].replace('.json', '') for e in retval['result']]
                                except:
                                    retval['result'] = []
                            elif input_name == 'load' and event.get('@id'):
                                record_uuid = event['@id']
                                record = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/record/{class_name}/{record_uuid}.json'.format(data_root=env['data_root'], class_name=class_name, record_uuid=record_uuid))['Body'].read().decode('utf-8'))
                                retval = record
                    elif heading == 'edit':
                        if record_type:
                            class_definition = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/system/class/{class_name}.json'.format(data_root=env['data_root'], class_name=class_name))['Body'].read().decode('utf-8'))
                            properties = class_definition.get('properties', {})
                            for property_name, property_types in properties.items():
                                property_definition = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/system/property/{property_name}.json'.format(data_root=env['data_root'], property_name=property_name))['Body'].read().decode('utf-8'))
                                class_definition['properties'][property_name] = {'label': property_definition.get('comment', ''), 'types': property_types}
                            retval = class_definition
                        elif event.get('datatypes'):
                            datatypes = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/system/datatype/index.json'.format(data_root=env['data_root']))['Body'].read().decode('utf-8'))
                            for type_name in datatypes:
                                datatypes[type_name]['label'] = datatypes[type_name].get('comment')
                                del datatypes[type_name]['comment']
                            retval = datatypes

                        

    return retval

