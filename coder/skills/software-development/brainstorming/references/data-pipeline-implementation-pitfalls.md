# Data Pipeline Implementation Pitfalls

**Context:** Implementation of an inbox-to-SQLite pipeline for personal finance
data. Two bugs found during the subagent-driven execution phase (after spec
approval). These are general lessons for any CSV-to-DB ingestion pipeline.

## Pitfall 1: Dedup key mismatch between seed and import paths

**Scenario:** Two code paths parse the same CSV format — a one-time seed script
(reads by column position) and a daily import script (reads by column header
name). Both produce rows with a dedup UNIQUE constraint on
`(date, amount, description_lower)`.

**Bug:** The seed script did `row[2].strip()` for the amount field, while the
import script did `row[2].replace(',', '').strip()`. For HSBC exports with
thousands-separator amounts (e.g. `"4,976.01"` — note the CSV-quoted commas),
the seed produced `amount = '4,976.01'` but the import produced
`amount = '4976.01'`. The UNIQUE constraint didn't catch the duplicate because
the dedup keys differed.

**Symptoms:** After seed + import both ran on the same file, the HSBC table had
579 rows instead of 457 (122 extras). The INSERT OR IGNORE skipped nothing
because every key was unique-in-its-own-format.

**Root cause:** Two code paths applying different cleaning to the same column
before computing the dedup key. Neither path was wrong individually — they just
disagreed.

**Fix:** Standardise the amount-cleaning function (`parse_amount()` — strip £,
commas, whitespace) and use it in BOTH the seed script and import script. Or
better: have the seed script use the SAME parser functions as the import script
instead of duplicating parsing logic.

**General rule:** In any pipeline with separate seed and import paths, the dedup
key derivation MUST be a single shared function. Never duplicate the cleaning
logic — they will inevitably diverge.

## Pitfall 2: SQL injection via CSV column headers in INSERT

**Scenario:** A generic `insert_rows()` function takes parsed row dicts (keys
from CSV header names) and interpolates them into an INSERT statement:

```python
col_names = ','.join(rows[0].keys())
sql = f'INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})'
```

**Risk:** Column names come from CSV header labels. A malicious or mangled CSV
could have a header like `date,amount,description_lower); DROP TABLE barclays;--`
— and that string would be interpolated directly into the SQL.

**Fix:** Whitelist column names against the known schema per table before
interpolation:

```python
COLUMN_WHITELIST = {
    'barclays': {'date', 'number', 'account', 'amount', 'description_lower', ...},
    'amex_gold': {'date', 'description', 'amount', 'description_lower', ...},
    ...
}

allowed = COLUMN_WHITELIST.get(table, set())
invalid = [c for c in cols if c not in allowed]
if invalid:
    raise ValueError(f'Invalid column(s) for {table}: {invalid}')
```

**General rule:** Any code path that maps external data (CSV headers, API
responses, user input) to SQL column names must validate against a known
whitelist. Table names from a `TABLE_NAMES` dict (trusted internal source)
are safe; column names from the data are not.

## Pitfall 3: File handle leaks in parser functions

**Scenario:** Parser functions read the CSV header with a helper that opens the
file and returns the file handle alongside the header and reader:

```python
header, reader, f = _read_csv_header(filepath)
# ... parse rows ...
f.close()
```

**Bug:** If an exception occurs during parsing (malformed row, unexpected data
type), `f.close()` is never reached. The file handle leaks until GC.

**Fix:** Wrap the parser body in try/finally:

```python
header, reader, f = _read_csv_header(filepath)
try:
    for row in reader:
        # ... parse ...
finally:
    f.close()
```

Or better: use a context manager inside the helper so the handle is scoped
properly.

**General rule:** Any function that opens a file and returns the handle to the
caller for closing is fragile. Prefer context managers. If returning the handle
is unavoidable (because the caller needs the reader too), wrap the body in
try/finally.

## Pitfall 4: Archive filename collision on same-day runs

