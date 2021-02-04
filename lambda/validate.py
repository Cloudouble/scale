### expand to validate any uploaded thing... {entity={}, scope='', path=[]}

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

def main(record, context):
    # called by other lambdas to validate a record
    valid = False
    if record and type(record) is dict and record.get('@type') and uuid_valid(record.get('@id')):
        s3 = boto3.resource('s3')
        try:
            type_schema = json.loads(s3.Object(os.environ['bucket'], 'schema/classes/{}.json'.format(record['@type'])).get()['Body'].read().decode('utf-8'))
            if type_schema and type(type_schema) is dict:
                type_properties_map = type_schema.get('properties', {})
                non_core_record_properties = [p for p in record if p and type(p) is str and p[0] != '@']
                if type_properties_map and all([type_properties_map.get(p) for p in non_core_record_properties]):
                    valid = all([ any([validators.get(t, validators['Record'])(record[p]) for t in type_properties_map[p]]) for p in non_core_record_properties ])
        except:
            pass
    return valid

