env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3, time

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['system_root']):] if p.startswith(env['system_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')


def main(event, context):
    '''
    - triggered by react-index
    - event => {'connection_id': affected_connection, 'class_name': class_name, 'query_id': query_id, 'index': index}
    - gets the index
    - for each record_id calls mask with the query_id to trigger mask to include the record_id into the relevant index if the masked record is non-empty
    '''
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    if event.get('connection_id') and event.get('class_name') and event.get('query_id') and event.get('index'):
        connection_id = event['connection_id']
        class_name = event['class_name']
        query_id = event['query_id']
        index = event['index']
        index_record_ids = set(json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{system_root}/query/{class_name}/{query_id}/{index}.json'.format(
            system_root=env['system_root'], class_name=class_name, query_id=query_id, index=index))['Body'].read().decode('utf-8')))
        for record_id in index_record_ids:
            lambda_client.invoke(FunctionName='{lambda_namespace}-core-mask'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps({
                'connection_id': affected_connection,
                'entity_type': 'record', 
                'method': 'GET', 
                'class_name': class_name, 
                'entity_id': record_id, 
                'write': True, 
                'query_id': query_id
            }), 'utf-8'))
            counter = counter + 1
    return counter
