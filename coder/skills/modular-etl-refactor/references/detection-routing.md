# Account Detection & Routing Logic

Pattern extracted from personal-finance-data pipeline: detecting which parser should handle an incoming CSV/OFX file based on headers, filename hints, and folder context.

## Problem Statement

When files are placed in a shared inbox without subdirectory structure, the detection logic must infer the account type from headers alone — which is ambiguous when multiple banks produce 3-col (date, description, amount) CSVs.

### The Bug
Lloyds cleaned CSV (4 columns: Date, Description, Amount, Balance) was misdetected as HSBC Credit Card because both share similar header patterns and no unique identifier could distinguish them.

## Detection Strategy: Filename Hints > Header Matching > Reject

### Step 1: Check folder context first
Files in known subdirectories (`inbox/`, `amex/`, `barclays/`, etc.) have reliable folder-based routing. This is the **only** time ambiguous header patterns should be auto-routed.

```python
folder = os.path.basename(os.path.dirname(filepath)).lower()
is_inbox = folder == 'inbox'
```

### Step 2: Filename hints (for flat inbox files)
When no folder context or in inbox, check filename for known hints **before** header analysis:

```python
FILENAME_HINTS = {
    'lloyds': 'lloyds_cleaned',  # catches lloyds.csv, my_lloyds_export.csv, etc.
    'amex': 'amex_ba',            # catches amex_test.csv, amex_transactions.csv, etc.
}

for hint, parser in FILENAME_HINTS.items():
    if hint in fname:  # substring match — NOT exact equality
        return parser
```

### Step 3: Header feature matching (most specific first)
Only reach header matching when filename hints fail or folder context provides routing.

**Key rules:**
- Check unique headers early (Barclays has `Number`, Lloyds raw has `Transaction Date`)
- Use substring/contains matching (`'account' in 'account type'`), never exact equals
- Count columns — many banks have a unique column count
- 3-col files are the most ambiguous — only auto-route if folder context exists

**Column matching helper:**
```python
def _col_matches(header_lower, keyword):
    for col in header_lower:
        if keyword in col:  # substring match
            return True
    return False
```

### Step 4: Reject rather than default
When a file can't be confidently identified, **return `None`** instead of guessing. Better to reject an unknown file than insert it into the wrong table (which is worse than never inserting).

```python
# Bad: defaults to something
if ambiguous:
    return 'hsbc_credit_cleaned'  # might be wrong!

# Good: explicit rejection
return None
```

## Per-Source Header Patterns

| Source | Unique Headers | Column Count | Notes |
|--------|---------------|--------------|-------|
| Barclays | `Number` | 6+ | Only bank with Number column |
| AMEX Gold (native) | `DateProcessed`, `Cardmember` | 13 | Most columns, very specific |
| AMEX BA (cleaned) | `Type`, `Category`, `Notes` | 6 | Needs all three extra cols |
| Lloyds raw | `Transaction Date`, `Debit Amount`, `Credit Amount` | 8 | Unique 3 debit/credit system |
| HSBC Premier 5-col | `Account Type`, `Subcategory` | 6 | Has both account AND subcategory |
| HSBC Credit cleaned | `Balance` column | 4 | Date, Description, Amount, Balance |
| Generic inbox CSV | Any date+amount combo | 3-4 | Reject unless filename hint matches |

## OFX Detection Pattern
OFX files are detected by **content inspection** — looking for specific XML tags:
- `BANKACCTFROM` → bank checking/savings account
- `CCACCTFROM` → credit card account
- Also check folder context (`hsbc/`, `barclays/`) first before content scanning

## Testing
Always verify detection with synthetic CSV headers before deploying changes. Use temp files in memory to test header parsing without touching real data:

```python
fd, path = tempfile.mkstemp(suffix='.csv')
os.write(fd, ','.join(headers).encode('utf-8'))
os.close(fd)
result = detect_account(path)  # verify
os.unlink(path)
```

Remember to clear `__pycache__` after changing detection logic — stale `.pyc` files cause tests to return cached results.