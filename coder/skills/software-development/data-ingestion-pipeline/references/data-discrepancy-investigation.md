# Data Discrepancy Investigation

How to systematically investigate why two databases (source and target)
have different row counts. Pattern emerged from reconciling a golden-source
finance.db against an app database that had accumulated data via a
different import pipeline over several years.

## Workflow

### 1. Establish baseline counts by entity

Don't start with global totals. Break down by the natural unit of
account — usually the source table or the app's account model.

```sql
-- Per-source table in golden source
SELECT 'source_tbl' AS tbl, COUNT(*) FROM source_tbl

-- Per-account in app DB
SELECT a.name, COUNT(t.id) AS txns, MIN(t.date), MAX(t.date)
FROM accounts a LEFT JOIN transactions t ON t.account_id = a.id
GROUP BY a.id
```

### 2. Check for duplicates in the app DB

If the app DB had a different import pipeline (or older version of it),
duplicates are the most likely cause. Compare:

```sql
SELECT 'total' AS info, COUNT(*) FROM transactions WHERE account_id = '...'
UNION ALL
SELECT 'unique', COUNT(DISTINCT date || amount || description)
FROM transactions WHERE account_id = '...'
```

If unique count is significantly lower than total count, the old pipeline
imported without dedup. The unique count is the number to compare against
the golden source.

### 3. Compare by year

Discrepancies often concentrate in specific periods:

```sql
SELECT strftime('%Y', date) AS year, COUNT(*) AS txns
FROM transactions WHERE account_id = '...'
GROUP BY year ORDER BY year;

SELECT strftime('%Y', date) AS year, COUNT(*) AS txns
FROM source_table GROUP BY year ORDER BY year;
```

### 4. Spot-check a specific date

Pick a date where source and app both have data. Compare exact rows:

- Use `ORDER BY amount, description` on both sides so rows line up
- Verify sign conventions (is debit stored as positive or negative?)
- Verify description casing (source may store lowercased, app uppercased)

### 5. Identify per-entity date gaps

Find which source entity has data the app hasn't seen yet, and vice versa:

```sql
-- What does source have that app doesn't?
SELECT MIN(date), MAX(date) FROM source_tbl
-- vs
SELECT MIN(date), MAX(date) FROM transactions WHERE account_id = 'mapped_acct'
```

A later end-date in source means fresh data to sync.
An earlier start-date or higher count in app means historical data the
source doesn't cover.

### 6. Compile comparison table

Build a per-account table:

| Account | App total | App unique | Source total | Gap | Direction |
|---|---|---|---|---|---|
| Lloyds | 8,559 | 4,670 | 5,336 | +666 | Source has more (2019-2020) |
| AMEX Gold | 3,315 | 2,058 | 2,173 | +115 | Source has more (2025-2026) |

### 7. Check for orphan accounts

Accounts in the app with no counterpart in any source table. These are
usually test accounts or manually-entered data. Decide whether to:
- Ignore them (keep as-is, don't sync into them)
- Investigate if they need a source mapping

## Common findings

| Finding | Likely cause | Action |
|---|---|---|
| App has ~2x the unique count | Old pipeline imported without dedup | Accept; sync is append-only going forward |
| App has more data in specific years | Source collection started later | Accept; source is the canonical forward path |
| Source has data past app's latest date | Sync hasn't been run yet | Build the sync |
| App has accounts with no source mapping | Manual/test entries or renamed accounts | Verify mapping; may need disambiguation |
| Duplicate app account records | Manual creation error or rename artifact | Route sync to active account only |

## Amount sign detective work

Sources represent debits/credits differently. Clues to look for:

- **Positive debit / Positive credit** (Lloyds pattern): Two columns, both
  always ≥ 0. Debits and credits are stored separately. The app converts
  to a single signed amount (negative = debit).
- **Signed amount** (Amex, Barclays pattern): One amount column. Positive
  may be debit or credit depending on bank. Check a known transaction
  (e.g. a coffee purchase) to determine the convention.
- **OFX TRNTYPE**: `DEBIT`/`CREDIT` tag in the transaction record.
  Reliable; map directly.
