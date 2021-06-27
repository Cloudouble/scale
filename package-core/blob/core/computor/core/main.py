import json, platform, configuration

def get_object_via_prefixed_address(address, module, package_name):
    if ':' in address:
        processor = None
        if '@context' in module:
            context = platform.get('{}/{}.json'.format(package_name, module['@context']))
            if context and type(context) is dict:
                processor_address_prefix, processor_address_main = module['associatedProcessor'].split(':', 1)
                processor_address = ''
                if processor_address_prefix in context:
                    if type(context[processor_address_prefix]) is dict and '@id' in context[processor_address_prefix]:
                        processor_address = '{}{}'.format(context[processor_address_prefix]['@id'], processor_address_main)
                    elif type(context[processor_address_prefix]) is str:
                        processor_address = '{}{}'.format(context[processor_address_prefix], processor_address_main)
                else:
                    processor_address = processor_address_main
                if processor_address:
                    processor = platform.get('{}.json'.format(processor_address))
    else:
        processor = platform.get('{}.json'.format(module['associatedProcessor']))
    return processor
    

def run(module_address, processor_input, event={}, synchronous=None):
    processor_result = None
    package_name, component_name, module_name = (module_address.lower().split('.') + ['', '', ''])[:3]
    if package_name and component_name and module_name:
        package = platform.get('core/package/{}.json'.format(package_name))
        if package and type(package) is dict:
            component = platform.get('{}/component/{}.json'.format(package_name, component_name))
            if component and type(component) is dict:
                module = platform.get('{}/{}/{}.json'.format(package_name, component_name, module_name))
                if module and type(module) is dict:
                    if 'associatedProcessor' in module:
                        processor = get_object_via_prefixed_address(module['associatedProcessor'], module, package_name)
                        if processor:
                            configuration = {}
                            if 'associatedProcessorConfiguration' in module:
                                configuration = get_object_via_prefixed_address(module['associatedProcessorConfiguration'], module, package_name)
                            processor_result = platform.invoke(
                                '{}-{}-{}'.format(configuration['processorNamespace'], package_name, processor['@id'].split('/')[-1]), 
                                {
                                    'package': package, 
                                    'component': component, 
                                    'module': module, 
                                    'configuration': configuration, 
                                    'inputObject': processor_input
                                }, 
                                synchronous)
                            if event and type(event) is dict and all([type(v) is dict for v in event.values()]):
                                queue = module.get('eventbusQueue')
                                if not queue:
                                    queue = component.get('eventbusQueue')
                                if not queue:
                                    queue = package.get('eventbusQueue')
                                if not queue:
                                    queue = 'default'
                                for event_type, event_detail in event.items():
                                    platform.send(queue, module_address, event_type, event_detail)
    return processor_result if synchronous else None
