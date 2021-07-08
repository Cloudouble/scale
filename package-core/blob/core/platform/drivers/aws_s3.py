import boto3, json, base64


def read(path, configuration):
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


def write(path, data_object, configuration):
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


def delete(path, configuration):
    try:
        boto3.client('s3').delete_object(**configuration.get('default_parameters', {}).get('delete', {}), 
            Bucket=configuration['Bucket'], Key='{}{}'.format(configuration.get('root', ''), path))
        return True
    except:
        return False

def ls(path, configuration):
    try:
        list_result = boto3.client('s3').list_objects_v2(**configuration.get('default_parameters', {}).get('ls', {}), 
            Bucket=configuration['Bucket'], Prefix='{}{}'.format(configuration.get('root', ''), path), Delimiter='/')
        return sorted([c['Key'] for c in list_result['Contents']]  + [p['Prefix'] for p in list_result['CommonPrefixes']])
    except:
        return []

