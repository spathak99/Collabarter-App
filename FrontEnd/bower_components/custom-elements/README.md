# Custom Elements #

Custom elements are a part of the [W3C Web Components](http://w3c.github.io/webcomponents/explainer/) specification ([see spec](http://w3c.github.io/webcomponents/spec/custom/)). They allow you to define and register new HTML tags/elements in your documents. You can then use these tags as regular HTML.

This library polyfills the Custom Elements API on browsers today. It is a barebones fork of the [X-Tag core library](https://github.com/x-tag/core) from Mozilla ([see website](http://x-tags.org/)). X-Tags in turn uses the [Polymer](https://github.com/Polymer/polymer) polyfills from Google ([see website](http://www.polymer-project.org/)).

The aim of this fork is to provide a stripped down version of the above polyfills, with zero additional weight.

## What’s included? ##

There are two source files in the repository:

- `CustomElements.js`, which polyfills the W3C Web Components Custom Elements API.
- `MutationObserver.js`, which polyfills the [MutationObserver](https://developer.mozilla.org/en/docs/Web/API/MutationObserver) API. This is needed for the CustomElements polyfill and additionally polyfills the [WeakMap](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakMap) API.

Each of these files are minified for distributions (see the `dist` directory).

## How do I use it? ##

Including `CustomElements.js` (`CustomElements.min.js`) in your source will polyfill the Custom Elements API.

For browsers that already support CustomMutations, it is not necessary to include `CustomMutations.js` (`CustomMutations.min.js`), although it will do no harm if you do (apart from possibly polyfilling the WeakMap API unecessarily). The CustomMutations polyfill must be included before the CustomElement polyfill:

    <script type="text/javascript" src="./MutationObserver.min.js"></script>
    <script type="text/javascript" src="./CustomElements.min.js"></script>

Sample code is located in the `example` directory. An introduction to the Custom Elements API (with code examples) is [available on](http://www.html5rocks.com/en/tutorials/webcomponents/customelements/) the HTML5 Rocks website from Google.

## Licensing ##

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

Thanks to [Arron Schaar](https://github.com/pennyfx) and [Daniel Buchner](https://github.com/csuwildcat) of Mozilla for their help.
