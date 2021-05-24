window.LiveElement.Live.processors.IdeAssetSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
        return window.LiveElement.Scale.Console.IDE.Asset.asset
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
                        window.LiveElement.Scale.Console.IDE.Asset.Search.result = searchResult.result
                        var datalist = document.getElementById('ide-asset-search-list')
                        datalist.innerHTML = ''
                        Object.keys(window.LiveElement.Scale.Console.IDE.Asset.Search.result).sort().forEach(asset_path => {
                            var optionElement = document.createElement('option')
                            optionElement.setAttribute('value', asset_path)
                            optionElement.innerHTML = asset_path
                            datalist.appendChild(optionElement)
                        })
                    }
                })
            }
        } else if (input.attributes.name == 'load') {
            window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
            window.LiveElement.Scale.Console.IDE.Asset.asset = {...window.LiveElement.Scale.Console.IDE.Asset.Search.result[searchInput.value]}
            window.LiveElement.Scale.Console.IDE.Asset.asset.path = searchInput.value
            searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
        }
    }
}
window.LiveElement.Live.processors.IdeAssetEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'trigger') {
        var editFieldset = input.triggersource.closest('fieldset')
        window.LiveElement.Scale.Console.IDE.Asset.Edit.div = editFieldset.querySelector('div.editor')
        var datalistContentTypes = document.getElementById('ide--content-type')
        var pathInput = editFieldset.querySelector('input[name="path"]')
        var contentTypeInput = editFieldset.querySelector('input[name="content-type"]')
        var clearButton = editFieldset.querySelector('button[name="clear"]')
        var saveButton = editFieldset.querySelector('button[name="save"]')
        if (input.attributes.name == 'path') {
            window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
            window.LiveElement.Scale.Console.IDE.Asset.asset.path = input.properties.value
            if (input.properties.value && !contentTypeInput.value || contentTypeInput.value == 'application/octet-stream') {
                let matchedOption = datalistContentTypes.querySelector(`option[suffix="${input.properties.value.split('.').pop()}"]`)
                var newValue = matchedOption ? matchedOption.getAttribute('value') : 'application/octet-stream'
                if (contentTypeInput.value != newValue) {
                    contentTypeInput.value = newValue
                    contentTypeInput.dispatchEvent(new window.Event('change'))
                }
            }
        } else if (input.attributes.name == 'content-type') {
            var matchedOption = datalistContentTypes.querySelector(`option[value="${input.properties.value}"]`), aceMode
            if (matchedOption) {
                window.LiveElement.Scale.Console.IDE.Asset.Edit.modelist = window.LiveElement.Scale.Console.IDE.Asset.Edit.modelist || window.ace.require("ace/ext/modelist")
                aceMode = window.LiveElement.Scale.Console.IDE.Asset.Edit.modelist.getModeForPath(`test.${matchedOption.getAttribute('suffix')}`).mode
            }
            if (!aceMode) {
                aceMode = 'ace/mode/text'
            }
            var contentTypeBase = input.properties.value.split('/')[0]
            if (window.LiveElement.Scale.Console.IDE.Asset.editor) {
                if (typeof window.LiveElement.Scale.Console.IDE.Asset.editor.destroy == 'function') {
                    window.LiveElement.Scale.Console.IDE.Asset.editor.destroy()
                } else if (typeof window.LiveElement.Scale.Console.IDE.Asset.editor.remove == 'function') {
                    window.LiveElement.Scale.Console.IDE.Asset.editor.remove()
                }
            }
            if (aceMode != 'ace/mode/text' || contentTypeBase == 'text') {
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.removeAttribute('disabled')
                window.LiveElement.Scale.Console.IDE.Asset.editor = window.ace.edit(window.LiveElement.Scale.Console.IDE.Asset.Edit.div)
                window.LiveElement.Scale.Console.IDE.Asset.editor.setOptions({...window.LiveElement.Scale.Console.aceOptions, ...{minLines: 47, maxLines: 47}})
                window.LiveElement.Scale.Console.IDE.Asset.editor.renderer.setScrollMargin(10, 10)
                window.LiveElement.Scale.Console.IDE.Asset.editor.session.setMode(aceMode)
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.setAttribute('editor', 'text')
            } else if (contentTypeBase == 'image') {
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.removeAttribute('disabled')
                window.LiveElement.Scale.Console.IDE.Asset.editor = document.createElement('element-imageeditor')
                if (window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL) {
                    var imgElement = document.createElement('img')
                    imgElement.setAttribute('src', window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL)
                    window.LiveElement.Scale.Console.IDE.Asset.editor.appendChild(imgElement)
                    delete window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL
                }
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.appendChild(window.LiveElement.Scale.Console.IDE.Asset.editor)
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.setAttribute('editor', 'image')
                saveButton.removeAttribute('disabled')
            } else {
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.setAttribute('disabled', true)
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.removeAttribute('editor')
            }
        } else if (input.attributes.name == 'upload') {
            window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
            if (input.triggersource.files.length) {
                window.LiveElement.Scale.Console.IDE.Asset.asset.file = input.triggersource.files[0]
                window.LiveElement.Scale.Console.IDE.Asset.asset.ContentType = window.LiveElement.Scale.Console.IDE.Asset.asset.file.type
                if (window.LiveElement.Scale.Console.IDE.Asset.asset.path && window.LiveElement.Scale.Console.IDE.Asset.asset.path.slice(-1) == '/') {
                    window.LiveElement.Scale.Console.IDE.Asset.asset.path = `${window.LiveElement.Scale.Console.IDE.Asset.asset.path}${window.LiveElement.Scale.Console.IDE.Asset.asset.file.name}`
                } else if (!window.LiveElement.Scale.Console.IDE.Asset.asset.path) {
                    window.LiveElement.Scale.Console.IDE.Asset.asset.path = window.LiveElement.Scale.Console.IDE.Asset.asset.file.name
                }
                pathInput.value = window.LiveElement.Scale.Console.IDE.Asset.asset.path
                contentTypeInput.value = window.LiveElement.Scale.Console.IDE.Asset.asset.ContentType
                window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL = URL.createObjectURL(window.LiveElement.Scale.Console.IDE.Asset.asset.file)
                contentTypeInput.dispatchEvent(new window.Event('change'))
            } else {
                clearButton.dispatchEvent(new window.Event('click'))
            }
        } else if (input.attributes.name == 'clear') {
            window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
            delete window.LiveElement.Scale.Console.IDE.Asset.asset.file
            delete window.LiveElement.Scale.Console.IDE.Asset.asset.body
            delete window.LiveElement.Scale.Console.IDE.Asset.asset.encoding
            if (window.LiveElement.Scale.Console.IDE.Asset.Edit.div.getAttribute('editor') == 'image') {
                window.LiveElement.Scale.Console.IDE.Asset.editor.querySelectorAll('img').forEach(imgElement => {
                    imgElement.remove()
                })
                saveButton.setAttribute('disabled', true)
            } else {
                //clear the text editor
            }
        } else if (input.attributes.name == 'save') {
            if (window.LiveElement.Scale.Console.IDE.Asset.Edit.div.getAttribute('editor') == 'image') {
                window.LiveElement.Scale.Console.IDE.Asset.editor.mime = contentTypeInput.value
                window.fetch(
                    `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/asset/${pathInput.value}`, 
                    {method: 'PUT', headers: {"Content-Type": contentTypeInput.value}, body: `${window.LiveElement.Scale.Console.IDE.Asset.editor}`}
                ).then(r => {
                    saveButton.setAttribute('disabled', true)
                })
            } else {
                //save the text editor value
            }
        }
    } else if (handlerType == 'subscription') {
        var pathInput = input.subscriber.querySelector(`input[name="path"]`)
        pathInput.value = input.payload.path || ''
        input.subscriber.querySelector(`input[name="content-type"]`).value = input.payload.ContentType || ''
        pathInput.dispatchEvent(new window.Event('change'))
        if (!pathInput.value) {
            pathInput.focus()
        }
    } else if (handlerType == 'listener') {
        console.log('line 88: listener', input)
    }
}


