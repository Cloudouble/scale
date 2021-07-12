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

def enable_schedule(schedule_name, configuration={}):
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

def disable_schedule(schedule_name, configuration={}):
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

