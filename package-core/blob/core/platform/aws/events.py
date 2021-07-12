import boto3, json


def deploy_schedule(schedule_name, options={}, configuration={}):
    if schedule_name and (options or configuration):
        events_client = boto3.client('events')
        full_schedule_name = '{namespace}-{schedule_name}'.format(namespace=configuration['namespace'], schedule_name=schedule_name)
        try:
            events_client.put_rule(**configuration.get('default_parameters', {}).get('deploy_schedule', {}), 
                Name=full_schedule_name, **options)
            return True
        except:
            return False
    else:
        return None

def start_schedule(schedule_name, configuration={}):
    if schedule_name:
        events_client = boto3.client('events')
        full_schedule_name = '{namespace}-{schedule_name}'.format(namespace=configuration['namespace'], schedule_name=schedule_name)
        eventbus_name = configuration.get('default_parameters', {}).get('enable_schedule', {}).get('EventBusName')
        try:
            enable_rule_params = {'Name': full_schedule_name}
            if eventbus_name:
                enable_rule_params['EventBusName'] = eventbus_name
            events_client.enable_rule(**enable_rule_params)
            return True
        except:
            return False
    else:
        return None

def stop_schedule(schedule_name, configuration={}):
    if schedule_name:
        events_client = boto3.client('events')
        full_schedule_name = '{namespace}-{schedule_name}'.format(namespace=configuration['namespace'], schedule_name=schedule_name)
        eventbus_name = configuration.get('default_parameters', {}).get('disable_schedule', {}).get('EventBusName')
        try:
            disable_rule_params = {'Name': full_schedule_name}
            if eventbus_name:
                disable_rule_params['EventBusName'] = eventbus_name
            events_client.disable_rule(**disable_rule_params)
            return True
        except:
            return False
    else:
        return None

def remove_schedule(schedule_name, configuration={}):
    if schedule_name:
        events_client = boto3.client('events')
        full_schedule_name = '{namespace}-{schedule_name}'.format(namespace=configuration['namespace'], schedule_name=schedule_name)
        eventbus_name = configuration.get('default_parameters', {}).get('remove_schedule', {}).get('EventBusName')
        try:
            list_target_params = {'Rule': full_schedule_name}
            remove_targets_params = {'Rule': full_schedule_name}
            if eventbus_name:
                list_target_params['EventBusName'] = eventbus_name
                remove_targets_params['EventBusName'] = eventbus_name
            remove_targets_params['Ids'] = [t['Id'] for t in events_client.list_targets_by_rule(**list_target_params)['Targets']]
            if remove_targets_params['Ids']:
                events_client.remove_targets(**remove_targets_params)
            events_client.delete_rule(**configuration.get('default_parameters', {}).get('remove_schedule', {}), 
                Name=full_schedule_name)
            return True
        except:
            return False
    else:
        return None

def connect_function(schedule_name, configuration={}, function_name='', function_service={}):
    if schedule_name and function_service.get('configuration', {}) and function_service.get('native', {}).get('Configuration', {}).get('FunctionArn'):
        events_client = boto3.client('events')
        full_schedule_name = '{namespace}-{schedule_name}'.format(namespace=configuration['namespace'], schedule_name=schedule_name)
        full_function_name = '{namespace}-{function_name}'.format(namespace=function_service['configuration'].get('namespace', ''), function_name=function_name)
        eventbus_name = configuration.get('default_parameters', {}).get('remove_schedule', {}).get('EventBusName')
        try:
            put_targets_params = {
                'Rule': full_schedule_name, 
                'Targets': [{'Id': full_function_name, 'Arn': function_service['native']['Configuration']['FunctionArn']}]
            }
            if eventbus_name:
                put_targets_params['EventBusName'] = eventbus_name
            events_client.put_targets(**put_targets_params)
            return True
        except:
            return False
    else:
        return None

def disconnect_function(schedule_name, configuration={}, function_name='', function_service={}):
    if schedule_name and function_service.get('configuration', {}) and function_service.get('native', {}).get('Configuration', {}).get('FunctionArn'):
        events_client = boto3.client('events')
        full_schedule_name = '{namespace}-{schedule_name}'.format(namespace=configuration['namespace'], schedule_name=schedule_name)
        full_function_name = '{namespace}-{function_name}'.format(namespace=function_service['configuration'].get('namespace', ''), function_name=function_name)
        eventbus_name = configuration.get('default_parameters', {}).get('remove_schedule', {}).get('EventBusName')
        try:
            remove_targets_params = {
                'Rule': full_schedule_name, 
                'Ids': [full_function_name]
            }
            if eventbus_name:
                remove_targets_params['EventBusName'] = eventbus_name
            events_client.remove_targets(**remove_targets_params)
            return True
        except:
            return False
    else:
        return None

def describe_native(schedule_name, configuration={}):
    if schedule_name:
        events_client = boto3.client('events')
        full_schedule_name = '{namespace}-{schedule_name}'.format(namespace=configuration['namespace'], schedule_name=schedule_name)
        eventbus_name = configuration.get('default_parameters', {}).get('remove_schedule', {}).get('EventBusName')
        try:
            describe_rule_params = {'Name': full_schedule_name}
            if eventbus_name:
                describe_rule_params['EventBusName'] = eventbus_name
            return events_client.describe_rule(**describe_rule_params)
        except:
            return {}
    else:
        return {}
    
