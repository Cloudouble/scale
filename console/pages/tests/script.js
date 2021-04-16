window.LiveElement.Scale.Console.Tests = window.LiveElement.Scale.Console.Tests || {}

window.LiveElement.Scale.Console.Tests.runTest = function(tr, test) {
    tr.classList.remove('success', 'warning', 'error')
    tr.classList.add('warning')
    var start = window.performance.now()
    tr.querySelector('time').innerHTML = '...'
    test().then(() => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        tr.classList.remove('success', 'warning', 'error')
        tr.classList.add('success')
    }).catch(e => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        tr.classList.remove('success', 'warning', 'error')
        tr.classList.add('error')
        tr.querySelector('code').innerHTML = e
    })
}

var tests = document.getElementById('tests')
var installation = tests.querySelector('table[name="installation"]')

var createSudoConnection = installation.querySelector('[name="create-sudo-connection"]')
createSudoConnection.querySelector('button').addEventListener('click', event => {
    window.LiveElement.Scale.Console.Tests.runTest(createSudoConnection, () => {
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
            createSudoConnection.querySelector('code').innerHTML = connection_id
        }).catch(e => {
            installation.removeAttribute('connection-id')
        })
    })
})



