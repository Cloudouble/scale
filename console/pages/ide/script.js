window.LiveElement.Scale.Console.IDE = window.LiveElement.Scale.Console.IDE || {}
window.LiveElement.Scale.Console.IDE.pageElement = document.getElementById('ide')
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
})





