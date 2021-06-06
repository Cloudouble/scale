var entitySearchElement = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="feed"] element-entitysearch')
if (entitySearchElement) {
    var connectionSearchInputElement = entitySearchElement.querySelector('input[name="connection"]')
    var classSearchInputElement = entitySearchElement.querySelector('input[name="class"]')
    var querySearchInputElement = entitySearchElement.querySelector('input[name="query"]')
    var connectionSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${connectionSearchInputElement.getAttribute('list')}"]`)
    var classSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${classSearchInputElement.getAttribute('list')}"]`)
    var querySearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${querySearchInputElement.getAttribute('list')}"]`)
    var entitySearchLoadButton = entitySearchElement.shadowRoot.querySelector('button[name="load"]')
    connectionSearchInputElement.addEventListener('search', event => {
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
            var loadButtonAlreadyDisabled = entitySearchLoadButton.getAttribute('disabled'), resultIncludesValue = entitySearchElement.result.includes(connectionSearchInputElement.value)
            if ((loadButtonAlreadyDisabled && resultIncludesValue) || (entitySearchElement.allowNew && new window.RegExp(entitySearchElement.allowNew).test(connectionSearchInputElement.value))) {
                entitySearchLoadButton.removeAttribute('disabled')
            } else if (!loadButtonAlreadyDisabled && !resultIncludesValue) {
                entitySearchLoadButton.setAttribute('disabled', true)
            }
        })
    })
    
    window.LiveElement.Scale.Core.buildDataList(classSearchDatalistElement, Object.assign({}, ...Object.entries(window.LiveElement.Scale.Console.IDE.classes).map(entry => ({[entry[0]]: entry[1].label}))))
    
    querySearchInputElement.addEventListener('search', event => {
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
            var loadButtonAlreadyDisabled = entitySearchLoadButton.getAttribute('disabled'), resultIncludesValue = entitySearchElement.result.includes(querySearchInputElement.value)
            if ((loadButtonAlreadyDisabled && resultIncludesValue) || (entitySearchElement.allowNew && new window.RegExp(entitySearchElement.allowNew).test(querySearchInputElement.value))) {
                entitySearchLoadButton.removeAttribute('disabled')
            } else if (!loadButtonAlreadyDisabled && !resultIncludesValue) {
                entitySearchLoadButton.setAttribute('disabled', true)
            }
        })
    })
    
}


window.LiveElement.Live.processors.IdeFeedEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="feed"] fieldset[name="edit"]')
    //var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="feed"] fieldset[name="code"]')
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
            //codeFieldset.setAttribute('active', true)
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
            //window.LiveElement.Scale.Console.IDE.Feed.feedElement.setAttribute('live-subscription', 'IdeFeedEdit:IdeFeedCode')
            //window.LiveElement.Live.listen(window.LiveElement.Scale.Console.IDE.Feed.feedElement, 'IdeFeedEdit', 'change', false, true)
        } else {
            editFieldset.removeAttribute('active')
            //codeFieldset.removeAttribute('active')
        }
    }
}

/*window.LiveElement.Live.processors.IdeConnectionCode = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var codeFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="connection"] fieldset[name="code"]')
    if (handlerType == 'subscription') {
        var websocketUrlInputElement = codeFieldset.querySelector('input[name="websocketUrl"]')
        if (websocketUrlInputElement && input.payload['@id']) {
            websocketUrlInputElement.value = (input.payload['@id']) ? `${window.LiveElement.Scale.Console.IDE.systemURL}/connection/${input.payload['@id']}/websocket` : ''
        }
    }
}*/

window.LiveElement.Scale.Console.buildSnippets('ide', 'connection')

//window.LiveElement.Live.listeners.IdeConnectionEdit = {processor: 'IdeConnectionEdit', expired: true}
