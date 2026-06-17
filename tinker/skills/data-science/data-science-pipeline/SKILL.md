---
name: data-science-pipeline
description: "End-to-end data science and finance analytics pipeline: CSV/OFX ETL, financial balance computation, SQLite visualization with Plotly, personal net worth tracking. Zero external Python dependencies."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ETL, CSV, OFX, SQLite, Financial, Balance-Sheet, Visualization, Net-Worth, ETL, Data-Ingestion]
---

# Data Science & Finance Analytics Pipeline

End-to-end pipeline for financial data processing: import raw CSV/OFX statements → clean and normalize → store in SQLite → generate interactive visualizations → compute personal net worth. Zero external Python dependencies (uses stdlib + sqlite3).

## When to Use

- Ingesting bank/investment statements (CSV, OFX, XLSX) into a unified database
- Building financial dashboards and charts from SQLite data
- Computing and tracking personal/net-worth over time
- Data pipeline where pip install is unavailable (uses stdlib/zip/xml for XLSX)

## Architecture Overview

```
data/raw/           ← all raw exports (single source of truth, git-tracked)
    ├── lloyds_2024.csv
    ├── hsbc_2025.ofx
    └── vanguard_statement.xlsx

clean.py            → data/cleaned/         ← canonical CSVs per account
inbox/              ← staging area for import.py (one-time drops)
import.py           → finance.db            → /archive/ (timestamped imports)

build_balance_sheet.py → balance_sheet table (monthly snapshots)
plot_nw.py          → net_worth.html        ← interactive Plotly chart
```

## Core Concepts

### Cash-Flow vs Balance-Sheet Accounts

**Never mix these two types:**

| Type | Examples | Data Model | Analysis Use |
|------|----------|------------|--------------|
| **Cash-flow** | Current accounts, credit cards | Per-transaction: `(date, amount, description, balance)` | Income/expense tracking, spending breakdowns |
| **Balance-sheet** | Mortgages, pensions, investments, property | Periodic snapshot: `(date, value)` only | Net worth calculation, equity tracking |

Credit cards are cash-flow only (paid in full monthly). Including them in net worth double-counts.

### Database Schema

```sql
CREATE TABLE v_combined AS  -- unified view across all accounts
SELECT account, date, amount, description, balance, category
FROM lloyds UNION ALL
FROM hsbc UNION ALL
FROM amex_ba ... ;

CREATE TABLE balance_sheet (
    date TEXT NOT NULL,       -- YYYY-MM-01 (month start)
    account TEXT NOT NULL,
    amount REAL NOT NULL,     -- positive=asset, negative=liability
    kind TEXT NOT NULL,       -- 'asset' or 'liability'
    PRIMARY KEY (date, account)
);
```

---

## Labeled Subsections: Phase-by-Phase Details

### 1. Detection & Routing (csv-data-pipeline)

**The Header Collision Problem:** Two accounts may produce CSVs with identical headers. Header-only detection cannot distinguish them → data misrouted to wrong table.

**Fix: Filename-based routing as primary, header matching as fallback.**

```python
def detect_account(filepath):
    fname = os.path.basename(filepath).lower()
    # 1. Filename-based (PRIORITY)
    if 'lloyds' in fname and 'cleaned' in fname: return 'lloyds_cleaned'
    if 'hsbc_credit' in fname and 'cleaned' in fname: return 'hsbc_credit_cleaned'
    # 2. Header fallback for unknown filenames
    header = read_first_line(filepath)
    cols = [c.strip().lower() for c in header.split(',')]
    if len(cols) >= 6 and 'date' in cols and 'amount' in cols:
        return 'hsbc'
    return None
```

**Pitfalls:**
- Never route by `len(header) == N` — columns change over time
- Always compare ALL cleaned outputs' headers for collisions before building routing logic
- UTF-8 BOM (`\ufeff`) appears as phantom column name — strip it before parsing: `content = content.lstrip('\ufeff')`

### 2. Cleaning & Normalization (csv-data-pipeline + financial-etl)

**Sign conventions vary by bank.** Document the normalization per-bank in code comments:
- AMEX Gold (old): negated for debit (`-£50` = spending)
- Barclays OFX/CSV: negative = debit spending
- HSBC: usually negative for spending
- Lloyds legacy: same pattern

**OFX balance backward-winding:** Use `<LEDGERBAL>` anchor to compute running balances. Only valid when data is contiguous — skip if inter-txn gap > 30 days or gap to anchor > 10 days (sparse data produces garbage).

**Audit trail (mandatory):** Every clean.py run generates:
- `manifest.md` — summary of accounts, file counts, raw→clean reductions
- `sign_fixes.csv` — every amount sign corrected
- `duplicates.csv` — rows removed during dedup
- `balance_anchors.csv` — OFX LEDGERBAL sources used

