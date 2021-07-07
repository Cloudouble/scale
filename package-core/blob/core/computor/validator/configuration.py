import json

configuration = json.loads('''
{
    "namespace": "liveelement", 
    "working_partitions": {
        "system": {
            "driver": {
                "efs": {
                    "LocalMountPath": "../../../../system"
                }
            }, 
            "root": "/"
        }, 
        "scratchpad": {
            "driver": {
                "efs": {
                    "LocalMountPath": "../../../../scratchpad"
                }
            }, 
            "root": "/"
        }, 
        "modified": {
            "driver": {
                "efs": {
                    "LocalMountPath": "../../../../modified"
                }
            }, 
            "root": "/"
        }, 
        "archive": {
            "driver": {
                "s3": {
                    "Bucket": "scale.live-element.net"
                }
            }, 
            "root": "_/archive/"
        }
    }
}
''')