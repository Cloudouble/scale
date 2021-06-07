window.LiveElement.Live.processors.IdeRecordEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="edit"]')
    if (handlerType == 'trigger') {
        var cleanUp = function() {
            if (window.LiveElement.Scale.Console.IDE.Record.recordElement) {
                window.LiveElement.Scale.Console.IDE.Record.recordElement.remove()
                delete window.LiveElement.Scale.Console.IDE.Record.recordElement
            }
        }
        if (input.entity) {
            cleanUp()
            editFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.Record.recordElement = editFieldset.querySelector('element-record')
            if (window.LiveElement.Scale.Console.IDE.Record.recordElement) {
                window.LiveElement.Scale.Console.IDE.Record.recordElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Record.recordElement = document.createElement('element-record')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Record.recordElement)
            window.LiveElement.Scale.Console.IDE.Record.recordElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Record.recordElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Record.recordElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'record')
            })
        } else {
            cleanUp()
            editFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('ide', 'record')

