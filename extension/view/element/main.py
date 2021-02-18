import json, boto3, base64

def render_element(record, prefix, class_name):
    attributes_list = ['{}="{}"'.format(k.lower(), v) for k, v in record.items()]
    return '<{prefix}-{class_name} {attributes_list}></{prefix}-{class_name}>'.format(prefix=prefix, class_name=class_name.lower(), attributes_list=' '.join(attributes_list))

    
def main(event, context):
    '''
    - triggered by view.py
    - event => {"options", "assets", "entity_type", switches": {"connection_id", "class_name", "entity_id", "field_name", "sort_field", "sort_direction", "page_name", "suffix"},
                    "page", "total_result_count": 1, "view_result_count"}
    - an example view to return records as custom HTML elements
    - returns an object with content_type, encoding and the base64-encoded text of the HTML element
    '''
    result = ''
    options = event.get('options', {})
    switches = event.get('switches', {})
    prefix = options.get('prefix', 'element')
    class_name = switches.get('class_name', 'Thing')
    elements = [render_element(p, prefix, class_name) for p in event.get('page', [])]
    result = ''.join(elements)
    return {'content_type': 'text/html', 'encoding': 'base64', 'body': base64.b64encode( bytes(result, 'utf-8'))}
    