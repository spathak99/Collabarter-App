/*
 * Function.prototype.bind polyfill from the Mozilla Developer Network
 * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind
 * License: http://creativecommons.org/publicdomain/zero/1.0/
 */
if (!Function.prototype.bind) {
Function.prototype.bind = function (oThis) {
  if (typeof this !== "function") {
    // closest thing possible to the ECMAScript 5 internal IsCallable function
    throw new TypeError("Function.prototype.bind - what is trying to be bound is not callable");
  }

  var aArgs = Array.prototype.slice.call(arguments, 1), 
    fToBind = this, 
    fNOP = function () {},
    fBound = function () {
      return fToBind.apply(
        this instanceof fNOP && oThis ? this : oThis,
        aArgs.concat(Array.prototype.slice.call(arguments)));
      };

    fNOP.prototype = this.prototype;
    fBound.prototype = new fNOP();

    return fBound;
  };
}

/*
 * Copyright 2013 The Polymer Authors. All rights reserved.
 * Use of this source code is governed by a BSD-style
 * license that can be found in the LICENSE file.
 */

/**
 * Implements `document.register`
 * @module CustomElements
*/

/**
 * Polyfilled extensions to the `document` object.
 * @class Document
*/

// normalise MutationObserver API
if (!window.MutationObserver && window.WebKitMutationObserver) {
  window.MutationObserver = window.WebKitMutationObserver;
}
if (!window.MutationObserver) {
  throw new Error('The CustomElements polyfill requires MutationObserver support. Include the MutationObserver polyfill then include the CustomElements polyfill.');
}


