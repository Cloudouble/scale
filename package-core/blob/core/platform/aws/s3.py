import boto3, json, base64


def mount_partition(partition_name, options={}, configuration={}):
    if partition_name and configuration and configuration.get('Bucket'):
        s3_client = boto3.client('s3')
        try:
            head_bucket_result = s3_client.head_bucket(Bucket=configuration['Bucket'])
        except:
            head_bucket_result = None
        if head_bucket_result:
            try:
                if options:
                    for method, method_params in option.items():
                        getattr(s3_client, method)(**method_params, Bucket=configuration['Bucket'])
                return True
            except:
                return False
        else:
            try:
                s3_client.create_bucket(**configuration.get('default_parameters', {}).get('mount_partition', {}), 
                    **options, Bucket=configuration['Bucket'])
                return True
            except:
                return False
    else:
        return None


def unmount_partition(partition_name, configuration={}):
    if partition_name:
        s3_client = boto3.client('s3')
        try:
            head_bucket_result = s3_client.head_bucket(Bucket=configuration['Bucket'])
        except:
            head_bucket_result = None
        if head_bucket_result:
            return False
        else:
            return True
    else:
        return None


def read(path, configuration):
    if path and configuration.get('Bucket'):
        try:
            s3_object = boto3.client('s3').get_object(**configuration.get('default_parameters', {}).get('read', {}), 
                Bucket=configuration['Bucket'], Key='{}{}'.format(configuration.get('root', ''), path))
            return {
                'Body': base64.b64encode(s3_object['Body'].read()).decode('utf-8'), 
                'ContentType': s3_object['ContentType'], 
                'ContentLength': s3_object['ContentLength']
            }
        except:
            return None
    else:
        return None


def write(path, data_object, configuration):
    if path and configuration.get('Bucket'):
        s3_arguments = {**configuration.get('default_parameters', {}).get('write', {}), 
            'Bucket': configuration['Bucket'], 
            'Key': '{}{}'.format(configuration.get('root', ''), path), 
            'Body': base64.b64decode(data_object['Body'])
        }
        if data_object['ContentType']:
            s3_arguments['ContentType'] = data_object['ContentType']
        try:
            boto3.client('s3').put_object(**s3_arguments)
            return True
        except:
            return False
    else:
        return None


def delete(path, configuration):
    if path and configuration.get('Bucket'):
        try:
            boto3.client('s3').delete_object(**configuration.get('default_parameters', {}).get('delete', {}), 
                Bucket=configuration['Bucket'], Key='{}{}'.format(configuration.get('root', ''), path))
            return True
        except:
            return False
    else:
        return None

def ls(path, configuration):
    if path and configuration.get('Bucket'):
        try:
            list_result = boto3.client('s3').list_objects_v2(**configuration.get('default_parameters', {}).get('ls', {}), 
                Bucket=configuration['Bucket'], Prefix='{}{}'.format(configuration.get('root', ''), path), Delimiter='/')
            return sorted([c['Key'] for c in list_result['Contents']]  + [p['Prefix'] for p in list_result['CommonPrefixes']])
        except:
            return []
    else:
        return []

def describe_native(path, configuration={}):
    if path and configuration.get('Bucket'):
        try:
            return boto3.client('s3').head_object(**configuration.get('default_parameters', {}).get('describe_native', {}), 
                Bucket=configuration['Bucket'], Key='{}{}'.format(configuration.get('root', ''), path))
        except:
            return {}
    else:
        return {}
