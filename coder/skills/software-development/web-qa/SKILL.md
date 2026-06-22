---
name: web-qa
description: "Verify, triage & fix bugs in live web apps — reproduce from reports, write tests, plan fixes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [qa, bug-verification, triage, frontend-backend-contract, data-integrity]
    related_skills: [systematic-debugging, test-driven-development, writing-plans]
---

# Web QA — Verify, Triage & Fix Bugs in Live Web Apps

Use when the user asks to **verify bugs against a running web application**, triage bug reports, write test cases for identified issues, or plan fixes for web UI/data bugs. Covers frontend-backend mismatches, data integrity bugs, rendering issues, and cascading zero-value problems.

## Workflow

### 1. Reproduce & Verify Each Bug
For every bug in the report:
1. **Navigate to the affected page** — log in if needed (`browser_navigate`, `browser_type`, `browser_click`)
2. **Snapshot the visible state** — what does the user actually see? (badges, tables, numbers)
3. **Query the database directly** — connect with Python/sqlite3, inspect actual data rows
4. **Trace the code path** — frontend template → backend route → DB query, each hop

### 2. Classify Each Bug
Mark each as one of:
- **Confirmed bug** — UI state contradicts DB or expected behavior (data integrity, logic error)
- **Frontend/backend mismatch** — API method/content-type mismatch between client and server
- **Expected empty state** — no data exists yet; pages show "No data" which is correct
- **Cascading bug** — symptom of another root bug (e.g., Net Worth = 0 because Balances = 0)

### 3. Write Test Case for Each Confirmed Bug
Before planning fixes, write a test that would fail today and pass after the fix:
```python
def test_<bug_description>(db):
    """Docstring describing expected behavior"""
    # Setup: insert known data or query existing
    # Assert: verify correct state
```

### 4. Plan Fixes Together
Present all fixes as a prioritized list with dependencies between bugs (fix root cause first). Group by priority:
- **P0**: Data integrity / incorrect numbers (duplicates, wrong aggregations)
- **P1**: UI logic errors (wrong time windows, broken filters)
- **P2**: Cleanup tasks (remove test data, closed accounts)
- **P3**: UX improvements (renaming tabs, chart clarity)

### 5. Deliver Consolidated Fix Plan
- Execution order with dependency DAG
- Each fix: what to change, where in code, expected outcome
- Group interdependent fixes under their shared root cause

## Common Pitfalls

### Frontend ↔ Backend Mismatch
Frontend sends **POST + JSON body** but backend is a **GET endpoint expecting query params** (or vice versa). Always check both sides of the contract:
- Frontend template → look for `fetch()`, `.post()`, form `method`
- Backend route → look for `@router.post()` vs `@router.get()`, request body model vs query params

### Empty Categories in Aggregations
"Spending Breakdown" showing only one number often means **all transactions are uncategorized** — the category key is blank/None. Filter out null categories or label them "Uncategorized".

### Cascading Zero-Balances
When account balances are all zero, net worth, spending breakdowns, and portfolio values will all be wrong (or zero). The root cause is usually:
- Sync engine not updating `balance` after importing transactions
- Missing running balance computation in import logic
- Duplicate records inflating computed totals

### Duplicate Records via SQL Detection
To find exact duplicates in any table:
```sql
SELECT <grouping_columns>, COUNT(*) as cnt
FROM <table>
GROUP BY <grouping_columns>
HAVING cnt > 1;
```
Check source DB vs app DB separately to determine if duplicates come from source data or sync engine.

### Trade/Portfolio Filter Bugs
Pages showing empty despite DB data often have an incorrect filter condition:
- `type_id == "investment"` when no accounts have that type
- Foreign key references to non-existent related records
- Check the actual values in the referenced column vs what the filter expects

## Output Format
For each bug, provide:
1. **Symptom** — what the user sees (quote numbers/badges from browser)
2. **Root Cause** — verified via DB query + code inspection (cite file + line)
3. **Test Case** — Python test that would fail today
4. **Fix Plan** — concrete changes with file paths

## Reference Files

- `references/duplicate-detection-sql.md` — SQL queries for exact duplicate detection, balance discrepancy checks, and empty category diagnosis.

## When NOT to Use This Skill
- Pure database schema changes without web UI impact
- Performance optimization of non-user-facing batch jobs
- API documentation updates without behavioral change
