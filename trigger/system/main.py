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

def deploy_entities(module_configuration, lambda_client, env, client_context):
    count = 0
    for entity_type, entities in module_configuration.get('entity_map', {}).items():
        if entity_type == 'record':
            for class_name, records in entities.items():
                for record_id, record in records.items():
                    validate_and_write(entity_type, class_name, record_id, None, None, record, env, client_context)
                    count = count + 1
        elif entity_type == 'query':
            for class_name, queries in entities.items():
                for query_id, query in queries.items():
                    validate_and_write(entity_type, class_name, query_id, None, None, query, env, client_context)
                    count = count + 1
        elif entity_type == 'feed':
            for class_name, queries in entities.items():
                for query_id, feeds in queries.items():
                    for feed_id, feed in feeds.items():
                        validate_and_write(entity_type, class_name, query_id, module_configuration.get('connection'), feed_id, feed, env, client_context)
                        count = count + 1
        elif entity_type == 'subscription':
            for class_name, records in entities.items():
                for record_id, subscriptions in queries.items():
                    for subscription_id, subscription in subscriptions.items():
                        validate_and_write(entity_type, class_name, record_id, module_configuration.get('connection'), subscription_id, subscription, env, client_context)
                        count = count + 1
    elif entity_type == 'view':
            for view_id, view in entities.items():
                validate_and_write(entity_type, None, view_id, None, None, view, env, client_context)
                count = count + 1
        elif entity_type == 'mask':
            for mask_id, mask in entities.items():
                validate_and_write(entity_type, None, mask_id, None, None, mask, env, client_context)
                count = count + 1
        elif entity_type == 'system':
            for scope, modules in entities.items():
                for module_id, module in modules.items():
                    validate_and_write(entity_type, scope, module_id, None, None, module, env, client_context)
                    count = count + 1
        elif entity_type in ['error', 'static', 'asset']:
            for path, file in entities.items():
                lambda_client.invoke(FunctionName=getprocessor(env, 'write'), Payload=bytes(json.dumps({
                    'entity_type': entity_type, 
                    'method': 'PUT', 
                    'body': file['@body'], 
                    'content-type': file['@content-type'], 
                    'path': path
                }), 'utf-8'), ClientContext=client_context)
                count = count + 1
    return True
    
def deploy_rules(module_configuration, scope, module, env):
    name_prefix = '{lambda_namespace}-{scope}-{module}-'.format(lambda_namespace=env['lambda_namespace'], scope=scope, module=module)
    try: 
        module_rules = events.list_rules(NamePrefix=name_prefix)['Rules']
    except:
        module_rules = []
    this_rule = [r for r in module_rules if r['Name'] == rule_full_name]
    this_rule = this_rule[0] if this_rule else {}
    events = boto3.client('events')
    for rule_name, rule in module_configuration['schedule']:
        rule_full_name = '{prefix}-{name}'.format(prefix=name_prefix, name=rule_name)
        events.put_rule(Name=rule_full_name, 
            Description='Rule created by {system_proper_name} in scope: {scope}, module: {module}'.format(system_proper_name=env['system_proper_name'], scope=scope, module=module)
            ScheduleExpression=rule, State=this_rule.get('State', 'DISABLED'))
    

