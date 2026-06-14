---
name: financial-etl
description: Handling bank CSV/OFX export to database pipelines — parsing, normalization, balance computation, and debugging impossible values.
---

# Financial ETL Pipeline Debugging

Handling bank CSV/OFX export → database pipelines: parsing, normalization, balance computation, and debugging impossible values.

## When to use

- Bank exports change format (columns reorder, sign conventions flip)
- Running balances show mathematically impossible values (negative for savings, huge magnitudes)
- OFX `<LEDGERBAL>` anchor doesn't match computed backward-wind balance
- Deduplication fails across multiple export files
- CSV detection/routing sends files to wrong account

## Core patterns

### 1. Backward-wind balance computation — safety guardrails

OFX `<LEDGERBAL>` provides an end-date balance. To get balances for earlier transactions, wind backward from anchor using transaction amounts: `bal(i) = bal(i+1) - amount(i)`.

**This is ONLY valid when transaction data is contiguous.** If there are days with no transaction records, the algorithm assumes zero activity — but interest, fees, and payments silently accumulate. This produces garbage (e.g., -£114k from sparse historical exports).

**Guardrail check (`_has_large_gaps`)** — skip balance computation if:
1. **Gap to anchor**: Latest transaction date is > `max_gap_days` (default 10) before OFX anchor date
2. **Inter-txn gaps**: Any two consecutive transactions separated by > 30 days

**Why not coverage percentage?** The old 80% coverage check was overbroad — it blocked Barclays (1600 txns, 30.6% coverage, but max inter-txn gap = only 24 days) while being too permissive for HSBC where the real issue is one txn every 111 days with no recorded activity between. For a current account, months of zero transactions mean the balance didn't change; silent activity (fees, interest) only matters when gaps are large (>30 days). The inter-txn gap check is both simpler and more accurate — use it as the primary reliability signal and drop blanket coverage thresholds entirely.

### 2. Bank CSV sign conventions vary wildly

| Bank | Raw Sign Convention | Correction |
|------|-------------------|------------|
| AMEX Gold (old) | Negated for debit: `-£50` = spending | Negate if negative and no "Debit" type marker |
| AMEX Gold (new) | Explicit "Credit"/"Debit" in type column | Use type field directly |
| AMEX BA (old) | Explicit "Credit"/"Debit" in type column | Use type field directly |
| AMEX BA (new) | Negative = spending, explicit sign | Use sign directly |
| Barclays OFX/CSV | Negative = debit spending | Use sign directly |
| HSBC | Usually negative for spending | Check export sample first |
| Lloyds (legacy) | Same as above | Check export sample |

**Rule**: Never assume all amounts follow the same convention. Always inspect raw exports and document the normalization per bank in code comments.

### 3. Preserve pre-computed bank balances

Banks like Lloyds export CSVs with a `Balance` column — this is a **bank-computed running balance**, NOT a value you should discard. Common bugs:
- `r.pop('Balance')` strips it early
- Missing OFX anchor → code forces `balance = '0'` when it should keep bank value
- Case mismatch: `Balance` vs `balance`

**Rule**: If a CSV has a pre-computed balance column, preserve it. Only compute from scratch if the bank doesn't provide one OR you have an OFX anchor to validate against. When no OFX anchor exists, fall back to bank-provided values, not zero.

### 4. CSV detection — use keyword matching, not length checks

Never route by `len(header) == N`. Columns get added/removed over time, breaking brittle length checks. Instead:
- Match on required keywords (`date`, `amount`, `account`)
- Use positive matches only (presence of key columns)
- For edge cases (3-col vs 4-col CSVs), prefer `len(lheader) >= N` AND keyword confirmation

Example pitfall: HSBC Credit Card cleaned CSV had 3 cols (Date, Description, Amount) which matched the generic HSBC pattern. The fix was to require `'description' in lheader` for the credit card variant.

### 5. OFX date parsing quirk

OFX `<DTASOF>` dates have timezone suffixes like `20260115000000[-5:GMT]`. Strip with regex:
```python
re.match(r'(\d{4})(\d{2})(\d{2})', raw_dt).groups()  # → ('2026','01','15')
```

