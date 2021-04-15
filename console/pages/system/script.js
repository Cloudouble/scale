window.LiveElement.Scale.Console.System = window.LiveElement.Scale.Console.System || {}
window.LiveElement.Scale.Console.System.createSudoConnection = function() {
    var connection_id = window.LiveElement.Scale.Core.generateUUID4()
    var system_access_url = window.localStorage.getItem('system:system_access_url')
    var system_root = window.localStorage.getItem('system:system_root')
    var sudo_key = window.localStorage.getItem('system:sudo_key')
    return window.fetch(`${system_access_url}_/connection/${connection_id}/connect.json`, 
        {method: 'PUT', headers: {"Content-Type": "application/json"}, body: JSON.stringify(
            {sudo: {key: sudo_key}}
        ) }
    ).then(r => {
        document.querySelector(`[name="system:connection_id"]`).innerHTML = connection_id
        window.localStorage.setItem(`system:connection_id`, connection_id)
    })
}

;(['system_access_url', 'system_root', 'sudo_key']).forEach(name => {
    var input = document.querySelector(`section[id="system"] input[name="${name}"]`)
    input.value = window.localStorage.getItem(`system:${name}`)
    var checkbox = document.querySelector(`section[id="system"] input[name="${name}"] + small > input[type="checkbox"]`)
    checkbox.addEventListener('change', event => window.LiveElement.Scale.Core.syncWithLocalStorage('system', checkbox, input))
    input.addEventListener('change', event => {
        window.LiveElement.Scale.Core.syncWithLocalStorage('system', checkbox, input)
        window.LiveElement.Scale.Console.System.createSudoConnection()
    })
    if (name == 'system_access_url') {
        if (input.value) {
            let system_access_url = input.value.slice(-1) == '/' ? input.value : `${input.value}/`
            system_access_url = system_access_url.slice(0,8) == 'https://' ? system_access_url : `https://${system_access_url}`
            if (system_access_url != input.value) {
                input.value = system_access_url
                var evt = document.createEvent("HTMLEvents")
                evt.initEvent("change", false, true)
                input.dispatchEvent(evt)
            }
        } else {
            input.value = window.location.origin
            window.LiveElement.Scale.Core.syncWithLocalStorage('system', checkbox, input)
        }
    }
})

Promise.resolve(function() {
    if ((['system_access_url', 'system_root', 'sudo_key']).every(k => window.localStorage.getItem(`system:${k}`)) && !window.localStorage.getItem('system:connection_id')) {
        return window.LiveElement.Scale.Console.System.createSudoConnection()
    } else {
        return document.querySelector(`[name="system:connection_id"]`).innerHTML = window.localStorage.getItem('system:connection_id')
    }
}()).then(() => {
    return window.fetch(`${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/subscription/-/00000000-0000-0000-0000-000000000000/env.json`).then(r => r.json()).then(r => {
        var table_environment = document.getElementById('system:environment')
        table_environment.innerHTML = ''
        Object.entries(r).forEach(entry => {
            let tr = document.createElement('tr')
            let th = document.createElement('th')
            let td = document.createElement('td')
            th.innerHTML = entry[0]
            td.innerHTML = entry[1]
            tr.append(th)
            tr.append(td)
            table_environment.append(tr)
        })
    })
})

