import json

import pyshacl

from rdflib import Graph, plugin
from rdflib.serializer import Serializer


def main(event, context):
    
    from os import listdir
    
    object_path = '../../../../system/core/application/console.json'
    
    print('starting...')
    
    with open(object_path) as object_file:
        object_text = object_file.read()
    object_object = json.loads(object_text)
        
        
        
    g = Graph().parse(data=object_text, format='json-ld')
    
    print(g.serialize(format='json-ld', indent=4))

    #object_as_rdf_graph
    
    #r = pyshacl.validate(object_as_rdf_graph, shacl_graph=validator_as_shacl_graph)
    #conforms, results_graph, results_text = r    
    
    return True

main({}, {})