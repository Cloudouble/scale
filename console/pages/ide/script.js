window.LiveElement.Scale.Console.IDE = window.LiveElement.Scale.Console.IDE || {}

window.LiveElement.Live.processors.ideChannelConfigureSnippet = function() {
    
}

var ide = document.getElementById('ide')
ide.querySelectorAll('input[type="uuid"]').forEach(uuidInput => {
    uuidInput.setAttribute('pattern', '^[0-9a-z]{8}-[0-9a-z]{4}-4[0-9a-z]{3}-[89ab][0-9a-z]{3}-[0-9a-z]{12}$')
    uuidInput.setAttribute('type', 'text')
})
ide.querySelectorAll('div[name="sidebar"] button').forEach(button => {
    button.addEventListener('click', event => {
        ide.setAttribute('entity-type', button.innerHTML.toLowerCase())
    })
})

ide.querySelector('fieldset[name="search"] button[name="new"]').addEventListener('click', event => {
    var channel_configure = ide.querySelector('fieldset[name="configure"]')
    var elements = {}
    ;(['id', 'receiveKey', 'sendKey', 'adminKey']).forEach(n => {
        elements[n] = channel_configure.querySelector(`input[name="${n}"]`)
        elements[n].value = window.LiveElement.Scale.Core.generateUUID4()
    })
    var channelId = elements['id'].value
    var channelObject = {receiveKey: elements.receiveKey.value, sendKey: elements.sendKey.value, adminKey: elements.adminKey.value}
    var nameInput = channel_configure.querySelector('input[name="name"]')
    var buildSnippet = function() {
        var codeSnippet = channel_configure.querySelector('code')
        codeSnippet.innerHTML = `
window.fetch(
    '${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/channel/${channelId}/connect.json', 
    {
        method: 'PUT', 
        headers: {
            "Content-Type": "application/json"
        }, 
        body: JSON.stringify({
            ${JSON.stringify(channelObject, null, 14).slice(1, -1)}
        }) 
    }
)
        `
    }
    nameInput.focus()
    channel_configure.querySelector('button[name="create"]').addEventListener('click', event => {
        if (nameInput.value) {
            channelObject['@name'] = nameInput.value
        }
    }, {once: true})
    nameInput.addEventListener('change', event => {
        if (nameInput.value) {
            channelObject['@name'] = nameInput.value
        }
        buildSnippet()
    })
    buildSnippet()
})