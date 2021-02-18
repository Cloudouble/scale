env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import boto3

def getpath(p):
    p = p.strip('/?')
    p = p[len(env['system_root']):] if p.startswith(env['system_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')


def main(event_data, context):
    '''
    - triggered by writes at _/connection/{connection_id}.json
    - deletes all objects under _/connection/{connection_id}/*
    '''
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    counter = 0
    for event_entry in event_data['Records']:
        path = getpath(event_entry['s3']['object']['key'])
        if path and len(path) == 2 and path[0] == 'connection':
            connection_id = path[1]
            s3_client = boto3.client('s3')
            list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix='{system_root}/connection/{connection_id}/'.format(system_root=env['system_root'], connection_id=connection_id))
            delete_response = s3_client.delete_objects(Bucket=env['bucket'], Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents']], 'Quiet': True})
            c = 1000
            while c and list_response.get('IsTruncated') and list_response.get('NextContinuationToken'):
                list_response = s3_client.list_objects_v2(Bucket=env['bucket'], Prefix='{system_root}/connection/{connection_id}/'.format(system_root=env['system_root'], connection_id=connection_id), ContinuationToken=list_response.get('NextContinuationToken'))
                delete_response = s3_client.delete_objects(Bucket=env['bucket'], Delete={'Objects': [{'Key': c['Key']} for c in list_response['Contents']], 'Quiet': True})
                c = c - 1
            counter = counter + 1
    return counter