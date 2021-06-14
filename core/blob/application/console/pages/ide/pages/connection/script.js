window.LiveElement.Live.processors.IdeConnectionEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="edit"]')
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="code"]')
    if (handlerType == 'listener') {
        return {
            '@id': (window.LiveElement.Scale.Console.IDE.Connection.connectionElement || {})['@id'], 
            mask: (window.LiveElement.Scale.Console.IDE.Connection.connectionElement || {}).mask, 
            authentication: (window.LiveElement.Scale.Console.IDE.Connection.connectionElement || {}).authentication
        }
    } else if (handlerType == 'trigger') {
        if (input.entity) {
            editFieldset.setAttribute('active', true)
            codeFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement = editFieldset.querySelector('element-connection')
            if (window.LiveElement.Scale.Console.IDE.Connection.connectionElement) {
                window.LiveElement.Scale.Console.IDE.Connection.connectionElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement = document.createElement('element-connection')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Connection.connectionElement)
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Connection.connectionElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'connection')
            })
            window.LiveElement.Scale.Console.IDE.Connection.connectionElement.setAttribute('live-subscription', 'IdeConnectionEdit:IdeConnectionCode')
            window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Connection.connectionElement, 'IdeConnectionEdit', 'change', false, true)
        } else {
            editFieldset.removeAttribute('active')
            codeFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Live.processors.IdeConnectionCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="code"]')
    if (handlerType == 'subscription') {
        var websocketUrlInputElement = codeFieldset.querySelector('input[name="websocketUrl"]')
        if (websocketUrlInputElement && input.payload['@id']) {
            websocketUrlInputElement.value = (input.payload['@id']) ? `${window.LiveElement.Scale.Console.IDE.systemURL}/connection/${input.payload['@id']}/websocket` : ''
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('ide', 'connection')

window.LiveElement.Live.listeners.IdeConnectionEdit = {processor: 'IdeConnectionEdit', expired: true}
