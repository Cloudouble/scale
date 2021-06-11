window.LiveElement.Scale.Console.Tests = window.LiveElement.Scale.Console.Tests || {}

window.LiveElement.Scale.Console.Tests.runTest = function(tr, test) {
    var testName = tr.getAttribute('name'), confirmationLabelSummary = window.LiveElement.Scale.Console.Tests.testMap[testName].confirmationLabel
    var previousResult = window.localStorage.getItem(`tests:${testName}:result`)
    window.localStorage.removeItem(`tests:${testName}:result`)
    var resultLabel = tr.querySelector(':scope > td > label[name="result"]'), confirmationLabel = tr.querySelector(':scope > td > label[name="confirmation"]')
    resultLabel.setAttribute('status', 'pending')
    resultLabel.querySelector('code').innerHTML = '---running---'
    confirmationLabel.querySelector('div').innerHTML = `<element-snippet open="true", summary="${confirmationLabelSummary}">---waiting---</element-snippet>`
    confirmationLabel.setAttribute('status', 'pending')
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
        confirmationLabel.querySelector('div').innerHTML = `<element-snippet open="true", summary="${confirmationLabelSummary}">---confirming---</element-snippet>`
        window.LiveElement.Scale.Console.System.invokeLambda({
            page: 'tests', 
            test: testName, 
            context: testContext, 
            result: result, 
        }).then(processResult => {
            if (!(processResult && typeof processResult == 'object' && processResult.confirmation === false)) {
                tr.querySelector('time[name="process"]').innerHTML = processResult && typeof processResult == 'object' && typeof processResult.timing == 'number' ? processResult.timing : ' ---error--- '
                confirmationLabel.querySelector('div').innerHTML = processResult && typeof processResult == 'object' && processResult.confirmation && typeof processResult.confirmation == 'object' 
                    ? `<element-snippet open="true", summary="${confirmationLabelSummary}">${JSON.stringify(processResult.confirmation, null, 4)}</element-snippet>` 
                    : `<element-snippet open="true", summary="${confirmationLabelSummary}">${processResult.confirmation}</element-snippet>`
                confirmationLabel.setAttribute('status', 'success')
                window.localStorage.setItem(`tests:${testName}:confirmation`, JSON.stringify(processResult.confirmation, null, 4))
            }
        })
        return result
    }).catch(e => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        resultLabel.setAttribute('status', 'error')
        tr.querySelector('time[name="process"]').innerHTML = ' ---error--- '
        confirmationLabel.querySelector('div').innerHTML = `<element-snippet open="true", summary="${confirmationLabelSummary}">---error---</element-snippet>`
        confirmationLabel.setAttribute('status', 'error')
    })
}

window.setTimeout(() => {
    var tableElement = document.getElementById('tests').querySelector('table'), 
        tableElementTbody = tableElement.querySelector('tbody')
    Object.entries(window.LiveElement.Scale.Console.Tests.testMap).forEach(entry => {
        var testTr = window.LiveElement.Scale.Core.createElement('tr', {name: entry[0]})
        var testTh = window.LiveElement.Scale.Core.createElement('th', {scope: 'row'}, 
            `${entry[1].title}<div><i>${entry[0]}</i><button>Run</button><time name="request">0</time><time name="process">0</time></div>`)
        testTh.querySelector('button').addEventListener('click', event => {
            window.LiveElement.Scale.Console.Tests.runTest(testTr, entry[1].runner).then(result => {
                testTr.querySelector('label[name="result"] code').innerHTML = result
            }).catch(e => {
                testTr.querySelector('label[name="result"] code').innerHTML = e
            })
        })
        testTr.appendChild(testTh)
        var testTd = document.createElement('td')
        testTd.innerHTML = `<label name="result">${entry[1].resultLabel}<code></code></label><label name="confirmation"><div></div></label>`
        testTr.appendChild(testTd)
        var resultStorageKey = `tests:${entry[0]}:result`, confirmationStorageKey = `tests:${entry[0]}:confirmation`
        if (window.localStorage.getItem(resultStorageKey)) {
            testTd.querySelector('label[name="result"]').setAttribute('status', 'success')
            testTd.querySelector('label[name="result"] code').innerHTML = window.localStorage.getItem(resultStorageKey)
        }
        if (window.localStorage.getItem(confirmationStorageKey)) {
            testTd.querySelector('label[name="confirmation"]').setAttribute('status', 'success')
            testTd.querySelector('label[name="confirmation"] div').innerHTML = `<element-snippet open="true", summary="${entry[1].confirmationLabel}">${window.localStorage.getItem(confirmationStorageKey)}</element-snippet>`
        }
        tableElementTbody.appendChild(testTr)
        var snippetTr = window.LiveElement.Scale.Core.createElement('tr', {class: 'snippet'}, `<td colspan="2"><element-snippet>${entry[1].runner.toString()}</element-snippet></td>`)
        tableElementTbody.appendChild(snippetTr)
    })
}, 1)

