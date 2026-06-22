# Worked Example: Personal Finance Web App

This document records a complete end-to-end run of the brainstorming skill on a real project. Future agents can reference this to see how the workflow plays out in practice.

## Project

Personal Finance Web App — FastAPI + HTMX + SQLite for tracking net worth, spending, investments, and DIY project budgets. Built from scratch with real bank data (9,505 transactions imported).

## Brainstorming Flow

### Step 1: Explore Context
Discovered an existing `pfin` CLI project in the PARA tree. User clarified this was a NEW app, not an extension of the old one.

### Step 2: Visual Companion
Skipped — CLI web app, no visual layout needed.

### Step 3: Clarifying Questions (one at a time)
1. New app or extension of existing `pfin`? → Fresh slate
2. What platform? → Web (internal network, phone/tablet/TV access)
3. Preferred tech stack? → Python
4. HTMX vs Vue for frontend? → HTMX (user expressed concern about limitations; honest trade-off comparison helped them decide)

### Step 4: Approaches Proposed
- A: FastAPI + HTMX + SQLite *(recommended)*
- B: FastAPI + Vue/React SPA + SQLite
- C: Django + HTMX + SQLite

User picked A.

### Step 5: Design Presented in Sections
- **Architecture** — FastAPI serves HTML directly, HTMX for interactivity, Alpine.js for widgets, Chart.js for graphs → approved
- **Data Model** — 6 tables refined to 5 (investment merged into account type + transaction extras) → approved
- **Screens** — 8 views (Dashboard, Accounts, Transactions, Categories, Reports, Projects, Budget) → approved

### Step 6: Spec Written
Saved to `docs/spec-2026-06-04-personal-finance-web-app.md`. Contains architecture, data model, all screens, boundaries.

### Step 7: Self-Review
- Placeholders: Auth marked TBD (intentional, deferred)
- Contradictions: None
- Scope: Tight v1 focus

### Step 8: User Review
User approved without changes (design was approved section-by-section during Step 5).

### Step 9: Transition to Plan
Loaded `writing-plans` skill. Phase 1 detailed with exact code and tests. Phases 2-5 outlined.

## Implementation Patterns Discovered

### TemplateResponse Requires Keyword Args
FastAPI 0.136.3/Starlette 1.2.1 `Jinja2Templates.TemplateResponse` has signature `(self, request, name, context, ...)`.  
**Always call with keyword arguments:**
```python
return templates.TemplateResponse(
    request=request,
    name="template.html",
    context={"key": "value"},
)
```
Positional calls map incorrectly — the template name string becomes `request` and the context dict becomes `name`, causing Jinja2 to receive a dict as template name.

### httpx ASGITransport Does Not Trigger Lifespan
`httpx.AsyncClient(transport=ASGITransport(app=app))` does not call the FastAPI lifespan context manager.  
**Use Starlette's TestClient instead:**
```python
from starlette.testclient import TestClient
with TestClient(app) as client:
    response = client.get("/")
```
TestClient triggers lifespan startup/shutdown correctly. TestClient is synchronous regardless of whether routes are async.

### Jinja2 3.1.6 LRUCache Bug
Setting `templates.env.cache = None` causes `TypeError: unhashable type: 'dict'` in Jinja2's LRUCache.  
**Do not disable the cache.** Just leave the default cache enabled.

### Python Dict → JavaScript in Templates
Using `{{ chart_data|safe }}` on a Python dict renders Python's `str()` representation (`{'key': True}`), not valid JavaScript (`{"key": true}`).  
**Always JSON-serialize in the router:**
```python
import json
return templates.TemplateResponse(
    request=request,
    name="report.html",
    context={"chart_data": json.dumps(chart_data)},
)
```
Then in the template: `var data = {{ chart_data|safe }};` produces valid JS.

### Relative Paths Break with uvicorn
`StaticFiles(directory="pfinweb/static")` breaks when uvicorn is run from a different working directory.  
**Use absolute paths:**
```python
from pathlib import Path
HERE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
templates = Jinja2Templates(directory=str(HERE / "templates"))
```

### SQLAlchemy Async Engine for Tests
Module-level engine creation captures the database URL at import time, making test configuration impossible.  
**Use lazy engine creation:**
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
    import pfinweb.models  # noqa: F401
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
```

### Chart.js Canvas Height
Setting `height="100"` as an HTML attribute only sets the canvas coordinate space, not the CSS display height. The chart renders at 0px and is invisible.  
**Use CSS style for display height:**
```html
<canvas id="chart" style="width:100%;height:400px;"></canvas>
```

## Files & Commits

```
946b757 docs: add Phase 1 implementation plan
9e4bde1 feat: project skeleton + SQLAlchemy models
daa7087 feat: Phase 2 — account CRUD with HTMX UI
4796326 feat: Phase 3 — transactions, categories, budgets
f5f8eec feat: Phases 4+5 — reports, projects, dashboard
95fd16b feat: CSV import script + 9,505 transactions
bc9a012 fix: absolute paths for static/templates
2cc2a5f feat: net worth history chart + search/export
```

## Test Stats
- 42 tests
- 39 passing originally, 3 added for new features
- All use Starlette TestClient (synchronous)
