import boto3, json, base64


def read(path, configuration):
    s3_object = boto3.client('s3').get_object(Bucket=configuration['Bucket'], Key='{}{}'.format(configuration.get('root', ''), path))
    return {
        'Body': base64.b64encode(s3_object['Body'].read()).decode('utf-8'), 
        'ContentType': s3_object['ContentType'], 
        'ContentLength': s3_object['ContentLength']
    }


def write(path, data_object, configuration):
    pass


def delete(path, configuration):
    pass

def ls(path, configuration):
    pass