**Preserve pre-computed bank balances:** Lloyds CSVs include a `Balance` column (bank-computed running balance). Do NOT overwrite with zeros when no OFX anchor exists.

### 3. Import & Schema Evolution (csv-data-pipeline)

**Schema/code sync rule:** If `import.py` creates a table at runtime, that table MUST also exist in `init_schema.py`. Mismatch causes DB rebuild failures. Always check both files before adding new tables.

**Schema evolution requires 5-file coordination:** Adding any column means updating ALL of: `init_schema.py`, `COLUMN_WHITELIST`, every parser, and audit/verification queries. After any change, rebuild DB from scratch and verify with a direct query.

### 4. Database Schema for Investment Accounts (financial-etl)

Brokerage accounts get TWO tables:
- `<account>_cash` — deposits, withdrawals, fund buys/sells with running balance
- `<account>_investment` — per-fund buy/sell records without balance column

**Transaction type classification** — text matching on "Details" field, ordered most-specific to least:
```python
if 'selling of account investments' in d:    return ('Sell', 'sell')  # must come first!
if 'regular deposit' in d:                   return ('Deposit', 'transfer_in')
if 'deposit' in d:                           return ('Deposit', 'transfer_in')
if 'bought' in d:                            return (details, 'buy')
if 'account fee' in d:                       return ('Fee', 'fee')
```

### 5. Balance Sheet & Net Worth (personal-balance-sheet + financial-etl)

**build_balance_sheet.py pattern:** Query all source tables, compute monthly values for every account, write `balance_sheet(date, account, amount, kind)`. Use `INSERT OR REPLACE` for idempotent re-runs.

**Forward-fill rules:**
- Active accounts (last data within 3 months): forward-fill to chart end
- Dead accounts (closed/paid off): stop at last data month, drop to zero
- Credit cards: exclude entirely — already reflected in current account outflows
- Mortgage: use balance from `mortgage` table directly; deduct from net worth

**Property as asset:** Without house valuation, net worth looks catastrophic. Extract from mortgage offer PDFs using `pdftotext -layout` and grep for "Value of the property". Use UK average ~3%/yr growth between valuations.

### 6. Visualization (sqlite-visualization)

Build Plotly HTML charts directly from SQLite queries — no pip installs needed. Build figure dict by hand, embed Plotly via CDN script tag.

**Critical pitfalls:**
- String x-values (month strings like "2022-01") get auto-parsed as year 2022. Always set `"type": "category"` on x-axes with date-like strings.
- Pin Plotly CDN version — auto-latest can break on API changes.
- Stacked bars need `barmode: "stack"` with expenses as positive values (use `ABS()` in SQL).

**Two-panel layout** — top panel shows monthly breakdown (bars), bottom shows cumulative line. Share x-axis, independent y-domains. Add filled area to cumulative line for visual punch.

**Stacked area chart** — assets above zero (greens), liabilities below zero (reds), net worth line overlay (black, bold). Set zero reference line via shapes.

### 7. Document Extraction Support (ocr-and-documents + personal-balance-sheet)

For extracting data from financial statements:
- `web_extract` for remote URLs (PDF-to-markdown)
- `pdftotext` for local text-based PDFs (zero deps)
- `pymupdf` for structured extraction with Python (tables, images, metadata)
- `marker-pdf` only when OCR is needed (~5GB install)

Mortgage offer parameter extraction: `pdftotext -layout "offer.pdf" - | grep -iE "amount|rate|duration|instalment"` extracts 5 parameters.

---

## Complete Reference Examples

See the skill's support files for:
- **`references/header-collision-diagnosis.md`** — step-by-step diagnostic recipe for header collision detection
- **`references/ofx-balance-computation.md`** — detailed guide on OFX LEDGERBAL parsing and backward-winding
- **`references/schema-sync-checklist.md`** — pre-import checklist for init_schema.py ↔ import.py consistency
- **`references/balance-zeroing-diagnosis.md`** — 5-cause diagnostic path when bank CSV balances end up as zeros
- **`references/xlsx-stdlib-parsing.md`** — parsing XLSX investment statements without openpyxl (zip + xml.etree)
- **`references/barclays-balance-recovery.md`** — restoring lost balance data patterns
- **`references/net-worth-stacked-chart.md`** — stacked area chart building from SQLite
- **`references/forward-fill-time-series.md`** — handling multi-account time series with staggered dates
- **`templates/boilerplate.py`** — minimal Plotly chart generation template
- **`references/financial-statements-batch.md`** — batch extraction of structured data from multiple annual PDFs

## Related Skills

- **ocr-and-documents** — PDF/text extraction for statement parsing