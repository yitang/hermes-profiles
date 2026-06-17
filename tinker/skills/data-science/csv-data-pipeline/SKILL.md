---
name: csv-data-pipeline
description: "Robust ETL for messy multi-format CSV/OFX data ingestion — routing, dedup, schema evolution, audit trails. Financial domain extensions: bank/brokerage parsing, backward-wind balance computation, mortgage amortization, personal net worth tracking. Covers full pipeline from raw exports to SQLite-backed balance sheets."
version: 2.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ETL, CSV, OFX, data-ingestion, financial-pipeline, balance-sheet, net-worth, routing, deduplication, schema-evolution, audit]
---

# CSV Data Pipeline — Robust ETL & Financial Data Patterns

Covers the full pipeline: raw CSV/OFX/brokerage statements → cleaning/routing → SQLite database → balance sheets and net worth tracking.

## When to Use

- Ingesting data from multiple external sources (bank exports, APIs, scrapers)
- Source CSV/OFX/XML formats change without warning
- Multiple accounts produce similar-looking data with identical headers
- Need to merge same-account data across different source formats
- Database schema must grow without breaking existing imports
- Building personal net worth tracking from bank/investment/mortgage statements
- Extracting financial data from PDF statements, XLSX exports, or OFX/CSV files

---

## Section 1: General ETL Patterns

### Core Architecture Pattern

```
data/raw/     ← all raw exports (single source of truth, git-tracked)
    ├── account_a_format1.csv
    ├── account_a_format2.csv  ← format drift!
    └── account_b.ofx          ← different format entirely

clean.py      → data/cleaned/   ← canonical CSVs per account
inbox/        ← staging area for import.py (one-time drops)
import.py     → finance.db      → /archive/ (timestamped imports)
```

**Key rule:** Raw data never mutates. Only append new files to `data/raw/`. Cleaning is always idempotent — run on the full directory, get reproducible outputs.

### Phase 1: Detection & Routing

#### Header Collision Problem ⚠️ CRITICAL

When two different accounts produce CSVs with identical headers (e.g., `Date,Description,Amount,balance`), header-only detection **cannot** distinguish them. This causes silent data misrouting into the wrong database table.

**Fix: Filename-based detection with header fallback.** Check filename patterns first, then fall back to column matching only for unrecognized files:

```python
def detect_account(filepath):
    fname = os.path.basename(filepath).lower()
    
    # 1. Filename-based routing (PRIORITY — handles identical headers)
    if 'lloyds' in fname and 'cleaned' in fname:
        return 'lloyds_cleaned'
    if 'hsbc_credit' in fname and 'cleaned' in fname:
        return 'hsbc_credit_cleaned'
    
    # 2. Header-based fallback (only for unknown filenames)
    header = read_first_line(filepath)
    cols = [c.strip().lower() for c in header.split(',')]
    
    if len(cols) >= 6 and 'date' in cols and 'amount' in cols:
        return 'hsbc'  # or whatever 6-col format
    
    return None  # truly unrecognized — skip with warning
```

**Pattern recognition checklist:**
1. List every output CSV's header from all sources
2. **Flag collisions**: any two accounts sharing the same header columns? → filename priority required
3. Check for columns that only exist in one format (e.g., `Category` vs `Subcategory`) — these can help distinguish if filenames aren't reliable

#### Use keyword matching, not length checks

Never route by `len(header) == N`. Columns get added/removed over time. Instead:
- Match on required keywords (`date`, `amount`, `account`)
- Use positive matches only (presence of key columns)
- For edge cases, prefer `len(lheader) >= N` AND keyword confirmation

### Phase 2: Cleaning & Canonicalization

#### Multi-format source merging

Same account may produce data in different formats. Clean.py must detect each file's format by header/columns or extension (.ofx), parse each into the **same canonical row schema**, and deduplicate across ALL inputs.

#### Dedup strategy
- Key: `(date, normalized_amount, description.lower())`
- Normalization: strip whitespace, normalize sign convention, handle decimal separators
- Use `INSERT OR IGNORE` at DB level; track duplicates in audit trail

#### Sign fixing

