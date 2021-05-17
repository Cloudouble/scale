window.LiveElement.Live.processors.IdeRecordSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return window.LiveElement.Scale.Console.IDE.Record.Edit.record
    } else if (handlerType == 'trigger') {
        var searchFieldset = input.triggersource.closest('fieldset')
        var editFieldset = searchFieldset.nextElementSibling
        var searchTypeInput = searchFieldset.querySelector('input[name="search-type"]')
        var searchUuidInput = searchFieldset.querySelector('input[name="search-uuid"]')
        if (input.attributes.name == 'search-uuid') {
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'record', 
                heading: 'search',
                input_name: input.attributes.name, 
                record_type: searchTypeInput.value, 
                search: input.properties.value
            }).then(searchResult => {
                if (searchResult && typeof searchResult == 'object' && searchResult.result && typeof searchResult.result == 'object') {
                    window.LiveElement.Scale.Console.IDE.Record.Search[input.attributes.name] = searchResult.result
                    var datalist = document.getElementById(`ide-record-${input.attributes.name}-list`)
                    window.LiveElement.Scale.Core.buildDataList(datalist, window.LiveElement.Scale.Console.IDE.Record.Search[input.attributes.name])
                }
            })
            if (window.LiveElement.Scale.Console.IDE.Record.Search.classes 
                    && (searchTypeInput.value in window.LiveElement.Scale.Console.IDE.Record.Search.classes)
                    && window.LiveElement.Scale.Console.IDE.Record.Search['search-uuid'] 
                    && (window.LiveElement.Scale.Console.IDE.Record.Search['search-uuid']).includes(input.properties.value)
                    ) {
                searchFieldset.querySelector('button[name="load"]').removeAttribute('disabled')
            } else {
                searchFieldset.querySelector('button[name="load"]').setAttribute('disabled', true)
            }
            
        } else if (input.attributes.name == 'search-type') {
            if (window.LiveElement.Scale.Console.IDE.Record.Search.classes && (input.properties.value in window.LiveElement.Scale.Console.IDE.Record.Search.classes)) {
                searchFieldset.querySelector('button[name="new"]').removeAttribute('disabled')
            } else {
                searchFieldset.querySelector('button[name="new"]').setAttribute('disabled', true)
            }
        } else if (input.attributes.name == 'load') {
            editFieldset.setAttribute('active', true)
            editFieldset.querySelector('button[name="duplicate"]').removeAttribute('disabled')
            window.LiveElement.Scale.Console.IDE.Record.Edit.record_type = searchTypeInput.value
            window.LiveElement.Scale.Console.IDE.Record.Edit.record_uuid = searchUuidInput.value
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'record', 
                heading: 'search',
                input_name: input.attributes.name,
                record_type: window.LiveElement.Scale.Console.IDE.Record.Edit.record_type, 
                record_uuid: window.LiveElement.Scale.Console.IDE.Record.Edit.record_uuid
            }).then(record => {
                if (record && typeof record == 'object') {
                    window.LiveElement.Scale.Console.IDE.Record.Edit.record = record
                    if (window.LiveElement.Scale.Console.IDE.Record.Edit.record) {
                        searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
                    }
                }
            })
        } else if (input.attributes.name == 'new') {
            editFieldset.setAttribute('active', true)
            searchTypeInput.value = ''
            searchUuidInput.value = ''
            window.LiveElement.Scale.Console.IDE.Record.Edit.record_type = ''
            window.LiveElement.Scale.Console.IDE.Record.Edit.record_uuid = ''
            window.LiveElement.Scale.Console.IDE.Record.Edit.record = {}
            searchFieldset.dispatchEvent(new window.CustomEvent('loaded'))
        }
    }
}

