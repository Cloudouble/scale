window.LiveElement.Live.processors.IdeRecordTypeEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="recordtype"] fieldset[name="edit"]')
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="recordtype"] fieldset[name="code"]')
    if (handlerType == 'listener') {
        return {
            '@id': (window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement || {})['@id'], 
            mask: (window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement || {}).mask, 
            authentication: (window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement || {}).authentication
        }
    } else if (handlerType == 'trigger') {
        if (input.entity) {
            editFieldset.setAttribute('active', true)
            codeFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement = editFieldset.querySelector('element-recordtype')
            if (window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement) {
                window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement = document.createElement('element-recordtype')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement)
            window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement, input.entity)
            window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'recordtype')
            })
            window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement.setAttribute('live-subscription', 'IdeRecordTypeEdit:IdeRecordTypeCode')
            window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.RecordType.recordtypeElement, 'IdeRecordTypeEdit', 'change', false, true)
        } else {
            editFieldset.removeAttribute('active')
            codeFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Live.processors.IdeRecordTypeCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="recordtype"] fieldset[name="code"]')
    if (handlerType == 'subscription') {
        var websocketUrlInputElement = codeFieldset.querySelector('input[name="websocketUrl"]')
        if (websocketUrlInputElement && input.payload['@id']) {
            websocketUrlInputElement.value = (input.payload['@id']) ? `${window.LiveElement.Scale.Console.IDE.systemURL}/recordtype/${input.payload['@id']}/websocket` : ''
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('ide', 'recordtype')

window.LiveElement.Live.listeners.IdeRecordTypeEdit = {processor: 'IdeRecordTypeEdit', expired: true}
