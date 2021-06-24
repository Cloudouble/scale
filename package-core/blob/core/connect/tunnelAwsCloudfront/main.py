import liveelement
import json, boto3

def main(packageObject, componentObject, moduleObject, operation):
    adaptorConfiguration = liveelement.run('core.storer', {
        'operation': 'read', 
        'source': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration']
    }, 'sync') if operation in ['create', 'update', 'delete'] else {}
    if operation in ['create', 'update'] and adaptorConfiguration:
        if adaptorConfiguration.get('CloudFront') and adaptorConfiguration['CloudFront'].get('DistributionConfig'):
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
        if adaptorConfiguration.get('ApiGateway'):
            apigatewayv2_client = boto3.client('apigatewayv2')
            if operation == 'update' and adaptorConfiguration['ApiGateway'].get('ApiId'):
                apigatewayv2_client.update_api(**adaptorConfiguration['ApiGateway'])
            elif operation == 'create' and not adaptorConfiguration['CloudFront'].get('Id'):
                adaptorConfiguration['ApiGateway']['Id'] = apigatewayv2_client.create_api(**adaptorConfiguration['ApiGateway'])['ApiId']
                # lambda deploy function
                # lamba add permission
                # websocketIntegrationUri="arn:aws:lambda:$coreRegion:$accountId:function:$lambdaNamespace-core-socket"
                # websocketIntegrationPath="arn:aws:apigateway:$coreRegion:lambda:path/2015-03-31/functions/$websocketIntegrationUri/invocations"
                integration_id = apigatewayv2_client.create_integration(ApiId=adaptorConfiguration['ApiGateway']['Id'], ConnectionType='INTERNET', 
                    ContentHandlingStrategy='CONVERT_TO_TEXT', IntegrationMethod='POST', IntegrationType='AWS_PROXY', IntegrationUri='', 
                    PassthroughBehavior='WHEN_NO_MATCH')['IntegrationId']
                for route in ['$connect', '$disconnect', '$default']:
                    apigatewayv2_client.create_route(ApiId=adaptorConfiguration['ApiGateway']['Id'], RouteKey=route, Target='integrations/{}'.format(integration_id))
                liveelement.run('core.storer', {
                    'operation': 'update', 
                    'source': adaptorConfiguration, 
                    'target': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration'], 
                }, False, 'silent')
    elif operation == 'delete': 
        if adaptorConfiguration.get('CloudFront', {}).get('Id'):
            cloudfront_client.delete_distribution(Id=adaptorConfiguration['Id'])
            del adaptorConfiguration['CloudFront']['Id']
            liveelement.run('core.storer', {
                'operation': 'update', 
                'source': adaptorConfiguration, 
                'target': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration'], 
            }, False, 'silent')
        if adaptorConfiguration.get('ApiGateway', {}).get('Id'):
            cloudfront_client.delete_api(Id=adaptorConfiguration['ApiGateway']['Id'])
            del adaptorConfiguration['ApiGateway']['Id']
            liveelement.run('core.storer', {
                'operation': 'update', 
                'source': adaptorConfiguration, 
                'target': moduleObject['https://live-element.net/reference/scale/core/property/associatedAdaptorConfiguration'], 
            }, False, 'silent')
