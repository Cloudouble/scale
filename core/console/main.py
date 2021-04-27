env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "LiveElementScale"}

import json, boto3, base64, hashlib, time


def run_test(test_path, test_field, test_value, start_time, s3_client):
    end_time = 0
    count = 1000
    retval = None
    while count and not end_time:
        try:
            test_record = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/{test_path}'.format(data_root=env['data_root'], test_path=test_path))['Body'].read().decode('utf-8'))
        except:
            test_record = {}
        if any([
            test_record and (test_field is None), 
            (not test_record) and (test_field is False), 
            test_field and type(test_record) is dict and test_record and type(test_field) is str and test_record.get(test_field) == test_value, 
            test_field and type(test_record) is dict and test_record and type(test_field) is str and type(test_value) is type and type(test_record.get(test_field)) == test_value, 
            test_field and type(test_record) is dict and test_record and type(test_field) is str and test_value is True and test_record.get(test_field), 
            test_field and type(test_record) is dict and test_record and type(test_field) is str and test_value is False and not test_record.get(test_field), 
            ]):
            end_time = time.time()
            retval = int(end_time*1000 - start_time*1000)
        count = count - 1
        time.sleep(0.1)
    return retval


def main(event, context):
    '''
    - triggered directly by the console client
    - event => {authentication_channel_name: {credentials}}
    '''
    start_time = time.time()
    key = event.get('_key')
    env['data_root'] = '{host}/{system_root}'.format(host=event.get('host', ''), system_root=env['system_root']).strip('/')
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    retval = {}
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
                    retval['timing'] = run_test('connection/{connection_id}/connect.json'.format(connection_id=result), None, result, start_time, s3_client)
                elif test == 'create-websocket':
                    if context.get('create-sudo-connection'):
                        retval['timing'] = run_test('connection/{connection_id}/connect.json'.format(connection_id=context['create-sudo-connection']), 'socket_url', str, start_time, s3_client)
                elif test == 'create-record-put':
                    retval['timing'] = run_test('record/Book/{record_id}.json'.format(record_id=result), None, result, start_time, s3_client)
                elif test == 'delete-record':
                    retval['timing'] = run_test('record/Book/{record_id}.json'.format(record_id=result), False, result, start_time, s3_client)
                elif test == 'create-view':
                    retval['timing'] = run_test('view/{view_id}.json'.format(view_id=result), None, result, start_time, s3_client)
                elif test == 'create-query':
                    retval['timing'] = run_test('query/Book/{query_id}.json'.format(query_id=result), None, result, start_time, s3_client)
                elif test == 'create-record-post':
                    retval['timing'] = run_test('record/Book/{record_id}.json'.format(record_id=result), None, result, start_time, s3_client)
                elif test == 'create-subscription':
                    inputs = [context.get('create-record-post'), context.get('create-sudo-connection'), result]
                    if all(inputs):
                        retval['timing'] = run_test('subscription/Book/{0}/{1}/{2}.json'.format(*inputs), None, result, start_time, s3_client)
                elif test == 'create-feed':
                    # feed/Book/0e351f63-f0e0-4c5d-ba53-9b794cb39355/d4d2618c-ca76-46f8-bb78-e327c5066f9f/fffbe95b-925a-4727-b066-cfebdfb30130.json
                    inputs = [context.get('create-query'), context.get('create-sudo-connection'), result]
                    if all(inputs):
                        retval['timing'] = run_test('feed/Book/{0}/{1}/{2}.json'.format(*inputs), None, result, start_time, s3_client)
                elif test == 'update-record-field-put':
                    if context.get('create-record-post'):
                        retval['timing'] = run_test('record/Book/{record_id}.json'.format(record_id=context['create-record-post']), 'numberOfPages', result, start_time, s3_client)
                            
                    

    
    return retval
