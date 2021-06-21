import liveelement

def main(packageObject, componentObject, moduleObject, operation):
    if operation in ['create', 'update']:
        liveelement.run('core.storer', {
            'operation': 'copy', 
            'source': moduleObject['https://schema.org/codeRepository'], 
            'target': moduleObject['https://live-element.net/reference/scale/core/property/deploymentPath']
        })
    elif operation == 'delete':
        liveelement.run('core.storer', {
            'operation': 'delete', 
            'target': moduleObject['https://live-element.net/reference/scale/core/property/deploymentPath']
        })
