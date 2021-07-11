import boto3, json


{
  "Records": [
    {
      "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
      "receiptHandle": "MessageReceiptHandle",
      "body": "Hello from SQS!",
      "attributes": {
        "ApproximateReceiveCount": "1",
        "SentTimestamp": "1523232000000",
        "SenderId": "123456789012",
        "ApproximateFirstReceiveTimestamp": "1523232000001"
      },
      "messageAttributes": {},
      "md5OfBody": "{{{md5_of_body}}}",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:ap-southeast-2:123456789012:MyQueue",
      "awsRegion": "ap-southeast-2"
    }
  ]
}


def read_queue(queue_name, queue_dump={}, configuration={}):
    raw_messages = []
    if queue_name and not queue_dump:
        sqs_client = boto3.client('sqs')
        full_queue_name = '{namespace}-{queue_name}'.format(namespace=configuration['namespace'], queue_name=queue_name)
        try:
            get_queue_result = sqs_client.get_queue_url(QueueName=full_queue_name)
        except:
            get_queue_result = None
        if get_queue_result and get_queue_result.get('QueueUrl'):
            try:
                raw_messages = sqs_client.receive_message(**configuration.get('default_parameters', {}).get('read_queue', {}), 
                    QueueUrl=get_queue_result['QueueUrl'], **options)['Messages']
            except:
                raw_messages = []
    elif queue_dump:
        raw_messages = queue_dump.get('Records')
    if raw_messages:
        messages = []
        for raw_message in raw_messages:
            try:
                
            except:
                pass

    


def deploy_queue(queue_name, options={}, configuration={}):
    if queue_name and (options or configuration):
        sqs_client = boto3.client('sqs')
        full_queue_name = '{namespace}-{queue_name}'.format(namespace=configuration['namespace'], queue_name=queue_name)
        try:
            get_queue_result = sqs_client.get_queue_url(QueueName=full_queue_name)
        except:
            get_queue_result = None
        if get_queue_result and get_queue_result.get('QueueUrl'):
            try:
                if options:
                    sqs_client.set_queue_attributes(QueueUrl=get_queue_result['QueueUrl'], **options)
                return True
            except:
                return False
        else:
            try:
                sqs_client.create_queue(**configuration.get('default_parameters', {}).get('deploy_queue', {}), 
                    QueueName=full_queue_name, **options)
                return True
            except:
                return False
    else:
        return None

def remove_queue(queue_name, configuration={}):
    if queue_name:
        sqs_client = boto3.client('sqs')
        full_queue_name = '{namespace}-{queue_name}'.format(namespace=configuration['namespace'], queue_name=queue_name)
        try:
            get_queue_result = sqs_client.get_queue_url(QueueName=full_queue_name)
        except:
            get_queue_result = None
        if get_queue_result and get_queue_result.get('QueueUrl'):
            try:
                sqs_client.delete_queue(**configuration.get('default_parameters', {}).get('deploy_queue', {}), 
                    QueueUrl=get_queue_result['QueueUrl'])
            except:
                return False
    else:
        return None

def send_message(message, configuration={}):
    if configuration and configuration.get('QueueUrl'):
        sqs = boto3.client('sqs')
        message = message if type(message) is str else json.dumps(message)
        sqs.send_message(**configuration.get('default_parameters', {}).get('send_message', {}), 
            QueueUrl=configuration['QueueUrl'], MessageBody=message)

def delete_message(message, configuration={}):
    if configuration and configuration.get('QueueUrl'):
        sqs = boto3.client('sqs')
        sqs.delete_message(**configuration.get('default_parameters', {}).get('delete_message', {}), 
            QueueUrl=configuration['QueueUrl'], ReceiptHandle=message)



