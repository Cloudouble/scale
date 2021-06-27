import boto3, json, configuration

def run(module_address, processor_input, synchronous=None, silent=None):
    result = boto3.client('lambda').invoke(
        FunctionName='{namespace}-core'.format(namespace=configuration['processorNamespace']), 
        InvocationType='RequestResponse' if synchronous else 'Event', 
        Payload=bytes(json.dumps({
            'module_address': module_address, 
            'processor_input': processor_input, 
            'synchronous': synchronous, 
            'silent': silent
        }), 'utf-8')
    )
    return json.loads(result['Payload'].read().decode('utf-8')) if synchronous else None