window.LiveElement.Live.processors.IdeRecordEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editor = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="edit"] table.editor tbody')
    var buildRow = function(property) {
        var trElement = document.createElement('tr')
        trElement.setAttribute('name', property)
        var buildCell = function(name, value, colspan, inputType, listId, trigger) {
            var cellTdElement = document.createElement('td')
            var cellInputElement = document.createElement('input')
            var cellSmallElement = document.createElement('small')
            cellSmallElement.innerHTML = '&nbsp;'
            cellTdElement.setAttribute('name', name)
            cellTdElement.setAttribute('colspan', colspan)
            cellInputElement.setAttribute('type', inputType)
            if (listId) {
                cellInputElement.setAttribute('list', listId)
            }
            cellInputElement.setAttribute('live-trigger', trigger)
            cellInputElement.value = value
            if (property == '@id' || property == '@type') {
                cellInputElement.setAttribute('readonly', true)
            }
            cellTdElement.appendChild(cellInputElement)
            cellTdElement.appendChild(cellSmallElement)
            return cellTdElement
        }
        var propertyTdElement = buildCell('property', property, 2, 'search', 'ide-record-edit-properties-list', 'change:IdeRecordEdit')
        trElement.appendChild(propertyTdElement)
        var typeListElementId = window.LiveElement.Scale.Core.generateUUID4()
        var typeTdElement = buildCell('type', '', 1, 'search', typeListElementId, 'change:IdeRecordEdit')
        var typeListElement = document.createElement('datalist')
        typeListElement.setAttribute('name', 'types')
        typeListElement.setAttribute('id', typeListElementId)
        typeTdElement.appendChild(typeListElement)
        trElement.appendChild(typeTdElement)
        var valueTdElement = buildCell('value', input && input.payload ? input.payload[property] || '' : '', 4, 'text', '')
        trElement.appendChild(valueTdElement)
        editor.appendChild(trElement)
    }
    if (handlerType == 'subscription') {
        editor.innerHTML = ''
        Object.keys(input.payload).sort().forEach(property => {
            buildRow(property)
        })
        buildRow('')
        var injectDataTypes = function() {
            var properties = window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type']].properties
            editor.querySelectorAll('tr').forEach(tr => {
                var property = tr.getAttribute('name')
                var types
                var label
                if (property in properties) {
                    types = properties[property].types
                    label = properties[property].label
                } else {
                    types = ['Text']
                    label = '&nbsp;'
                }
                var datalist = tr.querySelector('td[name="type"] datalist[name="types"]')
                window.LiveElement.Scale.Core.buildDataList(datalist, Object.assign({}, ...types.sort().map(type => { 
                    return {[type]: window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[type] 
                        ? window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[type].label 
                        : type}
                })))
                tr.querySelector('td[name="property"] small').innerHTML = label.length > 45 ? `${label.slice(0, 45)}...` : label
                if (types.length == 1) {
                    var typeInputElement = tr.querySelector('td[name="type"] input')
                    typeInputElement.value = types[0]
                    typeInputElement.dispatchEvent(new window.Event('change'))
                }
            })
        }
        var injectProperties = function() {
            var listElement = document.getElementById('ide-record-edit-properties-list')
            if (window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type'] != listElement.getAttribute('class')) {
                listElement.innerHTML = ''
                listElement.setAttribute('class', window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type'])
                var properties = window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type']].properties
                window.LiveElement.Scale.Core.buildDataList(listElement, Object.assign({}, ...Object.keys(properties).sort().map(propertyName => {
                    return {[propertyName]: properties[propertyName].label}
                })))
                if (!window.LiveElement.Scale.Console.IDE.Record.Edit.datatype) {
                    window.LiveElement.Scale.Console.System.invokeLambda({
                        page: 'ide', 
                        entity_type: 'record', 
                        heading: 'edit',
                        datatypes: true
                    }).then(dataTypes => {
                        if (dataTypes && typeof dataTypes == 'object') {
                            window.LiveElement.Scale.Console.IDE.Record.Edit.datatype = dataTypes
                            injectDataTypes()
                        }
                    })
                } else {
                    injectDataTypes()
                }
            }
        }
        window.LiveElement.Scale.Console.IDE.Record.Edit.class = window.LiveElement.Scale.Console.IDE.Record.Edit.class || {}
        if (!window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type']]) {
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'record', 
                heading: 'edit',
                record_type: window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type']
            }).then(classDefinition => {
                if (classDefinition && typeof classDefinition == 'object') {
                    window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type']] = classDefinition
                    injectProperties()
                }
            })
        } else {
            injectProperties()
        }
    } else if (handlerType == 'trigger') {
        var td = input.triggersource.closest('td')
        var name
        if (td) {
            name = td.getAttribute('name')
        } else {
            name = input.triggersource.name
        }
        if (name == 'property') {
            var trElement = input.triggersource.closest('tr')
            trElement.setAttribute('name', input.properties.value)
            
            if (!Array.from(editor.querySelectorAll('tr[name]')).filter(tr => !tr.getAttribute('name')).length) {
                console.log('line 231', input)
                buildRow('')
            }
            
            var typeTdElement = td.nextElementSibling
            var typeInputElement = typeTdElement.querySelector('input')
            var typeSmallElement = typeTdElement.querySelector('small')
            typeSmallElement.innerHTML = '&nbsp;'
            var listElement = typeTdElement.querySelector('datalist')
            listElement.innerHTML = ''
            if (window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type'] in window.LiveElement.Scale.Console.IDE.Record.Edit.class) {
                var classDefinition = window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type']]
                if (classDefinition.properties && (input.properties.value in classDefinition.properties)) {
                    var propertyDefinition = classDefinition.properties[input.properties.value]
                    td.querySelector('small').innerHTML = propertyDefinition.label.length > 45 ? `${propertyDefinition.label.slice(0, 45)}...` : propertyDefinition.label
                    if ('types' in propertyDefinition) {
                        window.LiveElement.Scale.Core.buildDataList(listElement, Object.assign({}, ...propertyDefinition.types.sort().map(type => { 
                            return {[type]:  window.LiveElement.Scale.Console.IDE.Record.Edit.datatype && type in window.LiveElement.Scale.Console.IDE.Record.Edit.datatype 
                                ? window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[type].label 
                                : (window.LiveElement.Scale.Console.IDE.Record.Search.classes && type in window.LiveElement.Scale.Console.IDE.Record.Search.classes ? window.LiveElement.Scale.Console.IDE.Record.Search.classes[type].label : type) }
                        })))
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
        } else if (name == 'type') {
            var ll
            if (input.properties.value in window.LiveElement.Scale.Console.IDE.Record.Edit.datatype) {
                ll = window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[input.properties.value].label
            } else if (input.properties.value in window.LiveElement.Scale.Console.IDE.Record.Search.classes) {
                ll = window.LiveElement.Scale.Console.IDE.Record.Search.classes[input.properties.value].label
            }
            if (ll) {
                td.querySelector('small').innerHTML = ll.length > 45 ? `${ll.slice(0, 45)}...` : ll
            }
            var trElement = td.closest('tr')
            var propertyName = trElement.getAttribute('name')
            var valueTdElement = td.nextElementSibling
            var valueInputElement = valueTdElement.querySelector('input')
            var valueSmallElement = valueTdElement.querySelector('small')
            var valueDatalistElement = valueTdElement.querySelector('datalist')
            if (valueDatalistElement) {
                valueDatalistElement.remove()
            }
            ;(['checked', 'readonly', 'step', 'live-trigger', 'list']).forEach(a => {
                valueInputElement.removeAttribute(a)
            })
            valueSmallElement.innerHTML = '&nbsp;'
            switch(input.properties.value) {
                case 'Boolean':
                case 'True':
                case 'False':
                    valueInputElement.setAttribute('type', 'checkbox')
                    if (valueInputElement.value || input.properties.value === 'True') {
                        valueInputElement.setAttribute('checked', 'true')
                    }
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
                    valueSmallElement.innerHTML = `Specify the ${input.properties.value} value`
                    break
                case 'Number':
                case 'Float':
                case 'Integer':
                    valueInputElement.setAttribute('type', 'number')
                    if (input.properties.value === 'Integer') {
                        valueInputElement.setAttribute('step', 1)
                    }
                    valueSmallElement.innerHTML = `Specify the ${input.properties.value} value`
                    break
                case 'URL':
                    valueInputElement.setAttribute('type', 'url')
                    valueSmallElement.innerHTML = `Requires a valid URL`
                    break
                case 'Text':
                case 'CssSelectorType':
                case 'PronounceableText':
                case 'XPathType':
                    valueInputElement.setAttribute('type', 'text')
                    valueSmallElement.innerHTML = propertyName == '@id' || propertyName == '@type' ? `The ${propertyName} of the record` : 'Any text value'
                    break
                default:
                    valueInputElement.setAttribute('type', 'search')
                    if (input.properties.value) {
                        var valueDatalistElement = document.createElement('datalist')
                        var datalistId = window.LiveElement.Scale.Core.generateUUID4()
                        valueDatalistElement.setAttribute('id', datalistId)
                        valueInputElement.setAttribute('list', datalistId)
                        valueInputElement.setAttribute('pattern', '[a-z0-9]{8}-[a-z0-9]{4}-4[a-z0-9]{3}-[89ab][a-z0-9]{3}-[a-z0-9]{12}')
                        valueSmallElement.innerHTML = `Requires a valid UUID of a linked record of the type ${input.properties.value}`
                        valueInputElement.setAttribute('live-trigger', 'keyup:IdeRecordEdit')
                        valueTdElement.appendChild(valueDatalistElement)
                    }
            }
            if (propertyName == '@id' || propertyName == '@type') {
                valueInputElement.setAttribute('readonly', 'true')
            }
        } else if (name == 'value') {
            var tr = td.closest('tr')
            var typeInputElement = tr.querySelector('td[name="type"] input')
            if (typeInputElement.value) {
                window.LiveElement.Scale.Console.System.invokeLambda({
                    page: 'ide', 
                    entity_type: 'record', 
                    heading: 'search',
                    input_name: 'search-uuid', 
                    record_type: typeInputElement.value, 
                    search: input.properties.value
                }).then(searchResult => {
                    if (searchResult && typeof searchResult == 'object' && searchResult.result && typeof searchResult.result == 'object') {
                        window.LiveElement.Scale.Console.IDE.Record.Search[input.attributes.name] = searchResult.result
                        var datalist = td.querySelector('datalist')
                        window.LiveElement.Scale.Core.buildDataList(datalist, searchResult.result)
                    }
                })
            }
        } else if (name == 'save') {
            
            
        } else if (name == 'duplicate') {
            var searchFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="search"]')
            var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="edit"]')
            searchFieldset.querySelector('input[name="search-uuid"]').value = ''
            window.LiveElement.Scale.Console.IDE.Record.Edit.record_uuid = window.LiveElement.Scale.Core.generateUUID4()
            window.LiveElement.Scale.Console.IDE.Record.Edit.record['@id'] = window.LiveElement.Scale.Console.IDE.Record.Edit.record_uuid
            editFieldset.querySelector('tr[name="@id"] td[name="value"] input').value = window.LiveElement.Scale.Console.IDE.Record.Edit.record['@id']
        } else if (name == 'delete') {
            
        }
    }
}


window.LiveElement.Live.listeners.IdeRecordSearch = {processor: 'IdeRecordSearch', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="search"]'), 'IdeRecordSearch', 'loaded', false, true)

window.LiveElement.Scale.Console.System.invokeLambda({
    page: 'ide', 
    entity_type: 'record', 
    heading: 'search',
    classes: true
}).then(classes => {
    if (classes && typeof classes == 'object') {
        window.LiveElement.Scale.Console.IDE.Record.Search.classes = classes
        var classList = document.getElementById('ide-record-search-type-list')
        window.LiveElement.Scale.Core.buildDataList(classList, Object.assign({}, ...Object.keys(classes).sort().map(className => {
            return {[className]: `${classes[className].label} [${classes[className].parents.join('&rarr;')}]`}
        })))
    }
})

