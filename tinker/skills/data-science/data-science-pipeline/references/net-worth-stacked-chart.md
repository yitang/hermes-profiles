# Net Worth Stacked Area + Line Chart

Full working example of a net worth chart with:
- Stacked area for assets (above zero) and liabilities (below zero)
- Bold net worth line overlay
- Forward-fill padding for accounts with different date ranges
- Active/dead account detection (stop forward-filling closed accounts)

## Query pattern

```sql
SELECT date, account, amount, kind
FROM balance_sheet
ORDER BY date, account
```

`kind` = 'asset' or 'liability'. Net worth = sum of all amounts per month.

## Forward-fill padding

Accounts appear/disappear at different times (Lloyds closed 2020, Vanguard started 2019, mortgage started 2024). Pad all arrays to the same length:

```python
raw_data = defaultdict(dict)  # account -> {month: amount}
for date, account, amount, kind in rows:
    raw_data[account][date] = amount

for acct, month_map in raw_data.items():
    values = []
    last_val = 0.0
    has_started = False
    last_data_month = max(month_map.keys())

    # Dead account detection: last data > 3 months before chart end
    active = (chart_end_date - last_data_month).days <= 93

    for month in all_months:
        if month in month_map:
            values.append(month_map[month])
            last_val = month_map[month]
            has_started = True
        elif has_started and (month <= last_data_month or active):
            values.append(last_val)  # forward-fill
        else:
            values.append(0.0)  # not yet born or died
    account_data[acct] = values
```

## Stacked traces config

```python
# Asset accounts → stackgroup='assets'
for acct in asset_accounts:
    traces.append({
        'type': 'scatter', 'stackgroup': 'assets',
        'mode': 'lines', 'fill': 'tonexty',
        ...
    })

# Liability accounts → stackgroup='liabilities'
for acct in liability_accounts:
    traces.append({
        'type': 'scatter', 'stackgroup': 'liabilities',
        'mode': 'lines', 'fill': 'tonexty',
        ...
    })

# Net worth line on top
traces.append({
    'type': 'scatter',
    'name': 'Net Worth',
    'line': {'color': '#000', 'width': 3},
    ...
})
```

## Full script

See `viz_net_worth.py` in personal-finance-data for the complete implementation.

## Pitfalls

- **Mutable dict during iteration**: Don't build `account_data` in a single pass — accounts appear mid-loop. Use two-pass: collect raw first, then pad.
- **Dead accounts forward-filling**: Lloyds closed with £87.66 — if you forward-fill unconditionally, it shows £87.66 in 2026. Detect dead accounts by checking gap between last data month and chart end.
- **String x-axis with Plotly**: Month strings like "2020-03-01" get auto-parsed as years. Always set `xaxis.type = 'category'`.
