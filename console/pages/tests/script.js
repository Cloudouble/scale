window.LiveElement.Scale.Console.Tests = window.LiveElement.Scale.Console.Tests || {}

window.LiveElement.Scale.Console.Tests.runTest = function(tr, test) {
    var testName = tr.getAttribute('name')
    var previousResult = window.localStorage.getItem(`tests:${testName}:result`)
    window.localStorage.removeItem(`tests:${testName}:result`)
    var resultLabel = tr.querySelector(':scope > td > label')
    resultLabel.setAttribute('status', 'pending')
    tr.querySelector('code.result').innerHTML = '...'
    tr.querySelector('code.confirmation').innerHTML = '...'
    tr.querySelector('code.confirmation').closest('label').setAttribute('status', 'pending')            
    var start = window.performance.now()
    tr.querySelectorAll('time').forEach(t => t.innerHTML = '...')
    var system_access_url = window.localStorage.getItem('system:system_access_url')
    var system_root = window.localStorage.getItem('system:system_root')
    var connection_id = window.localStorage.getItem(`tests:create-sudo-connection:result`)
    var connection_url = `${system_access_url}${system_root}/connection/${connection_id}`
    return Promise.resolve(test(connection_url, system_access_url, system_root, connection_id)).then(result => {
        tr.querySelector('time[name="request"]').innerHTML = `${Math.round(window.performance.now() - start)}`
        resultLabel.setAttribute('status', 'success')
        var testContext = Object.assign(
            {}, 
            ...Object.keys(window.LiveElement.Scale.Console.Tests.testMap).map(k => ({[k]: window.localStorage.getItem(`tests:${k}:result`)})), 
            {[testName]: previousResult}
        )
        window.localStorage.setItem(`tests:${testName}:result`, result)
        window.LiveElement.Scale.Console.System.invokeLambda({
            page: 'tests', 
            test: testName, 
            context: testContext, 
            result: result, 
        }).then(processResult => {
            if (!(processResult && typeof processResult == 'object' && processResult.confirmation === false)) {
                tr.querySelector('time[name="process"]').innerHTML = processResult && typeof processResult == 'object' && typeof processResult.timing == 'number' ? processResult.timing : ' ---error--- '
                tr.querySelector('code.confirmation').innerHTML = processResult && typeof processResult == 'object' && processResult.confirmation && typeof processResult.confirmation == 'object' ? JSON.stringify(processResult.confirmation, null, 4) : ' ---error--- '
                tr.querySelector('code.confirmation').closest('label').setAttribute('status', 'success')
                window.localStorage.setItem(`tests:${testName}:confirmation`, JSON.stringify(processResult.confirmation))
            }
        })
        return result
    }).catch(e => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        resultLabel.setAttribute('status', 'error')
        tr.querySelector('time[name="process"]').innerHTML = ' ---error--- '
        tr.querySelector('code.confirmation').innerHTML = ' ---error--- '
        tr.querySelector('code.confirmation').closest('label').setAttribute('status', 'error')
    })
}

window.setTimeout(() => {
    var installation = document.getElementById('tests').querySelector('table[name="installation"]')
    Object.entries(window.LiveElement.Scale.Console.Tests.testMap).forEach(entry => {
        var resultStorageKey = `tests:${entry[0]}:result`
        var tr = installation.querySelector(`tr[name="${entry[0]}"]`)
        tr.querySelector('i').innerHTML = entry[0]
        if (window.localStorage.getItem(resultStorageKey)) {
            tr.querySelector('label').setAttribute('status', 'success')
            tr.querySelector('code.result').innerHTML = window.localStorage.getItem(resultStorageKey)
        }
        var source = tr.nextElementSibling.querySelector('code.source')
        if (source) {
            source.innerHTML = entry[1].toString()
        }
        tr.querySelector('button').addEventListener('click', event => {
            window.LiveElement.Scale.Console.Tests.runTest(tr, entry[1]).then(result => {
                tr.querySelector('code.result').innerHTML = result
            }).catch(e => {
                tr.querySelector('code.result').innerHTML = e
            })
        })
    })
}, 1)

