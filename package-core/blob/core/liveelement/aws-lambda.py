import environment, boto3, json

def map_process_address_to_name(processor_address):
    return '{namespace}-{address}'.format(namespace=environment['namespace'], address=processor_address.replace('.', '-').lower())

def run(processor_address, processor_input, synchronous=None, silent=None):
    lambda_client = boto3.client('lambda')
    result = lambda_client.invoke(
        FunctionName=map_process_address_to_name(processor_address), 
        InvocationType='RequestResponse' if synchronous else 'Event', 
        Payload=bytes(json.dumps(processor_input), 'utf-8')
    )
    return json.loads(result['Payload'].read().decode('utf-8')) if synchronous else None

