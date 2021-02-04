import json, boto3, uuid

def uuid_valid(s):
    try:
        uuid.UUID(s).version == 4
    except:
        return False
    return True

 
def main(event, context):
    #called from receive
    mask = []

    return mask
    
    
    
    
    
