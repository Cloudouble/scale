import json, importlib, base64
from configuration import configuration as configuration


def deploy_function(function_name, options, to_service='system', non_system_function_configuration={}):
    service = configuration['computor'][to_service] if configuration.get('computor', {}).get(to_service) else non_system_function_configuration
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.deploy_function(function_name, configuration, service.get('configuration', {}))

def remove_function(function_name, from_service='system', non_system_function_configuration={}):
    service = configuration['computor'][from_service] if configuration.get('computor', {}).get(from_service) else non_system_function_configuration
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.remove_function(function_name, service.get('configuration', {}))

def invoke_function(function_name, payload, synchronous=None, use_service='system', non_system_function_configuration={}):
    service = configuration['computor'][use_service] if configuration.get('computor', {}).get(use_service) else non_system_function_configuration
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.invoke_function(function_name, payload, synchronous, service.get('configuration', {}))

def start_listener(function_name, source, function_service='system', non_system_function_configuration={}):
    service = configuration['computor'][function_service] if configuration.get('computor', {}).get(function_service) else non_system_function_configuration
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.start_listener(function_name, source, service.get('configuration', {}))

def stop_listener(function_name, source, function_service='system', non_system_function_configuration={}):
    service = configuration['computor'][function_service] if configuration.get('computor', {}).get(function_service) else non_system_function_configuration
    if service and service.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(service['driver']))
        except:
            driver = None
        if driver:
            return driver.stop_listener(function_name, source, service.get('configuration', {}))

def run_processor(module_address, _input, synchronous=None, event=None, non_system_function_configuration={}):
    return invoke_function('core', {'module_address': module_address, '_input': _input, 'synchronous': synchronous, 'event': event}, 
        synchronous, non_system_function_configuration)


def deploy_queue(queue_name, options, non_system_queue_configuration={}):
    queue = configuration['eventbus'][queue_name] if configuration.get('eventbus', {}).get(queue_name) else non_system_queue_configuration
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.deploy_queue(queue_name, options, queue.get('configuration', {}))

def remove_queue(queue_name, non_system_queue_configuration={}):
    queue = configuration['eventbus'][queue_name] if configuration.get('eventbus', {}).get(queue_name) else non_system_queue_configuration
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.remove_queue(queue_name, queue.get('configuration', {}))

def read_queue(from_queue, queue_dump={}, non_system_queue_configuration={}):
    queue = configuration['eventbus'][from_queue] if configuration.get('eventbus', {}).get(from_queue) else non_system_queue_configuration
    if queue_dump and queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            try:
                return driver.read_queue(from_queue, queue_dump, queue.get('configuration', {}))
            except:
                return []
        else:
            return []
    else:
        return []

def send_message(message, options={}, use_queue='system', non_system_queue_configuration={}):
    queue = configuration['eventbus'][use_queue] if configuration.get('eventbus', {}).get(use_queue) else non_system_queue_configuration
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            if type(message) is bytes:
                message = base64.b64encode(message).decode('utf-8')
            elif type(message) is not str or options.get('ContentType') == 'application/json':
                message = base64.b64encode(bytes(json.dumps(message), 'utf-8')).decode('utf-8')
                options['ContentType'] = 'application/json'
            else:
                message = base64.b64encode(bytes(str(message), 'utf-8')).decode('utf-8')
            driver.send_message(message, options, queue.get('configuration', {}))

def remove_message(message, use_queue='system', non_system_queue_configuration={}):
    queue = configuration['eventbus'][use_queue] if configuration.get('eventbus', {}).get(use_queue) else non_system_queue_configuration
    if queue and queue.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(queue['driver']))
        except:
            driver = None
        if driver:
            driver.delete_message(message, queue.get('configuration', {}))

def dispatch_event(source_module, event_type, event_detail={}, use_queue='system', non_system_queue_configuration={}):
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
    send_message(event, {'ContentType': 'application/json'}, use_queue, non_system_queue_configuration)

def process_events(from_queue, event_dump={}, non_system_queue_configuration={}):
    events = [m for m in read_queue(from_queue, event_dump, non_system_queue_configuration) 
        if m and type(m) is dict and m.get('source') and m.get('type') and m.get('detail')]
    if events:
        listeners = get_object('map/eventbus/{}'.format(from_queue), 'value')
        if listeners:
            for event in events:
                if listeners.get(event['type']):
                    listener = listeners[event['type']]
                    if listener.get('module'):
                        run_processor(listener['module'], {**listener.get('input', {}), **event['detail'], 'source': event['source']})
                        

def mount_partition(partition_name, options, non_system_partition_configuration={}):
    partition = configuration['storer'][partition_name] if configuration.get('storer', {}).get(partition_name) else non_system_partition_configuration
    if partition and partition.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(partition['driver']))
        except:
            driver = None
        if driver:
            driver.mount_partition(partition_name, options, partition.get('configuration', {}))

def unmount_partition(partition_name, non_system_partition_configuration={}):
    partition = configuration['storer'][partition_name] if configuration.get('storer', {}).get(partition_name) else non_system_partition_configuration
    if partition and partition.get('driver'):
        try:
            driver = importlib.import_module('./drivers/{}'.format(partition['driver']))
        except:
            driver = None
        if driver:
            driver.unmount_partition(partition_name, partition.get('configuration', {}))

def get_object(path, component=None, package='core', use_partition='system', non_system_partition_configuration={}):
    partition = configuration['storer'][use_partition] if configuration.get('storer', {}).get(use_partition) else non_system_partition_configuration
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


def set_object(path, data, encoding=None, content_type='application/json', component=None, package='core', use_partition='system', non_system_partition_configuration={}):
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
            partition = configuration['storer'][use_partition] if configuration.get('storer', {}).get(use_partition) else non_system_partition_configuration
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


def remove_object(path, component=None, package='core', use_partition='system', non_system_partition_configuration={}):
    partition = configuration['storer'][use_partition] if configuration.get('storer', {}).get(use_partition) else non_system_partition_configuration
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


def list_objects(path, component=None, package='core', use_partition='system', non_system_partition_configuration={}):
    partition = configuration['storer'][use_partition] if configuration.get('storer', {}).get(use_partition) else non_system_partition_configuration
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
