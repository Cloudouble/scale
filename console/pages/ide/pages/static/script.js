window.LiveElement.Live.processors.IdeStaticEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="static"] fieldset[name="edit"]')
    if (handlerType == 'trigger') {
        if (input.entity) {
            window.LiveElement.Scale.Console.IDE.Static.staticElement = editFieldset.querySelector('element-static')
            if (window.LiveElement.Scale.Console.IDE.Static.staticElement) {
                window.LiveElement.Scale.Console.IDE.Static.staticElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Static.staticElement = document.createElement('element-static')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Static.staticElement)
            window.LiveElement.Scale.Console.IDE.Static.staticElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Static.staticElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Static.staticElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'static')
            })
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('ide', 'static')
