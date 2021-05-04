window.LiveElement.Scale.Console.IDE = window.LiveElement.Scale.Console.IDE || {}

var ide = document.getElementById('ide')
ide.querySelectorAll('input[type="uuid"]').forEach(uuidInput => {
    uuidInput.setAttribute('pattern', '^[0-9a-z]{8}-[0-9a-z]{4}-4[0-9a-z]{3}-[89ab][0-9a-z]{3}-[0-9a-z]{12}$')
    uuidInput.setAttribute('type', 'text')
    var generateButton = document.createElement('button')
    generateButton.innerHTML = '+'
    generateButton.addEventListener('click', event => {
        event.preventDefault()
        uuidInput.value = window.LiveElement.Scale.Core.generateUUID4()
    })
    uuidInput.after(generateButton)
})