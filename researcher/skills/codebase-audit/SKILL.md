---
name: codebase-audit
description: "Systematic review of an existing codebase to identify architectural patterns, gaps, and improvement opportunities. Use when the user asks to review their software design/architecture, evaluate their codebase quality, or get actionable engineering recommendations for their project."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, audit, review, patterns, improvement]
    related_skills: [code-documentation, consulting-analysis, iterative-research]
---

# Codebase Architecture Audit

Systematic review of an existing codebase to identify architectural patterns, gaps, and actionable improvements. Use when the user asks to review their software design/architecture, evaluate their codebase quality, or get actionable engineering recommendations.

## When to Use

- User asks "review my architecture", "how can I improve my data pipeline", "what's wrong with my codebase"
- User wants feedback on existing code before building something new
- User is evaluating whether their current approach has scaling/quality risks
- Explicit trigger: "audit my codebase", "review my design", "architecture review"

## Overview

The process runs in three phases:

1. **Read** — examine actual source files (NOT just structure or summaries)
2. **Map** — identify what architectural patterns already exist and which standard concepts are missing
3. **Recommend** — frame findings as "you already do X well" / "gap Y needs attention", prioritised by impact x effort

## Critical Rule: Ground Everything in Actual Code

**Never write generic advice without reading the codebase first.** If you recommend "add validation", it must be because you saw a specific parser that silently accepts bad rows. If you recommend "canonical tables", it must be because you observed scattered column names across similar tables. Every recommendation traces back to a concrete file and line.

## Workflow

### Phase 1: Read — Examine Actual Files

Read the core files of the codebase, not just directory listings. Focus on:

- **Main pipeline / processing logic** (e.g., `import.py`, `main.py`, entry points)
- **Data access / persistence layer** (e.g., database queries, ORM models, schemas/)
- **Schema or data structure definitions** (e.g., table DDLs, Pydantic models)
- **Supporting scripts** (e.g., build scripts, migration scripts, compute scripts)
- **Any documentation** (AGENTS.md, README, CLAUDE.md)

Read at least 3-5 key files to understand the actual architecture. Don't rely on `ls` or search results alone — read enough code to see how pieces connect.

### Phase 2: Map — Identify Patterns Present and Missing

Compare what exists against standard architectural concepts, **adapted to the user's scale**:

| Enterprise Concept | Single-User / Lightweight Equivalent | What to Look For |
|---|---|---|
| CDC (Change Data Capture) | File-inbox pattern + re-import backfill | Does the system handle incremental updates? |
| Idempotency | `INSERT OR IGNORE` / dedup keys | Can you safely re-run the same operation? |
| Schema Registry | Header-based detection + format versioning | Does the system detect when upstream data changes format? |
| Dead Letter Queue | Files left in inbox with error message | Are failed operations isolated and visible? |
| Data Quality Checks | Post-import validation script | Is there anything that catches bad data before it spreads? |
| Reconciliation | Comparing computed vs authoritative totals | Can you verify the system's internal consistency? |
| Canonical Table | Standardised view across scattered sources | Are all accounts/entities represented consistently? |
| Price/Value Refresh | Periodic lookup of current market data | Is valuation based on stale reference prices? |

**Identify gaps by asking:**
- Does the system silently accept garbage and never alert?
- Can you re-run the same operation safely (idempotent)?
- When upstream data changes format, do you get a clear signal or just silent degradation?
- Are there computed values that may have drifted from reality?

### Phase 3: Recommend — Prioritised Findings

Present findings in this order:

**Already solid -- don't touch:** What the user already does well. This confirms good instincts and saves wasted effort.

**Priority 1 -- Add (high impact, low effort):** Quick wins that address real gaps. Usually data validation, basic reconciliation, or simple sanity checks.

**Priority 2 -- Consider (medium impact, medium effort):** Structural improvements that pay off over time but need a bit of planning. Canonical views, periodic price lookups, format versioning.

**Priority 3 -- Nice-to-have:** Improvements worth noting but not urgent. Scalability patterns for when the codebase grows beyond its current scope.

For each recommendation:
- Explain WHY it matters (the specific risk or limitation in their current code)
- Show HOW to implement it (code example, script sketch, SQL view)
- Estimate effort (keep/modify existing file vs new file)

### Phase 4: Deliverables

Save the full analysis as a research document:
```
docs/research-YYYY-MM-DD-<topic>.md
```

If the audit reveals a reusable pattern that other projects would benefit from, write it as a template or reference under this skill.

## Pitfalls

- **Don't recommend enterprise tooling for single-user problems.** No Kafka, no Airflow, no dbt unless the user explicitly asks and has 20+ data sources. Adapt every concept to their actual scale.
- **Don't assume gaps without reading the code.** Saying "you should add validation" is useless if you haven't checked whether a validation script already exists in a different directory.
- **Don't dismiss what's working.** Users spend real effort on existing architecture -- acknowledge it before suggesting changes.
- **Don't recommend schema redesigns for SQLite when union views solve the problem.** Materialising canonical data into separate tables adds maintenance burden for no gain if a `CREATE OR REPLACE VIEW` does the job.
- **Don't ignore growing pain points that aren't yet critical.** Stale investment valuations, hard-to-scope parsers -- flag them as "Priority 2" so they're not forgotten until they become emergencies.

## Reference Files

- `references/etl-patterns-single-user.md` — Condensed guide to adapting enterprise ETL concepts (CDC, canonical tables, DLQs) for single-user applications running locally on SQLite or small databases.
- `references/codebase-audit-checklist.md` — Step-by-step checklist for conducting a codebase architecture audit efficiently.
