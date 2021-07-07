import liveelement, json


def main(module_address, _input, synchronous=None, event=None):
    result = None
    package_name, component_name, module_name = (module_address.lower().split('.') + ['', '', ''])[:3]
    if package_name and component_name and module_name:
        package = liveelement.get_object(package_name, 'system', 'package', 'core')
        if package and type(package) is dict:
            component = liveelement.get_object(component_name, 'system', 'component', package_name)
            if component and type(component) is dict:
                module = liveelement.get_object(module_name, 'system', component_name, package_name)
                if module and type(module) is dict:
                    if 'associatedProcessor' in module:
                        processor = liveelement.get_object(module['associatedProcessor'], 'system', 'computor', package_name)
                        if processor:
                            configuration = {}
                            if 'associatedProcessorConfiguration' in module:
                                configuration = liveelement.get_object('configuration/{}'.format(module['associatedProcessorConfiguration']), 'system', 'value', package_name)
                            context = liveelement.get_object('context.json', 'scratchpad')
                            result = liveelement.invoke(
                                '{}-{}'.format(package_name, processor['@id'].split('/')[-1]).lower(), 
                                {
                                    'package': package, 
                                    'component': component, 
                                    'module': module, 
                                    'context': context, 
                                    'configuration': configuration, 
                                    '_input': _input
                                }, 
                                synchronous)
                            if event:
                                if type(event) is str:
                                    event_detail = result if type(result) is dict else {'result': result}
                                    liveelement.dispatch_event(module_address, event, event_detail)
                                elif type(event) is dict and 'type' in event:
                                    event_type = event['type']
                                    event_detail = result if type(result) is dict else {'result': result}
                                    if 'detail' in event and type(event['detail']) is dict:
                                        event_detail = {**event['detail'], **event_detail}
                                    liveelement.dispatch_event(
                                        event.get('source', module_address), 
                                        event_type, event_detail, 
                                        event.get('target_queue', 'system'), event.get('target_queue_package', 'core'))

    return result if synchronous else None
