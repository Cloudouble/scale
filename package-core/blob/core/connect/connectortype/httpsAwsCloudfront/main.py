import liveelement
import json, boto3

def main(packageObject, componentObject, moduleObject, operation):
    adaptorConfiguration = liveelement.run('core.storer', {
        'operation': 'read', 
        'source': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration']
    }, 'sync') if operation in ['create', 'update', 'delete'] else {}
    if operation in ['create', 'update'] and adaptorConfiguration and adaptorConfiguration['DistributionConfig']:
        cloudfront_client = boto3.client('cloudfront')
        if operation == 'update' and adaptorConfiguration['Id']:
            cloudfront_client.update_distribution(DistributionConfig=adaptorConfiguration['DistributionConfig'], Id=adaptorConfiguration['Id'])
        elif operation == 'create' and not adaptorConfiguration['Id']:
            adaptorConfiguration['Id'] = cloudfront_client.create_distribution(DistributionConfig=adaptorConfiguration['DistributionConfig'])['Distribution']['Id']
            liveelement.run('core.storer', {
                'operation': 'update', 
                'source': adaptorConfiguration, 
                'target': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration'], 
            }, False, 'silent')
    elif operation == 'delete' and adaptorConfiguration['Id']:
        cloudfront_client.delete_distribution(Id=adaptorConfiguration['Id'])
        del adaptorConfiguration['Id']
        liveelement.run('core.storer', {
            'operation': 'update', 
            'source': adaptorConfiguration, 
            'target': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration'], 
        }, False, 'silent')
