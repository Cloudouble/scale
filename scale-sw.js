/* global globalThis */
globalThis.LiveElement = globalThis.LiveElement || {}
globalThis.LiveElement.Scale = globalThis.LiveElement.Scale || Object.defineProperties({}, {
    version: {configurable: false, enumerable: true, writable: false, value: '1.0.0'}, 
    loopMaxMs: {configurable: false, enumerable: true, writable: false, value: 1000}, 
    defaultListenerDelay: {configurable: false, enumerable: true, writable: false, value: 1000}, 
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
    getHandlerType: {configurable: false, enumerable: false, writable: false, value: function(input) {
        if (!input) {
            return 'listener'
        } else if (input && typeof input == 'object' && input.listener && input.config && input.payload && input.subscriber 
            && typeof input.listener == 'string' && typeof input.config == 'object' && typeof input.payload == 'object' && typeof input.subscriber == 'object' 
            && typeof input.subscriber.setAttribute == 'function') {
            return 'subscription'
        } else if (input && typeof input == 'object' && input.attributes && input.properties && input.map && input.triggersource 
            && typeof input.attributes == 'object' && typeof input.properties == 'object' && typeof input.map == 'object' && typeof input.triggersource == 'object' 
            && typeof input.triggersource.setAttribute == 'function') {
            return 'trigger'
        }
    }}, 
    runListener: {configurable: false, enumerable: false, writable: false, value: function(key, config) {
        var now = Date.now()
        if (config && typeof config == 'object'
            && !config.expired 
            && typeof config.processor == 'string' && typeof globalThis.LiveElement.Scale.processors[config.processor] == 'function'
            && (((config.last || 0) + (config.delay || globalThis.LiveElement.Scale.defaultListenerDelay)) < now)) {
            if (config.expires && (config.expires <= now)) {
                config.expired = true
                globalThis.dispatchEvent(new globalThis.CustomEvent('live-listener-expired', {detail: {listener: key, config: config}}))
                globalThis.dispatchEvent(new globalThis.CustomEvent(`live-listener-expired-${key}`, {detail: {listener: key, config: config}}))
            } else if (config.count && config.max && (config.count >= config.max)) {
                config.expired = true
                globalThis.dispatchEvent(new globalThis.CustomEvent('live-listener-maxed', {detail: {listener: key, config: config}}))
                globalThis.dispatchEvent(new globalThis.CustomEvent(`live-listener-maxed-${key}`, {detail: {listener: key, config: config}}))
            } else if (config.next && (config.next > now)) {
                globalThis.dispatchEvent(new globalThis.CustomEvent('live-listener-passed', {detail: {listener: key, config: config}}))
                globalThis.dispatchEvent(new globalThis.CustomEvent(`live-listener-passed-${key}`, {detail: {listener: key, config: config}}))
            } else {
                config.last = now
                config.count = (config.count || 0) + 1
                var showconfig = {...config}
                if (config.next) {
                    showconfig.next = config.next
                    delete config.next
                }
                var payload = globalThis.LiveElement.Scale.processors[config.processor]()
                globalThis.dispatchEvent(new globalThis.CustomEvent('live-listener-run', {detail: {listener: key, config: showconfig, payload: payload}}))
                globalThis.dispatchEvent(new globalThis.CustomEvent(`live-listener-run-${key}`, {detail: {listener: key, config: showconfig, payload: payload}}))
            }
        }
    }},
    
    
    run: {configurable: false, enumerable: false, writable: false, value: function() {
        Object.entries(globalThis.LiveElement.Scale.listeners).forEach(entry => {
            globalThis.LiveElement.Scale.runListener(...entry)
        })
        globalThis.setTimeout(globalThis.LiveElement.Scale.run, globalThis.LiveElement.Scale.loopMaxMs || 1000)
    }}
})
Object.freeze(globalThis.LiveElement.Scale)
globalThis.setTimeout(globalThis.LiveElement.Scale.run, globalThis.LiveElement.Scale.loopMaxMs || 1000)
