window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement = window.LiveElement.Scale.Console.IDE.pageElement.querySelector('section[name="subscription"] element-entitysearch')
if (window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement) {
    window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchInputElement = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.querySelector('input[name="connection"]')
    window.LiveElement.Scale.Console.IDE.Subscription.classSearchInputElement = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.querySelector('input[name="class"]')
    window.LiveElement.Scale.Console.IDE.Subscription.recordSearchInputElement = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.querySelector('input[name="record"]')
    window.LiveElement.Scale.Console.IDE.Subscription.subscriptionSearchInputElement = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.querySelector('input[name="@id"]')
    window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchDatalistElement = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.querySelector(`datalist[id="${window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchInputElement.getAttribute('list')}"]`)
    window.LiveElement.Scale.Console.IDE.Subscription.classSearchDatalistElement = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.querySelector(`datalist[id="${window.LiveElement.Scale.Console.IDE.Subscription.classSearchInputElement.getAttribute('list')}"]`)
    window.LiveElement.Scale.Console.IDE.Subscription.recordSearchDatalistElement = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.querySelector(`datalist[id="${window.LiveElement.Scale.Console.IDE.Subscription.recordSearchInputElement.getAttribute('list')}"]`)
    window.LiveElement.Scale.Console.IDE.Subscription.subscriptionSearchDatalistElement = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.querySelector(`datalist[id="${window.LiveElement.Scale.Console.IDE.Subscription.subscriptionSearchInputElement.getAttribute('list')}"]`)
    window.LiveElement.Scale.Console.IDE.Subscription.entitySearchLoadButton = window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.shadowRoot.querySelector('button[name="load"]')
    window.LiveElement.Scale.Console.IDE.Subscription.toggleLoadButtonDisabled = function() {
        var supportInputsAllValid = window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchDatalistElement.querySelector(`option[value="${window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchInputElement.value}"]`)
                && window.LiveElement.Scale.Console.IDE.Subscription.classSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Subscription.classSearchDatalistElement.querySelector(`option[value="${window.LiveElement.Scale.Console.IDE.Subscription.classSearchInputElement.value}"]`)
                && window.LiveElement.Scale.Console.IDE.Subscription.recordSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Subscription.recordSearchDatalistElement.querySelector(`option[value="${window.LiveElement.Scale.Console.IDE.Subscription.recordSearchInputElement.value}"]`)
        if ((supportInputsAllValid && window.LiveElement.Scale.Console.IDE.Subscription.subscriptionSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Subscription.subscriptionSearchDatalistElement.querySelector(`option[value="${window.LiveElement.Scale.Console.IDE.Subscription.subscriptionSearchInputElement.value}"]`)) 
                || (window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.allowNew && new window.RegExp(window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.allowNew).test(window.LiveElement.Scale.Console.IDE.Subscription.subscriptionSearchInputElement.value))) {
            window.LiveElement.Scale.Console.IDE.Subscription.entitySearchLoadButton.removeAttribute('disabled')
        } else {
            window.LiveElement.Scale.Console.IDE.Subscription.entitySearchLoadButton.setAttribute('disabled', true)
        }
    }
    window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchInputElement.addEventListener('input', event => {
        window.LiveElement.Scale.Console.System.invokeLambda({
            page: 'ide', 
            entity_type: 'subscription', 
            heading: 'search',
            input_name: 'connection', 
            search: window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchInputElement.value
        }).then(connectionSearchResult => {
            if (connectionSearchResult && connectionSearchResult.result) {
                window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.connectionSearchResult = Array.isArray(connectionSearchResult.result) ? connectionSearchResult.result : (typeof connectionSearchResult.result == 'object' ? Object.keys(connectionSearchResult.result) : [])
                window.LiveElement.Scale.Core.buildDataList(window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchDatalistElement, window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.connectionSearchResult)
            }
            window.LiveElement.Scale.Console.IDE.Subscription.toggleLoadButtonDisabled()
        })
    })
    window.LiveElement.Scale.Core.buildDataList(window.LiveElement.Scale.Console.IDE.Subscription.classSearchDatalistElement, Object.assign({}, ...Object.entries(window.LiveElement.Scale.Console.IDE.classes).map(entry => ({[entry[0]]: entry[1].label}))))
    window.LiveElement.Scale.Console.IDE.Subscription.recordSearchInputElement.addEventListener('input', event => {
        if (window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchInputElement.value && window.LiveElement.Scale.Console.IDE.Subscription.classSearchInputElement.value) {
            window.LiveElement.Scale.Console.System.invokeLambda({
                page: 'ide', 
                entity_type: 'subscription', 
                heading: 'search',
                connection: window.LiveElement.Scale.Console.IDE.Subscription.connectionSearchInputElement.value, 
                'class': window.LiveElement.Scale.Console.IDE.Subscription.classSearchInputElement.value, 
                input_name: 'record', 
                search: window.LiveElement.Scale.Console.IDE.Subscription.recordSearchInputElement.value
            }).then(recordSearchResult => {
                if (recordSearchResult && recordSearchResult.result) {
                    window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.recordSearchResult = Array.isArray(recordSearchResult.result) ? recordSearchResult.result : (typeof recordSearchResult.result == 'object' ? Object.keys(recordSearchResult.result) : [])
                    window.LiveElement.Scale.Core.buildDataList(window.LiveElement.Scale.Console.IDE.Subscription.recordSearchDatalistElement, window.LiveElement.Scale.Console.IDE.Subscription.entitySearchElement.recordSearchResult)
                }
                window.LiveElement.Scale.Console.IDE.Subscription.toggleLoadButtonDisabled()
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
