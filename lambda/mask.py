import json, boto3, os, time

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main(event, context):
    # called by other functions to determine the masking of a given entity and connection {}
    masked_entity = None
    if event.get('connection_id'):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(os.environ['bucket'])
        connection_object = bucket.Object('_/connection/{connection_id}.json'.format(connection_id=event['connection_id']))
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
                    mask = mask.get(event['method']) if event['method'] in mask else mask.get('*', {})
                    for p in event['path']:
                        if mask:
                            mask = mask.get(p) if p in mask else mask.get('*', {})
                    if event['entity_type'] == 'static' and event['path'][0] == '_':
                        allowed = False
                    else:
                        if not mask:
                            allowed = False
                        elif mask == '*':
                            allowed = True
                        elif type(mask) is dict:
                            allowed = all([json.loads(lambda_client.invoke(FunctionName=mask_name, Payload=bytes(json.dumps({
                                'purpose': 'mask', 'connection_id': event['connection_id'], 'path': event['path'], 'options': options}), 'utf-8'))['Payload'].read().decode('utf-8')) 
                                for mask_name, options in mask.items()])
                    return allowed
                elif all([event.get(k) for k in ['method', 'class_name', 'entity_id', 'entity']]):
                        s3 = boto3.resource('s3')
                        bucket = s3.Bucket(os.environ['bucket'])
                        lambda_client = boto3.client('lambda')
                        switches = {'entity_type': event['entity_type'], 'method': event['method'], 'class_name': event['class_name'], 'entity_id': event['entity_id']}
                        mask = connection_mask.get(switches['entity_type']) if switches['entity_type'] in connection_mask else connection_mask.get('*', {})
                        mask = mask.get(switches['method']) if switches['method'] in mask else mask.get('*', {})
                        mask = mask.get(switches['class_name']) if switches['class_name'] in mask else mask.get('*', {})
                        masked_entity = {}
                        entity = event['entity']
                        constrained = True
                        allowfields = []
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
                            masked_entity = {**entity}

    return masked_entity
