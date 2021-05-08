window.LiveElement.Live.processors.IdeAssetSearch = function(input) {
    if (input.attributes.name == 'search') {
        var event = input.vector.split(':').shift()
        if (event == 'keyup') {
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'asset', 
                heading: 'search',
                search: input.properties.value
            }).then(searchResult => {
                if (searchResult && typeof searchResult == 'object' && searchResult.result && typeof searchResult.result == 'object') {
                    window.LiveElement.Scale.Console.IDE.Asset.Search = searchResult.result
                    var datalist = document.getElementById('ide-asset-search-list')
                    datalist.innerHTML = ''
                    Object.keys(window.LiveElement.Scale.Console.IDE.Asset.Search).sort().forEach(asset_path => {
                        var optionElement = document.createElement('option')
                        optionElement.setAttribute('value', asset_path)
                        optionElement.innerHTML = asset_path
                        datalist.appendChild(optionElement)
                    })
                }
            })
        }
    }
}
window.LiveElement.Live.processors.IdeAssetView = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        
    } else if (handlerType == 'subscription') {
        
    } else if (handlerType == 'listener') {
        
    }
}
window.LiveElement.Live.processors.IdeChannelCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return {}
    } else if (handlerType == 'subscription') {
        window.LiveElement.Scale.Console.IDE.Asset.Code = {
            view_url: `${window.localStorage.getItem('system:system_access_url').replace('https:', 'wss:')}${window.localStorage.getItem('system:system_root')}/channel/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel_id}/${window.LiveElement.Scale.Console.IDE.Channel.Configure.channel.receiveKey}`, 
        }
        if (input.subscriber.name == 'view_url') {
            return {'#value': window.LiveElement.Scale.Console.IDE.Channel.Code.receive_url}
        }
    }
}

window.LiveElement.Live.listeners.IdeAssetSearch = {processor: 'IdeAssetSearch', expired: true}
window.LiveElement.Live.listeners.IdeAssetView = {processor: 'IdeAssetView', expired: true}
window.LiveElement.Live.listeners.IdeAssetCode = {processor: 'IdeAssetCode', expired: true}

//window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('fieldset[name="configure"]'), 'IdeChannelCode', 'setup', false, true)


window.LiveElement.Scale.Console.IDE.Asset.div = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="asset"] div.editor')
window.LiveElement.Scale.Console.IDE.Asset.editor = window.ace.edit(window.LiveElement.Scale.Console.IDE.Asset.div)
window.LiveElement.Scale.Console.IDE.Asset.editor.setTheme("ace/theme/monokai")
window.LiveElement.Scale.Console.IDE.Asset.editor.setOptions({
    autoScrollEditorIntoView: true, 
    useSoftTabs: false, 
    navigateWithinSoftTabs: false, 
    highlightGutterLine: false, 
    displayIndentGuides: true, 
    maxLines: 30,
    minLines: 10, 
    scrollPastEnd: 0.5, 
    enableBasicAutocompletion: false, // ext-language_tools.js
    enableLiveAutocompletion: false, // ext-language_tools.js
    enableSnippets: false // ext-language_tools.js
})
window.LiveElement.Scale.Console.IDE.Asset.editor.renderer.setScrollMargin(10, 10)

//editor.session.setMode("ace/mode/javascript");