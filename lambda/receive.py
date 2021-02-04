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
    for request_object in request_objects:
        try:
            if request_object['cf']['request']['method'] in ['POST', 'PUT', 'PATCH', 'DELETE']:
                body = base64.b64decode(request_object['cf']['request']['body']['data']) if request_object['cf']['request']['isBase64Encoded'] else request_object['cf']['request']['body']['data']
                try: 
                    entity = json.loads(body)
                except: 
                    entity = {k: v[0] for k, v in parse_qs(body).items()}
                path = request_object['cf']['request']['uri'].strip('/?').removesuffix('.json').split('/')
                if path and path[0] == 'connection' and len(path) in [2,5,6] and uuid_valid(path[1]):
                    connection_id = path[1]
                    connection_object = bucket.Object('connection/{connection}.json'.format(connection=connection_id))
                    if len(path) == 2:
                        # a new connection or connection extension (PUT / POST / PATCH), or connection immediate expiration (DELETE)
                        if request_object['cf']['request']['method'] in ['POST', 'PUT', 'PATCH']:
                            try:
                                connection_record = connection_object.get()['Body'].read().decode('utf-8')
                            except:
                                connection_record = {'mask': []}
                            if entity and type(entity) is dict:
                                connection_record['mask'] = json.loads(lambda_client.invoke(FunctionName='authenticate', InvocationType='RequestResponse', Payload=bytes(json.dumps(entity), 'utf-8'))['Payload'].read().decode('utf-8'))
                            connection_object.put(Body=bytes(json.dumps(connection_record), 'utf-8'), ContentType='application/json')
                        elif request_object['cf']['request']['method'] == 'DELETE':
                            try:
                                connection_object.delete()
                            except:
                                pass
                    else:
                        entity_type, record_type, entity_id, record_field, sort_field, min_index, max_index = (path[2:5] + ([None] * 4))
                        if len(path) == 5:
                            entity_id, view_handle = (entity_id.split('.', 1) + ['json'])[:2]
                        elif len(path) == 6:
                            record_field, view_handle = (path[5].split('.', 1) + ['json'])[:2]
                        elif len(path) == 7: 
                            sort_field = path[5]
                            index_range, view_handle =  (path[5].split('.', 1) + ['json'])[:2]
                            min_index, max_index = (index_range.split('-', 1) + ['1000'])[:2]
                            min_index = int(min_index) if str(min_index).isnumeric() else 0
                            max_index = int(max_index) if str(max_index).isnumeric() else 0
                            max_index = max_index if max_index > min_index else min_index + 1000
                        if request_object['cf']['request']['method'] in ['POST', 'PUT', 'PATCH']:
                            is_valid = json.loads(
                                lambda_client.invoke(
                                    FunctionName='validate', 
                                    InvocationType='RequestResponse', 
                                    Payload=bytes(json.dumps({'entity': entity, 'entity_type': entity_type, 'path': path}), 'utf-8')
                                )['Payload'].read().decode('utf-8')
                            )
                            if is_valid:
                                try:
                                    connection_record = connection_object.get()['Body'].read().decode('utf-8')
                                except:
                                    connection_record = {'mask': []}
                                mask_map = connection_record.get('mask', {})
                                mask_map = mask_map.get(entity_type) if entity_type in mask_map else mask_map.get('*', {})
                                mask_map = mask_map.get(request_object['cf']['request']['method']) if request_object['cf']['request']['method'] in mask_map else mask_map.get('*', {})
                                mask_map = mask_map.get(record_type) if record_type in mask_map else mask_map.get('*', {})
                                masked_entity = {}
                                constrained = True
                                allowfields = []
                                switches = {'purpose': 'mask', 'entity_type': entity_type, 'record_type': record_type, 'entity_id': entity_id, 
                                        'record_field': record_field, 'view_handle': view_handle, 'sort_field': sort_field, 'min_index': min_index, 'max_index': max_index}
                                for mask_name, options in mask_map.items():
                                    options = options if type(options) is dict else {}
                                    if constrained:
                                        mask_payload = {'entity': entity, 'connection': {**connection_record, **{'@id': connection_id}}, 'switches': switches, 'options': options}
                                        allowfields.extend(json.loads(lambda_client.invoke(FunctionName=mask, InvocationType='RequestResponse', Payload=bytes(json.dumps(mask_payload), 'utf-8'))['Payload'].read().decode('utf-8')))
                                        if '*' in allowfields:
                                            constrained = False
                                            break
                                    else:
                                        break
                                if constrained:
                                    for field in allowfields:
                                        if field in record:
                                            masked_entity[field] = entity[field]
                                else:
                                    masked_entity = {**entity}
                                if masked_entity:
                                    try:
                                        current_entity = s3.Object(os.environ['bucket'],'{entity_type}/{record_type}/{entity_id}.{view_handle}'.format(**switches)).get()['Body'].read().decode('utf-8')
                                    except:
                                        current_entity = {}
                                    canwrite = bool(current_entity) if request_object['cf']['request']['method'] == 'PATCH' else True
                                    if canwrite:
                                        if not constrained and request_object['cf']['request']['method'] == 'PUT':
                                            entity_to_write = {**masked_entity}
                                        else:
                                            entity_to_write = {**current_entity, **masked_entity}
                                    if entity_to_write:
                                        lambda_client.invoke(FunctionName='entity-write', InvocationType='Event', Payload=bytes(json.dumps(entity_to_write), 'utf-8'))
                                    counter = counter + 1
        except:
            pass
                    
    return counter
