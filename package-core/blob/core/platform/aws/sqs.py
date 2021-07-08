import boto3, json

def send_message(message, configuration={}):
    if configuration and configuration.get('QueueUrl'):
        sqs = boto3.client('sqs')
        message = message if type(message) is str else json.dumps(message)
        sqs.send_message(**configuration.get('default_parameters', {}).get('send_message', {}), 
            QueueUrl=configuration['QueueUrl'], MessageBody=message)
