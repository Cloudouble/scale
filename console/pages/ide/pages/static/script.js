window.LiveElement.Scale.Console.IDE.Static.buildSnippet = function(snippetParams) {
    window.LiveElement.Scale.Console.IDE.Static.snippetParams = window.LiveElement.Scale.Console.IDE.Static.snippetParams || {}
    if (snippetParams && typeof snippetParams == 'object') {
        window.LiveElement.Scale.Console.IDE.Static.snippetParams = {...window.LiveElement.Scale.Console.IDE.Static.snippetParams, ...snippetParams}
    }
    window.LiveElement.Scale.Console.buildSnippets('static')
}

window.LiveElement.Live.processors.IdeStaticSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        window.LiveElement.Scale.Console.IDE.Static.static = window.LiveElement.Scale.Console.IDE.Static.static || {}
        return window.LiveElement.Scale.Console.IDE.Static.static
    } else if (window.LiveElement.Live.getHandlerType(input) == 'trigger') {
        var searchFieldset = input.triggersource.closest('fieldset')
        var searchInput = searchFieldset.querySelector('input[name="search"]'), deleteButton = searchFieldset.querySelector('button[name="delete"]')
        var loadButton = searchFieldset.querySelector('button[name="load"]'), datalist = searchFieldset.querySelector('datalist')
        if (input.attributes.name == 'search') {
            var event = input.vector.split(':').shift()
            if (event == 'keyup') {
                window.LiveElement.Scale.Console.System.invokeLambda({
                    page: 'ide', entity_type: 'static', heading: 'search', search: input.properties.value
                }).then(searchResult => {
                    if (searchResult && typeof searchResult == 'object' && searchResult.result && typeof searchResult.result == 'object') {
                        window.LiveElement.Scale.Console.IDE.Static.Search.result = searchResult.result
                        datalist.innerHTML = ''
                        Object.keys(window.LiveElement.Scale.Console.IDE.Static.Search.result).sort().forEach(static_path => {
                            var optionElement = document.createElement('option')
                            optionElement.setAttribute('value', static_path)
                            optionElement.innerHTML = static_path
                            datalist.appendChild(optionElement)
                        })
                    }
                })
            } else if (event == 'input') {
                if (datalist.querySelector(`option[value="${input.properties.value}"]`)) {
                    loadButton.removeAttribute('disabled')
                    deleteButton.removeAttribute('disabled')
                } else {
                    loadButton.setAttribute('disabled', true)
                    deleteButton.setAttribute('disabled', true)
                }
                window.LiveElement.Scale.Console.IDE.Static.buildSnippet({path: input.properties.value})
            }
        } else if (input.attributes.name == 'load') {
            window.LiveElement.Scale.Console.IDE.Static.static = {...window.LiveElement.Scale.Console.IDE.Static.Search.result[searchInput.value]}
            window.LiveElement.Scale.Console.IDE.Static.static.path = searchInput.value
            searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
            window.LiveElement.Scale.Console.IDE.Static.buildSnippet({path: searchInput.value})
        } else if (input.attributes.name == 'delete') {
            window.fetch(
                `${window.LiveElement.Scale.Console.IDE.connectionURL}/static/${searchInput.value}`, 
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
window.LiveElement.Live.processors.IdeStaticEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="static"] fieldset[name="edit"]')
    var pathInput = editFieldset.querySelector('input[name="path"]')
    var contentTypeInput = editFieldset.querySelector('input[name="content-type"]')
    if (handlerType == 'trigger') {
        window.LiveElement.Scale.Console.IDE.Static.Edit.div = editFieldset.querySelector('div.editor')
        var datalistContentTypes = document.getElementById('ide--content-type')
        var clearButton = editFieldset.querySelector('button[name="clear"]')
        var saveButton = editFieldset.querySelector('button[name="save"]')
        if (input.attributes.name == 'path') {
            window.LiveElement.Scale.Console.IDE.Static.static = window.LiveElement.Scale.Console.IDE.Static.static || {}
            window.LiveElement.Scale.Console.IDE.Static.static.path = input.properties.value
            window.LiveElement.Scale.Console.IDE.Static.buildSnippet({path: input.properties.value})
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
                window.LiveElement.Scale.Console.IDE.Static.Edit.modelist = window.LiveElement.Scale.Console.IDE.Static.Edit.modelist || window.ace.require("ace/ext/modelist")
                aceMode = window.LiveElement.Scale.Console.IDE.Static.Edit.modelist.getModeForPath(`test.${matchedOption.getAttribute('suffix')}`).mode
            }
            if (!aceMode) {
                aceMode = 'ace/mode/text'
            }
            var contentTypeBase = input.properties.value.split('/')[0]
            if (window.LiveElement.Scale.Console.IDE.Static.editor && window.LiveElement.Scale.Console.IDE.Static.Edit.div.getAttribute('editor') != contentTypeBase) {
                if (typeof window.LiveElement.Scale.Console.IDE.Static.editor.destroy == 'function') {
                    window.LiveElement.Scale.Console.IDE.Static.editor.destroy()
                } else if (typeof window.LiveElement.Scale.Console.IDE.Static.editor.remove == 'function') {
                    window.LiveElement.Scale.Console.IDE.Static.editor.remove()
                }
            }
            if (aceMode != 'ace/mode/text' || contentTypeBase == 'text') {
                window.LiveElement.Scale.Console.IDE.Static.Edit.div.removeAttribute('disabled')
                window.LiveElement.Scale.Console.IDE.Static.editor = window.ace.edit(window.LiveElement.Scale.Console.IDE.Static.Edit.div)
                window.LiveElement.Scale.Console.IDE.Static.editor.setOptions({...window.LiveElement.Scale.Console.aceOptions, ...{minLines: 47, maxLines: 47}})
                window.LiveElement.Scale.Console.IDE.Static.editor.renderer.setScrollMargin(10, 10)
                window.LiveElement.Scale.Console.IDE.Static.editor.session.setMode(aceMode)
                window.LiveElement.Scale.Console.IDE.Static.editor.session.on('change', function() {
                    saveButton.removeAttribute('disabled')
                    window.LiveElement.Scale.Console.IDE.Static.buildSnippet({body: window.btoa(window.LiveElement.Scale.Console.IDE.Static.editor.getValue())})
                })
                window.LiveElement.Scale.Console.IDE.Static.Edit.div.setAttribute('editor', 'text')
                if (window.LiveElement.Scale.Console.IDE.Static.static && window.LiveElement.Scale.Console.IDE.Static.static.file) {
                    window.LiveElement.Scale.Console.IDE.Static.static.file.text().then(t => window.LiveElement.Scale.Console.IDE.Static.editor.setValue(t))
                } else if (window.LiveElement.Scale.Console.IDE.Static.static && window.LiveElement.Scale.Console.IDE.Static.static.dataURL) {
                    window.LiveElement.Scale.Console.IDE.Static.editor.setValue(window.atob(window.LiveElement.Scale.Console.IDE.Static.static.dataURL.split(',', 2)[1]))
                    window.LiveElement.Scale.Console.IDE.Static.buildSnippet({body: window.LiveElement.Scale.Console.IDE.Static.static.dataURL.split(',', 2)[1]})
                }
            } else if (contentTypeBase == 'image') {
                var imgElement
                var appendImgElement = function() {
                    if (window.LiveElement.Scale.Console.IDE.Static.static.objectURL || window.LiveElement.Scale.Console.IDE.Static.static.dataURL) {
                        imgElement = document.createElement('img')
                        if (window.LiveElement.Scale.Console.IDE.Static.static.objectURL) {
                            imgElement.setAttribute('src', window.LiveElement.Scale.Console.IDE.Static.static.objectURL)
                            delete window.LiveElement.Scale.Console.IDE.Static.static.objectURL
                        } else {
                            imgElement.setAttribute('src', window.LiveElement.Scale.Console.IDE.Static.static.dataURL)
                            delete window.LiveElement.Scale.Console.IDE.Static.static.dataURL
                        }
                        window.LiveElement.Scale.Console.IDE.Static.editor.appendChild(imgElement)
                    }
                }
                if (window.LiveElement.Scale.Console.IDE.Static.Edit.div.getAttribute('editor') == 'image') {
                    appendImgElement()
                } else {
                    window.LiveElement.Scale.Console.IDE.Static.Edit.div.removeAttribute('disabled')
                    window.LiveElement.Scale.Console.IDE.Static.editor = document.createElement('element-imageeditor')
                    window.LiveElement.Scale.Console.IDE.Static.Edit.div.appendChild(window.LiveElement.Scale.Console.IDE.Static.editor)
                    window.LiveElement.Scale.Console.IDE.Static.Edit.div.setAttribute('editor', contentTypeBase)
                    appendImgElement()
                    saveButton.removeAttribute('disabled')
                    window.LiveElement.Scale.Console.IDE.Static.buildSnippet({body: `${window.LiveElement.Scale.Console.IDE.Static.editor}`})
                }
                if (window.LiveElement.Scale.Console.IDE.Static.editor) {
                    window.LiveElement.Scale.Console.IDE.Static.editor.contenttype = input.properties.value
                    window.LiveElement.Scale.Console.IDE.Static.buildSnippet({contenttype: input.properties.value})
                }
            } else {
                window.LiveElement.Scale.Console.IDE.Static.Edit.div.setAttribute('disabled', true)
                window.LiveElement.Scale.Console.IDE.Static.Edit.div.removeAttribute('editor')
            }
            saveButton.removeAttribute('disabled')
            window.LiveElement.Scale.Console.IDE.Static.buildSnippet({contenttype: input.properties.value})
        } else if (input.attributes.name == 'upload') {
            window.LiveElement.Scale.Console.IDE.Static.static = window.LiveElement.Scale.Console.IDE.Static.static || {}
            if (input.triggersource.files.length) {
                window.LiveElement.Scale.Console.IDE.Static.static.file = input.triggersource.files[0]
                window.LiveElement.Scale.Console.IDE.Static.static.ContentType = window.LiveElement.Scale.Console.IDE.Static.static.file.type
                window.LiveElement.Scale.Console.IDE.Static.buildSnippet({contenttype: window.LiveElement.Scale.Console.IDE.Static.static.file.type})
                if (window.LiveElement.Scale.Console.IDE.Static.static.path && window.LiveElement.Scale.Console.IDE.Static.static.path.slice(-1) == '/') {
                    window.LiveElement.Scale.Console.IDE.Static.static.path = `${window.LiveElement.Scale.Console.IDE.Static.static.path}${window.LiveElement.Scale.Console.IDE.Static.static.file.name}`
                } else if (!window.LiveElement.Scale.Console.IDE.Static.static.path) {
                    window.LiveElement.Scale.Console.IDE.Static.static.path = window.LiveElement.Scale.Console.IDE.Static.static.file.name
                }
                pathInput.value = window.LiveElement.Scale.Console.IDE.Static.static.path
                contentTypeInput.value = window.LiveElement.Scale.Console.IDE.Static.static.ContentType
                window.LiveElement.Scale.Console.IDE.Static.static.objectURL = URL.createObjectURL(window.LiveElement.Scale.Console.IDE.Static.static.file)
                window.LiveElement.Scale.Console.IDE.Static.buildSnippet({contenttype: contentTypeInput.value, path: pathInput.value})
                contentTypeInput.dispatchEvent(new window.Event('change'))
                editFieldset.querySelector('input[type="file"]').value = ''
            } else {
                clearButton.dispatchEvent(new window.Event('click'))
            }
            saveButton.removeAttribute('disabled')
        } else if (input.attributes.name == 'save') {
            var body = window.LiveElement.Scale.Console.IDE.Static.Edit.div.getAttribute('editor') == 'image' 
                ? `${window.LiveElement.Scale.Console.IDE.Static.editor}` : window.btoa(window.LiveElement.Scale.Console.IDE.Static.editor.getValue())
            var contentType = window.LiveElement.Scale.Console.IDE.Static.Edit.div.getAttribute('editor') == 'image' 
                ? window.LiveElement.Scale.Console.IDE.Static.editor.contenttype : contentTypeInput.value
            window.LiveElement.Scale.Console.IDE.Static.buildSnippet({contenttype: contentType, body: body})
            window.fetch(
                `${window.LiveElement.Scale.Console.IDE.connectionURL}/static/${pathInput.value}`, 
                {method: 'PUT', headers: {"Content-Type": contentType}, body: body}
            ).then(r => {
                saveButton.setAttribute('disabled', true)
            })
        }
    } else if (handlerType == 'subscription') {
        window.LiveElement.Scale.Console.IDE.Static.static = {}
        pathInput.value = input.payload.path || ''
        contentTypeInput.value = input.payload.ContentType || ''
        window.LiveElement.Scale.Console.IDE.Static.buildSnippet({contenttype: input.payload.ContentType, path: input.payload.path})
        pathInput.dispatchEvent(new window.Event('change'))
        window.LiveElement.Scale.Console.System.invokeLambda({
            page: 'ide', entity_type: 'static', heading: 'fetch', path: input.payload.path
        }).then(fetchResult => {
            if (fetchResult && typeof fetchResult == 'object' && fetchResult.result && typeof fetchResult.result == 'object') {
                window.LiveElement.Scale.Console.IDE.Static.static = window.LiveElement.Scale.Console.IDE.Static.static || {}
                window.LiveElement.Scale.Console.IDE.Static.static.dataURL = `data:${input.payload.ContentType};base64,${fetchResult.result.body}`
                contentTypeInput.dispatchEvent(new window.Event('change'))
            }
        })
        if (!pathInput.value) {
            pathInput.focus()
        }
    }
}

window.LiveElement.Live.listeners.IdeStaticSearch = {processor: 'IdeStaticSearch', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="static"] fieldset[name="search"]'), 'IdeStaticSearch', 'loaded', false, true)

window.LiveElement.Scale.Console.buildSnippets('static')
