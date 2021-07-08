import liveelement, json

import pyshacl
from rdflib import Graph, plugin
from rdflib.serializer import Serializer

def main(package, component, module, contexts, configuration, inputObject):

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



# remove for Lambda, only for local testing

system_path = liveelement.configuration.configuration['working_partitions']['system']['driver']['efs']['LocalMountPath']

with open('{}/core/package/core.json'.format(system_path)) as package_file:
    package = json.loads(package_file.read())

with open('{}/core/component/validator.json'.format(system_path)) as component_file:
    component = json.loads(component_file.read())

with open('{}/core/value/context/core.json'.format(system_path)) as context_file:
    context = json.loads(context_file.read())

module = {}

configuration = {}

with open('{}/core/application/console.json'.format(system_path)) as input_file:
    input_object = json.loads(input_file.read())

print(json.dumps(input_object, indent=4, sort_keys=True))

'''with open(validator_path) as validator_file:
    validator_text = validator_file.read()
validator_object = json.loads(validator_text)
validator_object['@context'] = context_object
'''

#main(package, component, module, context, configuration, inputObject)