### 6. Database schema — balance column everywhere

Every account table should have a `balance TEXT` column even when the value is '0'. This ensures:
- Queries like `SELECT MIN(balance), MAX(balance)` don't crash with "no such column"
- The combined view (`v_combined`) references consistent columns
- Schema migrations don't need per-table ALTER statements

## Common pitfalls

- **Backward-wind on sparse data**: Produces large negative values that look correct (single number matches anchor) but individual rows are garbage
- **Dedup with wrong key**: Using `(date, amount)` misses entries with same date/amount but different descriptions. Add `description_lower` to the dedup key
- **UTF-8 BOM in CSVs**: Banks sometimes export with BOM, causing header detection to fail. Use `encoding='utf-8-sig'` when reading
- **Multiple parsers per account**: AMEX Gold has both old and new format parsers — register both in PARSERS map and use TABLE_NAMES for DB routing
- **archive/ staging confusion**: `/archive/` is post-import (from inbox), NOT the same as `data/raw/` historical archive
- **Mortgage amortization off-by-one**: end_date check must happen BEFORE yield, not after. See "Mortgage amortization — off-by-one pitfall" section for the exact pattern.

## Account type classification for analysis

The personal-finance-data project has two fundamentally different account types:

| Type | Accounts | Behavior |
|------|----------|----------|
| **Current** | Barclays, HSBC, Lloyds | Salary in, bills out, transfers to credit cards. These drive the real monthly swings. Lloyds is legacy (closed 2020) but is still a current account — include it in current-account analyses for historical coverage back to 2013. |
| **Credit** | AMEX BA, AMEX Gold, HSBC Credit Card | Spending only (mostly). Settled monthly from current accounts. |

**Never combine current and credit accounts in the same analysis without accounting for the double-count**: when you pay an AMEX bill from Barclays, it shows as an expense on Barclays AND a credit (refund) on the AMEX. Summing both inflates both income and expense without changing the net. For cashflow analysis, use current accounts only. For spending breakdowns, use credit accounts only.

### Monthly balance query (income/expense/net per account)

```sql
SELECT account, strftime('%Y-%m', date) AS month,
       ROUND(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 2) AS income,
       ROUND(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 2) AS expense,
       ROUND(SUM(amount), 2) AS net
FROM v_combined
WHERE account IN ('Barclays', 'HSBC', 'Lloyds')   -- current only for cashflow
GROUP BY account, month ORDER BY account, month
```

## Liability accounts — mortgages as balance-sheet accounts

Mortgages are fundamentally different from transaction accounts (current/credit). They are **balance-sheet accounts**, not cash-flow accounts.

### Key concepts

| Term | Meaning |
|---|---|
| **Principal** | What you borrowed. Decreases each month as you pay it down. |
| **Interest** | The bank's charge for lending you money. Dead cost — not equity. |
| **Monthly payment** | Fixed DD from your current account. Split into interest + principal. |
| **Balance** | Outstanding amount you still owe. Starts at loan amount, declines to zero. |
| **Equity** | Property value − mortgage balance. Grows as balance shrinks. |

The monthly payment is already visible in current account data (the DD leaving Barclays/HSBC). Do NOT store the payment in the mortgage table — that would double-count cash flow. The mortgage is a **balance-only table**: `(date, balance)`.

### Design pattern

1. Extract 5 parameters from the mortgage offer (one-time, from config file):
   - `loan_amount`, `annual_rate`, `monthly_payment`, `start_date`, `fixed_to`
2. Store in `mortgage_config.py` — a standalone config, not hardcoded in the parser
3. Pre-compute the amortization schedule: `new_balance = old_balance × (1 + rate/12) − monthly_payment`
4. Insert into `mortgage` table with `date` and `balance` columns
5. Net worth calculation subtracts the balance: `net_worth = assets − mortgage.balance`
6. The balance is stored as a positive number (outstanding debt), not negative — the minus sign belongs in the net worth formula, not the data

