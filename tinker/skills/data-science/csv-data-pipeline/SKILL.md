---
name: csv-data-pipeline
description: "Robust ETL for messy multi-format CSV/OFX data ingestion — routing, dedup, schema evolution, and audit trails."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ETL, CSV, OFX, data-ingestion, routing, deduplication, schema-evolution, audit]
---

# CSV Data Pipeline — Robust ETL Patterns

For building reliable ingestion pipelines where source formats are messy, inconsistent, and evolve over time.

## When to Use

- Ingesting data from multiple external sources (bank exports, APIs, scrapers)
- Source CSV/OFX/XML formats change without warning
- Multiple accounts produce similar-looking data with identical headers
- Need to merge same-account data across different source formats
- Database schema must grow without breaking existing imports

## Core Architecture Pattern

```
data/raw/     ← all raw exports (single source of truth, git-tracked)
    ├── account_a_format1.csv
    ├── account_a_format2.csv  ← format drift!
    └── account_b.ofx          ← different format entirely

clean.py      → data/cleaned/   ← canonical CSVs per account
inbox/        ← staging area for import.py (one-time drops)
import.py     → finance.db      → /archive/ (timestamped imports)
```

**Key rule:** Raw data never mutates. Only append new files to `data/raw/`. Cleaning is always idempotent — run on the full directory, get reproducible outputs.

## Phase 1: Detection & Routing

### The Header Collision Problem ⚠️ CRITICAL

When two different accounts produce CSVs with identical headers (e.g., `Date,Description,Amount,balance`), header-only detection **cannot** distinguish them. This causes silent data misrouting into the wrong database table.

**Fix: Filename-based detection with header fallback.** Check filename patterns first, then fall back to column matching only for truly unrecognized files:

```python
def detect_account(filepath):
    fname = os.path.basename(filepath).lower()
    
    # 1. Filename-based routing (PRIORITY — handles identical headers)
    if 'lloyds' in fname and 'cleaned' in fname:
        return 'lloyds_cleaned'
    if 'hsbc_credit' in fname and 'cleaned' in fname:
        return 'hsbc_credit_cleaned'
    
    # 2. Header-based fallback (only for unknown filenames)
    header = read_first_line(filepath)
    cols = [c.strip().lower() for c in header.split(',')]
    
    if len(cols) >= 6 and 'date' in cols and 'amount' in cols:
        return 'hsbc'  # or whatever 6-col format
    
    return None  # truly unrecognized — skip with warning
```

### Pattern recognition checklist before writing detection logic:
1. List every output CSV's header from all sources
2. **Flag collisions**: any two accounts sharing the same header columns? → filename priority required
3. Check for columns that only exist in one format (e.g., `Category` vs `Subcategory`) — these can help distinguish if filenames aren't reliable

## Phase 2: Cleaning & Canonicalization

### Multi-format source merging
Same account may produce data in different formats (CSV export vs OFX download). Clean.py must:
- Detect each file's format by header/columns or extension (.ofx)
- Parse each format into the **same canonical row schema** before merging
- Deduplicate across ALL inputs for an account, not within individual files

### Dedup strategy
- Key: `(date, normalized_amount, description.lower())`
- Normalization: strip whitespace, normalize sign convention, handle decimal separators
- Use `INSERT OR IGNORE` at DB level; track duplicates in audit trail

### Sign fixing
External exports often use negation inconsistently (Amex uses negative for credits in some formats, positive in others). Detect by column semantics (`Category=Payment` with negative amount = double-negative) and normalize.

### Balance computation from OFX anchors
When the pipeline receives OFX files with `<LEDGERBAL>` tags:
1. Parse ledger balance + date from each OFX
2. Collect all anchors for an account, take the latest
3. **Backward-wind**: starting from the anchor value, go through rows in reverse order computing `row_balance = next_row_balance - amount` (adjusting sign convention)
4. Forward-reverse to align with original row order

**⚠️ CRITICAL: Preserve pre-computed bank CSV fields.** Some banks already compute running balances in their CSV exports (e.g., Lloyds `Balance` column). When no OFX anchor exists, do NOT overwrite these values with zeros — check if the field already has content first. If it does, keep the bank's value.

```python
def compute_balance(rows, ledger_bal):
    if not rows or not ledger_bal:
        # Preserve any pre-existing balance values (e.g. from bank CSVs); only default to 0 if missing
        for r in rows:
            if 'balance' not in r or not r['balance'].strip():
                r['balance'] = 0
        return
    
    balances = []
    current = float(ledger_bal['amount'])
    # Walk backwards (most recent first)
    for r in reversed(rows):
        balances.append(current)
        current -= float(r['amount'])
    balances.reverse()
    
    for i, r in enumerate(rows):
        if i < len(balances):
            r['balance'] = round(balances[i], 2)
```

### Audit trail (MANDATORY)
Every clean.py run MUST generate these files in `data/cleaned/audit/`:

