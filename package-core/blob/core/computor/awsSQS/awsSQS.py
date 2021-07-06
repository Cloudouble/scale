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
            if message:
                #do something with the message!
            
