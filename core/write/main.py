env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "liveelementscale"}

import json, boto3, os, base64, uuid, time
from urllib.parse import parse_qs

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

 
def main(event, context):
    '''
    - triggered as an endpoint for a CDN or API originated PUT / PATCH / POST / DELETE request, or a websocket $put/$post/$patch/$delete message
    - writes/deletes a connection configuration to _/connection/{connection_id}.json (finalised) OR
    - writes/deletes a view configuration to /view/{view_id}.json via /connection/{connection_id}/view/{view_id}.json (finalised) OR
    - writes/deletes an private asset to _/asset/{assetpath} via _/connection/{connection_id}/asset/{path} (finalised) OR
    - writes/deletes an static asset to {path} via ~connection/{connection_id}/static/{path} (finalised) OR
    - writes/deletes a query configuration to /query/{class_name}/{query_id}.json via /connection/{connection_id}/query/{class_name}/{query_id}.json (finalised) OR
    - writes/deletes a feed configuration to /feed/{class_name}/{query_id}/{connection_id}.json via /connection/{connection_id}/feed/{class_name}/{query_id}.json (finalised) OR 
    - writes/deletes a subscription configuration to /subscription/{class_name}/{record_id}/{connection_id}.json via /connection/{connection_id}/subscription/{class_name}/{record_id}.json (finalised) OR 
    - writes/deletes a system module configuration to /system/{scope}/{module}.json via /connection/{connection_id}/system/{scope}/{module}.json (finalised) OR
    - writes a record to /record/{class_name}/{record_id}.json via /connection/{connection_id}/record/{class_name}/{record_id}.json (finalised) OR 
    - writes a record field to /record/{class_name}/{record_id}[field_name].json via /connection/{connection_id}/record/{class_name}/{record_id}/{field_name}.json (finalised)
    - generates a version record at /version/{class_name}/{record_id}/{version_id}.json (finalised)
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
        body = bytes(request_object['body']['data'], 'utf-8') if request_object['body']['encoding'] == 'text' else base64.b64decode(request_object['body']['data'])
        content_type = request_object.get('headers', {}).get('content-type', [])
        if content_type and type(content_type[0]) is dict:
            content_type = content_type[0].get('value', 'application/json')
        else:
            content_type = 'application/json'
        if content_type == 'application/json':
            try: 
                entity = json.loads(body)
            except: 
                entity = {}
        elif content_type == 'application/x-www-form-urlencoded':
            try: 
                entity = {k: v[0] for k, v in parse_qs(body.decode('utf-8')).items()}
            except: 
                entity = {}
        else:
            entity = {}
        if env['shared']:
            host = request_object.get('headers', {}).get('host', {}).get('value')
        else: 
            host = ''
        env['data_root'] = '{host}/{system_root}'.format(host=host, system_root=system_root).strip('/')
        
        env['connection_id'] = None
        if request_object.get('headers', {}).get('cookie', {}).get('value'):
            raw_cookie = request_object['headers']['cookie']['value'].lower()
            cookie_name = '{authentication_namespace}connection'.format(authentication_namespace=env['authentication_namespace'])
            if cookie_name in raw_cookie:
                cookies = {c.split('=')[0]: c.split('=')[1] for c in c [raw_cookie.split('; ')]}
                if cookie_name in cookies: 
                    authorization_split = cookies[cookie_name].split(':')
                    env['connection_id'] = authorization_split[0]
        if not env['connection_id']:
            if request_object.get('headers', {}).get('authorization', {}).get('value'):
                authorization_header = request_object['headers']['authorization']['value']
                if authorization_header[0:6] == 'Basic ':
                    authorization_split = base64.b64decode(authorization_header[6:]).decode('utf-8').split(':')
                    env['connection_id'] = authorization_split[0]
        if not env['connection_id']:
            header_name = '{authentication_namespace}connection'.format(authentication_namespace=env['authentication_namespace'])
            if request_object.get('headers', {}).get(header_name, {}).get('value'):
                authorization_split = request_object['headers'][header_name]['value'].split(':')
                env['connection_id'] = authorization_split[0]
        env['path'] = []
        if not env['connection_id']:
            system_root_connection_prefix = '{system_root}/connection/'.format(env['system_root'])
            if request_object['uri'].startswith(system_root_connection_prefix):
                working_path_split = request_object['uri'][len(system_root_connection_prefix):].split('/')
                env['connection_id'] = working_path_split[0]
                p = '/'.join(working_path_split[1:]).strip('/?')
                p = p[:-len('.json')] if p.endswith('.json') else p
                env['path'] = p.strip('/').split('/')
        else:
            if request_object['uri'].startswith(system_root_connection_prefix):
                working_path_split = request_object['uri'][len(system_root_connection_prefix):].split('/')
                p = '/'.join(working_path_split[1:]).strip('/?')
                p = p[:-len('.json')] if p.endswith('.json') else p
                env['path'] = p.strip('/').split('/')
        client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8'))
        if env['path'] and uuid_valid(env['connection_id']):
            if len(path) == 1 and path[0] == 'connect':
                connection_object = bucket.Object('{data_root}/connection/{connection_id}.json'.format(data_root=env['data_root'], connection_id=connection_id))
                try:
                    connection_record = json.loads(connection_object.get()['Body'].read().decode('utf-8'))
                except:
                    connection_record = {'mask': {}}
                if request_object['method'] in ['POST', 'PUT', 'PATCH']:
                    if entity and type(entity) is dict and len(entity) == 1 and type(list(entity.values())[0]) is dict:
                        connection_record = {**connection_record, **json.loads(lambda_client.invoke(FunctionName='{}-core-authentication'.format(env['lambda_namespace']), InvocationType='RequestResponse', Payload=bytes(json.dumps(entity), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))}
                    connection_object.put(Body=bytes(json.dumps(connection_record), 'utf-8'), ContentType='application/json')
                    counter = counter + 1
                elif request_object['method'] == 'DELETE':
                    try:
                        connection_object.delete()
                        counter = counter + 1
                    except:
                        pass
            elif len(path) >= 2 and path[0] in ['asset', 'static']:
                usable_path = path[1:]
                allowed = json.loads(lambda_client.invoke(FunctionName='{}-core-mask'.format(env['lambda_namespace']), Payload=bytes(json.dumps({
                    'connection_id': connection_id, 
                    'entity_type': path[0], 
                    'method': request_object['method'], 
                    'path': usable_path
                }), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                if allowed:
                    the_object = bucket.Object('{data_root}/asset/{usable_path}'.format(data_root=env['data_root'], usable_path='/'.join(usable_path))) if path[0] == 'asset' else bucket.Object('/'.join(usable_path))
                    canwrite = True
                    if request_object['method'] == 'PATCH':
                        try:
                            the_object.get()['Body'].read()
                        except:
                            canwrite = False
                    if canwrite:
                        if request_object['method'] in ['PUT', 'POST', 'PATCH']:
                            the_object.put(Body=body, ContentType=content_type)
                        elif request_object['method'] == 'DELETE':
                            the_object.delete()
                        counter = counter + 1
            elif len(path) >= 2:
                if len(path) == 2:
                    entity_type, entity_id = path
                    switches = {'entity_type': entity_type, 'entity_id': entity_id}
                    entity_key = '{data_root}/{entity_type}/{entity_id}.json'.format(data_root=env['data_root'], **switches)
                else:
                    entity_type, class_name, entity_id, record_field = (path[0:3] + [None])
                    switches = {'entity_type': entity_type, 'class_name': class_name, 'entity_id': entity_id}
                    entity_key = '{data_root}/{entity_type}/{class_name}/{entity_id}/{connection_id}.json'.format(data_root=env['data_root'], **switches, connection_id=env['connection_id']) if entity_type in ['feed', 'subscription'] else '{data_root}/{entity_type}/{class_name}/{entity_id}.json'.format(data_root=env['data_root'], **switches)
                try:
                    current_entity = json.loads(s3.Object(env['bucket'], entity_key).get()['Body'].read().decode('utf-8'))
                except:
                    current_entity = {}
                if len(path) in [2, 3]:
                    entity_id, view_handle = (entity_id.split('.', 1) + ['json'])[:2]
                elif len(path) == 4:
                    if entity_type in ['subscription', 'feed']:
                        switches['record_id'] = entity_id
                        entity_id, view_handle = (path[3].split('.', 1) + ['json'])[:2]
                        switches['entity_id'] = entity_id
                        entity_key = '{data_root}/{entity_type}/{class_name}/{record_id}/{connection_id}/{entity_id}.json'.format(data_root=env['data_root'], **switches, connection_id=env['connection_id']) if entity_type in ['feed', 'subscription'] else '{data_root}/{entity_type}/{class_name}/{entity_id}.json'.format(data_root=env['data_root'], **switches)
                    else:
                        record_field, view_handle = (path[3].split('.', 1) + ['json'])[:2]
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
                        entity['@type'] = entity.get('@type', class_name)
                        entity['@id'] = entity.get('@id', entity_id)
                if entity_type == 'feed':
                    switches['query_id'] = switches['record_id']
                    del switches['record_id']
                elif entity_type == 'view':
                    class_name = None
                if view_handle == 'json' and request_object['method'] in ['POST', 'PUT', 'PATCH'] and json.loads(lambda_client.invoke(FunctionName='{}-core-validate'.format(env['lambda_namespace']), Payload=bytes(json.dumps({'entity': entity, 'switches': switches}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8')):
                    masked_entity = json.loads(lambda_client.invoke(FunctionName='{}-core-mask'.format(env['lambda_namespace']), Payload=bytes(json.dumps({
                        'entity_type': entity_type, 
                        'method': request_object['method'],
                        'class_name': class_name, 
                        'entity_id': entity_id, 
                        'entity': entity
                    }), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
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
                                if entity_type == 'record':
                                    updated_fields = [f for f in entity if entity[f] != current_entity.get(f)]
                                put_response = bucket.put_object(Body=bytes(json.dumps(entity_to_write), 'utf-8'), Key=entity_key, ContentType='application/json')
                                if entity_type == 'record':
                                    record_version_key = '{data_root}/version/{class_name}/{record_id}/{version_id}.json'.format(data_root=env['data_root'], class_name=entity['@type'], record_id=entity['@id'], version_id=put_response.version_id)
                                    bucket.put_object(Body=bytes(json.dumps(updated_fields), 'utf-8'), Key=record_version_key, ContentType='application/json')
                            elif request_object['method'] == 'DELETE' and current_entity:
                                if entity_type in ['query', 'record', 'view', 'feed', 'subscription', 'system']:
                                    current_entity.delete()
                            counter = counter + 1
    return counter
