import json, importlib, base64
from configuration import configuration as configuration


def deploy_function(function_name, options, to_service='system'):
    service = configuration['computor'].get(to_service)
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.deploy_function(function_name, configuration, service.get('configuration', {}))

def remove_function(function_name, from_service='system'):
    service = configuration['computor'].get(from_service)
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.remove_function(function_name, service.get('configuration', {}))

def invoke_function(function_name, payload, synchronous=None, use_service='system'):
    service = configuration['computor'].get(use_service)
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.invoke_function(function_name, payload, synchronous, service.get('configuration', {}))

def run_processor(module_address, _input, synchronous=None, event=None):
    return invoke_function('core', {'module_address': module_address, '_input': _input, 'synchronous': synchronous, 'event': event}, synchronous)


def deploy_queue(queue_name, options):
    queue = configuration['eventbus'].get(queue_name)
    if (queue and queue.get('driver')) or (not queue and options.get('driver')):
        if not queue:
            queue = {'driver': options['driver']}
            del options['driver']
            queue_configuration = options
        else:
            queue_configuration = queue.get('configuration')
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.deploy_queue(queue_name, options, queue_configuration)

def remove_queue(queue_name, options={}):
    queue = configuration['eventbus'].get(queue_name)
    if (queue and queue.get('driver')) or (not queue and options.get('driver')):
        if not queue:
            queue = {'driver': options['driver']}
            del options['driver']
            queue_configuration = options
        else:
            queue_configuration = queue.get('configuration')
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.remove_queue(queue_name, queue_configuration)

def send_message(message, use_queue='system'):
    queue = configuration['eventbus'].get(use_queue)
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.send_message(message, queue.get('configuration', {}))

def remove_message(message, use_queue='system'):
    queue = configuration['eventbus'].get(use_queue)
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.delete_message(message, queue.get('configuration', {}))

def dispatch_event(source_module, event_type, event_detail={}, use_queue='system'):
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
    send_message(event, use_queue)


def mount_partition(queue_name, options):
    queue = configuration['eventbus'].get(queue_name)
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.deploy_queue(queue_name, options, queue.get('configuration', {}))

def unmount_partition(queue_name):
    queue = configuration['eventbus'].get(queue_name)
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.remove_queue(queue_name, queue.get('configuration', {}))

def get_object(path, component=None, package='core', use_partition='system'):
    partition = configuration['storer'].get(use_partition)
    if partition and partition.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(partition['driver']))
        except:
            driver = None
        if driver:
            if component:
                if use_partition != 'system':
                    system_partition = configuration['storer'].get('system')
                    if system_partition and system_partition.get('driver'):
                        system_partition_configuration = system_partition.get('configuration')
                        try:
                            system_partition_driver = importlib.import_module('./drivers/{}'.format(system_partition['driver']))
                        except:
                            system_partition_driver = None
                else:
                    system_partition_driver = driver
                if system_partition_driver:
                    try:
                        component_object = json.loads( base64.b64decode(system_partition_driver.read(
                            '{}/component/{}.json'.format(package.lower(), component.lower()), system_partition_configuration
                            )['Body']).decode('utf-8'))
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
            object_data = base64.b64decode(driver.read(path, partition.get('configuration'))['Body']).decode('utf-8')
            if path.endswith('.json'):
                try:
                    return json.loads(object_data)
                except:
                    return {}
            else:
                return object_data


def set_object(path, data, encoding=None, content_type='application/json', component=None, package='core', use_partition='system'):
    if path and data:
        data_object = {}
        if type(data) is str:
            if encoding == 'base64':
                if content_type.startswith('application/json') or path.endswith('.json'):
                    try:
                        data = base64.b64encode(json.dumps(json.loads(base64.b64decode(bytes(data, 'utf-8')).decode('utf-8')), indent=4, sort_keys=True)).decode('utf-8')
                    except:
                        data = None
                if data:
                    data_object['Body'] = data
            else:
                if content_type.startswith('application/json') or path.endswith('.json'):
                    try:
                        data = json.dumps(json.loads(data), indent=4, sort_keys=True)
                    except:
                        data = None
                if data:
                    data_object['Body'] = base64.b64encode(data).decode('utf-8')
        else:
            if content_type.startswith('application/json') or path.endswith('.json'):
                data_object['Body'] = base64.b64encode(bytes(json.dumps(data, indent=4, sort_keys=True), 'utf-8')).decode('utf-8')
            else:
                data_object['Body'] = base64.b64encode(bytes(str(data), 'utf-8')).decode('utf-8')
        if data_object and content_type:
            data_object['ContentType'] = content_type
        if data_object:
            partition = configuration['storer'].get(use_partition)
            if partition and partition.get('driver'):
                try:
                    driver = importlib.import_module('./drivers/{}'.format(partition['driver']))
                except:
                    driver = None
                if driver:
                    if component:
                        if use_partition != 'system':
                            system_partition = configuration['storer'].get('system')
                            if system_partition and system_partition.get('driver'):
                                system_partition_configuration = system_partition.get('configuration')
                                try:
                                    system_partition_driver = importlib.import_module('./drivers/{}'.format(system_partition['driver']))
                                except:
                                    system_partition_driver = None
                        else:
                            system_partition_driver = driver
                        if system_partition_driver:
                            try:
                                component_object = json.loads( base64.b64decode(system_partition_driver.read(
                                    '{}/component/{}.json'.format(package.lower(), component.lower()), system_partition_configuration
                                    )['Body']).decode('utf-8'))
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
                    driver.write(path, data_object, partition.get('configuration', {}))    


def remove_object(path, component=None, package='core', use_partition='system'):
    partition = configuration['storer'].get(use_partition)
    if partition and partition.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(partition['driver']))
        except:
            driver = None
        if driver:
            if component:
                if use_partition != 'system':
                    system_partition = configuration['storer'].get('system')
                    if system_partition and system_partition.get('driver'):
                        system_partition_configuration = system_partition.get('configuration')
                        try:
                            system_partition_driver = importlib.import_module('./drivers/{}'.format(system_partition['driver']))
                        except:
                            system_partition_driver = None
                else:
                    system_partition_driver = driver
                if system_partition_driver:
                    try:
                        component_object = json.loads( base64.b64decode(system_partition_driver.read(
                            '{}/component/{}.json'.format(package.lower(), component.lower()), system_partition_configuration
                            )['Body']).decode('utf-8'))
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
            driver.delete(path, partition.get('configuration'))


def list_objects(path, component=None, package='core', use_partition='system'):
    partition = configuration['storer'].get(use_partition)
    if partition and partition.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(partition['driver']))
        except:
            driver = None
        if driver:
            if component:
                path = '{}/{}'.format(component.lower(), path)
            if package:
                path = '{}/{}'.format(package.lower(), path)
            if not path.endswith('/'):
                path = '{}/'.format(path)
            return driver.ls(path, partition.get('configuration'))
