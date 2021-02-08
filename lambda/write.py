import json, boto3, os, base64, uuid, time
from urllib.parse import parse_qs

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

 
def main(event, context):
    # used in edge context for PUT, POST and PATCH requests from CDN, or REST API Gateway trigger, or Websocket API Gateway trigger 
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    if event.get('body'):
        #API Gateway - either Rest or Websocket
        body = base64.b64decode(event['body']) if event.get('isBase64Encoded', False) else event['body']
        request_objects = [{'cf': {'request': {
            'method': event['httpMethod'], 
            'body': {'data': event['body']}, 
            'uri': event['path']
        }}}]
    elif event.get('Records'):
        #CDN: PUT, POST or PATCH
        request_objects = event.get('Records', [])
    for request_object in [r['cf']['request'] for r in request_objects if r.get('cf', {}).get('request', {}).get('method', 'POST') in ['POST', 'PUT', 'PATCH', 'DELETE']]:
        body = base64.b64decode(request_object['body']['data']) if request_object['isBase64Encoded'] else request_object['body']['data']
        try: 
            entity = json.loads(body)
        except: 
            entity = {k: v[0] for k, v in parse_qs(body).items()}
        path = request_object['uri'].strip('/?').removeprefix('_/').removesuffix('.json').split('/')
        if path and path[0] == 'connection' and len(path) >= 2 and uuid_valid(path[1]):
            connection_id = path[1]
            if len(path) == 2:
                connection_object = bucket.Object('_/connection/{connection}.json'.format(connection=connection_id))
                try:
                    connection_record = connection_object.get()['Body'].read().decode('utf-8')
                except:
                    connection_record = {'mask': {}}
                if request_object['method'] in ['POST', 'PUT', 'PATCH']:
                    if entity and type(entity) is dict:
                        connection_record = {**connection_record, **json.loads(lambda_client.invoke(FunctionName='authenticate', InvocationType='RequestResponse', Payload=bytes(json.dumps(entity), 'utf-8'))['Payload'].read().decode('utf-8'))}
                    connection_object.put(Body=bytes(json.dumps(connection_record), 'utf-8'), ContentType='application/json')
                elif request_object['method'] == 'DELETE':
                    try:
                        connection_object.delete()
                    except:
                        pass
            elif len(path) >= 4 and path[2] in ['asset', 'static']:
                # {connection_id, entity_type, path, method}
                usable_path = path[3:]
                allowed = json.loads(lambda_client.invoke(FunctionName='mask', Payload=bytes(json.dumps({
                    'connection_id': connection_id, 
                    'entity_type': path[2], 
                    'method': request_object['method'], 
                    'path': usable_path
                }), 'utf-8'))['Payload'].read().decode('utf-8'))
                if allowed:
                    the_object = bucket.Object('_/asset/{}'.format('/'.join(usable_path))) if path[2] == 'asset' else bucket.Object('/'.join(usable_path))
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
            elif len(path) >= 5:
                entity_type, class_name, entity_id, record_field = (path[2:5] + [None])
                switches = {'entity_type': entity_type, 'class_name': class_name, 'entity_id': entity_id}
                entity_key = '_/{entity_type}/{class_name}/{entity_id}/{connection_id}.json'.format(**switches, connection_id=connection_id) if entity_type == 'feed' else '_/{entity_type}/{class_name}/{entity_id}.json'.format(**switches)
                try:
                    current_entity = s3.Object(os.environ['bucket'], entity_key).get()['Body'].read().decode('utf-8')
                except:
                    current_entity = {}
                if len(path) == 5:
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
                if view_handle == 'json' and request_object['method'] in ['POST', 'PUT', 'PATCH'] and json.loads(lambda_client.invoke(FunctionName='validate', Payload=bytes(json.dumps({'entity': entity, 'switches': switches}), 'utf-8'))['Payload'].read().decode('utf-8')):
                    # {connection_id, entity_type, method, class_name, entity_id, entity}
                    masked_entity = json.loads(lambda_client.invoke(FunctionName='mask', Payload=bytes(json.dumps({
                        'connection_id': connection_id, 
                        'entity_type': path[2], 
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
                                    record_version_key = '_/version/{class_name}/{record_id}/{version_id}.json'.format(class_name=entity['@type'], record_id=entity['@id'], version_id=put_response['VersionId'])
                                    bucket.put_object(Body=bytes(json.dumps(updated_fields), 'utf-8'), Key=record_version_key, ContentType='application/json')
                            elif request_object['method'] == 'DELETE' and current_entity:
                                if entity_type in ['query', 'record', 'view']:
                                    current_entity.delete()
                            counter = counter + 1
    return counter
