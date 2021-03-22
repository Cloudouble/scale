import json, boto3, base64, urllib, uuid

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

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
    
def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
    
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
                del deployment_options['Code']
                lambda_client.update_function_configuration(**deployment_options, FunctionName=processor_full_name, Role=env['lambda_role'], Publish=True)
                return deploy_response.get('CodeSha256', False)
            except:
                return False

def deploy_entities(module_configuration, lambda_client, env, client_context):
    success = True
    for entity_type, entities in module_configuration.get('entity_map', {}).items():
        if entity_type in ['record', 'query', 'feed', 'subscription', 'view', 'mask', 'system', 'error', 'asset', 'static']:
            for entity_id, entity in entities.items():
                class_name = entity.get('@type')
                entity_to_write = {**entity}
                entity_key = None
                if entity_type in ['record', 'query'] and class_name:
                    entity_key = '{data_root}/{entity_type}/{class_name}/{entity_id}.json'.format(data_root=env['data_root'], entity_type=entity_type, class_name=class_name, entity_id=entity_id)
                elif entity in ['feed', 'subscription'] and class_name and module_configuration.get('connection'):
                    object_id = entity.get('@query') if entity_type == 'feed' else entity.get('@record')
                    if entity_type == 'feed':
                        object_id = entity.get('@query')
                        if object_id:
                            del entity_to_write['@query']
                    if entity_type == 'subscription':
                        object_id = entity.get('@record')
                        if object_id:
                            del entity_to_write['@record']
                    entity_key = '{data_root}/{entity_type}/{class_name}/{object_id}/{connection_id}/{entity_id}.json'.format(
                        data_root=env['data_root'], entity_type=entity_type, class_name=class_name, 
                        object_id=object_id, connection_id=module_configuration['connection'], entity_id=entity_id
                    )
                elif entity_type in ['view', 'mask']:
                    entity_key = '{data_root}/{entity_type}/{entity_id}.json'.format(data_root=env['data_root'], entity_type=entity_type, entity_id=entity_id)
                elif entity_type in ['system'] and entity.get('@scope') and entity.get('@module'):
                    entity_key = '{data_root}/{entity_type}/{scope}/{module}.json'.format(data_root=env['data_root'], entity_type=entity_type, scope=entity['@scope'], module=entity['@module'])
                    del entity_to_write['@scope']
                    del entity_to_write['@module']
                elif entity_type in ['error'] and entity.get('@code'):
                    entity_key = '{data_root}/{entity_type}/{code}.json'.format(data_root=env['data_root'], entity_type=entity_type, code=entity['@code'])
                    del entity_to_write['@code']
                elif entity_type in ['asset', 'static'] and entity.get('@path') and entity.get('@content-type') and entity.get('@body'):
                    path = entity['@path']
                    del entity_to_write['@path']
                    if entity_type == 'asset':
                        entity_key = '{data_root}/{entity_type}/{path}'.format(data_root=env['data_root'], entity_type=entity_type, path=path)
                    elif entity_type == 'static':
                        entity_key = None if entity_key == env['data_root'] or path.startswith(env['data_root']) else path
                if entity_type != 'record' and '@type' in entity_to_write: 
                    del entity_to_write['@type']
                if entity_key:
                    if entity_type in ['asset', 'static']: 
                        lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({
                            'entity_type': entity_type, 
                            'method': 'PUT', 
                            'body': entity['@body'], 
                            'content-type': entity['@content-type'], 
                            'path': entity['@path']
                        }), 'utf-8'), ClientContext=client_context)
                    else:
                        if json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'validate'), Payload=bytes(json.dumps({
                            'entity': entity_to_write, 
                            'entity_type': entity_type, 
                            'class_name': None if entity_type in ['view', 'mask'] else class_name, 
                            'entity_id': entity_id}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8')):
                            lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({
                                'entity_type': entity_type, 
                                'method': 'PUT', 
                                'entity': entity_to_write, 
                                'entity_key': entity_key
                            }), 'utf-8'), ClientContext=client_context)
                else:
                    success = False
    return success
    

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
            module_state = module_configuration.get('state')
            rewrite_module_configuration = False
            if scope == 'daemon':
                module_configuration['connection'] = module_configuration['connection'] if module_configuration.get('connection') and uuid_valid(module_configuration['connection']) else str(uuid.uuid4())
            processor_full_name = '-extension-'.join(context.function_name.rsplit('-trigger-', 1))
            processor_full_name = '-{scope}-{module}'.format(scope=scope, module=module).join(processor_full_name.rsplit('-system', 1))
            if module_state in ['install', 'update']:
                try:
                    processor_state = lambda_client.get_function(FunctionName=processor_full_name)
                except:
                    processor_state = {}
            if module_state == 'install': 
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
            elif module_state == 'update': 
                if processor_state:
                    module_configuration['processor']['code_checksum'] = deploy_processor(processor_full_name, module_configuration['processor'], lambda_client, env, 'update')
                    if module_configuration['processor']['code_checksum']: 
                        module_configuration['state'] = 'updated'
                    else: 
                        module_configuration['state'] = 'error'
                else:
                    module_configuration['state'] = 'error'
            elif scope == 'daemon' and module_state == 'run':
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
                                'Filter': {'Key': {'FilterRules': [{'Name': 'prefix', 'Value': '{data_root}/daemon/{module}{connection}/'.format(data_root=env['data_root'], module=module, connection=module_configuration['connection'])}]}}
                            }
                        ]
                    })
                    module_configuration['state'] = 'running'
            elif scope == 'daemon' and  module_state == 'pause':
                notification_configuration_current = s3_client.get_bucket_notification_configuration(Bucket=env['bucket'])
                notification_configuration_current = [n.get('Events', []) for n in notification_configuration_current if n.get('Id') == processor_full_name]
                if notification_configuration_current:
                    lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                    s3_client.put_bucket_notification_configuration(Bucket=env['bucket'], NotificationConfiguration={})
                    module_configuration['state'] = 'paused'
            elif module_state == 'remove':
                if scope == 'daemon':
                    notification_configuration_current = s3_client.get_bucket_notification_configuration(Bucket=env['bucket'])
                    notification_configuration_current = [n.get('Events', []) for n in notification_configuration_current if n.get('Id') == processor_full_name]
                    if notification_configuration_current:
                        lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                        s3_client.put_bucket_notification_configuration(Bucket=env['bucket'], NotificationConfiguration={})
                lambda_client.delete_function(FunctionName=processor_full_name)
                module_configuration['state'] = 'removed'
            if module_state in ['install', 'update'] and module_configuration['state'] != 'error':
                if not deploy_entities(module_configuration, lambda_client, env, client_context): 
                    module_configuration['state'] = 'error'
            if module_configuration['state'] != module_state:
                rewrite_module_configuration = True
            if rewrite_module_configuration:
                s3_client.put_object(Bucket=env['bucket'], Key=event['key'], Body=bytes(json.dumps(module_configuration), 'utf-8'))
            counter = counter + 1
    return counter