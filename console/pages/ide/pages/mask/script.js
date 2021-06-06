window.LiveElement.Live.processors.IdeMaskEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="mask"] fieldset[name="edit"]')
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="mask"] fieldset[name="code"]')
    if (handlerType == 'listener') {
        return {
            '@id': (window.LiveElement.Scale.Console.IDE.Mask.maskElement || {})['@id'], 
            mask: (window.LiveElement.Scale.Console.IDE.Mask.maskElement || {}).mask, 
            authentication: (window.LiveElement.Scale.Console.IDE.Mask.maskElement || {}).authentication
        }
    } else if (handlerType == 'trigger') {
        if (input.entity) {
            editFieldset.setAttribute('active', true)
            codeFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.Mask.maskElement = editFieldset.querySelector('element-mask')
            if (window.LiveElement.Scale.Console.IDE.Mask.maskElement) {
                window.LiveElement.Scale.Console.IDE.Mask.maskElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Mask.maskElement = document.createElement('element-mask')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Mask.maskElement)
            window.LiveElement.Scale.Console.IDE.Mask.maskElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Mask.maskElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Mask.maskElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'mask')
            })
            window.LiveElement.Scale.Console.IDE.Mask.maskElement.setAttribute('live-subscription', 'IdeMaskEdit:IdeMaskCode')
            window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Mask.maskElement, 'IdeMaskEdit', 'change', false, true)
        } else {
            editFieldset.removeAttribute('active')
            codeFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Live.processors.IdeMaskCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="mask"] fieldset[name="code"]')
    if (handlerType == 'subscription') {
        var websocketUrlInputElement = codeFieldset.querySelector('input[name="websocketUrl"]')
        if (websocketUrlInputElement && input.payload['@id']) {
            websocketUrlInputElement.value = (input.payload['@id']) ? `${window.LiveElement.Scale.Console.IDE.systemURL}/mask/${input.payload['@id']}/websocket` : ''
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('ide', 'mask')

window.LiveElement.Live.listeners.IdeMaskEdit = {processor: 'IdeMaskEdit', expired: true}
