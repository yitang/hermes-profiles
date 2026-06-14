---
name: personal-balance-sheet
description: Build and maintain a monthly personal net worth balance sheet from bank accounts, investments, pensions, mortgages, and property — config-driven, SQLite-backed, zero external deps.
---

# Personal Balance Sheet

Build a complete personal net worth tracking system from financial statements. One SQLite table (`balance_sheet`) with one row per account per month. Assets and liabilities tracked separately, monthly interpolation between known data points.

## When to use

- Building a personal net worth tracker from bank/investment/mortgage statements
- Adding a new asset or liability category to an existing balance sheet
- Extracting financial data from PDF statements, XLSX exports, or OFX/CSV files
- Generating net worth charts over time

## Architecture

### Cash-flow vs balance-sheet accounts

This is the fundamental distinction. Do NOT mix them:

- **Cash-flow accounts** (current accounts, credit cards): per-transaction data with `(date, amount, description, balance)`. Used for spending analysis. Imported via CSV/OFX parsers.
- **Balance-sheet accounts** (mortgages, pensions, investments, property): periodic balance snapshots. One row per month. Exist purely for net worth. Must NOT re-record payments already captured in cash-flow data — that would double-count.

Credit cards are cash-flow only — never include in balance sheet. They're paid in full monthly, so their spending is already reflected in current account outflows.

### Config files as single source of truth

Each static asset/liability gets a Python config file:

```python
# property_config.py — two known valuations, monthly interpolation
PROPERTY = {
    "valuations": [
        {"date": "2019-11-01", "value": 670000},
        {"date": "2024-09-17", "value": 820000},
    ],
}

# mortgage_config.py — amortization parameters
MORTGAGES = [
    {"name": "Barclays", "loan_amount": 461054.79, "annual_rate": 0.0407,
     "monthly_payment": 2788.46, "start": "2024-11-01"},
]
```

Keep property and mortgage configs SEPARATE — one is an asset, one is a liability. They are tightly related (valuation dates ARE mortgage offer dates) but the separation preserves the asset/liability boundary.

### Monthly interpolation

When you have sparse data points (annual pension statements, property valuations), interpolate linearly between known dates:

```python
def interpolate_value_at(month, snapshots):
    """Given [{"date": "YYYY-MM-DD", "value": float}, ...], return value at month."""
    v_sorted = sorted(snapshots, key=lambda v: v["date"])
    month_d = date.fromisoformat(month)

    # Before first snapshot: no data (return None)
    if month_d < date.fromisoformat(v_sorted[0]["date"]):
        return None

    # Between two snapshots: linear interpolation
    for i in range(len(v_sorted) - 1):
        v1, v2 = v_sorted[i], v_sorted[i + 1]
        d1, d2 = date.fromisoformat(v1["date"]), date.fromisoformat(v2["date"])
        if d1 <= month_d <= d2:
            fraction = (month_d - d1).days / max((d2 - d1).days, 1)
            return round(v1["value"] + (v2["value"] - v1["value"]) * fraction, 2)

    # After last snapshot: extrapolate at implied growth rate
    if len(v_sorted) >= 2:
        d1, d2 = date.fromisoformat(v_sorted[-2]["date"]), date.fromisoformat(v_sorted[-1]["date"])
        growth = (v_sorted[-1]["value"] / v_sorted[-2]["value"]) ** (365.25 / (d2-d1).days) - 1
    else:
        growth = 0.03
    years = (month_d - date.fromisoformat(v_sorted[-1]["date"])).days / 365.25
    return round(v_sorted[-1]["value"] * (1 + growth) ** years, 2)
```

### build_balance_sheet.py pattern

One script that queries all source tables, computes monthly values for every account, and writes `balance_sheet(date, account, amount, kind)`. Use `INSERT OR REPLACE` for idempotent re-runs.

Schema:
```sql
CREATE TABLE balance_sheet (
    date TEXT NOT NULL,
    account TEXT NOT NULL,
    amount REAL NOT NULL,   -- positive=asset, negative=liability
    kind TEXT NOT NULL,     -- 'asset' or 'liability'
    PRIMARY KEY (date, account)
);
```

Month range: from earliest data across all accounts to current month. Cap at today — do not include future mortgage projections.

Forward-fill rules:
- Active accounts (last data within 3 months of today): forward-fill to chart end
- Dead accounts (closed, paid off): stop at last data month, drop to 0 after

## Extracting data from financial documents

### PDF statements (e.g., pension benefit statements)

Use `pdftotext` (from poppler-utils, available on most Linux systems) — no Python deps:

```bash
pdftotext statement.pdf - 2>/dev/null
```

Extract values with regex. Find patterns unique to the document format:
- Old format: `Your pension pot value.*?£(\d+).*?£(\d+).*?£(\d+)`
- New format: `How much money you already have in your plan\n£(\d+)`
- Statement period: `This year \(([^)]+)\)` or `STATEMENT PERIOD:\s*(.+?)(?:\n|$)`

Always cross-validate the extracted values against the raw text before trusting.

### XLSX investment statements (e.g., Vanguard)

When `openpyxl` is unavailable (no pip), parse as ZIP + XML:
- `xl/sharedStrings.xml` → shared string table
- `xl/worksheets/sheetN.xml` → cell data
- Excel date serial numbers: `datetime(1899, 12, 30) + timedelta(days=n)`
- Detect sections by first-column text (e.g., "Cash Transactions", "Investment Transactions")
- Filter out summary/total rows (e.g., "Cost  29769.68")

### CSV bank exports

Import via CSV parsers with column-name-based detection. Dedup on `(date, amount, description_lower)`. Unknown columns go into an `extra` JSON column.

## Net worth visualization

Generate zero-dependency Plotly charts: query SQLite → build Python dicts → serialize as JSON → embed in HTML with Plotly CDN `<script>` tag. Always set `"type": "category"` on x-axes when using date strings — Plotly auto-parses "2022-01" as year 2022 otherwise.

Account coloring convention:
- Assets: greens, blues, teals, oranges
- Liabilities: reds
- Net worth line: black, bold
- Use stacked areas for asset/liability groups

## Common pitfalls

- **Credit cards in balance sheet**: They're paid in full monthly from current accounts. Including them double-counts. Exclude them.
- **Property without house value**: The mortgage is a liability but the house is the offsetting asset. Without it, net worth looks catastrophic.
- **Dead accounts forward-filled forever**: Lloyds closed in 2020 but its £87 balance would persist forever if forward-filled naively. Stop at last data month for inactive accounts.
- **Overdrawn current accounts**: Negative current account balances are real and should be tracked as-is. Don't force them positive.
- **Valuation ≠ purchase price**: Bank valuations can match, exceed, or undershoot purchase price. Use the bank's number from the mortgage offer — it's the one they lend against.
- **Investment values vs cash balances**: Investment accounts (pensions, ISAs) have near-zero cash balances because money is invested in funds. Track the investment holdings separately (units × price), not just cash.

## Related skills

- `financial-etl` — bank CSV/OFX parsing and normalization
- `sqlite-visualization` — Plotly HTML charts from SQLite
- `ocr-and-documents` — PDF text extraction (pdftotext, pymupdf, marker-pdf)
