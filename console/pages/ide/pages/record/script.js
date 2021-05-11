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
        var editor = input.subscriber.querySelector('div.editor')
        editor.innerHTML = ''
        Object.keys(input.payload).sort().forEach(field => {
            var labelElement = document.createElement('label')
            labelElement.innerHTML = field
            var inputElement = document.createElement('input')
            inputElement.value = input.payload[field]
            labelElement.appendChild(inputElement)
            editor.appendChild(labelElement)
        })
    } else if (handlerType == 'trigger') {
        console.log('line 67', input)
    }
}







window.LiveElement.Live.listeners.IdeRecordSearch = {processor: 'IdeRecordSearch', expired: true}

window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="record"] fieldset[name="search"]'), 'IdeRecordSearch', 'loaded', false, true)