### Why not store interest/principal per month?

- The monthly DD is already in current account data — storing it again in the mortgage table double-counts
- Interest and principal are implicit in the balance decline — recoverable via the amortization formula anytime
- No tax or reporting need for a residential mortgage
- If ever needed, recompute from the balance schedule

### Pitfall: double-counting DD + interest in analysis

When discussing mortgage cash flow, NEVER add the current-account DD to the mortgage interest charge to produce a "combined net." Example of wrong thinking:

> Barclays: −£2,788 (DD) + Mortgage: −£1,584 (interest) = −£4,372 total

This is nonsense — **the DD already contains the interest**. The £2,788 payment IS £1,584 interest + £1,204 principal. Adding them double-counts the interest. The correct mental model: the DD is the only cash movement; the mortgage balance change is a separate balance-sheet concern. Always keep cash-flow and balance-sheet analysis separate.

### Property as a balance-sheet asset

A mortgage is the liability side — the house itself is the largest asset for most people.
Without it, net worth shows deeply negative (£435k mortgage = -£355k at this project's June 2026 snapshot).
With a £820k valuation, net worth flips to +£465k.

**Data source:** Mortgage offer PDFs contain the lender's valuation. Extract with `pdftotext`:
```bash
pdftotext "Mortgage Offer.pdf" - | grep -i "value of the property"
# → Value of the property to prepare this Offer: £820,000.00
```

**Maintenance:** One valuation point every ~5 years (remortgage time). Between valuations,
use a simple growth assumption — UK average ~3%/yr has tracked within 2% of actual for this
project (2019→2024: projected £838k, actual £820k).

```python
# property_config.py
PROPERTY = {
    "address": "33 Romany Rise, Orpington, BR5 1HG",
    "valuation_date": "2024-09-17",
    "valuation": 820000,
    "annual_growth": 0.03,
}
```

Add to `balance_sheet` table as an asset row per month: `value = valuation × (1 + growth)^years`.
Single data point is fine — monthly precision for an illiquid asset you're not selling is noise.

### Parameter extraction from mortgage offer PDFs

For one-off parameter extraction (loan amount, rate, term, payment) from formal mortgage offer PDFs, use system `pdftotext`:

```bash
pdftotext -layout "Mortgage Offer.pdf" - | head -150
```

The `-layout` flag preserves column alignment. Mortgage offers (ESIS/illustration documents) have predictable section headers: "Amount and currency of the loan", "Duration", "fixed rate", "Number of payments", "Amount of each instalment". Regex or manual reading extracts 5 parameters — no need for pdfplumber or PyMuPDF.

This is sufficient for mortgage config bootstrapping. The PDF is the source of truth; the extracted numbers feed `mortgage_config.py`. Do NOT build a full PDF parser for 5 numbers that change every 5 years.

### Config format

```python
# mortgage_config.py
MORTGAGES = [
    {
        "name": "Barclays Mortgage",
        "account_number": "97-392-84446",
        "property": "33 Romany Rise, Orpington, BR5 1HG",
        "loan_amount": 461054.79,
        "annual_rate": 0.0407,
        "monthly_payment": 2788.46,
        "start_date": "2024-11-01",
        "fixed_to": "2029-12-31",
    },
]
```

### Account type summary (updated)

| Type | Accounts | Role in analysis | Stored in |
|------|----------|-----------------|-----------|
| **Current** | Barclays, HSBC, Lloyds | Cash flow (income/expense per month) | per-account tables + `v_combined` |
| **Credit** | AMEX BA, AMEX Gold, HSBC Credit Card | Spending breakdown | per-account tables + `v_combined` |
| **Liability** | Mortgage (Barclays, NatWest) | Net worth only — balance-sheet, not cash flow | `mortgage` table |
| **Investment** | Vanguard ISA, Vanguard Pension | Portfolio value + net worth | `vanguard_*_cash` + `vanguard_*_investment` |
| **Net worth** | All assets + liabilities | Monthly snapshot for time-series | `balance_sheet` table (materialized) |

## Debugging impossible balances

When you see a balance that makes no sense:
1. Check if OFX anchor exists (`<LEDGERBAL>` in export)
2. Compare latest transaction date vs anchor date — is there a gap?
3. Count transactions across the time span — is data sparse?
4. If both conditions true → backward-wind assumption violated → result is garbage

## Investment/brokerage account import (XLSX)

Vanguard and other brokerages export `.xlsx` statements, not CSV/OFX. These have
a fundamentally different structure: mixed cash and investment transactions in
the same sheet, separated by section headers.

### Parsing approach

Use stdlib `zipfile` + `xml.etree` when pip/sudo unavailable. See
`references/xlsx-stdlib-parsing.md` for the full technique.

### Dual-table schema: cash + investment

Each brokerage account gets TWO tables, not one:

| Table | Contents | Dedup key |
|---|---|---|
| `<account>_cash` | Deposits, withdrawals, fund buys/sells, fees, interest — with running balance | `(date, amount, description_lower)` |
| `<account>_investment` | Per-fund buy/sell records: fund_name, quantity, price, cost — NO balance column | `(date, cost, description_lower)` |

**Why split?** Cash transactions have banking-style running balances and need
bank-style dedup. Investment transactions track unit holdings and cost basis
— different query patterns, different dedup semantics.

### Transaction type classification

Use text matching on the "Details" field, ordered from most specific to least:

```python
if 'selling of account investments' in d:    return ('Sell for Fees', 'sell')
if 'regular deposit' in d:                   return ('Regular Deposit', 'transfer_in')
if 'deposit' in d:                           return ('Deposit', 'transfer_in')
if 'withdrawal' in d or 'payment by faster': return ('Withdrawal', 'transfer_out')
if 'bought' in d:                            return (details_text, 'buy')
if 'sold' in d:                              return (details_text, 'sell')
if 'account fee' in d:                       return ('Account Fee', 'fee')
if 'cash interest' in d:                     return ('Interest', 'interest')
if 'pension transfer' in d:                  return ('Pension Transfer In', 'transfer_in')
```

**Critical ordering**: "Selling of account investments for payment of Account Fee"
must match `sell` (not `fee`). Check "selling of account investments" first,
"account fee" later.

### Caveat: cash balance ≠ total value

Brokerage cash balance is only the uninvested cash portion. Total account value
= cash balance + current market value of all fund holdings. The cash table alone
understates value. For the Vanguard ISA example: £37,022 cash + £34,432 investments
= £71,455 total. The investment table provides cost basis; market value requires
external price data.

## Balance sheet — two-tier approach

For net worth tracking, use BOTH a live view (current snapshot) AND a materialized
table (monthly history). The view is for quick checks; the table is the source of
truth for time-series analysis.

### 1. Materialized `balance_sheet` table (monthly history)

Build with a Python script (`build_balance_sheet.py`) that walks every month
from earliest data to today and computes each account's value:

```sql
CREATE TABLE balance_sheet (
    date TEXT NOT NULL,      -- YYYY-MM-01 (month start)
    account TEXT NOT NULL,
    amount REAL NOT NULL,    -- positive = asset, negative = liability
    kind TEXT NOT NULL,      -- 'asset' or 'liability'
    PRIMARY KEY (date, account)
);
```

**Sources per account:**

| Account | Computation |
|---|---|
| Current accounts | `balance` column at month-end (no forward-fill past last data) |
| Investment cash | `balance` column at month-end (first-data filtered) |
| Investment holdings | Cumulative net units × last trade price ≤ month |
| Mortgage | Direct from `mortgage` table row |

**Key patterns:**
- Skip months before the account's first data row (don't show £0 for 2017 when ISA opened in 2019)
- Stop forward-fill at the account's last data month (closed accounts drop off)
- Skip credit cards entirely — paid in full monthly, already reflected in current account outflows. Including them double-counts.
- Active mortgage detection: no rows ≥ 60 days → paid off → exclude (NatWest drops off after 2024-10)
- Investment value: simple `SUM(quantity) × last_trade_price`. No external price feed needed — Vanguard statements provide per-transaction prices. The computation uses trade-date price, not current market, which is the best available without a live feed.

