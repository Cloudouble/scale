import json, platform, configuration

# platform is from //blob/core/platform/aws/platform.py
# configuration is value/configuration/platform/aws.json

def run(module_address, processor_input, synchronous=None, silent=None):
    # proxies ALL other function requests
    
    # create {package, component, module, processorConfiguration, processorInput}
    
    package_name, component_name, module_name = (module_address.lower().split('.') + ['', '', ''])[:3]
    
    if package_name and component_name and module_name:
        # get package object
        package = platform.get('core/package/{}.json'.format(package_name))
        if package and type(package) is dict:
            # get component object
            component = platform.get('{}/component/{}.json'.format(package_name, component_name))
            if component and type(component) is dict:
                # get module object
                module = platform.get('{}/{}/{}.json'.format(package_name, component_name, module_name))
                if module and type(module) is dict:
                    if 'associatedProcessor' in module:
                        if ':' in module['associatedProcessor']:
                            if '@context' in module:
                                # get context object 
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
                        
                            
                                        
                                            

                    
                        
                    
                    


    # resolve processor configuration and get configuration object
    
    # invoke processor platform function (synchronous or not)
    
    # if not silent then send event to eventbus
    
    # if synchronous return processor result 
    
    
    return {} if synchronous else None



