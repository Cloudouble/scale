import json, boto3, base64


def main(event, context):
    '''
    - triggered by core/view
    - event => {"options", "assets", "entity_type", "class_name", "entity_id", "field_name", "sort_field", "sort_direction", "page_name", "suffix",
                    "entity", page", "total_result_count": 1, "view_result_count"}
    - an example view to return records as non-traversed JSON records
    - returns an object with content_type, encoding and the base64-encoded text of the JSON record(s)
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')
    result = ''
    options = event.get('options', {})
    prefix = options.get('prefix', 'element')
    class_name = event.get('class_name', 'Thing')
    entity_type = event.get('entity_type')
    if entity_type == 'query':
        result = event.get('page', [])
    elif entity_type == 'record' and event.get('entity'):
        result = event['entity']
    return {'content_type': 'application/json', 'encoding': 'base64', 'body': base64.b64encode(bytes(json.dumps(result), 'utf-8'))}
    