window.LiveElement.Scale.Console.IDE = window.LiveElement.Scale.Console.IDE || {}

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
    var nameInput = channel_configure.querySelector('input[name="name"]')
    nameInput.focus()
    channel_configure.querySelector('button[name="create"]').addEventListener('click', event => {
        var channelId = elements['id'].value
        var channelObject = {receiveKey: elements.receiveKey.value, sendKey: elements.sendKey.value, adminKey: elements.adminKey.value}
        if (nameInput.value) {
            channelObject['@name'] = nameInput.value
        }
        console.log(channelId, channelObject)
    }, {once: true})
})