# SQLAlchemy `text()` Parameter Binding Pitfalls

## Symptom

A subagent writes a query with `?` placeholders and passes positional arguments as a plain list:

```python
rows = conn.execute(
    sa_text("SELECT * FROM t WHERE col IN (?, ?, ?)"),
    ["val1", "val2", "val3"]
).fetchall()
```

Error:

```
sqlalchemy.exc.ArgumentError: List argument must consist only of dictionaries
```

## Root Cause

`sqlalchemy.text()` (and `sa_text()`) uses **named‑parameter style** (`:name`) by default, not `?` positional style. When you pass a plain list, SQLAlchemy interprets it as a list of row‑parameter dicts and expects each element to be a `dict`.

## Fix

### Option A — Use `:name` placeholders with a dict (preferred)

```python
names = {"a0": "val1", "a1": "val2", "a2": "val3"}
rows = conn.execute(
    sa_text("SELECT * FROM t WHERE col IN (:a0, :a1, :a2)"),
    names
).fetchall()
```

For dynamic IN‑clause lengths:

```python
items = ["val1", "val2", "val3"]
placeholders = ",".join(f":a{i}" for i in range(len(items)))
params = {f"a{i}": v for i, v in enumerate(items)}

rows = conn.execute(
    sa_text(f"SELECT * FROM t WHERE col IN ({placeholders})"),
    params
).fetchall()
```

### Option B — Use `text()` with `bindparams` + `execution_options`

For SQLite connections you control, you can also switch to `?` style globally:

```python
# At connection time:
conn = engine.connect().execution_options(driver_sqlite_paramstyle="qmark")
```

But for code that shares a connection with other (named‑param) queries, stick with Option A.

## Detection

When a subagent writes a SQL query with IN clause, check:

- Are the placeholders `?` (positional) or `:name` (named)?
- Is the params argument a `dict` (named‑style) or a `list` (positional)?
- Does the query use `sa_text()` or raw `text()` with connection.execute()?

SQLite accepts `?` style from the raw `sqlite3` module, but SQLAlchemy layers on top of it. The tests may pass during subagent's own isolated run (if they use a different connection mode) and fail during full suite. Always run the full test suite.

## Existing codebase patterns

This project uses `sa_text(...)` consistently with named parameters and dicts:

```python
# Good — named params with dict:
conn.execute(
    sa_text("SELECT 1 FROM manual_entries WHERE transaction_hash = :h"),
    {"h": txn_hash}
).fetchone()
```

Follow this pattern for all new queries.