External exports use negation inconsistently. Detect by column semantics (`Category=Payment` with negative amount = double-negative) and normalize. Never assume all amounts follow the same convention — inspect raw exports and document per bank.

| Bank | Raw Sign Convention | Correction |
|------|-------------------|------------|
| AMEX Gold (old) | Negated for debit: `-£50` = spending | Negate if negative and no "Debit" type marker |
| AMEX Gold (new) | Explicit "Credit"/"Debit" | Use type field directly |
| Barclays OFX/CSV | Negative = debit spending | Use sign directly |
| HSBC | Usually negative for spending | Check export sample first |

#### Balance computation from OFX anchors

When pipeline receives OFX files with `<LEDGERBAL>` tags:
1. Parse ledger balance + date from each OFX
2. Collect all anchors, take the latest
3. **Backward-wind**: starting from anchor value, go through rows in reverse computing `row_balance = next_row_balance - amount`
4. Forward-reverse to align with original row order

#### Safety guardrails for backward-wind ⚠️

**ONLY valid when transaction data is contiguous.** If days have no records, interest/fees/payments silently accumulate → garbage results (e.g., -£114k from sparse exports).

**Guardrail check:** Skip balance computation if:
1. **Gap to anchor**: Latest txn date > `max_gap_days` (default 10) before OFX anchor date
2. **Inter-txn gaps**: Any two consecutive txns separated by > 30 days

For a current account, months of zero transactions mean the balance didn't change; silent activity only matters with large gaps (>30 days). Use inter-txn gap check as primary reliability signal — don't use blanket coverage thresholds.

#### OFX date parsing quirk

OFX `<DTASOF>` dates have timezone suffixes like `20260115000000[-5:GMT]`. Strip with regex:
```python
re.match(r'(\d{4})(\d{2})(\d{2})', raw_dt).groups()  # → ('2026','01','15')
```

#### Preserve pre-computed bank balances

Banks like Lloyds export CSVs with a `Balance` column — **bank-computed running balance**, NOT something to discard. Common bugs:
- `r.pop('Balance')` strips it early
- Missing OFX anchor → code forces `balance = '0'` when it should keep bank value
- Case mismatch: `Balance` vs `balance`

**Rule:** If CSV has pre-computed balance column, preserve it. Only compute from scratch if no OFX anchor and no bank-provided values. When no OFX anchor exists, fall back to bank-provided values, not zero.

```python
def compute_balance(rows, ledger_bal):
    if not rows or not ledger_bal:
        # Preserve any pre-existing balance values; only default to 0 if missing
        for r in rows:
            if 'balance' not in r or not r['balance'].strip():
                r['balance'] = 0
        return
    
    balances = []
    current = float(ledger_bal['amount'])
    for r in reversed(rows):
        balances.append(current)
        current -= float(r['amount'])
    balances.reverse()
    
    for i, r in enumerate(rows):
        if i < len(balances):
            r['balance'] = round(balances[i], 2)
```

#### Audit trail (MANDATORY)

Every clean.py run MUST generate files in `data/cleaned/audit/`:

| File | Purpose | Key columns |
|------|---------|-------------|
| `manifest.md` | Summary: accounts, file counts, raw→clean reductions | account, source_files, raw_rows, clean_rows |
| `sign_fixes.csv` | Every amount sign corrected | date, original_amount, corrected_amount, source_file |
| `duplicates.csv` | Rows removed during dedup | date, amount, description, kept_in |
| `balance_anchors.csv` | OFX LEDGERBAL sources used | account, anchor_amount, anchor_date, source_ofx_file, row_count |

**File skip list:** Skip non-data files — `.py`, `.md`, `.txt`, editor backups (`#*~`, `.#*`). Detect by checking if first line contains CSV columns or OFX tags. Skip with warning.

### Phase 3: Import & Database Schema

#### Schema evolution checklist

Every time a new account/parser is added:
1. Add parser → register in `PARSERS` dict
2. Update `TABLE_NAMES` → map key to DB table
3. Extend `COLUMN_WHITELIST` per-table for SQL injection protection
4. Update `detect_account()` → filename + header patterns
5. Update `init_schema.py` → new CREATE TABLE, update views/registry list
6. Rebuild DB → `rm finance.db && touch finance.db && python3 init_schema.py && python3 import.py`

