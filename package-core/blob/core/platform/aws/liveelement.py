import platform, configuration
import boto3, json

def run_processor(module_address, processor_input, event=None, synchronous=None):
    if event and type(event) is str:
        event = {'type': event}
    result = boto3.client('lambda').invoke(
        FunctionName='{namespace}-core'.format(namespace=configuration['processorNamespace']), 
        InvocationType='RequestResponse' if synchronous else 'Event', 
        Payload=bytes(json.dumps({
            'module_address': module_address, 
            'processor_input': processor_input, 
            'event': event, 
            'synchronous': synchronous
        }), 'utf-8')
    )
    return json.loads(result['Payload'].read().decode('utf-8')) if synchronous else None

def dispatch_event(module, event_type, event_detail={}, queue=None):
    if module and type(module) is dict:
        module_name = str(module.get('@id', '')).split('/').pop().lower()
        component_name = str(module.get('partOfComponent', '')).split('/').pop().lower()
        package_name = str(module.get('partOfPackage', '')).split('/').pop().lower()
        module_address = '.'.join([package_name, component_name, module_name])
    if module and type(module) is str:
        package_name, component_name, module_name = (module.lower().split('.') + ['', '', ''])[:3]
        module_address = module
        module = platform.get('{}/{}/{}.json'.format(package_name, component_name, module_name))
    if package_name and component_name and module_name and event_type and type(event_type) is str:
        queue = queue if queue else module.get('eventbusQueue')
        if queue:
            platform.send(queue, module_address, event_type, event_detail)
