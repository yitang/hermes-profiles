# Fixing Test Suites After Schema/Architecture Changes

Patterns for efficiently resolving test failures when production code changes (column renames, model removals, route updates) break existing tests.

## Decision: Direct vs Dispatch

**Do directly in orchestrator** — these need NO reasoning about existing code:
- Changing assertion values (`>= 2000` → `>= 1500`)
- Updating status codes (`== 404` → `in (405, 422)`)
- Deleting entire obsolete test classes or methods
- Renaming test functions to match new behavior

**Dispatch a subagent** — these require reading and understanding existing code:
- Fixing column name references across raw SQL + ORM constructors
- Adapting tests that depend on specific data shapes or relationships
- Rewriting integration tests that span multiple components

## Common Failure Categories After Schema Migration

### 1. Column renames
Pattern: `account_id` → `account`, `source_id` → `transaction_hash`, `created_at` → `imported_at`

Affects:
- Raw SQL INSERT/SELECT statements in test fixtures
- ORM constructor kwargs (`_Txn(created_at=...)` → `_Txn(imported_at=...)`)
- Any WHERE clauses referencing old column names

### 2. Model/table removals
Pattern: Account model removed; accounts now discovered via queries on other tables

Affects:
- Tests asserting CRUD endpoints return specific status codes (404/501 → 405 or 200)
- Tests creating fixture data via old ORM models (UNIQUE constraint violations if hash duplicates)
- Routes that no longer exist (POST to removed endpoints → 405)

### 3. Route behavior changes
Pattern: Web-only routes crash with TypeError on abstract models → HTTP 500 instead of expected 501/405

Affects:
- Tests expecting specific HTTP status codes from web form submissions
- Tests checking for "not implemented" stubs that now produce real (but wrong) behavior

### 4. Data threshold drift
Pattern: Vault data shape changes (yearly files only vs daily snapshots) reduces row counts

Affects:
- Row count assertions in parser tests
- Minimum thresholds in integration tests

### 5. Wrong fixture lookup paths
Pattern: Test looks for fixtures in `tests/inbox/` or `tests/data/raw/` when the project convention is `tests/fixtures/raw/` (or vice versa). Multiple tests in the same file can have this identical bug — they all silently skip, making it look like "only 5 skipped" when more are affected.

Symptom: `pytest.skip("fixtures not available")` appearing for test files that clearly should have fixtures present; `grep -rn "pytest.skip\|os.path.exists"` in the test file reveals hardcoded lookup paths different from other tests' base directory (`FIXTURE_DIR`).

Fix: Check what other tests in the same file use as base path, align lookup to that convention. Run individual skipped test with `-v --runxfail` or add `print()` before the skip condition to confirm it fires.

## Pre-Run Skip Check (orchestrator duty)
Before running `pytest -q` as step 5 of verification, first run `python3 -m pytest <suite> -v --tb=no | grep SKIPPED`. Skips are either:
- **Pre-existing fixture gaps** (fixtures never committed to git) — note and report but don't block
- **Wrong lookup paths** — fix as above, can turn skips into passes
- **New regressions** introduced by the changes — must investigate

Report skip count and which tests are skipped alongside the pass/fail summary. Always distinguish these from actual failures.

## Subagent Discovery Bonus

Subagents often self-discover secondary issues beyond the original scope:
- Redundant inserts causing UNIQUE constraint violations (two fixtures inserting same `transaction_hash`)
- Missing fixture files silently ignored by `.gitignore`
- Stale imports from old module paths
- Cross-test interference (fixtures created by one test polluting another)

**Always run the full suite after subagent changes**, not just the affected file — these secondary issues are the ones that actually break CI.

## Verification Checklist for Schema-Migration Test Fixes

1. Before: `pytest <affected_file> -v --tb=line` — capture exact failures
2. Apply fixes (direct patch or dispatch subagent)
3. After: `pytest <affected_file> -v --tb=no` — all tests in file should pass
4. Full API suite: `pytest pfin-api/tests/ -q --tb=no` — catch cross-file interference
5. Full cross-package: `pytest pfin-data/ pfin-core/pfin_core/ pfin-api/ -q --tb=no` — confirm no regressions elsewhere
6. Check that test count increased/decreased logically (deleted classes = fewer tests)