**Schema/code sync rule:** If `import.py` creates a table at runtime, it MUST also exist in `init_schema.py`. Any mismatch causes DB rebuild failures. Always check both files before adding any new table.

#### Import routing
1. Staged CSVs → `inbox/`
2. `import.py` detects account, parses, inserts → moves to `/archive/<timestamp>_<filename>.csv`
3. Archive preserves originals for replay/recovery
4. Dedup at DB level: `(date, amount, description_lower)` per-table

#### Database schema — balance column everywhere

Every account table should have a `balance TEXT` column even when value is '0'. Ensures queries like `SELECT MIN(balance), MAX(balance)` don't crash with "no such column". Combined view (`v_combined`) references consistent columns.

### Phase 4: Validation

#### Post-clean verification
1. Check `data/cleaned/audit/manifest.md` — raw→clean counts make sense?
2. Verify each cleaned CSV has matching `init_schema.py` table
3. If balance expected (OFX anchors), confirm non-zero in CSV
4. All balances zero → OFX anchor not found, investigate

#### Post-import verification
```bash
# Row counts per account
sqlite3 finance.db "SELECT account, COUNT(*) FROM v_combined GROUP BY account ORDER BY account;"

# Latest date per account
sqlite3 finance.db "SELECT account, MAX(date) FROM v_combined GROUP BY account ORDER BY account;"
```

---

## Section 2: Financial Domain Extensions

### Account type classification

| Type | Accounts | Behavior |
|------|----------|----------|
| **Current** | Barclays, HSBC, Lloyds | Salary in, bills out, transfers. Drive real monthly swings. |
| **Credit** | AMEX BA, AMEX Gold, HSBC CC | Spending only (mostly). Settled monthly from current accounts. |
| **Liability** | Mortgage (Barclays, NatWest) | Balance-sheet only — NOT cash flow |
| **Investment** | Vanguard ISA, Pension | Portfolio value + net worth |

**Never combine current and credit accounts in same analysis** without accounting for double-count: AMEX payment shows as expense on Barclays AND credit on AMEX. Summing inflates both income/expense. For cashflow analysis, use current accounts only. For spending breakdowns, use credit accounts only.

### Monthly balance query (income/expense/net)
```sql
SELECT account, strftime('%Y-%m', date) AS month,
       ROUND(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 2) AS income,
       ROUND(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 2) AS expense,
       ROUND(SUM(amount), 2) AS net
FROM v_combined
WHERE account IN ('Barclays', 'HSBC', 'Lloyds')   -- current only for cashflow
GROUP BY account, month ORDER BY account, month
```

### Mortgage — balance-sheet account (NOT cash-flow)

Mortgages are fundamentally different from transaction accounts. They are **balance-sheet accounts**: `(date, balance)`. The monthly DD is already in current account data — do NOT store it again in mortgage table (double-count).

#### Design pattern
1. Extract 5 parameters from mortgage offer (one-time): `loan_amount`, `annual_rate`, `monthly_payment`, `start_date`, `fixed_to`
2. Store in `mortgage_config.py` — standalone config, not hardcoded
3. Pre-compute amortization: `new_balance = old_balance × (1 + rate/12) − monthly_payment`
4. Insert into `mortgage` table with `date` and `balance` columns
5. Net worth: `assets − mortgage.balance`
6. Balance stored as **positive** number (outstanding debt) — minus sign in net worth formula

#### Why not store interest/principal per month?
- Monthly DD already in current account data → double-count if stored again
- Interest and principal implicit in balance decline — recoverable via amortization formula
- No tax/reporting need for residential mortgage

#### Pitfall: amortization off-by-one ⚠️

```python
# WRONG — yields one extra month
while balance > 0:
    balance = compute_new_balance(...)
    yield (date, balance)            # yields before checking end_date
    if date >= end_date: break       # → extra row slips through

# RIGHT — check BEFORE yield
while balance > 0:
    if date > end_date: break        # check BEFORE any work
    balance = compute_new_balance(...)
    yield (date, balance)            # now yields only valid months
    date = advance_month(date)
```

