---
name: brainstorming
description: "YOU MUST use this before any feature, component, or new work. Explores user intent, requirements, and design before any implementation. Blocks coding until design is approved."
version: 1.0.0
author: Adapted from obra/superpowers
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [brainstorming, design, planning, workflow, spec]
    related_skills: [writing-plans, subagent-driven-development, test-driven-development, requesting-code-review, finishing-a-development-branch]
---

# Brainstorming Skill

**Core mandate:** Do NOT write any code, create any files, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.

> **Anti-pattern — skipping design because it feels simple:** Simple projects are where unexamined assumptions cause the most wasted work. A todo list, a single utility, a config change, fixing tests — all of them.
>
> **Anti-pattern — "fix/do/implement X" is a workflow-start signal, not a gate-skip:** When the user says "fix the tests," "add X," or "implement Y," they are requesting the START of the gated workflow (spec → plan → execute), NOT granting permission to skip it. The user expects a spec and plan before any code change, even test-only fixes. A direct instruction like "fix these tests" is the trigger to load brainstorming and begin Step 1 exploration — not to open a file and start patching.
>
> **Anti-pattern — solutions that defeat the purpose:** When the user says "the app should figure out X so the user doesn't have to," and you propose options like "user opens app and points camera at X" or "user manually looks for X" — you've missed the point. The user just rejected the entire problem class your options assume. Stop, acknowledge the mistake, re-anchor on the core value: the app does the work, not the user. Don't iterate on bad options — go back to first principles.
>
> **Anti-pattern — test-fix shortcut:** "It's just updating test paths and URLs, no server logic changes." Test fixes carry assumptions about expected behavior. Example: a test asserting /import redirects to /login fails because /import now redirects to /sync. Fixing the test to expect /sync without confirming the redirect target is correct risks papering over a real bug. Always spec root causes first: enumerate every failure, confirm which side (server or test) is correct, then plan.

> **Anti-pattern — discussion-as-approval:** The user asking "what if I do X", "should I do X", "is X the right decision", or describing how they'd simplify something is a **DISCUSSION signal**, not an APPROVAL signal. Do not take any action — not file deletion, config changes, AGENTS.md updates, or any shell command — during the discussion phase. Wait for an explicit instruction like "go ahead", "do it", "yes please", or "make it so". A user pondering trade-offs out loud is NOT permission to start executing. When in doubt, talk more, act less. If you're drafting a tool call while the user is still thinking, you're moving too fast.

## Workflow Checklist

Complete these tasks **in order**. Do not skip steps.

### Step 1: Explore Project Context

Check the current project state — files, docs, recent commits. **Verify workspace isolation before designing anything.** If the user's conventions require worktrees for feature development (e.g., pfin uses `.worktrees/`), confirm you're in a proper isolated workspace first. Discovering mid-design that you're working in the main repo checkout wastes all subsequent effort and risks polluting the parent branch.

**If the project involves data files (CSVs, logs, exported data):** inspect samples of the actual data, not just the docs or directory tree. Don't write placeholder schemas or say "to be determined" — look at the real column headers, value ranges, and row counts. Users will call you out for guessing instead of reading the source data.

**Trust direct inspection over documentation.** AGENTS.md, READMEs, and package descriptions may be stale. If a doc says a package is "empty" but `ls` shows files, believe `ls`. If a doc says a route is at `/old-path` but the server redirects to `/new-path`, believe the server. Documentation is a starting point, not the final word — verify claims with direct observation before repeating them.

**If the project involves UI/frontend:** inspect `base.html` (or equivalent layout template) for which framework assets are actually loaded — not just which stylesheets are linked. CSS-only imports do NOT enable interactive components (Bootstrap dropdowns, modals, tooltips all require their JS bundle). See `references/frontend-framework-dependencies.md` for the full verification checklist.

### Step 2: Offer Visual Companion (if needed)

If the topic involves visual questions (layout, UI, diagrams), offer to fire up a visual companion tool (p5.js, Excalidraw, etc.) in its own message — do not combine with other content.

