import boto3, json

configuration = {'processorNamespace': 'liveeleement'}

def run(module_address, processor_input, synchronous=None, silent=None):
    lambda_client = boto3.client('lambda')
    result = lambda_client.invoke(
        FunctionName='{namespace}-{address}'.format(namespace=configuration['processorNamespace'], address=module_address.replace('.', '-').lower()), 
        InvocationType='RequestResponse' if synchronous else 'Event', 
        Payload=bytes(json.dumps(processor_input), 'utf-8')
    )
    return json.loads(result['Payload'].read().decode('utf-8')) if synchronous else None

