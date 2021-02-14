env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3, time

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main(event, context):
    '''
    - triggered by write.py, react-version.py, react-index.py, react-connection-record.py, react-connection-index.py
    - given a connection_id and a record, writes the masked version of the record to /connection/{connection_id}/record/{class_name}/{record_id}.json
    event = {'connection_id': '', 'entity_type': '', 'method': '', ?'path': [], ?'class_name': '', ?'entity_id': '', ?entity: {}}
    '''
    masked_entity = None
    if event.get('connection_id'):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(env['bucket'])
        connection_object = bucket.Object('{system_root}/connection/{connection_id}.json'.format(system_root=env['system_root'], connection_id=event['connection_id']))
        try:
            connection_record = json.loads(connection_object.get()['Body'].read().decode('utf-8'))
        except:
            connection_record = {'mask': {}}
        connection_mask = connection_record.get('mask', {})
        if connection_mask:
            if event.get('entity_type') and event.get('method'):
                lambda_client = boto3.client('lambda')
                if event['entity_type'] in ['asset', 'static'] and event.get('path'):
                    # event = {connection_id, entity_type, path, method}
                    mask = connection_mask.get(event['entity_type']) if event['entity_type'] in mask else mask.get('*', {})
                    if type(mask) is dict:
                        mask = mask.get(event['method']) if event['method'] in mask else mask.get('*', {})
                    for p in event['path']:
                        if type(mask) is dict:
                            mask = mask.get(p) if p in mask else mask.get('*', {})
                    if event['entity_type'] == 'static' and event['path'][0:len(env['system_root'])] == env['system_root']:
                        allowed = False
                    else:
                        if not mask:
                            allowed = False
                        elif mask == '*':
                            allowed = True
                        elif type(mask) is dict:
                            allowed = all([json.loads(lambda_client.invoke(FunctionName='{lambda_namespace}-{mask_name}'.format(lambda_namespace=lambda_namespace, mask_name=mask_name), Payload=bytes(json.dumps({
                                'purpose': 'mask', 'connection_id': event['connection_id'], 'path': event['path'], 'options': options}), 'utf-8'))['Payload'].read().decode('utf-8')) 
                                for mask_name, options in mask.items()])
                    return allowed
                elif all([event.get(k) for k in ['class_name', 'entity_id']]):
                    # event = {connection_id, entity_type, method, class_name, entity_id, entity}
                    s3 = boto3.resource('s3')
                    bucket = s3.Bucket(env['bucket'])
                    lambda_client = boto3.client('lambda')
                    switches = {'entity_type': event['entity_type'], 'method': event['method'], 'class_name': event['class_name'], 'entity_id': event['entity_id']}
                    mask = connection_mask.get(switches['entity_type']) if switches['entity_type'] in connection_mask else connection_mask.get('*', {})
                    if type(mask) is dict:
                        mask = mask.get(switches['method']) if switches['method'] in mask else mask.get('*', {})
                    if type(mask) is dict:
                        mask = mask.get(switches['class_name']) if switches['class_name'] in mask else mask.get('*', {})
                    masked_entity = {}
                    if type(event.get('entity')) is dict:
                        entity = event['entity']
                    else:
                        entity = json.loads(bucket.get_object(Key='{system_root}/{entity_type}/{class_name}/{entity_id}.json'.format(system_root=env['system_root'], entity_type=event['entity_type'], class_name=event['class_name'], entity_id=event['entity_id']))['Body'].read().decode('utf-8'))
                    constrained = True
                    allowfields = []
                    if not mask:
                        mask = {}
                    elif mask == '*':
                        constrained = False
                        mask = {}
                    for mask_name, options in mask.items():
                        options = options if type(options) is dict else {}
                        if constrained:
                            mask_payload = {'purpose': 'mask', 'entity': entity, 'connection_id': event['connection_id'], 'switches': switches, 'options': options}
                            allowfields.extend(json.loads(lambda_client.invoke(FunctionName=mask_name, Payload=bytes(json.dumps(mask_payload), 'utf-8'))['Payload'].read().decode('utf-8')))
                            if '*' in allowfields:
                                constrained = False
                                break
                        else:
                            break
                    if constrained:
                        for field in allowfields:
                            if field in entity:
                                masked_entity[field] = entity[field]
                    else:
                        masked_entity = {**entity, '__constrained': constrained}

    return masked_entity
