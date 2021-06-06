var entitySearchElement = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="feed"] element-entitysearch')
if (entitySearchElement) {
    var connectionSearchInputElement = entitySearchElement.querySelector('input[name="connection"]')
    var classSearchInputElement = entitySearchElement.querySelector('input[name="class"]')
    var querySearchInputElement = entitySearchElement.querySelector('input[name="query"]')
    var feedSearchInputElement = entitySearchElement.querySelector('input[name="@id"]')
    var connectionSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${connectionSearchInputElement.getAttribute('list')}"]`)
    var classSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${classSearchInputElement.getAttribute('list')}"]`)
    var querySearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${querySearchInputElement.getAttribute('list')}"]`)
    var feedSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${feedSearchInputElement.getAttribute('list')}"]`)
    var entitySearchLoadButton = entitySearchElement.shadowRoot.querySelector('button[name="load"]')
    var toggleLoadButtonDisabled = function() {
        var supportInputsAllValid = connectionSearchInputElement.value && connectionSearchDatalistElement.querySelector(`option[value="${connectionSearchInputElement.value}"]`)
                && classSearchInputElement.value && classSearchDatalistElement.querySelector(`option[value="${classSearchInputElement.value}"]`)
                && querySearchInputElement.value && querySearchDatalistElement.querySelector(`option[value="${querySearchInputElement.value}"]`)
        if ((supportInputsAllValid && feedSearchInputElement.value && feedSearchDatalistElement.querySelector(`option[value="${feedSearchInputElement.value}"]`)) 
                || (entitySearchElement.allowNew && new window.RegExp(entitySearchElement.allowNew).test(feedSearchInputElement.value))) {
            entitySearchLoadButton.removeAttribute('disabled')
        } else {
            entitySearchLoadButton.setAttribute('disabled', true)
        }
    }
    connectionSearchInputElement.addEventListener('input', event => {
        window.LiveElement.Scale.Console.System.invokeLambda({
            page: 'ide', 
            entity_type: 'feed', 
            heading: 'search',
            input_name: 'connection', 
            search: connectionSearchInputElement.value
        }).then(connectionSearchResult => {
            if (connectionSearchResult && connectionSearchResult.result) {
                entitySearchElement.connectionSearchResult = Array.isArray(connectionSearchResult.result) ? connectionSearchResult.result : (typeof connectionSearchResult.result == 'object' ? Object.keys(connectionSearchResult.result) : [])
                window.LiveElement.Scale.Core.buildDataList(connectionSearchDatalistElement, entitySearchElement.connectionSearchResult)
            }
            toggleLoadButtonDisabled()
        })
    })
    window.LiveElement.Scale.Core.buildDataList(classSearchDatalistElement, Object.assign({}, ...Object.entries(window.LiveElement.Scale.Console.IDE.classes).map(entry => ({[entry[0]]: entry[1].label}))))
    querySearchInputElement.addEventListener('input', event => {
        if (connectionSearchInputElement.value && classSearchInputElement.value) {
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'feed', 
                heading: 'search',
                connection: connectionSearchInputElement.value, 
                'class': classSearchInputElement.value, 
                input_name: 'query', 
                search: querySearchInputElement.value
            }).then(querySearchResult => {
                if (querySearchResult && querySearchResult.result) {
                    entitySearchElement.querySearchResult = Array.isArray(querySearchResult.result) ? querySearchResult.result : (typeof querySearchResult.result == 'object' ? Object.keys(querySearchResult.result) : [])
                    window.LiveElement.Scale.Core.buildDataList(querySearchDatalistElement, entitySearchElement.querySearchResult)
                }
                toggleLoadButtonDisabled()
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
