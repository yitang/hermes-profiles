# HTML esc() Missing Single-Quote Escape in onclick Handlers

## The Bug

When embedding user-controlled data into JavaScript strings inside HTML `onclick` attributes, the `esc()` function must escape single quotes (`'`) — otherwise a crafted input like `'; alert(1) /*` breaks out of the string literal.

```html
<!-- XSS VULNERABLE if esc() doesn't escape ' -->
onclick="removeTag('hash','person','<user_name>')"
<!-- If user_name = '; alert(1) /*, browser executes: removeTag('hash','person','; alert(1) /*') -->
```

## The Fix

Add single-quote escaping to the esc() function:

```javascript
function esc(s) {
  return String(s || '')
    .replace(/&/g,'&amp;')
    .replace(/'/g, '&#39;')       // ← must come BEFORE & replacement if using &amp;
    .replace(/"/g,'&quot;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;');
}
```

## Order Matters

If escaping `&` to `&amp;` comes before `'`, then `&#39;` in the replacement won't cause issues because the replacement string is literal (not user input). But be aware: if esc() ever processes its own output (e.g., nested escapes), double-escaping `&` could produce `&amp;amp;`.

## When to Check

- Code quality review for any Jinja/HTML template with inline onclick handlers
- Any pattern like `onclick="func(''" + esc(variable) + "')" ` in JavaScript embedded in templates
- Frontend code that embeds user data in JavaScript strings (not just text content)

## Note

This is NOT a Jinja2 `{% autoescape %}` issue — it's about values rendered into JavaScript string literals inside HTML attributes. Autoescape handles HTML entity encoding but doesn't escape `'` for JS context.
