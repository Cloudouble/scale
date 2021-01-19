/* global globalThis */

importScripts('scale-sw.js')

globalThis.LiveElement.Scale.listeners.testlistener = {processor: 'default', delaymultiple: 10, max: 100}

globalThis.LiveElement.Scale.subscriptions.test = ['testlistener:default']



