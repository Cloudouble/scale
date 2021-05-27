window.LiveElement.Scale.Console.IDE = window.LiveElement.Scale.Console.IDE || {}
window.LiveElement.Scale.Console.IDE.pageElement = document.getElementById('ide')
window.LiveElement.Scale.Console.IDE.systemURL = `${window.localStorage.getItem('system:system_access_url')}${window.localStorage.getItem('system:system_root')}`
window.LiveElement.Scale.Console.IDE.connectionURL = `${window.LiveElement.Scale.Console.IDE.systemURL}/connection/${window.localStorage.getItem('system:connection_id')}`
window.LiveElement.Scale.Console.IDE.newFlag = '---new---'

window.LiveElement.Scale.Console.IDE.writeHistory = function(entity_type, entity_subtype, entity_uuid, entity, trigger, searchFieldset) {
    var historyElement = searchFieldset.querySelector('.history')
    var historySmallElement = historyElement.querySelector('small')
    var liElement = document.createElement('li')
    liElement.classList.add('history-entry')
    liElement.setAttribute('entity-type', entity_type)
    liElement.setAttribute('entity-subtype', entity_subtype)
    liElement.setAttribute('entity-uuid', entity_uuid)
    var hint = ''
    var path = ''
    if (Object.keys(entity).length > 2) {
        if (entity.name) {
            hint = `${hint}name="${entity.name}", `
        }
        var extraHintField = Object.keys(entity)
            .filter(k => k != 'name' && k[0] != '@' && typeof entity[k] != 'object').sort().shift()
        if (extraHintField) {
            hint = `${hint}${extraHintField}=${JSON.stringify(entity[extraHintField])}`
        }
        path = entity_subtype ? `${entity_type}/${entity_subtype}/${entity_uuid}` : `${entity_type}/${entity_uuid}`
        liElement.innerHTML = window.LiveElement.Scale.Core.truncateLabel(`${path} [${hint}, ... ]`, 120)
    } else {
        path = entity_subtype ? `${entity_type}/${entity_subtype}/${entity_uuid}` : `${entity_type}/${entity_uuid}`
        liElement.innerHTML = `${path} [${window.LiveElement.Scale.Console.IDE.newFlag}]`
    }
    if (historySmallElement) {
        historySmallElement.remove()
    }
    if (trigger) {
        liElement.setAttribute('live-trigger', trigger)
    }
    historyElement.prepend(liElement)
}
window.LiveElement.Scale.Console.IDE.loadHistory = function(historyEntry, entityTypeInput, entitySubtypeInput, entityUuidInput, loadButton) {
    Object.entries({'entity-type': entityTypeInput, 'entity-subtype': entitySubtypeInput, 'entity-uuid': entityUuidInput}).forEach(entry => {
        if (entry[1]) {
            entry[1].focus()
            entry[1].value = historyEntry.getAttribute(entry[0]) || ''
            entry[1].dispatchEvent(new window.Event('search'))
        }
    })
    if (loadButton) {
        loadButton.removeAttribute('disabled')
        loadButton.focus()
        loadButton.click()
    }
}
window.LiveElement.Scale.Console.IDE.cleanEditorEntity = function(editor, context, targetKey) {
    var cleanRecord = Object.assign({}, ...Array.from(editor.querySelectorAll('tr[name]')).filter(tr => {
        var trName = tr.getAttribute('name')
        return trName && trName in context[targetKey]
    }).map(tr => {
        var trName = tr.getAttribute('name')
        return {[trName]: context[targetKey][trName]}
    }).sort((a, b) => {
        var aKey = Object.keys(a)[0], bKey = Object.keys(b)[0]
        return aKey < bKey ? -1 : (aKey > bKey ? 1 : 0)
    }))
    return cleanRecord
}

var p = []
window.LiveElement.Scale.Console.IDE.pageElement.querySelectorAll(`:scope > section[name]`).forEach(sectionElement => {
    var entity_type = sectionElement.getAttribute('name')
    var styleTag = document.createElement('link')
    styleTag.setAttribute('href', `pages/ide/pages/${entity_type}/style.css`)
    styleTag.setAttribute('rel', 'stylesheet')
    document.head.appendChild(styleTag)
    p.push(window.fetch(`pages/ide/pages/${entity_type}/index.html`).then(r => r.text()).then(t => {
        sectionElement.innerHTML = t
    }))
})
p.push(window.LiveElement.Scale.Core.waitUntil(() => window.LiveElement.Scale.Console.System && typeof window.LiveElement.Scale.Console.System.invokeLambda == 'function').then(() => {
    return window.LiveElement.Scale.Console.System.invokeLambda({
        page: 'ide', 
        entity_type: 'classes'
    }).then(classes => {
        if (classes && typeof classes == 'object') {
            window.LiveElement.Scale.Console.IDE.classes = classes
        }
    })
}))
Promise.all(p).then(() => {
    window.LiveElement.Scale.Console.IDE.pageElement.querySelectorAll('div[name="sidebar"] button').forEach(button => {
        window.LiveElement.Scale.Console.IDE[button.innerHTML] = window.LiveElement.Scale.Console.IDE[button.innerHTML] || {}
        var subsection = window.LiveElement.Scale.Console.IDE.pageElement.querySelector(`section[name="${button.innerHTML.toLowerCase()}"]`)
        if (subsection) {
            subsection.querySelectorAll('h3').forEach(h3 => {
                window.LiveElement.Scale.Console.IDE[button.innerHTML][h3.innerHTML] = window.LiveElement.Scale.Console.IDE[button.innerHTML][h3.innerHTML] || {}
            })
        }
    })
    window.LiveElement.Scale.Console.IDE.pageElement.querySelectorAll(`:scope > section[name]`).forEach(sectionElement => {
        var entity_type = sectionElement.getAttribute('name')
        var scriptTag = document.createElement('script')
        scriptTag.setAttribute('src', `pages/ide/pages/${entity_type}/script.js`)
        document.body.appendChild(scriptTag)
    })
    window.LiveElement.Scale.Console.IDE.pageElement.querySelectorAll('input[type="uuid"]').forEach(uuidInput => {
        uuidInput.setAttribute('pattern', '^[0-9a-z]{8}-[0-9a-z]{4}-4[0-9a-z]{3}-[89ab][0-9a-z]{3}-[0-9a-z]{12}$')
        uuidInput.setAttribute('type', 'text')
    })
    window.LiveElement.Scale.Console.IDE.pageElement.querySelectorAll('div[name="sidebar"] button').forEach(button => {
        button.addEventListener('click', event => {
            window.LiveElement.Scale.Console.IDE.pageElement.setAttribute('entity-type', button.innerHTML.toLowerCase())
        })
    })
    window.LiveElement.Scale.Core.buildDataList(document.getElementById('ide--class'), Object.assign({}, ...Object.keys(window.LiveElement.Scale.Console.IDE.classes).sort().map(className => {
        return {[className]: `${window.LiveElement.Scale.Console.IDE.classes[className].label} [${window.LiveElement.Scale.Console.IDE.classes[className].parents.join('&rarr;')}]`}
    })))
})

