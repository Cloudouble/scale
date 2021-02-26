import json, boto3, base64

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 

def main(event, context):
    '''
    - triggered by react-index
    - event => {'connection_id': affected_connection, 'class_name': class_name, 'query_id': query_id, 'index': index}
    - gets the index
    - for each record_id calls mask with the query_id to trigger mask to include the record_id into the relevant index if the masked record is non-empty
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    if env.get('connection_id') and event.get('class_name') and event.get('query_id') and event.get('index'):
        class_name = event['class_name']
        query_id = event['query_id']
        index = event['index']
        index_record_ids = set(json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/query/{class_name}/{query_id}/{index}.json'.format(
            data_root=env['data_root'], class_name=class_name, query_id=query_id, index=index))['Body'].read().decode('utf-8')))
        for record_id in index_record_ids:
            lambda_client.invoke(FunctionName=getprocessor(env, 'mask'), InvocationType='Event', Payload=bytes(json.dumps({
                'entity_type': 'record', 
                'method': 'GET', 
                'class_name': class_name, 
                'entity_id': record_id, 
                'write': True, 
                'query_id': query_id, 
                '_env': env
            }), 'utf-8'))
            counter = counter + 1
    return counter
