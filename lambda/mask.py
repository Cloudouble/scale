import json, boto3, os, time

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main(event, context):
    # called by other functions to determine the masking of a given entity and connection
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
