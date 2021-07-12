import liveelement
def lambda_function(event, context):
    liveelement.process_events('system', event)
