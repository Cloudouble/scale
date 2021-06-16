window.LiveElement.Scale.Console.System = window.LiveElement.Scale.Console.System || {}
window.LiveElement.Scale.Console.System.createSudoConnection = function() {
    var connection_id = window.LiveElement.Scale.Core.generateUUID4()
    var system_access_url = window.localStorage.getItem('system:system_access_url')
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
window.LiveElement.Scale.Console.System.invokeLambda = function(payload) {
    return new Promise(function(resolve, reject) {
        if (window.localStorage.getItem('system:lambda_namespace') && window.localStorage.getItem('system:sudo_key') && payload && typeof payload == 'object') {
                payload._key = window.localStorage.getItem('system:sudo_key')
                payload._host = window.location.host
            window.LiveElement.Scale.Console.System.lambda.invoke({
                FunctionName: `${window.localStorage.getItem('system:lambda_namespace')}-core-console`, 
                Payload: JSON.stringify(payload)
            }, function(err, data) { 
                if (err) {
                    reject(err)
                } else {
                    resolve(JSON.parse(data.Payload))
                }
            })
        } else {
            reject(undefined)
        }
    })
}


;(['system_access_url', 'system_root', 'lambda_namespace', 'sudo_key', 'aws_region', 'aws_access_key_id', 'aws_secret_access_key']).forEach(name => {
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
    if (name.slice(0, 4) == 'aws_') {
        if (['aws_region', 'aws_access_key_id', 'aws_secret_access_key'].every(name => document.querySelector(`section[id="system"] input[name="${name}"]`).value)) {
            var aws_config = new window.AWS.Config({
                accessKeyId: document.querySelector(`section[id="system"] input[name="aws_access_key_id"]`).value, 
                secretAccessKey: document.querySelector(`section[id="system"] input[name="aws_secret_access_key"]`).value, 
                region: document.querySelector(`section[id="system"] input[name="aws_region"]`).value
            })
            window.LiveElement.Scale.Console.System.lambda = new window.AWS.Lambda(aws_config)
        } else {
            delete window.LiveElement.Scale.Console.System.lambda
        }
    }
})

Promise.resolve(function() {
    if ((['system_access_url', 'system_root', 'lambda_namespace', 'sudo_key']).every(k => window.localStorage.getItem(`system:${k}`)) && !window.localStorage.getItem('system:connection_id')) {
        return window.LiveElement.Scale.Console.System.createSudoConnection()
    } else {
        return document.querySelector(`[name="system:connection_id"]`).innerHTML = window.localStorage.getItem('system:connection_id')
    }
}()).then(() => {
    return Promise.all((['environment']).map(table => {
        return window.LiveElement.Scale.Console.System.invokeLambda({page: 'system', table: table}).then(r => {
            window.LiveElement.Scale.Console.System[table] = r
            var tableElement = document.getElementById(`system:${table}`)
            tableElement.innerHTML = ''
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
                    tableElement.append(tr)
                } else if (entry[1] && typeof entry[1] == 'object') {
                    var th = document.createElement('th')
                    th.setAttribute('scope', 'col')
                    th.setAttribute('colspan', 2)
                    th.innerHTML = `<h3>${entry[0]}</h3>`
                    tr.append(th)
                    tableElement.append(tr)
                    Object.entries(entry[1]).forEach(moduleentry => {
                        var tr = document.createElement('tr')
                        var th = document.createElement('th')
                        th.setAttribute('scope', 'row')
                        var td = document.createElement('td')
                        th.innerHTML = moduleentry[0]
                        td.innerHTML = `<code>${JSON.stringify(moduleentry[1])}</code>`
                        tr.append(th)
                        tr.append(td)
                        tableElement.append(tr)
                    })
                }
            })
        }).catch(err => {
            console.log(`line 119: error loading ${table}`, err)
        })
    }))
})