def main(event, context):
    '''
    - triggered by writes at _/system/{scope}/{module}.json
    - installs / updates system modules and extensions
    - daemon: {state: '', ?connection: '', ?processor: {package_source_code|package_source_url|package_image_url, deployment_options: {}}, ?schedule: {$rule_name: '$rule'}, entity_map: {}}
    - daemon entity_map can have keys of 'record', 'query', 'feed', 'subscription', 'view', 'mask', 'system', 'error', 'asset', 'static'
    - daemon processor can be implied by already having the function available at -extension-daemon-{module}
    '''
    counter = 0
    if event.get('key'):
        env, client_context = get_env_context(event, context)    
        s3_client = boto3.client('s3')
        lambda_client = boto3.client('lambda')
        if env['path'] and len(env['path']) == 3 and env['path'][0] == 'system':
            scope, module = env['path'][1:3]
            if scope == 'schema':
                try:
                    class_definition = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8'))
                except:
                    class_definition = {}
                if not (class_definition and type(class_definition.get('label')) is str and type(class_definition.get('comment')) is str and type(class_definition.get('properties', [])) is dict and all([type(v) is list for v in class_definition['properties'].values()])):
                    class_definition = s3_client.delete_object(Bucket=env['bucket'], Key=event['key'])
                else:
                    if class_definition.get('subclassof', []) and type(class_definition['subclassof']) is list:
                        class_definition_json = json.dumps(class_definition)
                        properties = class_definition['properties']
                        for parent_class in class_definition['subclassof']:
                            try:
                                parent_definition = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/schema/classes/{parent_class}.json')['Body'].read().decode('utf-8'))
                            except:
                                try: 
                                    parent_definition = json.loads(s3_client.get_object(Bucket=env['bucket'], Key='{data_root}/system/schema/{parent_class}.json')['Body'].read().decode('utf-8'))
                                except:
                                    parent_definition = {}
                            if parent_definition and parent_definition.get('properties', {}):
                                for property_name, valid_types in parent_definition['properties']:
                                    for valid_type in reversed(valid_types):
                                        if valid_type not in class_definition['properties'].get(property_name, []):
                                            class_definition['properties'][property_name] = class_definition['properties'].get(property_name, [])
                                            class_definition['properties'][property_name].insert(0, valid_type)
                        if class_definition_json != json.dumps(class_definition):
                            s3_client.put_object(Bucket=env['bucket'], Key=event['key'], Body=bytes(json.dumps(class_definition), 'utf-8'), ContentType='application/json')
            else:
                module_configuration = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=event['key'])['Body'].read().decode('utf-8'))
                module_state = module_configuration.get('state')
                rewrite_module_configuration = False
                if scope == 'daemon':
                    module_configuration['connection'] = module_configuration['connection'] if module_configuration.get('connection') and uuid_valid(module_configuration['connection']) else str(uuid.uuid4())
                processor_full_name = '-extension-'.join(context.function_name.rsplit('-trigger-', 1))
                processor_full_name = '-{scope}-{module}'.format(scope=scope, module=module).join(processor_full_name.rsplit('-system', 1))
                if module_configuration.get('processor'):
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
                            lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                            lambda_client.add_permission(
                                FunctionName=processor_full_name, StatementId=module, Action='lambda:InvokeFunction', Principal='s3.amazonaws.com', 
                                SourceArn=lambdaFunctionArn, SourceAccount=env['account_id']
                            )
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
                        if scope == 'daemon' and module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                            deploy_rules(module_configuration, scope, module, env)                    
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
                                        'Filter': {'Key': {'FilterRules': [{'Name': 'prefix', 'Value': '{data_root}/daemon/{connection}/'.format(data_root=env['data_root'], module=module, connection=module_configuration['connection'])}]}}
                                    }
                                ]
                            })
                            module_configuration['state'] = 'running'
                        if module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                            events = boto3.client('events')
                            for rule_name, rule in module_configuration['schedule']:
                                rule_full_name = '{lambda_namespace}-{scope}-{module}-{name}'.format(lambda_namespace=env['lambda_namespace'], scope=scope, module=module, name=rule_name)
                                try:
                                    full_rule = events.describe_rule(Name=rule_full_name)
                                except:
                                    full_rule = {}
                                if full_rule:
                                    if full_rule.get('State') != 'ENABLED':
                                        event.enable_rule(Name=rule_full_name)
                                    processor_arn = 'arn:aws:lambda:{core_region}:{account_id}:function:{processor_full_name}'.format(core_region=env['core_region'], account_id=env['account_id'], processor_full_name=processor_full_name)
                                    try:
                                        rule_targets = events.list_rule_names_by_target(TargetArn=processor_arn)['RuleNames']
                                    except:
                                        rule_targets = []
                                    if rule_full_name not in rule_targets:
                                        events.put_targets(Rule=rule_full_name, Targets=[{'Id': processor_full_name, 'Arn': processor_arn}])
                    elif scope == 'daemon' and  module_state == 'pause':
                        notification_configuration_current = s3_client.get_bucket_notification_configuration(Bucket=env['bucket'])
                        notification_configuration_current = [n.get('Events', []) for n in notification_configuration_current if n.get('Id') == processor_full_name]
                        if notification_configuration_current:
                            lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                            s3_client.put_bucket_notification_configuration(Bucket=env['bucket'], NotificationConfiguration={})
                            module_configuration['state'] = 'paused'
                        if module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                            events = boto3.client('events')
                            for rule_name, rule in module_configuration['schedule']:
                                rule_full_name = '{lambda_namespace}-{scope}-{module}-{name}'.format(lambda_namespace=env['lambda_namespace'], scope=scope, module=module, name=rule_name)
                                processor_arn = 'arn:aws:lambda:{core_region}:{account_id}:function:{processor_full_name}'.format(core_region=env['core_region'], account_id=env['account_id'], processor_full_name=processor_full_name)
                                try:
                                    rule_targets = events.list_rule_names_by_target(TargetArn=processor_arn)['RuleNames']
                                except:
                                    rule_targets = []
                                if rule_full_name in rule_targets:
                                    events.remove_targets(Rule=rule_full_name, Targets=[processor_full_name], Force=True)
                                if len(rule_targets) == 1:
                                    event.disable_rule(Name=rule_full_name)
                    elif module_state == 'remove':
                        if scope == 'daemon':
                            notification_configuration_current = s3_client.get_bucket_notification_configuration(Bucket=env['bucket'])
                            notification_configuration_current = [n.get('Events', []) for n in notification_configuration_current if n.get('Id') == processor_full_name]
                            if notification_configuration_current:
                                lambdaFunctionArn = 'arn:aws:lambda:{core_region}:{account_id}:function:{name}'.format(core_region=env['core_region'], account_id=env['account_id'], name=processor_full_name)
                                s3_client.put_bucket_notification_configuration(Bucket=env['bucket'], NotificationConfiguration={})
                            if module_configuration.get('schedule') and type(module_configuration['schedule'] is dict):
                                events = boto3.client('events')
                                for rule_name, rule in module_configuration['schedule']:
                                    rule_full_name = '{lambda_namespace}-{scope}-{module}-{name}'.format(lambda_namespace=env['lambda_namespace'], scope=scope, module=module, name=rule_name)
                                    processor_arn = 'arn:aws:lambda:{core_region}:{account_id}:function:{processor_full_name}'.format(core_region=env['core_region'], account_id=env['account_id'], processor_full_name=processor_full_name)
                                    try:
                                        rule_targets = events.list_rule_names_by_target(TargetArn=processor_arn)['RuleNames']
                                    except:
                                        rule_targets = []
                                    if rule_full_name in rule_targets:
                                        events.remove_targets(Rule=rule_full_name, Targets=[processor_full_name], Force=True)
                                    if len(rule_targets) == 1:
                                        event.delete_rule(Name=rule_full_name, Force=True)
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