import json

configuration = json.loads('''
{
    "boot": {
        "computor": {
            "driver: {
                "aws_lambda": {
                    "namespace": "liveelement"
                }
            }
        }, 
        "storer": {
            "driver": {
                "aws_efs": {
                    "LocalMountPath": "../../../../system"
                }
            }, 
            "partition": "system", 
            "root": "/"
        }, 
        "eventbus": {
            "driver: {
                "aws_sqs": {
                }
            }
        }, 
    }
}
''')