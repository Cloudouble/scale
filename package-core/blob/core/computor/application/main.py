import liveelement

def main(operation, unit):
    if operation in ['create', 'update']:
        liveelement.run('core.storer', {
            'operation': 'copy', 
            'source': unit['https://schema.org/codeRepository'], 
            'target': unit['https://live-element.net/reference/scale/core/property/deploymentPath']
        })
    elif operation == 'delete':
        liveelement.run('core.storer', {
            'operation': 'delete', 
            'target': unit['https://live-element.net/reference/scale/core/property/deploymentPath']
        })
