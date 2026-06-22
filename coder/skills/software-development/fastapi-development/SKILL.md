---
name: fastapi-development
description: "Build FastAPI web apps with HTMX, SQLAlchemy async, Jinja2, and Chart.js. Covers project setup, test patterns, template rendering gotchas, and deployment quirks specific to this user's setup."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [fastapi, python, web, htmx, sqlalchemy, testing]
    related_skills: [brainstorming, writing-plans, test-driven-development]
---

# FastAPI Development

Patterns, gotchas, and conventions for building FastAPI web applications in this environment.

## Project Setup

### pyproject.toml
Use `setuptools.build_meta` as build-backend (NOT `setuptools.backends._legacy`):

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

### Project Structure
```
project/
├── pyproject.toml
├── pkgname/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── *.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── *.py
│   ├── templates/
│   └── static/
└── tests/
    ├── __init__.py
    └── *.py
```

## Application Factory Pattern

### ⚠ `create_app()` factory with module-level state + async dependencies

When using a **factory function** (e.g. `create_app()`) that sets module-level singleton state inside a lifespan context manager, and route handler dependencies read that same state, the value can be `None` at runtime even though the lifespan ran successfully.

**Root cause:** The lifespan context manager sets `_ctx_db` via `global _ctx_db`, but when an async dependency (`get_db()`) accesses the module-level variable without declaring `global`, it reads from its own local scope closure, which doesn't see the mutated global. This is a subtle Python scoping issue that only manifests in async route handlers (not sync ones).

**Symptoms:**
- App starts successfully — "Application startup complete" message appears
- Sync endpoints work fine (or the app never reaches them)
- Async endpoint dependencies raise `AssertionError: Database not configured` or similar
- The same code works in tests with `TestClient` (sync context) but fails under uvicorn

**Fix — lazy-initialise the dependency function:**

```python
# WRONG — asserts that lifespan already ran
_ctx_db: Database | None = None

def get_db() -> Database:
    assert _ctx_db is not None, "Database not configured"
    return _ctx_db

# CORRECT — falls back to lazy initialisation if lifespan didn't set it
_ctx_db: Database | None = None

def get_db() -> Database:
    global _ctx_db
    if _ctx_db is None:
        _ctx_db = Database(_default_db_path())
        init_db(_ctx_db)
    return _ctx_db
```

**When the factory pattern is unavoidable** (tests pass `test_db` parameter, live server uses default), ensure EVERY module-level singleton accessed from route handlers has this lazy-initialisation guard.

**Alternative: avoid module-level state entirely.** Pass app state via `app.state` instead of globals:

```python
# In create_app():
app.state.db = Database(_default_db_path())
init_db(app.state.db)

# In dependency:
def get_db(request: Request) -> Database:
    return request.app.state.db
```

This completely avoids the scoping issue because `request` is passed explicitly to every dependency.

## Jinja2 Templates

### TemplateResponse Requires Keyword Args
FastAPI 0.136.3 / Starlette 1.2.1 — the signature is `(self, request, name, context, ...)`.
**Always use keyword arguments:**
```python
return templates.TemplateResponse(
    request=request,
    name="template.html",
    context={"key": "value"},
)
```
Positional calls map the template name string to the `request` parameter and the context dict to the `name` parameter, causing a hard-to-debug `TypeError: unhashable type: 'dict'` in Jinja2's LRUCache.

### Jinja2 3.1.6 Cache Bug
Do NOT set `templates.env.cache = None`. It causes `TypeError: unhashable type: 'dict'` in `LRUCache.__getitem__`. Just leave the default cache enabled.

## Report Endpoints with Chart.js

### Python Dict → JavaScript Chart Data
When embedding Chart.js data in templates, the `{{ chart_data|safe }}` filter renders Python `str()` format (`{'fill': True}`), not valid JavaScript (`{"fill": true}`).  
**Always JSON-serialize in the router:**
```python
import json

chart_data = {"labels": [...], "datasets": [...]}
# Pass as JSON string:
context = {"chart_data": json.dumps(chart_data)}
```
Then in the template:
```html
<script>
var data = {{ chart_data|safe }};
new Chart(ctx, { type: 'line', data: data });
</script>
```

