# Alpine.js Diagnostic Workflow

## Quick diagnostic checklist

When Alpine components aren't rendering (page looks static, `x-show`/`x-text` etc. have no effect):

```javascript
// 1. Is Alpine loaded at all?
typeof Alpine;                 // should be "object" (not "undefined")
Alpine.version;                // should be e.g. "3.14.8"

// 2. Did Alpine's init complete?
document.querySelector('html').getAttribute('data-alpine');  // should be truthy

// 3. Does the component element have Alpine's internal marker?
var el = document.querySelector('[x-data="importWizard()"]');
el._x_marker;                  // number > 0 means Alpine scanned it
el._x_dataStack;               // Array — component data lives at [0] if wired

// 4. Is the component data accessible?
el._x_dataStack[0].step;       // should be "upload" etc.
```

## Key fact about Alpine 3.14.8 CDN builds

**`__x` is NOT set on elements.** The commonly-documented `el.__x.$data` accessor does not exist in this build. Component state lives in `el._x_dataStack[0]` instead.

## Race condition triage

If components are broken (step 3 shows `_x_marker` set but no `_x_dataStack`):

1. Check the `x-data` expression — does it reference a function that might not be globally defined?
   ```html
   <!-- Check for undefined function references -->
   <body x-data="pfinApp()">  <!-- if pfinApp not defined → full tree failure -->
   ```
2. Check if the component function is defined in an inline `<script>` that might not have run before Alpine scanned. The inline script runs at parse time, Alpine (defer) runs after parsing — but CDN latency can cause ordering issues.
3. Check `typeof myComponentFunction` — if it's `"function"` now but components still broken, Alpine already failed during its initial scan and won't retry. The element has `_x_marker` set from the failed attempt.

## Remote CDP debugging flow

Using Hermes' `browser_cdp` with `Runtime.evaluate`:

```javascript
// Navigate first, then inspect on the right target
browser_cdp(method="Target.getTargets")
// Find the page target (type: "page", url: your app)

// Evaluate in that target
browser_cdp(
  target_id="...",
  method="Runtime.evaluate",
  params={expression: "document.querySelector('[x-data]').outerHTML.substring(0,200)", returnByValue: true}
)

// Check Alpine internal state
browser_cdp(
  target_id="...",
  method="Runtime.evaluate",
  params={expression: "var el = document.querySelector('[x-data]'); ({marker: el._x_marker, hasDataStack: !!el._x_dataStack, dataKeys: el._x_dataStack ? Object.keys(el._x_dataStack[0]) : []})", returnByValue: true}
)
```

**Gotcha with `let` in CDP evaluate:** The CDP sandbox re-uses the same global scope for `Runtime.evaluate`. A `let e = ...` expression in one call causes `SyntaxError: Identifier 'e' has already been declared` on the next call. Use `var` instead.

## Fix strategies (in order of reliability)

| Strategy | Reliability | Caveat |
|----------|-------------|--------|
| Inline object `x-data="{ step: 'upload', ... }"` | 100% | Verbose for complex components |
| Serve Alpine locally, no defer | 99% | ~45KB download, no CDN caching |
| `Alpine.data()` registration in `alpine:init` | 95% | Must fire before Alpine scans |
| Global function + CDN with defer | 60% | Race condition on slow connections |

## Known Alpine 3.x rendering limitations

| Context | Works? | Notes |
|---------|--------|-------|
| `<div x-for>` | ✅ | Native block container |
| `<ul>/<ol>` with `<template x-for>` | ✅ | Works, renders `<li>` correctly |
| `<tbody>` with `<template x-for>` | ❌ | Alpine's comment-anchor approach fails inside `<tbody>` — browser strips comment nodes between `<tr>` elements. Use manual DOM rendering instead (see `SKILL.md` pitfall section). |
| `<thead>` / `<tfoot>` with `<template x-for>` | ❌ | Same root cause as `<tbody>` — HTML spec restricts child types |
| `<tr>` with `x-for` directly | ❌ | Alpine v3 doesn't support `x-for` on elements that can't wrap their own comment anchors |

When rendering tabular data from an Alpine component, always build `<tr>` elements via plain JavaScript (`document.createElement('tr')` / `innerHTML`). Do NOT attempt `<template x-for>` inside table section elements.
