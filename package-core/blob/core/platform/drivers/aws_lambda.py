import boto3, json


def invoke(function_name, payload, synchronous=None, configuration={}):
    result = boto3.client('lambda').invoke(
        FunctionName='{namespace}-{function_name}'.format(namespace=configuration['namespace'], function_name=function_name), 
        InvocationType='RequestResponse' if synchronous else 'Event', 
        Payload=bytes(json.dumps(payload), 'utf-8')
    )
    return json.loads(result['Payload'].read().decode('utf-8')) if synchronous else None
