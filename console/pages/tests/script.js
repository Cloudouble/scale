window.LiveElement.Scale.Console.Tests = window.LiveElement.Scale.Console.Tests || {}

window.LiveElement.Scale.Console.Tests.runTest = function(tr, test) {
    tr.classList.remove('success', 'warning', 'error')
    tr.classList.add('warning')
    var start = window.performance.now()
    tr.querySelector('time').innerHTML = '...'
    return test().then(result => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        tr.classList.remove('success', 'warning', 'error')
        tr.classList.add('success')
        return result
    }).catch(e => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        tr.classList.remove('success', 'warning', 'error')
        tr.classList.add('error')
        tr.querySelector('code').innerHTML = e
    })
}

window.setTimeout(() => {
    Object.entries(testMap).forEach(entry => {
        installation.querySelector(`[name="${entry[0]}"] button`).addEventListener('click', event => {
            var tr = event.target.closest('[name')
            window.LiveElement.Scale.Console.Tests.runTest(tr, entry[1]).then(result => {
                tr.querySelector('code').innerHTML = result
            })
        })
    })
}, 1)

var tests = document.getElementById('tests')
var installation = tests.querySelector('table[name="installation"]')

var testMap = {
    'create-sudo-connection': function() {
        var connection_id = window.LiveElement.Scale.Core.generateUUID4()
        var system_access_url = window.localStorage.getItem('system:system_access_url')
        var system_root = window.localStorage.getItem('system:system_root')
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
    }
}



