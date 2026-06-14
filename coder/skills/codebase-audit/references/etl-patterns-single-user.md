# ETL Patterns — Single-User Edition

Adapting enterprise data pipeline concepts for local, single-user applications (SQLite, cron scripts, CSV/OFX imports).

## The Problem: Enterprise Patterns Don't Fit

Enterprise patterns were designed for distributed systems with thousands of concurrent writers, SLA requirements, and dedicated ops teams. A personal finance app has one writer (you), one reader (you), and data that arrives at most once a week via bank export files. The goal is **correctness and recoverability**, not throughput or uptime guarantees.

## Concept Mappings

### Idempotency — You Already Have It (Probably)
Enterprise: distributed transaction retries, exactly-once semantics.
Single-user: `INSERT OR IGNORE` on `(date, amount, description)` key. If you re-import a file twice, the second pass silently ignores duplicates. That's exactly-once at single-user scale.

**What to verify:** Check that your dedup key covers all columns that distinguish one transaction from another. Date alone is insufficient — two transactions on the same date with different amounts or descriptions will collide if not included.

### CDC (Change Data Capture)
Enterprise: Kafka Connect, Debezium, log tailing from WAL.
Single-user: File inbox + re-import. Drop a new export in `inbox/`, run import script, file gets archived. If you discover the parser was wrong, fix it, copy the original back into `inbox/`, and re-run.

**Practical pattern:** Keep originals forever in `archive/`. The archive IS your CDC log — it contains every source record that ever passed through the pipeline.

### Dead Letter Queue
Enterprise: DLQ topic with error handling workflow, poison pill detection.
Single-user: File left in `inbox/` after a failed import, with an error message printed to stdout. The inbox itself is the DLQ — anything not successfully imported and archived stays behind for you to inspect.

**What to verify:** Ensure failed imports don't partially write data. Either use transactions that roll back on failure, or check every row before committing.

### Data Quality Gate
Enterprise: Great Expectations, Soda Core, custom assertions on billions of rows.
Single-user: A `validate.py` script that runs after import and checks:
- Amounts are numeric and non-zero
- Dates fall in expected ranges (e.g., 2000-2100)
- Transaction totals reconcile with the last known ledger balance
- No suspicious spikes in spending patterns

**Implementation:** One Python file, one SQLite query per check, print warnings to stdout. If you're using this as a cron job, exit non-zero on any failure so the scheduler can alert you.

### Reconciliation
Enterprise: Hash checks between source and target, row count comparisons.
Single-user: Sum all transactions for an account, compare with the OFX ledger balance. They should match within £0.01 (rounding). A mismatch means something went wrong during parsing or insertion — possibly a bad import you missed.

**Key insight:** This is the single highest-impact data quality check you can add. One number tells you whether your entire transaction history is internally consistent.

### Canonical Table
Enterprise: Data warehouse with conformed dimensions, unified entity resolution.
Single-user: A `CREATE OR REPLACE VIEW` that standardises columns across all accounts. Instead of having `v_combined` with inconsistent columns from different source tables, create a view with a fixed schema (date, account, amount, description, category) that maps each source's column names to the canonical ones.

**Why:** All analytics queries — spending by category, trends over time, budget comparisons — read from this one clean interface. Adding a new bank just means adding another `UNION ALL` branch, not rewriting every report query.

### Price/Value Refresh
Enterprise: Streaming market data feeds, Bloomberg API.
Single-user: Monthly cron job pulling fund NAVs from Yahoo Finance (or similar free API). Store prices in a `fund_prices(date, fund, price)` table. Your valuation query joins the last known units with the NAV at month-end.

**Trade-off:** Free APIs have rate limits and occasional failures. One monthly pull per fund is trivial — no need for complex retry logic. If a particular month's price fails, use the previous month's price (forward-fill) rather than breaking the whole balance sheet.

## Anti-Patterns to Avoid

| Enterprise Pattern | Why It Doesn't Fit Single-User |
|---|---|
| Separate staging tables | Adds maintenance overhead for no throughput gain |
| Async message queues | You have one producer and one consumer — synchronous is simpler |
| Schema versioning with migrations | Your schema changes rarely enough that a manual `ALTER TABLE` + re-run from archive is sufficient |
| Real-time dashboards | Monthly net worth snapshots are all you need; push-based updates beat polling |
| Automated alerting infrastructure | A cron job that exits non-zero on validation failure, logged to stdout, and checked by your existing scheduler — no PagerDuty required |
