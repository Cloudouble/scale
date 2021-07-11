import boto3, json, base64

###
def mount_partition(partition_name, options={}, configuration={}):
    if partition_name and (options or configuration):
        s3_client = boto3.client('s3')
        full_bucket_name = '{namespace}-{bucket_name}'.format(namespace=configuration['namespace'], bucket_name=bucket_name)
        try:
            get_queue_result = sqs_client.get_queue_url(QueueName=full_queue_name)
        except:
            get_queue_result = None
        if get_queue_result and get_queue_result.get('QueueUrl'):
            try:
                if options:
                    sqs_client.set_queue_attributes(QueueUrl=get_queue_result['QueueUrl'], **options)
                return True
            except:
                return False
        else:
            try:
                sqs_client.create_queue(**configuration.get('default_parameters', {}).get('deploy_queue', {}), 
                    QueueName=full_queue_name, **options)
                return True
            except:
                return False
    else:
        return None

def remove_queue(queue_name, configuration={}):
    if queue_name:
        sqs_client = boto3.client('sqs')
        full_queue_name = '{namespace}-{queue_name}'.format(namespace=configuration['namespace'], queue_name=queue_name)
        try:
            get_queue_result = sqs_client.get_queue_url(QueueName=full_queue_name)
        except:
            get_queue_result = None
        if get_queue_result and get_queue_result.get('QueueUrl'):
            try:
                sqs_client.delete_queue(**configuration.get('default_parameters', {}).get('deploy_queue', {}), 
                    QueueUrl=get_queue_result['QueueUrl'])
            except:
                return False
    else:
        return None
###



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

