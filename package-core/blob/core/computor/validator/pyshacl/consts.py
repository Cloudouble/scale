# -*- coding: utf-8 -*-
from rdflib import OWL, RDF, RDFS
from rdflib.namespace import Namespace


SH = Namespace('http://www.w3.org/ns/shacl#')

# Classes
RDF_Property = RDF.term('Property')
RDF_List = RDF.term('List')
RDFS_Resource = RDFS.term('Resource')
RDFS_Class = RDFS.term('Class')
OWL_Ontology = OWL.term("Ontology")
OWL_Class = OWL.term("Class")
OWL_DatatypeProperty = OWL.term("DatatypeProperty")
SH_NodeShape = SH.term('NodeShape')
SH_PropertyShape = SH.term('PropertyShape')
SH_ValidationResult = SH.term('ValidationResult')
SH_ValidationReport = SH.term('ValidationReport')
SH_Violation = SH.term('Violation')
SH_Info = SH.term('Info')
SH_Warning = SH.term('Warning')
SH_IRI = SH.term('IRI')
SH_BlankNode = SH.term('BlankNode')
SH_Literal = SH.term('Literal')
SH_BlankNodeOrIRI = SH.term('BlankNodeOrIRI')
SH_BlankNodeORLiteral = SH.term('BlankNodeOrLiteral')
SH_IRIOrLiteral = SH.term('IRIOrLiteral')
SH_ConstraintComponent = SH.term('ConstraintComponent')
SH_SHACLFunction = SH.term('SHACLFunction')
SH_SPARQLFunction = SH.term('SPARQLFunction')
SH_SPARQLRule = SH.term('SPARQLRule')
SH_TripleRule = SH.term('TripleRule')
SH_SPARQLTarget = SH.term('SPARQLTarget')
SH_SPARQLTargetType = SH.term('SPARQLTargetType')
SH_JSTarget = SH.term('JSTarget')
SH_JSTargetType = SH.term('JSTargetType')
SH_JSFunction = SH.term('JSFunction')

# predicates
RDF_type = RDF.term('type')
RDF_first = RDF.term('first')
RDF_rest = RDF.term('rest')
RDF_object = RDF.term('object')
RDF_predicate = RDF.term('predicate')
RDF_subject = RDF.term('subject')
RDFS_subClassOf = RDFS.term('subClassOf')
RDFS_comment = RDFS.term('comment')
SH_path = SH.term('path')
SH_deactivated = SH.term('deactivated')
SH_message = SH.term('message')
SH_name = SH.term('name')
SH_description = SH.term('description')
SH_property = SH.term('property')
SH_node = SH.term('node')
SH_target = SH.term('target')  # from advanced spec
SH_targetClass = SH.term('targetClass')
SH_targetNode = SH.term('targetNode')
SH_targetObjectsOf = SH.term('targetObjectsOf')
SH_targetSubjectsOf = SH.term('targetSubjectsOf')
SH_focusNode = SH.term('focusNode')
SH_resultSeverity = SH.term('resultSeverity')
SH_resultPath = SH.term('resultPath')
SH_resultMessage = SH.term('resultMessage')
SH_sourceConstraint = SH.term('sourceConstraint')
SH_sourceConstraintComponent = SH.term('sourceConstraintComponent')
SH_sourceShape = SH.term('sourceShape')
SH_severity = SH.term('severity')
SH_value = SH.term('value')
SH_conforms = SH.term('conforms')
SH_result = SH.term('result')
SH_inversePath = SH.term('inversePath')
SH_alternativePath = SH.term('alternativePath')
SH_zeroOrMorePath = SH.term('zeroOrMorePath')
SH_oneOrMorePath = SH.term('oneOrMorePath')
SH_zeroOrOnePath = SH.term('zeroOrOnePath')
SH_prefixes = SH.term('prefixes')
SH_prefix = SH.term('prefix')
SH_namespace = SH.term('namespace')
SH_rule = SH.term('rule')
SH_condition = SH.term('condition')
SH_order = SH.term('order')
SH_construct = SH.term('construct')
SH_subject = SH.term('subject')
SH_predicate = SH.term('predicate')
SH_object = SH.term('object')
SH_parameter = SH.term('parameter')
SH_ask = SH.term('ask')
SH_select = SH.term('select')
SH_this = SH.term('this')
SH_filterShape = SH.term('filterShape')
SH_nodes = SH.term('nodes')
SH_union = SH.term('union')
SH_intersection = SH.term('intersection')
SH_datatype = SH.term('datatype')
SH_nodeKind = SH.term('nodeKind')
SH_optional = SH.term('optional')
SH_js = SH.term('js')
SH_jsFunctionName = SH.term('jsFunctionName')
SH_jsLibrary = SH.term('jsLibrary')