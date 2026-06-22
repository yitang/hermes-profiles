# SQL Patterns for Duplicate Detection & Data Integrity

When verifying bugs involving inflated numbers, duplicated records, or data integrity issues.

## Exact Duplicate Grouping
Find all rows with identical values in a set of columns:
```sql
SELECT <col1>, <col2>, ..., COUNT(*) as cnt
FROM <table>
GROUP BY <col1>, <col2>, ...
HAVING cnt > 1;
```

## Find All Detail Rows in Duplicate Groups
To see the actual duplicate rows (not just counts):
```sql
SELECT * FROM <table>
WHERE (<col1>, <col2>, ...) IN (
    SELECT <col1>, <col2> FROM <table>
    GROUP BY <col1>, <col2> HAVING COUNT(*) > 1
);
```

## Compare Row Counts Between Two DBs
To verify if duplicates exist in source or app DB:
```bash
# Source DB count per symbol
python3 -c "
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser('<path-to-source>'))
rows = conn.execute('SELECT symbol, COUNT(*) FROM investment_trades GROUP BY symbol').fetchall()
for r in rows: print(f'{r[0]:60s} | {r[1]} trades')
"

# App DB count (same query)
python3 -c "
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser('<path-to-app-db>'))
rows = conn.execute('SELECT symbol, COUNT(*) FROM investment_trades GROUP BY symbol').fetchall()
for r in rows: print(f'{r[0]:60s} | {r[1]} trades')
"
```

## Detect Running Balance Issues
When account balances should reflect transactions:
```sql
-- Expected balance per account
SELECT account_id, SUM(amount) as expected_balance
FROM transactions
GROUP BY account_id;

-- Actual stored balance
SELECT id, name, balance FROM accounts;

-- Join to find discrepancies
SELECT a.id, a.name, a.balance, COALESCE(t.expected_balance, 0) as expected_balance,
       a.balance - COALESCE(t.expected_balance, 0) as discrepancy
FROM accounts a
LEFT JOIN (SELECT account_id, SUM(amount) as expected_balance FROM transactions GROUP BY account_id) t
ON a.id = t.account_id;
```

## Check for Empty/Null Category Keys
When aggregations show only one lump sum:
```sql
SELECT COUNT(*) as categorized,
       SUM(CASE WHEN category_id IS NOT NULL THEN 1 ELSE 0 END) as with_category
FROM transactions WHERE amount < 0;
```
