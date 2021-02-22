import json, boto3, base64

def render_element(record, prefix, class_name):
    attributes_list = ['{}="{}"'.format(k.lower(), v) for k, v in record.items()]
    return '<{prefix}-{class_name} {attributes_list}></{prefix}-{class_name}>'.format(prefix=prefix, class_name=class_name.lower(), attributes_list=' '.join(attributes_list))

    
def main(event, context):
    '''
    - triggered by view
    - event => {"options", "assets", "entity_type", "class_name", "entity_id", "field_name", "sort_field", "sort_direction", "page_name", "suffix",
                    "entity", page", "total_result_count": 1, "view_result_count"}
    - an example view to return records as custom HTML elements
    - returns an object with content_type, encoding and the base64-encoded text of the HTML element
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    result = ''
    options = event.get('options', {})
    prefix = options.get('prefix', 'element')
    class_name = event.get('class_name', 'Thing')
    entity_type = event.get('entity_type')
    if entity_type == 'query':
        elements = [render_element(p, prefix, class_name) for p in event.get('page', [])]
        result = ''.join(elements)
    elif entity_type == 'record' and event.get('entity'):
        result = render_element(event['entity'], prefix, class_name)
    return {'content_type': 'text/html', 'encoding': 'base64', 'body': base64.b64encode(bytes(result, 'utf-8'))}
    