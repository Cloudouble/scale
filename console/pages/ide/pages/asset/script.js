window.LiveElement.Live.processors.IdeAssetEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="asset"] fieldset[name="edit"]')
    if (handlerType == 'trigger') {
        if (input.entity) {
            window.LiveElement.Scale.Console.IDE.Asset.assetElement = editFieldset.querySelector('element-asset')
            if (window.LiveElement.Scale.Console.IDE.Asset.assetElement) {
                window.LiveElement.Scale.Console.IDE.Asset.assetElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Asset.assetElement = document.createElement('element-asset')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Asset.assetElement)
            window.LiveElement.Scale.Console.IDE.Asset.assetElement.mode = 'editor'
            //Object.keys(input.entity).sort().forEach(k => window.LiveElement.Scale.Console.IDE.Asset.assetElement[k] = input.entity[k])
            Object.assign(window.LiveElement.Scale.Console.IDE.Asset.assetElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Asset.assetElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('asset')
            })
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('asset')