window.LiveElement.Live.listeners.IdeAssetSearch = {processor: 'IdeAssetSearch', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="asset"] fieldset[name="search"]'), 'IdeAssetSearch', 'loaded', false, true)





// asset = {body, encoding, ContentType, path, ContentLength, ContentType}



/*
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
*/
/*
window.LiveElement.Live.listeners.IdeAssetSearch = {processor: 'IdeAssetSearch', expired: true}
window.LiveElement.Live.listeners.IdeAssetView = {processor: 'IdeAssetView', expired: true}
window.LiveElement.Live.listeners.IdeAssetCode = {processor: 'IdeAssetCode', expired: true}
*/

//window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('fieldset[name="configure"]'), 'IdeChannelCode', 'setup', false, true)

/*
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
window.LiveElement.Scale.Console.aceOptions
window.LiveElement.Scale.Console.IDE.Asset.editor.renderer.setScrollMargin(10, 10)
window.LiveElement.Scale.Console.IDE.Asset.editor.session.setMode("ace/mode/javascript")
*/
/* 

var modelist = ace.require("ace/ext/modelist")
window.LiveElement.Scale.Console.IDE.Asset.editor.setReadOnly(true)
window.LiveElement.Scale.Console.IDE.Asset.editor.setMode(modelist.getModeForPath('abc.html').mode);


*/