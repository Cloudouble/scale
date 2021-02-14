env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3, os, base64, uuid, time
from urllib.parse import parse_qs

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

 
def main(event, context):
    '''
    - triggered as an endpoint for a CDN or API originated PUT / PATCH / POST / DELETE request, or a websocket $put/$post/$patch/$delete message
    - writes/deletes a connection configuration to ~connection/{connection_id}.json OR
    - writes/deletes a view configuration to /view/{view_id}.json via /connection/{connection_id}/view/{view_id}.json OR
    - writes/deletes an private asset to ~asset/{assetpath} via ~connection/{connection_id}/asset/{path}
    - writes/deletes an static asset to {path} via ~connection/{connection_id}/static/{path}
    - writes/deletes a query configuration to /query/{class_name}/{query_id}.json via /connection/{connection_id}/query/{class_name}/{query_id}.json  OR
    - writes/deletes a feed configuration to /feed/{class_name}/{query_id}/{connection_id}.json via /connection/{connection_id}/feed/{class_name}/{query_id}.json OR 
    - writes/deletes a subscription configuration to /subscription/{class_name}/{record_id}/{connection_id}.json via /connection/{connection_id}/subscription/{class_name}/{record_id}.json OR 
    - writes/deletes a system module configuration to /system/{scope}/{module}.json via /connection/{connection_id}/system/{scope}/{module}.json OR
    - writes a record to /record/{class_name}/{record_id}.json via /connection/{connection_id}/record/{class_name}/{record_id}.json
    - writes a record field to /record/{class_name}/{record_id}[field_name].json via /connection/{connection_id}/record/{class_name}/{record_id}/{field_name}.json
    - generates a version record at /version/{class_name}/{record_id}/{version_id}.json
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    if event.get('body'):
        #API Gateway - either Rest or Websocket
        request_objects = [{'cf': {'request': {
            'method': event['httpMethod'], 
            'body': {'data': event['body']}, 
            'uri': event['path']
        }}}]
    elif event.get('Records'):
        #CDN: PUT, POST or PATCH
        request_objects = event.get('Records', [])
    for request_object in [r['cf']['request'] for r in request_objects if r.get('cf', {}).get('request', {}).get('method', 'POST') in ['POST', 'PUT', 'PATCH', 'DELETE']]:
        body = base64.b64decode(request_object['body']['data']) if request_object.get('isBase64Encoded') else request_object['body']['data']
        try: 
            entity = json.loads(body)
        except: 
            entity = {k: v[0] for k, v in parse_qs(body).items()}
        path = request_object['uri'].strip('/?').replace('{}/'.format(env['system_root']), '').replace('.json', '').split('/')
        if path and path[0] == 'connection' and len(path) >= 2 and uuid_valid(path[1]):
            connection_id = path[1]
            if len(path) == 2:
                connection_object = bucket.Object('{system_root}/connection/{connection_id}.json'.format(system_root=env['system_root'], connection_id=connection_id))
                try:
                    connection_record = json.loads(connection_object.get()['Body'].read().decode('utf-8'))
                except:
                    connection_record = {'mask': {}}
                if request_object['method'] in ['POST', 'PUT', 'PATCH']:
                    if entity and type(entity) is dict and len(entity) == 1 and type(list(entity.values())[0]) is dict:
                        connection_record = {**connection_record, **json.loads(lambda_client.invoke(FunctionName='{}-authenticate'.format(env['lambda_namespace']), InvocationType='RequestResponse', Payload=bytes(json.dumps(entity), 'utf-8'))['Payload'].read().decode('utf-8'))}
                    connection_object.put(Body=bytes(json.dumps(connection_record), 'utf-8'), ContentType='application/json')
                    counter = counter + 1
                elif request_object['method'] == 'DELETE':
                    try:
                        connection_object.delete()
                        counter = counter + 1
                    except:
                        pass
            elif len(path) >= 4 and path[2] in ['asset', 'static']:
                # {connection_id, entity_type, path, method}
                usable_path = path[3:]
                allowed = json.loads(lambda_client.invoke(FunctionName='{}-mask'.format(env['lambda_namespace']), Payload=bytes(json.dumps({
                    'connection_id': connection_id, 
                    'entity_type': path[2], 
                    'method': request_object['method'], 
                    'path': usable_path
                }), 'utf-8'))['Payload'].read().decode('utf-8'))
                if allowed:
                    the_object = bucket.Object('{system_root}/asset/{usable_path}'.format(system_root=env['system_root'], usable_path='/'.join(usable_path))) if path[2] == 'asset' else bucket.Object('/'.join(usable_path))
                    canwrite = True
                    if request_object['method'] == 'PATCH':
                        try:
                            the_object.get()['Body'].read()
                        except:
                            canwrite = False
                    if canwrite:
                        if request_object['method'] in ['PUT', 'POST', 'PATCH']:
                            the_object.put(Body=bytes(body, 'utf-8'))
                        elif request_object['method'] == 'DELETE':
                            the_object.delete()
            elif len(path) >= 4:
                if len(path) == 4:
                    entity_type, entity_id = path[2:]
                    switches = {'entity_type': entity_type, 'entity_id': entity_id}
                    entity_key = '{system_root}/{entity_type}/{entity_id}.json'.format(system_root=env['system_root'], **switches)
                else:
                    entity_type, class_name, entity_id, record_field = (path[2:5] + [None])
                    switches = {'entity_type': entity_type, 'class_name': class_name, 'entity_id': entity_id}
                    entity_key = '{system_root}/{entity_type}/{class_name}/{entity_id}/{connection_id}.json'.format(system_root=env['system_root'], **switches, connection_id=connection_id) if entity_type in ['feed', 'subscription'] else '_/{entity_type}/{class_name}/{entity_id}.json'.format(**switches)
                try:
                    current_entity = s3.Object(os.environ['bucket'], entity_key).get()['Body'].read().decode('utf-8')
                except:
                    current_entity = {}
                if len(path) in [4, 5]:
                    entity_id, view_handle = (entity_id.split('.', 1) + ['json'])[:2]
                elif len(path) == 6:
                    record_field, view_handle = (path[5].split('.', 1) + ['json'])[:2]
                    if request_object['method'] in ['POST', 'PUT']:
                        entity = {record_field: entity}
                        request_object['method'] = 'POST'
                    elif request_object['method'] in ['DELETE', 'PATCH']:
                        if request_object['method'] == 'PATCH':
                            if current_entity:
                                entity = {record_field: entity}
                                request_object['method'] = 'POST'
                            else:
                                entity = {} 
                        elif request_object['method'] == 'DELETE':
                            entity = current_entity
                            del entity[record_field]
                            request_object['method'] = 'PUT'
                if view_handle == 'json' and request_object['method'] in ['POST', 'PUT', 'PATCH'] and json.loads(lambda_client.invoke(FunctionName='{}-validate'.format(env['lambda_namespace']), Payload=bytes(json.dumps({'entity': entity, 'switches': switches}), 'utf-8'))['Payload'].read().decode('utf-8')):
                    # {connection_id, entity_type, method, class_name, entity_id, entity}
                    masked_entity = json.loads(lambda_client.invoke(FunctionName='{}-mask'.format(env['lambda_namespace']), Payload=bytes(json.dumps({
                        'connection_id': connection_id, 
                        'entity_type': entity_type, 
                        'method': request_object['method'],
                        'class_name': class_name, 
                        'entity_id': entity_id, 
                        'entity': entity
                    }), 'utf-8'))['Payload'].read().decode('utf-8'))
                    constrained = masked_entity.get('__constrained', True)
                    del masked_entity['__constrained']
                    if masked_entity:
                        canwrite = bool(current_entity) if request_object['method'] == 'PATCH' else True
                        if canwrite:
                            if not constrained and request_object['method'] == 'PUT':
                                entity_to_write = {**masked_entity}
                            else:
                                entity_to_write = {**current_entity, **masked_entity}
                        if entity_to_write:
                            if request_object['method'] in ['PUT', 'POST', 'PATCH']:
                                updated_fields = [f for f in entity if entity[f] != current_entity.get(f)]
                                put_response = bucket.put_object(Body=bytes(json.dumps(entity_to_write), 'utf-8'), Key=entity_key, ContentType='application/json')
                                if entity_type == 'record':
                                    record_version_key = '{system_root}/version/{class_name}/{record_id}/{version_id}.json'.format(system_root=env['system_root'], class_name=entity['@type'], record_id=entity['@id'], version_id=put_response['VersionId'])
                                    bucket.put_object(Body=bytes(json.dumps(updated_fields), 'utf-8'), Key=record_version_key, ContentType='application/json')
                            elif request_object['method'] == 'DELETE' and current_entity:
                                if entity_type in ['query', 'record', 'view', 'feed', 'subscription', 'system']:
                                    current_entity.delete()
                            counter = counter + 1
    return counter
