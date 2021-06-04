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
        if (input.entity) {
            editFieldset.setAttribute('active', true)
            codeFieldset.setAttribute('active', true)
            //testFieldset.setAttribute('active', true)
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
            window.LiveElement.Scale.Console.buildSnippets('ide', 'channel')            
        } else {
            editFieldset.removeAttribute('active')
            codeFieldset.removeAttribute('active')
            //testFieldset.removeAttribute('active')
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

window.LiveElement.Scale.Console.buildSnippets('ide', 'channel')

window.LiveElement.Live.listeners.IdeChannelEdit = {processor: 'IdeChannelEdit', expired: true}
//window.LiveElement.Live.listeners.IdeChannelTest = {processor: 'IdeChannelTest', expired: true}





/*window.LiveElement.Live.processors.IdeChannelSearch = function(input) {
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
}*/


/*window.LiveElement.Live.processors.IdeChannelConfigure = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return {...window.LiveElement.Scale.Console.IDE.Channel.Configure.channel, ...{id : window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}}
    } else if (handlerType == 'subscription') {
        var complete = true
        input.subscriber.querySelectorAll('input[name]').forEach(i => {
            if (i.name in input.payload) {
                i.value = input.payload[i.name] || ''
            } else {
                i.value = ''
                if (i.name != '@name') {
                    complete = false
                }
            }
        })
        window.LiveElement.Scale.Console.buildSnippets('ide', 'channel')
        if (complete) {
            input.subscriber.setAttribute('mode', window.LiveElement.Scale.Console.IDE.Channel.Search && window.LiveElement.Scale.Console.IDE.Channel.Search[input.payload.id] ? 'load' : 'new')
        } else {
            input.subscriber.removeAttribute('mode')
        }
        if (input.subscriber.getAttribute('mode') == 'new') {
            input.subscriber.querySelector('input[name="@name"]').value = ''
        }
    } else if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        if (input.attributes.name == '@name') {
            window.LiveElement.Scale.Console.IDE.Channel.Configure.channel['@name'] = input.triggersource.value
            window.LiveElement.Scale.Console.buildSnippets('ide', 'channel')
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
            ).then(() => {
                delete window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id
                window.LiveElement.Scale.Console.IDE.Channel.Configure.channel = {}
                var searchFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="channel"] fieldset[name="search"]')
                input.triggersource.closest('fieldset').removeAttribute('mode')                
                var searchInput = searchFieldset.querySelector('input')
                searchInput.value = ''
                searchInput.focus()
                searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
            })
        }
    }
}
window.LiveElement.Live.processors.IdeChannelCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return window.LiveElement.Scale.Console.IDE.Channel.Configure
    } else if (handlerType == 'subscription') {
        window.LiveElement.Scale.Console.IDE.Channel.Code = {
            receive_url: window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.receiveKey ? `${window.localStorage.getItem('system:system_access_url').replace('https:', 'wss:')}${window.localStorage.getItem('system:system_root')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.receiveKey}` : undefined, 
            send_url: window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.sendKey ? `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.sendKey}` : undefined, 
            admin_url: window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.adminKey ? `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.adminKey}` : undefined
        }
        input.subscriber.querySelectorAll('input[name]').forEach(i => {
            if (window.LiveElement.Scale.Console.IDE.Channel.Code[i.name]) {
                i.value = window.LiveElement.Scale.Console.IDE.Channel.Code[i.name]
                window.LiveElement.Scale.Console.buildSnippets('ide', 'channel')
            } else {
                i.value = ''
                i.nextElementSibling.removeAttribute('built')
            }
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
*/