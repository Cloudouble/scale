/* global */
window.LiveElement.Scale = window.LiveElement.Scale || {}
window.LiveElement.Scale.Core = window.LiveElement.Scale.Core || {}
window.LiveElement.Scale.Console = window.LiveElement.Scale.Console || {}
window.LiveElement.Scale.Core.generateUUID4 = function() {
    var u = '********-****-4***-N***-************'
    var v = ['8', '9', 'a', 'b']
    var v_index = 0
    while (!v_index) {
        let va = new window.Uint8Array(1)
        window.crypto.getRandomValues(va)
        let va_v = parseInt(String(va[0]).slice(-1), 10)
        v_index = va_v >=1 && va_v <= 4 ? va_v : 0 
    }
    u = u.replace('N', v[v_index-1])
    while (u.includes('*')) {
        let va = new window.Uint8Array(1)
        window.crypto.getRandomValues(va)
        if ((va[0] >= 48 && va[0] <= 57) || (va[0] >= 97 && va[0] <= 102)) {
            u = u.replace('*', String.fromCharCode(va[0]))
        }
    }
    return u
}
window.LiveElement.Scale.Core.syncWithLocalStorage = function(page, checkboxElement, inputElement) {
    if (checkboxElement.checked) {
        window.localStorage.setItem(`${page}:${inputElement.getAttribute('name')}`, inputElement.value)
    } else {
        window.localStorage.removeItem(`${page}:${inputElement.getAttribute('name')}`)
    }
}


window.LiveElement.Element.root = 'https://cdn.jsdelivr.net/gh/cloudouble/element@1.7.5/elements/'
window.LiveElement.Element.load().then(() => {
  window.LiveElement.Element.root = 'https://cdn.jsdelivr.net/gh/cloudouble/schema@1.0.4/types/'
  window.LiveElement.Element.load(['Schema'].concat(window.LiveElement.Schema.CoreTypes).concat(window.LiveElement.Schema.DataTypes)).then(() => {
    var setPage = function(page) {
      page = page || window.location.hash.slice(1)
      var pageLink = document.querySelector(`header > nav > ul > li > a[href="#${page}"]`)
      page = pageLink ? page : 'home'
      document.body.setAttribute('page', page)
      var sectionElement = document.querySelector(`section[id="${page}"]`)
      document.querySelector('header > h1').innerHTML = sectionElement.getAttribute('title')
      sectionElement.removeAttribute('title')
    }
    document.querySelectorAll('header > nav > ul > li > a').forEach(a => {
      var page = a.getAttribute('href').slice(1)
      a.addEventListener('click', event => {
        setPage(page)
      })
      var styleTag = document.createElement('link')
      styleTag.setAttribute('href', `pages/${page}/style.css`)
      styleTag.setAttribute('rel', 'stylesheet')
      document.head.appendChild(styleTag)
      window.fetch(`pages/${page}/index.html`).then(r => r.text()).then(t => {
        document.querySelector(`section[id="${page}"]`).innerHTML = t
        var scriptTag = document.createElement('script')
        scriptTag.setAttribute('src', `pages/${page}/script.js`)
        document.body.appendChild(scriptTag)
      })
    })
    window.addEventListener("hashchange", event => {
      setPage()
    }, false);
    setPage()
  })    
})    



/*
window.navigator.serviceWorker.ready.then(function(registration) {
  return registration.pushManager.getSubscription().then(subscription => {
    if (subscription) { 
      return subscription
    } else {
      return registration.pushManager.subscribe()
    }
  })
}).then(function(subscription) {
  fetch('./register', {
    method: 'post',
    headers: {
      'Content-type': 'application/json'
    },
    body: JSON.stringify({
      subscription: subscription
    }),
  });

  document.getElementById('doIt').onclick = function() {
    const delay = document.getElementById('notification-delay').value;
    const ttl = document.getElementById('notification-ttl').value;
    fetch('./sendNotification', {
      method: 'post',
      headers: {
        'Content-type': 'application/json'
      },
      body: JSON.stringify({
        subscription: subscription,
        delay: delay,
        ttl: ttl,
      }),
    });
  };

});"
*/
/*

// define processors for window.LiveElement.Live
window.LiveElement.Live.processors.example = function(input) {
  switch(window.LiveElement.Live.getHandlerType(input)) {
      case 'subscription': 
          return {placeholder: input.payload._timestamp}
      case 'trigger':
          console.log(`You changed the value of ${input.attributes.name} to "${input.map['#value']}"`)
  }
}

// define listeners for window.LiveElement.Live
window.LiveElement.Live.listeners.testlistener = {processor: 'default', delay: 1000, max: 10}

*/