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
    }
}



