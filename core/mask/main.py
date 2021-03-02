import json, boto3, base64

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 

def main(event, context):
    '''
    - triggered by core/request, trigger/version, trigger/index, trigger/connection-record, trigger/connection-index
    - event = {'connection_id': '', 'entity_type': '', 'method': '', ?'path': [], ?'class_name': '', ?'entity_id': '', ?entity: {}, ?query_id}
    - given a connection_id and a record, writes the masked version of the record to _/connection/{connection_id}/record/{class_name}/{record_id}.json
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    masked_entity = None
    if env.get('connection_id'):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(env['bucket'])
        s3_client = boto3.client('s3')
        connection_object = bucket.Object('{data_root}/connection/{connection_id}/connect.json'.format(data_root=env['data_root'], connection_id=env['connection_id']))
        try:
            connection_record = json.loads(connection_object.get()['Body'].read().decode('utf-8'))
        except:
            connection_record = {'mask': {}}
        connection_mask = connection_record.get('mask', {})
        if connection_mask:
            if event.get('entity_type') and event.get('method'):
                lambda_client = boto3.client('lambda')
                if event['entity_type'] in ['asset', 'static'] and event.get('path'):
                    mask = connection_mask[event['entity_type']] if event['entity_type'] in connection_mask else connection_mask.get('*', {})
                    if type(mask) is dict:
                        mask = mask.get(event['method']) if event['method'] in mask else mask.get('*', {})
                    for p in event['path']:
                        if type(mask) is dict:
                            mask = mask.get(p) if p in mask else mask.get('*', {})
                    if event['entity_type'] == 'static' and event['path'][0:len(env['data_root'])] == env['data_root']:
                        allowed = False
                    else:
                        if not mask:
                            allowed = False
                        elif mask == '*':
                            allowed = True
                        elif type(mask) is dict:
                            allowed = all([json.loads(lambda_client.invoke(FunctionName=getprocessor(env, mask_name, 'extension', 'mask'), Payload=bytes(json.dumps({
                                'purpose': 'mask', 'path': event['path'], 'options': options}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8')) 
                                for mask_name, options in mask.items()])
                    return allowed
                elif event['entity_type'] == 'view' or all([event.get(k) for k in ['class_name', 'entity_id']]):
                    switches = {'entity_type': event['entity_type'], 'method': event['method'], 'class_name': event['class_name'], 'entity_id': event['entity_id']}
                    mask = connection_mask.get(switches['entity_type']) if switches['entity_type'] in connection_mask else connection_mask.get('*', {})
                    if type(mask) is dict:
                        mask = mask.get(switches['method']) if switches['method'] in mask else mask.get('*', {})
                    if type(mask) is dict and event['entity_type'] != 'view':
                        mask = mask.get(switches['class_name']) if switches['class_name'] in mask else mask.get('*', {})
                    masked_entity = {}
                    if type(event.get('entity')) is dict:
                        entity = event['entity']
                    else:
                        if event['entity_type'] == 'view':
                            entity_key = '{data_root}/{entity_type}/{entity_id}.json'.format(data_root=env['data_root'], entity_type=event['entity_type'], entity_id=event['entity_id'])
                        else:
                            entity_key = '{data_root}/{entity_type}/{class_name}/{entity_id}.json'.format(data_root=env['data_root'], entity_type=event['entity_type'], class_name=event['class_name'], entity_id=event['entity_id'])
                        entity = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=entity_key)['Body'].read().decode('utf-8'))
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
                            allowfields.extend(json.loads(lambda_client.invoke(FunctionName=getprocessor(env, mask_name, 'extension', 'mask'), Payload=bytes(json.dumps(mask_payload), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8')))
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
                    did_write = False
                    if masked_entity and event.get('write'):
                        writable_entity = {**masked_entity}
                        del writable_entity['__constrained']
                        if event['entity_type'] == 'view':
                            write_key = '{data_root}/connection/{connection_id}/view/{entity_id}.json'.format(data_root=env['data_root'], connection_id=env['connection_id'], entity_id=event['entity_id'])
                        else:
                            write_key = '{data_root}/connection/{connection_id}/{entity_type}/{class_name}/{entity_id}.json'.format(data_root=env['data_root'], connection_id=env['connection_id'], entity_type=event['entity_type'], class_name=event['class_name'], entity_id=event['entity_id'])
                        current_writable_entity_json = s3_client.get_object(Bucket=env['bucket'], Key=write_key)['Body'].read().decode('utf-8')
                        new_writable_entity_json = json.dumps(writable_entity)
                        if current_writable_entity_json != new_writable_entity_json:
                            bucket.put_object(Body=bytes(json.dumps(writable_entity), 'utf-8'), Key=write_key, ContentType='application/json')
                            did_write = True
                    if event.get('query_id'):
                        index_key = '{data_root}/connection/{connection_id}/query/{class_name}/{query_id}/{index}.json'.format(
                            data_root=env['data_root'], connection_id=env['connection_id'], class_name=event['class_name'], query_id=event['query_id'], index=event['entity_id'][0])
                        try:
                            index_record_ids = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=index_key)['Body'].read().decode('utf-8'))
                        except:
                            index_record_ids = []
                        index_changed = False
                        if masked_entity and event['entity_id'] not in index_record_ids:
                            index_record_ids.append(event['entity_id'])
                            index_changed = True
                        elif not masked_entity and event['entity_id'] in index_record_ids:
                            index_record_ids.remove(event['entity_id'])
                            index_changed = True
                        index_record_ids.sort()
                        bucket.put_object(Body=bytes(json.dumps(index_record_ids), 'utf-8'), Key=index_key, ContentType='application/json')
    return masked_entity
