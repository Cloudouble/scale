/* global */
window.LiveElement.Scale = window.LiveElement.Scale || {}
window.LiveElement.Scale.Core = window.LiveElement.Scale.Core || {}
window.LiveElement.Scale.Console = window.LiveElement.Scale.Console || {}
window.LiveElement.Scale.Core.uuid4Pattern = '^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$'
window.LiveElement.Scale.Core.setAttributes = function(element, attributes) {
  if (element && typeof element == 'object' && attributes && typeof attributes == 'object' && typeof element.setAttribute == 'function') {
    Object.entries(attributes).forEach(entry => element.setAttribute(entry[0], entry[1]))
  }
}
window.LiveElement.Scale.Core.createElement = function(tagName, attributes, value) {
  if (tagName && typeof tagName == 'string') {
    var element = document.createElement(tagName)
    if (attributes && typeof attributes == 'object') {
      Object.entries(attributes).forEach(entry => {
        if (typeof entry[1] == 'string' || typeof entry[1] == 'number' || typeof entry[1] == 'boolean') {
          element.setAttribute(entry[0], entry[1])
        } else if (entry[1] == null || entry[1] == undefined) {
          element.setAttribute(entry[0], '')
        }
      })
    }
    if (typeof value != 'object') {
      var renderedValue = value ? value : (value === false ? 'false' : '')
      if (tagName == 'input' || tagName == 'select') {
        element.value = renderedValue
      } else {
        element.innerHTML = renderedValue
      }
    } else if (value instanceof window.HTMLElement) {
      element.appendChild(value)
    }
    return element
  }
}
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
window.LiveElement.Scale.Core.waitUntil = function(condition, aggressiveness=100) {
  return new Promise(function(resolve, reject) {
    if (condition && typeof condition == 'function') {
      var i = window.setInterval(function() {
          if (condition()) {
              window.clearInterval(i)
              resolve()
          }
      }, aggressiveness)
    } else {
      resolve()
    }
  })
}
window.LiveElement.Scale.Core.syncWithLocalStorage = function(page, checkboxElement, inputElement) {
    if (checkboxElement.checked) {
        window.localStorage.setItem(`${page}:${inputElement.getAttribute('name')}`, inputElement.value)
    } else {
        window.localStorage.removeItem(`${page}:${inputElement.getAttribute('name')}`)
    }
}
window.LiveElement.Scale.Core.buildDataList = function(datalistElement, optionValues, blankOptions) {
    datalistElement.innerHTML = ''
    if (optionValues && typeof optionValues == 'object') {
      if (Array.isArray(optionValues)) {
        optionValues.sort().forEach(k => {
            var optionElement = document.createElement('option')
            optionElement.setAttribute('value', k)
            optionElement.innerHTML = k
            datalistElement.appendChild(optionElement)
        })
      } else {
        Object.keys(optionValues).sort().forEach(k => {
            var optionElement = document.createElement('option')
            optionElement.setAttribute('value', k)
            optionElement.innerHTML = optionValues[k]
            datalistElement.appendChild(optionElement)
        })
      }
    }
    if (blankOptions && typeof blankOptions == 'object') {
      if (!Array.isArray(blankOptions)) {
        blankOptions = [blankOptions]
      }
      if (blankOptions && typeof Array.isArray(blankOptions)) {
        blankOptions.filter(b => b && typeof b == 'object').reverse().forEach(blankOption => {
          Object.keys(blankOption).sort().forEach(value => {
            var newOptionElement = document.createElement('option')
            newOptionElement.setAttribute('value', value)
            newOptionElement.innerHTML = blankOption[value] || value
            datalistElement.prepend(newOptionElement)
          })
        })
      }
    }
}
window.LiveElement.Scale.Core.truncateLabel = function(label, maxLength) {
  return label.length > maxLength ? `${label.slice(0, maxLength)}...` : label
}

window.LiveElement.Element.root = 'https://cdn.jsdelivr.net/gh/cloudouble/element@1.7.5/elements/'
window.LiveElement.Element.load().then(() => {
  window.LiveElement.Element.root = 'elements/'
  return window.LiveElement.Element.load()
}).then(() => {
  window.LiveElement.Element.root = 'https://cdn.jsdelivr.net/gh/cloudouble/schema@1.0.4/types/'
  return window.LiveElement.Element.load(['Schema'].concat(window.LiveElement.Schema.CoreTypes).concat(window.LiveElement.Schema.DataTypes))
}).then(() => {
  var setPage = function(page) {
    page = page || window.location.hash.slice(1)
    var pageLink = document.querySelector(`header > nav > ul > li > a[href="#${page}"]`)
    page = pageLink ? page : 'home'
    document.body.setAttribute('page', page)
    var sectionElement = document.querySelector(`section[id="${page}"]`)
    document.querySelector('header > h1').innerHTML = sectionElement.getAttribute('heading')
  }
  var p = []
  document.querySelectorAll('header > nav > ul > li > a').forEach(a => {
    var page = a.getAttribute('href').slice(1)
    a.addEventListener('click', event => {
      setPage(page)
    })
    var styleTag = document.createElement('link')
    styleTag.setAttribute('href', `pages/${page}/style.css`)
    styleTag.setAttribute('rel', 'stylesheet')
    document.head.appendChild(styleTag)
    p.push(window.fetch(`pages/${page}/index.html`).then(r => r.text()).then(t => {
      document.querySelector(`section[id="${page}"]`).innerHTML = t
      var scriptTag = document.createElement('script')
      scriptTag.setAttribute('src', `pages/${page}/script.js`)
      document.body.appendChild(scriptTag)
    }))
  })
  window.addEventListener("hashchange", event => {
    setPage()
  }, false);
  setPage()
  return Promise.all(p)
}).then(() => {
  var observer = new window.MutationObserver(function() {
    document.querySelectorAll('input[readonly]:not([_selectready])').forEach(i => {
      i.addEventListener('click', event => {
        i.select()
        document.execCommand('copy')
      })
      i.setAttribute('_selectready', true)
    })
    document.querySelectorAll('pre code:not([_selectready])').forEach(c => {
      c.addEventListener('click', event => {
        var selection = window.getSelection()
        selection.selectAllChildren(c.closest('pre'))
      })
      c.setAttribute('_selectready', true)
    })
  })
  observer.observe(document.querySelector('main'), {subtree: true, childList: true});
  
  window.LiveElement.Element.elements.Snippet.aceOptions = {...window.LiveElement.Scale.Console.aceOptions, ...{readOnly: true}}
  document.querySelectorAll('element-snippet').forEach(snippetElement => {
    snippetElement.build()
  })
  
})    

window.LiveElement.Scale.Console.buildSnippets = function(page, section) {
  var pageElement = document.getElementById(page)
  if (pageElement) {
    var sectionElement = pageElement.querySelector(`:scope > section[name="${section}"]`)
    if (sectionElement) {
      sectionElement.querySelectorAll('element-snippet').forEach(snippetElement => {
        snippetElement.build()
      })
    }
  }
}

window.LiveElement.Scale.Console.aceOptions = {
    autoScrollEditorIntoView: true, 
    useSoftTabs: true, 
    navigateWithinSoftTabs: true, 
    highlightGutterLine: true, 
    displayIndentGuides: true, 
    maxLines: 30,
    minLines: 3, 
    scrollPastEnd: 0.5, 
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true, 
    enableSnippets: true, 
    theme: 'ace/theme/merbivore'
}

window.ace.config.set("basePath", "https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/")


