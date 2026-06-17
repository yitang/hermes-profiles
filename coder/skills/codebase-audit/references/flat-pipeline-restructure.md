# Restructuring Flat Python Data Pipelines

## Target State for Small-Scale Financial Data Pipelines

When reviewing a flat project where all scripts live at root level (e.g., `import.py`, `compute_balances.py`, `mortgage.py`), the following structure is the minimal improvement that yields real value without over-engineering:

### Recommended Structure
```
src/pipeline_name/          # proper package
    __init__.py
    config.py               # shared constants: DB_PATH, INBOX_DIR, ARCHIVE_DIR
    cli.py                  # unified entry point
    detection.py            # account/file routing logic
    schemas.py              # database schema definitions
parsers/csv/                # all CSV parsers per account type
    base.py                 # shared helpers (try_date, parse_amount, _make_source_id)
    barclays.py
    amex.py
    hsbc.py
    lloyds.py
parsers/ofx.py              # OFX parsing (shared across banks)
importers/
    bank_import.py          # inbox scanning + archiving pipeline
computations/               # downstream processing
    running_balances.py
    holdings.py
    mortgage.py
    balance_sheet.py
pyproject.toml              # project metadata, entry points
tests/
data/raw_clean/             # permanent source-of-truth (unchanged)
docs/
```

## Missing Components Checklist

| Component | Why It Matters | Effort |
|---|---|---|
| `config.py` (shared paths) | Every script hardcodes `DB_PATH`, `INBOX_DIR` — changes require edits in 7+ files | Low |
| `cli.py` (orchestration) | No single command to run full rebuild; user must remember script order and arguments | Low |
| Proper logging | All scripts use `print()` — no log levels, no structured output for debugging | Medium |
| Detection tests | Account routing logic has zero test coverage; bugs like Lloyds→HSBC misrouting slip through silently | Low |
| Schema module | `init_schema.py` exists but schema isn't importable by other modules | Low |

## Key Principles

- **Keep scripts idempotent** — all compute scripts should support re-running without corrupting data (`INSERT OR REPLACE`, DROP + CREATE).
- **One canonical path per source** — never duplicate logic across multiple scripts. If two parsers handle the same account type, factor out the shared part.
- **Flat inbox is a processing layer, not storage** — inbox files are temporary copies of permanent sources. Processing should move them to archive after success.
- **Adapt to scale** — no Kafka, Airflow, or dbt for a 7-script project. A single CLI entry point that orchestrates the rebuild sequence is sufficient.

## Before You Restructure

1. Verify all existing data is correct (run verification queries against the DB)
2. Fix any active bugs in detection/parsing BEFORE refactoring (refactoring while fixing bugs doubles error surface)
3. Run the full rebuild pipeline end-to-end on current code to establish a baseline
4. Then refactor — test each module independently as you extract it
