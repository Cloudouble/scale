window.LiveElement.Scale.Console.IDE.Asset.buildSnippet = function(snippetParams) {
    window.LiveElement.Scale.Console.IDE.Asset.snippetParams = window.LiveElement.Scale.Console.IDE.Asset.snippetParams || {}
    if (snippetParams && typeof snippetParams == 'object') {
        window.LiveElement.Scale.Console.IDE.Asset.snippetParams = {...window.LiveElement.Scale.Console.IDE.Asset.snippetParams, ...snippetParams}
    }
    window.LiveElement.Scale.Core.buildSnippet(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="asset"] fieldset[name="edit"] div.snippet'))
}

window.LiveElement.Live.processors.IdeAssetSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
        return window.LiveElement.Scale.Console.IDE.Asset.asset
    } else if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        var searchFieldset = input.triggersource.closest('fieldset')
        var searchInput = searchFieldset.querySelector('input[name="search"]')
        var deleteButton = searchFieldset.querySelector('button[name="delete"]')
        var loadButton = searchFieldset.querySelector('button[name="load"]')
        var datalist = searchFieldset.querySelector('datalist')
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
                        datalist.innerHTML = ''
                        Object.keys(window.LiveElement.Scale.Console.IDE.Asset.Search.result).sort().forEach(asset_path => {
                            var optionElement = document.createElement('option')
                            optionElement.setAttribute('value', asset_path)
                            optionElement.innerHTML = asset_path
                            datalist.appendChild(optionElement)
                        })
                    }
                })
            } else if (event == 'input') {
                if (datalist.querySelector(`option[value="${input.properties.value}"]`)) {
                    loadButton.removeAttribute('disabled')
                    deleteButton.removeAttribute('disabled')
                    window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({path: input.properties.value})
                } else {
                    loadButton.setAttribute('disabled', true)
                    deleteButton.setAttribute('disabled', true)
                    window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({path: ''})
                }
            }
        } else if (input.attributes.name == 'load') {
            window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
            window.LiveElement.Scale.Console.IDE.Asset.asset = {...window.LiveElement.Scale.Console.IDE.Asset.Search.result[searchInput.value]}
            window.LiveElement.Scale.Console.IDE.Asset.asset.path = searchInput.value
            searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
            window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({path: searchInput.value})
        } else if (input.attributes.name == 'delete') {
            window.fetch(
                `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/asset/${searchInput.value}`, 
                {method: 'DELETE'}
            ).then(r => {
                searchInput.value = ''
                loadButton.setAttribute('disabled', true)
                deleteButton.setAttribute('disabled', true)
                searchInput.focus()
            })
        }
    }
}
window.LiveElement.Live.processors.IdeAssetEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="asset"] fieldset[name="edit"]')
    var pathInput = editFieldset.querySelector('input[name="path"]')
    var contentTypeInput = editFieldset.querySelector('input[name="content-type"]')
    if (handlerType == 'trigger') {
        window.LiveElement.Scale.Console.IDE.Asset.Edit.div = editFieldset.querySelector('div.editor')
        var datalistContentTypes = document.getElementById('ide--content-type')
        var clearButton = editFieldset.querySelector('button[name="clear"]')
        var saveButton = editFieldset.querySelector('button[name="save"]')
        if (input.attributes.name == 'path') {
            window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
            window.LiveElement.Scale.Console.IDE.Asset.asset.path = input.properties.value
            window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({path: input.properties.value})
            if (input.properties.value && !contentTypeInput.value || contentTypeInput.value == 'application/octet-stream') {
                let matchedOption = datalistContentTypes.querySelector(`option[suffix="${input.properties.value.split('.').pop()}"]`)
                var newValue = matchedOption ? matchedOption.getAttribute('value') : 'application/octet-stream'
                if (contentTypeInput.value != newValue) {
                    contentTypeInput.value = newValue
                    contentTypeInput.dispatchEvent(new window.Event('change'))
                }
            }
            saveButton.removeAttribute('disabled')
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
            if (window.LiveElement.Scale.Console.IDE.Asset.editor && window.LiveElement.Scale.Console.IDE.Asset.Edit.div.getAttribute('editor') != contentTypeBase) {
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
                window.LiveElement.Scale.Console.IDE.Asset.editor.session.on('change', function() {
                    saveButton.removeAttribute('disabled')
                    console.log('line 118')
                    window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({body: window.btoa(window.LiveElement.Scale.Console.IDE.Asset.editor.getValue())})
                })
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.setAttribute('editor', 'text')
                if (window.LiveElement.Scale.Console.IDE.Asset.asset && window.LiveElement.Scale.Console.IDE.Asset.asset.file) {
                    window.LiveElement.Scale.Console.IDE.Asset.asset.file.text().then(t => window.LiveElement.Scale.Console.IDE.Asset.editor.setValue(t))
                } else if (window.LiveElement.Scale.Console.IDE.Asset.asset && window.LiveElement.Scale.Console.IDE.Asset.asset.dataURL) {
                    window.LiveElement.Scale.Console.IDE.Asset.editor.setValue(window.atob(window.LiveElement.Scale.Console.IDE.Asset.asset.dataURL.split(',', 2)[1]))
                    console.log('line 126')
                    window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({body: window.LiveElement.Scale.Console.IDE.Asset.asset.dataURL.split(',', 2)[1]})
                }
            } else if (contentTypeBase == 'image') {
                var imgElement
                var appendImgElement = function() {
                    if (window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL || window.LiveElement.Scale.Console.IDE.Asset.asset.dataURL) {
                        imgElement = document.createElement('img')
                        if (window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL) {
                            imgElement.setAttribute('src', window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL)
                            delete window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL
                        } else {
                            imgElement.setAttribute('src', window.LiveElement.Scale.Console.IDE.Asset.asset.dataURL)
                            delete window.LiveElement.Scale.Console.IDE.Asset.asset.dataURL
                        }
                        window.LiveElement.Scale.Console.IDE.Asset.editor.appendChild(imgElement)
                    }
                }
                if (window.LiveElement.Scale.Console.IDE.Asset.Edit.div.getAttribute('editor') == 'image') {
                    appendImgElement()
                } else {
                    window.LiveElement.Scale.Console.IDE.Asset.Edit.div.removeAttribute('disabled')
                    window.LiveElement.Scale.Console.IDE.Asset.editor = document.createElement('element-imageeditor')
                    window.LiveElement.Scale.Console.IDE.Asset.Edit.div.appendChild(window.LiveElement.Scale.Console.IDE.Asset.editor)
                    window.LiveElement.Scale.Console.IDE.Asset.Edit.div.setAttribute('editor', contentTypeBase)
                    appendImgElement()
                    saveButton.removeAttribute('disabled')
                    console.log('line 153')
                    window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({body: `${window.LiveElement.Scale.Console.IDE.Asset.editor}`})
                }
                if (window.LiveElement.Scale.Console.IDE.Asset.editor) {
                    window.LiveElement.Scale.Console.IDE.Asset.editor.contenttype = input.properties.value
                    window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({contenttype: input.properties.value})
                }
            } else {
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.setAttribute('disabled', true)
                window.LiveElement.Scale.Console.IDE.Asset.Edit.div.removeAttribute('editor')
            }
            saveButton.removeAttribute('disabled')
            window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({contenttype: input.properties.value})
        } else if (input.attributes.name == 'upload') {
            window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
            if (input.triggersource.files.length) {
                window.LiveElement.Scale.Console.IDE.Asset.asset.file = input.triggersource.files[0]
                window.LiveElement.Scale.Console.IDE.Asset.asset.ContentType = window.LiveElement.Scale.Console.IDE.Asset.asset.file.type
                window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({contenttype: window.LiveElement.Scale.Console.IDE.Asset.asset.file.type})
                if (window.LiveElement.Scale.Console.IDE.Asset.asset.path && window.LiveElement.Scale.Console.IDE.Asset.asset.path.slice(-1) == '/') {
                    window.LiveElement.Scale.Console.IDE.Asset.asset.path = `${window.LiveElement.Scale.Console.IDE.Asset.asset.path}${window.LiveElement.Scale.Console.IDE.Asset.asset.file.name}`
                } else if (!window.LiveElement.Scale.Console.IDE.Asset.asset.path) {
                    window.LiveElement.Scale.Console.IDE.Asset.asset.path = window.LiveElement.Scale.Console.IDE.Asset.asset.file.name
                }
                pathInput.value = window.LiveElement.Scale.Console.IDE.Asset.asset.path
                contentTypeInput.value = window.LiveElement.Scale.Console.IDE.Asset.asset.ContentType
                window.LiveElement.Scale.Console.IDE.Asset.asset.objectURL = URL.createObjectURL(window.LiveElement.Scale.Console.IDE.Asset.asset.file)
                window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({contenttype: contentTypeInput.value, path: pathInput.value})
                contentTypeInput.dispatchEvent(new window.Event('change'))
                editFieldset.querySelector('input[type="file"]').value = ''
            } else {
                clearButton.dispatchEvent(new window.Event('click'))
            }
            saveButton.removeAttribute('disabled')
        } else if (input.attributes.name == 'save') {
            var body = window.LiveElement.Scale.Console.IDE.Asset.Edit.div.getAttribute('editor') == 'image' 
                ? `${window.LiveElement.Scale.Console.IDE.Asset.editor}` : window.btoa(window.LiveElement.Scale.Console.IDE.Asset.editor.getValue())
            var contentType = window.LiveElement.Scale.Console.IDE.Asset.Edit.div.getAttribute('editor') == 'image' 
                ? window.LiveElement.Scale.Console.IDE.Asset.editor.contenttype : contentTypeInput.value
            console.log('line 192')
            window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({contenttype: contentType, body: body})
            window.fetch(
                `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/asset/${pathInput.value}`, 
                {method: 'PUT', headers: {"Content-Type": contentType}, body: body}
            ).then(r => {
                saveButton.setAttribute('disabled', true)
            })
        }
    } else if (handlerType == 'subscription') {
        window.LiveElement.Scale.Console.IDE.Asset.asset = {}
        contentTypeInput.value = ''
        pathInput.value = ''
        pathInput.value = input.payload.path || ''
        contentTypeInput.value = input.payload.ContentType || ''
        window.LiveElement.Scale.Console.IDE.Asset.buildSnippet({contenttype: input.payload.ContentType, path: input.payload.path})
        pathInput.dispatchEvent(new window.Event('change'))
        window.LiveElement.Scale.Console.System.invokeLambda({
            page: 'ide', 
            entity_type: 'asset', 
            heading: 'fetch',
            path: input.payload.path
        }).then(fetchResult => {
            if (fetchResult && typeof fetchResult == 'object' && fetchResult.result && typeof fetchResult.result == 'object') {
                window.LiveElement.Scale.Console.IDE.Asset.asset = window.LiveElement.Scale.Console.IDE.Asset.asset || {}
                window.LiveElement.Scale.Console.IDE.Asset.asset.dataURL = `data:${input.payload.ContentType};base64,${fetchResult.result.body}`
                contentTypeInput.dispatchEvent(new window.Event('change'))
            }
        })
        if (!pathInput.value) {
            pathInput.focus()
        }
    }
}

window.LiveElement.Live.listeners.IdeAssetSearch = {processor: 'IdeAssetSearch', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="asset"] fieldset[name="search"]'), 'IdeAssetSearch', 'loaded', false, true)

window.LiveElement.Scale.Core.buildSnippet(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="asset"] fieldset[name="edit"] div.snippet'))
