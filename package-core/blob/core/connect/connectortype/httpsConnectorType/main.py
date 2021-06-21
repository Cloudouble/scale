import liveelement

def main(event):
    request = liveelement.adaptor.parse(event)
    liveelement.storer.write(request)
    liveelement.eventbus.dispatch_event()



