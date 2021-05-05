window.LiveElement.Scale.Console.IDE = window.LiveElement.Scale.Console.IDE || {}
var ide = document.getElementById('ide')
ide.querySelectorAll('div[name="sidebar"] button').forEach(button => {
    window.LiveElement.Scale.Console.IDE[button.innerHTML] = window.LiveElement.Scale.Console.IDE[button.innerHTML] || {}
})

window.LiveElement.Live.processors.IdeChannelConfigure = function(input) {
    if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        if (input.attributes.name == 'new') {
            var channel_configure = ide.querySelector('fieldset[name="configure"]')
            var elements = {}
            ;(['name', 'id', 'receiveKey', 'sendKey', 'adminKey']).forEach(n => {
                elements[n] = channel_configure.querySelector(`input[name="${n}"]`)
                if (n != 'name') {
                    elements[n].value = window.LiveElement.Scale.Core.generateUUID4()
                }
            })
            var channelId = elements['id'].value
            var channelObject = {receiveKey: elements.receiveKey.value, sendKey: elements.sendKey.value, adminKey: elements.adminKey.value}
            window.LiveElement.Scale.Console.IDE.Channel.Configure = {...{name: elements.name.value, id: elements.id.value}, ...channelObject}
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
            buildSnippet()
        } else if ((['name', 'id', 'receiveKey', 'sendKey', 'adminKey']).includes(input.attributes.name)) {
            window.LiveElement.Scale.Console.IDE.Channel.Configure = window.LiveElement.Scale.Console.IDE.Channel.Configure || {}
            window.LiveElement.Scale.Console.IDE.Channel.Configure[input.attributes.name] = input.properties.value
        }
    }

}

ide.querySelectorAll('input[type="uuid"]').forEach(uuidInput => {
    uuidInput.setAttribute('pattern', '^[0-9a-z]{8}-[0-9a-z]{4}-4[0-9a-z]{3}-[89ab][0-9a-z]{3}-[0-9a-z]{12}$')
    uuidInput.setAttribute('type', 'text')
})
ide.querySelectorAll('div[name="sidebar"] button').forEach(button => {
    button.addEventListener('click', event => {
        ide.setAttribute('entity-type', button.innerHTML.toLowerCase())
    })
})
