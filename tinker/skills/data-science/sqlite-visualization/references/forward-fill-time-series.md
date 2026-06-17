# Forward-fill for Sparse Multi-Account Time Series

When charting multiple accounts that start and end at different times
on a shared monthly axis, naive pivoting produces arrays of unequal
length. This causes IndexError or missing data.

## The problem

Three accounts with different lifespans:
```
Barclays:    2018-01 ──────────────────────────────── 2026-06  (102 months)
ISA:                      2019-05 ──────────────────── 2026-06  (86 months)
Lloyds:      2017-12 ────── 2020-03                            (28 months)
```

If each account's array only spans its active months, the net worth
computation at index 50 fails because Lloyds has no entry.

## The fix

Build arrays of equal length (one per month in the full range), then:
- **Before first data**: fill with 0 (account didn't exist)
- **Within active range, no data this month**: forward-fill last known value
- **After last data, account is dead**: fill with 0
- **After last data, account is still active** (last row within 90 days
  of chart end): forward-fill to chart end

```python
from datetime import date

all_months = sorted({d for rows in raw_data.values() for d in rows})
chart_end = all_months[-1]

padded = {}
for acct, month_map in raw_data.items():
    values = []
    last_val = 0.0
    has_started = False
    last_data_month = max(month_map.keys())
    
    # Is this account still active? (last data within 90 days of chart end)
    active = (date.fromisoformat(chart_end) -
              date.fromisoformat(last_data_month)).days <= 90

    for month in all_months:
        if month in month_map:
            values.append(month_map[month])
            last_val = month_map[month]
            has_started = True
        elif has_started and (month <= last_data_month or active):
            values.append(last_val)  # forward-fill
        else:
            values.append(0.0)       # before birth or after death
    padded[acct] = values
```

## Pitfalls

- **Dead accounts forward-filled forever**: without the `active` check,
  Lloyds' £87.66 from 2020 persists through 2026, overstating net worth
- **New accounts not backfilled**: accounts born mid-series need zeros
  for months before they existed, or they'll have shorter arrays
- **String date comparison**: `"2026-06-01" > "2026-05-01"` works
  fine for ISO dates, but prefer `date.fromisoformat()` for arithmetic
