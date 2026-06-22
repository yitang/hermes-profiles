# Post-Refactor Build Verification

When a large refactor moves files, renames directories, splits modules, or adds new
wiring (registry entries, detection routes, import paths, config locations), unit
tests and dry-runs are NOT sufficient verification. The tests may pass because they
use temp DBs or mock paths. A dry-run may skip steps that only fail at runtime.

**The rule:** after any restructure that touches data pipeline wiring, run a full
real rebuild against the actual source data and verify:

1. All sources appear in the output
2. New registry entries (PARSERS, TABLE_NAMES, COLUMN_WHITELIST) are complete
3. Config imports resolve at runtime (not just during pip install)
4. Derived steps (balances, holdings, balance sheet) all produce rows
5. Row counts are reasonable vs baseline

## Pitfalls this catches (example from personal-finance-data restructure)

### Missing TABLE_NAMES entries
Adding `vanguard` and `lg_workpension` to `PARSERS` but not `TABLE_NAMES` → "no parser/table for key" at runtime. Dry-run showed the keys detected but wouldn't have caught the insert failure.

### Config import path after pip install -e
`from config.X import Y` works during development (repo root in path) but fails when
run as `pipeline rebuild` (editable install only adds `src/` to sys.path). Only a
real rebuild catches this — `pip install -e . && python3 -c "import X"` tests
pass because the cwd adds the path.

### Detection routing gaps
L&G CSVs nested under `lg-workplace-pension/transaction/` — folder detection saw
`transaction` not `lg-workplace-pension`. Dry-run showed them as SKIPPED but the
error message was generic. A real rebuild with the parser registered revealed the
detection gap.

### Derivative dependency order
After moving mortgage config, the mortgage step silently failed (caught by try/except
in rebuild.py). Without reading the rebuild output carefully, you'd miss that 304
mortgage rows and 550 balance sheet rows were missing.

## Procedure

```bash
# 1. Record baseline counts
sqlite3 finance.db "SELECT source_name, COUNT(*) FROM transactions GROUP BY source_name;" > before.txt

# 2. Full rebuild
pipeline rebuild 2>&1 | tee rebuild.log

# 3. Check all derived steps succeeded
grep '✗' rebuild.log  # should be empty

# 4. Compare counts
sqlite3 finance.db "SELECT source_name, COUNT(*) FROM transactions GROUP BY source_name;" > after.txt
diff before.txt after.txt  # understand any differences
```
