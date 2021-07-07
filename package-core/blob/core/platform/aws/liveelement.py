import configuration, boto3, json

def run_processor(module_address, processor_input, synchronous=None, event=None):
    if event and type(event) is str:
        event = {'type': event}
    result = boto3.client('lambda').invoke(
        FunctionName='{namespace}-core'.format(namespace=configuration['namespace']), 
        InvocationType='RequestResponse' if synchronous else 'Event', 
        Payload=bytes(json.dumps({
            'module': module_address, 
            'input': processor_input, 
            'synchronous': synchronous
        }), 'utf-8')
    )
    if event:
        if type(event) is str:
            event_detail = result if type(result) is dict else {'result': result}
            dispatch_event(module_address, event, event_detail)
        elif type(event) is dict and 'type' in event:
            event_type = event['type']
            event_detail = result if type(result) is dict else {'result': result}
            if 'detail' in event and type(event['detail']) is dict:
                event_detail = {**event['detail'], **event_detail}
            dispatch_event(event.get('source', module_address), event_type, event_detail, event.get('target_queue', 'system'), event.get('target_queue_package', 'core'))
    return json.loads(result['Payload'].read().decode('utf-8')) if synchronous else None

def dispatch_event(source_module, event_type, event_detail={}, target_queue='system', target_queue_package='core'):
    if source_module and type(source_module) is dict:
        source_module_name = str(source_module.get('@id', '')).split('/').pop().lower()
        source_component_name = str(source_module.get('partOfComponent', '')).split('/').pop().lower()
        source_package_name = str(source_module.get('partOfPackage', '')).split('/').pop().lower()
        source_module_address = '.'.join([source_package_name, source_component_name, source_module_name])
    if source_module and type(source_module) is str:
        source_package_name, source_component_name, source_module_name = (source_module.lower().split('.') + ['', '', ''])[:3]
        source_module_address = source_module
        source_module = get_object('{}/{}/{}.json'.format(source_package_name, source_component_name, source_module_name))
    if source_package_name and source_component_name and source_module_name and event_type and type(event_type) is str:
        target_queue = target_queue if target_queue else source_module.get('eventbusQueue')
        if target_queue:
            target_queue_package = target_queue_package if target_queue_package else 'core'
            target_queue_module = get_object('{}/eventbus/{}'.format(target_queue_package, target_queue))
            if target_queue_module and 'associatedProcessorConfiguration' in target_queue_module:
                target_queue_configuration = get_object(target_queue_module['associatedProcessorConfiguration'])
                if target_queue_configuration and 'QueueUrl' in target_queue_configuration:
                    if len(source_module_address.split('.')) == 3:
                        sqs = boto3.client('sqs')
                        event = {
                            'source': source_module_address, 
                            'type': event_type, 
                            'detail': event_detail if type(event_detail) is dict else {}
                        }
                        sqs.send_message(
                            QueueUrl=target_queue_configuration['QueueUrl'], 
                            MessageBody=json.dumps(event)
                        )

def get_object(path, partition='system', component=None, package='core'):
    if partition and partition in configuration and type(configuration[partition]) is dict and 'driver' in configuration[partition]:
        partition_driver = configuration[partition]['driver']
        partition_configuration = configuration[partition].get('configuration', {})
        partition_root = configuration[partition].get('root', '')
        if partition_driver == 's3':
            partition_bucket = partition_configuration.get('Bucket') if type(partition_configuration) is dict else None
            if partition_bucket:
                if component:
                    try:
                        component_key = '{}{}/component/{}.json'.format(partition_root, package.lower(), component.lower())
                        component_object = json.loads(boto3.client('s3').get_object(Bucket=partition_bucket, Key=component_key)['Body'].read().decode('utf-8'))
                    except:
                        component_object = {}
                else:
                    component_object = {}
                if '.' not in path:
                    filename_extension = component_object.get('defaultModuleFilenameExtension', 'json')
                    if type(filename_extension) is dict:
                        for subdir, ext in filename_extension.items():
                            if path.startswith('{}/'.format(subdir)):
                                filename_extension = ext
                                break
                    path = '{}.{}'.format(path, filename_extension)
                if component:
                    path = '{}/{}'.format(component.lower(), path)
                if package:
                    path = '{}/{}'.format(package.lower(), path)
                object_data = boto3.client('s3').get_object(Bucket=partition_bucket, Key='{}{}'.format(partition_root, path))['Body'].read().decode('utf-8')
                if path.endswith('.json'):
                    try:
                        return json.loads(object_data)
                    except:
                        return {}
                else:
                    return object_data
                
                
            
        elif partition_driver == 'efs':
            partition_localmountpath = partition_configuration.get('LocalMountPath') if type(partition_configuration) is dict else None
            
            
    
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
        if component:
            path = '{}/{}'.format(component.lower(), path)
        if package:
            path = '{}/{}'.format(package.lower(), path)
        return json.loads(boto3.client('s3').get_object(
            Bucket=configuration['systemBucket'], 
            Key='{}/{}'.format(configuration['systemRoot'], path)
        )['Body'].read().decode('utf-8'))
    except:
        return {}


'''
configuration => 
{
    "namespace": "liveelement", 
    "system": {
        "configuration": {
            "Bucket": "", 
            "LocalMountPath": ""
        }, 
        "driver": "s3/efs", 
        "root": "_/system/"
    }, 
    "scratchpad": {
        "configuration": {
            "Bucket": "", 
            "LocalMountPath": ""
        }, 
        "driver": "s3/efs", 
        "root": "_/scratchpad/"
    }, 
    "modified": {
        "configuration": {
            "Bucket": "", 
            "LocalMountPath": ""
        }, 
        "driver": "s3/efs", 
        "root": "_/modified/"
    }, 
    "archive": {
        "configuration": {
            "Bucket": "", 
            "LocalMountPath": ""
        }, 
        "driver": "s3/efs", 
        "root": "_/archive/"
    }
}

'''