**Net worth over time query:**
```sql
SELECT date,
  ROUND(SUM(CASE WHEN kind='asset' THEN amount ELSE 0 END)) AS assets,
  ROUND(SUM(CASE WHEN kind='liability' THEN ABS(amount) ELSE 0 END)) AS liabilities,
  ROUND(SUM(amount)) AS net_worth
FROM balance_sheet
WHERE date LIKE '%-01-01' OR date LIKE '%-06-01'
ORDER BY date;
```

### 2. `v_balance_sheet` view (current snapshot only)

For quick "what's my net worth now" checks without building the full table:

```sql
CREATE VIEW v_balance_sheet AS
-- Active mortgage liabilities (exclude paid-off: no rows in last 60 days)
SELECT name AS account, date, -balance AS amount, 'liability' AS kind
FROM mortgage m1
WHERE date = (
    SELECT MAX(date) FROM mortgage m2
    WHERE m2.name = m1.name AND date <= date('now')
)
AND date >= date('now', '-60 days')
UNION ALL
-- Vanguard ISA cash balance
SELECT 'Vanguard ISA' AS account, date, CAST(balance AS REAL), 'asset'
FROM vanguard_isa_cash
WHERE date = (SELECT MAX(date) FROM vanguard_isa_cash)
UNION ALL
-- Vanguard ISA investment holdings
SELECT 'Vanguard ISA Investment' AS account,
    as_of_date AS date, estimated_value AS amount, 'asset' AS kind
FROM investment_holdings WHERE account = 'Vanguard ISA'
UNION ALL
-- Vanguard Pension cash + investment (same pattern)
...
```

