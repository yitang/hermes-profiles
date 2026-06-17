# SQLite ALTER TABLE Migrations for Existing Databases

## Problem

`CREATE TABLE IF NOT EXISTS` won't add new columns to an existing table.
When a schema migration adds columns, the existing database on disk keeps
the old schema. Queries referencing the new columns fail:

```
sqlite3.OperationalError: no such column: ca.opening_balance
```

## Pattern

After the `CREATE TABLE IF NOT EXISTS` statements, check the existing columns
via `PRAGMA table_info()` and `ALTER TABLE ADD COLUMN` for any that are
missing. Run ALTER TABLE **before** any seed INSERT that references the new
columns.

```python
def migrate(db: Database) -> None:
    with db._engine.connect() as conn:
        # 1. CREATE TABLE IF NOT EXISTS (handles fresh databases)
        conn.execute(text("""CREATE TABLE IF NOT EXISTS cash_accounts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            opening_balance REAL NOT NULL DEFAULT 0,
            opening_date TEXT
        )"""))

        # 2. CREATE junction tables, etc.
        conn.execute(text("""CREATE TABLE IF NOT EXISTS transaction_people (...)"""))

        # 3. ALTER TABLE for existing databases — runs BEFORE seed INSERT
        existing = {row[1] for row in
                    conn.execute(text("PRAGMA table_info(cash_accounts)")).fetchall()}
        if "opening_balance" not in existing:
            conn.execute(text(
                "ALTER TABLE cash_accounts ADD COLUMN opening_balance REAL NOT NULL DEFAULT 0"
            ))
        if "opening_date" not in existing:
            conn.execute(text(
                "ALTER TABLE cash_accounts ADD COLUMN opening_date TEXT"
            ))

        # 4. Seed INSERT (now safe because columns exist)
        conn.execute(text("INSERT OR IGNORE INTO cash_accounts ..."))
        conn.commit()
```

## Limitations

- SQLite's `ALTER TABLE ADD COLUMN` cannot add `NOT NULL` without `DEFAULT`.
  Always provide a `DEFAULT` value when adding a NOT NULL column.
- `ALTER TABLE` cannot add foreign key constraints, UNIQUE, or PRIMARY KEY
  to existing columns. Those need table recreation.
- `PRAGMA table_info()` returns `(cid, name, type, notnull, dflt_value, pk)`.
  We only care about the `name` field (index 1).

## When to use

Any time you add new columns to an existing SQLite table in a project that
has a persistent database file on disk. This pattern makes migration
idempotent — safe to run multiple times.
