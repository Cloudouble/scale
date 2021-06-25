import liveelement

def main(package, component, module, processorConfiguration, processorInput):
    operation = processorInput.get('operation', 'read')
    if operation in ['create', 'update']:
        liveelement.run('core.storer', {
            'operation': 'copy', 
            'source': module['https://schema.org/codeRepository'], 
            'target': module['https://live-element.net/reference/scale/core/property/deploymentPath']
        })
    elif operation == 'delete':
        liveelement.run('core.storer', {
            'operation': 'delete', 
            'target': module['https://live-element.net/reference/scale/core/property/deploymentPath']
        })
