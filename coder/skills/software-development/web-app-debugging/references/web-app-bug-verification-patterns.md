# Web App Bug Verification Patterns (FastAPI + Jinja2/HTMX)

## Complete Verification Checklist (when user provides bug list from main.org)

For EACH reported bug, complete all steps below before proposing any fix:

### 1. Browser Verification
- [ ] Navigate to affected page (`<url>`)
- [ ] Confirm the EXACT symptom manifests (don't assume it does)
- [ ] Record observed values in format: `expected=X, observed=Y`
- [ ] For visual bugs (charts, layouts): take screenshot with `browser_vision`

### 2. Database State Verification
Run these queries against the live DB:
```bash
# General counts
sqlite3 ~/.pfn/pfin.db "SELECT 'accounts', COUNT(*), SUM(CASE WHEN balance=0 THEN 1 ELSE 0 END) FROM accounts"
sqlite3 ~/.pfn/pfin.db "SELECT 'transactions', COUNT(*) FROM transactions"
sqlite3 ~/.pfn/pfin.db "SELECT 'categories', COUNT(*) FROM categories"
sqlite3 ~/.pfn/pfin.db "SELECT 'trades with dupes', COUNT(*) FROM (SELECT symbol, date, quantity, COUNT(*) AS cnt FROM investment_trades GROUP BY symbol,date,quantity HAVING cnt>1)"

# Balance check: any non-zero balances?
sqlite3 ~/.pfn/pfin.db "SELECT name, type_id, balance FROM accounts WHERE balance != 0"

# Category coverage: how many transactions have categories?
sqlite3 ~/.pfn/pfin.db "SELECT COUNT(*) FROM transactions WHERE category_id IS NOT NULL AND category_id != ''"
```

### 3. Code Path Tracing
Read these files in order for each page:
1. `pfin_api/routes/web.py` — HTML page handlers
2. `pfin_api/routes/<feature>.py` — API endpoints
3. `templates/<page>.html` — rendering logic + any inline JS
4. `pfin_db/sync.py` — only if data integrity suspected

### 4. Root Cause Classification (pick ONE)
Use the table from the main SKILL.md. If multiple categories apply, pick the ROOT cause (not the symptom).

### 5. Write Failing Test
One test per confirmed bug. See templates below.

## Database Check Reference Recipes

### Account Balances
```sql
-- Total balance across all accounts
SELECT SUM(balance) FROM accounts;

-- Balance by account type
SELECT type_id, COUNT(*), SUM(balance) FROM accounts GROUP BY type_id;

-- Any negative balances (credit cards?)
SELECT name, balance FROM accounts WHERE balance < 0;

-- Any positive balances (checking/savings?)
SELECT name, balance FROM accounts WHERE balance > 0;
```

### Transaction Categorization
```sql
-- How many are categorized?
SELECT 
  CASE WHEN category_id IS NULL OR category_id = '' THEN 'uncategorized' ELSE 'categorized' END as cat_status,
  COUNT(*) 
FROM transactions 
GROUP BY cat_status;

-- Breakdown of uncategorized spending (last 180 days)
SELECT COALESCE(c.name, '<uncategorized>') as cat, 
       SUM(ABS(t.amount)) as total_spent
FROM transactions t
LEFT JOIN categories c ON c.id = t.category_id
WHERE t.amount < 0 AND t.date >= date('now', '-180 days')
GROUP BY cat
ORDER BY total_spent DESC;
```

### Trade Duplicates
```sql
-- Groups with duplicate (date, symbol, quantity)
SELECT symbol, date, quantity, COUNT(*) as cnt,
       GROUP_CONCAT(id) as ids
FROM investment_trades 
GROUP BY date, symbol, quantity 
HAVING cnt > 1;

-- Per-symbol total quantity (inflated if duplicates exist)
SELECT symbol, SUM(quantity) as total_qty
FROM investment_trades 
GROUP BY symbol;

-- Expected quantity (if unique by source_id)
SELECT symbol, SUM(quantity) as total_qty, COUNT(DISTINCT source_id) as distinct_sources
FROM investment_trades 
GROUP BY symbol;
```

### Net Worth History Sanity Check
```sql
-- Total of all transactions per account (what net worth history computes)
SELECT a.name, SUM(t.amount) as running_balance
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
GROUP BY a.id;

-- Compare against stored account balances (if sync ran)
SELECT a.name, a.balance as stored_balance, COALESCE(SUM(t.amount),0) as computed_balance
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
GROUP BY a.id;
```

## Test Templates

### POST vs GET Mismatch Test
```python
def test_search_accepts_json_post():
    from fastapi.testclient import TestClient
    from pfin_api import create_app
    # ... setup DB fixture ...
    
    resp = client.post("/api/transactions/search", json={"payee": "Tesco"})
    assert resp.status_code == 200, f"POST returned {resp.status_code} (expected GET or POST handler)"
```

### Balance Computation Test
```python
def test_account_balance_reflects_transactions():
    # Insert account + transactions
    db.add(Account(name="Test", type_id="checking", balance=0.0))
    db.add(Transaction(account_id=..., amount=-50.0))
    db.add(Transaction(account_id=..., amount=+30.0))
    db.commit()
    
    # Refresh and check
    acct = db.get(Account, ...).balance
    assert acct == -20.0  # sum of transaction amounts
```

### Duplicate Trade Test
```python
def test_no_duplicate_investment_trades():
    # Insert same trade twice with different IDs
    t1 = InvestmentTrade(id="aaa", symbol="TEST", date=..., quantity=10.0)
    t2 = InvestmentTrade(id="bbb", symbol="TEST", date=..., quantity=10.0)
    db.add(t1); db.add(t2); db.commit()
    
    # Should dedup to 1, not 2
    assert len(db.query(InvestmentTrade)) == 1
```

### Calendar Month Filter Test
```python
def test_month_expense_is_actual_calendar_month():
    # Insert txn in current month: -100
    db.add(Transaction(account_id=..., date=date.today(), amount=-100.0))
    # Insert txn in last month: -500 (should NOT count)
    db.add(Transaction(account_id=..., date=last_month_date, amount=-500.0))
    db.commit()
    
    # Only the current-month transaction should count
    assert month_expense == 100.0  # NOT 600.0
```