### ⚠ Pitfall — Jinja conditions on JSON-stringified data
When you pass `json.dumps(chart_data)` to the template context, it becomes a **string** in Jinja's view. Do NOT write:
```python
# DON'T — chart_data is a string, not a dict
context = {"chart_data": json.dumps(chart_data)}
```
```html
{# Jinja treats chart_data as a string — .labels is always falsy #}
{% if chart_data.labels %}
  <canvas id="chart"></canvas>
{% endif %}
```
The condition `{% if chart_data.labels %}` accesses `.labels` on a Python string, which is always undefined/falsy in Jinja. The chart never renders even though the data is correctly embedded in the JavaScript.

**Fix:** Check a separate Python-native variable instead:
```python
context = {
    "chart_data": json.dumps(chart_data),  # for the JS script tag
    "labels": labels,                        # for Jinja conditions
}
```
```html
{% if labels %}       {# ✅ works — labels is a list #}
  <canvas id="chart"></canvas>
  <script>
    var data = {{ chart_data|safe }};  # ✅ JSON for JS
  </script>
{% endif %}
```
This pattern keeps the JSON string for JavaScript consumption and the native Python list for template control flow — never mix the two roles.

### Chart.js Canvas Height
The HTML `height` attribute sets the canvas coordinate space, not the CSS display size.  
**Use CSS style for visible height:**
```html
<canvas id="chart" style="max-height:450px;"></canvas>
```

### ⚠ Pitfall — Chart.js Not Loading on New Pages That Extend base.html

When `dashboard.html` loads Chart.js via a `<script>` tag inline (not in `base.html`), any NEW page template that extends `base.html` and includes a chart will silently fail — Chart is `undefined`. The CDN is only loaded on the dashboard, not globally.

**Detection:** Open the page, check browser console for `Uncaught ReferenceError: Chart is not defined`.

**Fix — two options:**

**A. Use the `extra_head` block** (preferred, non-invasive):
```html
{% extends "base.html" %}
{% block extra_head %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
{% endblock %}
```
Only add this if `base.html` actually defines `{% block extra_head %}{% endblock %}` in its `<head>`. Check with `grep 'block.*head' base.html` before using. The block name may vary (`head_extra`, `extra_head`, `head_scripts`). If none exists, add one to `base.html` first, or use option B.

**B. Add the script tag in the content block itself** — less clean but always works:
```html
{% block content %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<!-- rest of page -->
{% endblock %}
```

### ⚠ Pitfall — `maintainAspectRatio: false` causes vertical stretch

When Chart.js is loaded via a `<script defer>` tag in the base template, it executes after the DOM is parsed but **before `DOMContentLoaded` fires**. Inline `<script>` blocks in child templates that call `new Chart(ctx, ...)` or `ctx.getContext('2d')` run **synchronously at parse time** — before `defer`'d scripts have finished loading.

If Chart.js hasn't finished evaluating when the inline script runs, `Chart` is `undefined` and the chart silently fails (no error visible to the user, just a blank canvas).

**Root cause chain:**
- `base.html` has `<script defer src="chart.js">` — this defers execution until after DOM parsing, which means Chart.js evaluation races with inline scripts in child templates
- Child template has `<script>const ctx = doc.getElementById('chart').getContext('2d'); new Chart(ctx, ...)</script>` — this runs immediately when the parser hits it, potentially before Chart.js is defined
- The `getContext('2d')` call succeeds (the canvas exists), but `Chart` is undefined

**Fix — always wrap chart initialization in DOMContentLoaded:**
```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {{ chart_data|safe }},
        options: { ... }
    });
});
</script>
```

