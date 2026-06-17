# OFX Balance Computation Guide

## Overview

When bank exports include OFX (Open Financial Exchange) files, they contain `<LEDGERBAL>` tags with the account balance as of a specific date. Use this anchor to compute running balances for all rows.

## Parsing OFX LEDGERBAL

```python
import xml.etree.ElementTree as ET

def parse_ledgerbal(ofx_file):
    """Extract ledger balance and its date from an OFX file."""
    with open(ofx_file) as f:
        content = f.read()
    
    # Strip OFX wrapper tags, keep only the XML portion
    xml_start = content.find('<STMTTRNRS>')
    xml_end = content.rfind('</STMTTRNRS>') + len('</STMTTRNRS>')
    if xml_start == -1 or xml_end == -1:
        return None, ''
    
    xml_content = content[xml_start:xml_end]
    root = ET.fromstring(xml_content)
    
    # Navigate to LEDGERBAL
    bal_el = root.find('.//LEDGERBAL')
    if bal_el is None:
        return None, ''
    
    amount = bal_el.findtext('BALAMT', '').strip()
    date = bal_el.findtext('DTASOF', '').strip()
    # Remove OFX timestamp suffix (e.g. "20260605143000" → "2026-06-05")
    if len(date) >= 8:
        date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    
    return amount, date
```

## Backward-Winding Algorithm

The anchor represents the balance **at** the anchor date. All rows on or before that date need balances computed backwards from it.

```python
def compute_balance(rows, ledger_bal):
    """
    Compute running balances by backward-winding from OFX LEDGERBAL.
    
    Logic:
    1. Start with the ledger balance at the anchor date
    2. Walk rows in REVERSE chronological order
    3. For each row: current_balance = next_row_balance - transaction_amount
       (subtract because amounts are already signed: debit=positive, credit=negative)
    4. Reverse back to forward order
    
    Args:
        rows: list of dicts with 'amount' key (as string or float)
        ledger_bal: dict with 'amount' (str) and 'date' (str), or None
    """
    if not rows or not ledger_bal:
        for r in rows:
            r['balance'] = 0
        return
    
    start_bal = float(ledger_bal['amount'])
    
    # Build balances backwards
    current = start_bal
    balances = []
    for r in reversed(rows):
        balances.append(current)
        amount = float(r.get('amount', '0'))
        current -= amount  # subtract the transaction to get previous balance
    
    # Reverse to forward order and assign
    for i, r in enumerate(rows):
        if i < len(balances):
            r['balance'] = round(balances[i], 2)
        else:
            r['balance'] = 0
```

## Sign Convention Pitfalls

Different banks use different sign conventions:

| Bank | Positive means | Negative means | Formula to compute previous balance |
|------|---------------|----------------|-------------------------------------|
| Barclays (CSV export) | Credit/Deposit | Debit/Withdrawal | `prev = current - amount` |
| Amex (some exports) | Purchase (debit) | Payment (credit) | `prev = current + amount` |

**Rule of thumb:** If the anchor balance is positive and amounts are mostly negative, you're likely dealing with a "customer perspective" format where negative = spending. The subtraction formula (`current - amount`) still works because subtracting a negative adds.

**To verify:** After computing balances, check:
- Does `balance[-1]` match the anchor?
- Are early-period balances reasonable (not astronomically large or small)?

## Edge Cases

1. **OFX file covers only future rows:** If some CSV rows have dates AFTER the OFX anchor date, the backward-winding won't cover them. Consider:
   - Including those rows with `balance=0` (conservative)
   - Or using forward-winding from the anchor for post-anchor rows

2. **Multiple OFX anchors per account:** Take the LATEST one (highest date). The earlier ones are superseded.

3. **OFX without LEDGERBAL:** Some OFX exports only have `<BALASOFPENDING>`. This is less reliable — prefer `LEDGERBAL` which is the settled balance.

4. **Decimal separators:** OFX uses period as decimal separator (`10489.67`). Ensure no locale conversion happens.
