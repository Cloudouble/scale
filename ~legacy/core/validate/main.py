import json, boto3, base64, datetime, uuid, re
from datetime import datetime
from datetime import date
from datetime import time
from urllib.parse import urlparse

def datetime_valid(mod, s):
    try:
        mod.fromisoformat(dt_str)
    except:
        return False
    return True
    
def url_valid(s):
    try:
        urlparse(s)
    except:
        return False
    return True
    
def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True
        
def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
    

validators = {
    'True': lambda i: type(i) is bool and i, 
    'False': lambda i: type(i) is bool and not i, 
    'Boolean': lambda i: type(i) is bool, 
    'DateTime': lambda i: datetime_valid(datetime, i), 
    'Date': lambda i: datetime_valid(date, i), 
    'Time': lambda i: datetime_valid(time, i), 
    'Integer': lambda i: type(i) is int, 
    'Float': lambda i: type(i) is float, 
    'Number': lambda i: type(i) in [float, int], 
    'XPathType': lambda i: type(i) is str,
    'CssSelectorType': lambda i: type(i) is str,
    'URL': lambda i: url_valid(i),
    'Text': lambda i: type(i) is str,
    'Record': lambda i: type(i) is dict and len(i) == 2 and type(i.get('@type')) is str and uuid_valid(i.get('@id'))
}

def valid_view(view, direct=False):
    return all([
        type(view) is dict, 
        view.get('connection_type', 'connection') in ['connection', 'daemon'], 
        type(view.get('processor', None if direct else '')) is str, 
        type(view.get('view', '' if direct else None)) is str, 
        type(view.get('options', {})) is dict, 
        type(view.get('assets', {})) is dict, 
        type(view.get('field_name', '')) is str, 
        type(view.get('content_type', '')) is str, 
        type(view.get('suffix', '')) is str, 
        type(view.get('expires', 0)) is int, 
        type(view.get('sort_field', '@id')) is str, 
        view.get('sort_direction', 'ascending') in ['ascending', 'descending'], 
        type(view.get('min_index', 0)) is int, 
        type(view.get('max_index', 0)) is int])


def main(event, context):
    '''
    - triggered by core/request
    - {'entity': entity, 'entity_type': entity_type, 'class_name'?: class_name?, 'entity_id': entity_id}
    - validate the given record according to its datatype
    - return True if valid else False
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    valid = False
    if event and type(event['entity']) is dict and event.get('entity_type') and event.get('entity_id'):
        s3 = boto3.resource('s3')
        entity = event['entity']
        entity_type = event['entity_type']
        entity_id = event['entity_id']
        class_name = event.get('class_name')
        if entity_type == 'view':
            valid = valid_view(entity, True)
        elif entity_type == 'query':
            valid = type(entity.get('processor')) is str and type(entity.get('vector')) is list and type(entity.get('options', {})) is dict and type(entity.get('count', 0)) is int
        elif entity_type == 'feed':
            valid = valid_view(entity)
        elif entity_type == 'subscription':
            valid = valid_view(entity)
        elif entity_type in ['system', 'mask']:
            valid = type(entity) is dict
        elif entity_type == 'schema':
            valid = type(entity) is dict and entity.get('@context') and type(entity.get('@context')) is dict and entity.get('@graph') and type(entity.get('@graph')) is list and all([type(n) is dict for n in entity['@graph']])
        elif entity_type == 'record':
            if entity.get('@type') and entity.get('@id'):
                try:
                    type_schema = json.loads(s3.Object(env['bucket'], '{data_root}/system/class/{entity_type}.json'.format(data_root=env['data_root'], entity_type=entity['@type'])).get()['Body'].read().decode('utf-8'))
                except:
                    type_schema = {}
                if type_schema and type(type_schema) is dict and entity['@type'] == class_name and entity['@id'] == entity_id:
                    type_properties_map = type_schema.get('properties', {})
                    non_core_record_properties = [p for p in entity if p and type(p) is str and p[0] != '@']
                    if type_properties_map and all([type_properties_map.get(p) for p in non_core_record_properties]):
                        valid = all([ any([validators.get(t, validators['Record'])(entity[p]) for t in type_properties_map[p]]) for p in non_core_record_properties ])
                        if not valid:
                            invalid_properties = []
                            datatypes_index = {}
                            for property_name in non_core_record_properties:
                                property_valid = False
                                for t in type_schema.get(property_name, []):
                                    if t in validators:
                                        property_valid = validators[t](entity[property_name])
                                    else:
                                        if not datatypes_index:
                                            datatypes_index_path = '{data_root}/system/datatype/index.json'.format(data_root=env['data_root'])
                                            datatypes_index = json.loads(s3_client.get_object(Bucket=env['bucket'], Key=datatypes_index_path)['Body'].read().decode('utf-8'))
                                        if datatypes_index:
                                            datatype_definition = datatypes_index.get(t)
                                            if datatype_definition:
                                                if datatype_definition.get('@regex'):
                                                    property_valid = re.fullmatch(datatype_definition['@regex'], entity[property_name])
                                                if not property_valid and datatype_definition.get('@lambda'):
                                                    property_valid = eval(datatype_definition['@lambda'], {}, {'class': entity.get('@type'), 'property': property_name, 'datatype': t, 'value': entity[property_name], 'record': entity})
                                                if not property_valid and datatype_definition.get('@processor'):
                                                    try:
                                                        property_valid = json.loads(lambda_client.invoke(FunctionName=getprocessor(env, datatype_definition['@processor'], 'extension', 'validator'), 
                                                        Payload=bytes(json.dumps({'class': entity.get('@type'), 'property': property_name, 'datatype': t, 'value': entity[property_name], 'record': entity}), 'utf-8'), ClientContext=client_context)['Payload'].read().decode('utf-8')):
                                                    except:
                                                        property_valid = False
                                if not property_valid:
                                    valid = False
                                    break
    return valid
