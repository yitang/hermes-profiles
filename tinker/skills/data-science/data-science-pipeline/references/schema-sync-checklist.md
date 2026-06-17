# Schema Sync Checklist

## Problem

`init_schema.py` (DDL for DB creation) and `import.py` (runtime data insertion) must stay in sync. If `import.py` references a table that `init_schema.py` doesn't create, DB initialization fails with SQL errors. This happened when a `balance_snapshots` table was created by `import.py` at runtime but missing from `init_schema.py`.

## Pre-Import Checklist

Before running import on any new schema:

### 1. Table definitions
- [ ] Every `CREATE TABLE IF NOT EXISTS` in `init_schema.py` has a matching runtime creation in `import.py`
- [ ] Every table that `import.py` creates at runtime exists in `init_schema.py`'s `SCHEMA_SQL` string
- [ ] All table names in the `tables` registry list match actual DB tables

### 2. View definitions
- [ ] `v_combined` (or equivalent union view) includes every data table
- [ ] Each UNION ALL selects from the correct table with the correct column alias
- [ ] Adding a new table required updating: `init_schema.py` (view SQL + tables list), `import.py` (TABLE_NAMES)

### 3. Column whitelists
- [ ] Every new parser has an entry in `COLUMN_WHITELIST`
- [ ] Whitelist covers all known columns for that format
- [ ] New optional columns don't break existing parsing logic

### 4. Detection routing
- [ ] `detect_account()` checks every cleaned CSV filename
- [ ] Header fallback covers any CSV without a filename marker
- [ ] No two accounts match the same detection branch (collision check)

## After Adding a Table — Sync Steps

1. **init_schema.py:** Add `CREATE TABLE IF NOT EXISTS` to `SCHEMA_SQL` string before main creation block
2. **init_schema.py:** Add new table name to `tables` registry list
3. **init_schema.py:** Update `v_combined` view with additional UNION ALL selecting from the new table
4. **import.py:** Register parser in `PARSERS` dict (key = output_name)
5. **import.py:** Register in `TABLE_NAMES` (map parser key → DB table name)
6. **import.py:** Add to `COLUMN_WHITELIST` if new columns exist

## Verification Command

```bash
# After rebuilding schema and importing, verify all tables:
sqlite3 finance.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"

# Check view includes all tables:
sqlite3 finance.db "SELECT sql FROM sqlite_master WHERE type='view' AND name='v_combined';"
```

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Error: no such table: lloyds` | init_schema.py missing CREATE TABLE | Add to SCHEMA_SQL |
| Rows inserted but not in v_combined | New table not in UNION ALL | Update view SQL |
| SQLite error on INSERT | Column whitelist missing new column | Update COLUMN_WHITELIST |
| Duplicate rows from format drift | Dedup key doesn't account for new format | Add sign/amount normalization |
