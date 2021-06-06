window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="feed"] element-entitysearch')
if (window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement) {
    window.LiveElement.Scale.Console.IDE.Feed.connectionSearchInputElement = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySelector('input[name="connection"]')
    window.LiveElement.Scale.Console.IDE.Feed.classSearchInputElement = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySelector('input[name="class"]')
    window.LiveElement.Scale.Console.IDE.Feed.querySearchInputElement = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySelector('input[name="query"]')
    window.LiveElement.Scale.Console.IDE.Feed.feedSearchInputElement = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySelector('input[name="@id"]')
    window.LiveElement.Scale.Console.IDE.Feed.connectionSearchDatalistElement = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySelector(`datalist[id="${window.LiveElement.Scale.Console.IDE.Feed.connectionSearchInputElement.getAttribute('list')}"]`)
    window.LiveElement.Scale.Console.IDE.Feed.classSearchDatalistElement = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySelector(`datalist[id="${window.LiveElement.Scale.Console.IDE.Feed.classSearchInputElement.getAttribute('list')}"]`)
    window.LiveElement.Scale.Console.IDE.Feed.querySearchDatalistElement = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySelector(`datalist[id="${window.LiveElement.Scale.Console.IDE.Feed.querySearchInputElement.getAttribute('list')}"]`)
    window.LiveElement.Scale.Console.IDE.Feed.feedSearchDatalistElement = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySelector(`datalist[id="${window.LiveElement.Scale.Console.IDE.Feed.feedSearchInputElement.getAttribute('list')}"]`)
    window.LiveElement.Scale.Console.IDE.Feed.entitySearchLoadButton = window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.shadowRoot.querySelector('button[name="load"]')
    window.LiveElement.Scale.Console.IDE.Feed.toggleLoadButtonDisabled = function() {
        var supportInputsAllValid = window.LiveElement.Scale.Console.IDE.Feed.connectionSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Feed.connectionSearchDatalistElement.querySelector(`option[value="${window.LiveElement.Scale.Console.IDE.Feed.connectionSearchInputElement.value}"]`)
                && window.LiveElement.Scale.Console.IDE.Feed.classSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Feed.classSearchDatalistElement.querySelector(`option[value="${window.LiveElement.Scale.Console.IDE.Feed.classSearchInputElement.value}"]`)
                && window.LiveElement.Scale.Console.IDE.Feed.querySearchInputElement.value && window.LiveElement.Scale.Console.IDE.Feed.querySearchDatalistElement.querySelector(`option[value="${window.LiveElement.Scale.Console.IDE.Feed.querySearchInputElement.value}"]`)
        if ((supportInputsAllValid && window.LiveElement.Scale.Console.IDE.Feed.feedSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Feed.feedSearchDatalistElement.querySelector(`option[value="${window.LiveElement.Scale.Console.IDE.Feed.feedSearchInputElement.value}"]`)) 
                || (window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.allowNew && new window.RegExp(window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.allowNew).test(window.LiveElement.Scale.Console.IDE.Feed.feedSearchInputElement.value))) {
            window.LiveElement.Scale.Console.IDE.Feed.entitySearchLoadButton.removeAttribute('disabled')
        } else {
            window.LiveElement.Scale.Console.IDE.Feed.entitySearchLoadButton.setAttribute('disabled', true)
        }
    }
    window.LiveElement.Scale.Console.IDE.Feed.connectionSearchInputElement.addEventListener('input', event => {
        window.LiveElement.Scale.Console.System.invokeLambda({
            page: 'ide', 
            entity_type: 'feed', 
            heading: 'search',
            input_name: 'connection', 
            search: window.LiveElement.Scale.Console.IDE.Feed.connectionSearchInputElement.value
        }).then(connectionSearchResult => {
            if (connectionSearchResult && connectionSearchResult.result) {
                window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.connectionSearchResult = Array.isArray(connectionSearchResult.result) ? connectionSearchResult.result : (typeof connectionSearchResult.result == 'object' ? Object.keys(connectionSearchResult.result) : [])
                window.LiveElement.Scale.Core.buildDataList(window.LiveElement.Scale.Console.IDE.Feed.connectionSearchDatalistElement, window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.connectionSearchResult)
            }
            window.LiveElement.Scale.Console.IDE.Feed.toggleLoadButtonDisabled()
        })
    })
    window.LiveElement.Scale.Core.buildDataList(window.LiveElement.Scale.Console.IDE.Feed.classSearchDatalistElement, Object.assign({}, ...Object.entries(window.LiveElement.Scale.Console.IDE.classes).map(entry => ({[entry[0]]: entry[1].label}))))
    window.LiveElement.Scale.Console.IDE.Feed.querySearchInputElement.addEventListener('input', event => {
        if (window.LiveElement.Scale.Console.IDE.Feed.connectionSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Feed.classSearchInputElement.value) {
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'feed', 
                heading: 'search',
                connection: window.LiveElement.Scale.Console.IDE.Feed.connectionSearchInputElement.value, 
                'class': window.LiveElement.Scale.Console.IDE.Feed.classSearchInputElement.value, 
                input_name: 'query', 
                search: window.LiveElement.Scale.Console.IDE.Feed.querySearchInputElement.value
            }).then(querySearchResult => {
                if (querySearchResult && querySearchResult.result) {
                    window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySearchResult = Array.isArray(querySearchResult.result) ? querySearchResult.result : (typeof querySearchResult.result == 'object' ? Object.keys(querySearchResult.result) : [])
                    window.LiveElement.Scale.Core.buildDataList(window.LiveElement.Scale.Console.IDE.Feed.querySearchDatalistElement, window.LiveElement.Scale.Console.IDE.Feed.entitySearchElement.querySearchResult)
                }
                window.LiveElement.Scale.Console.IDE.Feed.toggleLoadButtonDisabled()
            })
        }
    })
    
}


window.LiveElement.Live.processors.IdeFeedEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="feed"] fieldset[name="edit"]')
    if (handlerType == 'listener') {
        return {
            connection: (window.LiveElement.Scale.Console.IDE.Feed.feedElement || {}).connection, 
            'class': (window.LiveElement.Scale.Console.IDE.Feed.feedElement || {}).class, 
            query: (window.LiveElement.Scale.Console.IDE.Connection.feedElement || {}).query, 
            '@id': (window.LiveElement.Scale.Console.IDE.Feed.feedElement || {})['@id']
        }
    } else if (handlerType == 'trigger') {
        if (input.entity) {
            editFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.Feed.feedElement = editFieldset.querySelector('element-feed')
            if (window.LiveElement.Scale.Console.IDE.Feed.feedElement) {
                window.LiveElement.Scale.Console.IDE.Feed.feedElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Feed.feedElement = document.createElement('element-feed')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Feed.feedElement)
            window.LiveElement.Scale.Console.IDE.Feed.feedElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Feed.feedElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Feed.feedElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'feed')
            })
        } else {
            editFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('ide', 'feed')
