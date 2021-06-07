window.LiveElement.Live.processors.IdeProcessorEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="processor"] fieldset[name="edit"]')
    if (handlerType == 'trigger') {
        if (input.entity) {
            editFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.Processor.processorElement = editFieldset.querySelector('element-processor')
            if (window.LiveElement.Scale.Console.IDE.Processor.processorElement) {
                window.LiveElement.Scale.Console.IDE.Processor.processorElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Processor.processorElement = document.createElement('element-processor')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Processor.processorElement)
            window.LiveElement.Scale.Console.IDE.Processor.processorElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Processor.processorElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Processor.processorElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'processor')
            })
        } else {
            editFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('ide', 'processor')