| File | Purpose | Key columns |
|------|---------|-------------|
| `manifest.md` | Summary of all accounts, file counts, raw→clean reductions | account, source_files, raw_rows, clean_rows |
| `sign_fixes.csv` | Every amount sign corrected | date, original_amount, corrected_amount, source_file |
| `duplicates.csv` | Rows removed during dedup | date, amount, description, kept_in (filename) |
| `balance_anchors.csv` | OFX LEDGERBAL sources used for balance computation | account, anchor_amount, anchor_date, source_ofx_file, row_count_backfilled |

### File skip list
clean.py scans the raw directory. It should **skip non-data files**:
- Python scripts (`.py`)
- Documentation (`.md`, `.txt`)
- Editor backups (`#*~`, `.#*`)
- Previous audit/manifest files
- Any file without a recognized data header

Detect by checking if the first line contains CSV columns or OFX tags. Skip everything else with a logged warning.

## Phase 3: Import & Database Schema

### Schema evolution checklist
Every time a new account/parser is added:
1. **Add parser function** → register in `PARSERS` dict (key = output_name)
2. **Update `TABLE_NAMES`** → map parser key → DB table name
3. **Extend `COLUMN_WHITELIST`** → whitelist per-table for SQL injection protection
4. **Update `detect_account()`** → filename + header patterns
5. **Update `init_schema.py`** → new CREATE TABLE, update v_combined view UNION ALL, update tables registry list
6. **Rebuild DB** → `rm finance.db && touch finance.db && python3 init_schema.py && python3 import.py`

### Schema/code sync rule
If `import.py` creates a table at runtime (e.g., for balance snapshots), that table MUST also exist in `init_schema.py`. Any mismatch causes DB rebuild failures. **Always check both files before adding any new table.**

### Import routing
1. Staged CSVs go into `inbox/`
2. `import.py` detects account, parses, inserts → moves to `/archive/<timestamp>_<filename>.csv`
3. Archive preserves all imported originals for replay/recovery
4. Dedup at DB level: `(date, amount, description_lower)` per-table

## Phase 4: Validation

### Post-clean verification
After clean.py runs and before import:
1. Check `data/cleaned/audit/manifest.md` — raw→clean counts make sense?
2. Verify each cleaned CSV has a matching `init_schema.py` table
3. If balance was expected (OFX had anchors), confirm non-zero balance values in CSV
4. If all balances are zero → OFX anchor not found, investigate

### Post-import verification
```bash
# Row counts per account
sqlite3 finance.db "SELECT account, COUNT(*) FROM v_combined GROUP BY account ORDER BY account;"

# Latest date per account (check against source file dates)
sqlite3 finance.db "SELECT account, MAX(date) FROM v_combined GROUP BY account ORDER BY account;"

# Balance sanity: all zero balances when OFX anchors should exist?
sqlite3 finance.db "SELECT name FROM sqlite_master WHERE type='table';" -- cross-check with audit/balance_anchors.csv
```

## Pitfalls

1. **Header collision is silent** — no error, data just goes into wrong table. Always compare headers of ALL cleaned outputs before building routing logic.
2. **OFX balance backward-winding sign convention** — be explicit about whether amounts are debits or credits. The sign depends on the export format's perspective (bank's vs customer's). Test with known values.
3. **BOM in CSV files** — UTF-8 BOM (`\ufeff`) appears as a phantom column name (`\ufeffDate`). Strip it: `content = content.lstrip('\ufeff')` before parsing.
4. **init_schema.py vs import.py sync** — if the runtime script creates a table that init_schema doesn't know about, DB init fails. They must mirror each other exactly.
5. **Dedup across format merge** — when an account has both CSV and OFX files for the same date range, transactions will overlap. Dedup must happen across ALL source files, not per-file.
6. **Pre-computed bank CSV fields silently overwritten** ⚠️ NEW. When no OFX anchor exists, `compute_balance()` may zero out existing balance columns that banks already computed (e.g., Lloyds' `Balance` column). Always check if a field has pre-existing values before defaulting. Also verify parsers do NOT explicitly `.pop()` the column — both in clean.py normalization AND import.py parsing logic.
7. **Schema evolution requires 5-file coordination** ⚠️ NEW. Adding any new DB column means updating ALL of: `init_schema.py` (CREATE TABLE), `COLUMN_WHITELIST` in import.py, every parser that encounters the field, and the audit/verification queries. If you only update some of these, the field either crashes on import (whitelist/schema mismatch) or silently drops into the `extra` JSON blob (parser omission). After any column addition, rebuild DB from scratch (`rm finance.db && python3 init_schema.py && python3 import.py`) and verify with a direct query — do NOT assume staged imports will pick up changes incrementally.

## Skill Support Files

See `references/` for:
- `header-collision-diagnosis.md` — step-by-step diagnostic recipe for header collision detection
- `ofx-balance-computation.md` — detailed guide on OFX LEDGERBAL parsing and backward-winding
- `schema-sync-checklist.md` — pre-import checklist for init_schema.py ↔ import.py consistency
- `balance-zeroing-diagnosis.md` — 5-cause diagnostic path for when bank CSV balances end up as zeros in DB