env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['system_root']):] if p.startswith(env['system_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')


def main(event, context):
    '''
    - triggered by new/updated/deleted /connection/{connection_id}/query/{class_name}/{query_id}/{index_initial}.json
    - use /feed/{class_name}/{query_id}/{connection_id}/* to find affected views for this connection and query
    - trigger view for each affected feed view
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    for record_event in event['Records']:
        path = getpath(record_event['s3']['object']['key'])
        if len(path) == 6:
            connection_id, entity_type, class_name, query_id, index = path[1:]
            connection_feed_list_path = '{system_root}/feed/{class_name}/{query_id}/{connection_id}/'.format(system_root=env['system_root'], class_name=class_name, query_id=query_id, connection_id=connection_id)
            connection_feed_list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix=connection_feed_list_path)
            for key_obj in connection_feed_list_response.get('Contents', []):
                try:
                    view = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=key_obj['Key'])['Body'].read().decode('utf-8'))
                except:
                    view = {}
                if view:
                    lambda_client.invoke(FunctionName='{lambda_namespace}-core-view'.format(lambda_namespace=env['lambda_namespace']), InvocationType='Event', Payload=bytes(json.dumps({
                        'connection_id': connection_id,
                        'class_name': class_name, 
                        'entity_type': 'query', 
                        'entity_id': query_id, 
                        'view': view
                    }), 'utf-8'))
            counter = counter + 1

    return counter