### Step 3: Ask Clarifying Questions

Ask questions **one at a time**. Only one question per message. Prefer multiple choice when possible. Focus on:
- Purpose — what problem are you solving?
- Constraints — budget, timeline, space, tools?
- Success criteria — what does "done" look like?

If the request describes multiple independent subsystems, flag this immediately and help decompose into sub-projects. Each sub-project gets its own design → plan → implementation cycle.

### Step 4: Propose 2-3 Approaches

Propose 2-3 different approaches with trade-offs. Lead with your recommendation and explain why.

### Step 5: Present Design in Sections

Scale each section to its complexity (a few sentences if straightforward, up to 200-300 words if nuanced). Ask for approval after each section. Cover:
- What is being built
- How it works
- Dependencies and materials
- What success looks like

### Step 6: Write Design Doc (Spec)

Save the approved design to `docs/spec-YYYY-MM-DD-<topic>.md` (flat in `docs/`, no subdirectories) and commit:

> **Anti-pattern — GitHub Issues as specs:** A GitHub issue is not a spec file. It lives outside the repo, can't be versioned alongside the code, and breaks the `docs/` convention. If an issue already describes the feature, extract it into a proper spec file, commit it, then close the issue with a reference to the spec. The spec is the source of truth — the issue is a tracker, not a design document.

```markdown
# <Title> — Specification

**Date:** YYYY-MM-DD
**Context:** What prompted this

## Scope
What is being built

## Requirements
- Exact details
- Dimensions, products, materials
- Constraints

## Decisions
Key choices made during brainstorming
```

### Step 7: Spec Self-Review

Before presenting to the user, quickly check:
1. **Placeholders** — any "TBD", "TODO", vague requirements? Fix them.
2. **Internal consistency** — do the requirements match what was discussed?
3. **Scope** — is it focused enough for a single plan? If not, decompose.
4. **Ambiguity** — any sentence with two possible interpretations? Pick one and make it explicit.
5. **Edge-case coverage** — for any section about "handling change" or "format variation" (schema evolution, error handling, fallback logic), don't stop at the first case. List every concrete scenario you can think of — labels renamed, positions shuffled, columns added (end vs middle), columns removed, complete format change. The user will spot the gaps; fix them before presenting.
6. **Preservation default** — when spec'ing a data pipeline, the default should be preserve-all-data unless the user explicitly says to discard. If you're tempted to write "ignore" or "discard" for unknown/extra data, pause and design a catch-all instead (e.g. an `extra` JSON column). Users notice when their data gets silently dropped.

### Step 8: User Reviews Written Spec

> "Spec written and committed. Please review it and let me know if you want to make any changes before we write the implementation plan."

**When to require file review:**
- Spec was written offline (no live back-and-forth during brainstorming) → **always** require review
- Design was presented section-by-section and approved in conversation → the user effectively approved already; offer but don't block

**Trust signal — skip the review when user says "i trust you":**
When the user says "i trust you", "go ahead", "approved", or similar after a spec is presented, skip the formal review step and proceed directly to worktree → plan → implementation. The user has signaled they don't need to read the spec file — they trust the design. Don't ask them to review it again.

**When to skip:**
- User says "go ahead" or "approved" during the conversation
- User says "i trust you" — trust signal, proceed immediately
- The user explicitly says to skip the review

Wait for the user's response. If changes are requested, fix and re-present. Proceed only on explicit approval.

### Step 9: Transition to Implementation

Once the spec is approved, load the `writing-plans` skill to create the implementation plan. Do NOT invoke any other skill — not even tool calls that look like implementation.

**Critical gate:** Stay in spec mode until the spec is fully approved. Do NOT start discussing the plan, proposing task breakdowns, or estimating effort while still pinning down requirements. If the user says something that sounds like a plan detail, note it but keep the conversation focused on the spec. The user will explicitly prompt for the plan when they're ready.

