import json

import pyshacl

from rdflib import Graph, plugin
from rdflib.serializer import Serializer


def main(event, context):
    
    from os import listdir
    
    object_path = '../../../../system/core/application/console.json'
    
    context_path = '../../../../system/core/value/context/core.json'
    
    validator_path = '../../../../system/core/validator/class/Application.sh.json'
    
    print(' ')

    with open(context_path) as context_file:
        context_text = context_file.read()
    context_object = json.loads(context_text)

    with open(object_path) as object_file:
        object_text = object_file.read()
    object_object = json.loads(object_text)
        
    object_object['@context'] = context_object
    
    with open(validator_path) as validator_file:
        validator_text = validator_file.read()
    validator_object = json.loads(validator_text)
    validator_object['@context'] = context_object
    
    validator_ancestors = []
    
    
        
    object_as_rdf_graph = Graph().parse(data=json.dumps(object_object), format='json-ld')

    validator_as_rdf_graph = Graph().parse(data=json.dumps(validator_object), format='json-ld')

    
    print(object_as_rdf_graph.serialize(format='n3', indent=4).decode('utf-8'))
    
    print(' --- ')
    
    print(validator_as_rdf_graph.serialize(format='n3', indent=4).decode('utf-8'))

    print(' --- ')
    
    r = pyshacl.validate(object_as_rdf_graph, shacl_graph=validator_as_rdf_graph)
    
    conforms, results_graph, results_text = r    
    
    print(' --- ')
    print(conforms)
    
    print(' --- ')
    print(results_graph.serialize(format='n3', indent=4).decode('utf-8'))

    print(' --- ')
    print(results_text)

    print(' ')
    
    return True

main({}, {})