/* global globalThis */
globalThis.LiveElement = globalThis.LiveElement || {}
globalThis.LiveElement.Scale = globalThis.LiveElement.Scale || Object.defineProperties({}, {
    version: {configurable: false, enumerable: true, writable: false, value: '1.0.0'}, 
    State: {configurable: false, enumerable: true, writable: false, value: Object.defineProperties({}, {
        LoopDormantMs: {configurable: false, enumerable: true, writable: true, value: 10000}, 
        LoopBackgroundMs: {configurable: false, enumerable: true, writable: true, value: 1000}, 
        LoopMiddlegroundMs: {configurable: false, enumerable: true, writable: true, value: 200}, 
        LoopForegroundMs: {configurable: false, enumerable: true, writable: true, value: 100}, 
        DefaultListenerDelayMultiple: {configurable: false, enumerable: true, writable: true, value: 1}, 
        CurrentGround: {configurable: false, enumerable: true, writable: true, value: 'Foreground'}, 
        LoopCurrentMs: {configurable: false, enumerable: true, writable: true, value: 1000}, 
        ClientCountAll: {configurable: false, enumerable: true, writable: true, value: 1}, 
        ClientCountBackground: {configurable: false, enumerable: true, writable: true, value: 0}, 
        ClientCountMiddleground: {configurable: false, enumerable: true, writable: true, value: 0}, 
        ClientCountForeground: {configurable: false, enumerable: true, writable: true, value: 1}, 
    })}, 
    clients: {configurable: false, enumerable: true, writable: false, value: {}}, 
    listeners: {configurable: false, enumerable: true, writable: false, value: {}}, 
    processors: {configurable: false, enumerable: true, writable: false, value: {
        default: function(input) {
            switch(globalThis.LiveElement.Scale.getHandlerType(input)) {
                case 'listener': 
                    return {_timestamp: Date.now()}
                case 'subscription': 
                    return input.payload
                case 'trigger':
                    console.log(input)
            }
        }
    }}, 
    subscriptions: {configurable: false, enumerable: true, writable: false, value: {}}, 
    getHandlerType: {configurable: false, enumerable: false, writable: false, value: function(input) {
        if (!input) {
            return 'listener'
        } else if (input && typeof input == 'object' && input.listener && input.config && input.payload && input.subscriber
            && typeof input.listener == 'string' && typeof input.config == 'object' && typeof input.payload == 'object' && typeof input.subscriber == 'object') {
            return 'subscription'
        } else if (input && typeof input == 'object' && input.payload && input.triggersource && typeof input.payload == 'object' && typeof input.triggersource == 'object') {
            return 'trigger'
        }
    }}, 
    runListener: {configurable: false, enumerable: false, writable: false, value: function(key, config) {
        var now = Date.now()
        if (config && typeof config == 'object'
            && !config.expired 
            && typeof config.processor == 'string' && typeof globalThis.LiveElement.Scale.processors[config.processor] == 'function'
            && (((config.last || 0) + ((config.delaymultiple || globalThis.LiveElement.Scale.State.DefaultListenerDelayMultiple) * globalThis.LiveElement.Scale.State.LoopCurrentMs)) < now)) {
            if (config.expires && (config.expires <= now)) {
                config.expired = true
                globalThis.dispatchEvent(new globalThis.CustomEvent('scale-listener-expired', {detail: {listener: key, config: config}}))
                globalThis.dispatchEvent(new globalThis.CustomEvent(`scale-listener-expired-${key}`, {detail: {listener: key, config: config}}))
            } else if (config.count && config.max && (config.count >= config.max)) {
                config.expired = true
                globalThis.dispatchEvent(new globalThis.CustomEvent('scale-listener-maxed', {detail: {listener: key, config: config}}))
                globalThis.dispatchEvent(new globalThis.CustomEvent(`scale-listener-maxed-${key}`, {detail: {listener: key, config: config}}))
            } else if (config.next && (config.next > now)) {
                globalThis.dispatchEvent(new globalThis.CustomEvent('scale-listener-passed', {detail: {listener: key, config: config}}))
                globalThis.dispatchEvent(new globalThis.CustomEvent(`scale-listener-passed-${key}`, {detail: {listener: key, config: config}}))
            } else {
                config.last = now
                config.count = (config.count || 0) + 1
                var showconfig = {...config}
                if (config.next) {
                    showconfig.next = config.next
                    delete config.next
                }
                var listenerResult = globalThis.LiveElement.Scale.processors[config.processor]()
                if (listenerResult && typeof listenerResult == 'object') {
                    var processorInput = {
                        listener: key, 
                        config: config, 
                        payload: listenerResult
                    }
                    Object.entries(globalThis.LiveElement.Scale.subscriptions).forEach(entry => {
                        entry[1].map(vector => vector.split(':', 2)).filter(vectorSplit => vectorSplit[0] == key && typeof globalThis.LiveElement.Scale.processors[vectorSplit[1]] == 'function').forEach(vectorSplit => {
                            var message = {
                                meta: {source: 'worker', 'channel': entry[0]}, 
                                payload: globalThis.LiveElement.Scale.processors[vectorSplit[1]]({...processorInput, ...{subscriber: {[entry[0]]: entry[1]}}})
                            }
                            Object.values(globalThis.LiveElement.Scale.clients).forEach(client => {
                                client.postMessage(message)
                            })
                        })
                    })
                }
                globalThis.dispatchEvent(new globalThis.CustomEvent('scale-listener-run', {detail: {listener: key, config: showconfig, payload: listenerResult}}))
                globalThis.dispatchEvent(new globalThis.CustomEvent(`scale-listener-run-${key}`, {detail: {listener: key, config: showconfig, payload: listenerResult}}))
            }
        }
    }},
    run: {configurable: false, enumerable: false, writable: false, value: function() {
        globalThis.clients.claim()
        globalThis.clients.matchAll({includeUncontrolled: true}).then(clients => {
            Object.assign(globalThis.LiveElement.Scale.clients, ...clients.map(client => ({[client.id]: client})))
            globalThis.LiveElement.Scale.State.ClientCountAll = Object.values(globalThis.LiveElement.Scale.clients).length
            if (globalThis.LiveElement.Scale.State.ClientCountAll) {
                globalThis.LiveElement.Scale.State.ClientCountBackground = Object.values(globalThis.LiveElement.Scale.clients).filter(client => client.visibilityState == 'hidden').length
                globalThis.LiveElement.Scale.State.ClientCountMiddleground = Object.values(globalThis.LiveElement.Scale.clients).filter(client => !client.focused && ['visible', 'prerender'].includes(client.visibilityState)).length
                globalThis.LiveElement.Scale.State.ClientCountForeground = Object.values(globalThis.LiveElement.Scale.clients).filter(client => client.focused).length
                globalThis.LiveElement.Scale.State.CurrentGround = globalThis.LiveElement.Scale.State.ClientCountForeground ? 'Foreground' : (globalThis.LiveElement.Scale.State.ClientCountMiddleground ? 'Middleground' : 'Background')
            } else {
                globalThis.LiveElement.Scale.State.ClientCountBackground = 0
                globalThis.LiveElement.Scale.State.ClientCountMiddleground = 0
                globalThis.LiveElement.Scale.State.ClientCountForeground = 0
                globalThis.LiveElement.Scale.State.CurrentGround = 'Dormant'
            }
            globalThis.LiveElement.Scale.State.LoopCurrentMs = globalThis.LiveElement.Scale.State[`Loop${globalThis.LiveElement.Scale.State.CurrentGround}Ms`]
            Object.entries(globalThis.LiveElement.Scale.listeners).forEach(entry => {
                globalThis.LiveElement.Scale.runListener(...entry)
            })
            globalThis.setTimeout(globalThis.LiveElement.Scale.run, globalThis.LiveElement.Scale.State.LoopCurrentMs || 1000)
        })
    }}
})
Object.freeze(globalThis.LiveElement.Scale)
globalThis.setTimeout(globalThis.LiveElement.Scale.run, globalThis.LiveElement.Scale.State.LoopCurrentMs || 1000)

