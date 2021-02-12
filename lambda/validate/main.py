env = {"bucket": "scale.live-element.net", "lambda_namespace": "liveelement-scale", "system_root": "_"}

import json, boto3, os, datetime, uuid
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


def valid_view(view):
    return all([type(view) is dict, type(view.get('view_id')) is str, type(view.get('expires', 0)) is int])


def main(event, context):
    '''
    - triggered by clean.py, write.py
    - validate the given record according to its datatype
    
    {'entity': entity, 'switches': {'entity_type': entity_type, 'class_name'?: class_name?, 'entity_id': entity_id}}
    entity_type => view query feed subscription system record
    '''
    valid = False
    if event and type(event['entity']) is dict and type(event.get('switches')) is dict and event['switches'].get('entity_type') and event['switches'].get('entity_id'):
        s3 = boto3.resource('s3')
        entity = event['entity']
        entity_type = event['switches']['entity_type']
        entity_id = event['switches']['entity_id']
        class_name = event['switches'].get('class_name')
        if entity_type == 'view':
            # {processor='', ?options={}, ?assets={alias: assetpath}}
            valid = type(entity.get('processor')) is str and type(entity.get('options', {})) is dict and type(entity.get('assets', {})) is dict
        elif entity_type == 'query':
            # {processor='', ?options={}, vector=[], ?count=0}
            valid = type(entity.get('processor')) is str and type(entity.get('vector')) is list and type(entity.get('options', {})) is dict and type(entity.get('count', 0)) is int
        elif entity_type == 'feed':
            # {sort_field='', ?sort_direction='ascending', ?min_index=0, ?max_index=1000, view=[{view_id='', ?expires=0, ?max=0, ?count=0, ?last=0, ?next=0}]}
            valid = all([
                type(entity.get('sort_field')) is str, 
                type(entity.get('sort_direction')) in ['ascending', 'descending'], 
                type(entity.get('min_index', 0)) is int, 
                type(entity.get('min_index', 0)) is int, 
                type(entity.get('max_index', 0)) is int, 
                type(entity.get('view')) is list, 
                all([valid_view(v) for v in entity['view']])
            ])
        elif entity_type == 'subscription':
            # {view=[{view_id='', ?expires=0, ?max=0, ?count=0, ?last=0, ?next=0}]}
            valid = all([type(entity.get('view')) is list, all([valid_view(v) for v in entity['view']])])
        elif entity_type == 'system':
            valid = type(entity) is dict
        elif entity_type == 'record':
            if entity.get('@type') and entity.get('@id'):
                type_schema = json.loads(s3.Object(env['bucket'], '{system_root}/schema/classes/{entity_type}.json'.format(system_root=env['system_root'], entity_type=entity['@type'])).get()['Body'].read().decode('utf-8'))
                if type_schema and type(type_schema) is dict and entity['@type'] == class_name and entity['@id'] == entity_id:
                    type_properties_map = type_schema.get('properties', {})
                    non_core_record_properties = [p for p in entity if p and type(p) is str and p[0] != '@']
                    if type_properties_map and all([type_properties_map.get(p) for p in non_core_record_properties]):
                        valid = all([ any([validators.get(t, validators['Record'])(entity[p]) for t in type_properties_map[p]]) for p in non_core_record_properties ])
    return valid
