window.LiveElement.Scale.Console.Tests = window.LiveElement.Scale.Console.Tests || {}
var tests = document.getElementById('tests')
var installation = tests.querySelector('table[name="installation"]')

var createSudoConnection = installation.querySelector('[name="create-sudo-connection"]')
createSudoConnection.querySelector('button').addEventListener('click', event => {
    installation.removeAttribute('connection-id')
    createSudoConnection.classList.remove('success', 'warning', 'error')
    createSudoConnection.classList.add('warning')
    var start = window.performance.now()
    createSudoConnection.querySelector('time').innerHTML = '...'
    var connection_id = window.LiveElement.Scale.Core.generateUUID4()
    var system_access_url = window.localStorage.getItem('system:system_access_url')
    var system_root = window.localStorage.getItem('system:system_root')
    var sudo_key = window.localStorage.getItem('system:sudo_key')
    return window.fetch(`${system_access_url}${system_root}/connection/${connection_id}/connect.json`, 
        {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(
            {sudo: {key: sudo_key}}
        ) }
    ).then(r => {
        createSudoConnection.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        installation.setAttribute('connection-id', connection_id)
        createSudoConnection.classList.remove('success', 'warning', 'error')
        createSudoConnection.classList.add('success')
        createSudoConnection.querySelector('code').innerHTML = connection_id
    }).catch(e => {
        createSudoConnection.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        installation.removeAttribute('connection-id')
        createSudoConnection.classList.remove('success', 'warning', 'error')
        createSudoConnection.classList.add('error')
        createSudoConnection.querySelector('code').innerHTML = e
    })
    
    
    
    
})



