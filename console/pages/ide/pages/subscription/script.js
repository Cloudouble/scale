var entitySearchElement = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="subscription"] element-entitysearch')
if (entitySearchElement) {
    var connectionSearchInputElement = entitySearchElement.querySelector('input[name="connection"]')
    var classSearchInputElement = entitySearchElement.querySelector('input[name="class"]')
    var recordSearchInputElement = entitySearchElement.querySelector('input[name="record"]')
    var subscriptionSearchInputElement = entitySearchElement.querySelector('input[name="@id"]')
    var connectionSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${connectionSearchInputElement.getAttribute('list')}"]`)
    var classSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${classSearchInputElement.getAttribute('list')}"]`)
    var recordSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${recordSearchInputElement.getAttribute('list')}"]`)
    var subscriptionSearchDatalistElement = entitySearchElement.querySelector(`datalist[id="${subscriptionSearchInputElement.getAttribute('list')}"]`)
    var entitySearchLoadButton = entitySearchElement.shadowRoot.querySelector('button[name="load"]')
    var toggleLoadButtonDisabled = function() {
        var supportInputsAllValid = connectionSearchInputElement.value && connectionSearchDatalistElement.querySelector(`option[value="${connectionSearchInputElement.value}"]`)
                && classSearchInputElement.value && classSearchDatalistElement.querySelector(`option[value="${classSearchInputElement.value}"]`)
                && recordSearchInputElement.value && recordSearchDatalistElement.querySelector(`option[value="${recordSearchInputElement.value}"]`)
        if ((supportInputsAllValid && subscriptionSearchInputElement.value && subscriptionSearchDatalistElement.querySelector(`option[value="${subscriptionSearchInputElement.value}"]`)) 
                || (entitySearchElement.allowNew && new window.RegExp(entitySearchElement.allowNew).test(subscriptionSearchInputElement.value))) {
            entitySearchLoadButton.removeAttribute('disabled')
        } else {
            entitySearchLoadButton.setAttribute('disabled', true)
        }
    }
    connectionSearchInputElement.addEventListener('input', event => {
        window.LiveElement.Scale.Console.System.invokeLambda({
            page: 'ide', 
            entity_type: 'subscription', 
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
    recordSearchInputElement.addEventListener('input', event => {
        if (connectionSearchInputElement.value && classSearchInputElement.value) {
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'subscription', 
                heading: 'search',
                connection: connectionSearchInputElement.value, 
                'class': classSearchInputElement.value, 
                input_name: 'record', 
                search: recordSearchInputElement.value
            }).then(recordSearchResult => {
                if (recordSearchResult && recordSearchResult.result) {
                    entitySearchElement.recordSearchResult = Array.isArray(recordSearchResult.result) ? recordSearchResult.result : (typeof recordSearchResult.result == 'object' ? Object.keys(recordSearchResult.result) : [])
                    window.LiveElement.Scale.Core.buildDataList(recordSearchDatalistElement, entitySearchElement.recordSearchResult)
                }
                toggleLoadButtonDisabled()
            })
        }
    })
    
}


window.LiveElement.Live.processors.IdeSubscriptionEdit = function(input) {
    var handlerType = window.LiveElement.Live.getHandlerType(input)
    var editFieldset = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="subscription"] fieldset[name="edit"]')
    if (handlerType == 'listener') {
        return {
            connection: (window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement || {}).connection, 
            'class': (window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement || {}).class, 
            record: (window.LiveElement.Scale.Console.IDE.Connection.subscriptionElement || {}).record, 
            '@id': (window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement || {})['@id']
        }
    } else if (handlerType == 'trigger') {
        if (input.entity) {
            editFieldset.setAttribute('active', true)
            window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement = editFieldset.querySelector('element-subscription')
            if (window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement) {
                window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement.remove()
            }
            window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement = document.createElement('element-subscription')
            editFieldset.querySelector('h3').after(window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement)
            window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement.mode = 'editor'
            Object.assign(window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement, input.entity)
            window.LiveElement.Scale.Console.IDE.Subscription.subscriptionElement.addEventListener('change', event => {
                window.LiveElement.Scale.Console.buildSnippets('ide', 'subscription')
            })
        } else {
            editFieldset.removeAttribute('active')
        }
    }
}

window.LiveElement.Scale.Console.buildSnippets('ide', 'subscription')
