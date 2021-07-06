import liveelement
import json, boto3, base64

def listener(event, context):
    if 'Records' in event:
        for event_record in event['Records']:
            event_source_arn = event_record.get('eventSourceARN')
            if event_source_arn:
                queue_map = liveelement.platform.get('value/map/queueMap')
                if event_source_arn in queue_map:
                    queue_module_address = queue_map[event_source_arn]
                    if queue_module_address:
                        package_name, component_name, module_name = queue_module_address.split('.')
                        module = liveelement.platform.get('{}/{}'.format(component_name, module_name), package_name)
                        component = liveelement.platform.get('component/{}'.format(component_name), package_name)
                        package = liveelement.platform.get('package/{}'.format(package_name), package_name)
                        contexts = liveelement.platform.get('context/{}'.format(package['context']), package_name)
                        configuration = liveelement.platform.get(module['associatedProcessorConfiguration'], package_name)
                        main(package, component, module, contexts, configuration, event)

def main(package, component, module, contexts, configuration, inputObject):
    operation, message, records = [inputObject.get(f) for f in {'operation': 'receive', 'message': {}, 'Records': []}.items()]
    sqs_client = boto3.client('sqs')
    if operation == 'send' and configuration.get('QueueUrl'):
        sqs_client.send_message(
            QueueUrl=configuration['QueueUrl'], 
            MessageBody=json.dumps(message)
        )
    elif operation == 'create' and configuration.get('QueueName'):
        try:
            queue_url = sqs_client.get_queue_url(QueueName=configuration['QueueName'])['QueueUrl']
        except:
            queue_url = sqs_client.create_queue(QueueName=configuration['QueueName'])['QueueUrl']
        if queue_url and queue_url != configuration.get('QueueUrl'):
            configuration['QueueUrl'] = queue_url
            liveelement.run_processor('core.storer.system', {
                'operation': 'update', 
                'path': module['associatedProcessorConfiguration'], 
                'body': configuration, 
                'content_type': 'application/json'
            })
    elif operation == 'delete': 
        try:
            queue_url = sqs_client.get_queue_url(QueueName=configuration['QueueName'])['QueueUrl']
        except:
            queue_url = sqs_client.create_queue(QueueName=configuration['QueueName'])['QueueUrl']
        if queue_url:
            del configuration['QueueUrl']
            liveelement.run_processor('core.storer.system', {
                'operation': 'update', 
                'path': module['associatedProcessorConfiguration'], 
                'body': configuration, 
                'content_type': 'application/json'
            })
            queue_url = sqs_client.delete_queue(QueueUrl=queue_url)
    elif configuration.get('QueueUrl') and records and type(records) is list:
        for message_record in records:
            try:
                message = json.loads(message_record.get('body'))
            except:
                message = {}
            if message and message.get('module'):
                liveelement.run_processor(message['module'], message.get('input', {}), message.get('event', None))
            elif message and message.get('type'):
                try:
                    listener_map = json.loads(liveelement.platform.get(component['core:property/listenerMap']))
                except:
                    listener_map = {}
                if listener_map and message['type'] in listener_map:
                    if not type(listener_map[message['type']]) is list:
                        listener_map[message['type']] = [listener_map[message['type']]]
                    for event_type in listener_map[message['type']]:
                        if event_type.get('module'):
                            processor_input = {**event_type.get('input', {}), **message.get('input', {})}
                            processor_event = {**event_type.get('event', {}), **message.get('event', {})}
                            liveelement.run_processor(event_type['module'], processor_input, processor_event)
            sqs_client.delete_message(
                QueueUrl=configuration['QueueUrl'], 
                ReceiptHandle=message_record['receiptHandle']
            )
            
