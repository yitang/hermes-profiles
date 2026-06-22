# Cross-Database Stable Identity for Enrichment-Safe Sync

## Problem

You have two databases: a golden-source DB (e.g., `finance.db`) and an application DB (e.g., `pfin.db`). The app DB adds enrichment (categories, projects, tags) on top of source rows. If the source DB is rebuilt (schema migration, re-import), enrichment is orphaned — the app has no way to reconnect its work to the rebuilt source rows.

## What NOT to use

- **SQLite rowid** — unstable across `VACUUM`, `REPLACE`, `INSERT OR REPLACE`, or table rebuilds. Rowid is a physical storage concept, not a logical identity.

- **uuid4()** — random, non-deterministic. Every rebuild produces different IDs. Same logical row → different uuid4 → enrichment lost.

## The pattern: deterministic content-based hash

Generate a stable identifier from the content that defines row uniqueness:

```python
import hashlib

def make_source_id(table: str, date: str, amount: float, description: str) -> str:
    raw = f"{table}:{date}:{amount}:{description.lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

**Properties:**
- Same logical row → same ID, even after full rebuild
- Different rows → different IDs (collision probability negligible at 16 hex chars)
- No dependency on physical storage or import order
- Works across any schema — just pick the fields that define uniqueness

## Upsert behavior

On re-sync, match by `(source_table, source_id)`:

- **Found in app DB** → update mutable fields (description, amount, date, memo, notes) from source, **preserve** enrichment fields (category_id, project_id, tags, reconciled). User's categorization work survives anything.
- **Not found** → insert new row.

## When to use

Any pipeline where:
1. Source data is periodically rebuilt or re-imported
2. A downstream system enriches the data
3. Losing enrichment on rebuild is unacceptable