Wrong pattern: mortgage ending Oct 2024 produces 61 rows (through Nov 2024) instead of correct 60. Extra month adds ~£1,400 to ending balance and breaks cross-validation.

#### Double-counting DD + interest

NEVER add current-account DD to mortgage interest charge: Barclays £2,788 DD = £1,584 interest + £1,204 principal. Adding them double-counts the interest. Keep cash-flow and balance-sheet analysis separate.

#### Parameter extraction from mortgage offer PDFs
```bash
pdftotext -layout "Mortgage Offer.pdf" - | head -150
# Mortgage offers have predictable section headers:
# "Amount and currency of the loan", "Duration", "fixed rate", etc.
```

Sufficient for mortgage config bootstrapping. PDF is source of truth; extracted numbers feed `mortgage_config.py`.

#### Property as balance-sheet asset

Mortgage = liability side, house = largest asset for most people. Without property valuation, net worth shows deeply negative (e.g., £435k mortgage = -£355k). With £820k valuation, net worth flips to +£465k.

```python
# property_config.py
PROPERTY = {
    "address": "33 Romany Rise, Orpington, BR5 1HG",
    "valuation_date": "2024-09-17",
    "valuation": 820000,
    "annual_growth": 0.03,
}
```

Single data point per ~5 years (remortgage time) is fine. Monthly precision for illiquid asset is noise. Use UK average ~3%/yr between valuations.

### Investment/brokerage import (XLSX)

Brokerages export `.xlsx` statements — fundamentally different structure: mixed cash and investment transactions in same sheet.

#### Parsing approach

Use stdlib `zipfile` + `xml.etree` when pip/sudo unavailable:
- `xl/sharedStrings.xml` → shared string table
- `xl/worksheets/sheetN.xml` → cell data
- Excel date serial numbers: `datetime(1899, 12, 30) + timedelta(days=n)`
- Detect sections by first-column text (e.g., "Cash Transactions", "Investment Transactions")

#### Dual-table schema: cash + investment

| Table | Contents | Dedup key |
|---|---|---|
| `<account>_cash` | Deposits, withdrawals, fund buys/sells, fees, interest — running balance | `(date, amount, description_lower)` |
| `<account>_investment` | Per-fund buy/sell: fund_name, quantity, price, cost — NO balance | `(date, cost, description_lower)` |

#### Transaction type classification (ordered specific→generic)
```python
if 'selling of account investments' in d:    return ('Sell for Fees', 'sell')
if 'regular deposit' in d:                   return ('Regular Deposit', 'transfer_in')
if 'deposit' in d:                           return ('Deposit', 'transfer_in')
if 'withdrawal' in d or 'payment by faster': return ('Withdrawal', 'transfer_out')
if 'bought' in d:                            return (details_text, 'buy')
if 'sold' in d:                              return (details_text, 'sell')
if 'account fee' in d:                       return ('Account Fee', 'fee')
if 'cash interest' in d:                     return ('Interest', 'interest')
```

**Critical ordering:** "Selling of account investments for payment of Account Fee" must match `sell` (not `fee`). Check "selling of account investments" first.

#### Caveat: cash balance ≠ total value

Brokerage cash is only uninvested portion. Total = cash + market value of fund holdings. Investment table provides cost basis; market value requires external price data.

---

## Section 3: Personal Balance Sheet Construction

### Cash-flow vs balance-sheet distinction (FUNDAMENTAL)

- **Cash-flow accounts** (current, credit cards): per-transaction `(date, amount, description, balance)` — spending analysis
- **Balance-sheet accounts** (mortgages, pensions, investments, property): periodic snapshots. One row per month. Must NOT re-record payments already in cash-flow data.

**Credit cards are cash-flow only** — paid in full monthly from current accounts. Include them → double-count.

### Architecture

#### Config files as single source of truth

