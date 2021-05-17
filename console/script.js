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
window.LiveElement.Scale.Core.buildSnippet = function(codeElement) {
    if (!codeElement.getAttribute('regex')) {
      codeElement.setAttribute('regex', codeElement.innerText)
    }
    var newValue = codeElement.getAttribute('regex').replace(/\$\{(?<code>[^\}]+)\}/g, function(...args) { 
        var code = args.pop().code 
        var retval 
        try {
          retval = code ? Function(`"use strict";return (${code})`)() : ''
        } catch(e) {
          retval = '${'+code+'}'
        }
        return retval
    })
    var editor = window.ace.edit(codeElement)
    editor.setOptions({...window.LiveElement.Scale.Console.aceOptions, ...{readOnly: true}})
    editor.renderer.setScrollMargin(10, 10)
    editor.session.setMode(`ace/mode/${codeElement.getAttribute('mode') || 'javascript'}`)
    editor.setValue(newValue)
    var snippetContainer = codeElement.parentElement
    if (snippetContainer.classList.contains('snippet-container')) {
      snippetContainer.setAttribute('built', true)
    }
}
window.LiveElement.Scale.Core.buildDataList = function(datalistElement, optionValues) {
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
}
window.LiveElement.Element.root = 'https://cdn.jsdelivr.net/gh/cloudouble/element@1.7.5/elements/'
window.LiveElement.Element.load().then(() => {
  window.LiveElement.Element.root = 'https://cdn.jsdelivr.net/gh/cloudouble/schema@1.0.4/types/'
  return window.LiveElement.Element.load(['Schema'].concat(window.LiveElement.Schema.CoreTypes).concat(window.LiveElement.Schema.DataTypes)).then(() => {
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
  })    
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
  
})    

window.ace.config.set("basePath", "https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/")
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



