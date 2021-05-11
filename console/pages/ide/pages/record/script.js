window.LiveElement.Live.processors.IdeRecordSearch = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    if (handlerType == 'listener') {
        return window.LiveElement.Scale.Console.IDE.Record.Edit.record
    } else if (handlerType == 'trigger') {
        var searchFieldset = input.triggersource.closest('fieldset')
        var searchTypeInput = searchFieldset.querySelector('input[name="search-type"]')
        var searchUuidInput = searchFieldset.querySelector('input[name="search-uuid"]')
        if ((input.attributes.name == 'search-type') || (input.attributes.name == 'search-uuid')) {
            var event = input.vector.split(':').shift()
            if (event == 'keyup') {
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
                        datalist.innerHTML = ''
                        window.LiveElement.Scale.Console.IDE.Record.Search[input.attributes.name].sort().forEach(k => {
                            var optionElement = document.createElement('option')
                            optionElement.setAttribute('value', k)
                            optionElement.innerHTML = k
                            datalist.appendChild(optionElement)
                        })
                    }
                })
            }
        } else if (input.attributes.name == 'load') {
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
    if (handlerType == 'subscription') {
        var editor = input.subscriber.querySelector('table.editor tbody')
        editor.innerHTML = ''
        Object.keys(input.payload).sort().forEach(property => {
            var trElement = document.createElement('tr')
            trElement.setAttribute('name', property)

            var propertyTdElement = document.createElement('td')
            var propertyInputElement = document.createElement('input')
            var propertySmallElement = document.createElement('small')
            propertySmallElement.innerHTML = '&nbsp;'
            propertyTdElement.setAttribute('name', 'property')
            propertyTdElement.setAttribute('colspan', '2')
            propertyInputElement.setAttribute('type', 'search')
            propertyInputElement.setAttribute('list', 'ide-record-edit-properties-list')
            propertyInputElement.value = property
            if (property == '@id' || property == '@type') {
                propertyInputElement.setAttribute('readonly', true)
            }
            propertyTdElement.appendChild(propertyInputElement)
            propertyTdElement.appendChild(propertySmallElement)
            trElement.appendChild(propertyTdElement)
            
            var typeTdElement = document.createElement('td')
            typeTdElement.setAttribute('name', 'type')
            typeTdElement.setAttribute('colspan', '1')
            var listElementId = window.LiveElement.Scale.Core.generateUUID4()
            var listElement = document.createElement('datalist')
            listElement.setAttribute('name', 'types')
            listElement.setAttribute('id', listElementId)
            typeTdElement.appendChild(listElement)
            var typeInputElement = document.createElement('input')
            var typeSmallElement = document.createElement('small')
            typeSmallElement.innerHTML = '&nbsp;'
            typeInputElement.setAttribute('list', listElementId)
            if (property == '@id' || property == '@type') {
                typeInputElement.setAttribute('readonly', true)
            }
            typeTdElement.appendChild(typeInputElement)
            typeTdElement.appendChild(typeSmallElement)
            trElement.appendChild(typeTdElement)

            var valueTdElement = document.createElement('td')
            var valueInputElement = document.createElement('input')
            var valueSmallElement = document.createElement('small')
            valueSmallElement.innerHTML = '&nbsp;'
            valueTdElement.setAttribute('name', 'value')
            valueTdElement.setAttribute('colspan', '4')
            valueInputElement.value = input.payload[property]
            if (property == '@id' || property == '@type') {
                valueInputElement.setAttribute('readonly', true)
            }
            valueTdElement.appendChild(valueInputElement)
            valueTdElement.appendChild(valueSmallElement)
            trElement.appendChild(valueTdElement)
            
            editor.appendChild(trElement)
        })
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
                var datalist = tr.querySelector('datalist[name="types"]')
                datalist.innerHTML = ''
                types.sort().forEach(type => {
                    var option = document.createElement('option')
                    option.setAttribute('value', type)
                    option.innerHTML = window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[type] 
                        ? window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[type].label 
                        : type
                    datalist.appendChild(option)
                })
                tr.querySelector('td[name="property"] small').innerHTML = label
                if (types.length == 1) {
                    tr.querySelector('td[name="type"] input').value = types[0]
                    tr.querySelector('td[name="type"] small').innerHTML = window.LiveElement.Scale.Console.IDE.Record.Edit.datatype[types[0]].label
                }
            })
        }
        var injectProperties = function() {
            var listElement = document.getElementById('ide-record-edit-properties-list')
            if (window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type'] != listElement.getAttribute('class')) {
                listElement.innerHTML = ''
                listElement.setAttribute('class', window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type'])
                var properties = window.LiveElement.Scale.Console.IDE.Record.Edit.class[window.LiveElement.Scale.Console.IDE.Record.Edit.record['@type']].properties
                Object.keys(properties).sort().forEach(property_name => {
                    var optionElement = document.createElement('option')
                    optionElement.setAttribute('value', property_name)
                    optionElement.innerHTML = properties[property_name].label
                    listElement.appendChild(optionElement)
                })
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
        console.log('line 67', input)
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
        console.log('line 221', classes)
        window.LiveElement.Scale.Console.IDE.Record.Search.classes = classes
        var classList = document.getElementById('ide-record-search-type-list')
        classList.innerHTML = ''
        Object.keys(classes).forEach(className => {
            var optionElement = document.createElement('option')
            optionElement.setAttribute('value', className)
            optionElement.innerHTML = `${classes[className].label} [${classes[className].parents.join('&rarr;')}]`
            classList.appendChild(optionElement)
        })
    }
})
