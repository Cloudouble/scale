/* global */
window.LiveElement.Element.root = 'https://cdn.jsdelivr.net/gh/cloudouble/element@1.7.5/elements/'
window.LiveElement.Element.load().then(() => {
  window.LiveElement.Element.root = 'https://cdn.jsdelivr.net/gh/cloudouble/schema@1.0.4/types/'
  window.LiveElement.Element.load(['Schema'].concat(window.LiveElement.Schema.CoreTypes).concat(window.LiveElement.Schema.DataTypes)).then(() => {
    var setPage = function(page) {
      var page = page || window.location.hash.slice(1)
      var pageLink = document.querySelector(`header > nav > ul > li > a[href="#${page}"]`)
      page = pageLink ? page : 'home'
      document.body.setAttribute('page', page)
      document.querySelector('header > h1').innerHTML = document.querySelector(`section[id="${page}"]`).getAttribute('title')
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