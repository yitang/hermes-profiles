# Schema Migration Pitfalls (CREATE TABLE IF NOT EXISTS)

## The Problem

A migration function uses `CREATE TABLE IF NOT EXISTS` to define a table with new columns:

```python
conn.execute(text("""
    CREATE TABLE IF NOT EXISTS cash_accounts (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL DEFAULT 'Cash Wallet',
        opening_balance REAL NOT NULL DEFAULT 0,  # ← new column
        created_at TEXT DEFAULT (datetime('now'))
    )
"""))
```

This works for **fresh databases** — the table is created with all columns. But for **existing databases** where the table was already created by an earlier version of the schema, `IF NOT EXISTS` does nothing. The old table keeps its original columns, and the new column is silently absent.

## The Fix

Add ALTER TABLE migrations after the CREATE TABLE, using `PRAGMA table_info` to check which columns already exist:

```python
# After CREATE TABLE IF NOT EXISTS (which is a no-op for existing DBs)…
existing_cols = {row[1] for row in
                 conn.execute(text("PRAGMA table_info(cash_accounts)")).fetchall()}
if "opening_balance" not in existing_cols:
    conn.execute(text(
        "ALTER TABLE cash_accounts ADD COLUMN opening_balance REAL NOT NULL DEFAULT 0"
    ))
if "opening_date" not in existing_cols:
    conn.execute(text(
        "ALTER TABLE cash_accounts ADD COLUMN opening_date TEXT"
    ))
```

## Critical Ordering

**The ALTER TABLE migrations must run BEFORE any seed INSERT that references the new columns.**

If the seed INSERT comes first:
```python
conn.execute(text(
    "INSERT INTO cash_accounts (id, name, opening_balance) VALUES (…)",
    #                                ^^^^^^^^^^^^^^^^
    #          This column doesn't exist yet in the old table!
))
conn.commit()

# ALTER TABLE runs later but we never get here — the INSERT failed above
```

Result: the server crashes at startup with `sqlite3.OperationalError: table cash_accounts has no column named opening_balance`.

**Correct order:**
1. `CREATE TABLE IF NOT EXISTS` (new-table path — also handles fresh DBs)
2. `PRAGMA table_info` checks + `ALTER TABLE ADD COLUMN` (existing-table path)
3. Seed INSERT (now safe because both new and old tables have the column)

## When to Check For This

- Any `migrate_*()` function that uses `CREATE TABLE IF NOT EXISTS` and was **later extended** with new columns
- Any codebase that ships a schema as part of the application (not managed via a proper migration tool like Alembic)
- During **code quality review** of any subagent that modified schema-creation code, verify whether the new columns would be silently absent on existing databases

## Worktree Path Resolution Trap

When patching db.py in a worktree context, the `patch` tool may resolve relative paths against the **main repo root** (current working directory) instead of the **worktree checkout** (`.worktrees/<name>/`). If you merge the worktree branch to master first, then patch `pfin-core/pfin_db/db.py` from the main repo CWD, the change goes to the correct copy. But if you haven't merged yet and the worktree is still active, the path may resolve to the wrong checkout.

**Detection after patching schema code:**
```bash
# Check if the patch landed in the worktree or the main repo
diff <(git -C .worktrees/<name>/ show HEAD:pfin-core/pfin_db/db.py) \
     pfin-core/pfin_db/db.py
# If different, you're looking at two different copies
```
