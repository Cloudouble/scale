import liveelement
import json, boto3, base64

def main(package, component, module, contexts, configuration, inputObject):
    operation, path, target, body, content_type = [inputObject.get(f) for f in {'operation': 'read', 'path': '', 'target': None, 'body': None, 'content_type': 'application/json'}.items()]
    s3_client = boto3.client('s3')
    if operation == 'copy' and path and target:
        path_prefix = '{}/{}'.format(configuration['root'], path)
        try:
            sources = []
            s3_result = s3_client.list_objects_v2(Bucket=configuration['Bucket'], Prefix=path_prefix)
            sources = sources + [k['Key'] for k in s3_result['Contents']]
            while s3_result['isTruncated']:
                s3_result = s3_client.list_objects_v2(Bucket=configuration['Bucket'], Prefix=path_prefix, ContinuationToken=s3_result['ContinuationToken'])
                sources = sources + [k['Key'] for k in s3_result['Contents']]
            sources = [s.replace(path_prefix, '', 1).lstrip('/') for s in sources]
            sources.sort(Key=str.lower)
        except:
            sources = []
        for source_path in sources:
            target_path_split = target.split('/', 3)
            if len(target_path_split) == 4:
                source_object = s3_client.get_object(Bucket=configuration['Bucket'], Key='{}/{}'.format(path_prefix, source_path))
                source_body = base64.b64encode(source_object['Body'].read()).decode('utf-8'), 
                source_content_type = source_object['ContentType']
                liveelement.run_processor('core.storer.{}'.format(target_path_split[2]), {
                    'operation': 'update', 
                    'path': '{}/{}'.format(target_path_split[3].strip('/'), source_path), 
                    'body': source_body, 
                    'content_type': source_content_type
                })
    elif operation in ['create', 'update'] and path and body:
        try:
            return s3_client.put_object(
                Bucket=configuration['Bucket'], 
                Key='{}/{}'.format(configuration['root'], path), 
                Body=base64.b64decode(body), 
                ContentType=content_type
            )['Body'].read().decode('utf-8')
        except:
            return None
    elif operation == 'read' and path:
        try:
            the_object = s3_client.get_object(Bucket=configuration['Bucket'], Key='{}/{}'.format(configuration['root'], path))
            return {
                'body': base64.b64encode(the_object['Body'].read()).decode('utf-8'), 
                'content_type': the_object['ContentType']
            }
        except:
            return None
    elif operation == 'delete' and path:
        try:
            s3_client.delete_object(Bucket=configuration['Bucket'], Key='{}/{}'.format(configuration['root'], path))
            return None
        except:
            return None
    elif operation == 'list' and path:
        try:
            results = []
            path_prefix = '{}/{}'.format(configuration['root'], path)
            s3_result = s3_client.list_objects_v2(Bucket=configuration['Bucket'], Prefix=path_prefix, Delimiter='/')
            results = results + [k['Key'] for k in s3_result['Contents']] + [k['Prefix'] for k in s3_result['CommonPrefixes']]
            while s3_result['isTruncated']:
                s3_result = s3_client.list_objects_v2(Bucket=configuration['Bucket'], Prefix=path_prefix, 
                    Delimiter='/', ContinuationToken=s3_result['ContinuationToken'])
                results = results + [k['Key'] for k in s3_result['Contents']] + [k['Prefix'] for k in s3_result['CommonPrefixes']]
            results = [r.replace(path_prefix, '', 1).lstrip('/') for r in results]
            results.sort(Key=str.lower)
            return results
        except:
            return []
    elif operation == 'mount':
        try:
            bucket_location_result = s3_client.get_bucket_location(Bucket=configuration['Bucket'])
        except:
            bucket_location_result = None
        if bucket_location_result and bucket_location_result['LocationConstraint'] == configuration.get('CreateBucketConfiguration', {}).get('LocationConstraint'):
            pass
        elif configuration.get('CreateBucketConfiguration', {}).get('LocationConstraint') and bucket_location_result:
            return None
        else:
            s3_client.create_bucket(
                Bucket=configuration['Bucket'], 
                ACL='private', 
                CreateBucketConfiguration=configuration.get('CreateBucketConfiguration', {'LocationConstraint': 'us-east-1'})
            )
    elif operation == 'unmount':
        pass
        
