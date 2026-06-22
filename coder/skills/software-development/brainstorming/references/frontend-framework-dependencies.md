# Frontend Framework Dependencies — Design-Time Verification

**Discovered:** 2026-06-16, cash account tagging planning. A plan task was drafted using `data-bs-toggle="dropdown"` (Bootstrap dropdowns) on a page where base.html loads Bootstrap **CSS only** — no JS bundle. The pattern failed silently; the fix was plain click-to-toggle divs with custom JS.

## Pattern: Verify which framework assets are actually loaded

When designing any UI feature that uses framework components (Bootstrap, Alpine.js, Chart.js, HTMX interactions), you MUST check `base.html` (or equivalent layout template) for what is actually available — not just what is linked in the HTML `<head>`.

### Checklist

1. **CSS only vs CSS+JS** — Bootstrap, Tailwind, etc. often ship as separate bundles. Loading the stylesheet does NOT enable interactive components (`data-bs-toggle`, modals, dropdowns, tooltips). Verify by searching `base.html` for `<script src="...bootstrap">` or equivalent JS import.
2. **CDN version pinning** — If a CDN is used (e.g., Chart.js, Alpine.js), verify the version matches what you're coding against. A mismatch between expected and actual API surface causes silent failures.
3. **Defer/async on scripts** — Scripts loaded with `defer` or `async` may not be ready when inline scripts execute. Check `<script defer src="...">` vs bare `<script>` ordering. In this project, Chart.js is loaded via `{% block extra_head %}` in the template itself (not in base), so any new page that needs it must include the script tag explicitly.
4. **Alpine.js `x-data` scope** — Alpine components are scoped to their DOM tree. If a script initializes Alpine data outside the component's element, bindings won't work. Prefer placing `x-data` on the root container of each page's content block.

### Pitfall: Assuming framework features are available because they're "part of the stack"

A framework can be in the project without being loaded everywhere. Example: Bootstrap CSS is linked globally but Bootstrap JS is only loaded (if at all) per-page, or not at all. Coding against Bootstrap interactive components on a page that lacks the JS bundle produces pages that look correct but are completely non-interactive.

**Fix:** Before writing any UI task that depends on framework interactivity, grep `base.html` for script imports. If the needed JS is absent, use either (a) a vanilla JS fallback, or (b) explicitly include the JS in `{% block extra_head %}` / `{% block extra_scripts %}`.

### Reference: this project's base.html asset map

| Asset | Loaded? | Where |
|-------|---------|-------|
| Bootstrap 5 CSS | Yes (CDN) | `base.html` `<link>` |
| Bootstrap 5 JS | **No** | Not in base.html — use vanilla JS or include explicitly |
| FontAwesome 6 | Yes (CDN) | `base.html` `<link>` |
| HTMX 2.x | Yes (CDN) | `base.html` `<script>` |
| Alpine.js | Yes (local, no defer) | `base.html` `<script src="/static/js/alpine.min.js">` at end of body |
| Chart.js | Per-page | `{% block extra_head %}` in templates that need it |
