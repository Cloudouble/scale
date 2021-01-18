/* global globalThis */

importScripts('scale-sw.js')

addEventListener('activate', function (activateEvent) {
    activateEvent.waitUntil(globalThis.clients.claim())
    activateEvent.waitUntil(globalThis.clients.matchAll({type: 'all', includeUncontrolled: true}).then(function (windowClients) {
        windowClients.forEach(client => {
            client.postMessage({
                one: 1,
                two: 2
            })
        })
    }))
})