**Scenario:** Archive filenames use `datetime.now().strftime('%Y-%m-%d')` as a
prefix. If import.py runs twice on the same day, the second file overwrites
the first.

**Fix:** Add a time component: `%Y-%m-%d_%H%M%S`. Or use a UUID. Or append a
counter.

**General rule:** Archive/backup filenames should be unique within the expected\nrun frequency. Daily prefix is too coarse if the script can run multiple times\nper day.

## Pitfall 5: `float(None)` from a NULL database column

**Scenario:** A row-mapping function reads a numeric column from a SQLite query\nand immediately casts it: `amount = float(row["amount"])`. If the column is\nNULL in the DB, `sqlite3.Row` returns `None`, and `float(None)` raises\n`TypeError`. A single NULL in thousands of rows crashes the entire pipeline.

**Bug:** The source schema showed the column as non-nullable but a rogue\nimport or migration left a NULL. No defensive guard.

```python\n# BUG — crashes on None\namount = float(row["amount"])\n\n# FIX — guard against None\nraw = row.get("amount")\namount = float(raw) if raw is not None else 0.0\n```

**Variant:** The same pattern hits `int()` on None, `datetime.fromisoformat()`\non None, and `len()` on None.

**General rule:** Every column from a database read is potentially None,\nregardless of the declared schema. Guard all numeric/time casts at the first\npoint of use, not at the calling site. Use `row.get("col")` + conditional,\nnot direct indexing + try/except.

## Pitfall 6: Feature-flag setup that skips dependent infrastructure

**Scenario:** A sync pipeline has a `--dry-run` flag that skips creating the\ntracking table (`_sync_log`) because no data will be written. But the read\npath calls `_get_last_sync_date()` which queries that table. On a fresh\ndatabase, the SELECT raises `sqlite3.OperationalError: no such table`.\nDry-run on first use crashes instead of reporting what would happen.

**Bug:** The feature flag (`dry_run`) conditionally skips setup but the\ndependent code doesn't know about the flag:

```python\n# dry-run: table is NOT created\nif not dry_run:\n    _ensure_sync_log(pfin_db)\n\n# ... later in same function, regardless of dry_run:\nlast_date = _get_last_sync_date(pfin_db, table, account_name)\n# CRASH: _sync_log table doesn't exist\n```

**Fix 1:** Make the read path resilient to missing infrastructure:

```python\ndef _get_last_sync_date(...):\n    try:\n        # query _sync_log\n    except Exception:\n        return None   # no prior sync = first run\n```

**Fix 2:** Create the tracking table unconditionally (it's a 6-line DDL,\nnot a performance concern).

**General rule:** Any feature-flag mode (dry-run, preview, read-only) that\nconditionally skips setup steps must audit every downstream code path that\nassumes the setup was done. The cheapest fix is usually "do the harmless\nsetup unconditionally" — a CREATE TABLE IF NOT EXISTS weighs nothing.

## Pitfall 7: Unvalidated `float()` and `date.fromisoformat()` in row mapping

**Scenario:** Row mapping functions trust that all source columns contain\nvalid values for their expected type. A single corrupt date string or\ngarbage amount field crashes the entire pipeline.

```python\n# BUG — assumes every date is valid ISO-8601\nreturn date.fromisoformat(raw.split("T")[0])\n\n# FIX — catch and fall back\ntry:\n    return date.fromisoformat(raw.split("T")[0])\nexcept (ValueError, TypeError):\n    return date.today()  # or log and skip row\n```

**The same applies to `float()` and `int()`** on amounts, quantities, and\nother numeric fields. The data source may have empty strings, "N/A", or\nlocale-formatted numbers (`1.234,56`) that crash a naive cast.

**General rule:** Every row-mapping function in a data pipeline is a\ntransformation boundary — treat all input as untrusted. Guard every\n`float()`, `int()`, and `date.fromisoformat()` with validation that either\nskips the row (log + continue) or falls back to a safe default. A pipeline\nthat crashes on one bad row is a pipeline that needs manual babysitting.
