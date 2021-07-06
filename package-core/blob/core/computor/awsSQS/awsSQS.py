import liveelement
import json, boto3, base64

def main(package, component, module, contexts, configuration, inputObject):
    operation, message, records = [inputObject.get(f) for f in {'operation': 'receive', 'message': {}, 'Records': []}.items()]
    sqs_client = boto3.client('sqs')
    if operation == 'send' and configuration.get('QueueUrl'):
        sqs_client.send_message(
            QueueUrl=configuration['QueueUrl'], 
            MessageBody=json.dumps(message)
        )
    elif operation == 'mount' and configuration.get('QueueName'):
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
    elif operation == 'unmount': 
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
    elif records and type(records) is list:
        for message_record in records:
            try:
                message = json.loads(message_record.get('body'))
            except:
                message = {}
            if message and message.get('module'):
                liveelement.run_processor(message['module'], message.get('input', {}), message.get('event', None))
            if message and message.get('type'):
                listener_map = liveelement.run_processor('core.storer.system', component['core:property/listenerMap'])
                if message['type'] in listener_map:
                    if not type(listener_map[message['type']]) is list:
                        listener_map[message['type']] = [listener_map[message['type']]]
                    for event_type in listener_map[message['type']]:
                        liveelement.run_processor(event_type['module'], event_type.get('input', {}), event_type.get('event', None))
            