window.LiveElement.Scale.Console.Tests.testMap = {
    'create-sudo-connection': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create Sudo Connection', 
        resultLabel: 'Connection ID', 
        confirmationLabel: 'Connection Object'
    }, 
    'create-websocket': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create A Websocket', 
        resultLabel: 'Socket URL', 
        confirmationLabel: 'Connection Object'
    }, 
    'create-record-put': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create Record Of Type "Book" Using PUT', 
        resultLabel: 'Record ID', 
        confirmationLabel: 'Book Record'
    }, 
    'delete-record': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Delete Record', 
        resultLabel: 'Record ID', 
        confirmationLabel: 'Book Record'
    }, 
    'create-view': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var view = {processor: 'json', content_type: 'application/json'}
    return window.fetch(
        `${connection_url}/system/view/json.json`, 
        {
            method: 'PUT', 
            headers: {
                "Content-Type": "application/json"
            }, 
            body: JSON.stringify(view)
        }
    ).then(r => {
        return 'json'
    })
},
        title: 'Create "json" view', 
        resultLabel: 'View Handle', 
        confirmationLabel: 'View Object'
    }, 
    'create-query': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var query = {processor: 'books', vector: ['numberOfPages'], options: {pagesFilter: true}, recordtypes: ['Book']}
    return window.fetch(
        `${connection_url}/system/query/totalpages.json`, 
        {
            method: 'PUT', 
            headers: {
                "Content-Type": "application/json"
            }, 
            body: JSON.stringify(query)
        }
    ).then(r => {
        return 'totalpages'
    })
},
        title: 'Create "totalPages" Query', 
        resultLabel: 'Query Handle', 
        confirmationLabel: 'Query Object'
    }, 
    'create-record-post': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create Record of Type "Book" Using POST', 
        resultLabel: 'Record ID', 
        confirmationLabel: 'Book Record'
    }, 
    'create-subscription': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create "Book" Subscription', 
        resultLabel: 'Subscription ID',
        confirmationLabel: 'Subscription Object'
    }, 
    'create-feed': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create "totalPages" Feed', 
        resultLabel: 'Feed ID', 
        confirmationLabel: 'Feed Object'
    }, 
    'update-record-field-put': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Update "numberOfPages" Field Using PUT', 
        resultLabel: 'numberOfPages', 
        confirmationLabel: 'Book Record'
    }, 
    'create-bookreadonly-mask': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create "Books-Read-Only" Mask', 
        resultLabel: 'Mask ID', 
        confirmationLabel: 'Mask Object'
    }, 
    'create-readonly-authentication-extension': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create Read-Only Authentication Extension', 
        resultLabel: 'Module Name', 
        confirmationLabel: 'Authentication Module'
    }, 
    'create-bookreadonly-connection': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create "Book-Read-Only" Connection', 
        resultLabel: 'Connection ID', 
        confirmationLAbel: 'Connection Object'
    }, 
    'delete-bookreadonly-connection': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Delete "Book-Read-Only" Connection', 
        resultLabel: 'Connection ID', 
        confirmationLabel: 'Connection Object'
    }, 
    'create-tunnel': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
                    if (tr.querySelector('label[name="confirmation"] code').innerHTML == '---confirming---') {
                        tr.querySelector('label[name="confirmation"] code').innerHTML = message.tunnel_id
                    }
                    tr.querySelector('label[name="confirmation"]').setAttribute('status', 'success')
                } catch(e) {
                    tr.querySelector('time[name="process"]').innerHTML = ' ---error--- '
                    tr.querySelector('label[name="confirmation"] code').innerHTML = ' ---error--- '
                    tr.querySelector('label[name="confirmation"]').setAttribute('status', 'error')
                }
            })
            return tunnelUrl
        } catch (e) {
            return e
        }
    }
}, 
        title: 'Create A Tunnel', 
        resultLabel: 'Tunnel URL', 
        confirmationLabel: 'Tunnel Key'
    }, 
    'send-tunnel': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var data = window.LiveElement.Scale.Core.generateUUID4()
    if (system_access_url && system_root && connection_id) {
        var tr = document.querySelector('#tests table tr[name="send-tunnel"]')
        tr.setAttribute('now', window.performance.now())
        var receiveMessage = function(event) {
            if (tr.querySelector('time[name="process"]').innerHTML == '...') {
                tr.querySelector('time[name="process"]').innerHTML = Math.round(window.performance.now() - tr.getAttribute('now'))
            }
            if (tr.querySelector('label[name="confirmation"] code').innerHTML == '---confirming---') {
                tr.querySelector('label[name="confirmation"] code').innerHTML = event.data
            }
            tr.querySelector('label[name="confirmation"]').setAttribute('status', 'success')
            window.LiveElement.Scale.Console.Tests.tunnel.removeEventListener('message', receiveMessage)
        }
        var tunnel_key = document.querySelector('#tests table tr[name="create-tunnel"] code.confirmation').innerHTML
        window.fetch(`${system_access_url}${system_root}/tunnel/${tunnel_key}`, {
            method: 'PUT', 
            body: JSON.stringify(data)
        })
        window.LiveElement.Scale.Console.Tests.tunnel.addEventListener('message', receiveMessage)
    }
    return JSON.stringify(data, null, 4)
}, 
        title: 'Send Data Via Tunnel', 
        resultLabel: 'Data Sent', 
        confirmationLabel: 'Data Received'
    }, 
    'create-channel': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var channel_id = window.LiveElement.Scale.Core.generateUUID4()
    var channel_object = {
        '@name': 'test', 
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
        title: 'Create A Channel', 
        resultLabel: 'Channel ID', 
        confirmationLabel: 'Channel Object'
    }, 
    'subscribe-channel': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Subscribe To A Channel', 
        resultLabel: 'Channel Receive URL', 
        confirmationLabel: 'Channel Object'
    }, 
    'send-channel': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
            if (tr.querySelector('label[name="confirmation"] code').innerHTML == '---confirming---') {
                tr.querySelector('label[name="confirmation"] code').innerHTML = event.data
            }
            tr.querySelector('label[name="confirmation"]').setAttribute('status', 'success')
            window.LiveElement.Scale.Console.Tests.channel.removeEventListener('message', receiveMessage)
        }
        window.fetch(`${system_access_url}${system_root}/channel/${channel_id}/${sendKey}`, {
            method: 'POST', 
            body: JSON.stringify(data)
        })
        window.LiveElement.Scale.Console.Tests.channel.addEventListener('message', receiveMessage)
    }
    return JSON.stringify(data, null, 4)
}, 
        title: 'Send Data To A Channel', 
        resultLabel: 'Data Sent', 
        confirmationLabel: 'Data Received'
    }, 
    'delete-channel': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Delete A Channel', 
        resultLabel: 'Channel ID', 
        confirmationLabel: 'Channel Object'
    }, 
    'create-daemon': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Create A Daemon', 
        resultLabel: 'Module Name', 
        confirmationLabel: 'Module Configuration'
    }, 
    'run-daemon': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
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
        title: 'Start A Daemon', 
        resultLabel: 'Daemon Connection ID', 
        confirmationLabel: 'Daemon Configuration'
    }, 
    'pause-daemon': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var module_name = window.localStorage.getItem('tests:create-daemon:result')
    var daemon_object = JSON.parse(window.localStorage.getItem('tests:run-daemon:confirmation'))
    daemon_object.state = 'pause'
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
        title: 'Stop A Daemon', 
        resultLabel: 'Daemon Connection ID', 
        confirmationLabel: 'Daemon Configuration'
    }, 
    'remove-daemon': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var module_name = window.localStorage.getItem('tests:create-daemon:result')
    var daemon_object = JSON.parse(window.localStorage.getItem('tests:pause-daemon:confirmation'))
    daemon_object.state = 'remove'
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
        return module_name
    })
}, 
        title: 'Remove A Daemon', 
        resultLabel: 'Daemon ID', 
        confirmationLabel: 'Daemon Configuration'
    }, 
    'create-418-error': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var num = Math.round(Math.random()*100) + 1
    var html_code = `<html><head><title>Error 418</title></head><body>I'm teapot number ${num}.</body></html>`
    return window.fetch(
        `${connection_url}/error/418.html`, 
        {
            method: 'PUT', 
            headers: {
                "Content-Type": "text/html"
            }, 
            body: html_code 
        }
    ).then(r => {
        return html_code
    })
}, 
        title: 'Create "418" Custom Error Page', 
        resultLabel: 'Error Page Text', 
        confirmationLabel: 'Error Page Text'
    }, 
    'create-custom-recordtype': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var novel_type_definition = {
        "label": "Novel",
        "comment": "A book containing a long fictional story.",
        "subclassof": [
            "Book"
        ],
        "release": "1.0",
        "parents": [
            "Book",
            "CreativeWork",
            "Thing"
        ],
        "properties": {
            "synopsis": [
                "Text"
            ]
        }
    }
    return window.fetch(
        `${connection_url}/system/recordtype/Novel.json`, 
        {
            method: 'PUT', 
            headers: {
                "Content-Type": "application/json"
            }, 
            body: JSON.stringify(novel_type_definition) 
        }
    ).then(r => {
        return 'Novel'
    })
}, 
        title: 'Create Custom Record Type "Novel" Based On The "Book" Record Type', 
        resultLabel: 'Type Object', 
        confirmationLabel: 'Type Object'
    }, 
    'create-custom-record': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var record_id = window.LiveElement.Scale.Core.generateUUID4()
    var novelNumber = Math.floor(Math.random()* 1000)
    var record = {'@type': 'Novel', '@id': record_id, name: `Novel Named ${novelNumber}`, numberOfPages: 1000, synopsis: `${novelNumber} goes on an adventure...`}
    return window.fetch(
        `${connection_url}/record/Novel/${record_id}.json`, 
        {
            method: 'PUT', 
            headers: {"Content-Type": "application/json"}, 
            body: JSON.stringify(record)
        }
    ).then(r => {
        return record_id
    })
}, 
        title: 'Create A New "Novel" Record', 
        resultLabel: 'Record ID', 
        confirmationLabel: 'Novel Record'
    }, 
    'install-schema': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var schema_url = `https://schema.org/version/12.0/schemaorg-all-https.jsonld`
    var schema_id = 'schemaorg-12.0'
    return window.fetch(
        `${connection_url}/system/schema/${schema_id}.json`, 
        {
            method: 'PUT', 
            headers: {
                "Content-Type": "application/json"
            }, 
            body: JSON.stringify(schema_url)
        }
    ).then(r => {
        return schema_id
    })
}, 
        title: 'install A Schema', 
        resultLabel: 'Schema ID', 
        confirmationLabel: 'Schema Configuration'
    }, 
    'uninstall-schema': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var schema_id = 'schemaorg-12.0'
    return window.fetch(
        `${connection_url}/system/schema/${schema_id}.json`, 
        {
            method: 'DELETE'
        }
    ).then(r => {
        return schema_id
    })
}, 
        title: 'Uninstall A Schema', 
        resultLabel: 'Schema ID', 
        confirmationLabel: 'Package Configuration'
    }, 
    'install-package': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var package_definition = {
        id: 'novella', 
        state: 'install', 
        entity_map: {
            'system': {
                'recordtype': {
                    'Novella': {
                        "label": "Novella",
                        "comment": "A short novel.",
                        "subclassof": [
                            "Novel"
                        ],
                        "release": "1.0",
                        "parents": [
                            "Novel", 
                            "Book",
                            "CreativeWork",
                            "Thing"
                        ],
                        "properties": {
                            "universe": [
                                "Text"
                            ]
                        }
                    }
                }
            }
        }
    }
    return window.fetch(
        `${connection_url}/system/package/novella.json`, 
        {
            method: 'PUT', 
            headers: {
                "Content-Type": "application/json"
            }, 
            body: JSON.stringify(package_definition) 
        }
    ).then(r => {
        return 'novella'
    })
}, 
        title: 'Install A Package', 
        resultLabel: 'Package ID', 
        confirmationLabel: 'Package Configuration'
    }, 
    'uninstall-package': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var module_name = window.localStorage.getItem('tests:install-package:result')
    var package_object = JSON.parse(window.localStorage.getItem('tests:install-package:confirmation'))
    package_object.state = 'remove'
    return window.fetch(
        `${connection_url}/system/package/${module_name}.json`, 
        {
            method: 'PUT', 
            headers: {
                "Content-Type": "application/json"
            }, 
            body: JSON.stringify(package_object) 
        }
    ).then(r => {
        return module_name
    })
}, 
        title: 'Remove A Package', 
        resultLabel: 'Package ID', 
        confirmationLabel: 'Package Configuration'
    }, 
    'build-snapshot': {
        runner: 
function(connection_url, system_access_url, system_root, connection_id) {
    var snapshot_id = window.LiveElement.Scale.Core.generateUUID4()
    var snapshot_definition = {
        'directives': {
            'system': {
                'recordtype': ['Novel', 'Novella'],
                'authentication': true
            }, 
            'view': 'processor=json'
        }
    }
    return window.fetch(
        `${connection_url}/system/snapshot/${snapshot_id}.json`, 
        {
            method: 'PUT', 
            headers: {
                "Content-Type": "application/json"
            }, 
            body: JSON.stringify(snapshot_definition) 
        }
    ).then(r => {
        return snapshot_id
    })
},
        title: 'Build A Snapshot', 
        resultLabel: 'Snapshot ID', 
        confirmationLabel: 'Snapshot Package Configuration'
    }
}
