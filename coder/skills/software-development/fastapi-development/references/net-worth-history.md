# Net Worth Over Time — Running Balance Computation

Computes net worth at each month boundary by calculating cumulative transaction balances per account and summing across all accounts. No snapshot data needed — derived entirely from transaction history.

## Endpoint

```
GET /api/dashboard/net-worth-history
```

Returns:
```json
{
  "labels": ["2013-04", "2013-05", ..., "2026-07"],
  "values": [-335.9, ... , 54538.94],
  "accounts": {
    "<account_id>": {
      "name": "Amex Gold",
      "values": [...]
    }
  }
}
```

## Algorithm

```python
def compute_net_worth_history(accounts, all_transactions):
    # 1. Sort transactions by date
    all_txns.sort(key=lambda t: t.date if t.date else date.min)

    # 2. Build month labels from first txn date to today
    labels = []
    current = all_txns[0].date.replace(day=1)
    cutoff = date.today().replace(day=1) + timedelta(days=32)
    while current < cutoff:
        labels.append(current.strftime("%Y-%m"))
        # advance to next month
        ...

    # 3. For each month, compute running balance per account
    totals = []
    per_account = {aid: [] for aid in account_ids}

    for month_label in labels:
        # Month boundary = last day of the month
        boundary = last_day_of_month(month_label)
        month_total = 0.0

        for aid in account_ids:
            # Sum ALL transactions for this account up to boundary
            bal = sum(t.amount for t in all_txns
                      if t.account_id == aid and t.date <= boundary)
            per_account[aid].append(bal)
            month_total += bal

        totals.append(round(month_total, 2))

    return {"labels": labels, "values": totals, "accounts": per_account}
```

## Performance

For 15,862 transactions across 8 accounts over 160 months, this endpoint completes in <1 second on SQLite. The algorithm is O(txns × months) which is ~2.5M iterations — fine for this scale but would need optimisation at >100K transactions.

## Limitations

- **Assumes accounts start at £0.** The first computed net worth is the cumulative balance of all transactions up to the first month. If an account had a pre-existing balance before the earliest transaction, it won't be reflected.
- **No liability tracking.** Credit card balances show as positive when they should be negative (the transaction data shows debits/credits from the card's perspective, not from the user's perspective). For a true net worth, credit card accounts should be treated as liability accounts (invert the sign).
- **No net worth snapshots.** This computes from transactions only. If you want to track net worth independently of transaction data (e.g. manually set a baseline), you'd need a separate `net_worth_snapshots` table.

## Related

- `docs/bugs-2026-06-04-csv-import-parsers.md` — the import pipeline that feeds the transaction data
- The pfin `dashboard.html` template loads this via `fetch('/api/dashboard/net-worth-history')` and renders a Chart.js line chart
