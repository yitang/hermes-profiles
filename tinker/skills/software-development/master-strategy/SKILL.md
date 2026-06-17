---
name: master-strategy
description: "Execute a documented master plan against an existing codebase — audit the plan, find deviations between design and reality, then implement phase-by-phase with verification."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, implementation, audit, refactoring, data-pipeline, strategy-execution]
    related_skills: [systematic-debugging, plan, test-driven-development]
---

# Master Strategy Implementation

Execute a documented master plan against an existing codebase — audit the plan, find deviations between design and reality, then implement phase-by-phase with verification at each step.

## When to use

- A `docs/plan-*.md` or equivalent strategy document exists for a project refactor, pipeline redesign, or migration
- The user says "implement X master plan" or "get the current state aligned with the plan"
- You need to bridge the gap between documented architecture and actual codebase reality

## Steps (numbered, do in order)

### 0. Read the plan + scan the repo
1. Find and read the master strategy document (`docs/plan-*.md`, similar paths).
2. Do a `find` or directory listing to understand the real current state: what files/dirs exist, what's missing, what's extra.
3. Note mismatches immediately — these are your implementation gaps.

### 1. Identify header collisions and routing bugs
Financial CSV import pipelines almost always break on header collision: two different accounts produce identical column headers (e.g., Lloyds CSV vs HSBC Credit Card CSV both have `Date,Description,Amount,balance`). **Header-based detection alone is never sufficient.**

- Check if any parsers share the same CSV signature
- If so, filename-based routing MUST be added as the primary dispatcher, with header matching as fallback
- Verify by simulating detection on sample files from each account before proceeding

### 2. Fix schema first
Before touching import logic:
1. Ensure `init_schema.py` (or equivalent) creates ALL tables referenced by any parser, including newly supported accounts
2. Update aggregate views (`v_combined`, etc.) to include all new tables
3. Verify with a dry-run DB creation

### 3. Fix routing in import/parsing layer
Add filename-based detection at the TOP of `detect_account()` (or equivalent):
1. Extract account type from known filename patterns FIRST
2. Fall back to header matching only for unknown/unmatched files
3. Register any new parsers in the PARSERS dict, TABLE_NAMES mapping, and COLUMN_WHITELIST

### 4. Clean historical data before rebuild
- Run `clean.py` (or equivalent dedup/normalization script) on raw historical data
- Verify output: correct number of cleaned CSVs per account, audit trail generated, duplicates logged
- Copy clean outputs to the inbox for import stage

### 5. Rebuild database from scratch
1. Remove old DB file
2. Create fresh schema (run init_schema.py)
3. Import all clean CSVs via `import.py`
4. Verify: check row counts per table, confirm no misrouting, validate latest dates match plan expectations

### 6. Update documentation
- Update README.org or equivalent with current row counts and latest dates
- Note any new accounts, formats, or supported banks added during implementation
- Run verification queries to confirm data integrity

## When to deviate from the plan (acceptable deviations)

A plan says "unchanged" but practical constraints require modification — this is normal and acceptable when:

1. **Header collision breaks routing**: Two different account CSVs produce identical column headers (`Date,Description,Amount,balance`). Header-only detection misroutes data. Adding filename-based routing to the import router is a justified deviation from "keep import.py unchanged."
2. **Missing init_schema.py**: If the original codebase has no dedicated schema file, CREATE one rather than baking SQL into import scripts. This keeps schema manageable across multiple new accounts.
3. **Balance computation on CSV-only accounts**: `compute_balance()` falls back to zeros when no OFX LEDGERBAL anchor exists. CSV-only accounts (e.g., Amex) will show `balance=0` in cleaned output — this is a data-availability limitation, not a bug. Accounts that only have CSV exports cannot get real running balances without OFX anchor data.

**Not acceptable**: Deviating from plan without documenting WHY the deviation was necessary. Always note what the plan said vs what you did and why.

## Pitfalls
- **Missing tables in schema**: Plan often assumes tables exist that aren't in init_schema.py — always verify schema completeness before import
- **Overlapping date ranges**: Historical exports from different sources will share dates; dedup is mandatory, not optional
- **Archive directories**: Old `archive/` folders may need migration into canonical locations (`data/raw/`) — don't skip this step
- **Audit trail artifacts**: Clean scripts produce empty manifests from warm-up runs that look like they ran but didn't process data — always verify output file sizes and row counts
- **Plan assumptions vs reality**: Master plans frequently assume header uniqueness or sufficient parser coverage. The first pass is always finding what the plan missed, then fixing it
- **init_schema.py may not exist**: Original codebases rarely have a standalone schema initialization script. If missing, create `init_schema.py` with full CREATE TABLE statements and all aggregate views — don't just add new tables into existing inline SQL strings

### Pitfalls: Subagent-written implementations (plan-vs-reality drift)
When auditing an implementation produced by another session or subagent, check for these specific categories of drift:

- **Key name drift**: Subagents frequently rename keys without updating all consumers. The plan may define `start_date`/`end_date` in config while the parser reads `start`/`end`. Always grep the codebase for every key referenced in the plan — a mismatch means one of the files is stale and the pipeline will silently use wrong data or crash at runtime.

- **Loop break-after-yield (off-by-one)**: In amortization, iteration, or any generator that yields before checking a termination condition, the loop may emit one extra row past the specified boundary. Pattern to detect:
  ```python
  yield ...               # always runs first
  if condition: break     # too late — already emitted
  ```
  Correct order: check BEFORE yield. Verify by comparing last-emitted row's key against the plan's stated end boundary.

- **Cross-validation gap (numbers don't add up)**: Plans often include a numeric cross-check (e.g., "NatWest ending balance should match Barclays starting loan within £5"). Subagents implement the code and call it "done" without actually running the cross-validation query. Always re-run the specific numerical checks the plan lists — the code may work but produce wrong numbers due to subtle logic errors. A >1% deviation from expected values is a red flag, not rounding noise.

- **Name string mismatch**: The DB contains rows with names that differ from what the plan calls them ("NatWest" vs "NatWest Mortgage"). This breaks all downstream queries referencing the canonical name. Verify `SELECT DISTINCT name FROM table` matches plan expectations exactly.

## Verification checklist (run at end)
- [ ] All accounts from plan have their own database table
- [ ] No cross-contamination: rows for one account only appear in its correct table
- [ ] Total row count matches or exceeds plan expectations (dedup should reduce but not eliminate)
- [ ] inbox/ is empty and ready for new drops
- [ ] Data files moved from archive/ to canonical locations per plan
- [ ] Documentation reflects actual current state (row counts, dates, supported formats)

## Audit: Did the plan get faithfully implemented?

Before declaring completion, run a **plan-vs-reality audit** — compare every step of the original plan against what actually got done. Use the reference template at `references/plan-vs-reality-audit.md` for the structured format. Key things to verify:

- Schema completeness: all tables from plan exist + aggregate views include them
- init_schema.py may have been CREATED if missing (not just modified)
- No header collision remains between any pair of cleaned CSV outputs
- Balance computation only produced real values where OFX LEDGERBAL anchors existed (other accounts correctly show `balance=0`)

## Reference materials

- `references/plan-vs-reality-audit.md` — structured template for the plan-vs-reality audit phase
- `references/mortgage-amortization-pitfalls.md` — concrete examples of subagent drift patterns: key name mismatches, off-by-one loop breaks, unvalidated cross-checks in financial data pipelines
