import liveelement

def main(package, component, module, configuration, inputObject, contexts):
    operation = inputObject.get('operation', 'read')
    if operation in ['create', 'update'] and module.get('codeRepository') and module.get('deploymentPath'):
        code_repository_split = module['codeRepository'].split('/', 3)
        if len(code_repository_split) == 4:
            liveelement.run_processor('core.storer.{}'.format(code_repository_split[2]), {
                'operation': 'copy', 
                'path': code_repository_split[3], 
                'target': module['deploymentPath']
            })
            liveelement.dispatch_event('.'.join([r['@id'].split('/').pop() for r in [package, component, module]]).lower(), 'deploy')
    elif operation == 'delete' and module.get('deploymentPath'):
        deployment_path_split = module['deploymentPath'].split('/', 3)
        if len(deployment_path_split) == 4:
            liveelement.run_processor('core.storer.{}'.format(deployment_path_split[2]), {
                'operation': 'delete', 
                'path': deployment_path_split[3]
            })
            liveelement.dispatch_event('.'.join([r['@id'].split('/').pop() for r in [package, component, module]]).lower(), 'remove')
