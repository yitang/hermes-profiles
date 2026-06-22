---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 2.0.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [brainstorming, subagent-driven-development, test-driven-development, requesting-code-review, finishing-a-development-branch]
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development
- ANY non-trivial work (see Gated Workflow below)

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Gated Workflow (User Preference)

**This skill is used AFTER a spec has been approved via the `brainstorming` skill.** The user enforces a gated lifecycle for non-trivial work:

```
Brainstorming ──→ Spec ──→ Worktree ──→ Plan ──→ Execute (kanban/subagent) ──→ finishing-a-development-branch ──→ Merge + Cleanup
```

- Do NOT write a plan without an approved spec (the spec must come from the `brainstorming` skill's Step 8 approval gate).
- Do NOT implement directly from a spec without a plan.
- After execution completes, use the `finishing-a-development-branch` skill to present structured merge/PR/keep/discard options and handle worktree cleanup.
- Trivial tasks (one-step actions, obvious fixes) skip the gate.

**What counts as non-trivial?** Anything involving purchasing decisions, multi-step dependencies, >15 minutes of execution, or decisions that would be painful to undo.

### Step 2: Prepare Feature Branch via Worktree (before planning)

For any feature with 2+ kanban tasks, create a **feature branch inside a git worktree** — never on master. This keeps the stable baseline isolated and ensures the plan + code diff live together in one PR.

```bash
# From master (main repo directory, NOT the worktree)
cd /path/to/main-repo
git checkout master && git pull origin master  # ensure clean baseline
git checkout -b feat/<short-description>       # create feature branch here

# Now create the worktree — shares storage with master (cheap), isolated working dir
git worktree add /path/to/feature-workspace feat/<short-description>

# Plan and all implementation commits go into the worktree directory
cd /path/to/feature-workspace
```

**Key rules:**
- **Plan.md lives in the worktree/feature branch, NOT on master.** Planning is iterative — if you discover a dedup key change or balance sheet tweak while reviewing CSV data, those mutations stay local. Master only gets finished features via squash merge.
- **Anti-pattern — writing the plan on master first:** If you write the plan (or spec) on master before creating the worktree, you create a recovery mess: stash dirty changes, create branch, create worktree, checkout master, pop stash, copy files into worktree, patch the plan header. The worktree must exist before plan.md is written. Always: `git checkout -b feat/... && git worktree add .worktrees/...` FIRST, then `cd` into the worktree and write the plan there.
- **Main repo dir stays on master** — stable baseline for other work. Workers operate inside the worktree.
- **One branch = one PR.** For multi-task epics, don't create per-task branches. All workers commit to the same feature branch inside the worktree. When everything's green: `git push origin HEAD` → `gh pr create`.
- **Worktrees share storage** — no duplication of git objects. Just separate working directories on different branches.

**Branch naming:** `feat/<short-description>` for features, `fix/<short-description>` for bug fixes, `docs/<short-description>` for doc-only work. Lowercase, hyphens, minimal words.

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

**Scope-creep trap — a single task that rewrites an existing module is too big:**
If a task says "rewrite the sync loop to support X" or "add 5 new functions and modify 3 existing ones", it needs splitting. A task that fundamentally restructures an existing module inevitably produces debugging overhead (50+ turns, context compression, timeout risk). Split into: (a) add helper functions, (b) modify main function, (c) update tests. Each should be its own kanban task. Estimated times should reflect actual complexity — if a task touches 3+ existing functions, double the estimate.

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> **Gate requirement:** This plan MUST have followed from an approved spec (`docs/spec-YYYY-MM-DD-<topic>.md`).

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Spec reference:** `docs/spec-YYYY-MM-DD-<topic>.md` (link to the approved spec)

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

**Scope Boundary — REQUIRED per task:**
Every task MUST declare an explicit scope boundary. This defines what the worker may NOT touch. Without it, workers naturally drift into fixing everything they break downstream.

Good:
- `**Scope:** pfin-core/ only. Do not modify pfin-api/ or pfin-data/.`
- `**Scope:** This route file only. Do not touch other routes, schemas, or tests.`
- `**Scope:** Unit tests for this component only. Do not implement the feature.`
- `**Scope:** pfin-data/ parsers and tests only. Do not touch derived/ or rebuild.py.`

Bad (no boundary — worker will fix downstream breakage):
- ~~`Update sync.py to handle new schema`~~ (doesn't say what else is off-limits)
- ~~`Remove Account model and update all references`~~ (worker hunts references across repos)

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`
**Scope:** [which files/dirs may change, which must NOT change]

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min); use the **complexity sniff test** below
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

**Complexity sniff test — run before finalizing EACH task:**

A task is likely too big if it meets **any 2+** of these criteria:

1. **Multiple new functions** — the task creates 3+ distinct functions/classes
2. **Multiple files touched for different reasons** — modifying sync.py for the loop AND modifying 10 parser functions in the same task
3. **State machine change** — replacing a core algorithm (batch dedup → per-row matching) is one task; wiring it into every caller is separate tasks
4. **Test migration bundled** — rewriting existing tests to match a new API is a separate task from writing the API itself
5. **Two-phase debugging implied** — if the task requires testing on two branches (master + worktree), it's at least two tasks
6. **Estimated time > 15 min** — the plan's own time estimate is the simplest signal; if you wrote "~8 min" but the step count and code volume suggest 30+, split it

**How to split:** When a task triggers the sniff test, extract the self-contained sub-tasks:
- **Core logic** (new functions/helpers) → Task N
- **Wiring** (modify callers, add to mapping dicts, update imports) → Task N+1
- **Test migration** (rewrite old tests, add new test class) → Task N+2
- **Integration verification** (run on both branches, fix cross-branch issues) → Task N+3

This turns a 128-minute monster into 4 tasks of 20-30 min each — none hits the turn budget, and they can be dispatched with clear dependencies.

**Example: "P4: Upsert-by-source_id logic" should have been:**
- P4a: Add `_make_source_id` + `_compute_source_id` helpers + source_id to all mapping functions [deps: P3]
- P4b: Add `_load_existing_by_source_id` + `_update_transaction` + `_update_trade` helpers [deps: P4a]
- P4c: Rewrite main sync loop to use per-row source_id matching [deps: P4a, P4b]
- P4d: Add `_sync_balance_sheet` + TestSourceIdentity migration [deps: P4c]

### Step 6.5: Add Execution Order & Dependencies (before Task 1)

For plans with 4+ tasks, add this section after the header block and before Task 1. Two sub-elements — both go together in one heading:

**a. Dependency graph + table**

```markdown
## Execution Order & Dependencies

| Task | Depends On | Can Parallelize With | Time |
|------|------------|---------------------|------|
| **1. Schema** | — (none) | *anything* | ~3 min |
| **2. Import script** | — (self-contained) | Task 1, Task 3 | ~15 min |
| **3. Verify print loop** | Task 1 | — | ~1 min |
| **4. Compute holdings** | **Task 2** | — | ~8 min |
| **5. Balance sheet** | **Task 2, Task 4** | — | ~5 min |
| **6. Config update** | — (docs only) | any | ~2 min |
| **7. End-to-end validation** | **All of 1-6** | — | ~10 min |

**Critical path:** Task 1 → Task 4 → Task 5 → Task 7 (≈ 16 min)
```

**Time estimation rule:** Use the "code locations × 5 min" heuristic. Each distinct code location (new function, patched caller, test rewrite) adds ~5 min of agent time. If a task creates 3+ new functions plus modifies 5+ callers, it's not an 8-min task — it's 40+. When the estimate exceeds 15 min, the task MUST be split using the complexity sniff test in Step 6. Be pessimistic in estimates — a task that finishes 2 min early is fine; a task that takes 128 min and hits the agent turn budget is a botched plan.

**b. Inline dependency annotations on each task header** — lets both human and machine readers see dependencies at a glance:

```markdown
## Task 1: Add WP schema to init_schema.py [deps: none | parallel: yes]

## Task 4: Update compute_holdings.py for WP holdings [deps: Task 2 | parallel: no]

## Task 5: Update build_balance_sheet.py [deps: Task 2 (schema), Task 4 (holds) | parallel: no]
```

Format: `[deps: <list of prerequisite task numbers, or 'none'> | parallel: yes|no]`

### Step 6.6: Add Kanban Mapping (at the END of the plan)

For plans with kanban-eligible tasks, add this section AFTER everything else — after the Summary and total effort estimate, right before the final `---` or EOF. This enables autonomous kanban workers to create linked tickets without guessing parent arrays or board routing.

```markdown
## Kanban Mapping

| Plan Task | Kanban ID | Parents | Board | Plan Est. |
|-----------|-----------|---------|-------|-----------|
| Epic: [Feature Name] | EPIC-001 | — | finance | — |
| 1. Schema | EPIC-02 | [EPIC-001] | finance | 5m |
| 2. Import script | EPIC-03 | [EPIC-001] | finance | 10m |
| 3. Verify print loop | EPIC-04 | [EPIC-001, EPIC-02] | finance | 2m |
| 4. Compute holdings | EPIC-05 | [EPIC-001, EPIC-03] | finance | 8m |
| ... etc for all tasks ... |
| N. End-to-end validation | EPIC-N | [EPIC-001, all above] | finance | 5m |

**The `Plan Est.` column is machine-readable and drives execution monitoring:**
- Use suffixes: `s` for seconds, `m` for minutes, `h` for hours (e.g., `30s`, `5m`, `2h`).
- Every non-epic task MUST have an estimate. If omitted, the orchestrator defaults to `--max-runtime 30m`.
- These estimates feed into the kanban orchestrator's `--max-runtime` setting (3× plan estimate) and time-overrun detection (see `kanban-orchestrator` Step 4.5).

**How a worker uses this:** Create the epic ticket first (status: backlog), then create all subtasks linked via `parents=[...]` (as shown above). Workers pick up any task whose parents are in done/not-in-progress. Critical path tasks should be prioritized first; independent tasks can be dispatched as parallel workers alongside them.
```

Kanban ID naming: `<EPIC-prefix>-NN` where NN is zero-padded sequence matching task order. Epic gets `-001`, Task 1 gets `-02`. Board: use the domain-appropriate kanban board name (e.g. `finance`, `tools`, `hobbies`).

### Step 6.7: Validate task granularity

**Before finalizing tasks, check if any are too broad.** A task is too broad when it would need to:

- Touch 3+ files with different concerns (e.g., add a function in src/, wire it in a loop, write tests in a separate file, fix a bug in a third file)
- Rewrite or significantly restructure existing logic
- Debug tool-specific gotchas (SQLAlchemy Session vs conn, hash mismatches, import issues) — these compound with every other concern

**Red flag example — split this:**
```markdown
### Task 4: Implement upsert logic
[Modifies sync.py, test_sync.py, debug SQLAlchemy, write 5 functions]
```
**Better:**
```markdown
### Task 4a: Add upsert helper functions
[Adds _make_source_id, _update_transaction, etc. to sync.py only]
### Task 4b: Wire upsert into sync loop
[Rewrites the existing sync loop in sync.py to call the new helpers]
### Task 4c: Test and debug
[Fixes bugs, updates tests in test_sync.py, runs them green]
```

**Why it matters:** A single over-scoped task that hits bugs, tool edge cases, or context-compression limits can take 60-70 minutes and crash once before completing. Splitting keeps each turn focused, makes failures cheap, and parallelizes across profiles.

### Step 6.8: Add Workspace Header (if inside a worktree)

If the plan is being written inside a git worktree, add a workspace header at the **very top** of the plan file so kanban orchestrators can route workers to the correct checkout:

```markdown
Workspace: <absolute-path-to-worktree> (branch: feature/<name>)
Git root: <absolute-path-to-git-root>
Kanban board: finance
Epic: <EPIC-PREFIX>
Plan created: YYYY-MM-DD
```

**How to get the path:** Run `pwd` from inside the worktree, or `git worktree list` to find the absolute path. Copy it exactly — no `~/` shortcuts, no relative paths. The kanban dispatcher needs an absolute path for `workspace_kind`.

**Reference:** The full header convention and kanban-worker integration is documented in `kanban-orchestrator/references/plan-header-convention.md` and `kanban-orchestrator/references/kanban-worktrees.md`.

**Why:** Without this header, kanban workers default to `scratch` workspace and their commits are garbage-collected after completion. The header is how any orchestrator (or future session) knows where to dispatch work.

**When NOT needed:** If operating on master (no worktree), omit the header. Workers default to scratch, which is fine for read-only tasks.

### Step 6.9: Reference the Completion Skill

After execution, the work should be completed via the `finishing-a-development-branch` skill:
- It verifies tests independently (doesn't trust worker summaries)
- Detects worktree vs normal repo, presents exactly 4 options
- Handles merge, worktree cleanup, and branch deletion
- This is the canonical **Step 6** of the full pipeline: `brainstorming → spec → worktree → plan → execute → finishing-a-development-branch → merge + cleanup`

### Pitfall: Plan Written on Master Instead of Worktree

**Symptom:** You wrote `docs/plan-*.md` and it's sitting in the main repo's working directory, not in a worktree. `git status` on master shows untracked plan/spec files. The user asks "did you use a worktree?"

**Root cause:** The plan was written from the main repo checkout (on master) instead of from inside a freshly-created worktree. This happens when you jump to `write_file` without first running `git worktree add`.

**Fix recipe — move the plan into a proper worktree:**
```bash
# 1. Stash any unstaged changes on master
cd /path/to/main-repo && git stash

# 2. Create the feature branch
git checkout -b feat/<name>

# 3. Pop stash onto the feature branch
git stash pop

# 4. Go back to master on main repo
git checkout master

# 5. Create the worktree pointing at the feature branch
git worktree add .worktrees/<name> feat/<name>

# 6. Now the plan lives in the worktree. Copy any remaining files from master:
cp docs/spec-*.md .worktrees/<name>/docs/
cp docs/plan-*.md .worktrees/<name>/docs/

# 7. Add the workspace header to the plan
```

**Prevention:** Before writing ANY plan, check: `git branch --show-current`. If it says `master`, STOP. Create the worktree first. The plan file MUST be written to the worktree path, not the main repo path.

**Exception — user-specified absolute path:** If the user gives an explicit absolute path for the plan file (e.g. `/home/user/project/docs/plan-*.md`), write there AND also copy the file into the worktree at the equivalent path, committing on the feature branch. The user's explicit path takes priority, but the worktree branch must also contain the plan for kanban dispatch to find it.

### Pitfall: Writing Plan Without Loading the Skill

**Symptom:** You wrote a plan at module-level granularity (one task per file) without TDD cycles, complete code, or dependency annotations. The user asks "did you use writing-plans?"

**Root cause:** You started planning without loading this skill, or loaded a different similarly-named skill (e.g. `plan` instead of `writing-plans`). The `plan` skill is a lighter generic version; `writing-plans` is the user's authoritative skill with TDD, worktree integration, and kanban mapping requirements.

**Fix:** Delete the inadequate plan. Load this skill (`skill_view("writing-plans")`). Rewrite the plan from scratch following every step. Do not salvage the old plan — bite-sized TDD tasks cannot be retrofitted onto module-level stubs.

### Step 7: Save the Plan

```bash
# Save plan flat in docs/ — date-prefixed, no subdirectories.
# NOTE: this should be run from inside the worktree (feature branch), NOT master.
git add docs/plan-YYYY-MM-DD-<topic>.md
git commit -m "docs: add implementation plan for [feature]"
```

**User convention:** ALL project documents (plans, specs, changelists) live flat in `docs/` with date prefixes — no subdirectories. Examples:
- `docs/plan-2026-06-04-led-lighting-wiring.md`
- `docs/spec-2026-06-03-rebuild-db-from-raw-source.md`
- `docs/changelist-2026-06-14-rebuild-db-from-raw_clean.md`

Do NOT put documents in the repo root — they always go in `docs/`.

## Reference: Plan to Kanban Integration

See `references/plan-to-kanban-integration.md` for how the plan's workspace header and Kanban Mapping table connect to kanban dispatch — including multi-repo dependency ordering and worktree path conventions. See also `kanban-orchestrator/references/plan-header-convention.md` for the workspace header format and execution monitoring via plan estimates.

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Adapting for Physical / DIY Projects

When the user's task is a physical build (woodworking, lighting, construction) rather than code, adapt the plan structure:

- **Tasks are physical steps** — cut, drill, solder, mount, route, order
- **Files become locations** — "Workshop: cutting station", "Kitchen: under-cabinet area"
- **Tests become verification** — "Check fitment before gluing", "Test continuity with multimeter"
- **TDD doesn't apply** — replace with Measure-Twice-Cut-Once: verify dimensions before irreversible steps
- **Commits become checkpoints** — "Complete zone 1 wiring", "All panels dry-fitted"
- **Include product references** — exact product names, prices, URLs, quantities

Example physical task:
```markdown
### Task 3: Solder Zone 1 LED Strip

**Objective:** Wire the warm-light zone strip to the driver via the RF controller.

**Prep:**
- [ ] Strip ends cut square with scissors
- [ ] 4-wire speaker cable stripped 8mm on each end
- [ ] Solder iron hot (350°C)

**Step 1: Tin strip pads and wire ends**

Apply flux, tin both contact pads on the strip and both stripped wire ends.

**Step 2: Solder joint**

Hold wire to pad, apply iron for 2-3s until solder flows. Repeat for second connection. Inspect for bridges.

**Step 3: Verify continuity**

Multimeter on resistance mode: check strip end-to-pad at driver end. Expected: < 1Ω per conductor. No shorts between + and -.

**Step 4: Test zone**

Connect driver to mains momentarily. Strip should light at full brightness. If not, check polarity and solder joints.
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

### Using `:` prefix for non-plugin skills

Skills from your filesystem (`~/.hermes/skills/` or `external_dirs`) do NOT use the `prefix:name` notation. That's only for plugin-provided skills. Just use the bare name:

- **Right:** `skill_view("finishing-a-development-branch")` — finds it in external_dirs
- **Wrong:** `skill_view("superpowers:finishing-a-development-branch")` — fails because no plugin named "superpowers" provides this skill

The directory layout (`para/2_areas/agents/skills/superpowers/...`) is just filesystem organization — it does not create a `superpowers:` namespace. When in doubt, try the bare name first.

### Dirty Worktree After Setup

**Always verify** the worktree is clean before starting work: `git status --short`. A clean baseline (`nothing to commit`) prevents accidentally carrying over stale files or `.gitignore`-hidden assets (e.g., global gitignore hiding `*.pdf`). If you discover hidden files after planning starts, use `git add -f <path>` to force-add them — the worktree branch should contain all source-of-truth data.

### Pitfall: Under-Specced Plans for Model Execution

**Symptom:** You write a plan where Tasks 5-7 say "People page route + template" with a paragraph description but no actual code. The user says "rewrite" and asks you to double-check task complexities.

**Root cause:** Plans written for human implementers can rely on inference. Plans executed by a different AI model (or a subagent with no domain context) need complete copy-pasteable code for every file. The model can't infer Bootstrap classes, Jinja2 patterns, or the exact JS fetch/CRUD flow from a one-line description.

**Fix — the self-test:** After writing a plan, ask: "If I handed this to a junior dev who has never seen this project and told them 'type exactly what's here,' would they produce a working feature?" If any task says "similar pattern to X" or "same approach as Y" without the actual code, it fails. Every API route, every template, every test must be written out in full.

**This is especially critical when:**
- The plan will be executed by a SUBAGENT (fresh context, no prior exposure to project conventions)
- The plan will be executed by a DIFFERENT MODEL (model comparison, kanban dispatch across profiles)
- The plan touches MULTIPLE PAGES with similar-but-not-identical templates

**Example of under-specced:**
```markdown
### Task 5: People page route + template [deps: Task 3 | parallel: yes]
**Objective:** Replace stub /people page with card-based list showing balances.
```
**Correct — full code provided:**
```markdown
### Task 5: People page route + template [deps: Task 3 | parallel: yes]
**Step 1: Update route** (full code)
**Step 2: Rewrite template** (complete HTML/JS, ~100 lines)
```

### Pitfall: New Page Template Missing JS Libraries

**Symptom:** A new page with a Chart.js chart renders the canvas but no chart appears. The JS console shows `Chart is not defined`. The data is correct in the HTML source.

**Root cause:** Jinja2 templates in this project extend `base.html`. The dashboard page loads Chart.js via an inline `<script>` tag inside its own template, not in `base.html`. When you write a new page template (e.g. `trades.html`) that also needs Chart.js, you must add it explicitly.

**Fix — use the `extra_head` block (not `head_extra`):**
```html
{% extends "base.html" %}
{% block extra_head %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
{% endblock %}
```

**Verification before marking template task complete:**
```bash
curl -s http://127.0.0.1:8125/new-page | grep -c 'chart.js'
# Expected: 1 (the CDN script tag is present)
```

**Prevention:** When a plan task creates or rewrites a template that uses Chart.js, explicitly include the `extra_head` block with the CDN script in the plan's code example. Do not assume base.html includes it.

## Kanban Data Flow (Important)

When plans feed into kanban workers, understand the actual data path:

1. **The orchestrator reads the plan** — full detail extraction happens here
2. **Task body = summary line + target path only** — workers never see plan.md or spec.md on disk
3. **Plan reference (spec link) is human traceability only** — it documents design → plan provenance for debugging, not machine input

So when writing plans: put the full detail in the plan itself (exact code, file paths, steps). The kanban mapping table enables workers to create linked tickets with correct parent arrays. The spec reference is metadata, not a runtime dependency. If a task body gets too long during creation, use `kanban_comment` to add detail after the task exists — this avoids write-protection safety gates on large bodies.

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
Workspace header at top of plan
```

**A good plan makes implementation obvious.**

**Plan quality dominates model choice.** When a plan has complete copy-pasteable code and exact file paths for every task, different AI models produce near-identical output — the plan, not the model, determines quality. Vague plans produce wildly divergent implementations. The leverage point is the plan. See `subagent-driven-development` skill → `references/model-comparison-parallel-worktrees.md` for methodology and benchmark data.

## Reference: Complete Pipeline Flow

See `references/complete-pipeline-flow.md` for the full gated workflow: brainstorming → spec → worktree → plan (with header) → kanban dispatch → execute → finishing-a-development-branch → merge + cleanup.