```python
# property_config.py — valuations with interpolation
PROPERTY = {
    "valuations": [
        {"date": "2019-11-01", "value": 670000},
        {"date": "2024-09-17", "value": 820000},
    ],
}

# mortgage_config.py — amortization parameters
MORTGAGES = [{
    "name": "Barclays", "loan_amount": 461054.79,
    "annual_rate": 0.0407, "monthly_payment": 2788.46,
    "start": "2024-11-01"}]
```

Keep property and mortgage configs **SEPARATE** — one is asset, one is liability. Separation preserves the asset/liability boundary even though valuation dates match mortgage offer dates.

#### Monthly interpolation

When you have sparse data points (annual statements, valuations), interpolate linearly:

```python
def interpolate_value_at(month, snapshots):
    """Return value at month given [{date, value}, ...]."""
    v_sorted = sorted(snapshots, key=lambda v: v["date"])
    month_d = date.fromisoformat(month)
    
    if month_d < date.fromisoformat(v_sorted[0]["date"]):
        return None  # Before first snapshot
    
    for i in range(len(v_sorted) - 1):
        d1, d2 = date.fromisoformat(v_sorted[i]["date"]), date.fromisoformat(v_sorted[i+1]["date"])
        if d1 <= month_d <= d2:
            fraction = (month_d - d1).days / max((d2 - d1).days, 1)
            return round(v_sorted[i]["value"] + (v_sorted[i+1]["value"] - v_sorted[i]["value"]) * fraction, 2)
    
    # Extrapolate at implied growth rate after last snapshot
    if len(v_sorted) >= 2:
        d1, d2 = date.fromisoformat(v_sorted[-2]["date"]), date.fromisoformat(v_sorted[-1]["date"])
        growth = (v_sorted[-1]["value"] / v_sorted[-2]["value"]) ** (365.25 / (d2-d1).days) - 1
    else:
        growth = 0.03  # default UK average
    
    years = (month_d - date.fromisoformat(v_sorted[-1]["date"])).days / 365.25
    return round(v_sorted[-1]["value"] * (1 + growth) ** years, 2)
```

#### build_balance_sheet.py pattern

One script querying all source tables, computing monthly values for every account, writing `balance_sheet(date, account, amount, kind)`. Use `INSERT OR REPLACE` for idempotent re-runs.

```sql
CREATE TABLE balance_sheet (
    date TEXT NOT NULL,      -- YYYY-MM-01
    account TEXT NOT NULL,
    amount REAL NOT NULL,    -- positive=asset, negative=liability
    kind TEXT NOT NULL,      -- 'asset' or 'liability'
    PRIMARY KEY (date, account)
);
```

Month range: earliest data to current month. Cap at today.

**Forward-fill rules:**
- **Active accounts** (last data within 3 months): forward-fill to chart end
- **Dead accounts** (closed/paid off): stop at last data, drop to £0 after
- **Not-yet-opened**: show £0 before first data month

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

#### Sources per account type

| Account | Computation |
|---|---|
| Current accounts | `balance` column at month-end |
| Investment cash | `balance` column at month-end |
| Investment holdings | Cumulative net units × last trade price ≤ month |
| Mortgage | Direct from `mortgage` table row |

**Key patterns:** Skip months before account's first data. Stop forward-fill at account's last data (closed accounts drop off). Skip credit cards entirely — double-counts with current account outflows. Active mortgage check: no rows ≥ 60 days → paid off → exclude. Investment value: `SUM(quantity) × last_trade_price` — no external price feed needed.

#### Net worth over time query
```sql
SELECT date,
  ROUND(SUM(CASE WHEN kind='asset' THEN amount ELSE 0 END)) AS assets,
  ROUND(SUM(CASE WHEN kind='liability' THEN ABS(amount) ELSE 0 END)) AS liabilities,
  ROUND(SUM(amount)) AS net_worth
FROM balance_sheet
WHERE date LIKE '%-01-01' OR date LIKE '%-06-01'
ORDER BY date;
```

#### `v_balance_sheet` view (current snapshot)

