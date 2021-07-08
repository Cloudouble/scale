import json, base64, os, mimetypes


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

