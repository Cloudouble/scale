window.LiveElement.Live.processors.IdeRecordSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return (input.detail || {}).entity || {}
    }
}

window.LiveElement.Live.processors.IdeRecordEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editor = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="edit"] table.editor tbody')
    //var searchFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="search"]')
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="edit"]')
    var buildRow = function(property) {
        var trElement = document.createElement('tr')
        trElement.setAttribute('name', property)
        var buildCell = function(name, value, colspan, inputType, listId, trigger, record) {
            var cellTdElement = document.createElement('td'), cellInputElement = document.createElement('input'),  cellSmallElement = document.createElement('small')
            cellSmallElement.innerHTML = '&nbsp;'
            cellTdElement.setAttribute('name', name)
            cellTdElement.setAttribute('colspan', colspan)
            cellInputElement.setAttribute('type', inputType)
            if (listId) {
                cellInputElement.setAttribute('list', listId)
            }
            cellInputElement.setAttribute('live-trigger', trigger)
            if (record && property in record && record[property] && typeof record[property] == 'object') {
                if (name == 'type') {
                    cellInputElement.value = record[property]['@type'] || value
                } else if (name == 'value') {
                    cellInputElement.value = record[property]['@id'] || ''
                } else {
                    cellInputElement.value = value
                }
            } else {
                cellInputElement.value = value
            }
            if (property == '@id' || property == '@type') {
                cellInputElement.setAttribute('readonly', true)
            }
            cellTdElement.appendChild(cellInputElement)
            cellTdElement.appendChild(cellSmallElement)
            return cellTdElement
        }
        trElement.appendChild(buildCell('property', property, 2, 'search', 'ide-record-edit-properties-list', 'input:IdeRecordEdit change:IdeRecordEdit', input.payload))
        var typeListElementId = window.LiveElement.Scale.Core.generateUUID4(), typeListElement = document.createElement('datalist')
        var typeTdElement = buildCell('type', '', 1, 'search', typeListElementId, 'input:IdeRecordEdit change:IdeRecordEdit', input.payload)
        typeListElement.setAttribute('name', 'types')
        typeListElement.setAttribute('id', typeListElementId)
        typeTdElement.appendChild(typeListElement)
        trElement.appendChild(typeTdElement)
        var valueTdElement = buildCell('value', input && input.payload ? input.payload[property] || '' : '', 4, 'text', '', 'input:IdeRecordEdit change:IdeRecordEdit', input.payload)
        valueTdElement.querySelector('input').setAttribute('required', true)
        trElement.appendChild(valueTdElement)
        editor.appendChild(trElement)
    }
    if (handlerType == 'subscription') {
        console.log('line 61', input)
        editor.innerHTML = ''
        Object.keys(input.payload).sort().forEach(property => {
            buildRow(property)
        })
        buildRow('')
        var injectDataTypes = function() {
            var properties = window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.record['@type']].properties
            editor.querySelectorAll('tr').forEach(tr => {
                var property = tr.getAttribute('name'), types, label
                if (property in properties) {
                    types = properties[property].types
                    label = properties[property].label
                } else {
                    types = ['Text']
                    label = '&nbsp;'
                }
                window.LiveElement.Scale.Core.buildDataList(tr.querySelector('td[name="type"] datalist[name="types"]'), Object.assign({}, ...types.sort().map(type => { 
                    return {[type]: window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[type] 
                        ? window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[type].label 
                        : type}
                })))
                tr.querySelector('td[name="property"] small').innerHTML = window.LiveElement.Scale.Core.truncateLabel(label, 45)
                if (types.length == 1 && tr.querySelector('td[name="property"] input') && tr.querySelector('td[name="property"] input').value) {
                    var typeInputElement = tr.querySelector('td[name="type"] input')
                    typeInputElement.value = typeInputElement.value || types[0]
                    typeof window.requestIdleCallback == 'function' ? window.requestIdleCallback(function() {
                        typeInputElement.dispatchEvent(new window.Event('input'))
                    }, {timeout: 1000}) : window.setTimeout(function() {
                        typeInputElement.dispatchEvent(new window.Event('input'))
                    }, 1000)
                }
            })
        }
        var injectProperties = function() {
            var listElement = document.getElementById('ide-record-edit-properties-list')
            if (window.LiveElement.Scale.Console.IDE.Record.record['@type'] != listElement.getAttribute('class')) {
                listElement.innerHTML = ''
                listElement.setAttribute('class', window.LiveElement.Scale.Console.IDE.Record.record['@type'])
                var properties = window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.record['@type']].properties
                window.LiveElement.Scale.Core.buildDataList(listElement, Object.assign({}, ...Object.keys(properties).sort().map(propertyName => {
                    return {[propertyName]: properties[propertyName].label}
                })))
                if (!window.LiveElement.Scale.Console.IDE.Record.Edit.datatype) {
                    return window.LiveElement.Scale.Console.System.invokeLambda({
                        page: 'ide', 
                        entity_type: 'record', 
                        heading: 'edit',
                        datatypes: true
                    }).then(dataTypes => {
                        if (dataTypes && typeof dataTypes == 'object') {
                            window.LiveElement.Scale.Console.IDE.Record.Edit.datatype = dataTypes
                            return Promise.resolve(injectDataTypes())
                        }
                    })
                } else {
                    return Promise.resolve(injectDataTypes())
                }
            } else {
                return Promise.resolve(injectDataTypes())
            }
        }
        window.LiveElement.Scale.Console.IDE.Record.Edit.class = window.LiveElement.Scale.Console.IDE.Record.Edit.class || {}
        if (!window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.record['@type']]) {
            editFieldset.setAttribute('disabled', true)
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'record', 
                heading: 'edit',
                record_type: window.LiveElement.Scale.Console.IDE.Record.record['@type']
            }).then(classDefinition => {
                if (classDefinition && typeof classDefinition == 'object') {
                    window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.record['@type']] = classDefinition
                    injectProperties().then(() => {
                        editFieldset.removeAttribute('disabled')
                        editFieldset.querySelector('button[name="save"]').setAttribute('disabled', true)
                    })
                }
            })
        } else {
            editFieldset.setAttribute('disabled', true)
            injectProperties().then(() => {
                editFieldset.removeAttribute('disabled')
                editFieldset.querySelector('button[name="save"]').setAttribute('disabled', true)
            })
        }
        editFieldset.querySelector('button[name="duplicate"]').removeAttribute('disabled')
        editFieldset.querySelector('button[name="delete"]').removeAttribute('disabled')
        editFieldset.querySelector('button[name="save"]').setAttribute('disabled', true)
    } else if (handlerType == 'trigger') {
        var eventName = input.vector.split(':').shift()
        if (eventName == 'loaded') {
            var record = input.entity
            editFieldset.setAttribute('active', true)
            
        }
    }
}
        
        

        /*
        var td = input.triggersource.closest('td')
        var trElement = input.triggersource.closest('tr')
        var propertyName = trElement ? trElement.getAttribute('name') : undefined
        var name
        if (td) {
            name = td.getAttribute('name')
        } else {
            name = input.triggersource.name
        }
        if (name == 'property') {
            editFieldset.querySelector('button[name="save"]').removeAttribute('disabled')
            trElement.setAttribute('name', input.properties.value)
            var blankRows = Array.from(editor.querySelectorAll('tr[name]')).filter(tr => !tr.getAttribute('name'))
            blankRows.forEach(blankRow => {
                try {
                    blankRow.remove()
                } catch(e) {
                    //do nothing
                }
            })
            window.LiveElement.Scale.Console.IDE.Record.record = window.LiveElement.Scale.Console.IDE.cleanEditorEntity(editor, window.LiveElement.Scale.Console.IDE.Record, 'record')
            window.LiveElement.Scale.Console.buildSnippets('record')
            blankRows = Array.from(editor.querySelectorAll('tr[name]')).filter(tr => !tr.getAttribute('name'))
            if (!blankRows.length) {
                buildRow('')
            }
            var typeTdElement = td.nextElementSibling, typeInputElement = typeTdElement.querySelector('input'), typeSmallElement = typeTdElement.querySelector('small')
            typeSmallElement.innerHTML = '&nbsp;'
            var listElement = typeTdElement.querySelector('datalist')
            listElement.innerHTML = ''
            if (input.properties.value) {
                if (window.LiveElement.Scale.Console.IDE.Record.record['@type'] in window.LiveElement.Scale.Console.IDE.Record.Edit.class) {
                    var classDefinition = window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.record['@type']]
                    if (classDefinition.properties && (input.properties.value in classDefinition.properties)) {
                        var propertyDefinition = classDefinition.properties[input.properties.value]
                        td.querySelector('small').innerHTML = window.LiveElement.Scale.Core.truncateLabel(propertyDefinition.label, 45)
                        if ('types' in propertyDefinition) {
                            var childrenSet = new window.Set()
                            var optionsMap = Object.assign({}, ...propertyDefinition.types.sort().map(type => {
                                if (window.LiveElement.Scale.Console.IDE.Record.Edit.datatype && type in window.LiveElement.Scale.Console.IDE.Record.Edit.datatype) {
                                    return {[type]: window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[type].label}
                                } else if (type in window.LiveElement.Scale.Console.IDE.classes) {
                                    if (window.LiveElement.Scale.Console.IDE.classes[type].children) {
                                        window.LiveElement.Scale.Console.IDE.classes[type].children.forEach(childClass => {
                                            childrenSet.add(childClass)
                                        })
                                    }
                                    return {[type]: window.LiveElement.Scale.Console.IDE.classes[type].label}
                                } else {
                                    return {[type]: type}
                                }
                            }))
                            childrenSet.forEach(childClass => {
                                if (window.LiveElement.Scale.Console.IDE.classes[childClass] && !optionsMap[childClass]) {
                                    optionsMap[childClass] = window.LiveElement.Scale.Console.IDE.classes[childClass].label
                                }
                            })
                            window.LiveElement.Scale.Core.buildDataList(listElement, optionsMap)
                        }
                        if (propertyDefinition.types.length == 1) {
                            typeInputElement.value = propertyDefinition.types[0]
                        } else {
                            typeInputElement.value = ''
                            typeInputElement.focus()
                        }
                        typeInputElement.dispatchEvent(new window.Event('change'))
                    }
                }
            } else {
                td.querySelector('small').innerHTML = '&nbsp;'
                typeInputElement.value = ''
                typeInputElement.dispatchEvent(new window.Event('change'))
            }
        } else if (name == 'type') {
            editFieldset.querySelector('button[name="save"]').removeAttribute('disabled')
            var datatypeLabel
            if (input.properties.value in window.LiveElement.Scale.Console.IDE.Record.Edit.datatype) {
                datatypeLabel = window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[input.properties.value].label
            } else if (input.properties.value in window.LiveElement.Scale.Console.IDE.classes) {
                datatypeLabel = window.LiveElement.Scale.Console.IDE.classes[input.properties.value].label
            }
            if (datatypeLabel) {
                td.querySelector('small').innerHTML = window.LiveElement.Scale.Core.truncateLabel(datatypeLabel, 45)
            }
            var valueTdElement = td.nextElementSibling
            var valueInputElement = valueTdElement.querySelector('input'), valueSmallElement = valueTdElement.querySelector('small'), valueDatalistElement = valueTdElement.querySelector('datalist')
            if (valueDatalistElement) {
                valueDatalistElement.remove()
            }
            (['checked', 'readonly', 'step', 'live-trigger', 'live-triggersource', 'list', 'pattern', 'required']).forEach(a => {
                valueInputElement.removeAttribute(a)
            })
            valueLoadButton = valueTdElement.querySelector('button')
            if (valueLoadButton) {
                valueLoadButton.remove()
            }
            valueSmallElement.innerHTML = '&nbsp;'
            switch(input.properties.value) {
                case 'Boolean':
                case 'True':
                case 'False':
                    valueInputElement.setAttribute('type', 'checkbox')
                    if (valueInputElement.value || input.properties.value === 'True') {
                        valueInputElement.setAttribute('checked', 'true')
                    }
                    valueInputElement.setAttribute('live-trigger', 'input:IdeRecordEdit change:IdeRecordEdit')
                    if (input.properties.value !== 'Boolean') {
                        valueInputElement.setAttribute('readonly', true)
                        valueSmallElement.innerHTML = `Requires a ${input.properties.value} value`
                    } else {
                        valueSmallElement.innerHTML = `Requires a True (checked box) or False (unchecked box) value`
                    }
                    break
                case 'Date':
                case 'DateTime':
                case 'Time':
                    var inputTypeAttribute = input.properties.value.toLowerCase()
                    inputTypeAttribute = inputTypeAttribute == 'datetime' ? `${inputTypeAttribute}-local` : inputTypeAttribute
                    valueInputElement.setAttribute('type', inputTypeAttribute)
                    valueInputElement.setAttribute('required', true)
                    valueInputElement.setAttribute('live-trigger', 'input:IdeRecordEdit change:IdeRecordEdit')
                    valueSmallElement.innerHTML = `Specify the ${input.properties.value} value`
                    break
                case 'Number':
                case 'Float':
                case 'Integer':
                    valueInputElement.setAttribute('type', 'number')
                    if (input.properties.value === 'Integer') {
                        valueInputElement.setAttribute('step', 1)
                    }
                    valueInputElement.setAttribute('required', true)
                    valueInputElement.setAttribute('live-trigger', 'input:IdeRecordEdit change:IdeRecordEdit')
                    valueSmallElement.innerHTML = `Specify the ${input.properties.value} value`
                    break
                case 'URL':
                    valueInputElement.setAttribute('type', 'url')
                    valueInputElement.setAttribute('required', true)
                    valueInputElement.setAttribute('live-trigger', 'input:IdeRecordEdit change:IdeRecordEdit')
                    valueSmallElement.innerHTML = `Requires a valid URL`
                    break
                case 'Text':
                case 'CssSelectorType':
                case 'PronounceableText':
                case 'XPathType':
                    valueInputElement.setAttribute('type', 'text')
                    valueInputElement.setAttribute('required', true)
                    valueInputElement.setAttribute('live-trigger', 'input:IdeRecordEdit change:IdeRecordEdit')
                    valueSmallElement.innerHTML = propertyName == '@id' || propertyName == '@type' ? `The ${propertyName} of the record` : 'Any text value'
                    break
                default:
                    if (input.properties.value) {
                        valueInputElement.setAttribute('type', 'search')
                        var newValueDatalistElement = document.createElement('datalist')
                        var datalistId = window.LiveElement.Scale.Core.generateUUID4()
                        newValueDatalistElement.setAttribute('id', datalistId)
                        valueInputElement.setAttribute('list', datalistId)
                        valueInputElement.setAttribute('required', true)
                        valueInputElement.setAttribute('pattern', '(^---new---$)|(^[a-z0-9]{8}-[a-z0-9]{4}-4[a-z0-9]{3}-[89ab][a-z0-9]{3}-[a-z0-9]{12}$)')
                        valueInputElement.setAttribute('live-trigger', 'focus:IdeRecordEdit input:IdeRecordEdit search:IdeRecordEdit')
                        valueSmallElement.innerHTML = `Requires a UUID of a linked record of this type or '---new---'`
                        valueTdElement.appendChild(newValueDatalistElement)
                        var valueLoadButton = document.createElement('button')
                        valueLoadButton.setAttribute('name', 'load')
                        valueLoadButton.setAttribute('live-trigger', 'click:IdeRecordEdit')
                        valueLoadButton.innerHTML = 'Load'
                        valueTdElement.appendChild(valueLoadButton)
                    } else {
                        valueInputElement.setAttribute('type', 'text')
                        valueInputElement.value = ''
                        valueInputElement.dispatchEvent(new window.Event('input'))
                    }
            }
            if (propertyName == '@id' || propertyName == '@type') {
                valueInputElement.setAttribute('readonly', 'true')
            }
            valueInputElement.dispatchEvent(new window.Event('input'))
        } else if (name == 'value') {
            if (input.triggersource.tagName.toLowerCase() == 'button') {
                //var searchTypeInput = searchFieldset.querySelector('input[name="search-type"]'), searchUuidInput = searchFieldset.querySelector('input[name="search-uuid"]')
                //var searchLoadButton = searchFieldset.querySelector('button[name="load"]')
                searchTypeInput.focus()
                searchTypeInput.value = trElement.querySelector('td[name="type"] input').value
                searchTypeInput.dispatchEvent(new window.Event('search'))
                searchUuidInput.focus()
                searchUuidInput.value = trElement.querySelector('td[name="value"] input').value
                searchUuidInput.dispatchEvent(new window.Event('search'))
                searchLoadButton.removeAttribute('disabled')
                searchLoadButton.focus()
                searchLoadButton.click()
            } else {
                editFieldset.querySelector('button[name="save"]').removeAttribute('disabled')
                var propertyTypeInputElement = trElement.querySelector('td[name="type"] input')
                var propertyType = propertyTypeInputElement.value
                if (propertyName && propertyType && input.attributes.type == 'search' && input.attributes.list) {
                    var blankOptions = {[window.LiveElement.Scale.Console.IDE.newFlag]: 'Generate UUID for a new record...'}
                    var datalist = td.querySelector('datalist')
                    if (propertyType) {
                        if (input.properties.value == window.LiveElement.Scale.Console.IDE.newFlag) {
                            input.triggersource.value = window.LiveElement.Scale.Core.generateUUID4()
                            input.triggersource.dispatchEvent(new window.Event('search'))
                        } else {
                            window.LiveElement.Scale.Console.System.invokeLambda({
                                page: 'ide', 
                                entity_type: 'record', 
                                heading: 'search',
                                input_name: 'search-uuid', 
                                record_type: propertyType, 
                                search: input.properties.value
                            }).then(searchResult => {
                                if (searchResult && typeof searchResult == 'object' && searchResult.result && typeof searchResult.result == 'object') {
                                    window.LiveElement.Scale.Console.IDE.Record.Search[input.attributes.name] = searchResult.result
                                    window.LiveElement.Scale.Core.buildDataList(datalist, searchResult.result, blankOptions)
                                }
                            })
                        }
                    }
                    if (input.properties.value && input.properties.value != window.LiveElement.Scale.Console.IDE.newFlag && input.triggersource.reportValidity()) {
                        window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = {'@type': propertyType, '@id': input.properties.value}
                        window.LiveElement.Scale.Console.buildSnippets('record')
                    }
                } else {
                    if (propertyName && propertyType && input.triggersource.reportValidity()) {
                        switch(propertyType) {
                            case 'Boolean':
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = input.triggersource.checked
                            break
                            case 'True':
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = true
                            break
                            case 'False':
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = false
                            break
                            case 'Date':
                            case 'DateTime':
                            case 'Time':
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = input.properties.value
                            break
                            case 'Number':
                                let floatVal = parseFloat(input.properties.value), intVal = parseInt(input.properties.value, 10)
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = floatVal == intVal ? intVal : floatVal
                            break
                            case 'Float':
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = parseFloat(input.properties.value)
                            break
                            case 'Integer':
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = parseInt(input.properties.value, 10)
                            break
                            case 'URL':
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = input.properties.value
                            break
                            case 'Text':
                            case 'CssSelectorType':
                            case 'PronounceableText':
                            case 'XPathType':
                                window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = input.properties.value
                            break
                            default:
                                try {
                                    window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = JSON.parse(input.properties.value)
                                } catch(e) {
                                    window.LiveElement.Scale.Console.IDE.Record.record[propertyName] = input.properties.value
                                }
                        }
                        window.LiveElement.Scale.Console.buildSnippets('record')
                    }
                }
            }
        } else if (name == 'save') {
            window.LiveElement.Scale.Console.IDE.Record.record = window.LiveElement.Scale.Console.IDE.cleanEditorEntity(editor, window.LiveElement.Scale.Console.IDE.Record, 'record')
            editFieldset.setAttribute('disabled', true)
            window.fetch(
                `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/record/${window.LiveElement.Scale.Console.IDE.Record.record['@type']}/${window.LiveElement.Scale.Console.IDE.Record.record['@id']}.json`, 
                {
                    method: 'PUT', 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify(window.LiveElement.Scale.Console.IDE.Record.record)
                }
            ).then(() => {
                editFieldset.removeAttribute('disabled')
                editFieldset.querySelector('button[name="save"]').setAttribute('disabled', true)
            }).catch(() => {
                editFieldset.removeAttribute('disabled')
                editFieldset.querySelector('button[name="save"]').setAttribute('disabled', true)
            })
            window.LiveElement.Scale.Console.buildSnippets('record')
        } else if (name == 'duplicate') {
            editFieldset.querySelector('button[name="save"]').removeAttribute('disabled')
            //searchFieldset.querySelector('input[name="search-uuid"]').value = ''
            window.LiveElement.Scale.Console.IDE.Record.record_uuid = window.LiveElement.Scale.Core.generateUUID4()
            window.LiveElement.Scale.Console.IDE.Record.record['@id'] = window.LiveElement.Scale.Console.IDE.Record.record_uuid
            editFieldset.querySelector('tr[name="@id"] td[name="value"] input').value = window.LiveElement.Scale.Console.IDE.Record.record['@id']
            window.LiveElement.Scale.Console.IDE.writeHistory('record', 
                window.LiveElement.Scale.Console.IDE.Record.record['@type'], window.LiveElement.Scale.Console.IDE.Record.record['@id'], 
                window.LiveElement.Scale.Console.IDE.Record.record, 'click:IdeRecordSearch', searchFieldset)
            window.LiveElement.Scale.Console.buildSnippets('record')
        } else if (name == 'delete') {
            editFieldset.querySelector('button[name="save"]').removeAttribute('disabled')
            window.fetch(
                `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}/connection/${window.localStorage.getItem('system:connection_id')}/record/${window.LiveElement.Scale.Console.IDE.Record.record['@type']}/${window.LiveElement.Scale.Console.IDE.Record.record['@id']}.json`, 
                {
                    method: 'DELETE'
                }
            ).then(() => {
                editor.querySelectorAll('tr[name]').forEach(tr => {
                    var trName = tr.getAttribute('name')
                    if (trName && trName != '@id' && trName != '@type') {
                        tr.remove()
                        if (window.LiveElement.Scale.Console.IDE.Record.record[trName]) {
                            delete window.LiveElement.Scale.Console.IDE.Record.record[trName]
                        }
                    }
                })
                editFieldset.removeAttribute('disabled')
                editFieldset.querySelector('button[name="save"]').removeAttribute('disabled')
                window.LiveElement.Scale.Console.IDE.Record.record = window.LiveElement.Scale.Console.IDE.cleanEditorEntity(editor, window.LiveElement.Scale.Console.IDE.Record, 'record')
                window.LiveElement.Scale.Console.buildSnippets('record')
            }).catch(() => {
                editFieldset.removeAttribute('disabled')
                editFieldset.querySelector('button[name="save"]').setAttribute('disabled', true)
            })
            
        }*/
    //}
//}


//window.LiveElement.Live.listeners.IdeRecordSearch = {processor: 'IdeRecordSearch', expired: true}

//window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] element-entitysearch'), 'IdeRecordSearch', 'loaded', false, true)