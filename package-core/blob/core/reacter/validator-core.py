import environment, compute, store


def main(event, context):
    #(scope, module, live)
    scope = event.get('scope')
    module = event.get('module')
    live = event.get('live')
    retval = False
    if scope and module and live:
        
        
        
        request = store.read(path).get('live', {})
        object_path = request.get('path', '')
        object_path_split = object_path.split('/')
        if object_path_split and len(object_path_split) > 1 and type(request.get('live')) is dict:
            is_valid = False
            if object_path_split[0] == 'core' and len(object_path_split) == 3:
                scope, module = object_path_split[1:]
                module, suffix = (module.split('.') + 2 * [''])[:2]
                if suffix == 'json':
                    is_valid = compute.run_sync('core-validator-core', scope, module, request['live'])
            elif object_path_split[0] == 'record' and len(object_path_split) == 2:
                record_uuid, suffix = (object_path_split[1].split('.') + 2 * [''])[:2]
                if suffix == 'json':
                    is_valid = compute.run_sync('core-validator-record', record_uuid, request['live'])
            elif object_path_split[0] == 'import' and len(object_path_split) == 2 and all([request.get(p) for p in ['path', 'body', 'content_type', 'encoding']]):
                is_valid = compute.run_sync('core-validator-import', request['path'], request['body'], request['content_type'], request['encoding'])
            elif object_path_split[0] == 'connection' and len(object_path_split) == 4 and object_path_split[3] in ['connect.json', 'listen.json']:
                connection_type, connection_identifier, trailer = (object_path_split[1:] + 3 * [''])[:3]
                trailer, suffix = (trailer.split('.') + 2 * [''])[:2]
                if suffix == 'json':
                    is_valid = compute.run_sync('core-validator-connection', connection_type, connection_identifier, trailer, request['live'])
            if is_valid and all([request.get(p) for p in ['connection_type', 'connection_identifier', 'operation', 'path', 'live']]):
                masked_object = compute.run_sync('core-mask', request['connection_type'], request['connection_identifier'], request['operation'], request['path'], request['live'])
                if masked_object:
                    if request['operation'] == 'delete':
                        retval = store.delete(request['path'])
                    elif request['operation'] in ['create', 'update']:
                        retval = getattr(store, request['operation'])(request['path'], masked_object)
    return retval
