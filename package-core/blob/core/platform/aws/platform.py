import configuration
import boto3, json


def get(path, component=None, package='core'):
    try:
        try:
            if component:
                component_object = json.loads(boto3.client('s3').get_object(
                    Bucket=configuration['systemBucket'], 
                    Key='{}/{}/component/{}.json'.format(configuration['systemRoot'], package.lower(), component.lower())
                )['Body'].read().decode('utf-8'))
            else:
                component_object = {}
        except:
            component_object = {}
        if '.' not in path:
            filename_extension = component_object.get('defaultModuleFilenameExtension', 'json')
            if type(filename_extension) is dict:
                for subdir, ext in filename_extension.items():
                    if path.startswith('{}/'.format(subdir)):
                        filename_extension = ext
                        break
            path = '{}.{}'.format(path, filename_extension)
        if component_object.get('homeDirectory'):
            path = '{}/{}'.format(component_object['homeDirectory'], path)
        elif component:
            path = '{}/{}'.format(component.lower(), path)
        if package:
            path = '{}/{}'.format(package.lower(), path)
        return json.loads(boto3.client('s3').get_object(
            Bucket=configuration['systemBucket'], 
            Key='{}/{}'.format(configuration['systemRoot'], path)
        )['Body'].read().decode('utf-8'))
    except:
        return {}


def invoke(function_name, payload, synchronous=False):
    result = boto3.client('lambda').invoke(
        FunctionName='{}-{}'.format(configuration['processorNamespace'], function_name), 
        InvocationType='RequestResponse' if synchronous else 'Event', 
        Payload=bytes(json.dumps(payload), 'utf-8')
    )
    return json.loads(result['Payload'].read().decode('utf-8')) if synchronous else {}


def send(queue, module_address, event_type, event_detail):
    if all([a and type(a) is str for a in [queue, module_address, event_type]]):
        queue_module = get('core/eventbus/{}'.format(queue))
        if queue_module and 'associatedProcessorConfiguration' in queue_module:
            queue_configuration = get(queue_module['associatedProcessorConfiguration'])
            if queue_configuration and 'QueueUrl' in queue_configuration:
                if len(module_address.split('.')) == 3:
                    sqs = boto3.client('sqs')
                    event = {
                        'source': module_address, 
                        'type': event_type, 
                        'detail': event_detail if type(event_detail) is dict else {}
                    }
                    sqs.send_message(
                        QueueUrl=queue_configuration['QueueUrl'], 
                        MessageBody=json.dumps(event)
                    )
