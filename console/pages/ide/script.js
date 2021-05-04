window.LiveElement.Scale.Console.IDE = window.LiveElement.Scale.Console.IDE || {}

var ide = document.getElementById('ide')
ide.querySelectorAll('input[type="uuid"]').forEach(uuidInput => {
    uuidInput.setAttribute('pattern', '^[0-9a-z]{8}-[0-9a-z]{4}-4[0-9a-z]{3}-[89ab][0-9a-z]{3}-[0-9a-z]{12}$')
    uuidInput.setAttribute('type', 'text')
    var generateButton = document.createElement('button')
    generateButton.innerHTML = '+'
    generateButton.setAttribute('title', 'Click to fill with a new UUID v4')
    generateButton.addEventListener('click', event => {
        event.preventDefault()
        uuidInput.value = window.LiveElement.Scale.Core.generateUUID4()
    })
    uuidInput.after(generateButton)
})
ide.querySelectorAll('div[name="sidebar"] button').forEach(button => {
    button.addEventListener('click', event => {
        ide.setAttribute('entity-type', button.innerHTML.toLowerCase())
    })
})