(function(){

  var scope = {};
  scope.logFlags = {dom:false};

  // native document.register?

  if (!Boolean(document.register)) {

    /**
     * Registers a custom tag name with the document.
     *
     * When a registered element is created, a `createdCallback` method is called
     * in the scope of the element. The `createdCallback` method can be specified on
     * either `options.prototype` or `options.lifecycle` with the latter taking
     * precedence.
     *
     * @method register
     * @param {String} name The tag name to register. Must include a dash ('-'),
     *    for example 'x-component'.
     * @param {Object} options
     *    @param {String} [options.extends]
     *      (_off spec_) Tag name of an element to extend (or blank for a new
     *      element). This parameter is not part of the specification, but instead
     *      is a hint for the polyfill because the extendee is difficult to infer.
     *      Remember that the input prototype must chain to the extended element's
     *      prototype (or HTMLElement.prototype) regardless of the value of
     *      `extends`.
     *    @param {Object} options.prototype The prototype to use for the new
     *      element. The prototype must inherit from HTMLElement.
     *    @param {Object} [options.lifecycle]
     *      Callbacks that fire at important phases in the life of the custom
     *      element.
     *
     * @example
     *      FancyButton = document.register("fancy-button", {
     *        extends: 'button',
     *        prototype: Object.create(HTMLButtonElement.prototype, {
     *          createdCallback: {
     *            value: function() {
     *              console.log("a fancy-button was created",
     *            }
     *          }
     *        })
     *      });
     * @return {Function} Constructor for the newly registered type.
     */
    function register(name, options) {
      //console.warn('document.register("' + name + '", ', options, ')');
      // construct a defintion out of options
      // TODO(sjmiles): probably should clone options instead of mutating it
      var definition = options || {};
      if (!name) {
        // TODO(sjmiles): replace with more appropriate error (EricB can probably
        // offer guidance)
        throw new Error('document.register: first argument `name` must not be empty');
      }
      if (name.indexOf('-') < 0) {
        // TODO(sjmiles): replace with more appropriate error (EricB can probably
        // offer guidance)
        throw new Error('document.register: first argument (\'name\') must contain a dash (\'-\'). Argument provided was \'' + String(name) + '\'.');
      }
      // elements may only be registered once
      if (getRegisteredDefinition(name)) {
        throw new Error('DuplicateDefinitionError: a type with name \'' + String(name) + '\' is already registered');
      }
       // must have a prototype, default to an extension of HTMLElement
      // TODO(sjmiles): probably should throw if no prototype, check spec
      if (!definition.prototype) {
        // TODO(sjmiles): replace with more appropriate error (EricB can probably
        // offer guidance)
        throw new Error('Options missing required prototype property');
      }
      // record name
      definition.name = name.toLowerCase();
      // ensure a lifecycle object so we don't have to null test it
      definition.lifecycle = definition.lifecycle || {};
      // build a list of ancestral custom elements (for native base detection)
      // TODO(sjmiles): we used to need to store this, but current code only
      // uses it in 'resolveTagName': it should probably be inlined
      definition.ancestry = ancestry(definition['extends']);
      // extensions of native specializations of HTMLElement require localName
      // to remain native, and use secondary 'is' specifier for extension type
      resolveTagName(definition);
      // some platforms require modifications to the user-supplied prototype
      // chain
      resolvePrototypeChain(definition);
      // overrides to implement attributeChanged callback
      overrideAttributeApi(definition.prototype);
      // 7.1.5: Register the DEFINITION with DOCUMENT
      registerDefinition(definition.name, definition);
      // 7.1.7. Run custom element constructor generation algorithm with PROTOTYPE
      // 7.1.8. Return the output of the previous step.
      definition.ctor = generateConstructor(definition);
      definition.ctor.prototype = definition.prototype;
      // force our .constructor to be our actual constructor
      definition.prototype.constructor = definition.ctor;
      // if initial parsing is complete
      scope.addedNode(document);
      return definition.ctor;
    }

    function ancestry(extnds) {
      var extendee = getRegisteredDefinition(extnds);
      if (extendee) {
        return ancestry(extendee['extends']).concat([extendee]);
      }
      return [];
    }

    function resolveTagName(definition) {
      // if we are explicitly extending something, that thing is our
      // baseTag, unless it represents a custom component
      var baseTag = definition['extends'];
      // if our ancestry includes custom components, we only have a
      // baseTag if one of them does
      for (var i=0, a; (a=definition.ancestry[i]); i++) {
        baseTag = a.is && a.tag;
      }
      // our tag is our baseTag, if it exists, and otherwise just our name
      definition.tag = baseTag || definition.name;
      if (baseTag) {
        // if there is a base tag, use secondary 'is' specifier
        definition.is = definition.name;
      }
    }

    function resolvePrototypeChain(definition) {
      // if we don't support __proto__ we need to locate the native level
      // prototype for precise mixing in
      if (!Object.__proto__) {
        // default prototype
        var nativePrototype = HTMLElement.prototype;
        // work out prototype when using type-extension
        if (definition.is) {
          var inst = document.createElement(definition.tag);
          nativePrototype = Object.getPrototypeOf(inst);
        }
        // ensure __proto__ reference is installed at each point on the prototype
        // chain.
        // NOTE: On platforms without __proto__, a mixin strategy is used instead
        // of prototype swizzling. In this case, this generated __proto__ provides
        // limited support for prototype traversal.
        var proto = definition.prototype, ancestor;
        while (proto && (proto !== nativePrototype)) {
          var ancestor = Object.getPrototypeOf(proto);
          proto.__proto__ = ancestor;
          proto = ancestor;
        }
      }
      // cache this in case of mixin
      definition['native'] = nativePrototype;
    }

    // SECTION 4

    function instantiate(definition) {
      // 4.a.1. Create a new object that implements PROTOTYPE
      // 4.a.2. Let ELEMENT by this new object
      //
      // the custom element instantiation algorithm must also ensure that the
      // output is a valid DOM element with the proper wrapper in place.
      //
      return upgrade(domCreateElement(definition.tag), definition);
    }

    function upgrade(element, definition) {
      // some definitions specify an 'is' attribute
      if (definition.is) {
        element.setAttribute('is', definition.is);
      }
      // remove 'unresolved' attr, which is a standin for :unresolved.
      element.removeAttribute('unresolved');
      // make 'element' implement definition.prototype
      implement(element, definition);
      // flag as upgraded
      element.__upgraded__ = true;
      // there should never be a shadow root on element at this point
      // we require child nodes be upgraded before `created`
      scope.addedSubtree(element);
      // lifecycle management
      created(element);
      // OUTPUT
      return element;
    }

    function implement(element, definition) {
      // prototype swizzling is best
      if (Object.__proto__) {
        element.__proto__ = definition.prototype;
      } else {
        // where above we can re-acquire inPrototype via
        // getPrototypeOf(Element), we cannot do so when
        // we use mixin, so we install a magic reference
        customMixin(element, definition.prototype, definition['native']);
        element.__proto__ = definition.prototype;
      }
    }

    function customMixin(inTarget, inSrc, inNative) {
      // TODO(sjmiles): 'used' allows us to only copy the 'youngest' version of
      // any property. This set should be precalculated. We also need to
      // consider this for supporting 'super'.
      var used = {};
      // start with inSrc
      var p = inSrc;
      // sometimes the default is HTMLUnknownElement.prototype instead of
      // HTMLElement.prototype, so we add a test
      // the idea is to avoid mixing in native prototypes, so adding
      // the second test is WLOG
      while (p !== inNative && p !== HTMLUnknownElement.prototype) {
        var keys = Object.getOwnPropertyNames(p);
        for (var i=0, k; k=keys[i]; i++) {
          if (!used[k]) {
            Object.defineProperty(inTarget, k,
                Object.getOwnPropertyDescriptor(p, k));
            used[k] = 1;
          }
        }
        p = Object.getPrototypeOf(p);
      }
    }

    function created(element) {
      // invoke createdCallback
      if (element.createdCallback) {
        element.createdCallback();
      }
    }

    // attribute watching

    function overrideAttributeApi(prototype) {
      // overrides to implement callbacks
      // TODO(sjmiles): should support access via .attributes NamedNodeMap
      // TODO(sjmiles): preserves user defined overrides, if any
      if (prototype.setAttribute._polyfilled) {
        return;
      }
      var setAttribute = prototype.setAttribute;
      prototype.setAttribute = function(name, value) {
        changeAttribute.call(this, name, value, setAttribute);
      }
      var removeAttribute = prototype.removeAttribute;
      prototype.removeAttribute = function(name) {
        changeAttribute.call(this, name, null, removeAttribute);
      }
      prototype.setAttribute._polyfilled = true;
    }

    // https://dvcs.w3.org/hg/webcomponents/raw-file/tip/spec/custom/
    // index.html#dfn-attribute-changed-callback
    function changeAttribute(name, value, operation) {
      var oldValue = this.getAttribute(name);
      operation.apply(this, arguments);
      var newValue = this.getAttribute(name);
      if (this.attributeChangedCallback
          && (newValue !== oldValue)) {
        this.attributeChangedCallback(name, oldValue, newValue);
      }
    }

    // element registry (maps tag names to definitions)

    var registry = {};
    scope.registry = registry;

    function getRegisteredDefinition(name) {
      if (name) {
        return registry[name.toLowerCase()];
      }
    }

    function registerDefinition(name, definition) {
      registry[name] = definition;
    }

    function generateConstructor(definition) {
      return function() {
        return instantiate(definition);
      };
    }

    function createElement(tag, typeExtension) {
      // TODO(sjmiles): ignore 'tag' when using 'typeExtension', we could
      // error check it, or perhaps there should only ever be one argument
      var definition = getRegisteredDefinition(typeExtension || tag);
      if (definition) {
        return new definition.ctor();
      }
      return domCreateElement(tag);
    }

    function upgradeElement(element) {
      if (!element.__upgraded__ && (element.nodeType === Node.ELEMENT_NODE)) {
        var type = element.getAttribute('is') || element.localName;
        var definition = getRegisteredDefinition(type);
        return definition && upgrade(element, definition);
      }
    }

    function cloneNode(deep) {
      // call original clone
      var n = domCloneNode.call(this, deep);
      // upgrade the element and subtree
      addedNode(n);
      // return the clone
      return n;
    }
    // capture native createElement before we override it

    var domCreateElement = document.createElement.bind(document);

    // capture native cloneNode before we override it

    var domCloneNode = Node.prototype.cloneNode;

    // exports

    document.register = register;
    document.createElement = createElement; // override
    Node.prototype.cloneNode = cloneNode; // override
    scope.upgradeElement = upgradeElement;
  }

  (function(scope){

    var logFlags = scope.logFlags;

    /*
    Copyright 2013 The Polymer Authors. All rights reserved.
    Use of this source code is governed by a BSD-style
    license that can be found in the LICENSE file.
    */

    // walk the subtree rooted at node, applying 'find(element, data)' function
    // to each element
    // if 'find' returns true for 'element', do not search element's subtree
    function findAll(node, find, data) {
      var e = node.firstElementChild;
      if (!e) {
        e = node.firstChild;
        while (e && e.nodeType !== Node.ELEMENT_NODE) {
          e = e.nextSibling;
        }
      }
      while (e) {
        if (find(e, data) !== true) {
          findAll(e, find, data);
        }
        e = e.nextElementSibling;
      }
      return null;
    }

    // walk the subtree rooted at node, including descent into shadow-roots,
    // applying 'cb' to each element
    function forSubtree(node, cb) {
      //logFlags.dom && node.childNodes && node.childNodes.length && console.group('subTree: ', node);
      findAll(node, function(e) {
        if (cb(e)) {
          return true;
        }
      });
      //logFlags.dom && node.childNodes && node.childNodes.length && console.groupEnd();
    }

    // manage lifecycle on added node
    function added(node) {
      if (upgrade(node)) {
        insertedNode(node);
        return true;
      }
      inserted(node);
    }

    // manage lifecycle on added node's subtree only
    function addedSubtree(node) {
      forSubtree(node, function(e) {
        if (added(e)) {
          return true;
        }
      });
    }

    // manage lifecycle on added node and it's subtree
    function addedNode(node) {
      return added(node) || addedSubtree(node);
    }

    // upgrade custom elements at node, if applicable
    function upgrade(node) {
      if (!node.__upgraded__ && node.nodeType === Node.ELEMENT_NODE) {
        var type = node.getAttribute('is') || node.localName;
        var definition = scope.registry[type];
        if (definition) {
          logFlags.dom && console.group('upgrade:', node.localName);
          scope.upgradeElement(node);
          logFlags.dom && console.groupEnd();
          return true;
        }
      }
    }

    function insertedNode(node) {
      inserted(node);
      if (inDocument(node)) {
        forSubtree(node, function(e) {
          inserted(e);
        });
      }
    }

    // TODO(sorvell): on platforms without MutationObserver, mutations may not be 
    // reliable and therefore entered/leftView are not reliable.
    // To make these callbacks less likely to fail, we defer all inserts and removes
    // to give a chance for elements to be inserted into dom. 
    // This ensures enteredViewCallback fires for elements that are created and 
    // immediately added to dom.
    var hasPolyfillMutations = (window.MutationObserver === window.MutationObserverPolyfill);

    var isPendingMutations = false;
    var pendingMutations = [];
    function deferMutation(fn) {
      pendingMutations.push(fn);
      if (!isPendingMutations) {
        isPendingMutations = true;
        var async = (window.Platform && window.Platform.endOfMicrotask) ||
            setTimeout;
        async(takeMutations);
      }
    }

    function takeMutations() {
      isPendingMutations = false;
      var $p = pendingMutations;
      for (var i=0, l=$p.length, p; (i<l) && (p=$p[i]); i++) {
        p();
      }
      pendingMutations = [];
    }

    function inserted(element) {
      if (hasPolyfillMutations) {
        deferMutation(function() {
          _inserted(element);
        });
      } else {
        _inserted(element);
      }
    }

    // TODO(sjmiles): if there are descents into trees that can never have inDocument(*) true, fix this
    function _inserted(element) {
      // TODO(sjmiles): it's possible we were inserted and removed in the space
      // of one microtask, in which case we won't be 'inDocument' here
      // But there are other cases where we are testing for inserted without
      // specific knowledge of mutations, and must test 'inDocument' to determine
      // whether to call inserted
      // If we can factor these cases into separate code paths we can have
      // better diagnostics.
      // TODO(sjmiles): when logging, do work on all custom elements so we can
      // track behavior even when callbacks not defined
      //console.log('inserted: ', element.localName);
      if (element.enteredViewCallback || (element.__upgraded__ && logFlags.dom)) {
        logFlags.dom && console.group('inserted:', element.localName);
        if (inDocument(element)) {
          element.__inserted = (element.__inserted || 0) + 1;
          // if we are in a 'removed' state, bluntly adjust to an 'inserted' state
          if (element.__inserted < 1) {
            element.__inserted = 1;
          }
          // if we are 'over inserted', squelch the callback
          if (element.__inserted > 1) {
            logFlags.dom && console.warn('inserted:', element.localName,
              'insert/remove count:', element.__inserted)
          } else if (element.enteredViewCallback) {
            logFlags.dom && console.log('inserted:', element.localName);
            element.enteredViewCallback();
          }
        }
        logFlags.dom && console.groupEnd();
      }
    }

    function removedNode(node) {
      removed(node);
      forSubtree(node, function(e) {
        removed(e);
      });
    }

    function removed(element) {
      if (hasPolyfillMutations) {
        deferMutation(function() {
          _removed(element);
        });
      } else {
        _removed(element);
      }
    }

    function _removed(element) {
      // TODO(sjmiles): temporary: do work on all custom elements so we can track
      // behavior even when callbacks not defined
      if (element.leftViewCallback || (element.__upgraded__ && logFlags.dom)) {
        logFlags.dom && console.log('removed:', element.localName);
        if (!inDocument(element)) {
          element.__inserted = (element.__inserted || 0) - 1;
          // if we are in a 'inserted' state, bluntly adjust to an 'removed' state
          if (element.__inserted > 0) {
            element.__inserted = 0;
          }
          // if we are 'over removed', squelch the callback
          if (element.__inserted < 0) {
            logFlags.dom && console.warn('removed:', element.localName,
                'insert/remove count:', element.__inserted)
          } else if (element.leftViewCallback) {
            element.leftViewCallback();
          }
        }
      }
    }

    function inDocument(element) {
      var p = element;
      var doc = document;
      while (p) {
        if (p == doc) {
          return true;
        }
        p = p.parentNode || p.host;
      }
    }

    function handler(mutations) {
      //
      if (logFlags.dom) {
        var mx = mutations[0];
        if (mx && mx.type === 'childList' && mx.addedNodes) {
            if (mx.addedNodes) {
              var d = mx.addedNodes[0];
              while (d && d !== document && !d.host) {
                d = d.parentNode;
              }
              var u = d && (d.URL || d._URL || (d.host && d.host.localName)) || '';
              u = u.split('/?').shift().split('/').pop();
            }
        }
        console.group('mutations (%d) [%s]', mutations.length, u || '');
      }
      //
      mutations.forEach(function(mx) {
        //logFlags.dom && console.group('mutation');
        if (mx.type === 'childList') {
          forEach(mx.addedNodes, function(n) {
            //logFlags.dom && console.log(n.localName);
            if (!n.localName) {
              return;
            }
            // nodes added may need lifecycle management
            addedNode(n);
          });
          // removed nodes may need lifecycle management
          forEach(mx.removedNodes, function(n) {
            //logFlags.dom && console.log(n.localName);
            if (!n.localName) {
              return;
            }
            removedNode(n);
          });
        }
        //logFlags.dom && console.groupEnd();
      });
      logFlags.dom && console.groupEnd();
    };

    var observer = new MutationObserver(handler);

    var forEach = Array.prototype.forEach.call.bind(Array.prototype.forEach);

    function observeDocument() {
      observer.observe(document, {childList: true, subtree: true});
    }

    function upgradeDocument() {
      logFlags.dom && console.group('upgradeDocument: ', (document.URL || document._URL || '').split('/').pop());
      addedNode(document);
      logFlags.dom && console.groupEnd();
    }

    // export
    scope.addedNode = addedNode;
    scope.addedSubtree = addedSubtree;

    /*
     * Copyright 2013 The Polymer Authors. All rights reserved.
     * Use of this source code is governed by a BSD-style
     * license that can be found in the LICENSE file.
     */
    // observe document for dom changes
    observeDocument();

    window.addEventListener('DOMContentLoaded', function() {
      upgradeDocument();
    });
  })(scope);

})();