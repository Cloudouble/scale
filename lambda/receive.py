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
        records = [{'cf': {'request': {
            'method': event['httpMethod'], 
            'body': {'data': event['body']}, 
            'uri': event['path']
        }}}]
    elif event.get('Records'):
        #CDN: PUT, POST or PATCH
        records = event.get('Records', [])
    for request_object in records:
        try:
            if request_object['cf']['request']['method'] in ['POST', 'PUT', 'PATCH', 'DELETE']:
                body = base64.b64decode(request_object['cf']['request']['body']['data']) if request_object['cf']['request']['isBase64Encoded'] else request_object['cf']['request']['body']['data']
                record = {}
                try: 
                    record = json.loads(body)
                except: 
                    record = {k: v[0] for k, v in parse_qs(body).items()}
                path = request_object['cf']['request']['uri'].strip('/?').removesuffix('.json').split('/')
                if path and path[0] == 'connection' and len(path) in [2,5,6] and uuid_valid(path[1]):
                    if len(path) == 2:
                        # a new connection or connection extension (PUT / POST / PATCH), or connection immediate expiration (DELETE)
                        connection = path[1]
                        connection_object = bucket.Object('connection/{connection}.json'.format(connection=connection))
                        if request_object['cf']['request']['method'] in ['POST', 'PUT', 'PATCH']:
                            try:
                                connection_record = connection_object.get()['Body'].read().decode('utf-8')
                            except:
                                connection_record = {}
                            connection_expires = connection_record.get('expires', 0)
                            if connection_expires <= now:
                                connection_object.delete()
                                connection_record = {}
                            record['expires'] = record.get('expires', now + 1000)
                            if type(record) is dict and record['expires'] != connection_record.get('expires'):
                                try:
                                    connection_record['expires'] = float(record['expires'])
                                except:
                                    connection_record['expires'] = 0
                                connection_object.put(Body=bytes(json.dumps(connection_record), 'utf-8'), ContentType='application/json')
                                counter = counter + 1
                            else :
                                counter = counter + 1
                        elif request_object['cf']['request']['method'] == 'DELETE':
                            try:
                                connection_object.delete()
                            except:
                                pass
                            counter = counter + 1
                    elif len(path) == 5:
                        if path[2] == 'query':
                            if request_object['cf']['request']['method'] in ['POST', 'PUT', 'PATCH']:
                                query_object = bucket.Object('{}.json'.format('/'.join(path)))
                                try:
                                    query_record = json.loads(query_object.get()['Body'].read().decode('utf-8'))
                                    canwrite = True
                                except:
                                    query_record = {}
                                    canwrite = False if request_object['cf']['request']['method'] == 'PATCH' else True
                                if canwrite:
                                    allowfields = []
                                    for field in allowfields:
                                        if field in record:
                                            query_record[field] = record[field]
                                    query_object.put(Body=bytes(json.dumps(query_record), 'utf-8') , ContentType='application/json')
                            elif request_object['cf']['request']['method'] == 'DELETE':
                                query_object.delete()
                        elif path[2] == 'record':
                            pass
                        
                    elif len(path) == 6:
                            # record update at the field scope, subscription update
                        
                        
                        
                    
                    connection, area, record_type, record_id = path[1:]
                    if area == 'record' and uuid_valid(connection) and uuid_valid(record_id):
                        is_valid = record['@type'].lower() == record_type.lower() and record['@id'].lower() == record_id.lower() and json.loads(lambda_client.invoke(FunctionName='record-validate', 
                            InvocationType='RequestResponse', Payload=bytes(json.dumps(record), 'utf-8'))['Payload'].read().decode('utf-8'))
                        if is_valid:
                            connection_config = s3.Object(os.environ['bucket'],'connection/{}/config.json'.format(connection)).get()['Body'].read().decode('utf-8')
                            mask_map = connection_config.get('mask', {})
                            mask_map = mask_map.get(request_object['cf']['request']['method']) if request_object['cf']['request']['method'] in mask_map else mask_map.get('*', {})
                            mask_map = mask_map.get(record['@type']) if record['@type'] in mask_map else mask_map.get('*', {})
                            masked_record = {}
                            constrained = True
                            allowfields = []
                            for mask_name, mask_args in mask_map.items():
                                if constrained:
                                    mask_payload = {'purpose': 'mask', 'record': record, 'connection': connection_config, 'args': mask_args}
                                    allowfields.extend(json.loads(lambda_client.invoke(FunctionName=mask, InvocationType='RequestResponse', Payload=bytes(json.dumps(mask_payload), 'utf-8'))['Payload'].read().decode('utf-8')))
                                    if '*' in allowfields:
                                        constrained = False
                                        break
                                else:
                                    break
                            if constrained:
                                for field in allowfields:
                                    if field in record:
                                        masked_record[field] = record[field]
                            else:
                                masked_record = {**record}
                            if masked_record:
                                try:
                                    current_record = s3.Object(os.environ['bucket'],'record/{record_type}/{record_id}.json'.format(record_type=record_type, record_id=record_id)).get()['Body'].read().decode('utf-8')
                                except:
                                    current_record = {}
                                canwrite = bool(current_record) if request_object['cf']['request']['method'] == 'PATCH' else True
                                if canwrite:
                                    if not constrained and request_object['cf']['request']['method'] == 'PUT':
                                        record_to_write = {**masked_record}
                                    else:
                                        record_to_write = {**current_record, **masked_record}
                                if record_to_write:
                                    lambda_client.invoke(FunctionName='record-write', InvocationType='Event', Payload=bytes(json.dumps(record_to_write), 'utf-8'))
                                counter = counter + 1
        except:
            pass
    return counter



