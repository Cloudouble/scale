import json, boto3, os, base64, uuid
from urllib.parse import parse_qs

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

 
def main(event, context):
    # used in edge context for GET requests
    
    
    
    
    
    
    
    
    
    
    
    
    
    counter = 0
    s3 = boto3.resource('s3')
    lambda_client = boto3.client('lambda')
    for request_object in event.get('Records', []):
        try:
            if request_object['cf']['request']['method'] in ['POST', 'PUT', 'PATCH']:
                body = base64.b64decode(request_object['cf']['request']['body']['data'])
                record = {}
                try: 
                    record = json.loads(body)
                except: 
                    record = {k: v[0] for k, v in parse_qs(body).items()}
                if record:
                    path = request_object['cf']['request']['uri'].strip('/?').removesuffix('.json').split('/')
                    if len(path) == 4:
                        connection, area, record_type, record_id = path
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
                                        current_record = s3.Object(os.environ['bucket'],'record/{}.json'.format(record_id)).get()['Body'].read().decode('utf-8')
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