> **Anti-pattern — spec-to-code shortcut:** A common failure mode is writing the spec, getting user approval, then starting implementation directly (creating files, writing code, running tests) without writing a plan first. This happens especially when you feel you understand the task well. The user enforces the full gate: spec → **plan** → execute. If they say "go ahead" after the spec, load `writing-plans` and write the plan — do not interpret "go ahead" as permission to skip to coding. The plan is the handoff document that makes implementation obvious. The user will tell you when they want you to proceed to execution.

> **Anti-pattern — user says "stop" or "wait":** A mid-implementation "stop" is the user catching you in a gate violation — you started coding before the spec or plan was approved. The correct response is: (1) immediately halt all tool calls, (2) acknowledge the skipped gate, (3) revert any premature changes if the user asks, (4) load brainstorming and start the full workflow from Step 1. Do NOT defend the premature work as "just a small fix" or "already applied — might as well keep it." The user's "stop" overrides any sunk cost.

## When NOT to Use This Skill

- The user explicitly says "skip the design, just do it"
- Trivial reversible tasks (rename a file, fix a typo)
- The user says "just research X" (use research-*.md instead)

## Reference: Worked Example

See `references/personal-finance-web-app-worked-example.md` for a complete walkthrough of this skill applied to a real project — including how questions unfolded, what the user corrected mid-design, and how the spec was structured.

## Reference: Chart Rendering Pitfalls

See `references/chart-rendering-pitfalls.md` for four post-launch chart bugs discovered during manual testing — Jinja conditions on JSON strings, Chart.js `defer` race conditions, aspect ratio stretching, and date-range gaps.  \n_This reference lives under the brainstorming skill because it documents debugging insights from the personal-finance web app use case._

## Reference: Dedup Key Design for Financial Data Imports

See `references/dedup-key-design-for-financial-data.md` for rules and patterns on designing dedup keys across financial import pipelines. Covers the common mistake of using `ABS(amount)`, the surjective key principle, per-account examples, and edge cases that break naive dedup (multi-fund charges, fund switches, orphan rows with empty descriptions).

## Reference: Data Pipeline Implementation Pitfalls

See `references/data-pipeline-implementation-pitfalls.md` for four bugs caught during implementation of an inbox-to-SQLite pipeline — dedup-key mismatch between seed and import paths (thousands-separator commas), SQL injection via CSV column headers in INSERT statements, file handle leaks in parser functions, and archive filename collisions on same-day runs. Each has a concrete fix and a general rule.\n_This reference lives under the brainstorming skill because these are design-adjacent bugs that the spec didn't catch — they only surfaced during execution._

## Reference: GitHub Issue as Proto-Spec

See `references/github-issue-as-proto-spec.md` for the pattern of converting a GitHub issue into a proper spec file when the issue already contains a clear feature description.

## Reference: Data Pipeline Schema Edge Cases

See `references/data-pipeline-schema-edge-cases.md` for three real corrections from a user during a data-pipeline spec review — writing schemas from real data instead of placeholders, enumerating all edge cases for format handling, and preserving unknown columns by default rather than discarding them.

## Reference: Financial Data Format Selection

See `references/financial-data-format-selection.md` for guidance on choosing between OFX and CSV for financial data imports, including OFX parsing patterns, the FITID dedup advantage, and the general pattern for extending a pipeline with new file formats.

## Reference: Golden-Source Sync Pipeline

See `references/golden-source-sync-pipeline-worked-example.md` for a worked example of designing a sync pipeline from a read-only golden-source database into an application database. Covers two-database architecture, per-account dedup, `_sync_log` incremental tracking, per-table column mapping normalisation, and source metadata preservation — distinct from the single-database inbox-to-SQLite pattern in `data-pipeline-schema-edge-cases.md`.

## Reference: Cross-Database Stable Identity

See `references/cross-database-stable-identity.md` for the deterministic content-based hash pattern that produces stable source_ids across database rebuilds. Covers why SQLite rowids and uuid4() are wrong for cross-DB identity, and the upsert-by-source_id pattern that preserves enrichment fields during re-sync.

