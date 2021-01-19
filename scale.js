window.LiveElement = window.LiveElement || {}
window.LiveElement.Scale = window.LiveElement.Scale || Object.defineProperties({}, {
    version: {configurable: false, enumerable: true, writable: false, value: '1.0.0'}, 
    Options: {configurable: false, enumerable: true, writable: false, value: {
        Listen: true
    }}, 
    Channels: {configurable: false, enumerable: true, writable: false, value: {}}, 
    OpenChannels: {configurable: false, enumerable: true, writable: false, value: {}}, 
    isValidMessage: {configurable: false, enumerable: false, writable: false, value: function(message) {
        return message && typeof message == 'object' && message.meta && typeof message.meta == 'object' && message.payload && typeof message.payload == 'object' && message.meta.channel && message.meta.source
    }}, 
    getChannelProcessor: {configurable: false, enumerable: true, writable: false, value: function(channelName, processorName=undefined, subscriptionCallback=undefined, triggerCallback=undefined) {
        processorName = processorName || channelName
        if (processorName) {
            var hasSubscriptionCallback = subscriptionCallback && typeof subscriptionCallback == 'function'
            var hasTriggerCallback = triggerCallback && typeof triggerCallback == 'function' 
            if (hasSubscriptionCallback || hasTriggerCallback) {
                return function(input) {
                    switch (window.LiveElement.Live.getHandlerType(input)) {
                        case 'subscription':
                            return hasSubscriptionCallback ? subscriptionCallback(input) : input
                        case 'trigger':
                            return hasTriggerCallback ? triggerCallback(input) : input
                        default: 
                            var message = (window.LiveElement.Scale.Channels[processorName] || []).shift()
                            return message && typeof message == 'object' ? message : {}
                    }
                }
            } else {
                return function() {
                    var message = (window.LiveElement.Scale.Channels[processorName] || []).shift()
                    return message && typeof message == 'object' && message.payload && typeof message.payload == 'object' ? message.payload : {}
                }
            }
        }
    }}
})
if ('serviceWorker' in window.navigator) {
    window.navigator.serviceWorker.register('worker.js')
    window.navigator.serviceWorker.addEventListener('message', event => {
        if (window.LiveElement.Scale.Options.Listen) {
            if (window.LiveElement.Scale.isValidMessage(event.data)) {
                if (window.LiveElement.Scale.OpenChannels[event.data.meta.channel]) {
                    window.LiveElement.Scale.Channels[event.data.meta.channel] = window.LiveElement.Scale.Channels[event.data.meta.channel] || []
                    window.LiveElement.Scale.Channels[event.data.meta.channel].push(event.data.payload)
                }
            }
        }
    })
}