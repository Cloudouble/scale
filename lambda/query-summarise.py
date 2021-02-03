import json, boto3, os

def main(event, context):
    #reacts to updated query results in /query/{record_type}/{query_id}/{record_initial}.json snd generates /query/{query_id}.json
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['bucket'])
    query_triples = [record['s3']['object']['key'].strip('/?').removesuffix('.json').split('/')[1:4] for record in event['Records']]
    query_initial_map = {}
    query_type_map = {}
    for triple in query_triples:
        query_initial_map[triple[0]] = query_initial_map.get(triple[0], [])
        query_initial_map[triple[0]].append(triple[1])
        query_type_map[triple[0]] = query_initial_map.get(triple[0], triple[2])
    counter = 0
    for query_id, query_initial_list in query_initial_map.items():
        query_summary_key = 'query/{record_type}/{query_id}.json'.format(record_type=query_type_map[query_id], query_id=query_id)
        try: 
            query_summary = json.loads(bucket.get_object(Key=query_summary_key)['Body'].read().decode('utf-8'))
        except:
            query_summary = {}
        query_summary['initials'] = query_summary.get('initials', {})
        for initial in query_initial_list:
            try: 
                query_index_key = 'query/{record_type}/{query_id}/{record_initial}.json'.format(record_type=query_type_map[query_id], query_id=query_id, record_initial=initial)
                query_index = json.loads(bucket.get_object(Key=query_index_key)['Body'].read().decode('utf-8'))
            except:
                query_index = []
            query_summary['initials'][initial] = len(query_index)
        query_summary['count'] = sum(list(query_summary['initials'].values()))
        bucket.put_object(Body=bytes(json.dumps(query_summary), 'utf-8'), Key=query_summary_key, ContentType='application/json')
        counter = counter + 1
    return counter