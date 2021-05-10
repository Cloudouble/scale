window.LiveElement.Live.processors.IdeAssetSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return {...window.LiveElement.Scale.Console.IDE.Asset.Edit.asset, ...{path : window.LiveElement.Scale.Console.IDE.Asset.Edit.path}}
    } else if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        var searchFieldset = input.triggersource.closest('fieldset')
        var searchInput = searchFieldset.querySelector('input[name="search"]')
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
        } else if (input.attributes.name == 'load') {
            window.LiveElement.Scale.Console.IDE.Asset.Edit.path = searchInput.value
            window.LiveElement.Scale.Console.IDE.Asset.Edit.asset = window.LiveElement.Scale.Console.IDE.Asset.Search[searchInput.value]
            if (window.LiveElement.Scale.Console.IDE.Asset.Edit.asset) {
                searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
            }
        } else if (input.attributes.name == 'new') {
            searchInput.value = ''
            window.LiveElement.Scale.Console.IDE.Asset.Edit.path = ''
            window.LiveElement.Scale.Console.IDE.Asset.Edit.asset = {}
            if (window.LiveElement.Scale.Console.IDE.Asset.Edit.asset) {
                searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
            }
        }
    }
}
window.LiveElement.Live.processors.IdeAssetEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        var fieldset = input.triggersource.closest('fieldset')
        var contentTypeInput = fieldset.querySelector('input[name="content-type"]')
        var datalist = fieldset.querySelector('datalist')
        var suffix = `.${input.properties.value.split('.').pop()}`
        var matchedOptions = Array.from(datalist.querySelectorAll('option')).filter(opt => {
            return opt.innerText.indexOf(`(${suffix})`) > 0
        })
        if (matchedOptions.length) {
            contentTypeInput.value = matchedOptions[0].getAttribute('value')
        }
    } else if (handlerType == 'subscription') {
        var pathInput = input.subscriber.querySelector(`input[name="path"]`)
        pathInput.value = input.payload.path || ''
        input.subscriber.querySelector(`input[name="content-type"]`).value = input.payload.ContentType || ''
        if (!pathInput.value) {
            pathInput.focus()
        }
    } else if (handlerType == 'listener') {
        console.log('line 46: listener', input)
    }
}



window.LiveElement.Live.listeners.IdeAssetSearch = {processor: 'IdeAssetSearch', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="asset"] fieldset[name="search"]'), 'IdeAssetSearch', 'loaded', false, true)










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
window.LiveElement.Scale.Console.IDE.Asset.editor.setOptions({
    autoScrollEditorIntoView: true, 
    useSoftTabs: true, 
    navigateWithinSoftTabs: true, 
    highlightGutterLine: true, 
    displayIndentGuides: true, 
    maxLines: 30,
    minLines: 10, 
    scrollPastEnd: 0.5, 
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true, 
    enableSnippets: true, 
    theme: 'ace/theme/merbivore'
})

window.LiveElement.Scale.Console.IDE.Asset.editor.renderer.setScrollMargin(10, 10)

window.LiveElement.Scale.Console.IDE.Asset.editor.session.setMode("ace/mode/javascript")

/* 

var modelist = ace.require("ace/ext/modelist")
window.LiveElement.Scale.Console.IDE.Asset.editor.setReadOnly(true)
window.LiveElement.Scale.Console.IDE.Asset.editor.setMode(modelist.getModeForPath('abc.html').mode);


*/