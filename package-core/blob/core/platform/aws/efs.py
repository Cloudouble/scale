import json, base64, os, mimetypes, boto3

def mount_partition(partition_name, options={}, configuration={}):
    if partition_name and configuration:
        efs_client = boto3.client('efs')
        full_partition_name = '{namespace}-{partition_name}'.format(namespace=configuration['namespace'], partition_name=partition_name)
        try:
            describe_result = [f.get('Name') for f in efs_client.describe_file_systems()['FileSystems']]
        except:
            describe_result = []
        if full_partition_name in describe_result:
            try:
                if options:
                    for method, method_params in option.items():
                        getattr(s3_client, method)(**method_params, Bucket=configuration['Bucket'])
                return True
            except:
                return False
        else:
            try:
                efs_client.create_file_system(**configuration.get('default_parameters', {}).get('mount_partition', {}), 
                    **options, CreationToken=configuration['FileSystemId'], Tags=[{'Key': 'Name', 'Value': full_partition_name}])['FileSystemId']
                return True
            except:
                return False
    else:
        return None


def unmount_partition(partition_name, configuration={}):
    if partition_name and configuration:
        efs_client = boto3.client('efs')
        full_partition_name = '{namespace}-{partition_name}'.format(namespace=configuration['namespace'], partition_name=partition_name)
        try:
            describe_result = [f.get('Name') for f in efs_client.describe_file_systems()['FileSystems']]
        except:
            describe_result = []
        if full_partition_name in describe_result:
            return False
        else:
            return True
    else:
        return None


def read(path, configuration):
    if path and configuration.get('LocalMountPath'):
        path = '{}/{}{}'.format(configuration['LocalMountPath'], configuration.get('root', ''), path)
        data_object = {}
        try:
            with open(path, 'r+b') as object_file:
                object_bytes = object_file.read()
            data_object['Body'] = base64.b64encode(object_bytes).decode('utf-8')
            try:
                data_object['ContentLength'] = os.path.getsize(path)
            except:
                pass
            try:
                data_object['ContentType'] = mimetypes.guess_type(path)
            except:
                pass
        except:
            pass
        return data_object
    else:
        return None


def write(path, data_object, configuration):
    if path and configuration.get('LocalMountPath'):
        path = '{}/{}{}'.format(configuration['LocalMountPath'], configuration.get('root', ''), path)
        try:
            with open(path, 'w+b') as object_file:
                object_file.write(base64.b64decode(data_object['Body']))
            return True
        except:
            return False
    else:
        return None
    

def delete(path, configuration):
    if path and configuration.get('LocalMountPath'):
        try:
            path = '{}/{}{}'.format(configuration['LocalMountPath'], configuration.get('root', ''), path)
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)
            return True
        except:
            return False
    else:
        return None


def ls(path, configuration):
    if path and configuration.get('LocalMountPath'):
        try:
            path = '{}/{}{}'.format(configuration['LocalMountPath'], configuration.get('root', ''), path)
            results = []
            with os.scandir(path) as it:
                for entry in it:
                    if not entry.name in ['.', '..']:
                        result.append(entry.name)
            return sorted(results)
        except:
            return []
    else:
        return []


def connect_function(partition_name, configuration={}, function_name='', function_service={}):
    return None


def disconnect_function(partition_name, configuration={}, function_name='', function_service={}):
    return None


def describe_native(partition_name, configuration={}):
    if partition_name and configuration:
        efs_client = boto3.client('efs')
        full_partition_name = '{namespace}-{partition_name}'.format(namespace=configuration['namespace'], partition_name=partition_name)
        try:
            describe_result = {f.get('Name'): f for f in efs_client.describe_file_systems()['FileSystems'] if f.get('Name')}
        except:
            describe_result = {}
        if full_partition_name in describe_result:
            return describe_result[full_partition_name]
        else:
            return {}
    else:
        return {}
