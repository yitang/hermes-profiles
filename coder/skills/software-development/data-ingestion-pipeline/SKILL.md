---
name: data-ingestion-pipeline
description: "Build append-only data ingestion pipelines with SQLite golden source — multi-source CSV/OFX ingestion, dedup, schema evolution, inbox/archive workflow."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [data-pipeline, sqlite, ingestion, dedup, etl]
    related_skills: [data-analysis, brainstorming, writing-plans]
---

# Data Ingestion Pipeline

Build append-only data pipelines that ingest records from multiple sources
into a SQLite golden source. Focused on bank/financial data but applicable
to any multi-source append-only workload.

## Core Architecture

```
inbox/  →  import.py  →  finance.db  (golden source, append-only)
                              ↓
                        archive/  (raw originals preserved)
```

- **inbox/** — drop raw exports here
- **import.py** — the importer: detect source, parse, dedup, insert, archive
- **finance.db** — SQLite golden source with canonical tables (transactions, investment_trades, balance_sheet). Per-source raw tables may be kept as legacy audit trails.
- **archive/** — processed files timestamped and moved here

## Two-Tier Database Architecture

```
raw inbox/  →  import.py  →  finance.db  (golden source, canonical schema)
                                    │
                            sync.py │  thin incremental copy (~100 lines)
                                    ▼
                          app.db  (pfin.db — enriched with
                          categories, projects, tags, budgets)
```

### Golden source (finance.db) — canonical schema

The pipeline **owns data normalization**. It produces clean canonical tables:

- `transactions(date, amount, description, description_original, account_type, source_name, source_id PK, source_file, extra)` — all cash/credit transactions
- `investment_trades(date, type, symbol, quantity, price, fees, account_type, source_name, source_id PK, source_file, extra)` — buys/sells
- `balance_sheet(date, account, amount, kind)` — monthly net worth snapshots

`account_type` is one of: `checking`, `credit`, `investment`, `pension`.
`source_name` is the human-readable source: `"Barclays Premier"`, `"AMEX Gold"`, etc.
Per-bank raw tables may be kept as legacy audit trails but are never queried by downstream consumers.

### App database (app.db)
- Holds both imported transactions AND user-enriched data
- Enrichment fields (categories, projects, tags, reconciled) are null on
  import — set later via the app
- Sync is **one-way, thin incremental copy**: reads canonical tables by
  watermark, inserts into app tables. No per-bank mapping logic.
- Tracks last-synced date per source in a `_sync_log` table

### Sync design rules

1. **Do zero normalization in sync.** All sign conventions, column mapping,
   format detection, and data cleaning must happen in the pipeline's import
   step. The sync copies canonical columns as-is. If sync.py grows beyond
   ~150 lines, something is wrong — normalization has leaked downstream.
2. **Account-scoped dedup**: scope dedup by account_id, not globally.
   Same date+amount+description on two accounts are two legitimate rows.
3. **Incremental runs**: per-source watermark tracking via `_sync_log`.
   `WHERE date > last_synced_date` for each canonical table.
4. **Idempotent**: re-running sync against an unchanged golden source
   should insert zero rows. Use `--dry-run` to verify before writing.
5. **source_id as dual-purpose key**: the canonical table's `source_id`
   (SHA-256 hex) becomes both `id` (PK) and `source_id` (traceability column)
   in the app DB's ORM object. Example:
   ```python
   obj = Transaction(
       id=canonical_row["source_id"],       # PK for dedup
       source_id=canonical_row["source_id"], # traceability column
       account_id=account_lookup[source_name],
       ...
   )
   ```

### App DB schema drift (ALTER TABLE)

When the ORM definition adds new columns (e.g. `source_id`, `source_table`)
but the app DB was created before those columns existed, SQLAlchemy's
`create_all()` won't add them — it only creates tables that don't exist.
The sync will fail with "no such column" on the first SELECT that lists them.

**Fix:** add missing columns with raw ALTER TABLE before running sync:

```bash
sqlite3 app.db "ALTER TABLE transactions ADD COLUMN source_id VARCHAR(16)"
sqlite3 app.db "ALTER TABLE transactions ADD COLUMN source_table VARCHAR(64)"
sqlite3 app.db "ALTER TABLE investment_trades ADD COLUMN source_id VARCHAR(16)"
sqlite3 app.db "ALTER TABLE investment_trades ADD COLUMN source_table VARCHAR(64)"
sqlite3 app.db "ALTER TABLE balance_sheet ADD COLUMN source_id VARCHAR(16)"
sqlite3 app.db "ALTER TABLE balance_sheet ADD COLUMN source_table VARCHAR(64)"
```

**Detection:** if `sync()` on a real DB crashes with "no such column" but
passes all in-memory tests, the issue is schema drift — the in-memory DB
gets fresh tables from `create_all()`, but the file DB has old schema.

## Canonical Table Pattern

When you have multiple data sources that feed a single consuming app, use
**canonical tables** with discriminator columns rather than per-source tables:

```sql
CREATE TABLE transactions (
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    description_original TEXT NOT NULL DEFAULT '',
    account_type TEXT NOT NULL,    -- "checking", "credit", "investment", "pension"
    source_name TEXT NOT NULL,     -- "Barclays Premier", "AMEX Gold", "Vanguard ISA"
    source_id TEXT PRIMARY KEY,    -- sha256(source_name|date|amount|description)[:16]
    source_file TEXT,
    extra TEXT DEFAULT '{}',       -- JSON: unmapped source columns
    imported_at TEXT DEFAULT (datetime('now'))
);
```

**Why canonical over per-source:**
- The sync/app queries one table, not N tables — no per-bank mapping in sync
- Adding a new data source adds rows to existing tables, not new tables
- Filtering by source is trivial: `WHERE source_name = 'Barclays Premier'`
- Rebuilding/migrating the source DB doesn't break the app's sync contract

**Computed tables are not canonical tables.** Tables that are derived from other
data (not directly imported) stay outside the canonical pipeline:
- `mortgage` — amortization schedule computed by `mortgage.py` from config
- `investment_holdings` — cache computed by `compute_holdings.py` from investment_trades
- `balance_sheet` — computed by `build_balance_sheet.py` from multiple sources

These are downstream consumers of canonical tables, not canonical tables themselves.
When migrating to canonical schema, leave them unchanged — only the import scripts
and their direct consumers need updating.

**When per-source tables are still acceptable:**
- The sources are genuinely different entity types (not all rows map to the
  same target schema)
- You have multiple independent consumers querying different subsets
- The data is genuinely append-only and never needs cross-source analysis

**Legacy tables:** After migrating to canonical, keep per-source raw tables as
audit trails but mark them as legacy. Never query them from downstream code.

## Architectural Diagnosis: Don't Fix Symptoms

When debugging "tight coupling" between pipeline and app, look at **what the
sync layer actually does** before recommending structural changes.

**Symptom:** sync.py is 1100 lines with per-bank mapping functions. It knows
about Barclays 6-column layout, AMEX sign conventions, Lloyds debit/credit
columns.

**Wrong fix:** "merge the repos" — this moves files around but doesn't
eliminate the coupling. The app still needs to know about every bank's format.

**Right fix:** move normalization into the pipeline. The pipeline should
produce canonical tables. The sync becomes a thin incremental copy (~100
lines). The repos can stay separate because the contract is now the canonical
schema, not 11 per-bank table layouts.

**Diagnostic questions:**
1. What does the sync code actually do? Parse it — don't guess from file size.
2. Is it doing normalization (sign conventions, column mapping) or just
   copying? If normalization, it belongs in the pipeline.
3. After moving normalization upstream, what's left? If it's just incremental
   copy, the architecture is clean — no repo merge needed.

**Do NOT design schemas by guessing or from memory.** Inspect the actual
data files first. Every bank uses its own column names, formats, and quirks:

- Read raw CSV headers and sample rows with `head` or `csv.DictReader`
- Check for quoted fields, embedded commas, multi-line values
- Look for date formats, sign conventions (positive=debit vs negative=debit)
- Count rows to verify you're reading the right file
- Verify dedup key uniqueness against real data before committing

The user's correction on this is firm: \"why can't you have a look of the
files and design the schema for now?\" — always inspect, never guess.

## Combined View Pattern (legacy — prefer canonical tables)

When using per-source tables (pre-canonical approach), add a `v_combined` view for
cross-source queries. After migrating to canonical tables, replace `v_combined` with
a thin `v_canonical` view or query `transactions` directly.

```sql
-- Legacy per-source approach (superseded by canonical tables):
CREATE VIEW v_combined AS
SELECT date, amount, memo AS description, 'SourceName' AS account,
       source_file, imported_at FROM source_table
UNION ALL
SELECT date, amount, description, 'OtherSource' AS account,
       source_file, imported_at FROM other_table;

-- Post-migration canonical approach:
CREATE VIEW v_canonical AS
SELECT date, amount, description, source_name AS account, source_file, imported_at
FROM transactions ORDER BY date;
```

Use UNION ALL — never UNION (dedup) — to preserve provenance.

## Dedup Strategy

### Single-source dedup (within finance.db)

Use a UNIQUE index on `(date, amount, description_lower)` for CSV sources.
This handles overlapping exports and re-imports safely.

**For sources that provide unique IDs** (OFX has FITID, some bank CSVs have
reference numbers), use that as the dedup key instead — it's exact.

**Risk:** same-date same-amount same-merchant purchases (e.g. two coffees).
Mitigated because banks almost always include a slight differentiator in the
description (timestamp, reference, till number). Verified against 10k+ real
rows: zero collisions with `(date, amount, description_lower)`.

### Sync dedup (finance.db → app DB) — always scope by account

When syncing from the golden source into the app database, the dedup key
MUST include the **account scope**. Multi-source tables (e.g. `barclays`
with a `account` column holding \"Premier Account\", \"20-26-46 43663337\")
map to different app accounts, and the same date+amount+description on
different accounts is a legitimate duplicate — both should be imported.

Correct dedup key: `(account_id, date, amount, description_lower)`
Wrong dedup key: `(date, amount, description_lower)` — would lose
transactions when the same merchant amount hits two accounts on the same day.

## Schema Evolution (Bank Format Changes)

Banks change their CSV schemas without notice. The parser must handle all
scenarios gracefully:

| What changes | What happens |
|---|---|
| Header labels renamed | File stays in inbox, add alias to parser |
| Column positions change | Handled automatically (name-based lookup, NEVER positional) |
| Column added (end or middle) | Auto-collected into `extra` JSON column — no data lost |
| Column removed | File stays in inbox, make column optional in parser |
| Complete format change (CSV→JSON) | File stays in inbox, write new parser |

**Critical rule:** Every parser reads by header column NAME, not position.
No index-based fallback. If the header doesn't match any known pattern,
the file is rejected with a clear error — never silently mis-imported.

**Extra column safety net:** Each table gets a TEXT `extra` column storing
unmapped CSV columns as JSON. This preserves data from new columns even
before the parser is updated.

## OFX/QBO Parsing

When a bank offers OFX or QBO, prefer it over CSV — OFX/QBO include FITID (unique
transaction ID) for exact dedup.

**Detection:** Use content-based detection, never filename-based. Look for
account-type tags in the OFX body:
- `<BANKACCTFROM>` = current/checking account (raw OFX)
- `<CCACCTFROM>` = credit card (OFX or QBO)
- `<CREDITCARDMSGSRSV1>` = QBO/QuickBooks format variant (header v.200+, single-line XML)

**Parsing:** Extract `<STMTTRN>` blocks with regex (`re.DOTALL`), pull
`TRNTYPE`, `DTPOSTED`, `TRNAMT`, `FITID`, `NAME`, `MEMO`. Convert
`DTPOSTED` (YYYYMMDDHHMMSS) to YYYY-MM-DD. After `</BANKTRANLIST>`,
extract `<LEDGERBAL>` — this is both a validation figure AND a balance
**anchor for backward-wind** (see `references/export-format-patterns.md`
for the full method). For credit cards, forward-accumulation from £0
is simpler than backward-wind (see references §Credit Card Shortcut).

## Git Branching and SQLite DB Recovery

When feature branches create or modify the golden-source SQLite database,
merging them back into master can clobber master's `finance.db` — especially
if a branch runs `init_schema.py` to rebuild the DB from scratch and only
creates a subset of tables (e.g. 4 tables instead of 19). Master's DB shrinks
from 4MB to 150KB silently on merge.

**Worktrees as recovery:** Git worktrees hold independent copies of tracked
files including SQLite DBs. If a branch worktree still has the real DB:

```bash
cp .worktrees/<worktree-name>/finance.db finance.db
git add finance.db && git commit -m "fix: restore finance.db from worktree"
```

**Merge-blocking untracked files:** When a file exists untracked on master
but is committed in the incoming branch, `git merge` aborts with "would be
overwritten by merge." If the file is the same content (verified via
`git show <branch>:<file>`), move it aside, merge, then restore:

```bash
mv <file> <file>.tmp && git merge <branch> && mv <file>.tmp <file>
```

**WAL/journal cleanup:** SQLite `*.db-shm` and `*.db-wal` files appear
when the DB is in WAL mode and should be gitignored. Add to `.gitignore`:

```
*.db-shm
*.db-wal
```

## Common Pitfalls

- **Don't use sync.py for data normalization** — sign conventions, column
  mapping, format detection, and data cleaning must happen in the pipeline's
  import step. If sync.py grows per-bank mapping functions (like `_map_barclays`,
  `_map_amex_gold`), normalization has leaked downstream. The fix is to move
  that logic into the pipeline's parsers and have them write canonical tables.
  After the fix, sync.py should be a thin incremental COPY from canonical tables
  into the app DB — no per-source knowledge, no sign flipping, no column merging.
  **Diagnosis:** if sync.py exceeds ~150 lines, check whether it's doing
  normalization that should be upstream.
- **When switching from old sync to thin sync, clear the app DB first.**
  The old sync populated `transactions` with `id = uuid4().hex[:16]` (random).
  The new thin sync uses `id = source_id` (SHA-256 hash of canonical row).
  These keys never collide, so re-running sync against a DB that has old rows
  produces **duplicates** — 11k old rows + 11k new rows = 22k total, with
  different PKs for the same transaction. Fix:
  ```bash
  sqlite3 app.db "DELETE FROM transactions; DELETE FROM investment_trades;
  DELETE FROM balance_sheet; DELETE FROM _sync_log; VACUUM;"
  ```
  Then run sync fresh. The `_sync_log` reset is critical — without it, the
  watermark check skips rows inserted by the old sync that share the same
  date range.
- **Cross-format description canonicalization is mandatory** — When the same transactions appear in multiple formats (e.g., Barclays CSV + OFX), their description fields come from entirely different source columns: CSV `Memo` vs OFX `NAME` + `MEMO`. The dedup key `(date, amount, description_lower)` will FAIL to match equivalent rows because `memo_text != name_tag`. **Fix:** Before computing the dedup key, canonicalize all sources into a single `Description` field. For CSV Memo: split on tab (`\\t`), strip whitespace, join parts with space, then strip trailing date patterns like `08 JAN BCC` using regex `r'\\s*\\d{1,2}\\s+[A-Z][a-z]{2}\\s+\\w+'`. This matches how OFX combines NAME+MEMO. **Verify:** After cleaning, count expected duplicates — if CSV has 3 rows for a date range and OFX also covers that range with the same transactions, dedup should reduce to exactly 3 rows total.
- **Don't assume amount sign convention is consistent across sources** — Lloyds stores debits as positive values in a `debit_amount` column, Amex stores debits as positive in a single `amount` column, Barclays stores debits as negative in `amount`. Each source needs its own sign mapping. Check a known low-value purchase (coffee, transport) to verify the direction before committing.
- **Worse: a single source can flip its sign convention partway through** — Amex UK changed their CSV export format at the 2022-01-01 boundary. Pre-2022 exports used the standard convention (negative = spend, positive = payment). Post-2022 exports inverted the signs (positive = spend, negative = payment). **Root cause:** the data source changed — pre-2022 data came from MoneyHub (third-party aggregator), post-2022 from direct Amex CSV downloads. The import pipeline must detect and normalise this. Detection: inspect the first few rows — if the oldest transaction has negative amount for a known purchase and the newest has positive for the same kind of purchase, you have a sign flip. Fix: normalise during import by checking the date boundary (e.g. negate `WHERE date >= '2022-01-01'`) or by detecting the sign of the first non-payment row and normalising everything to match QBO convention (negative = spend). Verify by backward-winding from a QBO `<LEDGERBAL>` anchor and checking the running balance converges to ~£0 at the account opening date.
- **AMEX PDF statements: "Direct Debit Amount" is NOT the full payment** — On AMEX monthly statements, the prominently displayed "Direct Debit Amount" is the **minimum repayment** (typically £25-£100), not the actual full-balance payment. The real payment appears in the transaction table as "PAYMENT RECEIVED - THANK YOU" (often marked CR). Do not extract the Direct Debit Amount figure as a transaction — it will produce tiny false payment entries. Also: on AMEX PDFs, "New Credits" in the Account Summary includes BOTH the full payment AND any CR refund entries — it is not just refunds.
- **Don't use truthiness checks for numeric amount fields** — `if debit:`, `if row[\"amount\"]:`, etc. are falsy for `0.00` which is a legitimate transaction value. Always use `if x is not None and str(x).strip():` for optional numeric fields, or `float(x) if x is not None else 0.0` for required ones. A real bug was caught during code review where `debit_amount=\"0.00\"` was treated as absent, routing it to the `credit_amount` branch instead.
- **Don't use filename-based detection** — users rename files, download names vary, archive prefixes break patterns. Detect from file content.
- **Don't use positional column lookup** — the first bank format change that reorders columns will silently corrupt data. Always map by header name.
- **Don't silently drop unknown columns** — store them in `extra` JSON so useful new data isn't lost.
- **Test dedup with real data** — synthetic tests won't catch edge cases like comma-formatted amounts (`4,976.01` vs `4976.01`) that produce different dedup keys. Verify against actual production rows.
- **Prefer OFX > CSV when available** — unique transaction IDs eliminate dedup ambiguity entirely.
- **QBO looks like XML but isn't** — Amex QBO files are single-line XML (not pretty-printed) with OFXHEADER:200 / VERSION:202, not the 102 header that raw OFX uses. Don't assume pretty-printing — extract with regex.
- **Credit cards don't need backward-wind** — forward-accumulate from £0. The `<LEDGERBAL>` is just a validation check, not an anchor requirement.
- **OFX/QBO `<LEDGERBAL>` can be preceded by `<AVAILBAL>`** — some banks include an available balance tag before the ledger balance. Always extract `<LEDGERBAL>` specifically, not the first `<BALAMT>` tag encountered.

## Reference

See `references/export-format-patterns.md` for specific bank header patterns and OFX structures encountered in the wild (includes backward-wind method, credit card shortcut, and Amex sign convention flip).

See `references/data-discrepancy-investigation.md` for a systematic workflow to reconcile row counts between a golden source and a target app database — includes per-account comparison, duplicate detection, year-breakdown, spot-checking, and amount sign investigation.

See `references/canonical-migration-recipe.md` for the 5-phase recipe to migrate from per-source raw tables to canonical tables — add DDL → one-shot migration script → rewrite imports → update downstream consumers → validate. Includes what NOT to change (computed tables, config-based data).
