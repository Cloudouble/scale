import liveelement

def main(package, component, module, configuration, inputObject):
    operation = inputObject.get('operation', 'read')
    if operation in ['create', 'update']:
        code_repository = module.get('https://schema.org/codeRepository')
        deployment_path = module.get('https://live-element.net/reference/scale/core/property/deploymentPath')
        if code_repository and deployment_path:
            code_repository_split = code_repository.split('/', 3)
            partition = code_repository_split[2]
            if len(code_repository_split) == 4:
                liveelement.run_processor('core.storer.{}'.format(partition), {
                    'operation': 'copy', 
                    'source': code_repository_split[3], 
                    'target': deployment_path
                })
    elif operation == 'delete':
        deployment_path = module.get('https://live-element.net/reference/scale/core/property/deploymentPath')
        if deployment_path:
            deployment_path_split = deployment_path.split('/', 3)
            if len(deployment_path_split) == 4:
                partition = deployment_path_split[2]
                liveelement.run_processor('core.storer.{}'.format(partition), {
                    'operation': 'delete', 
                    'target': deployment_path_split[3]
                })
