window.LiveElement.Live.processors.IdeChannelSearch = function(input) {
    if (input.attributes.name == 'search') {
        var event = input.vector.split(':').shift()
        if (event == 'keyup') {
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'channel', 
                heading: 'search',
                search: input.properties.value
            }).then(searchResult => {
                if (searchResult && typeof searchResult == 'object' && searchResult.result && typeof searchResult.result == 'object') {
                    window.LiveElement.Scale.Console.IDE.Channel.Search = searchResult.result
                    var datalist = document.getElementById('ide-channel-search-list')
                    datalist.innerHTML = ''
                    Object.keys(window.LiveElement.Scale.Console.IDE.Channel.Search).sort().forEach(channel_id => {
                        var optionElement = document.createElement('option')
                        optionElement.setAttribute('value', channel_id)
                        if (window.LiveElement.Scale.Console.IDE.Channel.Search[channel_id]['@name']) {
                            optionElement.innerHTML = `${channel_id} (@${window.LiveElement.Scale.Console.IDE.Channel.Search[channel_id]['@name']})`
                        } else {
                            optionElement.innerHTML = `${channel_id}`
                        }
                        datalist.appendChild(optionElement)
                    })
                }
            })
        }
    }
}
window.LiveElement.Live.processors.IdeChannelConfigure = function(input) {
    var setupConfigure = function(configureElement) {
        var elements = {}
        ;(['@name', 'id', 'receiveKey', 'sendKey', 'adminKey']).forEach(n => {
            elements[n] = configureElement.querySelector(`input[name="${n}"]`)
            if (n == 'id') {
                elements[n].value = window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id || ''
            } else {
                elements[n].value = window.LiveElement.Scale.Console.IDE.Channel.Configure.channel[n] || ''
            }
        })
        window.LiveElement.Scale.Core.buildSnippet(configureElement.querySelector('div.snippet'))
        configureElement.dispatchEvent(new window.CustomEvent('setup'))
    }
    if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        var configureElement = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="configure"]')
        if (input.attributes.name == 'new') {
            configureElement.setAttribute('mode', 'new')
            window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id = window.LiveElement.Scale.Core.generateUUID4()
            window.LiveElement.Scale.Console.IDE.Channel.Configure.channel = {
                receiveKey: window.LiveElement.Scale.Core.generateUUID4(), 
                sendKey: window.LiveElement.Scale.Core.generateUUID4(), 
                adminKey: window.LiveElement.Scale.Core.generateUUID4()
            }
            setupConfigure(configureElement)
            configureElement.querySelector('input[name="@name"]').focus()
        } else if ((['@name', 'id', 'receiveKey', 'sendKey', 'adminKey']).includes(input.attributes.name)) {
            window.LiveElement.Scale.Console.IDE.Channel.Configure.channel = window.LiveElement.Scale.Console.IDE.Channel.Configure.channel || {}
            if (input.attributes.name == 'id') {
                window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id = input.properties.value
            } else {
                window.LiveElement.Scale.Console.IDE.Channel.Configure.channel[input.attributes.name] = input.properties.value
            }
            setupConfigure(configureElement)
        } else if (input.attributes.name == 'load') {
            configureElement.setAttribute('mode', 'load')
            var searchElement = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="search"] input[name="search"]')
            if (searchElement) {
                if (window.LiveElement.Scale.Console.IDE.Channel.Search && window.LiveElement.Scale.Console.IDE.Channel.Search[searchElement.value]) {
                    window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id = searchElement.value
                    window.LiveElement.Scale.Console.IDE.Channel.Configure.channel = window.LiveElement.Scale.Console.IDE.Channel.Search[searchElement.value]
                    setupConfigure(configureElement)
                }
            }
        } else if (input.attributes.name == 'create') {
            window.fetch(
                `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/connect.json`, 
                {
                    method: 'PUT', 
                    headers: {
                        "Content-Type": "application/json"
                    }, 
                    body: JSON.stringify(window.LiveElement.Scale.Console.IDE.Channel.Configure.channel) 
                }
            )
        }
    }
}
window.LiveElement.Live.processors.IdeChannelCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return window.LiveElement.Scale.Console.IDE.Channel.Configure
    } else if (handlerType == 'subscription') {
        window.LiveElement.Scale.Console.IDE.Channel.Code = {
            receive_url: `${window.localStorage.getItem('system:system_access_url').replace('https:', 'wss:')}${window.localStorage.getItem('system:system_root')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.receiveKey}`, 
            send_url: `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.sendKey}`, 
            admin_url: `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.adminKey}`
        }
        window.LiveElement.Scale.Core.buildSnippet(input.subscriber.parentElement.querySelector('div.snippet'))
        if (input.subscriber.name == 'receive_url') {
            return {'#value': window.LiveElement.Scale.Console.IDE.Channel.Code.receive_url}
        } else if (input.subscriber.name == 'send_url') {
            return {'#value': window.LiveElement.Scale.Console.IDE.Channel.Code.send_url}
        } else if (input.subscriber.name == 'admin_url') {
            return {'#value': window.LiveElement.Scale.Console.IDE.Channel.Code.admin_url}
        }
    }
}
window.LiveElement.Live.processors.IdeChannelTest = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        var event = input.vector.split(':').shift()
        if (event == 'change') {
            if (!window.LiveElement.Scale.Console.IDE.Channel.Test.socket 
                || (window.LiveElement.Scale.Console.IDE.Channel.Test.socket && (window.LiveElement.Scale.Console.IDE.Channel.Test.socket.url != window.LiveElement.Scale.Console.IDE.Channel.Code.receive_url))) {
                try {
                    window.LiveElement.Scale.Console.IDE.Channel.Test.socket = new WebSocket(window.LiveElement.Scale.Console.IDE.Channel.Code.receive_url)
                    window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Channel.Test.socket, 'IdeChannelTest', 'message', false, true)
                } catch(e) {
                    delete window.LiveElement.Scale.Console.IDE.Channel.Test.socket
                }
            }
            window.fetch(
                window.LiveElement.Scale.Console.IDE.Channel.Code.send_url, 
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

window.LiveElement.Live.listeners.IdeChannelConfigure = {processor: 'IdeChannelConfigure', expired: true}
window.LiveElement.Live.listeners.IdeChannelCode = {processor: 'IdeChannelCode', expired: true}
window.LiveElement.Live.listeners.IdeChannelTest = {processor: 'IdeChannelTest', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="configure"]'), 'IdeChannelCode', 'setup', false, true)
