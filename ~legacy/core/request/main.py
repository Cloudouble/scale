env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_", "shared": 0, "authentication_namespace": "LiveElementScale"}

import json, boto3, base64, uuid, hashlib, urllib

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
    
 
def main(event, context):
    '''
    - triggered by request objects written to the core request bucket
    - writes/deletes a connection configuration to _/connection/{connection_id}/connect.json (tested) OR
    - writes/deletes a view configuration to _/view/{view_id}.json via _/connection/{connection_id}/view/{view_id}.json (tested) OR
    - writes/deletes a mask to _/mask/{mask_id}.json via _/connection/{connection_id}/mask/{mask_id}.json (tested) OR
    - writes/deletes an private asset to _/asset/{assetpath} via _/connection/{connection_id}/asset/{path} (tested) OR
    - writes/deletes an static asset to {path} via _/connection/{connection_id}/static/{path} (tested) OR
    - writes/deletes a query configuration to _/query/{class_name}/{query_id}.json via _/connection/{connection_id}/query/{class_name}/{query_id}.json (tested) OR
    - writes/deletes a feed configuration to _/feed/{class_name}/{query_id}/{connection_id}.json via _/connection/{connection_id}/feed/{class_name}/{query_id}.json (tested) OR 
    - writes/deletes a subscription configuration to _/subscription/{class_name}/{record_id}/{connection_id}.json via _/connection/{connection_id}/subscription/{class_name}/{record_id}.json (tested) OR 
    - writes/deletes a system module configuration to _/system/{scope}/{module}.json via _/connection/{connection_id}/system/{scope}/{module}.json (tested) OR
    - writes a record to _/record/{class_name}/{record_id}.json via _/connection/{connection_id}/record/{class_name}/{record_id}.json (tested) OR 
    - writes a record field to _/record/{class_name}/{record_id}[field_name].json via _/connection/{connection_id}/record/{class_name}/{record_id}/{field_name}.json (tested)
    - generates a version record at _/version/{class_name}/{record_id}/{version_id}.json (tested)
    '''
    s3_client = boto3.client('s3')
    requests = []
    for entry in [ent for ent in [{**r.get('s3', {}).get('bucket', {}), **r.get('s3', {}).get('object', {})} for r in event.get('Records', [])] if ent.get('key') and ent.get('name')]:
        try:
            requests.append(json.loads(s3_client.get_object(Bucket=entry['name'], Key=entry['key'])['Body'].read().decode('utf-8')))
        except:
            pass
    if not requests:
        return 0
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    lambda_client = boto3.client('lambda')
    counter = 0
    for request in requests:
        host = request.get('headers', {}).get('host') if env['shared'] else ''
        env['data_root'] = '{host}/{system_root}'.format(host=host, system_root=env['system_root']).strip('/')
        env['connection_id'] = None
        if request.get('headers', {}).get('cookie'):
            raw_cookie = request['headers']['cookie'].lower()
            cookie_name = '{authentication_namespace}Connection'.format(authentication_namespace=env['authentication_namespace'])
            if cookie_name in raw_cookie:
                cookies = {c.split('=')[0]: c.split('=')[1] for c in c [raw_cookie.split('; ')]}
                if cookie_name in cookies: 
                    authorization_split = cookies[cookie_name].split(':')
                    env['connection_id'] = authorization_split[0]
        if not env['connection_id']:
            if request.get('headers', {}).get('authorization'):
                authorization_header = request['headers']['authorization']
                if authorization_header[0:6] == 'Basic ':
                    authorization_split = base64.b64decode(authorization_header[6:]).decode('utf-8').split(':')
                    env['connection_id'] = authorization_split[0]
        if not env['connection_id']:
            header_name = '{authentication_namespace}Connection'.format(authentication_namespace=env['authentication_namespace'])
            if request.get('headers', {}).get(header_name):
                authorization_split = request['headers'][header_name].split(':')
                env['connection_id'] = authorization_split[0]
        env['path'] = []
        root_connection_prefix = '{data_root}/connection/'.format(data_root=env['data_root'])
        if not env['connection_id']:
            if request['uri'].startswith(root_connection_prefix):
                working_path_split = request['uri'][len(root_connection_prefix):].split('/')
                env['connection_id'] = working_path_split[0][:-len('.json')] if working_path_split[0].endswith('.json') else working_path_split[0]
                p = '/'.join(working_path_split[1:]).strip('/?')
                p = p[:-len('.json')] if p.endswith('.json') else p
                env['path'] = p.strip('/').split('/')
        else:
            if request['uri'].startswith(root_connection_prefix):
                working_path_split = request['uri'][len(root_connection_prefix):].split('/')
                p = '/'.join(working_path_split[1:]).strip('/?')
                p = p[:-len('.json')] if p.endswith('.json') else p
                env['path'] = p.strip('/').split('/')
        client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
        if env['path'] and uuid_valid(env['connection_id']):
            if len(env['path']) == 1 and env['path'][0] == 'connect' and (request.get('entity') or request.get('method') == 'DELETE'):
                connection_object = bucket.Object('{data_root}/connection/{connection_id}/connect.json'.format(data_root=env['data_root'], connection_id=env['connection_id']))
                try:
                    connection_record = json.loads(connection_object.get()['Body'].read().decode('utf-8'))
                except:
                    connection_record = {}
                if request['method'] in ['POST', 'PUT', 'PATCH']:
                    if request.get('entity') and type(request['entity']) is dict and len(request['entity']) == 1 and type(list(request['entity'].values())[0]) is dict:
                        connection_record = {**connection_record, **json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'authentication'), Payload=bytes(json.dumps(request['entity']), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))}
                if request['method'] in ['POST', 'PUT', 'PATCH', 'DELETE']:
                    lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': 'connection', 'entity': connection_record, 'method': request['method'], '_env': env}), 'utf-8'), InvocationType='Event')
                    counter = counter + 1
            elif len(env['path']) == 3 and env['path'][0] == 'system' and env['path'][1] == 'schema':
                try:
                    schema_definition = json.loads(base64.b64decode(request['body']).decode('utf-8'))
                except:
                    schema_definition = {}
                if schema_definition:
                    allowed = json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'mask'), Payload=bytes(json.dumps({
                        'entity_type': 'schema', 'method': 'PUT', 'path': env['path']}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                    if allowed:
                        if type(schema_definition) is str:
                            try:
                                schema_definition = json.loads(urllib.request.urlopen(schema_definition).read().decode('utf-8'))
                            except:
                                pass
                        elif type(schema_definition) is dict:
                            pass
                        else:
                            schema_definition = None
                        if schema_definition and type(schema_definition) is dict:
                            is_valid =json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'validate'), Payload=bytes(json.dumps({
                            'entity': schema_definition, 
                            'entity_type': 'schema', 
                            'class_name': None, 
                            'entity_id': env['path'][2]}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                            if is_valid:
                                s3_client.put_object(
                                    Bucket=env['bucket'], 
                                    Body=bytes(json.dumps(schema_definition), 'utf-8'), 
                                    Key='{data_root}/system/schema/{schema_id}.json'.format(data_root=env['data_root'], schema_id=env['path'][2]), 
                                    ContentType='application/json'
                                )
                                counter = counter + 1
                elif not schema_definition and request['method'] == 'DELETE':
                    lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': 'system', 'method': 'DELETE', 'path': env['path'], 'entity_key': '{data_root}/system/schema/{schema_id}.json'.format(data_root=env['data_root'], schema_id=env['path'][2]), '_env': env}), 'utf-8'), InvocationType='Event')
            elif len(env['path']) == 3 and env['path'][0] == 'channel':
                channel_id = env['path'][1] if uuid_valid(env['path'][1]) else None
                channel_object = bucket.Object('{data_root}/channel/{channel_id}/connect.json'.format(data_root=env['data_root'], channel_id=channel_id))
                try:
                    channel_record = json.loads(channel_object.get()['Body'].read().decode('utf-8'))
                except:
                    channel_record = {}
                if request['method'] in ['PUT', 'DELETE']:
                    if request['method'] == 'PUT' and env['path'][2] == 'connect' and type(request['entity']) is dict and not channel_record and all([uuid_valid(request['entity'].get('{}Key'.format(k))) for k in ['receive', 'send', 'admin']]):
                        allowed = json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'mask'), Payload=bytes(json.dumps({
                            'entity_type': 'channel', 'method': 'PUT', 'path': env['path']}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                        if allowed:
                            lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': 'channel', 'entity': request['entity'], 'method': 'PUT', 'path': env['path']}), 'utf-8'), ClientContext=client_context)
                            counter = counter + 1
                    elif request['method'] == 'DELETE' and channel_record and uuid_valid(env['path'][2]):
                        allowed = json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'mask'), Payload=bytes(json.dumps({
                            'entity_type': 'channel', 'method': 'DELETE', 'path': env['path']}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                        if allowed and channel_record.get('adminKey') == env['path'][2]:
                            lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': 'channel', 'method': 'DELETE', 'path': env['path'], '_env': env}), 'utf-8'), InvocationType='Event')
                            counter = counter + 1
            elif len(env['path']) >= 2 and env['path'][0] in ['asset', 'static', 'error']:
                usable_path = env['path'][1:]
                entity_type = env['path'][0]
                allowed = json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'mask'), Payload=bytes(json.dumps({
                    'entity_type': entity_type, 
                    'method': request['method'], 
                    'path': usable_path
                }), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                if allowed:
                    object_path = '/'.join(usable_path)
                    the_object = bucket.Object('{data_root}/{entity_type}/{usable_path}'.format(data_root=env['data_root'], entity_type=entity_type, usable_path=object_path)) if entity_type in ['asset', 'error'] else bucket.Object(object_path)
                    canwrite = True
                    if request['method'] == 'PATCH':
                        try:
                            the_object.get()['Body'].read()
                        except:
                            canwrite = False
                    if canwrite:
                        lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({
                            'entity_type': entity_type, 
                            'method': request['method'], 
                            'body': str(request.get('body', '')).strip() if entity_type == 'error' else base64.b64decode(str(request.get('body', '')).strip()).decode('utf-8'), 
                            'content-type': request.get('content-type'), 
                            'path': object_path, 
                            '_env': env
                        }), 'utf-8'), InvocationType='Event')
                        counter = counter + 1
            elif len(env['path']) >= 2:
                if len(env['path']) == 2:
                    entity_type, entity_id = env['path']
                    if entity_type == 'mask':
                        mask_hash = hashlib.sha512(bytes(json.dumps(request['entity']), 'utf-8')).hexdigest()
                        entity_id = mask_hash
                    entity_key = '{data_root}/{entity_type}/{entity_id}.json'.format(data_root=env['data_root'], entity_type=entity_type, entity_id=entity_id)
                else:
                    entity_type, class_name, entity_id, record_field = (env['path'][0:3] + [None])
                    if entity_type in ['feed', 'subscription']:
                        entity_key = '{data_root}/{entity_type}/{class_name}/{entity_id}/{connection_id}.json'.format(
                        data_root=env['data_root'], entity_type=entity_type, 
                        class_name=class_name, entity_id=entity_id, connection_id=env['connection_id'])
                    else:
                        entity_key = '{data_root}/{entity_type}/{class_name}/{entity_id}.json'.format(
                            data_root=env['data_root'], entity_type=entity_type, class_name=class_name, entity_id=entity_id)
                try:
                    current_entity = json.loads(s3.Object(env['bucket'], entity_key).get()['Body'].read().decode('utf-8'))
                except:
                    current_entity = {}
                if len(env['path']) in [2, 3]:
                    entity_id, view_handle = (entity_id.split('.', 1) + ['json'])[:2]
                elif len(env['path']) == 4:
                    if entity_type in ['subscription', 'feed']:
                        record_id = entity_id
                        entity_id, view_handle = (env['path'][3].split('.', 1) + ['json'])[:2]
                        if entity_type in ['feed', 'subscription']:
                            entity_key = '{data_root}/{entity_type}/{class_name}/{record_id}/{connection_id}/{entity_id}.json'.format(
                                data_root=env['data_root'], entity_type=entity_type, class_name=class_name, record_id=record_id, 
                                connection_id=env['connection_id'], entity_id=entity_id) 
                        else: 
                            entity_key = '{data_root}/{entity_type}/{class_name}/{entity_id}.json'.format(
                                data_root=env['data_root'], entity_type=entity_type, class_name=class_name, entity_id=entity_id)
                    else:
                        record_field, view_handle = (env['path'][3].split('.', 1) + ['json'])[:2]
                        if request['method'] in ['POST', 'PUT']:
                            request['entity'] = {record_field: request['entity']}
                            request['method'] = 'POST'
                        elif request['method'] in ['DELETE', 'PATCH']:
                            if request['method'] == 'PATCH':
                                if current_entity:
                                    request['entity'] = {record_field: request['entity']}
                                    request['method'] = 'POST'
                                else:
                                    request['entity'] = {} 
                            elif request['method'] == 'DELETE':
                                request['entity'] = current_entity
                                del request['entity'][record_field]
                                request['method'] = 'PUT'
                        request['entity']['@type'] = request['entity'].get('@type', class_name)
                        request['entity']['@id'] = request['entity'].get('@id', entity_id)
                
                if request['method'] == 'POST' and type(request.get('entity')) is dict and request.get('headers', {}).get('content-type') == 'application/x-www-form-urlencoded':
                    for k, v in request['entity'].items():
                        try:
                            if type(v) is str and type(json.loads(v)) in [int, float, bool]:
                                request['entity'][k] = json.loads(v)
                        except:
                            pass
                if view_handle == 'json' and  (request['method'] == 'DELETE' or (request['method'] in ['POST', 'PUT', 'PATCH'] and json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'validate'), Payload=bytes(json.dumps({
                    'entity': request['entity'], 
                    'entity_type': entity_type, 
                    'class_name': None if entity_type in ['view', 'mask'] else class_name, 
                    'entity_id': entity_id}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8')))):
                    masked_entity = json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'mask'), Payload=bytes(json.dumps({
                        'entity_type': entity_type, 
                        'method': request['method'],
                        'class_name': None if entity_type in ['view', 'mask'] else class_name, 
                        'entity_id': entity_id, 
                        'entity': request.get('entity')
                    }), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8'))
                    constrained = masked_entity.get('__constrained', True)
                    del masked_entity['__constrained']
                    if masked_entity:
                        canwrite = bool(current_entity) if request['method'] == 'PATCH' else True
                        if canwrite:
                            if not constrained and request['method'] == 'PUT':
                                entity_to_write = {**masked_entity}
                            else:
                                entity_to_write = {**current_entity, **masked_entity}
                        if entity_to_write:
                            lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({
                                'entity_type': env['path'][0], 
                                'method': request['method'], 
                                'entity': entity_to_write, 
                                'current_entity': current_entity, 
                                'entity_key': entity_key, 
                                '_env': env
                            }), 'utf-8'), InvocationType='Event')
                            counter = counter + 1
    return counter
