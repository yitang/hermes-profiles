# Worked Example: Golden-Source Sync Pipeline Design

**Date:** 2026-06-05
**Context:** A personal finance app (pfin) had an application database with enriched
data (categories, projects, budgets). A separate data-collection repo was introduced
that writes raw bank transactions to a golden-source database (`finance.db`).
The design problem: import new raw data from the golden source into the app database
on a weekly cadence, preserving the app's ability to enrich transactions independently.

This is a fundamentally different architecture from the inbox-to-SQLite pipeline
(one database, direct-from-CSV import). The golden-source pattern assumes two
independent databases with distinct responsibilities.

## Architecture Pattern

```
finance.db                    ~/.pfn/pfin.db
─────────────────             ─────────────────
Golden source                 Application database
Read-only for pfin            Holds enriched data
Written by collection repo    Categories, projects, budgets
(weekly)                      tags, reconciled status
                              + raw transactions from sync
```

The sync is one-way, append-only. It never writes to the golden source.

## Pre-Architecture Data Inventory (Critical Step)

Before designing a single line, investigate BOTH databases in full. The user will
ask about discrepancies. The questions to answer:

**Golden source (finance.db):**
- What tables exist? What are their column schemas? (`sqlite3 finance.db .schema`)
- How many rows per table?
- Date ranges per table (MIN/MAX date)?
- What account names/identifiers exist? Are there multiple accounts in one table?
- Do amounts have consistent sign conventions?
- Are there empty rows, null amounts, or stub accounts to skip?

**Application database (pfin.db):**
- What accounts exist? (IDs, names, institutions)
- How many transactions per account?
- Date ranges per account?
- Are there accounts with no source counterpart? (manually entered, test accounts)
- Are there duplicate accounts? (e.g. two "Amex Gold" entries, one empty)

**Reconciliation: source vs target**
- `COUNT(*)` in source vs target — if they differ substantially, explain why
- Check for accounts in the target that have no source counterpart
- Check for source tables that map to multiple target accounts
- Summary table format:

```
| pfin Account | pfin txn count | Source match    | Source raw count | New after last date |
|---|---|---|---|---|
| Amex Gold    | 3,315          | → amex_gold     | 2,173            | 115                 |
| Barclays Cur | 392            | → barclays/acct | 1,462            | 406                 |
```

**Signal phrase to watch for:** User asks "why does X have more/fewer rows than Y?"
— answer factually, don't speculate.

## Core Design Decisions

### 1. Append-Only, Never Modify

Sync inserts new rows. It never:
- Updates existing transactions
- Touches enrichment fields (category_id, project_id, person_id, tags, reconciled)
- Deletes anything

### 2. Per-Account Dedup Scope

User explicitly corrected: dedup key is `(account_id, date, amount, description)`  —
**scoped per account**, not global. Two transactions with the same date/amount/description
on different accounts import correctly.

### 3. Incremental Tracking

Use a tracking table inside the target database:

```sql
CREATE TABLE _sync_log (
    source_table TEXT NOT NULL,
    account_name TEXT NOT NULL DEFAULT '',
    last_date TEXT,
    row_count INTEGER,
    synced_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (source_table, account_name)
);
```

On each run: read `last_date`, query `WHERE date > last_date`, insert, update.

### 4. Per-Table Column Mapping

Each source table has different columns. Normalise them to the target schema via
per-table mapping functions. Structure:

```python
SOURCES = [
    {
        "table": "barclays",
        "account_col": "account",       # column that disambiguates accounts
        "select": "date, amount, ...",
        "row_map": _map_barclays,       # dict of canonical fields
    },
    ...
]
```

### 5. Source Metadata Preservation

The target application has its own enrichment model (categories, projects, tags).
Source data may have its own categorisation that shouldn't be lost. Preserve it:

- **Structured JSON in a memo/text field**: source subcategories, categories, notes
- **Extra JSON blobs in a notes field**: columns not mapped to any named field

This keeps the import clean while preserving all data. Users notice when data
gets silently discarded — preserve by default.

### 6. Amount Sign Convention Must Be Explicit

Document the convention in the spec:

- Negative = expense / withdrawal / debit
- Positive = income / deposit / credit
- Zero = neutral transfer

Amex sources often store debits as positive values — negate them on import.

## When This Pattern Applies

- You have a read-only data source maintained by a separate system
- The app database needs new data appended but users curate enrichment in-app
- Weekly or batch cadence (not real-time)
- Source and target have different schemas and different column layouts per source table

## Anti-Pattern: Duplicating Computation Across Layers

When the data layer already computes derived data (net worth, balance sheets,
investment holdings), do NOT sync those derived tables into the app layer.
The app layer should sync only **raw data that needs enrichment** — bank
transactions, fund trades. Leave aggregation to the data layer.

### Example (Wrong)

Data layer has `balance_sheet` (738 monthly net-worth snapshots). App designer
proposes creating a `net_worth_snapshots` table in the app DB and syncing
`balance_sheet` → `net_worth_snapshots`. This duplicates:
- The storage (same data in two places)
- The computation path (data layer already has `build_balance_sheet.py`)
- The divergence risk (which one is authoritative?)

### Example (Right)

App layer syncs raw transactions and fund trades. App dashboard reads from
synced transactions for enrichment views (categorised spending, budget tracking).
Net worth charts either:
- Read directly from data layer's `balance_sheet` via cross-DB query, or
- Stay in the data layer's own visualisation (`net_worth.html`)

The app layer focuses on its unique value: enrichment (categories, projects,
budgets, person tagging). The data layer owns computation and aggregation.

### Test: "Is this table raw data, or is it computed?"

| Synced | Skipped |
|---|---|
| `barclays`, `amex_gold`, `hsbc` — raw bank rows | `balance_sheet` — derived from raw rows |
| `vanguard_isa_cash` — raw cash flows | `investment_holdings` — derived from trades |
| `vanguard_isa_investment` — raw fund trades | `lg_workpension_cash` — derived from raw |
| `lg_workpension_transactions` — raw pension rows | `lg_workpension_investment` — derived from raw |

If the source table was created by a script that reads *other* source tables,
it's derived. Skip it.

### What About Mortgage?

Mortgage is a borderline case. It's not derived from transactions — it comes
from amortization tables (`mortgage_config.py`). But it's still a liability
balance, not a transaction to enrich. Sync as monthly `transactions` rows
(negative amount) if the app needs it for category/project grouping; otherwise
leave it in the data layer.

## When It Does NOT Apply

- Single-user app with no enrichment layer → inbox-to-SQLite is simpler
- Real-time sync needed → consider triggers or streaming
- Source is writeable and mutable → consider views or federation
- No existing app database → start with a combined design
