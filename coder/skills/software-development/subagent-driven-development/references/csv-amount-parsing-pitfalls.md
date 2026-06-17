# CSV Amount Parsing Pitfalls

Real-world lesson from the inbox-to-SQLite finance pipeline.

## Commas as thousands separators

Bank CSVs sometimes quote amounts with thousands separators:

```
2022-02-23,,"4,976.01",,B E CR
```

If the parser does `row[2].strip()` (seed.py), the stored value is `"4,976.01"`
(with quotes and comma). A second parser using `parse_amount()` (import.py, which
strips `£`, `,`, and whitespace) produces `4976.01`. These create different dedup
keys — the same transaction appears twice in the DB.

**Fix amount parsing early** — before any seed/import step. Always:
```python
amount = val.replace('£', '').replace(',', '').replace('\xa3', '').strip()
```

## Currency symbols

Bank exports vary:
- `£` (pound sign, U+00A3) — most common
- `\xa3` (raw byte A3, latin-1 encoding) — appears when encoding is misdeclared
- No symbol at all (just a signed number)

Always strip `£` and `\xa3` before storing. The `utf-8-sig` encoding handles BOM.

## Signed vs unsigned amounts

Different banks use different conventions:
- Standard: debits are negative (`-17.44`), credits positive
- AMEX March 2020 export: debits are positive (`48.45`), refunds negative
- Some HSBC files: amounts are unsigned, credit/debit distinguished by column

When building a single amount column parser, keep it raw — store whatever the
bank provides. Handle sign normalisation in the consuming application (the app
DB), not in the golden source.

## Quoted fields with commas

CSV `reader` handles quoted fields correctly:
```
"4,976.01"  →  ['4,976.01']  (single string, comma preserved)
```
But if you then do `row[2].strip()`, the comma stays. You need to explicitly
remove it.
