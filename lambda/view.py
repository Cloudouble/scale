import json, boto3, os, time

def main(event, context):
    # called by other functions to generate views on given connections and queries
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    counter = 0
    now = time.time()
    view_key = '_/connection/{feed_connection_id}/view/{class_name}/{query_id}/{sort_field}/{sort_direction}/{min_index}-{max_index}.{view_id}'.format(**event)

    
    
    
    return counter
