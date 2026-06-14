# Staggered Time Series Forward-Fill Pattern

When plotting multiple accounts/categories over a shared month axis, each trace
must have exactly the same array length. If accounts start or end at different
dates, naive per-account pivoting produces ragged arrays → IndexError.

## Problem

```python
# SQL returns sparse data — Lloyds only has rows 2017-12 to 2020-03,
# Vanguard Pension starts in 2022-03. Pivoting gives different lengths:
account_data = {
    'Lloyds':           [3345, 3200, ...],  # 28 entries
    'Vanguard Pension': [4695, 0, ...],      # 52 entries
}

# This blows up:
nw = sum(account_data[acct][i] for acct in account_data)
# IndexError when i >= 28 for Lloyds
```

## Solution: Two-Pass Padding

### Pass 1: collect raw month→value map

```python
from collections import defaultdict

raw_data = defaultdict(dict)  # account -> {month: amount}
for date, account, amount, kind in rows:
    raw_data[account][date] = amount

all_months = sorted(set(r[0] for r in rows))
```

### Pass 2: pad each account to full month range

```python
from datetime import date

chart_end = all_months[-1]

for acct, month_map in raw_data.items():
    values = []
    last_val = 0.0
    has_started = False
    last_data_month = max(month_map.keys()) if month_map else None

    # Detect if account is still active
    active = False
    if last_data_month:
        lm = date.fromisoformat(last_data_month)
        ce = date.fromisoformat(chart_end)
        active = (ce - lm).days <= 93  # ~3 months

    for month in all_months:
        if month in month_map:
            values.append(month_map[month])
            last_val = month_map[month]
            has_started = True
        elif has_started and (month <= last_data_month or active):
            # Within account's life or still active — forward-fill
            values.append(last_val)
        else:
            # Before first data or after account died
            values.append(0.0)

    account_data[acct] = values
```

## Key rules

1. **Before first data**: 0.0 (account didn't exist).
2. **Within active range**: forward-fill the last known value.
3. **After account closure** (last data > 3 months before chart end): 0.0. This
   prevents dead accounts from leaking stale balances into the present.
4. **Still-active accounts** (last data ≤ 3 months before chart end):
   forward-fill to chart end. Without this, an account whose last transaction
   was April shows £0 in June even though it's still open.

## Why 3 months (93 days)?

Monthly snapshots. An account missing for 1-2 months likely just had no
transactions. Missing for 3+ months = likely closed. Adjust the threshold for
your data granularity.

## Closures that go to zero naturally

Some closed accounts reach £0 naturally (NatWest mortgage paid off). The
forward-fill carries £0 forward, which is correct. No special handling needed.
