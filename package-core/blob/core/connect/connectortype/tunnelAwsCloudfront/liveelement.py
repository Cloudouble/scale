environment = {
    'eventbus': {}
}

package = {}

component = {}

module = {
    'buckets': {
        'ap-southeast-1': 'ap-southeast-1.request.scale.live-element.net', 
        'us-east-1': 'us-east-1.request.scale.live-element.net', 
        '_': 'ap-southeast-2.request.scale.live-element.net'
    }
}

def run(processor_address, processor_input, synchronous=None, silent=None):
    return {} if synchronous else None