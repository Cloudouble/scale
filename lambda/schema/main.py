import urllib.request, json, boto3, os

def main(event, context):
    '''
    - triggered on-demand by an administrator
    - updates schema data to all system paths under /schema
    '''
    release = '11.01'
    feed = 'https://schema.org/version/{}/schemaorg-all-https.jsonld'.format(release)
    feed_response = urllib.request.urlopen(feed)
    feed_text = feed_response.read().decode('utf-8')
    graph = json.loads(feed_text)['@graph']
    
    properties_list = [p for p in graph if (p.get('@type') and ((type(p['@type']) is str and p['@type'] == 'rdf:Property') or (type(p['@type']) is list and 'rdf:Property' in p['@type'])))]
    properties = {}
    for prop in properties_list:
        rdfslabel = prop['rdfs:label'] if type(prop['rdfs:label']) is str else (prop['rdfs:label'].get('@value') if type(prop['rdfs:label']) is dict else None)
        rdfscomment = prop['rdfs:comment'] if type(prop['rdfs:comment']) is str else (prop['rdfs:comment'].get('@value') if type(prop['rdfs:comment']) is dict else None)
        range_includes = prop.get('schema:rangeIncludes', [])
        range_includes = [range_includes] if range_includes and type(range_includes) is dict else range_includes
        domain_includes = prop.get('schema:domainIncludes', [])
        domain_includes = [domain_includes] if domain_includes and type(domain_includes) is dict else domain_includes
        properties[rdfslabel] = {
            'label': rdfslabel, 
            'comment': rdfscomment, 
            'types': [r.get('@id') for r in range_includes], 
            'classes': [r.get('@id') for r in domain_includes], 
            'release': release
        }
        properties[rdfslabel]['types'] = [r for r in properties[rdfslabel]['types'] if r]
        properties[rdfslabel]['types'] = [r.split(':')[-1] for r in properties[rdfslabel]['types']]
        properties[rdfslabel]['classes'] = [r for r in properties[rdfslabel]['classes'] if r]
        properties[rdfslabel]['classes'] = [r.split(':')[-1] for r in properties[rdfslabel]['classes']]
        

    def get_parent_classes(c, all_parent_classes=[]):
        all_parent_classes = all_parent_classes if all_parent_classes else [c]
        sc = classes[c].get('subclassof', [])
        for cc in sc:
            all_parent_classes.append(cc)
            get_parent_classes(cc, all_parent_classes)
        return all_parent_classes

    class_list = [p for p in graph if (p.get('@type') and ((type(p['@type']) is str and p['@type'] == 'rdfs:Class') or (type(p['@type']) is list and 'rdfs:Class' in p['@type'])))]
    classes = {}
    for c in class_list:
        rdfslabel = c['rdfs:label'] if type(c['rdfs:label']) is str else (c['rdfs:label'].get('@value') if type(c['rdfs:label']) is dict else None)
        rdfscomment = c['rdfs:comment'] if type(c['rdfs:comment']) is str else (c['rdfs:comment'].get('@value') if type(c['rdfs:comment']) is dict else None)
        subclassof = [s.get('@id') for s in c.get('rdfs:subClassOf', [])] if type(c.get('rdfs:subClassOf', [])) is list else [c.get('rdfs:subClassOf', {}).get('@id')]
        subclassof = [s.split(':')[-1] for s in subclassof]
        classes[rdfslabel] = {
            'label': rdfslabel, 
            'comment': rdfscomment, 
            'subclassof': subclassof, 
            'release': release
        }

    for n, d in classes.items():
        d['parents'] = sorted(list(set(get_parent_classes(n))))
        d['parents'].remove(n)
    for n, d in classes.items():
        d['children'] = sorted(list(set([nn for nn, dd in classes.items() if n in dd.get('parents', [])])))
    for p, pd in properties.items():
        pd['classes'] = pd.get('classes', [])
        for pdc in pd['classes']:
            pd['classes'] = sorted(list(set(pd['classes'] + classes.get(pdc, {}).get('children', []))))
    for n, d in classes.items():
        d['properties'] = { p: properties.get(p, {}).get('types', []) for p in sorted(list(set([pn for pn, pd in properties.items() if n in pd.get('classes', [])]))) }

    
    datatype_list = [p for p in graph if (p.get('@type') and ((type(p['@type']) is str and p['@type'] == 'schema:DataType') or (type(p['@type']) is list and 'schema:DataType' in p['@type'])))]
    boolean_list = [p for p in graph if (p.get('@type') and ((type(p['@type']) is str and p['@type'] == 'schema:Boolean') or (type(p['@type']) is list and 'schema:Boolean' in p['@type'])))]
    other_list = [p for p in graph if p['@id'] in ['schema:Float', 'schema:Integer', 'schema:CssSelectorType', 'schema:PronounceableText', 'schema:URL', 'schema:XPathType']]
    datatypes = {}
    for d in datatype_list + boolean_list + other_list:
        rdfslabel = d['rdfs:label'] if type(d['rdfs:label']) is str else (d['rdfs:label'].get('@value') if type(d['rdfs:label']) is dict else None)
        rdfscomment = d['rdfs:comment'] if type(d['rdfs:comment']) is str else (d['rdfs:comment'].get('@value') if type(d['rdfs:comment']) is dict else None)
        datatypes[rdfslabel] = {
            'label': rdfslabel, 
            'comment': rdfscomment, 
            'release': release
        }

        
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    bucket.put_object(Body=bytes(json.dumps(classes), 'utf-8'), ContentType='application/json', Key='schema/classes.json')
    bucket.put_object(Body=bytes(json.dumps(properties), 'utf-8'), ContentType='application/json', Key='schema/properties.json')
    bucket.put_object(Body=bytes(json.dumps(datatypes), 'utf-8'), ContentType='application/json', Key='schema/datatypes.json')
        
    for k, v in properties.items():
        bucket.put_object(Body=bytes(json.dumps(v), 'utf-8'), ContentType='application/json', Key='schema/properties/{}.json'.format(k))
    for k, v in classes.items():
        bucket.put_object(Body=bytes(json.dumps(v), 'utf-8'), ContentType='application/json', Key='schema/classes/{}.json'.format(k))
    for k, v in datatypes.items():
        bucket.put_object(Body=bytes(json.dumps(v), 'utf-8'), ContentType='application/json', Key='schema/datatypes/{}.json'.format(k))
        
    return True
