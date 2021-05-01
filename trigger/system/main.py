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

def validate_and_write(entity_type, class_name, entity_id, connection_id, subentity_id, entity, env, client_context):
    if entity_type in ['feed', 'subscription'] and connection_id and subentity_id:
        entity_key = '{data_root}/{entity_type}/{class_name}/{entity_id}/{connection_id}/{subentity_id}.json'.format(data_root=env['data_root'], entity_type=entity_type, class_name=class_name, entity_id=entity_id, connection_id=connection_id, subentity_id=subentity_id)
    elif entity_type in ['record', 'query', 'system']:
        entity_key = '{data_root}/{entity_type}/{class_name}/{entity_id}.json'.format(data_root=env['data_root'], entity_type=entity_type, class_name=class_name, entity_id=entity_id)
    elif entity_type in ['view']:
        entity_key = '{data_root}/{entity_type}/{entity_id}.json'.format(data_root=env['data_root'], entity_type=entity_type, entity_id=entity_id)
    if json.loads(lambda_client.invoke(FunctionName=getprocessor(env, 'validate'), Payload=bytes(json.dumps({'entity_type': entity_type, 'class_name': class_name, 'entity_id': entity_id, 'entity': entity}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8')):
        lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': entity_type, 'method': 'PUT', 'entity': entity, 'entity_key': entity_key}), 'utf-8'), ClientContext=client_context)
        return 1
    else:
        return 0

def deploy_entities(module_configuration, lambda_client, env, client_context):
    count = [0, 0]
    for entity_type, entities in module_configuration.get('entity_map', {}).items():
        if entity_type == 'record':
            for class_name, records in entities.items():
                for record_id, record in records.items():
                    count[0] = count[0] + 1
                    count[1] = count[1] + validate_and_write(entity_type, class_name, record_id, None, None, record, env, client_context)
        elif entity_type == 'query':
            for class_name, queries in entities.items():
                for query_id, query in queries.items():
                    count[0] = count[0] + 1
                    count[1] = count[1] + validate_and_write(entity_type, class_name, query_id, None, None, query, env, client_context)
        elif entity_type == 'feed':
            for class_name, queries in entities.items():
                for query_id, feeds in queries.items():
                    for feed_id, feed in feeds.items():
                        count[0] = count[0] + 1
                        count[1] = count[1] + validate_and_write(entity_type, class_name, query_id, module_configuration.get('connection'), feed_id, feed, env, client_context)
        elif entity_type == 'subscription':
            for class_name, records in entities.items():
                for record_id, subscriptions in queries.items():
                    for subscription_id, subscription in subscriptions.items():
                        count[0] = count[0] + 1
                        count[1] = count[1] + validate_and_write(entity_type, class_name, record_id, module_configuration.get('connection'), subscription_id, subscription, env, client_context)
        elif entity_type == 'view':
            for view_id, view in entities.items():
                count[0] = count[0] + 1
                count[1] = count[1] + validate_and_write(entity_type, None, view_id, None, None, view, env, client_context)
        elif entity_type == 'mask':
            for mask_id, mask in entities.items():
                count[0] = count[0] + 1
                count[1] = count[1] + validate_and_write(entity_type, None, mask_id, None, None, mask, env, client_context)
        elif entity_type == 'system':
            for scope, modules in entities.items():
                for module_id, module in modules.items():
                    count[0] = count[0] + 1
                    count[1] = count[1] + validate_and_write(entity_type, scope, module_id, None, None, module, env, client_context)
        elif entity_type in ['error', 'static', 'asset']:
            for path, file in entities.items():
                lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({
                    'entity_type': entity_type, 
                    'method': 'PUT', 
                    'body': file['@body'], 
                    'content-type': file['@content-type'], 
                    'path': path
                }), 'utf-8'), ClientContext=client_context)
                count[0] = count[0] + 1
                count[1] = count[1] + 1
    return count
    
def deploy_rules(module_configuration, scope, module, env):
    name_prefix = '{lambda_namespace}-{scope}-{module}-'.format(lambda_namespace=env['lambda_namespace'], scope=scope, module=module)
    events = boto3.client('events')
    try: 
        module_rules = events.list_rules(NamePrefix=name_prefix)['Rules']
    except:
        module_rules = []
    for rule_name, rule in module_configuration.get('schedule', {}).items():
        rule_full_name = '{prefix}-{name}'.format(prefix=name_prefix, name=rule_name.lower().replace(' ', '-'))
        this_rule = [r for r in module_rules if r['Name'] == rule_full_name]
        this_rule = this_rule[0] if this_rule else {}
        events.put_rule(Name=rule_full_name, 
            Description='Rule created by {system_proper_name} in scope: {scope}, module: {module}'.format(system_proper_name=env['system_proper_name'], scope=scope, module=module), 
            ScheduleExpression=rule, State=this_rule.get('State', 'DISABLED'))
    

def main(event, context):
    '''
    - triggered by writes at _/system/{scope}/{module}.json
    - installs / updates system modules and extensions
    - daemon: {state: '', ?connection: '', ?processor: {package_source_code|package_source_url|package_image_url, deployment_options: {}}, ?schedule: {$rule_name: '$rule'}, entity_map: {}}
    - daemon entity_map can have keys of 'record', 'query', 'feed', 'subscription', 'view', 'mask', 'system', 'error', 'asset', 'static'
    - daemon processor can be implied by already having the function available at -extension-daemon-{module}
    '''
    print(json.dumps(event))
    counter = 0
    if event.get('key'):
        env, client_context = get_env_context(event, context)    
        s3_client = boto3.client('s3')
        lambda_client = boto3.client('lambda')
        if env['path'] and len(env['path']) == 3 and env['path'][0] == 'system':
            scope, module = env['path'][1:3]
            if scope == 'class':
                try:
                    class_definition = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8'))
                except:
                    class_definition = {}
                if not (class_definition and type(class_definition.get('label')) is str and type(class_definition.get('comment')) is str and type(class_definition.get('properties', [])) is dict and all([type(v) is list for v in class_definition['properties'].values()])):
                    class_definition = s3_client.delete_object(Bucket=env['bucket'], Key=event['key'])
                else:
                    if class_definition.get('subclassof', []) and type(class_definition['subclassof']) is list:
                        class_definition_json = json.dumps(class_definition)
                        for parent_class in reversed(class_definition['subclassof']):
                            try:
                                parent_definition = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/schema/classes/{parent_class}.json'.format(data_root=env['data_root'], parent_class=parent_class))['Body'].read().decode('utf-8'))
                            except:
                                try: 
                                    parent_definition = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/system/class/{parent_class}.json'.format(data_root=env['data_root'], parent_class=parent_class))['Body'].read().decode('utf-8'))
                                except:
                                    parent_definition = {}
                            for property_name, valid_types in parent_definition.get('properties', {}).items():
                                for valid_type in reversed(valid_types):
                                    if valid_type not in class_definition['properties'].get(property_name, []):
                                        class_definition['properties'][property_name] = class_definition['properties'].get(property_name, [])
                                        class_definition['properties'][property_name].insert(0, valid_type)
                        if class_definition_json != json.dumps(class_definition):
                            s3_client.put_object(Bucket=env['bucket'], Key=event['key'], Body=bytes(json.dumps(class_definition), 'utf-8'), ContentType='application/json')
            else:
                module_configuration = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8'))
                starting_module_configuration_json = json.dumps(module_configuration)
                module_state = module_configuration.get('state')
                processor_full_name = '-extension-'.join(context.function_name.rsplit('-trigger-', 1))
                processor_full_name = '-{scope}-{module}'.format(scope=scope, module=module).join(processor_full_name.rsplit('-system', 1))
                if module_state in ['install', 'update']:
                    try:
                        processor_state = lambda_client.get_function(FunctionName=processor_full_name)
                    except:
                        processor_state = {}
                    if module_configuration.get('processor') and type(module_configuration['processor']) is dict:
                        if module_state == 'install': 
                            if not processor_state:
                                module_configuration['processor']['code_checksum'] = deploy_processor(processor_full_name, module_configuration['processor'], lambda_client, env, 'install')
                                if module_configuration['processor']['code_checksum']: 
                                    lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                                    module_configuration['state'] = 'installed'
                                else: 
                                    module_configuration['state'] = 'error'
                            else:
                                lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                                module_configuration['state'] = 'installed'
                            if scope == 'daemon' and module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                                deploy_rules(module_configuration, scope, module, env)
                        elif module_state == 'update': 
                            if processor_state:
                                module_configuration['processor']['code_checksum'] = deploy_processor(processor_full_name, module_configuration['processor'], lambda_client, env, 'update')
                                if module_configuration['processor']['code_checksum']: 
                                    module_configuration['state'] = 'updated'
                                else: 
                                    module_configuration['state'] = 'error'
                            else:
                                module_configuration['state'] = 'error'
                    else:
                        if not processor_state:
                            module_configuration['state'] = 'error'
                if scope == 'daemon' and module_state == 'install' and module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                    deploy_rules(module_configuration, scope, module, env)                    
                if scope == 'daemon' and module_state == 'run':
                    module_configuration['connection'] = module_configuration.get('connection', str(uuid.uuid4()))
                    module_configuration['mask'] = module_configuration.get('mask', {'record': {'GET': {'*': '*'}}})
                    connection_record = {'name': module, 'daemon': module, 'mask': module_configuration['mask']}
                    write_env = {**env, 'connection_id': module_configuration['connection']}
                    lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': 'connection', 'entity': connection_record, 'method': 'PUT', '_env': write_env}), 'utf-8'))
                    if module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                        events = boto3.client('events')
                        for rule_name, rule in module_configuration['schedule'].items():
                            rule_full_name = '{lambda_namespace}-{scope}-{module}--{name}'.format(lambda_namespace=env['lambda_namespace'], scope=scope, module=module, name=rule_name.lower().replace(' ', '-'))
                            try:
                                full_rule = events.describe_rule(Name=rule_full_name)
                            except:
                                full_rule = {}
                            if full_rule:
                                if full_rule.get('State') != 'ENABLED':
                                    events.enable_rule(Name=rule_full_name)
                                processor_arn = 'arn:aws:lambda:{core_region}:{account_id}:function:{processor_full_name}'.format(core_region=env['core_region'], account_id=env['account_id'], processor_full_name=processor_full_name)
                                try:
                                    processor_rules = events.list_rule_names_by_target(TargetArn=processor_arn)['RuleNames']
                                except:
                                    processor_rules = []
                                if rule_full_name not in processor_rules:
                                    events.put_targets(Rule=rule_full_name, Targets=[{'Id': processor_full_name, 'Arn': processor_arn}])
                                    try:
                                        lambda_client.remove_permission(FunctionName=processor_full_name, StatementId=module)
                                    except:
                                        pass
                                    lambda_client.add_permission(
                                        FunctionName=processor_full_name, StatementId=module, Action='lambda:InvokeFunction', 
                                        Principal='events.amazonaws.com', SourceAccount=env['account_id'], 
                                        SourceArn='arn:aws:events:{core_region}:{account_id}:rule/{rule_full_name}'.format(core_region=env['core_region'], account_id=env['account_id'], rule_full_name=rule_full_name)
                                    )
                    module_configuration['state'] = 'running'
                elif scope == 'daemon' and  module_state == 'pause':
                    if module_configuration.get('connection'):
                        write_env = {**env, 'connection_id': module_configuration['connection']}
                        lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({'entity_type': 'connection', 'method': 'DELETE', '_env': write_env}), 'utf-8'))
                        del module_configuration['connection']
                        module_configuration['state'] = 'paused'
                    if module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                        events = boto3.client('events')
                        for rule_name, rule in module_configuration['schedule'].items():
                            rule_full_name = '{lambda_namespace}-{scope}-{module}--{name}'.format(lambda_namespace=env['lambda_namespace'], scope=scope, module=module, name=rule_name.lower().replace(' ', '-'))
                            processor_arn = 'arn:aws:lambda:{core_region}:{account_id}:function:{processor_full_name}'.format(core_region=env['core_region'], account_id=env['account_id'], processor_full_name=processor_full_name)
                            try:
                                lambda_client.remove_permission(FunctionName=processor_full_name, StatementId=module)
                            except:
                                pass
                            try:
                                processor_rules = events.list_rule_names_by_target(TargetArn=processor_arn)['RuleNames']
                            except:
                                processor_rules = []
                            if rule_full_name in processor_rules:
                                events.remove_targets(Rule=rule_full_name, Ids=[processor_full_name], Force=True)
                            if len(processor_rules) == 1:
                                events.disable_rule(Name=rule_full_name)
                if module_state == 'remove':
                    if scope == 'daemon':
                        if module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                            events = boto3.client('events')
                            for rule_name, rule in module_configuration['schedule'].items():
                                rule_full_name = '{lambda_namespace}-{scope}-{module}--{name}'.format(lambda_namespace=env['lambda_namespace'], scope=scope, module=module, name=rule_name.lower().replace(' ', '-'))
                                processor_arn = 'arn:aws:lambda:{core_region}:{account_id}:function:{processor_full_name}'.format(core_region=env['core_region'], account_id=env['account_id'], processor_full_name=processor_full_name)
                                try:
                                    lambda_client.remove_permission(FunctionName=processor_full_name, StatementId=module)
                                except:
                                    pass
                                try:
                                    processor_rules = events.list_rule_names_by_target(TargetArn=processor_arn)['RuleNames']
                                except:
                                    processor_rules = []
                                if rule_full_name in processor_rules:
                                    events.remove_targets(Rule=rule_full_name, Ids=[processor_full_name], Force=True)
                                try:
                                    rule_targets = events.list_targets_by_rule(Rule=rule_full_name)['Targets']
                                except:
                                    rule_targets = []
                                if not rule_targets:
                                    events.delete_rule(Name=rule_full_name, Force=True)
                    if module_configuration.get('ephemeral'):
                        lambda_client.delete_function(FunctionName=processor_full_name)
                    module_configuration['state'] = 'removed'
                if module_state in ['install', 'update'] and module_configuration['state'] != 'error':
                    if module_configuration.get('entity_map', {}):
                        deploy_entities_count = deploy_entities(module_configuration, lambda_client, env, client_context)
                        if deploy_entities_count[0] != deploy_entities_count[1]:
                            module_configuration['state'] = 'error'
                    if module_state == 'install':
                        module_configuration['state'] = 'installed' 
                    elif module_state == 'update':
                        module_configuration['state'] = 'updated' 
                if starting_module_configuration_json != json.dumps(module_configuration):
                    s3_client.put_object(Bucket=env['bucket'], Key=event['key'], Body=bytes(json.dumps(module_configuration), 'utf-8'))
            counter = counter + 1
    return counter