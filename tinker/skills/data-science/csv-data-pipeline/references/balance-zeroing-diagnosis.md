# Balance Zeroing Bug — Diagnostic & Fix Pattern

**Session origin:** 2026-06-10, personal-finance-data repo. Lloyds CSV had bank-computed running balances (-£24 to £26K) but DB showed zeros for all accounts except OFX-backed ones (Barclays, HSBC Premier).

## Symptoms

- Account has no OFX source file but CSV export already includes a running balance column
- DB shows `balance=0` or `balance` column missing entirely
- Other accounts with OFX anchors show correct balances
- Cleaned CSV also shows zero/null/missing balance values (even though raw CSV had real values)

## Root Causes (in order of likelihood)

### Cause 1: `clean.py` explicitly discards the bank's balance column
```python
# BAD — silently drops pre-computed value
r.pop('Balance', None)  # or 'balance' or any variant

# FIX — preserve it; just rename/normalize the key
for r in data_rows:
    if 'Balance' in r and 'balance' not in r:
        r['balance'] = r.pop('Balance')
```

### Cause 2: `compute_balance()` overwrites existing values when no OFX anchor
```python
# BAD — wipes existing balances
if not rows or not ledger_bal:
    for r in rows: r['balance'] = 0

# FIX — only default to 0 if field is missing/empty
if not rows or not ledger_bal:
    for r in rows:
        if 'balance' not in r or not r['balance'].strip():
            r['balance'] = 0
```

### Cause 3: `init_schema.py` lacks the column in CREATE TABLE
- Column added to clean output but not in DB schema → import silently skips it or crashes
- **Fix:** Add column to `CREATE TABLE` for every table that should have it

### Cause 4: Import parser doesn't extract the field into the INSERT dict
- Cleaned CSV has `balance` column but parser puts it in `extra` JSON blob instead
- Parser's insert dict lacks `'balance': lookup.get('balance', '')`
- **Fix:** Add balance extraction to every parser that encounters the column

### Cause 5: `COLUMN_WHITELIST` doesn't include the field name
- DB schema has the column but whitelist blocks it from INSERT
- **Fix:** Add `'balance'` (or whatever the new column is called) to all relevant whitelists

## Diagnostic Steps

```bash
# Step 1: Check raw CSV — does bank already compute balances?
head -5 data/raw/*lloyds*.csv | grep -i balance

# Step 2: Check cleaned output — are balances preserved?
head -5 data/cleaned/*.csv | grep -i balance

# Step 3: Check DB schema — does column exist?
sqlite3 finance.db "PRAGMA table_info(lloyds);" | grep -i balance

# Step 4: Check actual DB values — are they zero?
sqlite3 finance.db "SELECT MIN(balance), MAX(balance), COUNT(DISTINCT balance) FROM lloyds;"

# Step 5: If all steps pass but DB still wrong → parser bug
python3 -c "from import import parse_lloyds_cleaned; rows = parse_lloyds_cleaned('inbox/lloyds.csv'); print('balance' in rows[0])"
```

## Fix Checklist (all must be done together)

1. [ ] Remove any `r.pop('Balance', None)` / column deletion from clean.py
2. [ ] Update `compute_balance()` to preserve existing values when no anchor
3. [ ] Add column to `init_schema.py` CREATE TABLE for all affected tables
4. [ ] Add `'balance'` (or new field name) to `COLUMN_WHITELIST` in import.py
5. [ ] Update EVERY parser function that encounters the column to extract it into the insert dict
6. [ ] Rebuild DB from scratch: `rm finance.db && python3 init_schema.py && python3 import.py`
7. [ ] Verify with direct SQL query — don't assume staging imports worked incrementally

## Real Example (Lloyds fix)

- Raw CSV had `Balance` column with 5,233 unique values (-£24 to £26K)
- clean.py line 488: `r.pop('Balance', None)` → deleted it
- compute_balance(): zeroed all when no OFX anchor
- init_schema.py: no `balance` column for lloyds table
- parse_lloyds_cleaned(): didn't pass balance to insert dict
- COLUMN_WHITELIST: missing 'balance' for lloyds

All five issues fixed in one coordinated update. DB rebuilt → 5,349 rows with real balances.