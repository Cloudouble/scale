window.LiveElement.Scale.Console.Tests = window.LiveElement.Scale.Console.Tests || {}

window.LiveElement.Scale.Console.Tests.runTest = function(tr, test) {
    window.localStorage.removeItem(`tests:${tr.getAttribute('name')}:result`)
    var resultLabel = tr.querySelector(':scope > td > label')
    resultLabel.setAttribute('status', 'pending')
    tr.querySelector('code').innerHTML = '...'
    var start = window.performance.now()
    tr.querySelectorAll('time').forEach(t => t.innerHTML = '...')
    var system_access_url = window.localStorage.getItem('system:system_access_url')
    var system_root = window.localStorage.getItem('system:system_root')
    var connection_id = window.localStorage.getItem(`tests:create-sudo-connection:result`)
    var connection_url = `${system_access_url}${system_root}/connection/${connection_id}`
    return Promise.resolve(test(connection_url, system_access_url, system_root, connection_id)).then(result => {
        tr.querySelector('time[name="request"]').innerHTML = `${Math.round(window.performance.now() - start)}`
        resultLabel.setAttribute('status', 'success')
        window.localStorage.setItem(`tests:${tr.getAttribute('name')}:result`, result)
        return result
    }).catch(e => {
        tr.querySelector('time').innerHTML = `${Math.round(window.performance.now() - start)}ms`
        resultLabel.setAttribute('status', 'error')
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
        var numberOfPages = Math.floor(Math.random()* 88) + 12
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
    }
}



