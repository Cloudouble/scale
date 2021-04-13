var syncWithLocalStorage = function(checkboxElement, inputElement) {
    if (checkboxElement.checked) {
        window.localStorage.setItem(`system:${inputElement.getAttribute('name')}`, inputElement.value)
    } else {
        window.localStorage.removeItem(`system:${inputElement.getAttribute('name')}`)
    }
}
;(['system_access_url', 'sudo_key']).forEach(name => {
    var input = document.querySelector(`section[id="system"] input[name="${name}"]`)
    input.value = window.localStorage.getItem(`system:${name}`)
    var checkbox = document.querySelector(`section[id="system"] input[name="${name}"] + small > input[type="checkbox"]`)
    checkbox.addEventListener('change', event => syncWithLocalStorage(checkbox, input))
    input.addEventListener('change', event => syncWithLocalStorage(checkbox, input))
    if (name == 'system_access_url' && !input.value) {
        input.value = window.location.origin
        syncWithLocalStorage(checkbox, input)
    }
})



