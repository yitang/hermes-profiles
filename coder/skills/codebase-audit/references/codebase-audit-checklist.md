# Codebase Audit Checklist

Step-by-step checklist for efficiently conducting a codebase architecture audit. Takes about 15-20 minutes per project for the read phase, plus 10 minutes to write findings.

## Pre-Flight (2 minutes)

- [ ] Confirm the user wants an architectural review, not a deep dive on one specific component
- [ ] Note the user's scale context: single-user? team of N? deployed to production? cloud-native or local-only?
- [ ] Identify 3-5 entry-point files to read first (main.py, import.py, config.py, schema definitions)

## Phase 1 — Read (8 minutes)

Read each file below, noting what patterns exist and which standard concepts are missing.

- [ ] **Entry point / main script** — How does the system start? What's the top-level flow?
- [ ] **Data import / ingestion logic** — How does external data get in? Is there format detection? Dedup? Validation?
- [ ] **Persistence layer** — Database schema, queries, ORMs. Are there UNION views or separate materialised tables for cross-source queries?
- [ ] **Configuration** — Hardcoded values vs config files. Is schema/config separate from logic?
- [ ] **Supporting scripts** — Any compute, transform, report, or maintenance scripts? How do they relate to the main pipeline?

## Phase 2 — Map Patterns (3 minutes)

For each enterprise concept below, mark what exists in the codebase:

| Pattern | Present? | Where? | Notes |
|---|---|---|---|
| Idempotency (re-runnable imports) | | | e.g., INSERT OR IGNORE, dedup keys |
| Data validation / quality checks | | | e.g., parse-time filtering, post-import scripts |
| Reconciliation (computed vs authoritative) | | | e.g., balance verification |
| Schema versioning / format detection | | | e.g., header-based routing, version markers |
| Dead letter handling (failed ops isolated) | | | e.g., files left in inbox on error |
| Canonical representation | | | e.g., unified view, standardised schema |
| Price/value refresh mechanism | | | e.g., external API lookup, stale vs current |
| Backup / archive of originals | | | e.g., raw file preservation, version history |

## Phase 3 — Identify Gaps (2 minutes)

For each missing or weak pattern, write one sentence describing the risk:

- [ ] If idempotency is missing: "Re-importing a file will create duplicate transactions"
- [ ] If validation is missing: "Bad data from upstream silently enters the system with no alert"
- [ ] If reconciliation is missing: "There's no way to verify transaction totals match bank records without manual inspection"
- [ ] If format detection is missing: "A format change from the upstream will corrupt data silently"
- [ ] If canonical representation is missing: "Analytics queries must handle inconsistent column names across sources"

## Phase 4 — Prioritise Recommendations (3 minutes)

For each gap, assess effort and impact:

| Recommendation | Effort | Impact | Priority |
|---|---|---|---|
| Validation script | Low | High | P1 |
| Reconciliation check | Low | High | P1 |
| Canonical view | Medium | Medium | P2 |
| Format version marker | Low | Medium | P2 |
| Price refresh mechanism | Medium | Medium | P2 |

## Deliverable

Save findings to:
```
docs/research-YYYY-MM-DD-audit-<project-name>.md
```

Structure:
1. Overview (what was reviewed, what the system does)
2. Already solid (patterns present and working well)
3. Gaps identified (each with specific risk explanation)
4. Recommendations (prioritised, with code examples where feasible)
5. Architecture diagram showing current state + proposed additions
