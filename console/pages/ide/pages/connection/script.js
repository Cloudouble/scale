window.LiveElement.Live.processors.IdeConnectionEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="edit"]')
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="code"]')
    var testFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="test"]')
    if (handlerType == 'listener') {
        return {
            '@id': (window.LiveElement.Scale.Console.IDE.Connection.connectionElement || {})['@id'], 
            adminKey: (window.LiveElement.Scale.Console.IDE.Connection.connectionElement || {}).adminKey, 
            receiveKey: (window.LiveElement.Scale.Console.IDE.Connection.connectionElement || {}).receiveKey, 
            sendKey: (window.LiveElement.Scale.Console.IDE.Connection.connectionElement || {}).sendKey
        }
    } else if (handlerType == 'trigger') {
        var cleanUp = function() {
            if (window.LiveElement.Scale.Console.IDE.Connection.connectionElement) {
                window.LiveElement.Scale.Console.IDE.Connection.connectionElement.remove()
                delete window.LiveElement.Scale.Console.IDE.Connection.connectionElement
            }
            if (window.LiveElement.Scale.Console.IDE.Connection.Test.socket) {
                if (window.LiveElement.Scale.Console.IDE.Connection.Test.socket.readyState && window.LiveElement.Scale.Console.IDE.Connection.Test.socket.readyState < 2) {
                    window.LiveElement.Scale.Console.IDE.Connection.Test.socket.close()
                }
                delete window.LiveElement.Scale.Console.IDE.Connection.Test.socket
            }
            testFieldset.querySelector('textarea').value = ''
        }
        if (input.entity) {
            cleanUp()
            editFieldset.setAttribute('active', true)
            codeFieldset.setAttribute('active', true)
            testFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement = editFieldset.querySelector('element-connection')
            if (window.LiveElement.Scale.Console.IDE.Connection.connectionElement) {
                window.LiveElement.Scale.Console.IDE.Connection.connectionElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement = document.createElement('element-connection')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Connection.connectionElement)
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Connection.connectionElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'connection')
            })
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement.setAttribute('live-subscription', 'IdeConnectionEdit:IdeConnectionCode')
            window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Connection.connectionElement, 'IdeConnectionEdit', 'change', false, true)
        } else {
            cleanUp()
            editFieldset.removeAttribute('active')
            codeFieldset.removeAttribute('active')
            testFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Live.processors.IdeConnectionCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="code"]')
    if (handlerType == 'subscription') {
        (['adminKey', 'receiveKey', 'sendKey']).forEach(key => {
            var adminUrlInputElement = codeFieldset.querySelector('input[name="adminUrl"]')
            if (adminUrlInputElement && input.payload.adminKey) {
                adminUrlInputElement.value = (input.payload.adminKey) ? `${window.LiveElement.Scale.Console.IDE.systemURL}/connection/${input.payload['@id']}/${input.payload.adminKey}` : ''
            }
            var receiveUrlInputElement = codeFieldset.querySelector('input[name="receiveUrl"]')
            if (receiveUrlInputElement && input.payload.receiveKey) {
                receiveUrlInputElement.value = (input.payload.receiveKey) ? `${window.LiveElement.Scale.Console.IDE.systemURL.replace('https:', 'wss:')}/connection/${input.payload['@id']}/${input.payload.receiveKey}` : ''
            }
            var sendUrlInputElement = codeFieldset.querySelector('input[name="sendUrl"]')
            if (sendUrlInputElement && input.payload.sendKey) {
                sendUrlInputElement.value = (input.payload.sendKey) ? `${window.LiveElement.Scale.Console.IDE.systemURL}/connection/${input.payload['@id']}/${input.payload.sendKey}` : ''
            }
        })
    }
}

window.LiveElement.Live.processors.IdeConnectionTest = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        var event = input.vector.split(':').shift()
        if (event == 'change') {
            if (window.LiveElement.Scale.Console.IDE.Connection.connectionElement 
                && window.LiveElement.Scale.Console.IDE.Connection.connectionElement['@id']
                && window.LiveElement.Scale.Console.IDE.Connection.connectionElement.receiveKey
                && window.LiveElement.Scale.Console.IDE.Connection.connectionElement.sendKey) {
                var receiveUrl = `${window.LiveElement.Scale.Console.IDE.systemURL.replace('https:', 'wss:')}/connection/${window.LiveElement.Scale.Console.IDE.Connection.connectionElement['@id']}/${window.LiveElement.Scale.Console.IDE.Connection.connectionElement.receiveKey}`
                if (!window.LiveElement.Scale.Console.IDE.Connection.Test.socket 
                    || (window.LiveElement.Scale.Console.IDE.Connection.Test.socket && (window.LiveElement.Scale.Console.IDE.Connection.Test.socket.url != receiveUrl))) {
                    try {
                        window.LiveElement.Scale.Console.IDE.Connection.Test.socket = new WebSocket(receiveUrl)
                        window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Connection.Test.socket, 'IdeConnectionTest', 'message', false, true)
                    } catch(e) {
                        delete window.LiveElement.Scale.Console.IDE.Connection.Test.socket
                    }
                }
                var sendUrl = `${window.LiveElement.Scale.Console.IDE.systemURL}/connection/${window.LiveElement.Scale.Console.IDE.Connection.connectionElement['@id']}/${window.LiveElement.Scale.Console.IDE.Connection.connectionElement.sendKey}`
                window.fetch(
                    sendUrl, 
                    {
                        method: 'POST', 
                        body: JSON.stringify(input.properties.value)
                    }
                ).then(() => {
                    window.setTimeout(function() {
                        input.triggersource.value = ''
                    }, 250)
                })
            }
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

window.LiveElement.Scale.Console.buildSnippets('ide', 'connection')

window.LiveElement.Live.listeners.IdeConnectionEdit = {processor: 'IdeConnectionEdit', expired: true}
window.LiveElement.Live.listeners.IdeConnectionTest = {processor: 'IdeConnectionTest', expired: true}
