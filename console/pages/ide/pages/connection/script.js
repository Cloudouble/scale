window.LiveElement.Live.processors.IdeConnectionSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var searchFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="search"]')
    var configureFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="configure"]')
    var datalistElement = searchFieldset.querySelector('datalist')
    var searchInput = searchFieldset.querySelector('input[name="search"]')
    var loadButton = searchFieldset.querySelector('button[name="load"]')
    var blankOptions = {[window.LiveElement.Scale.Console.IDE.newFlag]: 'Generate UUID for a new connection...'}
    if (handlerType == 'listener') {
        return {...window.LiveElement.Scale.Console.IDE.Connection.connection}
    } else if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        if (input.attributes.name == 'search') {
            
            if (input.properties.value == window.LiveElement.Scale.Console.IDE.newFlag) {
                input.triggersource.value = window.LiveElement.Scale.Core.generateUUID4()
                window.LiveElement.Scale.Console.IDE.Connection.Search.result = {}
                window.LiveElement.Scale.Core.buildDataList(datalistElement, window.LiveElement.Scale.Console.IDE.Connection.Search.result)
            } else if (!input.properties.value) {
                loadButton.setAttribute('disabled', true)
                window.LiveElement.Scale.Core.buildDataList(datalistElement, {}, blankOptions)
            } else {
                window.LiveElement.Scale.Console.System.invokeLambda({
                    page: 'ide', 
                    entity_type: 'connection', 
                    heading: 'search',
                    search: input.properties.value
                }).then(searchResult => {
                    if (searchResult && typeof searchResult == 'object' && searchResult.result && typeof searchResult.result == 'object') {
                        window.LiveElement.Scale.Console.IDE.Connection.Search.result = searchResult.result
                        window.LiveElement.Scale.Core.buildDataList(datalistElement, window.LiveElement.Scale.Console.IDE.Connection.Search.result, blankOptions)
                    }
                })
            }
        } else if (input.attributes.name == 'load') {
            configureFieldset.setAttribute('active', true)
            if (record && typeof record == 'object' && '@type' in record && '@id' in record) {
                window.LiveElement.Scale.Console.IDE.Record.record = record
                if (window.LiveElement.Scale.Console.IDE.Record.record) {
                    window.LiveElement.Scale.Console.IDE.writeHistory('record', 
                        window.LiveElement.Scale.Console.IDE.Record.record_type, window.LiveElement.Scale.Console.IDE.Record.record_uuid, 
                        window.LiveElement.Scale.Console.IDE.Record.record, 'click:IdeRecordSearch', searchFieldset)
                    searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
                }
            } else {
                window.LiveElement.Scale.Console.IDE.Record.record = {
                    '@type': window.LiveElement.Scale.Console.IDE.Record.record_type, 
                    '@id': window.LiveElement.Scale.Console.IDE.Record.record_uuid
                }
                window.LiveElement.Scale.Console.IDE.writeHistory('record', 
                    window.LiveElement.Scale.Console.IDE.Record.record_type, window.LiveElement.Scale.Console.IDE.Record.record_uuid, 
                    window.LiveElement.Scale.Console.IDE.Record.record, 'click:IdeRecordSearch', searchFieldset)
                searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
            }
            window.LiveElement.Scale.Console.IDE.Record.buildSnippet()

            
            
            if (input.attributes.name == 'new') {
                window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id = window.LiveElement.Scale.Core.generateUUID4()
                window.LiveElement.Scale.Console.IDE.Connection.Configure.connection = {
                    receiveKey: window.LiveElement.Scale.Core.generateUUID4(), 
                    sendKey: window.LiveElement.Scale.Core.generateUUID4(), 
                    adminKey: window.LiveElement.Scale.Core.generateUUID4()
                }
            } else {
                var searchElement = searchFieldset.querySelector('input[name="search"]')
                if (window.LiveElement.Scale.Console.IDE.Connection.Search && window.LiveElement.Scale.Console.IDE.Connection.Search[searchElement.value]) {
                    window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id = searchElement.value
                    window.LiveElement.Scale.Console.IDE.Connection.Configure.connection = window.LiveElement.Scale.Console.IDE.Connection.Search[searchElement.value]
                }
            }
            searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
        }
    }
}
window.LiveElement.Live.processors.IdeConnectionConfigure = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return {...window.LiveElement.Scale.Console.IDE.Connection.Configure.connection, ...{id : window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id}}
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
        window.LiveElement.Scale.Core.buildSnippet(input.subscriber.querySelector('div.snippet'))
        if (complete) {
            input.subscriber.setAttribute('mode', window.LiveElement.Scale.Console.IDE.Connection.Search && window.LiveElement.Scale.Console.IDE.Connection.Search[input.payload.id] ? 'load' : 'new')
        } else {
            input.subscriber.removeAttribute('mode')
        }
        if (input.subscriber.getAttribute('mode') == 'new') {
            input.subscriber.querySelector('input[name="@name"]').value = ''
        }
    } else if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        if (input.attributes.name == '@name') {
            window.LiveElement.Scale.Console.IDE.Connection.Configure.connection['@name'] = input.triggersource.value
            window.LiveElement.Scale.Core.buildSnippet(input.triggersource.closest('fieldset').querySelector('div.snippet'))
        } else if (input.attributes.name == 'create') {
            window.fetch(
                `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/connection/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id}/connect.json`, 
                {
                    method: 'PUT', 
                    headers: {
                        "Content-Type": "application/json"
                    }, 
                    body: JSON.stringify(window.LiveElement.Scale.Console.IDE.Connection.Configure.connection) 
                }
            )
        } else if (input.attributes.name == 'delete') {
            window.fetch(
                `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id}/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection.adminKey}`, 
                {
                    method: 'DELETE', 
                }
            ).then(() => {
                delete window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id
                window.LiveElement.Scale.Console.IDE.Connection.Configure.connection = {}
                var searchFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="search"]')
                input.triggersource.closest('fieldset').removeAttribute('mode')                
                var searchInput = searchFieldset.querySelector('input')
                searchInput.value = ''
                searchInput.focus()
                searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
            })
        }
    }
}
window.LiveElement.Live.processors.IdeConnectionCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return window.LiveElement.Scale.Console.IDE.Connection.Configure
    } else if (handlerType == 'subscription') {
        window.LiveElement.Scale.Console.IDE.Connection.Code = {
            receive_url: window.LiveElement.Scale.Console.IDE.Connection.Configure.connection.receiveKey ? `${window.localStorage.getItem('system:system_access_url').replace('https:', 'wss:')}${window.localStorage.getItem('system:system_root')}/connection/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id}/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection.receiveKey}` : undefined, 
            send_url: window.LiveElement.Scale.Console.IDE.Connection.Configure.connection.sendKey ? `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id}/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection.sendKey}` : undefined, 
            admin_url: window.LiveElement.Scale.Console.IDE.Connection.Configure.connection.adminKey ? `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection_id}/${window.LiveElement.Scale.Console.IDE.Connection.Configure.connection.adminKey}` : undefined
        }
        input.subscriber.querySelectorAll('input[name]').forEach(i => {
            var snippetElement = i.nextElementSibling.querySelector('div.snippet')
            if (window.LiveElement.Scale.Console.IDE.Connection.Code[i.name]) {
                i.value = window.LiveElement.Scale.Console.IDE.Connection.Code[i.name]
                window.LiveElement.Scale.Core.buildSnippet(snippetElement)
            } else {
                i.value = ''
                i.nextElementSibling.removeAttribute('built')
            }
        })
    }
}
window.LiveElement.Live.processors.IdeConnectionTest = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        var event = input.vector.split(':').shift()
        if (event == 'change') {
            if (!window.LiveElement.Scale.Console.IDE.Connection.Test.socket 
                || (window.LiveElement.Scale.Console.IDE.Connection.Test.socket && (window.LiveElement.Scale.Console.IDE.Connection.Test.socket.url != window.LiveElement.Scale.Console.IDE.Connection.Code.receive_url))) {
                try {
                    window.LiveElement.Scale.Console.IDE.Connection.Test.socket = new WebSocket(window.LiveElement.Scale.Console.IDE.Connection.Code.receive_url)
                    window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Connection.Test.socket, 'IdeConnectionTest', 'message', false, true)
                } catch(e) {
                    delete window.LiveElement.Scale.Console.IDE.Connection.Test.socket
                }
            }
            window.fetch(
                window.LiveElement.Scale.Console.IDE.Connection.Code.send_url, 
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

window.LiveElement.Live.listeners.IdeConnectionSearch = {processor: 'IdeConnectionSearch', expired: true}
window.LiveElement.Live.listeners.IdeConnectionTest = {processor: 'IdeConnectionTest', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="search"]'), 'IdeConnectionSearch', 'loaded', false, true)
