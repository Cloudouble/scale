import liveelement
import json, boto3

def main(packageObject, componentObject, moduleObject, operation):
    adaptorConfiguration = liveelement.run('core.storer', {
        'operation': 'read', 
        'source': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration']
    }, 'sync') if operation in ['create', 'update', 'delete'] else {}
    if operation in ['create', 'update'] and adaptorConfiguration and adaptorConfiguration.get('CloudFront') and adaptorConfiguration['CloudFront'].get('DistributionConfig'):
        cloudfront_client = boto3.client('cloudfront')
        if operation == 'update' and adaptorConfiguration['CloudFront'].get('Id'):
            cloudfront_client.update_distribution(DistributionConfig=adaptorConfiguration['CloudFront']['DistributionConfig'], Id=adaptorConfiguration['CloudFront']['Id'])
        elif operation == 'create' and not adaptorConfiguration['CloudFront'].get('Id'):
            adaptorConfiguration['Cloudront']['Id'] = cloudfront_client.create_distribution(DistributionConfig=adaptorConfiguration['CloudFront']['DistributionConfig'])['Distribution']['Id']
            liveelement.run('core.storer', {
                'operation': 'update', 
                'source': adaptorConfiguration, 
                'target': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration'], 
            }, False, 'silent')
    elif operation == 'delete' and adaptorConfiguration.get('CloudFront', {}).get('Id'):
        cloudfront_client.delete_distribution(Id=adaptorConfiguration['Id'])
        del adaptorConfiguration['CloudFront']['Id']
        liveelement.run('core.storer', {
            'operation': 'update', 
            'source': adaptorConfiguration, 
            'target': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration'], 
        }, False, 'silent')
