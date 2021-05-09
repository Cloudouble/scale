window.LiveElement.Live.processors.IdeTunnelCreate = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_handle = window.LiveElement.Scale.Core.generateUUID4()
        window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_url = `${window.localStorage.getItem('system:system_access_url').replace('https:', 'wss:')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/tunnel/${window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_handle}`
        window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_socket = new WebSocket(window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_url)
        window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_socket, 'IdeTunnelCreate', 'message', true, true)
    } else if (handlerType == 'subscription') {
        window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_id = input.payload.tunnel_id
        window.LiveElement.Scale.Core.buildSnippet(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="tunnel"] fieldset[name="test"] div.snippet'))
        window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_socket, 'IdeTunnelTest', 'message', false, true)
        return {'#value': input.payload.tunnel_id}
    } else if (handlerType == 'listener') {
        return JSON.parse(input.event.data)
    }
}
window.LiveElement.Live.processors.IdeTunnelTest = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        var event = input.vector.split(':').shift()
        if (event == 'change') {
            window.fetch(`${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/tunnel/${window.LiveElement.Scale.Console.IDE.Tunnel.Create.tunnel_id}`, {
                method: 'PUT', 
                body: JSON.stringify(input.properties.value)
            }).then(() => {
                input.triggersource.value = ''
            })
        }
    } else if (handlerType == 'subscription') {
        return {'#value': `${input.payload.message}\n${input.subscriber.value}`}
    } else if (handlerType == 'listener') {
        var message = input.event.data
        try {
            message = JSON.parse(message)
        } catch(e) {
            message = message
        }
        return {message: message}
    }
}

window.LiveElement.Live.listeners.IdeTunnelCreate = {processor: 'IdeTunnelCreate', expired: true}
window.LiveElement.Live.listeners.IdeTunnelTest = {processor: 'IdeTunnelTest', expired: true}

window.LiveElement.Scale.Core.buildSnippet(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="tunnel"] fieldset[name="create"] div.snippet'))
window.LiveElement.Scale.Core.buildSnippet(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="tunnel"] fieldset[name="test"] div.snippet'))



