---
name: modular-etl-refactor
description: Convert monolithic import/batch scripts into structured Python ETL pipeline packages with detection, parsing, and insertion layers.
category: software-development
---

# Modular ETL Refactoring

Convert a monolithic import/batch script into a structured Python ETL pipeline package.

## Triggers
- User asks to restructure a flat import script
- Codebase has 8+ standalone scripts in the root directory
- Need to add missing components (logging, config, validation) to an existing pipeline
- Inbox/file routing bugs exist in detection logic

## Approach

1. **Analyse first** — read ALL scripts, map data flow: file → parse → transform → insert → archive
2. **Define boundaries** — separate detection/routing from parsing from database insertion
3. **Build core layer** — config (paths), schemas (SQL), detection (routing)
4. **Build parser layer** — CSV/OFX parsers per source, all returning canonical row dicts
5. **Build importer layer** — detect → parse → insert → archive pipeline function
6. **Preserve backwards compatibility** — root wrapper scripts delegate to package
7. **Verify with synthetic tests** — test detection with fake CSV headers before touching real data

## Pitfalls

### Inbox/ flat file routing
Files dropped without folder context need filename hints as fallback, not header guessing. Reject ambiguous files rather than defaulting to wrong parser. This is the #1 cause of misrouted data (e.g. Lloyds CSV routed to HSBC Credit Card).

Filename hint pattern:
```python
FILENAME_HINTS = {
    'lloylds': 'lloyds_cleaned',  # catches both raw and cleaned
    'amex': 'amex_ba',             # AMEX BA Premium
}

for hint, parser in FILENAME_HINTS.items():
    if hint in fname:  # substring match, not exact
        return parser
```

### Editable install stale cache
After rewriting module files under `pip install -e .`, clear `__pycache__` before re-running tests — Python serves stale `.pyc`. Use `find . -name "__pycache__" -exec rm -rf {} +`.

### Column name matching
Real-world CSV headers vary (e.g. "Account Type" vs "account"). Always use substring/contains matching, never exact equals:
```python
def _col_matches(header_lower, keyword):
    for col in header_lower:
        if keyword in col:  # NOT ==, use 'in'
            return True
    return False
```

### UTF-8 BOM
UK bank CSVs consistently use `utf-8-sig` encoding. Always specify explicitly when opening CSV files.

## File Structure Template

```
src/<package>/
├── __init__py          # version + public API exports
├── config.py            # all paths, constants (single source of truth)
├── schemas.py           # consolidated SQL schema from init_schema.py
├── detection.py         # detect_account(), detect_ofx_account() — routing logic
├── parsers/
│   ├── __init__py      # PARSERS dict: {account_type: parser_fn}
│   ├── base.py          # shared utilities (try_date, normalise, parse_amount)
│   ├── csv/
│   │   ├── barclays.py  # per-source CSV parsers
│   │   ├── hsbc.py
│   │   ├── amex.py
│   │   └── lloyds.py
│   └── ofx.py           # OFX transaction extraction
└── importers/
    └── __init__py      # main pipeline function (detect→parse→insert→archive)
```

## Detection Rule Hierarchy

Most specific checks first:
1. Filename hints → returns immediately (inbox fallback)
2. Header feature match → column name analysis
3. Column count + required keywords
4. Reject ambiguous files with no context

See references/detection-routing.md for the complete routing logic and inbox bug patterns.

## Support Files

- `references/detection-routing.md` — detailed detection algorithm, per-source header patterns, OFX tag-based routing
- `scripts/test_detection_template.py` — reusable template for writing account detection test cases (copy to your project)