# pfin Project Conventions

Project-specific knowledge for developing the personal finance FastAPI app.

## Project Layout

```
~/dev/personal-finance/
├── pfin-core/       → Pydantic v2 models, SQLAlchemy ORM, CSV parsers, sync engine
├── pfin-api/        → FastAPI REST server + Jinja2/HTMX web dashboard
├── pfin-web/        → scaffold only (dead code, ignore)
├── finance.db       → golden-source SQLite DB (read by sync engine)
└── docs/            → specs, plans, bug reports
```

## Install & Run

```bash
pip install -e pfin-core/
pip install -e pfin-api/

# Start API server
pfin-api --host 0.0.0.0 --port 8125 --reload

# Run sync (finance.db → pfin.db)
pfin-sync [--source PATH] [--pfin-db PATH] [--dry-run] [--verbose]
```

DB file: `~/.pfn/pfin.db` (override with `PFIN_DB` env var).

## Tests

```bash
python3 -m pytest pfin-core/ -q      # 93 tests
python3 -m pytest pfin-api/tests/ -q  # 70 tests
# Total: 163 tests (all passing 2026-06-12)
```

In-memory SQLite (`StaticPool`). Never use file-based DB in tests.

## Auth Pattern

**Login uses `user_id`, not `username`.** Any `user_id` value auto-creates the account:

```
POST /login  form: user_id=<anything>
→ 302 redirect to /
→ Sets pfin_session cookie
```

No password required. In-memory only (sessions lost on restart).

To login via curl:
```bash
curl -s -c cookies.txt -X POST http://localhost:8125/login -d 'user_id=tangyi'
curl -s -b cookies.txt http://localhost:8125/
```

## Sync Engine

One-way import from `finance.db` (golden source) to `pfin.db` (app DB).
Dedup by `(account_id, date, amount, description)`.
Incremental via `_sync_log` table watermarks.

```bash
# Dry-run to see what would be imported
pfin-sync --dry-run --verbose

# Check sync log
sqlite3 ~/.pfn/pfin.db "SELECT * FROM _sync_log;"
```

Last sync: 2026-06-05. All accounts up to date.

## Key API Endpoints

| Endpoint | Notes |
|---|---|
| `GET /api/dashboard` | net worth, recent txns, top categories, monthly cashflow |
| `GET /api/dashboard/net-worth-history` | per-month balances, 160 months (2013-04 to 2026-07) |
| `GET /api/accounts` | 9 accounts (1 duplicate Amex Gold ghost at 1392aefa) |
| `GET /api/transactions` | 10,525+ transactions |
| `POST /api/import/parse-preview` | CSV upload, auto-detect parser |
| `POST /api/import/confirm` | bulk insert parsed rows |

## Known Issues

- **Net worth shows £0** — account `balance` field is static (not computed from transactions). Dashboard API computes it dynamically but the account model doesn't update.
- **Duplicate Amex Gold** — account `1392aefab2ff4208` has 0 transactions. Real data is in `d131d3cf2c9f45bc`.
- **Dead package** — `pfin-web/` is empty scaffold, no source code.

## Recent Commits (2026-06-12)

```
75e2a3e docs: sync spec + plan, bug reports, updated AGENTS.md + user manual
e899bb9 feat: net worth history endpoint, UI fixes, app startup polish
682d845 feat: Alpine.js sidebar toggle, import wizard fixes, toast system
a4a25e7 feat: one-way sync engine from finance.db to pfin.db
e6edaba feat: robust CSV import parsers — 7 bank formats, auto-detect
```
