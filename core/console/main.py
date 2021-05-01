env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "LiveElementScale"}

import json, boto3, base64, hashlib, time


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
            if page == 'tests':
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

                    
                            
                    

    
    return retval