The 60-day filter excludes paid-off mortgages (no recent activity) but keeps
active ones. This avoids showing old remortgaged loans as still outstanding.

### Forward-fill rules for sparse data

When accounts have different date ranges (opened/closed at different times), all
arrays must be the same length for charting. Rules per account:

**Active accounts** (last data within 3 months of chart end): forward-fill from
last known value to chart end.
**Dead accounts** (closed/paid off, last data > 3 months ago): stop at last data
month, drop to £0 after.
**Not-yet-opened**: show £0 before first data month.

```python
chart_end = all_months[-1]
last_data_month = max(raw_data[account].keys())
active = (date.fromisoformat(chart_end) - date.fromisoformat(last_data_month)).days <= 93

for month in all_months:
    if month in raw_data[account]:
        values.append(raw_data[account][month]); last_val = raw_data[account][month]; has_started = True
    elif has_started and (month <= last_data_month or active):
        values.append(last_val)  # forward-fill
    else:
        values.append(0.0)       # before start or after death
```

### Config-driven interpolation for static assets

Assets with sparse valuation points use config files with interpolation.
Between known dates: linear. After last: extrapolate at implied growth rate.
Before first: return None. See the `personal-balance-sheet` skill for full architecture.

**Net worth query**: `SELECT SUM(CASE WHEN kind='asset' THEN amount ELSE 0 END) as assets, SUM(CASE WHEN kind='liability' THEN -amount ELSE 0 END) as liabilities, SUM(amount) as net_worth FROM v_balance_sheet;`
When generating amortization schedules with an end_date, the loop termination
check must happen **before** yielding the row, not after:

```python
# WRONG — yields one extra month
while balance > 0:
    balance = compute_new_balance(...)
    yield (date, balance)            # yields for current month
    if date >= end_date: break       # checks AFTER yield
    date = advance_month(date)       # → extra row slips through

# RIGHT — check before yield
while balance > 0:
    if date > end_date: break        # check BEFORE any work
    balance = compute_new_balance(...)
    yield (date, balance)            # now yields only valid months
    date = advance_month(date)
```

With the wrong pattern, a mortgage ending Oct 2024 produces 61 rows (through
Nov 2024) instead of the correct 60 rows. The extra month adds ~£1,400 to the
computed ending balance and breaks cross-validation with the remortgage loan
amount.
