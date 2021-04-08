import json, boto3, base64, uuid, hashlib

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True


def main(event, context):
    '''
    - called by other functions, including extensions to ensure writing is always done consistently
    - does the work of writing an object
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    counter = 0
    entity_type =  event.get('entity_type')
    method = event.get('method')
    if entity_type and method:
        connection_type = env.get('connection_type', 'connection')
        connection_id = env['connection_id']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(env['bucket'])
        if entity_type == 'connection' and event.get('entity'):
            entity = event['entity']
            connection_object = bucket.Object('{data_root}/{connection_type}/{connection_id}/connect.json'.format(data_root=env['data_root'], connection_type=connection_type, connection_id=connection_id))
            if method in ['POST', 'PUT', 'PATCH']:
                if entity.get('mask') and type(entity['mask']) is dict:
                    mask_hash = hashlib.sha512(bytes(json.dumps(entity['mask']), 'utf-8')).hexdigest()
                    mask_object = bucket.Object('{data_root}/mask/{mask_hash}.json'.format(data_root=env['data_root'], mask_hash=mask_hash))
                    mask_object.put(Body=bytes(json.dumps(entity['mask']), 'utf-8'), ContentType='application/json')
                    entity['mask'] = mask_hash
                connection_object.put(Body=bytes(json.dumps(entity), 'utf-8'), ContentType='application/json')
                counter = counter + 1
            elif method == 'DELETE':
                try:
                    connection_object.delete()
                    counter = counter + 1
                except:
                    pass
        elif entity_type in ['asset', 'static'] and event.get('path') and event.get('body') and event.get('content-type'):
            object_path = '{data_root}/asset/{path}'.format(data_root=env['data_root'], path=event['path']) if entity_type == 'asset' else event['path']
            the_object = bucket.Object(object_path)
            if method in ['PUT', 'POST', 'PATCH']:
                the_object.put(Body=base64.b64decode(event['body']), ContentType=event['content-type'])
                counter = counter + 1
            elif method == 'DELETE':
                try:
                    the_object.delete()
                    counter = counter + 1
                except:
                    pass
        elif entity_type == 'channel' and type(event.get('path')) is list and len(event['path']) == 3 and uuid_valid(event['path'][1]) and event.get('method') in ['PUT', 'DELETE']:
            object_path = '{data_root}/channel/{channel_id}/connect.json'.format(data_root=env['data_root'], channel_id=event['path'][1])
            the_object = bucket.Object(object_path)
            if event['method'] == 'PUT' and type(event.get('entity')) is dict:
                the_object.put(Body=bytes(json.dumps(event['entity']), 'utf-8'), ContentType='application/json')
                counter = counter + 1
            elif event['method'] == 'DELETE':
                try:
                    the_object.delete()
                    counter = counter + 1
                except:
                    pass
        else:
            s3_client = boto3.client('s3')
            entity = event.get('entity', {})
            entity_key = event.get('entity_key', {})
            current_entity = event.get('current_entity', None)
            if not current_entity:
                try:
                    current_entity = json.loads(s3.Object(env['bucket'], entity_key).get()['Body'].read().decode('utf-8'))
                except:
                    current_entity = {}
            if method in ['PUT', 'POST', 'PATCH']:
                if json.dumps(current_entity) != json.dumps(entity):
                    if entity_type == 'record':
                        updated_fields = sorted(list(set([f for f in entity if entity[f] != current_entity.get(f)] + [f for f in current_entity if current_entity[f] != entity.get(f)])))
                    put_response = bucket.put_object(Body=bytes(json.dumps(entity), 'utf-8'), Key=entity_key, ContentType='application/json')
                    version_id = put_response.version_id
                    if entity_type == 'record' and entity.get('@type') and entity.get('@id'):
                        record_version_key = '{data_root}/version/{class_name}/{record_id}/{version_id}.json'.format(data_root=env['data_root'], class_name=entity['@type'], record_id=entity['@id'], version_id=version_id)
                        bucket.put_object(Body=bytes(json.dumps(updated_fields), 'utf-8'), Key=record_version_key, ContentType='application/json')
                        for updated_field in updated_fields:
                            if current_entity.get(updated_field) is not None:
                                old_field_value_hash = hashlib.sha512(bytes(json.dumps(current_entity[updated_field]), 'utf-8')).hexdigest()
                                old_value_index_key = '{data_root}/index/{class_name}/{field_name}/{value_hash}/{record_id}.json'.format(
                                    data_root=env['data_root'], class_name=current_entity['@type'], field_name=updated_field, value_hash=old_field_value_hash, record_id=current_entity['@id']
                                )
                                try: 
                                    s3_client.delete_object(Bucket=env['bucket'], Key=old_value_index_key)
                                except:
                                    pass
                            if entity.get(updated_field) is not None:
                                new_field_value_hash = hashlib.sha512(bytes(json.dumps(entity[updated_field]), 'utf-8')).hexdigest()
                                new_value_index_key = '{data_root}/index/{class_name}/{field_name}/{value_hash}/{record_id}.json'.format(
                                    data_root=env['data_root'], class_name=entity['@type'], field_name=updated_field, value_hash=new_field_value_hash, record_id=entity['@id']
                                )
                                bucket.put_object(Body=bytes(json.dumps(version_id), 'utf-8'), Key=new_value_index_key, ContentType='application/json')
                    counter = counter + 1
            elif method == 'DELETE' and current_entity:
                if entity_type in ['query', 'record', 'view', 'feed', 'subscription', 'system', 'mask']:
                    s3_client.delete_object(Bucket=env['bucket'], Key=entity_key)
                    if entity_type == 'record' and entity.get('@type') and entity.get('@id'):
                        updated_fields = sorted([f for f in current_entity])
                        record_version_key = '{data_root}/version/{class_name}/{record_id}/{version_id}.json'.format(data_root=env['data_root'], class_name=entity['@type'], record_id=entity['@id'], version_id='-deleted-')
                        bucket.put_object(Body=bytes(json.dumps(updated_fields), 'utf-8'), Key=record_version_key, ContentType='application/json')
                        counter = counter + 1
    return counter
