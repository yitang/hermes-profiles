# Canonical Schema Migration Recipe

When migrating from per-source raw tables to a canonical normalized schema,
follow this 5-phase approach. Used successfully on a 13-table → 3-table migration
(11,329 transactions + 663 investment trades + 812 balance sheet rows).

## Phase 1: Add canonical DDL alongside legacy tables

Add `CREATE TABLE IF NOT EXISTS` for the new canonical tables to the schema
init script. Do NOT drop legacy tables — they are your audit trail and safety net.
Use `source_id TEXT PRIMARY KEY` (SHA-256 hex[:16]) as the dedup key.

## Phase 2: Write a one-shot migration script

A standalone script (`migrate_to_canonical.py`) that:
1. Opens `finance.db`
2. Reads each legacy per-source table
3. Normalizes amounts (AMEX: `-abs()`, Lloyds: debit/credit merge, etc.)
4. Computes `source_id` using `source_name` (not table name) in the hash
5. `INSERT OR REPLACE` into canonical tables (source_id PK handles idempotency)
6. Prints per-source migration counts

**Critical:** test with an in-memory DB, not against the live DB. Create minimal
per-source table structures, insert test rows, run migration, assert canonical
tables have expected data. The live migration should be a one-shot run; the tests
run every time.

**source_id hash format:**
```python
import hashlib
def _make_source_id(source_name, date_val, amount_val, description_lower):
    payload = f'{source_name}|{date_val}|{amount_val}|{description_lower}'
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]
```

Use `source_name` (human-readable, e.g. "Barclays Premier"), NOT the old table
name (e.g. "barclays"). This keeps the hash stable even if the table is renamed.

## Phase 3: Rewrite import scripts to target canonical tables

Each import script (import.py, vanguard_import.py, workpension_import.py) must:
1. Output canonical row dicts (same shape as canonical table columns)
2. Include `account_type` and `source_name` in every row
3. Use `INSERT OR REPLACE` with `source_id` as PK
4. Remove per-bank table insertion code

All `TABLE_NAMES` and `COLUMN_WHITELIST` collapse to a single target: `"transactions"`.

## Phase 4: Update downstream consumers

Every script that reads per-source tables must switch to querying canonical tables
with `WHERE source_name = '...'` filters:

| Old | New |
|-----|-----|
| `FROM barclays` | `FROM transactions WHERE source_name = 'Barclays Premier'` |
| `FROM vanguard_isa_investment` | `FROM investment_trades WHERE source_name = 'Vanguard ISA'` |

Files to check:
- `compute_holdings.py` — queries investment tables
- `build_balance_sheet.py` — queries multiple per-source tables (+ keep mortgage/property)
- `viz_*.py` — queries v_combined views
- `init_schema.py` — print/summary loops

**Exception:** computed/derived tables that aren't directly imported (mortgage amortization
schedule, property valuations from config files) stay unchanged. They don't go through the
canonical pipeline.

## Phase 5: Validate and clean up

1. **Row count consistency:** compare legacy table row counts vs canonical table counts
2. **Full test suite:** all tests pass (per-source table tests updated to query canonical tables)
3. **Balance sheet rebuild:** verify same net worth values as pre-migration
4. **Import idempotency:** re-run each import script, verify 0 new inserts
5. **Mark legacy tables** in docs and init_schema.py print loops as legacy/audit-only

## What NOT to change

- **Computed tables** (mortgage amortization, investment_holdings cache) — these
  are derived, not imported. They stay as-is.
- **Config-based data** (property valuations from property_config.py) — not in the DB.
- **The balance_sheet table** — it's already canonical (date, account, amount, kind PK).
  No schema change needed, though its builder script may need to query canonical tables.

## Common failure: live DB migration with wrong hash

If the migration script and the import parsers use different hash components
(e.g., migration uses old table name but import uses source_name), the source_id
won't match and re-imports won't dedup. Always test both paths against the same
in-memory data.
