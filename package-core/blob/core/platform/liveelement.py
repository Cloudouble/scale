import json, importlib
from configuration import configuration as configuration

{
    "computor": {
        "system": {
            "driver": "aws_lambda", 
            "configuration": {
                "namespace": "liveelement"
            }
        }
    }, 
    "storer": {
        "system": {
            "driver": "aws_efs", 
            "configuration": {
                "LocalMountPath": "../../../../system", 
            }, 
            "root": "/"
        }
    }, 
    "eventbus": {
        "system": {
            "driver": "aws_sqs", 
            "configuration": {
                "QueueUrl"
            }
        }
    }
}


def invoke_function(function_name, payload, synchronous=None, target_service='system'):
    service = configuration['computor'].get(target_service)
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.invoke_function(function_name, payload, synchronous, service.get('configuration', {}))


def run_processor(module_address, _input, synchronous=None, event=None):
    return invoke_function('core', {'module_address': module_address, '_input': _input, 'synchronous': synchronous, 'event': event}, synchronous)


def dispatch_event(source_module, event_type, event_detail={}, target_queue='system'):
    queue = configuration['eventbus'].get(target_queue)
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            if source_module and type(source_module) is dict:
                source_module_name = str(source_module.get('@id', '')).split('/').pop().lower()
                source_component_name = str(source_module.get('partOfComponent', '')).split('/').pop().lower()
                source_package_name = str(source_module.get('partOfPackage', '')).split('/').pop().lower()
                source_module_address = '.'.join([source_package_name, source_component_name, source_module_name])
            if source_module and type(source_module) is str:
                source_module_address = source_module
            event = {
                'source': source_module_address, 
                'type': event_type, 
                'detail': event_detail if type(event_detail) is dict else {}
            }
            driver.send_message(event, queue.get('configuration', {}))
            

def get_object(path, partition='system', component=None, package='core'):
    working_partitions = configuration.get('working_partitions', {})
    if partition and partition in working_partitions and type(working_partitions[partition]) is dict and 'driver' in working_partitions[partition]:
        partition_driver = working_partitions[partition]['driver']
        partition_configuration = working_partitions[partition].get('configuration', {})
        partition_root = working_partitions[partition].get('root', '')
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
            if partition_localmountpath:
                if component:
                    try:
                        component_path = '{}/{}{}/component/{}.json'.format(partition_localmountpath, partition_root, package.lower(), component.lower())
                        with open(component_path, 'r') as component_file:
                            component_object = json.loads(component_file.read().decode('utf-8'))
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
                with open('{}/{}{}'.format(partition_localmountpath, partition_root, path), 'r') as object_file:
                    object_data = object_file.read().decode('utf-8')
                if path.endswith('.json'):
                    try:
                        return json.loads(object_data)
                    except:
                        return {}
                else:
                    return object_data

def set_object(path, data, content_type='application/json', partition='system', component=None, package='core'):
    working_partitions = configuration.get('working_partitions', {})
    if partition and partition in working_partitions and type(working_partitions[partition]) is dict and 'driver' in working_partitions[partition]:
        partition_driver = working_partitions[partition]['driver']
        partition_configuration = working_partitions[partition].get('configuration', {})
        partition_root = working_partitions[partition].get('root', '')
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
                if path.endswith('.json') or content_type == 'application/json':
                    if type(data) is str:
                        try:
                            data = json.loads(data)
                        except:
                            data = None
                    if data:
                        try:
                            data = json.dumps(data, indent=4, sort_keys=True)
                        except:
                            data = None
                else:
                    try:
                        data = str(data)
                    except:
                        data = None
                if data:
                    boto3.client('s3').put_object(
                        Bucket=partition_bucket, 
                        Key='{}{}'.format(partition_root, path), 
                        Body=bytes(data, 'utf-8'), 
                        ContentType=content_type
                    )
        elif partition_driver == 'efs':
            partition_localmountpath = partition_configuration.get('LocalMountPath') if type(partition_configuration) is dict else None
            if partition_localmountpath:
                if component:
                    try:
                        component_path = '{}/{}{}/component/{}.json'.format(partition_localmountpath, partition_root, package.lower(), component.lower())
                        with open(component_path, 'r') as component_file:
                            component_object = json.loads(component_file.read().decode('utf-8'))
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
                if path.endswith('.json') or content_type == 'application/json':
                    if type(data) is str:
                        try:
                            data = json.loads(data)
                        except:
                            data = None
                    if data:
                        try:
                            data = json.dumps(data, indent=4, sort_keys=True)
                        except:
                            data = None
                else:
                    try:
                        data = str(data)
                    except:
                        data = None
                if data:
                    with open('{}/{}{}'.format(partition_localmountpath, partition_root, path), 'w') as object_file:
                        object_file.write(data)
