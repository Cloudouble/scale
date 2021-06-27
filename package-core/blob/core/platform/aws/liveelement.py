import platform, configuration
import boto3, json

def run_processor(module_address, processor_input, event=None, synchronous=None):
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

def dispatch_event(module_address, event_type, event_detail={}, queue=None):
    if module_address and type(module_address) is str and event_type and type(event_type) is str:
        package_name, component_name, module_name = (module_address.lower().split('.') + ['', '', ''])[:3]
        if package_name and component_name and module_name:
            if not queue:
                module = platform.get('{}/{}/{}.json'.format(package_name, component_name, module_name))
                if module and type(module) is dict:
                    queue = module.get('eventbusQueue')
            if not queue:
                component = platform.get('{}/component/{}.json'.format(package_name, component_name))
                if component and type(component) is dict:
                    queue = component.get('eventbusQueue')
            if not queue:
                package = platform.get('core/package/{}.json'.format(package_name))
                if package and type(package) is dict:
                    queue = package.get('eventbusQueue')
            if not queue:
                queue = 'default'
            platform.send(queue, module_address, event_type, event_detail)
