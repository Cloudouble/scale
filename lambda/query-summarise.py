import json, boto3, os

def main(event, context):
    #reacts to updated query results in /query/{query_id}/{record_initial}.json snd generates /query/{query_id}.json
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    
    query_map = {}
    for pair in [record['s3']['object']['key'].strip('/?').removesuffix('.json').split('/')[1:3] for record in event['Records']]:
        query_map[pair[0]] = query_map[pair[0]] if query_map.get(pair[0]) else []
        query_map[pair[0]].append(pair[1])
    for query_id, query_initial_list in query_map.items():
        #query_summary = {'count': 0, 'initials': [], 'type': 'Thing', 'fields': []}
        
        query_summary_key = 'query/{query_id}.json'.format(query_id=query_id)
        try: 
            query_summary = json.loads(bucket.get_object(Key=query_summary_key)['Body'].read().decode('utf-8'))
        except:
            query_summary = {}
        query_summary['initials'] = query_summary['initials'] if query_summary.get('initials') else []
        query_summary['initials'] = sorted(list(set(query_summary['initials'] + query_initial_list)))
        
        
        
        bucket.put_object(Body=bytes(json.dumps(query_summary), 'utf-8'), Key=query_summary_key, ContentType='application/json')
        

        
        
        
        if len(path) == 4:
            record_type, record_id, record_version = path[1:]
            record_object = json.loads(bucket.get_object(Key='record/{record_type}/{record_id}.json'.format(record_type=record_type, record_id=record_id))['Body'].read().decode('utf-8'))
            updated_fields = sorted(json.loads(bucket.get_object(Key=record['s3']['object']['key'])['Body'].read().decode('utf-8')))
            query_list = []
            for updated_field in updated_fields:
                try:
                    query_list.entend(json.loads(bucket.get_object(Key='vector/{record_type}/{updated_field}.json'.format(record_type=record_type, updated_field=updated_field))['Body'].read().decode('utf-8')))
                except:
                    pass
            query_list = sorted(list(set(query_list)))
            for query_id in query_list:
                query_payload = {'purpose': 'query', 'record': record_object}
                query_result = json.loads(lambda_client.invoke(FunctionName=query_id, InvocationType='RequestResponse', Payload=bytes(json.dumps(query_payload), 'utf-8'))['Payload'].read().decode('utf-8'))
                query_index_key = 'query/{query_id}/{record_initial}.json'.format(query_id=query_id, record_initial=record_id[0])
                query_index = json.loads(bucket.get_object(Key=query_index_key)['Body'].read().decode('utf-8'))
                query_index_changed = False
                if query_result is True and record_id not in query_result:
                    query_index.append(record_id).sort()
                    query_index_changed = True
                elif query_result is False and record_id in query_result:
                    query_index.remove(record_id).sort()
                    query_index_changed = True
                if query_index_changed:
                    bucket.put_object(Body=bytes(json.dumps(query_index), 'utf-8'), Key=query_index_key, ContentType='application/json')
                    counter = counter + 1
    return counter
    
    
