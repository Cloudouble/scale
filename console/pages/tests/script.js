window.LiveElement.Scale.Console.Tests = window.LiveElement.Scale.Console.Tests || {}

window.LiveElement.Scale.Console.Tests.runTest = function(tr, test) {
    var resultLabel = tr.querySelector(':scope > td > label')
    resultLabel.setAttribute('status', 'pending')
    tr.querySelector('code').innerHTML = '...'
    var start = window.performance.now()
    tr.querySelector('time').innerHTML = '...'
    var system_access_url = window.localStorage.getItem('system:system_access_url')
    var system_root = window.localStorage.getItem('system:system_root')
    var connection_id = installation.getAttribute('connection-id')
    var connection_url = `${system_access_url}${system_root}/connection/${connection_id}`
    return Promise.resolve(test(connection_url, system_access_url, system_root, connection_id)).then(result => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        resultLabel.setAttribute('status', 'success')
        return result
    }).catch(e => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        resultLabel.setAttribute('status', 'error')
    })
}

window.setTimeout(() => {
    Object.entries(testMap).forEach(entry => {
        installation.querySelector(`[name="${entry[0]}"] button`).addEventListener('click', event => {
            var tr = event.target.closest('[name]')
            window.LiveElement.Scale.Console.Tests.runTest(tr, entry[1]).then(result => {
                tr.querySelector('code').innerHTML = result
            }).catch(e => {
                tr.querySelector('code').innerHTML = e
            })
        })
    })
}, 1)

var tests = document.getElementById('tests')
var installation = tests.querySelector('table[name="installation"]')

if (window.localStorage.getItem('system:connection_id')) {
    installation.setAttribute('connection-id', window.localStorage.getItem('system:connection_id'))
    installation.querySelector('tr[name="create-sudo-connection"] label').setAttribute('status', 'success')
    installation.querySelector('tr[name="create-sudo-connection"] code').innerHTML = window.localStorage.getItem('system:connection_id')
}

var testMap = {
    'create-sudo-connection': function(connection_url, system_access_url, system_root, connection_id) {
        var connection_id = window.LiveElement.Scale.Core.generateUUID4()
        var sudo_key = window.localStorage.getItem('system:sudo_key')
        return window.fetch(`${system_access_url}${system_root}/connection/${connection_id}/connect.json`, 
            {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(
                {sudo: {key: sudo_key}}
            ) }
        ).then(r => {
            installation.setAttribute('connection-id', connection_id)
            return connection_id
        }).catch(e => {
            installation.removeAttribute('connection-id')
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
    'create-view': function(connection_url, system_access_url, system_root, connection_id) {
        var view_id = window.LiveElement.Scale.Core.generateUUID4()
        var view = {processor: 'json', content_type: 'application/json', suffix: 'json'}
        return window.fetch(`${connection_url}/view/${view_id}.json`, {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(view)}).then(r => {
            return view_id
        })
    }, 
    'create-query': function(connection_url, system_access_url, system_root, connection_id) {
        var query_id = window.LiveElement.Scale.Core.generateUUID4()
        var query = {processor: 'books', vector: ['numberOfPages'], options: {pagesFilter: true}}
        return window.fetch(`${connection_url}/query/Book/${query_id}.json`, {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(query)}).then(r => {
            return query_id
        })
    }, 
    'create-record-put': function(connection_url, system_access_url, system_root, connection_id) {
        var record_id = window.LiveElement.Scale.Core.generateUUID4()
        var bookNumber = Math.floor(Math.random()* 1000)
        var record = {'@type': 'Book', '@id': record_id, name: `Test Book ${bookNumber}`, numberOfPages: 10}
        return window.fetch(`${connection_url}/record/Book/${record_id}.json`, {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(record)}).then(r => {
            return record_id
        })
    }, 
    'delete-record': function(connection_url, system_access_url, system_root, connection_id) {
        var record_id = installation.querySelector('[name="create-record-put"] code').innerHTML
        if (record_id) {
            return window.fetch(`${connection_url}/record/Book/${record_id}.json`, {method: 'DELETE', headers: {"Content-Type": "application/json"}}).then(r => {
                return record_id
            })
        } else {
            return `Error: please first run "${installation.querySelector('[name="create-record-put"] th[scope="row"]').innerText.split('\n').shift()}"`
        }
    }, 
    'create-record-post': function(connection_url, system_access_url, system_root, connection_id) {
        var record_id = window.LiveElement.Scale.Core.generateUUID4()
        var bookNumber = Math.floor(Math.random()* 1000)
        var record = {'@type': 'Book', '@id': record_id, name: `Test Book ${bookNumber}`, numberOfPages: 10}
        var recordAsQuerystring = new URLSearchParams(record).toString();
        return window.fetch(`${connection_url}/record/Book/${record_id}.json`, {method: 'POST', headers: {"Content-Type": "application/x-www-form-urlencoded"}, body: recordAsQuerystring}).then(r => {
            return record_id
        })
    }, 
    
    'create-subscription': function(connection_url, system_access_url, system_root, connection_id) {
        var subscription_id = window.LiveElement.Scale.Core.generateUUID4()
        var subscription = {processor: 'books', vector: ['numberOfPages'], options: {pagesFilter: true}}
        return window.fetch(`${connection_url}/subscription/Book/${subscription_id}.json`, {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(subscription)}).then(r => {
            return subscription_id
        })
    }
}