window.LiveElement.Scale.Console.Tests.testMap = {
    'create-sudo-connection': function(connection_url, system_access_url, system_root, connection_id) {
        connection_id = window.LiveElement.Scale.Core.generateUUID4()
        var sudo_key = window.localStorage.getItem('system:sudo_key')
        return window.fetch(
            `${system_access_url}${system_root}/connection/${connection_id}/connect.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify({
                    sudo: {key: sudo_key}
                }) 
            }
        ).then(r => {
            return connection_id
        })
    }, 
    'create-websocket': function(connection_url, system_access_url, system_root, connection_id) {
        delete window.LiveElement.Scale.Console.Tests.websocket
        if (system_access_url && system_root && connection_id) {
            var websocketUri = `${connection_url.replace('https:', 'wss:')}/websocket`
            try {
                window.LiveElement.Scale.Console.Tests.websocket = new WebSocket(websocketUri)
                return websocketUri
            } catch (e) {
                return e
            }
        }
    }, 
    'create-record-put': function(connection_url, system_access_url, system_root, connection_id) {
        var record_id = window.LiveElement.Scale.Core.generateUUID4()
        var bookNumber = Math.floor(Math.random()* 1000)
        var record = {'@type': 'Book', '@id': record_id, name: `Test Book ${bookNumber}`, numberOfPages: 10}
        return window.fetch(
            `${connection_url}/record/Book/${record_id}.json`, 
            {
                method: 'PUT', 
                headers: {"Content-Type": "application/json"}, 
                body: JSON.stringify(record)
            }
        ).then(r => {
            return record_id
        })
    }, 
    'delete-record': function(connection_url, system_access_url, system_root, connection_id) {
        var record_id = window.localStorage.getItem('tests:create-record-put:result')
        if (record_id) {
            return window.fetch(
                `${connection_url}/record/Book/${record_id}.json`, 
                {
                    method: 'DELETE', 
                    headers: {
                        "Content-Type": "application/json"
                    }
                }
            ).then(r => {
                window.localStorage.removeItem('tests:create-record-put:result')
                return record_id
            })
        } else {
            return `Error: please first run "create-record-put"`
        }
    }, 
    'create-view': function(connection_url, system_access_url, system_root, connection_id) {
        var view_id = window.LiveElement.Scale.Core.generateUUID4()
        var view = {processor: 'json', content_type: 'application/json', suffix: 'json'}
        return window.fetch(
            `${connection_url}/view/${view_id}.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(view)
            }
        ).then(r => {
            return view_id
        })
    }, 
    'create-query': function(connection_url, system_access_url, system_root, connection_id) {
        var query_id = window.LiveElement.Scale.Core.generateUUID4()
        var query = {processor: 'books', vector: ['numberOfPages'], options: {pagesFilter: true}}
        return window.fetch(
            `${connection_url}/query/Book/${query_id}.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(query)
            }
        ).then(r => {
            return query_id
        })
    }, 
    'create-record-post': function(connection_url, system_access_url, system_root, connection_id) {
        var record_id = window.LiveElement.Scale.Core.generateUUID4()
        var bookNumber = Math.floor(Math.random()* 1000)
        var record = {'@type': 'Book', '@id': record_id, name: `Test Book ${bookNumber}`, numberOfPages: 10}
        var recordAsQuerystring = new URLSearchParams(record).toString();
        return window.fetch(
            `${connection_url}/record/Book/${record_id}.json`, 
            {
                method: 'POST', 
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }, 
                body: recordAsQuerystring
            }
        ).then(r => {
            return record_id
        })
    }, 
    'create-subscription': function(connection_url, system_access_url, system_root, connection_id) {
        var subscription_id = window.LiveElement.Scale.Core.generateUUID4()
        var record_id = window.localStorage.getItem('tests:create-record-post:result')
        var subscription = {view: window.localStorage.getItem('tests:create-view:result')}
        return window.fetch(
            `${connection_url}/subscription/Book/${record_id}/${subscription_id}.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(subscription)
            }
        ).then(r => {
            return subscription_id
        })
    }, 
    'create-feed': function(connection_url, system_access_url, system_root, connection_id) {
        var feed_id = window.LiveElement.Scale.Core.generateUUID4()
        var query_id = window.localStorage.getItem('tests:create-query:result')
        var feed = {view: window.localStorage.getItem('tests:create-view:result')}
        return window.fetch(
            `${connection_url}/feed/Book/${query_id}/${feed_id}.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(feed)
            }
        ).then(r => {
            return feed_id
        })
    }, 
    'update-record-field-put': function(connection_url, system_access_url, system_root, connection_id) {
        var record_id = window.localStorage.getItem('tests:create-record-post:result')
        var numberOfPages = Math.floor(Math.random()* 89) + 11
        return window.fetch(
            `${connection_url}/record/Book/${record_id}/numberOfPages.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(numberOfPages)
            }
        ).then(r => {
            return numberOfPages
        })
    }, 
    'create-bookreadonly-mask': function(connection_url, system_access_url, system_root, connection_id) {
        var mask_id = window.LiveElement.Scale.Core.generateUUID4()
        var mask = {record: {GET: {Book: "*"}}}
        return window.fetch(
            `${connection_url}/mask/${mask_id}.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(mask)
            }
        ).then(r => {
            return mask_id
        })
    }, 
    'create-readonly-authentication-extension': function(connection_url, system_access_url, system_root, connection_id) {
        var module = {
          'processor': 'readonly',
          'options': {
            'types': ['Book'],
          }
        }
        return window.fetch(
            `${connection_url}/system/authentication/readonly.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(module)
            }
        ).then(r => {
            return 'readonly'
        })
    }, 
    'create-bookreadonly-connection': function(connection_url, system_access_url, system_root, connection_id) {
        connection_id = window.LiveElement.Scale.Core.generateUUID4()
        return window.fetch(
            `${system_access_url}${system_root}/connection/${connection_id}/connect.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify({
                    readonly: {}
                }) 
            }
        ).then(r => {
            return connection_id
        })
    }, 
    'delete-bookreadonly-connection': function(connection_url, system_access_url, system_root, connection_id) {
        connection_id = window.localStorage.getItem('tests:create-bookreadonly-connection:result')
        if (connection_id) {
            return window.fetch(
                `${system_access_url}${system_root}/connection/${connection_id}/connect.json`, 
                {
                    method: 'DELETE', 
                    headers: {
                        "Content-Type": "application/json"
                    }
                }
            ).then(r => {
                return connection_id
            })
        } else {
            return `Error: please first run "create-bookreadonly-connection"`
        }
    }, 
    'create-tunnel': function(connection_url, system_access_url, system_root, connection_id) {
        delete window.LiveElement.Scale.Console.Tests.tunnel
        var tunnel_handle = window.LiveElement.Scale.Core.generateUUID4()
        if (system_access_url && system_root && connection_id) {
            var tunnelUrl = `${connection_url.replace('https:', 'wss:')}/tunnel/${tunnel_handle}`
            try {
                window.LiveElement.Scale.Console.Tests.tunnel = new WebSocket(tunnelUrl)
                var now = window.performance.now()
                var tr = document.querySelector('#tests table tr[name="create-tunnel"]')
                window.LiveElement.Scale.Console.Tests.tunnel.addEventListener('message', event => {
                    var message = {}
                    try {
                        message = JSON.parse(event.data)
                        if (tr.querySelector('time[name="process"]').innerHTML == '...') {
                            tr.querySelector('time[name="process"]').innerHTML = Math.round(window.performance.now() - now)
                        }
                        if (tr.querySelector('code.confirmation').innerHTML == '...') {
                            tr.querySelector('code.confirmation').innerHTML = message.tunnel_id
                        }
                        tr.querySelector('code.confirmation').closest('label').setAttribute('status', 'success')
                    } catch(e) {
                        tr.querySelector('time[name="process"]').innerHTML = ' ---error--- '
                        tr.querySelector('code.confirmation').innerHTML = ' ---error--- '
                        tr.querySelector('code.confirmation').closest('label').setAttribute('status', 'error')
                    }
                })
                return tunnelUrl
            } catch (e) {
                return e
            }
        }
    }, 
    'send-tunnel': function(connection_url, system_access_url, system_root, connection_id) {
        var data = window.LiveElement.Scale.Core.generateUUID4()
        if (system_access_url && system_root && connection_id) {
            var tr = document.querySelector('#tests table tr[name="send-tunnel"]')
            tr.setAttribute('now', window.performance.now())
            var receiveMessage = function(event) {
                if (tr.querySelector('time[name="process"]').innerHTML == '...') {
                    tr.querySelector('time[name="process"]').innerHTML = Math.round(window.performance.now() - tr.getAttribute('now'))
                }
                if (tr.querySelector('code.confirmation').innerHTML == '...') {
                    tr.querySelector('code.confirmation').innerHTML = event.data
                }
                tr.querySelector('code.confirmation').closest('label').setAttribute('status', 'success')
                window.LiveElement.Scale.Console.Tests.tunnel.removeEventListener('message', receiveMessage)
            }
            var tunnel_key = document.querySelector('#tests table tr[name="create-tunnel"] code.confirmation').innerHTML
            window.fetch(`${system_access_url}${system_root}/tunnel/${tunnel_key}`, {
                method: 'PUT', 
                body: JSON.stringify(data)
            })
            window.LiveElement.Scale.Console.Tests.tunnel.addEventListener('message', receiveMessage)
        }
        return JSON.stringify(data)
    }, 
    'create-channel': function(connection_url, system_access_url, system_root, connection_id) {
        var channel_id = window.LiveElement.Scale.Core.generateUUID4()
        var channel_object = {
            receiveKey: window.LiveElement.Scale.Core.generateUUID4(), 
            sendKey: window.LiveElement.Scale.Core.generateUUID4(), 
            adminKey: window.LiveElement.Scale.Core.generateUUID4()
        }
        return window.fetch(
            `${connection_url}/channel/${channel_id}/connect.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(channel_object) 
            }
        ).then(r => {
            return channel_id
        })
    }, 
    'subscribe-channel': function(connection_url, system_access_url, system_root, connection_id) {
        delete window.LiveElement.Scale.Console.Tests.channel
        if (system_access_url && system_root && connection_id) {
            var channel_id = window.localStorage.getItem('tests:create-channel:result')
            var channel_object = JSON.parse(window.localStorage.getItem('tests:create-channel:confirmation'))
            var receiveKey = channel_object.receiveKey
            var channelReceiveUrl = `${system_access_url.replace('https:', 'wss:')}${system_root}/channel/${channel_id}/${receiveKey}`
            try {
                window.LiveElement.Scale.Console.Tests.channel = new WebSocket(channelReceiveUrl)
                return channelReceiveUrl
            } catch (e) {
                return e
            }
        }
    }, 
    'send-channel': function(connection_url, system_access_url, system_root, connection_id) {
        var data = window.LiveElement.Scale.Core.generateUUID4()
        if (system_access_url && system_root && connection_id) {
            var channel_id = window.localStorage.getItem('tests:create-channel:result')
            var channel_object = JSON.parse(window.localStorage.getItem('tests:create-channel:confirmation'))
            var sendKey = channel_object.sendKey
            var tr = document.querySelector('#tests table tr[name="send-channel"]')
            tr.setAttribute('now', window.performance.now())
            var receiveMessage = function(event) {
                if (tr.querySelector('time[name="process"]').innerHTML == '...') {
                    tr.querySelector('time[name="process"]').innerHTML = Math.round(window.performance.now() - tr.getAttribute('now'))
                }
                if (tr.querySelector('code.confirmation').innerHTML == '...') {
                    tr.querySelector('code.confirmation').innerHTML = event.data
                }
                tr.querySelector('code.confirmation').closest('label').setAttribute('status', 'success')
                window.LiveElement.Scale.Console.Tests.channel.removeEventListener('message', receiveMessage)
            }
            window.fetch(`${system_access_url}${system_root}/channel/${channel_id}/${sendKey}`, {
                method: 'POST', 
                body: JSON.stringify(data)
            })
            window.LiveElement.Scale.Console.Tests.channel.addEventListener('message', receiveMessage)
        }
        return JSON.stringify(data)
    }, 
    'delete-channel': function(connection_url, system_access_url, system_root, connection_id) {
        var channel_id = window.localStorage.getItem('tests:create-channel:result')
        var channel_object = JSON.parse(window.localStorage.getItem('tests:create-channel:confirmation'))
        var adminKey = channel_object.adminKey
        if (channel_id && adminKey) {
            return window.fetch(
                `${system_access_url}${system_root}/channel/${channel_id}/${adminKey}`, 
                {
                    method: 'DELETE', 
                    headers: {
                        "Content-Type": "application/json"
                    }
                }
            ).then(r => {
                return channel_id
            })
        } else {
            return `Error: please first run "create-bookreadonly-connection"`
        }
    }, 
    'create-daemon': function(connection_url, system_access_url, system_root, connection_id) {
        var num = Math.round(Math.random()*100) + 1
        var daemon_object = {
            state: 'install', 
            schedule: {
                [`Each ${num} Minutes`]: `rate(${num} minutes)`
            }
        }
        return window.fetch(
            `${connection_url}/system/daemon/clock.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(daemon_object) 
            }
        ).then(r => {
            return 'clock'
        })
    }, 
    'run-daemon': function(connection_url, system_access_url, system_root, connection_id) {
        var module_name = window.localStorage.getItem('tests:create-daemon:result')
        var daemon_object = JSON.parse(window.localStorage.getItem('tests:create-daemon:confirmation'))
        daemon_object.state = 'run'
        daemon_object.connection = window.LiveElement.Scale.Core.generateUUID4()
        return window.fetch(
            `${connection_url}/system/daemon/${module_name}.json`, 
            {
                method: 'PUT', 
                headers: {
                    "Content-Type": "application/json"
                }, 
                body: JSON.stringify(daemon_object) 
            }
        ).then(r => {
            return daemon_object.connection
        })
    }, 
    
    
}
