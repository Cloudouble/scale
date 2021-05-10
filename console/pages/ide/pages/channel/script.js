window.LiveElement.Live.processors.IdeChannelSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return {...window.LiveElement.Scale.Console.IDE.Channel.Configure.channel, ...{id : window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}}
    } else if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        if (input.attributes.name == 'search') {
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
        } else if (input.attributes.name == 'load' || input.attributes.name == 'new') {
            var searchFieldset = input.triggersource.closest('fieldset')
            if (input.attributes.name == 'new') {
                window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id = window.LiveElement.Scale.Core.generateUUID4()
                window.LiveElement.Scale.Console.IDE.Channel.Configure.channel = {
                    receiveKey: window.LiveElement.Scale.Core.generateUUID4(), 
                    sendKey: window.LiveElement.Scale.Core.generateUUID4(), 
                    adminKey: window.LiveElement.Scale.Core.generateUUID4()
                }
            } else {
                var searchElement = searchFieldset.querySelector('input[name="search"]')
                if (window.LiveElement.Scale.Console.IDE.Channel.Search && window.LiveElement.Scale.Console.IDE.Channel.Search[searchElement.value]) {
                    window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id = searchElement.value
                    window.LiveElement.Scale.Console.IDE.Channel.Configure.channel = window.LiveElement.Scale.Console.IDE.Channel.Search[searchElement.value]
                }
            }
            searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
        }
    }
}
window.LiveElement.Live.processors.IdeChannelConfigure = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return {...window.LiveElement.Scale.Console.IDE.Channel.Configure.channel, ...{id : window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}}
    } else if (handlerType == 'subscription') {
        input.subscriber.querySelectorAll('input[name]').forEach(i => {
            if (i.name in input.payload) {
                i.value = input.payload[i.name] || ''
            }
        })
        window.LiveElement.Scale.Core.buildSnippet(input.subscriber.querySelector('div.snippet'))
        input.subscriber.setAttribute('mode', window.LiveElement.Scale.Console.IDE.Channel.Search && window.LiveElement.Scale.Console.IDE.Channel.Search[input.payload.id] ? 'load' : 'new')
        if (input.subscriber.getAttribute('mode') == 'new') {
            input.subscriber.querySelector('input[name="@name"]').value = ''
        }
    } else if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        if (input.attributes.name == '@name') {
            window.LiveElement.Scale.Console.IDE.Channel.Configure.channel['@name'] = input.triggersource.value
            window.LiveElement.Scale.Core.buildSnippet(input.triggersource.closest('fieldset').querySelector('div.snippet'))
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
        } else if (input.attributes.name == 'delete') {
            window.fetch(
                `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.adminKey}`, 
                {
                    method: 'DELETE', 
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
        input.subscriber.querySelectorAll('input[name]').forEach(i => {
            if (i.name in window.LiveElement.Scale.Console.IDE.Channel.Code) {
                i.value = window.LiveElement.Scale.Console.IDE.Channel.Code[i.name] || ''
            }
            window.LiveElement.Scale.Core.buildSnippet(i.nextElementSibling.querySelector('div.snippet'))
        })
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

window.LiveElement.Live.listeners.IdeChannelSearch = {processor: 'IdeChannelSearch', expired: true}
window.LiveElement.Live.listeners.IdeChannelTest = {processor: 'IdeChannelTest', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="search"]'), 'IdeChannelSearch', 'loaded', false, true)
