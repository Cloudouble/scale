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
    var system_access_url = window.localStorage.getItem('system:system_access_url')
    var system_root = window.localStorage.getItem('system:system_root')
    var connection_id = window.localStorage.getItem('system:connection_id')
    return Promise.all(Object.entries({
        'system:environment': 'subscription/-/00000000-0000-0000-0000-000000000000/env.json', 
        'system:modules': 'subscription/-/00000000-0000-0000-0000-000000000000/modules.json'
    }).map(entry => {
        return window.fetch(`${system_access_url}${system_root}/connection/${connection_id}/${entry[1]}`).then(r => r.json()).then(r => {
            var table = document.getElementById(entry[0])
            table.innerHTML = ''
            Object.entries(r).forEach(entry => {
                var tr = document.createElement('tr')
                if (typeof entry[1] == 'string') {
                    var th = document.createElement('th')
                    th.setAttribute('scope', 'row')
                    var td = document.createElement('td')
                    th.innerHTML = entry[0]
                    td.innerHTML = entry[1]
                    tr.append(th)
                    tr.append(td)
                    table.append(tr)
                } else if (entry[1] && typeof entry[1] == 'object') {
                    var th = document.createElement('th')
                    th.setAttribute('scope', 'col')
                    th.setAttribute('colspan', 2)
                    th.innerHTML = `<h3>${entry[0]}</h3>`
                    tr.append(th)
                    table.append(tr)
                    Object.entries(entry[1]).forEach(moduleentry => {
                        var tr = document.createElement('tr')
                        var th = document.createElement('th')
                        th.setAttribute('scope', 'row')
                        var td = document.createElement('td')
                        th.innerHTML = moduleentry[0]
                        td.innerHTML = `<code>${JSON.stringify(moduleentry[1])}</code>`
                        tr.append(th)
                        tr.append(td)
                        table.append(tr)
                    })
                }
            })
        })
    }))
})