This guarantees Chart.js has finished loading (defer'd scripts complete before DOMContentLoaded fires). The net worth template already had this pattern correct; the cashflow and spending templates did not.

**Checklist when adding a new chart template:** verify the chart script is wrapped in `DOMContentLoaded`. If it's not, it will randomly fail depending on CDN timing.

### ⚠ Pitfall — `maintainAspectRatio: false` causes vertical stretch
When a Chart.js chart has `responsive: true` (the default) and `maintainAspectRatio: false`, Chart.js overrides the CSS height and computes the canvas height from the parent container. If the parent card has no constrained height (e.g. `min-height` or `max-height`), the chart stretches vertically without bound — it can become very tall and unusable.

**Fix:** One of:
- Set `maintainAspectRatio: true` (default) — the canvas respects the inline `height` style and scales width responsively.
- Keep `maintainAspectRatio: false` but constrain the parent container with `max-height: 400px` or similar CSS.
- Keep `maintainAspectRatio: false` and set a fixed CSS `height` on the `<canvas>` element itself.

Best practice for most report charts: `maintainAspectRatio: true` with a sensible inline `height` (e.g. 300-400px). Only use `false` if the chart must grow/shrink with a genuinely constrained parent container.

## Alpine.js in Jinja2 Templates

### ⚠ Pitfall — `x-data="undefinedFunction()"` breaks Alpine entirely

When `<body x-data="undefinedFunction()">` references a function that doesn't exist, Alpine 3.14.8 silently swallows the ReferenceError during its initial DOM scan. Crucially, Alpine marks the component as broken and **prevents ALL child components from initialising**, not just the broken one. Every `x-data` deeper in the DOM silently fails.

**Always use inline objects for root-level Alpine data** unless the function is guaranteed to be in global scope before Alpine runs:

```html
<!-- ✅ SAFE — inline object, no function reference needed -->
<body x-data="{ sidebarOpen: true }">

<!-- ❌ BROKEN — pfinApp() must be globally defined BEFORE Alpine scans -->
<body x-data="pfinApp()">
```

### ⚠ Pitfall — Alpine CDN `defer` race with inline component function definitions

Alpine loaded via `<script defer>` executes after the DOM is fully parsed. Its internal scanner then evaluates every `x-data="myFunc()"` attribute — but if `myFunc` is defined in an inline `<script>` tag at the end of `<body>`, it may or may not be in scope depending on timing between the defer execution and the inline script.

The inline `function myFunc()` runs synchronously during HTML parsing. Alpine (defer'd) runs after parsing. So in theory the function should exist. **In practice**, browser caching and CDN latency can cause Alpine to execute before the inline script, or the browser's defer queue may interleave execution in unexpected ways. This is a known gotcha with Alpine 3.x CDN usage.

**Best practices to avoid the race:**

1. **Serve Alpine locally (no defer)** — download Alpine to `static/js/alpine.min.js` and include it as a regular synchronous script at the bottom of `<body>`:
   ```html
   <script src="/static/js/alpine.min.js"></script>
   ```
   This guarantees all inline scripts have already parsed and executed before Alpine runs.

2. **Use `Alpine.data()` registration** — register components in an `alpine:init` listener:
   ```html
   <script>
     document.addEventListener('alpine:init', () => {
       Alpine.data('importWizard', () => ({
         step: 'upload',
         handleFile(evt) { ... },
         // ...
       }));
     });
   </script>
   ```
   Then use `x-data="importWizard"` (no parentheses) in the template — Alpine resolves registered names differently from global function calls.

3. **Use inline objects** — simplest and most reliable:
   ```html
   <div x-data="{ step: 'upload', handleFile(evt) { ... }, ... }">
   ```
   No external function dependency at all.

### ⚠ Pitfall — API response format mismatch (array vs wrapped object)

A common inconsistency: some endpoints return a JSON array directly (e.g. `GET /api/transactions` → `[{...}]`) while others return a wrapped object (e.g. search endpoints → `{"transactions": [...]}`).

The frontend auto-load script may check `data.transactions` but if the endpoint returns a bare array, the condition fails silently:

```javascript
// Broken — /api/transactions returns [], not {transactions: []}
fetch('/api/transactions').then(r => r.json()).then(data => {
    if (data && data.transactions) renderTable(data.transactions);
});

// Fixed — handle both formats
fetch('/api/transactions').then(r => r.json()).then(data => {
    if (Array.isArray(data)) renderTable(data);
    else if (data && data.transactions) renderTable(data.transactions);
});
```

**Design rule:** keep list and search endpoint response formats consistent. If search returns `{"transactions": [...]}`, the simple list endpoint should too. Or always wrap — bare arrays are brittle when frontend patterns evolve.

### ⚠ Pitfall — `x-for` inside `<tbody>` doesn't render

**Alpine 3.14.8's `<template x-for>` silently fails to render inside a `<tbody>` element.** Alpine uses comment nodes as anchors for the loop and inserts cloned elements between them. Inside `<tbody>`, browsers don't reliably handle comment nodes or loose text nodes between `<tr>` elements — they get stripped or ignored during HTML parsing, and the rendered `<tr>` elements never appear in the DOM.

**Symptoms:** The preview panel shows a row count (e.g. "Preview (635 rows)"), the component data has `previewRows` correctly populated, but the table body is empty (0 `<tr>` elements in the DOM). No console errors.

**Fix:** Replace `<template x-for>` inside `<tbody>` with manual DOM rendering in JavaScript:

```html
<!-- ❌ DOES NOT WORK — Alpine's comment anchors stripped inside tbody -->
<tbody>
  <template x-for="row in rows" :key="row.id">
    <tr>
      <td x-text="row.date"></td>
      <td x-text="row.amount"></td>
    </tr>
  </template>
</tbody>

<!-- ✅ WORKS — manual DOM rendering -->
<tbody id="table-body"></tbody>
```
```javascript
// After setting component data, render rows directly:
const tbody = document.getElementById('table-body');
tbody.innerHTML = '';
for (const row of this.rows) {
  const tr = document.createElement('tr');
  tr.innerHTML = '<td>' + row.date + '</td><td>' + this.fmt(row.amount) + '</td>';
  tbody.appendChild(tr);
}
```

**Does `x-for` work anywhere else?** Yes — `<template x-for>` works correctly in `<div>`, `<ul>`/`<ol>`, `<span>`, and most other block/inline containers. The issue is specific to `<tbody>` and potentially `<thead>`/`<tfoot>` where the HTML spec restricts child element types.

### Debugging Alpine components via CDP

When Alpine components appear not to render (visible in accessibility tree but not wired up):

```javascript
// Check if Alpine loaded at all
typeof Alpine;  // should be "object", not "undefined"

// Check component data — in Alpine 3.14.8, __x.$data may not exist
// Data lives in _x_dataStack[0] instead:
var el = document.querySelector('[x-data="importWizard()"]');
el._x_dataStack[0].step;  // "upload" — component IS working

// Check if element has Alpine's internal marker
el._x_marker;  // number > 0 means Alpine scanned it
```

**In Alpine 3.14.8 CDN builds, `__x` is NOT set on the element.** Component data is in `_x_dataStack[0]` on the element itself. Do not check for `__x.$data` to determine if a component initialised — use `_x_dataStack` instead.

### Debugging reference

See `references/alpine-debugging.md` for a full diagnostic workflow — triage checklist, CDP inspection commands, fix-strategy comparison table, and the `_x_marker` / `_x_dataStack` inspection flow used in this session.

## User Conventions

### Frontend Aesthetic

This user prefers **Bootstrap 5 + FontAwesome** over custom dark CSS for frontend projects. They value visual polish and professional appearance even for personal/internal tools. When building UIs, default to:
- Bootstrap 5.3 via CDN for layout/components
- FontAwesome 6 via CDN for icons
- Alpine.js for reactive state (sidebar, form wizards)
- Chart.js for data visualisation
- HTMX for interactive updates (form submissions, partial page swaps)

Avoid custom CSS-only dark themes or emoji-as-icon patterns unless explicitly requested. The user has explicitly rejected the dark custom CSS approach in favour of Bootstrap-light with FontAwesome.

## Database (Async SQLAlchemy)

### Lazy Engine Creation
Module-level engine creation captures `settings.database_url` at import time, making test DB configuration impossible.  
**Create engine on demand:**
```python
def get_engine():
    return create_async_engine(settings.database_url, echo=False)

async def get_db():
    engine = get_engine()
    async with async_sessionmaker(engine) as session:
        try:
            yield session
        finally:
            await engine.dispose()

async def init_db():
    import pkgname.models  # noqa: F401
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
```

### Import Models Before create_all
The models must be imported before `Base.metadata.create_all` runs, otherwise no tables are created. Import inside `init_db()` to ensure they register:
```python
async def init_db():
    import pkgname.models  # noqa: F401
    # now create_all will find the models
```

## Testing

### Use Starlette TestClient (NOT httpx)
`httpx.AsyncClient(transport=ASGITransport(app=app))` does NOT trigger FastAPI lifespan events. The `init_db()` call in the lifespan never runs.  
**Use Starlette TestClient instead:**
```python
from starlette.testclient import TestClient

# In conftest.py:
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# In tests (synchronous):
def test_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
```

### Test DB Isolation
Use a temp file database per test session to prevent data leaking between tests:
```python
@pytest.fixture(scope="session", autouse=True)
def test_db():
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    settings.database_url = f"sqlite+aiosqlite:///{tmp.name}"
    yield
    import os
    os.unlink(tmp.name)
```

### ⚠ In-Memory SQLite Fixture with Shared DB Reference

When tests need BOTH a `TestClient` (which creates the app in a fixture) AND direct ORM access to the same DB instance, use a module-level list to keep the DB alive across fixtures. This is required because FastAPI's factory pattern creates the app with a test DB that must persist beyond the `client` fixture scope.

**Pattern** — put in your test file (e.g. `tests/test_bug_fixes.py`):
```python
_fixture_dbs = []  # keeps DB references alive across fixtures

@pytest.fixture()
def client():
    """TestClient with fresh in-memory DB & auto-login."""
    from pfin_api.__init__ import create_app, get_optional_user

    tdb = _make_test_db()  # Database.__new__(Database), assigns _engine
    _fixture_dbs.append(tdb)  # KEEP reference alive
    app = create_app(test_db=tdb)

    async def _fake_user():
        return {"user_id": "test", "email": "test@example.com"}

    app.dependency_overrides[get_optional_user] = _fake_user
    with TestClient(app) as tc:
        yield tc

@pytest.fixture()
def test_db():
    """Return the DB used by the client fixture (shared reference)."""
    if _fixture_dbs:
        return _fixture_dbs[-1]
    raise RuntimeError("No test DB — run 'client' fixture first")
```

**Why this works:** `Database.__new__(Database)` bypasses `__init__` to avoid creating a real engine. Then we assign `db._engine = engine` directly. The `_fixture_dbs.append(tdb)` prevents garbage collection of the DB between test steps that need both the HTTP client and ORM access.

**Key gotchas:**
- **Must use `Database.__new__(Database)`** — never call `Database()` constructor in tests; it tries to connect to a real file.
- **Call `init_db(db)` after assigning `_engine`** — creates tables on the engine.
- **Append to list, don't overwrite** — if you only store the last DB, earlier fixture-created DBs get garbage collected while still referenced by route handlers.

### ⚠ API Endpoint ≠ Web Route: Check the Right One for Assertions

FastAPI apps typically have BOTH an API endpoint (`/api/...`) and a web route (`/...`). The API returns JSON with a specific schema; the web route renders HTML and computes additional values not present in the API response.

**Common divergence:**
| Endpoint | Returns | Missing from API |
|----------|---------|-----------------|
| `GET /api/dashboard` | `{net_worth, accounts_count, recent_transactions, top_categories, monthly_cashflow}` | No `month_expense`, no portfolio summary |
| `GET /` (web) | HTML with Jinja2 template | Uses computed `month_expense`, `portfolio_summary`, etc. that the API does not expose |

**Test implications:**
```python
# ✅ Check month_expense — only exists in web route
r = client.get("/")  # NOT client.get("/api/dashboard")
assert "£50" in r.text, f"month_expense wrong: expected ~50, got HTML={r.text[:500]}"

# ❌ BROKEN — /api/dashboard does not return month_expense
r = client.get("/api/dashboard")
data = r.json()
data["month_expense"]  # KeyError!
```

**Design rule:** When writing a test for a value, first check which endpoint actually computes/returns it. If the API doesn't expose it, either: (a) add it to the API response schema, or (b) use the web route and assert on rendered HTML content (`r.text`).

### Rendered HTML Assertions

Some bugs are in template rendering, not API responses. Use `client.get("/")` and check `r.text` for expected strings:
```python
r = client.get("/")
assert r.status_code == 200

# Check that a label appears (not blank/empty)
assert "Uncategorized" in r.text, "Spending breakdown shows blank labels"

# Check that an inflated value does NOT appear
assert "£350" not in r.text, "Month expense uses wrong time window"
```

**⚠ Avoid BeautifulSoup overhead for simple checks** — use `in r.text` first. Only parse HTML when you need structured extraction.

### Test Auth Override Pattern

Most routes require authentication. When testing with `TestClient`, override auth dependencies:
```python
from pfin_api.auth import get_optional_user

app.dependency_overrides[get_optional_user] = lambda: {"user_id": "test", "email": "test@test.com"}
```

## Static Files

### Mounting in FastAPI
Static files need a `static/` directory and a mount in the app factory:
```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles

HERE = Path(__file__).parent
static_dir = HERE / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
```
⚠ Without this mount, `<script src="/static/js/...">` tags return 404.

### Use Absolute Paths
Relative paths for `StaticFiles` and `Jinja2Templates` break when uvicorn is run from a different working directory:
```python
from pathlib import Path
HERE = Path(__file__).parent

templates = Jinja2Templates(directory=str(HERE / "templates"))
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
```

### ⚠ Pitfall — `[:N]` list truncation before date filter breaks aggregation

When building dashboard charts that aggregate transactions by month, never
truncate the transaction list BEFORE applying the date range filter:

```python
# ❌ BROKEN — only sees 50 transactions, chart shows 3 months
transactions = sorted(
    [tx for tx in db.query(Transaction)][:50],
    key=lambda t: t.date, reverse=True,
)
for tx in transactions:
    if tx.date >= start_date:  # filter applied AFTER truncation
        monthly[month_key] = monthly.get(month_key, 0) + tx.amount

# ✅ CORRECT — filter first (or don't limit, the date range does it)
transactions = sorted(
    [tx for tx in db.query(Transaction)],
    key=lambda t: t.date, reverse=True,
)
for tx in transactions:
    if tx.date >= start_date:
        monthly[month_key] = monthly.get(month_key, 0) + tx.amount
```

**Why it manifests:** With 11k+ transactions spanning 2013-2026, 50 transactions
cover only ~3 months. The date filter runs on the truncated list, producing a
chart with 3 data points instead of 12. The fix is removing the `[:50]` — the
date filter already constrains the aggregation window. If performance is a
concern, apply `WHERE date >= ?` at the DB query level, not Python-side
truncation.

## CSV Import Pattern

When building an import system for bank transaction CSVs, handle multiple formats by detecting columns and dispatching to format-specific parsers. The user has 41 CSV files across 5+ bank formats in `/home/tangyi/data/primary/data_finance/banking/`.

### Parser Detection Pitfalls

**⚠ Filename-first detection misclassifies files.** If the detection function checks filename keywords before header column sniffing, a file named `lloyds_2019.csv` that uses Barclays column format gets the wrong parser and crashes with `KeyError`. Detection should use header columns as the primary signal and filename as a secondary hint.

**⚠ `csv.DictReader` is case-sensitive.** A CSV with lowercase headers (`date, desc, amount`) triggers `KeyError` when the parser looks for `Date`. Fix: normalise column lookups with case-insensitive matching:

```python
def _get(row, key, *aliases):
    """Get a value from a CSV row dict, case-insensitive, multiple fallback keys."""
    for k in [key] + list(aliases):
        for rk in row:
            if rk.strip().lower() == k.lower() and row[rk] is not None:
                return row[rk]
    return ""

# ⚠ csv.DictReader returns None for empty cells, not "". Always check row[rk] is not None
# before calling .strip() or returning the value. A None return will crash downstream
# .strip() calls in parsers.
```

**⚠ Currency symbols (`£`, `$`, `€`) crash `float()`.** If a bank includes `£3.50` in the amount column, `float("£3.50")` raises `ValueError`. Strip all known currency symbols before conversion:

```python
def _clean_amount(val: str | None) -> float:
    if val is None:
        return 0.0
    val = val.strip().replace(",", "")
    for sym in ("£", "$", "€", "¥"):
        val = val.replace(sym, "")
    return float(val or "0")
```

**⚠ Dates come in multiple formats.** Your bank CSVs use DD/MM/YYYY, YYYY-MM-DD (ISO), "DD Mon YYYY" (e.g. "03 Apr 2020"), and "DD-Mon-YY" (e.g. "03-Apr-20"). Try each format in order until one succeeds:

```python
def _parse_date(val: str) -> date:
    s = val.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d-%b-%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Cannot parse date: {s!r}")
```

**⚠ Return graceful errors, not 500s.** When no parser matches or parsing fails, catch the exception and return `{"ok": False, "error": "descriptive message"}` rather than letting it bubble up as a 500 Internal Server Error.

### Detecting Multiple CSV Formats

Use header column names (not just filename) to pick the parser:

```python
def detect_format(headers, filename=""):
    h = [c.strip().lower() for c in headers]
    if "appears on your statement as" in h:
        return AmexBA_2024Parser()
    if "subcategory" in h and "memo" in h:
        return BarclaysPremierParser()
    if "debit amount" in h and "credit amount" in h:
        return BarclaysParser()
    if "transaction date" in h:
        return BarclaysParser()
    if h == ["date", "desc", "amount"]:
        return HSBCParser()
    # Fallback to filename keyword
    f = filename.lower()
    if "barclays" in f or "lloyds" in f:
        return BarclaysParser()
    if "hsbc" in f:
        return HSBCParser()
    if "amex" in f or "gold" in f or "ba_" in f:
        return AmexGoldParser()
    return None
```

### Bank CSV Formats Reference

See `references/bank-csv-formats.md` for the full column layout mapping and parser status for all known bank CSV formats in this user's data (41 files across Amex, Barclays, HSBC, and Lloyds — all 41/41 passing as of 2026-06-04). Includes edge cases like:
- 13-column Amex with `£` prefixes in Amount and "03 Apr 2020" date format (AmexOldParser)
- Barclays Premier format: `Number,Date,Account,Amount,Subcategory,Memo` (BarclaysPremierParser)
- Barclays Transactions format: `Account,Date,OriginalDescription,Amount,L1Tag,L2Tag,L3Tag` (BarclaysLegacyParser)
- Lowercase HSBC headers: `date, desc, amount` (handled via case-insensitive `_get_ival`)
- Lloyds-named files with Barclays column format (header sniffing corrects mis-named files)

## Server Startup & CLI Verification

When the CDP browser isn't available (or for rapid API-level checks), verify the server entirely from the CLI:

### 1. Start server in background
```python
terminal(
    command="cd /project && app-server --host 0.0.0.0 --port 8125 --reload 2>&1",
    background=True,
    notify_on_complete=True,   # you'll be pinged if it crashes
)
```

### 2. Health check with curl
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8125/login
# Expected: 200
```

### 3. Inspect API responses via execute_code + json.loads
This pattern avoids markdown-formatting problems when piping curl through python:
```python
from hermes_tools import terminal
import json

r = terminal("curl -s http://localhost:8125/api/dashboard", timeout=10)
data = json.loads(r['output'])
print(f"Net worth: £{data['net_worth']:,.2f}")
print(f"Accounts: {data['accounts_count']}")
```

### 4. Check auth flow
The app's login form may use non-standard field names (e.g. `user_id` instead of `username`). Always inspect the login route handler or template to find the correct form field before attempting authenticated requests:
```python
# Login + save session cookie
import tempfile
jar = tempfile.NamedTemporaryFile(delete=False).name
r = terminal(f"curl -s -c {jar} -X POST http://localhost:8125/login -d 'user_id=myid' -D -", timeout=10)
# Check Set-Cookie header for session token

# Use the cookie for authenticated requests
r2 = terminal(f"curl -s -b {jar} http://localhost:8125/", timeout=10)
```

### ⚠ Pitfall — background process with no output
A FastAPI server started with `background=True` may show zero output for the first 3-5 seconds while uvicorn boots and the lifespan context manager runs. Don't assume it crashed — poll with `process(action='poll')` and check the HTTP endpoint:
```python
process(action='poll', session_id='proc_xxx')  # running
curl http://localhost:8125/login               # 200 → it's up
```

## SQL / Balance Query Pitfalls

### ⚠ Pitfall — `SELECT DISTINCT` without date filter returns stale balances

When querying a time-series table like `balance_sheet` for account balances, `SELECT DISTINCT account, amount FROM balance_sheet` picks an arbitrary `amount` — whichever row SQLite returns first for that account. There's no ORDER BY, and with `DISTINCT` you can't order by date.

**Symptoms:** Dashboard shows wrong account balances (e.g. £285 instead of £721k net worth). Individual account values are random historical snapshots, not the latest.

**Fix — always filter to the latest date:**
```sql
-- WRONG — random historical balance
SELECT DISTINCT account, amount FROM balance_sheet;

-- RIGHT — latest per account
SELECT account, amount FROM balance_sheet
WHERE date = (SELECT MAX(date) FROM balance_sheet WHERE account = balance_sheet.account);

-- RIGHT — all accounts in latest month (excludes closed accounts)
SELECT account, amount FROM balance_sheet
WHERE date = (SELECT MAX(date) FROM balance_sheet);
```

The second form (`MAX(date)` per-account) shows every account's latest value, including closed ones. The third form (single `MAX(date)` globally) only shows accounts active in the latest month — this implicitly hides closed accounts.

### ⚠ Pitfall — Cumulative transaction sum ≠ account balance

For credit cards and investment accounts, `SUM(amount)` across all transactions is NOT a meaningful balance. It's an artifact of raw data, not an accounting figure.

**Why it's wrong:**
- Credit cards are paid in full monthly — the lifetime cumulative sum includes all past spending AND all past payments, producing a meaningless negative number (e.g. -£26,398 for AMEX Gold)
- The actual balance is the latest statement closing balance, which the DB may not track
- A large refund creates a credit balance that carries forward for months with no payments — the cumulative sum drifts negative during that period but the actual balance is a credit

**What to show instead:**
- For credit cards: "Paid monthly — see statement" or this month's spend vs last payment
- For the dashboard net worth: read from `balance_sheet`, not from `SUM(transactions)`
- Never present cumulative transaction sums as account balances to the user

## Template Development

### ⚠ Pitfall — Template variable name mismatch after route refactor

When a route is refactored to pass new template variables (e.g. `holdings`, `total_value` instead of `grouped`, `all_trades`), the old template still references `grouped.items()` and crashes with Jinja2 `UndefinedError: 'grouped' is undefined`.

**Symptoms:** 500 Internal Server Error on the page. Server logs show `jinja2.exceptions.UndefinedError`. The route code looks correct but the template wasn't updated.

**Fix checklist when refactoring a route:**
1. Search the template for ALL Jinja2 variable references (`{{`, `{% for`, `{% if`)
2. Compare against the variables now being passed in `template.render(...)` 
3. Update every reference — don't miss inside `<script>` tags, `{% for %}` loops, or nested includes
4. Run a test that hits the page and checks for 200 status + expected content

### ⚠ Pitfall — Worktree removal breaks editable installs of sibling packages

When packages are installed via `pip install -e` from a worktree path, removing the worktree leaves stale `.pth` files in site-packages pointing to the deleted directory. The next server startup crashes with `ModuleNotFoundError`.

**Symptoms:** After `git worktree remove .worktrees/<name> && git branch -d feat/<name>`:
```
ModuleNotFoundError: No module named 'pfin_db'
```
Even though `pip install -e pfin-api/` succeeded. The error is in a DEPENDENCY package (pfin-core), not the one you just reinstalled.

**Root cause:** `pip install -e pfin-api/` with `--no-deps` doesn't reinstall `pfin-core`. The editable install for `pfin-core` still points at the deleted worktree path.

**Fix — always reinstall ALL editable packages after worktree removal:**
```bash
pip install --break-system-packages --force-reinstall --no-deps -e pfin-data/ -e pfin-core/ -e pfin-api/
```

**Prevention checklist after merging a worktree:**
1. `git checkout master && git merge feat/<name>`
2. Run tests on merged master
3. `git worktree remove .worktrees/<name> && git worktree prune && git branch -d feat/<name>`
4. **Reinstall all three editable packages** ← this step is easy to forget
5. Kill old server, start new server, verify with curl

### ⚠ Pitfall — FastAPI stub route silently intercepts real API

When a legacy stub route file (e.g. `categories.py`) has `@router.get("/api/categories")` and a new real API file (`categories_api.py`) uses `prefix="/api/categories"`, both routers are registered in `__init__.py`. FastAPI resolves the first-registered route — the stub wins silently, and the real API never receives traffic.

**Symptoms:** `GET /api/categories` returns stub data (`{"categories": []}`), `POST` returns `501 Not Implemented`. No startup error. The real API code is correct in isolation.

**Fix — empty the stub router:** Keep the file (if `__init__.py` imports it) but remove all routes:
```python
router = APIRouter()
# All routes removed — real API is in categories_api.py
```

**Prevention:** When adding routes for a feature that previously had a stub, check `routes/__init__.py` for existing imports that might shadow the new router.

### ⚠ Pitfall — Query outside `with conn:` context manager

```python
with db._engine.connect() as conn:
    rows = conn.execute(sa_text("SELECT ...")).fetchall()
# BUG: conn is closed here
more = conn.execute(sa_text("SELECT ...")).fetchall()  # ResourceClosedError
```
**Fix:** Keep all queries inside the same `with` block. When adding a second query to existing code, check that it's indented inside the block.

## Git Cleanup Workflow

When a project has a dirty working tree (modified + untracked files), clean up before starting new work:

1. **Delete stray temp files first** — check for editor backup files (`#filename#`), stale temp docs
2. **Audit untracked directories** — `static/` with test fixtures that belong in tests, vendored JS that's actually needed
3. **Fix `.gitignore`** — ensure `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `build/` are covered
4. **Stage in logical groups** — one commit per feature/fix area, not one giant blob:
   - Core library changes (parsers, models)
   - New modules (sync engine + tests)
   - Frontend assets (templates, static, JS)
   - API routes (endpoints, app factory)
   - Documentation (specs, plans, bug reports)
5. **Run full tests between commits** — verify nothing broke

## Reference

For a full worked example of these patterns in action, see the `brainstorming` skill's `references/personal-finance-web-app-worked-example.md`.

See also:
- `references/net-worth-history.md` — running-balance net worth computation endpoint (per-month, per-account breakdown, Chart.js integration)
- `references/pfin-project-conventions.md` — pfin-specific project conventions (auth, sync engine, project layout, verification commands)