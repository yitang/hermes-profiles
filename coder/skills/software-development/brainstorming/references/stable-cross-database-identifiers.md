# Stable Cross-Database Identifiers

**Context:** When syncing data from a golden-source database (finance.db) into an application database (pfin.db), the enrichment layer needs a stable way to reference source rows. If the source DB is rebuilt, all internal IDs change — without a deterministic foreign key, enrichment data (categories, projects, budgets) gets orphaned.

## The Problem

```
finance.db  ──sync──►  pfin.db
  row 4721              tx abc123  (category: "dining")
  
  -- finance.db gets rebuilt --
  
  row 8192              tx abc123 still references row 4721
                        but row 4721 no longer exists
                        → enrichment orphaned
```

## What Doesn't Work

### SQLite rowid
- Not stable across VACUUM, REPLACE, or table rebuilds
- User's rule: "using rowid is generally bad practice"

### uuid4() (random)
- Every import produces a different value
- Rebuild → re-import → all new IDs → enrichment lost

## What Works: Deterministic Hash

```python
import hashlib

def make_source_id(source_table: str, date: str, amount: str, description_lower: str) -> str:
    raw = f"{source_table}|{date}|{amount}|{description_lower}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

Same input → same output. Even after a full rebuild and re-import, every row gets the same source_id.

## When to Add It

**Add source_id when:**
- The app layer will accumulate enrichment that's painful to lose (categories, projects, budget allocations)
- The source database may be rebuilt (schema migrations, format corrections)
- There are two separate repos with a sync pipeline between them

**Skip source_id when:**
- The pipeline is append-only and source rows are immutable
- No enrichment happens downstream
- Rebuilds are extremely unlikely

## User's Design Constraint

> "Why would I need to do it manually myself?"

Systems should automate reconciliation. Manual cleanup as a design outcome is a failure. If a data pipeline could produce duplicates or orphaned enrichment on a routine operation (rebuild, re-import), the pipeline is wrong — fix the design, don't rely on the user to clean up.
