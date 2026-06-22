# Bank CSV Format Reference

This file documents the exact CSV column layouts found in the user's banking data at `/home/tangyi/data/primary/data_finance/banking/`, and maps each to the parser that handles it.

Last verified: 2026-06-04 — all 41 files tested, 41/41 pass.

## Batch Test Command

```bash
curl -s -c /tmp/pfin_cookies.txt -X POST http://localhost:8125/login -d "user_id=admin" > /dev/null
for f in /home/tangyi/data/primary/data_finance/banking/*.csv; do
  name=$(basename "$f")
  result=$(curl -s -b /tmp/pfin_cookies.txt -F "file=@$f" http://localhost:8125/api/import/parse-preview)
  ok=$(echo "$result" | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok=d.get('ok','?'); fmt=d.get('format','?'); rows=d.get('total_rows','?')
if not ok: print(f'FAIL:{d.get(\"error\",\"?\")}  {fmt:<25} {name}')
else: print(f'OK  {fmt:<25} {rows:>6}  {name}')
")
  echo "$ok"
done
```

## Results Matrix

**41/41 passing** as of 2026-06-04.

| File | Parser | Notes |
|------|--------|-------|
| `Amex_2020_March.csv` | AmexOldParser | 13-col, £-prefixed amounts, "03 Apr 2020" dates |
| `amex_ba_2024.csv` | AmexBA_2024Parser | 283 rows |
| `amex_ba_2024_slim.csv` | AmexBA_2024Parser | Empty file |
| `amex_gold_2020.csv` | AmexGoldParser | 13 rows |
| `amex-gold-2021.csv` | AmexGoldParser | 277 rows |
| `amex_gold_2022.csv` | AmexGoldParser | 635 rows |
| `amex_gold_2023.csv` | AmexGoldParser | 592 rows |
| `amex_gold_2024.csv` | AmexGoldParser | 249 rows |
| `Barclays_2019_2023.csv` | BarclaysPremierParser | Number,Date,Account,Amount,Subcategory,Memo |
| `barclays_premier_2020-2024.csv` | BarclaysPremierParser | 114-253 rows |
| `barclays_Transactions_2017_2020.csv` | BarclaysLegacyParser | Account,Date,OriginalDescription,Amount,L1Tag |
| `hsbc_premier_2020-2024.csv` | HSBCParser | 41-150 rows, lowercase headers handled |
| `lloyds_*.csv` (26 files) | BarclaysParser | 17-1384 rows, header sniffing corrects filename |

## Column Layouts

### Amex Gold — 9-col (quoted, 2020-2021)
`"Account","Date","Original Date","Description","Original Description","Amount","Currency","Category","Budget"`
Parser: AmexGoldParser

### Amex — 5-col (2022-2023)
`Date,Description,Card Member,Account #,Amount`
Parser: AmexGoldParser

### Amex — 13-col (2024+)
`Date,Description,Card Member,Account #,Amount,Extended Details,...`
Parser: AmexGoldParser

### Amex — March 2020 (13-col, quoted, £ prefix)
`"Date","Date Processed","Description","Cardmember","Amount","Foreign Spend Amount",...`
Example: `"03 Apr 2020","","TESCO","","-£3.50",...`
Parser: AmexOldParser

### Amex BA (2024)
`Date,Description,Amount,Extended Details,Appears On Your Statement As,...`
Parser: AmexBA_2024Parser (handles +/-/T prefixes)

### Barclays / Lloyds (same format, 26 files)
`Transaction Date,Transaction Type,Sort Code,Account Number,Transaction Description,Debit Amount,Credit Amount,Balance`
Files named lloyds_*.csv but Barclays column layout. Parser: BarclaysParser

### Barclays Premier
`Number,Date,Account,Amount,Subcategory,Memo`
Parser: BarclaysPremierParser

### Barclays Transactions (older export)
`"Account","Date","OriginalDescription","Amount","L1Tag","L2Tag","L3Tag",`
Parser: BarclaysLegacyParser (ISO dates handled by flexible _parse_date)

### HSBC
`date, desc, amount`
All lowercase — handled by case-insensitive _get_ival. Parser: HSBCParser

## Detection Design

`detect_parser()` in `import_parsers.py` uses a PARSER_TABLE with header column matching first, then FILENAME_PATTERNS fallback:

1. Split header row into column names (lowercased)
2. Iterate PARSER_TABLE in order — first match wins
3. Each entry: `(parser_class, [pattern, pattern, ...])` — ALL patterns must appear in any column
4. If no header match, fall back to filename keywords

More specific patterns first (AmexOldParser before AmexGoldParser, BarclaysParser before generic fallbacks).

Key helpers:
- `_get_ival(row, ...keys)` — case-insensitive column lookup
- `_parse_date(val)` — DD/MM/YYYY, YYYY-MM-DD, "DD Mon YYYY", "DD-Mon-YY"
- `_clean_amount(val)` — strips £, $, €, commas before float

## Adding a New Bank Format

1. Create parser class in `pfin-core/pfin_core/import_parsers.py` subclassing `CSVParser`
2. Add header pattern entry to PARSER_TABLE
3. Add filename fallback to FILENAME_PATTERNS
4. Test via curl against the actual CSV file
5. Extend _parse_date / _clean_amount if new format has novel date/amount representations
