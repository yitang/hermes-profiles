# SQL LEFT JOIN COUNT(*) Overcounting Pitfall

## The Bug

When aggregating with `LEFT JOIN` + `GROUP BY`, using `COUNT(*)` counts the NULL-producing row from untagged entities as 1, not 0.

```sql
-- WRONG: untagged person gets entry_count = 1
SELECT p.id, p.name, COALESCE(SUM(m.amount), 0) as total, COUNT(*) as entry_count
FROM people p
LEFT JOIN transaction_people tp ON p.id = tp.person_id
LEFT JOIN manual_entries m ON tp.transaction_hash = m.transaction_hash
GROUP BY p.id

-- RIGHT: untagged person gets entry_count = 0
SELECT p.id, p.name, COALESCE(SUM(m.amount), 0) as total, COUNT(tp.transaction_hash) as entry_count
FROM people p
LEFT JOIN transaction_people tp ON p.id = tp.person_id
LEFT JOIN manual_entries m ON tp.transaction_hash = m.transaction_hash
GROUP BY p.id
```

## Why It Happens

- `LEFT JOIN` with no match produces a single row filled with NULLs.
- `COUNT(*)` counts all rows in the group, including the NULL row.
- `COUNT(column)` only counts non-NULL values — junction column is NULL for untagged rows → correct count of 0.

## Rule

**Always use `COUNT(junction_table.primary_column)` or `COUNT(right_table.pk)` instead of `COUNT(*)` when the query uses LEFT JOINs that can produce NULL rows per group.**

Applies to person/project/category tagging stats, any LEFT JOIN aggregation where entities may have zero related records.

## When to Check

- Code quality review for any stats/aggregation endpoint
- Any `SELECT ... COUNT(*) FROM <entities> LEFT JOIN <junction> ... GROUP BY` pattern
- Spec reviewers should verify count semantics when reviewing data pipeline code