```sql
CREATE VIEW v_balance_sheet AS
SELECT name AS account, date, -balance AS amount, 'liability' AS kind  -- active mortgage
FROM mortgage m1
WHERE date = (SELECT MAX(date) FROM mortgage m2 WHERE m2.name = m1.name AND date <= date('now'))
AND date >= date('now', '-60 days')   -- exclude paid-off
UNION ALL
-- Vanguard ISA cash balance
SELECT 'Vanguard ISA' AS account, date, CAST(balance AS REAL), 'asset'
FROM vanguard_isa_cash
WHERE date = (SELECT MAX(date) FROM vanguard_isa_cash)
-- + ... other accounts following same pattern
```

The 60-day filter excludes paid-off mortgages but keeps active ones.

#### Config-driven interpolation for static assets

Between known dates: linear. After last: extrapolate at implied growth rate. Before first: return None.

**Net worth query:** `SELECT SUM(CASE WHEN kind='asset' THEN amount ELSE 0 END) as assets, SUM(CASE WHEN kind='liability' THEN -amount ELSE 0 END) as liabilities, SUM(amount) as net_worth FROM v_balance_sheet;`

### Extracting data from financial documents

#### PDF statements (e.g., pension benefits)

Use `pdftotext` — no Python deps:
```bash
pdftotext statement.pdf - 2>/dev/null
```

Extract values with regex. Always cross-validate extracted values against raw text.

#### CSV bank exports

Import via CSV parsers with column-name-based detection. Dedup on `(date, amount, description_lower)`. Unknown columns → `extra` JSON column.

### Net worth visualization

Zero-dependency Plotly charts: query SQLite → build Python dicts → serialize as JSON → embed in HTML with Plotly CDN `<script>` tag. Always set `"type": "category"` on x-axes when using date strings — Plotly auto-parses otherwise.

**Account coloring:** Assets = greens/blues/teals/oranges; Liabilities = reds; Net worth = black bold. Stacked areas for asset/liability groups.

### Common pitfalls (ALL sections)

1. **Header collision is silent** — data goes into wrong table without error. Compare headers of ALL outputs before building routing logic.
2. **Backward-wind on sparse data** → large negative values that look correct but rows are garbage
3. **UTF-8 BOM in CSVs** — phantom column name (`\ufeffDate`). Strip: `content = content.lstrip('\ufeff')` or use `encoding='utf-8-sig'`.
4. **init_schema.py vs import.py sync** — runtime script creates table that init_schema doesn't know → DB rebuild fails
5. **Dedup across format merge** — CSV + OFX for same date range → overlapping transactions → dedup must happen across ALL sources
6. **Pre-computed bank CSV fields overwritten** — when no OFX anchor, `compute_balance()` may zero out existing balance columns
7. **Schema evolution requires 5-file coordination** — adding a DB column means updating init_schema.py, COLUMN_WHITELIST, every parser, and verification queries
8. **Credit cards in balance sheet** — double-counts with current account outflows. Exclude them.
9. **Property without house value** — mortgage liability makes net worth look catastrophic without the asset offset.
10. **Dead accounts forward-filled forever** — closed accounts (Lloyds 2020) would persist £87 forever if forward-filled naively
11. **Overdrawn current accounts** — negative balances are real, track as-is
12. **Valuation ≠ purchase price** — use bank's mortgage offer number, not historical purchase price
13. **Investment values vs cash balances** — investment accounts have near-zero cash; track holdings (units × price), not just cash

---

## Skill Support Files

See `references/` for:
- `ofx-balance-computation.md` — OFX LEDGERBAL parsing and backward-winding detail
- `balance-zeroing-diagnosis.md` — 5-cause diagnostic path for zero balances in DB
- `schema-sync-checklist.md` — pre-import init_schema.py ↔ import.py consistency
- `header-collision-diagnosis.md` — step-by-step header collision detection recipe
- `barclays-balance-recovery.md` — Barclays-specific balance recovery techniques
- `barclays-balance-recovery.md` — Barclays-specific balance recovery techniques
- `xlsx-stdlib-parsing.md` — XLSX parsing with stdlib zipfile + xml.etree (no openpyxl)
- `extraction-patterns.md` — PDF/XLSX statement extraction patterns for pension, mortgage, property docs
