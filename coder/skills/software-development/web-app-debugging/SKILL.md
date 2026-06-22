---
name: web-app-debugging
description: "Systematically debug FastAPI + Jinja2/HTMX web applications: verify bugs in browser, trace DB state, identify root cause categories (data integrity, UI/API mismatch, calculation error, filter too restrictive), write tests, and plan consolidated fixes."
version: 1.0.0
author: Hermes Agent
tags: [debugging, troubleshooting, fastapi, jinja2, web-apps, verification, root-cause]
---

# Web App Debugging (FastAPI + Jinja2/HTMX)

## Overview

When a user provides a bug list (e.g. from `main.org`), verify EACH bug systematically before proposing fixes. This skill captures patterns specific to FastAPI web apps with Jinja2 templates, SQLite backends, and HTMX/Svelte frontends.

**Do NOT skip verification.** Users have reported bugs that are not actually bugs (e.g. empty categories/projects tabs when no data exists). Verify first, fix second.

## The Bug Verification Workflow

### Step 1: Verify Symptom in Browser

Navigate to each affected page and confirm the reported symptom:

| Page | URL Pattern | What to Check |
|------|-------------|---------------|
| Dashboard | `/` | Net worth value, monthly stats, spending breakdown, cash flow chart, portfolio table |
| Accounts | `/accounts` | Balance values, account list completeness, stale accounts visible |
| Transactions | `/transactions` | Filter controls present, table data renders, search works after submit |
| Trades | `/trades` | Trade rows display, account names populated, quantity values reasonable |
| Reports | `/reports` | Net worth chart renders, time range filters work |
| Import | `/import` | Page content matches user expectation (CSV upload vs sync operation) |

**Record exact observed values.** Example: "Net Worth = £0.00", "This Month Out = 266,728.60". These become your test assertions.

### Step 2: Check Database State

Connect directly to verify what the DB actually contains:

```bash
# SQLite CLI
sqlite3 ~/.pfn/pfin.db "SELECT COUNT(*) FROM transactions; SELECT COUNT(*) FROM accounts WHERE balance = 0;"

# Python (for complex queries)
python3 << 'EOF'
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser("~/.pfn/pfin.db"))
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM transactions WHERE category_id IS NOT NULL")
print(f"Transactions with categories: {c.fetchone()[0]}")
conn.close()
EOF
```

**Key DB checks per page:**
- **Dashboard/Accounts:** `SELECT id, name, type_id, balance FROM accounts` — are balances populated?
- **Transactions:** `SELECT COUNT(*) FROM transactions WHERE category_id IS NOT NULL` — how many are classified?
- **Trades:** `SELECT symbol, COUNT(*) FROM investment_trades GROUP BY symbol` — any duplicates?
- **Net Worth History:** Does the DB have opening balances anchored to each account?

### Step 3: Trace Code Path

For each page, read these files in order:

1. **Route handler** — Usually `pfin_api/routes/web.py` for HTML pages, `routes/dashboard.py`, etc. for API
2. **Template** — `templates/<page>.html` for rendering logic
3. **API endpoint** — If the template calls an API via fetch(), trace that route

### Step 4: Classify Root Cause

After tracing, classify the bug into one of these categories:

| Category | Symptoms | Examples from this session |
|----------|---------|---------------------------|
| **Data integrity** | Balances = 0, duplicates inflated quantities, sync not populating derived fields | Account balances all 0; portfolio qty doubled |
| **UI/API mismatch** | Filters do nothing, search returns empty, form submits but no result | POST form → GET endpoint (405) |
| **Calculation error** | Wrong time window, wrong aggregation, missing anchor point | "This Month Out" = 6-month total; net worth drifts negative over years |
| **Filter too restrictive** | Page empty despite DB having data | Trades page filters for `type_id == "investment"` when none exist |
| **Missing label fallback** | Single aggregate entry, blank labels | All spending under `<uncategorized>` as one line |

### Step 5: Write Failing Test

Each confirmed bug gets a unit test. Place in the appropriate test file:

```python
# pfin_api/tests/test_<feature>.py
def test_<description_of_bug>():
    """<Brief description of what should happen>"""
    # Set up minimal fixture (one account + one transaction)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    db = Database.__new__(Database); db._engine = engine; init_db(db)
    
    # ... insert data ...
    
    # Assert expected behavior (currently fails against buggy code)
```

### Step 6: Propose Consolidated Fix Plan

Group fixes by root cause category — bugs sharing a root cause share a fix phase.

**Example consolidation from this session:**
- Bugs 1.3, 1.6 both caused by sync engine not computing balances → Phase 1 fix
- Bugs 1.2, 4 both caused by duplicate trades + restrictive filter → Phase 1 fix
- Bug 3 (search) is independent frontend/backend mismatch → Phase 2 fix

## Common Root Cause Patterns

### Pattern: POST vs GET Method Mismatch

**How to detect:** Frontend JS does `fetch(url, {method: 'POST', body: JSON.stringify(...)})` but backend route has `@router.get("/api/...")`. 

**Check in templates:** Look for `onsubmit="..."` → follow the `fetch()` call. Check if method is POST while endpoint is GET.

**Fix options:**
- Change frontend to GET with query params (preferred — REST-conformant, bookmarkable)
- Add a parallel POST endpoint at the same path

### Pattern: Sync Engine Not Computing Derived Fields

**How to detect:** Raw rows exist in DB but dashboard values are 0 or wrong. Query DB directly and compare against what the UI shows.

**Fix:** After inserting records in sync, add aggregation step. E.g., for account balances:
```sql
UPDATE accounts SET balance = (SELECT SUM(amount) FROM transactions WHERE transactions.account_id = accounts.id)
WHERE EXISTS (SELECT 1 FROM transactions WHERE transactions.account_id = accounts.id);
```

### Pattern: Duplicate Records from Sync Running Twice

**How to detect:** Portfolio quantities are exactly 2x expected. Each source trade appears with different IDs but identical content in destination table.

**Fix:** 
1. Add UNIQUE constraint on `source_id` column
2. Use `INSERT OR REPLACE` or dedup check before inserting  
3. Run cleanup: `DELETE FROM investment_trades WHERE rowid NOT IN (SELECT MIN(rowid) GROUP BY source_id)`

### Pattern: Overly Restrictive Filter Logic

**How to detect:** Page is empty but DB has data. Check the route handler's filter conditions — they may exclude all records.

**Example from this session:**
```python
# web.py — filters ALL trades out because no accounts have type_id="investment"
inv_accounts = [a for a in accounts if (a.type_id or "") == "investment"]
# Result: [] → trades page is empty despite 600+ trades in DB
```

### Pattern: Net Worth/Time-Series Without Anchor Point

**How to detect:** Net worth history chart drifts over long periods, shows negative where positive expected.

**Root cause:** Calculation sums transaction amounts up to each month boundary, but never uses account opening balances as anchors. Over 10+ years of transactions starting from zero → garbage.

**Fix:** Use stored `account.balance` (post-sync) as the anchor point for each account's time series. Only sum transactions BETWEEN month boundaries.

### Pattern: All Data Unclassified Produces Single Aggregate

**How to detect:** Spending breakdown shows exactly one line with no meaningful label, or `<uncategorized>`.

**Fix:** Change `"<uncategorized>"` → `"Uncategorized"`. Consider showing a hint to users that they need to create categories.

## Reference Files

- See also: `software-development/systematic-debugging` for the general systematic debugging process (applies before this skill)
