window.LiveElement.Live.processors.IdeChannelEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="edit"]')
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="code"]')
    var testFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="test"]')
    if (handlerType == 'listener') {
        return {
            '@id': (window.LiveElement.Scale.Console.IDE.Channel.channelElement || {})['@id'], 
            adminKey: (window.LiveElement.Scale.Console.IDE.Channel.channelElement || {}).adminKey, 
            receiveKey: (window.LiveElement.Scale.Console.IDE.Channel.channelElement || {}).receiveKey, 
            sendKey: (window.LiveElement.Scale.Console.IDE.Channel.channelElement || {}).sendKey
        }
    } else if (handlerType == 'trigger') {
        var cleanUp = function() {
            if (window.LiveElement.Scale.Console.IDE.Channel.channelElement) {
                window.LiveElement.Scale.Console.IDE.Channel.channelElement.remove()
                delete window.LiveElement.Scale.Console.IDE.Channel.channelElement
            }
            if (window.LiveElement.Scale.Console.IDE.Channel.Test.socket) {
                if (window.LiveElement.Scale.Console.IDE.Channel.Test.socket.readyState && window.LiveElement.Scale.Console.IDE.Channel.Test.socket.readyState < 2) {
                    window.LiveElement.Scale.Console.IDE.Channel.Test.socket.close(1001)
                }
                delete window.LiveElement.Scale.Console.IDE.Channel.Test.socket
            }
            testFieldset.querySelector('textarea').value = ''
        }
        if (input.entity) {
            cleanUp()
            editFieldset.setAttribute('active', true)
            codeFieldset.setAttribute('active', true)
            testFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.Channel.channelElement = editFieldset.querySelector('element-channel')
            if (window.LiveElement.Scale.Console.IDE.Channel.channelElement) {
                window.LiveElement.Scale.Console.IDE.Channel.channelElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Channel.channelElement = document.createElement('element-channel')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Channel.channelElement)
            window.LiveElement.Scale.Console.IDE.Channel.channelElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Channel.channelElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Channel.channelElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'channel')
            })
            window.LiveElement.Scale.Console.IDE.Channel.channelElement.setAttribute('live-subscription', 'IdeChannelEdit:IdeChannelCode')
            window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Channel.channelElement, 'IdeChannelEdit', 'change', false, true)
        } else {
            cleanUp()
            editFieldset.removeAttribute('active')
            codeFieldset.removeAttribute('active')
            testFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Live.processors.IdeChannelCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="code"]')
    if (handlerType == 'subscription') {
        (['adminKey', 'receiveKey', 'sendKey']).forEach(key => {
            var adminUrlInputElement = codeFieldset.querySelector('input[name="adminUrl"]')
            if (adminUrlInputElement && input.payload.adminKey) {
                adminUrlInputElement.value = (input.payload.adminKey) ? `${window.LiveElement.Scale.Console.IDE.systemURL}/channel/${input.payload['@id']}/${input.payload.adminKey}` : ''
            }
            var receiveUrlInputElement = codeFieldset.querySelector('input[name="receiveUrl"]')
            if (receiveUrlInputElement && input.payload.receiveKey) {
                receiveUrlInputElement.value = (input.payload.receiveKey) ? `${window.LiveElement.Scale.Console.IDE.systemURL.replace('https:', 'wss:')}/channel/${input.payload['@id']}/${input.payload.receiveKey}` : ''
            }
            var sendUrlInputElement = codeFieldset.querySelector('input[name="sendUrl"]')
            if (sendUrlInputElement && input.payload.sendKey) {
                sendUrlInputElement.value = (input.payload.sendKey) ? `${window.LiveElement.Scale.Console.IDE.systemURL}/channel/${input.payload['@id']}/${input.payload.sendKey}` : ''
            }
        })
    }
}

window.LiveElement.Live.processors.IdeChannelTest = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        var event = input.vector.split(':').shift()
        if (event == 'change') {
            if (window.LiveElement.Scale.Console.IDE.Channel.channelElement 
                && window.LiveElement.Scale.Console.IDE.Channel.channelElement['@id']
                && window.LiveElement.Scale.Console.IDE.Channel.channelElement.receiveKey
                && window.LiveElement.Scale.Console.IDE.Channel.channelElement.sendKey) {
                var receiveUrl = `${window.LiveElement.Scale.Console.IDE.systemURL.replace('https:', 'wss:')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.channelElement['@id']}/${window.LiveElement.Scale.Console.IDE.Channel.channelElement.receiveKey}`
                if (!window.LiveElement.Scale.Console.IDE.Channel.Test.socket 
                    || (window.LiveElement.Scale.Console.IDE.Channel.Test.socket && (window.LiveElement.Scale.Console.IDE.Channel.Test.socket.url != receiveUrl))) {
                    try {
                        window.LiveElement.Scale.Console.IDE.Channel.Test.socket = new WebSocket(receiveUrl)
                        window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Channel.Test.socket, 'IdeChannelTest', 'message', false, true)
                    } catch(e) {
                        delete window.LiveElement.Scale.Console.IDE.Channel.Test.socket
                    }
                }
                var sendUrl = `${window.LiveElement.Scale.Console.IDE.systemURL}/channel/${window.LiveElement.Scale.Console.IDE.Channel.channelElement['@id']}/${window.LiveElement.Scale.Console.IDE.Channel.channelElement.sendKey}`
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

window.LiveElement.Scale.Console.buildSnippets('ide', 'channel')

window.LiveElement.Live.listeners.IdeChannelEdit = {processor: 'IdeChannelEdit', expired: true}
window.LiveElement.Live.listeners.IdeChannelTest = {processor: 'IdeChannelTest', expired: true}
