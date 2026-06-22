# Financial Data Format Selection — OFX vs CSV

**Context:** Personal finance data pipeline where users download bank/credit card
statements and import them into a database. Banks typically offer multiple export
formats (CSV, OFX, QIF, Excel, QuickBooks). This document covers which to choose
and how to design a pipeline that supports multiple formats.

## Format comparison

| Feature | CSV | OFX |
|---------|-----|-----|
| Unique transaction ID | Rare — none of the major UK retail banks (Barclays, HSBC, Lloyds) provide one | **FITID** — guaranteed unique per transaction from the bank |
| Standardised | No — each bank uses its own column layout | Yes — OFX 1.x SGML or 2.x XML is bank-agnostic |
| Human-readable | Yes — opens in any spreadsheet app | No — raw XML/SGML |
| Parser complexity | Easy — stdlib csv module | Moderate — regex or XML parser needed |
| Schema change risk | High — banks rename/reorder columns | Low — standardised tag names |
| False dedup risk | Low — (date+amount+description) is sufficient in practice but not provably unique | **Zero** — FITID is a guaranteed unique key |

**Rule of thumb:** Use OFX when the bank offers it. Fall back to CSV. Avoid
proprietary formats (QuickBooks QBO, Quicken QFX, Microsoft Money) unless
you're using that specific software.

## Detecting format at import time

Two strategies work well together:

1. **File extension** — `.ofx` files go through the OFX parser. `.csv` files go
   through CSV header detection. Easy, unambiguous.

2. **Content sniffing** — OFX files start with `OFXHEADER:100`. If you read the
   first line and see that, route to OFX even if the extension is wrong.

For OFX the detection is by filename pattern, not header columns. A naming
convention helps:

```
hsbc_current.ofx     → current account table
hsbc_credit.ofx      → credit card table
```

## OFX parsing approach

OFX 1.x uses SGML (not XML) — it's tag-based but with no strict schema, no
namespaces, and some non-standard constructs. A regex-based extractor on
`<STMTTRN>` blocks is more reliable than an XML parser:

```python
import re

def parse_ofx_transactions(filepath):
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    content = content.replace('\r\n', '\n')
    blocks = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', content, re.DOTALL)
    txns = []
    for block in blocks:
        txn = {}
        for tag in ['TRNTYPE', 'DTPOSTED', 'TRNAMT', 'FITID', 'NAME', 'MEMO']:
            m = re.search(rf'<{tag}>(.*?)</{tag}>', block, re.DOTALL)
            txn[tag] = m.group(1).strip() if m else ''
        txns.append(txn)
    return txns
```

Key fields:
- **FITID** — primary key for dedup. Use this as the UNIQUE constraint.
- **DTPOSTED** — date in YYYYMMDDHHMMSS format. Extract first 8 chars.
- **TRNAMT** — signed decimal (negative = debit/spend, positive = credit)
- **TRNTYPE** — CREDIT, DEBIT, OTHER, etc.
- **NAME** — payee/merchant name
- **MEMO** — additional description (may be empty)

## Extending a pipeline with a new format

When a new file format needs support, the pattern is:

1. **Create parser function** — reads the file, returns list of dicts matching
   the target table schema
2. **Register in parser registry** — add to `PARSERS` dict with a unique key
3. **Map to table** — add to `TABLE_NAMES` dict
4. **Add detection** — extension-based or content-based
5. **Add column whitelist** — if new table, update `COLUMN_WHITELIST`

This pattern works for both CSV-variant (new header pattern) and cross-format
(OFX, JSON, etc.) additions. Each is a separate parser key with its own
detection rule.
