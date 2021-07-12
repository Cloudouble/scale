import boto3, json


def deploy_function(function_name, options={}, configuration={}):
    if function_name and (options or configuration):
        lambda_client = boto3.client('lambda')
        full_function_name = '{namespace}-{function_name}'.format(namespace=configuration['namespace'], function_name=function_name)
        try:
            get_function_result = lambda_client.get_function(FunctionName=full_function_name)
        except:
            get_function_result = None
        if get_function_result:
            try:
                if options.get('Code'):
                    lambda_client.update_function_code(FunctionName=full_function_name, Publish=True, **options['Code'])
                    del options['Code']
                if options:
                    lambda_client.update_function_configuration(FunctionName=full_function_name, **options)
                return True
            except:
                return False
        else:
            try:
                lambda_client.create_function(**configuration.get('default_parameters', {}).get('deploy_function', {}), 
                    FunctionName=full_function_name, **options)
                return True
            except:
                return False
    else:
        return None


def remove_function(function_name, configuration={}):
    if function_name:
        lambda_client = boto3.client('lambda')
        full_function_name = '{namespace}-{function_name}'.format(namespace=configuration['namespace'], function_name=function_name)
        try:
            lambda_client.delete_function(FunctionName=full_function_name)
        except:
            return False
    else:
        return None
    

def invoke_function(function_name, payload, synchronous=None, configuration={}):
    result = boto3.client('lambda').invoke(**configuration.get('default_parameters', {}).get('invoke_function', {}), 
        FunctionName='{namespace}-{function_name}'.format(namespace=configuration['namespace'], function_name=function_name), 
        InvocationType='RequestResponse' if synchronous else 'Event', 
        Payload=bytes(json.dumps(payload), 'utf-8')
    )
    return json.loads(result['Payload'].read().decode('utf-8')) if synchronous else None


def connect_function(function_name, configuration={}, target_name='', target={}):
    full_function_name = '{namespace}-{function_name}'.format(namespace=configuration['namespace'], function_name=function_name)
    if target and target.get('native', {}) and target['native'].get('QueueArn'):
        lambda_client = boto3.client('lambda')
        lambda_client.create_event_source_mapping(**configuration.get('default_parameters', {}).get('connect_function', {}),
            EventSourceArn=target['native']['QueueArn'], FunctionName = full_function_name, Enabled=True)
    elif target and target.get('native', {}) and target['native'].get('FileSystemArn'):
        efs_object = {'Arn': target['native']['FileSystemArn'], 'LocalMountPath': configuration['LocalMountPath']}
        existing_efs = describe_native(function_name, configuration).get('FileSystemConfigs', [])
        if efs_object not in existing_efs:
            existing_efs.append(efs_object)
        lambda_client.update_function_configuration(**configuration.get('default_parameters', {}).get('connect_function', {}),
            FileSystemConfigs=existing_efs)


def disconnect_function(function_name, configuration={}, target_name='', target={}):
    full_function_name = '{namespace}-{function_name}'.format(namespace=configuration['namespace'], function_name=function_name)
    if target and target.get('native', {}) and target['native'].get('QueueArn'):
        lambda_client = boto3.client('lambda')
        mapping_uuids = [m['UUID'] for m in lambda_client.list_event_source_mappings(EventSourceArn=target['native']['QueueArn'], FunctionName=full_function_name)['EventSourceMappings']]
        for mapping_uuid in mapping_uuids:
            lambda_client.delete_event_source_mapping(UUID=mapping_uuid)
    elif target and target.get('native', {}) and target['native'].get('FileSystemArn'):
        efs_object = {'Arn': target['native']['FileSystemArn'], 'LocalMountPath': configuration['LocalMountPath']}
        existing_efs = describe_native(function_name, configuration).get('FileSystemConfigs', [])
        if efs_object in existing_efs:
            existing_efs.remove(efs_object)
        lambda_client.update_function_configuration(**configuration.get('default_parameters', {}).get('connect_function', {}),
            FileSystemConfigs=existing_efs)
        

def describe_native(function_name, configuration={}):
    if function_name:
        lambda_client = boto3.client('lambda')
        full_function_name = '{namespace}-{function_name}'.format(namespace=configuration['namespace'], function_name=function_name)
        try:
            return lambda_client.get_function(FunctionName=full_function_name)
        except:
            return {}
    else:
        return {}
