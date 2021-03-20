import json, boto3, base64

def getpath(p, env):
    p = p.strip('/?')
    p = p[len(env['data_root']):] if p.startswith(env['data_root']) else p
    p = p[:-len('.json')] if p.endswith('.json') else p
    return p.strip('/').split('/')

def getprocessor(env, name, source='core', scope=None):
    return name if ':' in name else '{lambda_namespace}-{source}-{name}'.format(lambda_namespace=env['lambda_namespace'], source=source, name='{}-{}'.format(scope, name) if scope else name)
 
def main(event, context):
    '''
    - triggered by core/request
    - event => {authentication_channel_name: {credentials}}
    - takes care of authentication sub-processes
    - returns a connection object with (at least) a 'mask' property, which is overlaid onto _/connection/{connection_id}/connect.json
    
        *** IN PROGRESS ***
    
        install (triggered by changes to _/system/daemon/{daemon_type}.json): 
            1: create Lambda function with the daemon code in the core region
            2: writes any start-up views and masks 
            3: creates trigger from _/daemon/{daemon_type}/* to it's own Lambda 
        
        start (after install) (trigger by PUT to _/daemon/{daemon_type}/{daemon_id}/daemon.json): 
            1: invoke core-authentication with daemon credentials and writes the result to _/daemon/{daemon_type}/{daemon_id}/daemon.json
        
        pause: 
            1: remove trigger
        
        stop (after pause): 
            1: remove any subscriptions and feeds
            2: remove any stop records and queries
            
        remove (after stop):
            1: removes any remove views and masks
            2: removes Lambda function
            3: removes _/system/daemon/{daemon_type}.json
    
    '''
    env = context.client_context.env if context.client_context and context.client_context.env else event.get('_env', {})
    client_context = base64.b64encode(bytes(json.dumps({'env': env}), 'utf-8')).decode('utf-8')    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(env['bucket'])
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')


    
    
    return True