## Reference: Stable Cross-Database Identifiers

See `references/stable-cross-database-identifiers.md` for guidance on designing deterministic source IDs that survive database rebuilds. Covers why SQLite rowids fail, why random UUIDs fail on re-import, the deterministic hash approach, and when source_ids are worth the complexity vs premature. Includes the user's constraint: systems should automate reconciliation, not rely on manual cleanup.

## Worked Examples

Two complete run-throughs of this workflow are available:

- **`references/personal-finance-web-app-worked-example.md`** — web app (FastAPI + HTMX): full pipeline from "brainstorm personal finance app" through 5 phases of execution, including FastAPI-specific gotchas discovered during implementation (TemplateResponse keyword args, TestClient vs httpx for lifespan, lazy SQLAlchemy engine patterns).

- **`references/data-pipeline-schema-edge-cases.md`** — data pipeline (inbox-to-SQLite): three concrete corrections from a user during spec review — writing schemas from real data, enumerating all format-change edge cases, and preserving unknown columns.

## Reference: Repo Merge Architectural Decision

See `references/repo-merge-architectural-decision.md` for the anti-pattern of recommending repo merges when coupling is accidental rather than structural. Before proposing to merge repos, determine whether the coupling is because one side didn't finish its job — if so, fix the pipeline, don't merge.

## Reference: Frontend Framework Dependencies

See `references/frontend-framework-dependencies.md` for the design-time checklist of verifying which CSS/JS framework assets are actually loaded (not just linked) in layout templates. Covers the CSS-only Bootstrap trap, CDN version mismatches, and deferred script ordering issues.

## Related Skills

This skill is **Step 1** of the pipeline. After the spec is approved, the sequence continues:

1. `brainstorming` ← you are here — produce the spec
2. `writing-plans` — turn approved spec into bite-sized implementation plan (in a worktree)
3. `subagent-driven-development` OR kanban dispatch — execute plan via subagents with 2-stage review, or route tasks to specialist profiles
4. `test-driven-development` — TDD during implementation
5. `requesting-code-review` — review before finishing
6. `finishing-a-development-branch` — verify tests, merge to master, clean up worktree

**Context:** The full pipeline, file conventions, and gated workflow rules are documented in the PARA root `AGENTS.md` under the "Gated Workflow: docs/" section. The Superpowers methodology comparison lives in `~/para/docs/research-2026-06-04-superpowers-comparison.md`.

## Doc File Conventions

All project docs live flat in `docs/` with date-prefixed filenames. No subdirectories.

| Doc Type | Pattern | Purpose |
|----------|---------|---------|
| Spec | `docs/spec-YYYY-MM-DD-<topic>.md` | Approved design from brainstorming |
| Plan | `docs/plan-YYYY-MM-DD-<topic>.md` | Implementation plan from writing-plans |
| Research | `docs/research-YYYY-MM-DD-<topic>.md` | Technical investigation or findings |
| Changelist | `docs/changelist-YYYY-MM-DD-<topic>.md` | Summary of what was built in a session — for handoff to future sessions |
| Bugs | `docs/bugs-YYYY-MM-DD-<topic>.md` | Bug reports found during testing — one doc per session's batch |

Bug doc template (user's preferred format over GitHub Issues):

```markdown
# Bug Report — <Summary>

**Date:** YYYY-MM-DD
**Found by:** Manual testing / automated testing

## Bug N — <Title>

**Severity:** Low / Medium / High
**Component:** <file path>
**Status:** Open / Fixed in <YYYY-MM-DD> / Won't fix

**Root Cause:** <what causes it>

**Symptoms:** <what the user sees>

**Fix:** <what was changed to fix it> (omit if not yet fixed)
```

After fixing a bug, update the entry's status line from `Open` to `Fixed in <date>` and append the fix details under **Fix:**.

If the user asks how to track bugs, propose this flat-file approach as an option alongside GitHub Issues (`github-issues` skill) — the user in this project prefers flat-file for simplicity and colocation with specs/plans.
