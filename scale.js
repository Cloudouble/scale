window.LiveElement = window.LiveElement || {}
window.LiveElement.Scale = window.LiveElement.Scale || Object.defineProperties({}, {
    version: {configurable: false, enumerable: true, writable: false, value: '1.0.0'}, 
    Options: {configurable: false, enumerable: true, writable: true, value: {
        Listen: true
    }}, 
    Queue: {configurable: false, enumerable: true, false: true, value: []}
})
if ('serviceWorker' in window.navigator) {
    window.navigator.serviceWorker.register('worker.js')
    window.navigator.serviceWorker.addEventListener('message', event => {
        if (window.LiveElement.Scale.Options.Listen) {
            window.LiveElement.Scale.Queue.push(event.data)
        }
    })
}