# CSV Detection Ambiguity in Financial Import Pipelines

## Problem

Bank/credit-card CSV exports often use identical minimal headers:
```
Date,Description,Amount,balance
```
Multiple account types produce this exact header (Lloyds current account, HSBC Credit Card, AMEX BA 3-col export). When placed in a flat inbox without folder context, detection must rely solely on headers — which is ambiguous.

## Pattern: Filename-First Disambiguation

When header matching alone can't distinguish between accounts, **filename is the next-most-reliable signal** (users typically name exports after the bank):

```python
def detect_account(filepath):
    fname = os.path.basename(filepath).lower()
    folder = os.path.basename(os.path.dirname(filepath)).lower()
    # ... read header into lheader ...

    # --- filename guards BEFORE ambiguous header fallbacks ---
    if is_inbox:  # flat file, no folder context
        if 'lloyds' in fname:
            return 'lloyds_cleaned'
        if 'amex' in fname:
            return 'amex_ba'
        if 'hsbc_credit' in fname:
            return 'hsbc_credit_cleaned'

    # --- header-based detection (only reached after filename guards) ---
    if len(lheader) >= 3 and all(c in lheader for c in ['date','amount']) \
       and 'account' not in lheader and 'subcategory' not in lheader:
        return 'hsbc_credit_cleaned'
```

## Pitfalls

- **Don't skip filename checks when files are in a flat inbox.** Folder context (`data/raw_clean/<account>/`) solves this naturally; flat inbox files need filename matching.
- **The catch-all header pattern is dangerous.** A generic `date + amount` detection without prior disambiguation will silently misroute files. Always add explicit guards before broad patterns.
- **Header-only matching breaks when CSV formats evolve.** Banks change column layouts (e.g., AMEX Gold 13-col → 4-col cleaned). Filename-based routing is more stable than header heuristics.

## Detection Priority Order

```
1. Folder context (data/raw_clean/<account>/) — highest confidence
2. Filename matching (barclays.csv, amex_gold.csv) — high confidence for flat inbox
3. Header pattern matching (specific column names) — medium confidence
4. Header catch-all (date + amount) — lowest confidence, only reached after guards
```
