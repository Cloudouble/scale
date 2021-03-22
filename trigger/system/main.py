import json, boto3, base64, urllib

def getpath(p, env=None):
    p = p.strip('/?')
    if env and env.get('data_root'):
        p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def get_env_context(event, context):
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    env['path'] = getpath(event['key'], env)
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    return env, client_context
    
def deploy_processor(processor_full_name, processor_configuration, lambda_client, env, install_or_update): 
    if any([processor_configuration.get('package_{}'.format(f)) for f in ['source_code', 'source_url', 'image_uri']]):
        deployment_options = {**{
            'Runtime': 'python3.8', 
            'Handler': 'main.main', 
            'Timeout': 900, 
            'MemorySize': 128
        }, **processor_configuration.get('deployment_options', {})}
        code_zipfile = None
        if processor_configuration.get('package_source_code'):
            code_zipfile = base64.b64decode(processor_configuration['package_source_code'])
        elif processor_configuration.get('package_source_url'):
            try:
                with urllib.request.urlopen(processor_configuration['package_source_url']) as r:
                    code_zipfile = r.read()
            except:
                pass
        if code_zipfile: 
            deployment_options['Code'] = {'ZipFile': code_zipfile}
            deployment_options['PackageType'] = 'Zip'
        elif processor_configuration.get('package_image_uri'):
            deployment_options['Code'] = {'ImageUri': processor_configuration['package_image_uri']}
            deployment_options['PackageType'] = 'Image'
        if install_or_update == 'install':
            try:
                deploy_response = lambda_client.create_function(**deployment_options, FunctionName=processor_full_name, Role=env['lambda_role'], Publish=True)
                return deploy_response.get('CodeSha256', False)
            except:
                return False
        elif install_or_update == 'update':
            try:
                deploy_response = lambda_client.update_function_code(**deployment_options['Code'], FunctionName=processor_full_name, Publish=True)
                return deploy_response.get('CodeSha256', False)
            except:
                return False


def main(event, context):
    '''
    - triggered by writes at _/system/{scope}/{module}.json
    - installs / updates system modules and extensions
    '''
    counter = 0
    if event.get('key'):
        env, client_context = get_env_context(event, context)    
        s3_client = boto3.client('s3')
        lambda_client = boto3.client('lambda')
        if env['path'] and len(env['path']) == 3 and env['path'][0] == 'system':
            scope, module = env['path'][1:3]
            module_configuration = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8'))
            if scope == 'authentication': 
                pass
            elif scope == 'daemon':
                # state: install update run pause remove (installed updated running paused removed error)
                # {state: '', processor: {package_source_code: '', package_source_url: '', package_image_uri: '', code_checksum: '', deployment_options: {}}}
                daemon_state = module_configuration.get('state', 'install')
                processor_full_name = '-extension-'.join(context.function_name.rsplit('-trigger-', 1))
                processor_full_name = '-daemon-{}'.format(module).join(processor_full_name.rsplit('-system', 1))
                processor_state = {}
                if daemon_state in ['install', 'update']:
                    try:
                        processor_state = lambda_client.get_function(FunctionName=processor_full_name)
                    except:
                        pass
                if daemon_state == 'install': 
                    if not processor_state:
                        module_configuration['processor']['code_checksum'] = deploy_processor(processor_full_name, module_configuration['processor'], lambda_client, env, 'install')
                        if module_configuration['processor']['code_checksum']: 
                            lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                            lambda_client.add_permission(
                                FunctionName=processor_full_name, StatementId=module, Action='lambda:InvokeFunction', Principal='s3.amazonaws.com', 
                                SourceArn=lambdaFunctionArn, SourceAccount=env['account_id']
                            )
                            module_configuration['state'] = 'installed'
                        else: 
                            module_configuration['state'] = 'error'
                    else:
                        module_configuration['state'] = 'installed'
                        
                elif daemon_state == 'update': 
                    if processor_state:
                        module_configuration['processor']['code_checksum'] = deploy_processor(processor_full_name, module_configuration['processor'], lambda_client, env, 'update')
                        if module_configuration['processor']['code_checksum']: 
                            module_configuration['state'] = 'updated'
                        else: 
                            module_configuration['state'] = 'error'
                    else:
                        module_configuration['state'] = 'error'
                elif daemon_state == 'run':
                    notification_configuration_current = s3_client.get_bucket_notification_configuration(Bucket=env['bucket'])
                    notification_configuration_current = [n.get('Events', []) for n in notification_configuration_current if n.get('Id') == processor_full_name]
                    if not notification_configuration_current:
                        lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                        s3_client.put_bucket_notification_configuration(Bucket=env['bucket'], NotificationConfiguration={
                            'LambdaFunctionConfigurations': [
                                {
                                    'Id': processor_full_name, 
                                    'LambdaFunctionArn': lambdaFunctionArn, 
                                    'Events': ['s3:ObjectCreated:*'], 
                                    'Filter': {'Key': {'FilterRules': [{'Name': 'prefix', 'Value': '{data_root}/daemon/{module}/'.format(data_root=env['data_root'], module=module)}]}}
                                }
                            ]
                        })
                        module_configuration['state'] = 'running'
                elif daemon_state == 'pause':
                    notification_configuration_current = s3_client.get_bucket_notification_configuration(Bucket=env['bucket'])
                    notification_configuration_current = [n.get('Events', []) for n in notification_configuration_current if n.get('Id') == processor_full_name]
                    if notification_configuration_current:
                        lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                        s3_client.put_bucket_notification_configuration(Bucket=env['bucket'], NotificationConfiguration={})
                        module_configuration['state'] = 'paused'
                elif daemon_state == 'remove':
                    lambda_client.delete_function(FunctionName=processor_full_name)
            elif scope == 'mask': 
                pass
            elif scope == 'query':
                pass
            elif scope == 'view':
                pass
            counter = counter + 1
    return counter