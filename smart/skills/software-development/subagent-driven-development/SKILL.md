---
name: subagent-driven-development
description: "Execute plans via delegate_task subagents (two-stage review). Handles commit divergence, spillover, fixture silence, and pre-existing failure detection."
version: 1.3.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel, divergence-recovery]
    related_skills: [writing-plans, requesting-code-review, test-driven-development]
---

# Subagent-Driven Development

## Overview

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## When to Use

Use this skill when:
- You have an implementation plan (from writing-plans skill or user requirements)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

**vs. manual execution:**
- Fresh context per task (no confusion from accumulated state)
- Automated review process catches issues early
- Consistent quality checks across all tasks
- Subagents can ask questions before starting work

## The Process

### 1. Read and Parse Plan

Read the plan file. Extract ALL tasks with their full text and context upfront. Create a todo list:

```python
# Read the plan
read_file("docs/plans/feature-plan.md")

# Create todo list with all tasks
todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

**Key:** Read the plan ONCE. Extract everything. Don't make subagents read the plan file — provide the full task text directly in context.

### 2. Per-Task Workflow

For EACH task in the plan:

#### Step 1: Dispatch Implementer Subagent

Use `delegate_task` with complete context:

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

#### Step 2: Dispatch Spec Compliance Reviewer

After the implementer completes, verify against the original spec:

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?
    - [ ] TEST COVERAGE: Every new function/method has ≥2 tests (normal path + edge/error case)
    - [ ] Full test suite passes (`pytest tests/ -v`), not just the single file
    - [ ] No zero%-covered functions in newly created files

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

**If spec issues found:** Fix gaps, then re-run spec review. Continue only when spec-compliant.

#### Step 3: Dispatch Code Quality Reviewer

After spec compliance passes:

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] TEST DEPTH: Each test checks real behavior, not mock structure; edge cases covered
    - [ ] No zero%-covered functions in new code (check with coverage.py if available)
    - [ ] Tests are deterministic — no time-based logic or external state dependencies
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding, e.g. uncovered functions, false positives in tests]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

**If quality issues found:** Fix issues, re-review. Continue only when approved.

#### Step 4: Mark Complete

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

### 3. Final Review

After ALL tasks are complete, dispatch a final integration reviewer:

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

### 4. Verify and Commit

```bash
# Pre-flight: check for skipped tests before running full suite
python3 -m pytest <suite> -v --tb=no | grep SKIPPED

# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

**Skip check**: Before the full `pytest -q`, grep for `SKIPPED`. If any appear, report them alongside pass/fail. Skips are either pre-existing fixture gaps, wrong lookup paths (fixable by aligning to `FIXTURE_DIR`), or new regressions. This prevents mistaking silent skips for "all tests passed."

**Pre-existing failure detection**: After the full test suite runs, if there are failures, verify each one:
1. Is it in a file that predates this feature branch (likely pre-existing)?
2. Does `git log --oneline HEAD..origin/master | head -5` show any changes to that file? If no, it's pre-existing.
3. Only treat as new regression if the file was modified by your subagent commits.

## Task Granularity

**Each task = 2-5 minutes of focused work.**

**Too big:**
- "Implement user authentication system"

**Right size:**
- "Create User model with email and password fields"
- "Add password hashing function"
- "Create login endpoint"
- "Add JWT token generation"
- "Create registration endpoint"

## DELEGATION IS MANDATORY (not advisory)

**When this skill is loaded, `delegate_task` is your ONLY implementation mechanism for plan tasks.** You MUST dispatch subagents — you may NOT write files, run terminal commands, or execute code for plan tasks in your own context. The ONLY exception is the mechanical scaffolding listed under "When to skip subagent dispatch" (directory creation, boilerplate files, pre-scripted moves).

**Why this is a hard rule:** A kanban worker loaded with SDD that executes a 10-task plan inline accumulates every file read, every diff, and every test run in a single context window. The result is a catastrophic compaction spiral — 8+ compactions in 20 minutes, each one eating ~20s of wall-clock time, until the process stalls permanently on `futex_wait_queue_` (syscall 202). The worktree sits dirty with uncommitted files, the task times out, and zero progress is saved. A session using `delegate_task` for the same plan finishes in 37 minutes with 6 commits and clean state.

**Self-check:** If you find yourself calling `write_file` or `terminal` to create implementation files that a plan task specifies, STOP. You are violating SDD. Read the task spec, dispatch it via `delegate_task`, and move on.

**Beware the copy-pasteable plan:** Plans that contain ready-to-use code blocks (full function bodies, complete templates) are the strongest temptation to abandon SDD. The reasoning sounds plausible: "the code is right there, I can write these files faster than dispatching subagents." This is a trap. The context cost of inline file writes (diffs, syntax checks, test runs) accumulates silently until compaction stalls the process. Subagent dispatch keeps your orchestrator context clean. **The shorter the path from plan to copy-paste, the STRONGER the need to dispatch — not weaker.**

## Red Flags — Never Do These

- **Implement plan tasks inline instead of dispatching subagents** — this IS the #1 cause of fatal context compaction stalls
- Start implementation without a plan
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Skip scene-setting context (subagent needs to understand where the task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance
- Skip review loops (reviewer found issues → implementer fixes → review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues
- **Trust a subagent's committed claim when it created new fixture files** — .gitignore may have silently blocked the add. Verify with git ls-files or instruct git add -f.
- **Mark a task complete when exit_reason is max_iterations/timeout** — the workspace is dirty. Run the recovery checklist before proceeding.
- **Assume old stub route files are inert when adding new API routers** — In FastAPI projects, old stub files like `routes/people.py` or `routes/projects.py` may have `@router.get("/people")` catch-all stubs that intercept requests BEFORE your new API router in a different file (e.g. `routes/people_api.py`). The symptom: API tests return 501/405 instead of 201/200 because the stub router matches first. **Fix: empty the old stub file's content to a bare APIRouter with no routes** (don't delete it — other modules may import the router). If you're replacing stubs with real implementations, search for and neutralize all old stub route files in the same project before declaring the task done.
- **Assume test helper functions are importable from existing test files** — `from tests.test_routes import _make_test_db` fails when `tests/` has no `__init__.py` (it may deliberately be a namespace directory). **Fix: inline the helper function directly in the new test file** rather than attempting an import that cannot resolve.
- **Assume a subagent deleted old files when moving content to new paths** — subagents that reorganize tests, rename modules, or restructure directories often copy the new files but forget to delete the originals. The test suite passes because both copies exist. After any file-move task, grep for stale imports/duplicates before marking complete.

## Handling Issues

### If Subagent Asks Questions

- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

### If Reviewer Finds Issues

- Implementer subagent (or a new one) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

**Exception — straightforward fixes:** When the flagged issues are mechanical guard clauses (None checks, try/except wrappers, help text corrections) and you can verify each one with a concrete command (syntax check, import test, dry-run), you may fix them directly and skip the re-review. Criteria for skipping:
- Each fix is ≤ 3 lines in one location
- Each fix has an exact verification command (e.g. `python3 -c "import ast; ast.parse(...)"`)
- No behavioural logic changes (no new branches, no changed return values)
- Fixes are purely defensive (guard against None/corrupt data, not changing how correct data flows)

If the fix touches logic, data flow, or spans multiple files, do NOT skip re-review.

### If the Reviewer Is Wrong (false alarm)

Quality reviewers sometimes flag issues based on incomplete context — they see
code in one file and assume it applies to another, or misinterpret the data domain.

**Before dispatching a fix subagent, investigate the claim yourself:**
- Is the flagged issue real in *this* context, or does it only apply in a different
  code path / data source / environment?
- Can you quickly verify with a terminal one-liner (`diff` some files, `grep` for
  the pattern, sample the data)?
- If the reviewer says "this is broken" but the existing data proves it works,
  the reviewer was wrong — note it and proceed without a fix loop.

**Common false-alarm types:**
- Code in a legacy/sibling file that looks similar but doesn't apply (e.g. a parser
  in seed.py that handles old bank archives, flagged during review of import.py
  which handles fresh downloads)
- Hardcoded assumptions about data format that don't match the actual CSV shape
  (reviewer didn't inspect the real data)
- Security concerns that exist in theory but can't be exploited (e.g. table name
  interpolation from a hardcoded internal dict — trusted, not user-supplied)

**Rule:** If you can't reproduce the issue with a concrete terminal command in under
30 seconds, it might be real — dispatch a fix. If you can disprove it in 5 seconds,
the reviewer was hallucinating context. Move on.

### If Subagent Fails a Task

- Dispatch a new fix subagent with specific instructions about what went wrong
- Don't try to fix manually in the controller session (context pollution)

### If Subagents Diverge (commits branched off earlier history instead of stacking)

Subagents in a worktree may each commit independently on the same branch, but their commits
can end up branching off an **earlier commit** rather than stacking sequentially. The symptom:
`git log --oneline -10` shows 2-3 commits on a diverged branch while the main line jumped ahead
to an unrelated head. This happens when subagents resolve paths relative to the worktree root but
their parent commit resolution differs from the orchestrator's expectation, or when git rebase/merge
state shifts between dispatches.

**Detection — after subagent completes, before marking task done:**
```bash
git log --oneline -10
```
If the latest commits don't sit cleanly on top of the previous task's HEAD (look for a branch
that splits off 2-3 commits ago), divergence has occurred.

**Recovery — do NOT re-dispatch subagents (they'll repeat the same branching pattern):**

1. `git log --oneline -10` to confirm divergence and identify which commit is the true head of the worktree branch
2. Identify which files were created/modified by the diverged commits vs what's actually on the main line
3. **Manually restore any lost files** using `write_file` (not subagent) — copy content from the diverged commits if needed:
   ```bash
   # Show the diff of a diverged commit to recover its changes
   git show <diverged-commit>:pfin-api/pfin_api/routes/people_api.py
   ```
4. Apply the restored/modified files via `patch` or `write_file` in the orchestrator session
5. Verify: `git diff --stat` should show only the correct in-scope changes, then commit once

**When to do this:** After every task dispatch when tasks create files (not just modify existing ones),
and after Task 9+ of multi-task runs where divergence is most likely.

### If Subagent Exits Dirty (max_iterations / timeout / interrupted)

**Also check for main-repo leak**: Subagents working in a git worktree sometimes write changes to BOTH the worktree AND the main repo checkout (if they resolve paths relative to the git root instead of the worktree root). After subagent dispatch, always check `git status` in the MAIN repo (not just the worktree). If `M  pfin-api/pfin_api/routes/web.py` appears on master, the subagent leaked — stash or discard those changes before merging.

**Recovery checklist (run in order, don't skip steps):**

1. **Check**: `git status --short` — expect modified files (M) and untracked test files (??)

2. **Check for spillover to main repo** — if files were modified at `/home/tangyi/dev/personal-finance/...` (not under `.worktrees/`), the subagent leaked to master. See `references/subagent-spillover-worktree-drift.md`. Stash before merging:
   ```bash
   git stash push -m "subagent leaked changes to main repo"
   ```

2. **Verify correctness** before adopting the changes:
   - `python3 -c "import ast; ast.parse(open('file.py').read())"` — syntax check
   - `python3 -m pytest tests/test_new.py -v --tb=short` — new tests pass
   - `ls` fixture paths referenced in tests — do they exist on disk?
   - `python3 -m pytest tests/ -q` — full suite still passes

3. **Fix broken fixture references**: Subagents reference fixtures at wrong paths or ones they created but `.gitignore` silently blocked. Fix the path, create missing fixtures, then re-run.

4. **Check for stale duplicate files**: When a subagent was told to move files (rename directories, reorganize tests), it may create the copies at new paths but forget to delete the originals. The test suite can still pass if both copies exist, masking the stale files. Detection:
   ```bash
   # If subagent was supposed to MOVE test files, old paths should NOT exist
   ls tests/test_old_path.py 2>/dev/null && echo "STALE — should be deleted"
   # grep for imports referencing old module paths
   grep -rn "from vanguard_import\|from workpension_import\|from import import" tests/ --include="*.py"
   ```
   If stale files found: delete them (`rm`), then verify tests still pass and commit.

5. **Selective diff review**: Run `git diff` or `git diff --stat`. Each modified file may contain a mix of correct in-scope changes AND out-of-scope scope creep. Revert only the wrong parts before committing. Example: subagent hit limit while fixing sync engine, but also added an unneeded `query()` hook to `db.py` creating circular dependency — reverted `db.py`, committed the 3 correct files.
   ```bash
   git diff --stat          # see what changed
   git checkout -- <bad-file>  # revert out-of-scope changes
   git add <correct-files>    # stage only what belongs
   git commit -m "..."
   ```

5. **When to discard entirely**: If the majority of changes are wrong, tests fail after selective review, or core logic is broken — do NOT commit. Discard and re-dispatch with clearer instructions.

6. **Python import path sanity check** (environment quirk): After subagent does `pip install .` (not `--break-system-packages`), old pth files from bare installs cause module imports to resolve to site-packages instead of the worktree. Fix:
   ```bash
   rm -rf ~/.local/lib/python3.13/site-packages/__editable__* ~/.local/lib/python3.13/site-packages/<package> ~/.local/lib/python3.13/site-packages/*-*.dist-info
   pip install --break-system-packages -e .
   python3 -c "import <pkg>; print(<pkg>.__file__)"  # should point to worktree, not site-packages
   ```
   Always verify imports resolve correctly after any pip install in a Python project that was previously installed without `--break-system-packages`.

### If Subagent Exits Without Committing (max_iterations / timeout / interruption)

Subagents that hit `max_iterations`, time out, or get interrupted often leave the workspace
dirty — files modified, tests written, but nothing committed. The summary says "completed"
but `exit_reason` is `max_iterations` or similar, not `completed`.

**Recovery checklist (run in order):**

1. **Check exit reason**: If `exit_reason` is NOT `completed`, the workspace is dirty.
   ```bash
   git status --short
   ```

2. **Verify the subagent's changes are correct** before adopting them:
   - Does the modified file import cleanly? (`python3 -c "import ast; ast.parse(open('file.py').read())"`)
   - Do the new tests pass? (`python3 -m pytest tests/test_new.py -v --tb=short`)
   - Do the tests reference fixtures that actually exist? (`ls` the fixture paths)
   - Does the full suite still pass? (`python3 -m pytest tests/ -q`)

3. **Fix broken fixture references**: Subagents writing tests against new fixtures often
   reference the wrong path or a fixture that was created but not committed (see below).
   Fix the path, create the fixture if needed, then re-run.

4. **Commit the subagent's work** once verified:
   ```bash
   git add <modified files>
   git commit -m "descriptive message"
   ```
   This prevents the partial work from being lost on the next subagent dispatch.

5. **When to re-dispatch instead**: If the changes are incomplete (tests fail, syntax
   errors, wrong logic), do NOT commit. Discard and re-dispatch with clearer instructions.

### Subagent Fixture Files and .gitignore

Subagents running in worktrees inherit project `.gitignore`. When a subagent creates a
test fixture matching an ignore pattern (e.g. `*.csv`, `*.xlsx`), `git add` silently
fails. The subagent may report "committed" but the file isn't tracked.

**Prevention — tell subagents to force-add:**
```
Commit: git add -f <files> && git commit -m "..."
```

**Detection — after subagent completes:**
```bash
# The test references a fixture — does it exist on disk AND in git?
ls tests/fixtures/raw/new_fixture.csv  # exists?
git ls-files tests/fixtures/raw/new_fixture.csv  # tracked?
```

If the file exists on disk but isn't tracked, `git add -f` it and amend the commit.

**This is also a Red Flag**: Never dispatch a subagent for a task that creates new
fixture files (especially `.csv`, `.json`, `.xlsx`, `.pdf`) without explicitly
instructing `git add -f` in the commit step.

## Efficiency Notes

**Why fresh subagent per task:**
- Prevents context pollution from accumulated state
- Each subagent gets clean, focused context
- No confusion from prior tasks' code or reasoning

**Why two-stage review:**
- Spec review catches under/over-building early
- Quality review ensures the implementation is well-built
- Catches issues before they compound across tasks

**When to skip subagent dispatch (do directly):**
Some plan tasks are purely mechanical — creating directories, moving files, renaming, writing
a single pyproject.toml from a known template. Dispatching a subagent for these wastes time
on context injection and handoff. A rule of thumb: if the task requires NO reasoning about
existing code (no parsing, no detection logic, no import resolution, no test adaptation),
do it directly in the orchestrator session. Examples:
- Creating directory structure and empty `__init__.py` files
- Copying files between locations with no content changes
- Writing a known boilerplate file (pyproject.toml, setup.cfg)
- Running a pre-scripted `mv`/`rm`/`cp` sequence

Tasks that DO need a subagent: any code extraction, import resolution, function signature
adaptation, test rewriting, or anything requiring reading and understanding existing code.

**Cost trade-off:**
- More subagent invocations (implementer + 2 reviewers per task)
- But catches issues early (cheaper than debugging compounded problems later)

## Integration with Other Skills

### With writing-plans

This skill EXECUTES plans created by the writing-plans skill:
1. User requirements → writing-plans → implementation plan
2. Implementation plan → subagent-driven-development → working code

### With test-driven-development (MANDATORY — not advisory)

TDD is loaded as a hard dependency for every SDD run. The orchestrator MUST:

1. **Load the TDD skill** at the start of any SDD execution — it's always available under `software-development/test-driven-development`.
2. **Embed the full TDD checklist** in every implementer subagent's context (below). Not a one-liner — paste the numbered steps verbatim so subagents cannot skip steps.
3. **Verify enforcement**: when the implementer reports completion, confirm that:
   - The test was run and **failed first** (not just "written")
   - `pytest tests/ -v` passes (full suite, not just the single test file)
4. **Require edge-case coverage**: each function/method must have ≥1 test for normal paths + ≥1 for error/edge cases. Zero%-covered functions are a spec gap — the spec reviewer MUST reject the task until fixed.
5. **Reject "tests written after"**: if the implementer admits writing code before tests or claims "I'll add tests later", reject immediately and re-dispatch.

#### TDD checklist to paste into every implementer context:

```
FOLLOW TDD (test-driven-development skill) — these are hard steps, not suggestions:
1. Identify which new function(s)/method(s) this task creates
2. Write a failing test in the appropriate tests/ file showing what they should do
3. Run pytest for THAT test file only and CONFIRM IT FAILS — read the failure message
4. Write the minimal code to make that specific test pass (hardcoding is OK here)
5. Run pytest for THAT test file — confirm it passes
6. Run pytest tests/ -v (full suite) — confirm no regressions, output clean
7. Check: does every new function/method have at least 2 tests (normal path + edge case/error)?
   If NO → add missing tests, re-run full suite, do NOT mark task complete
8. Commit with descriptive message
```

**Why this matters**: TDD mentioned as a `related_skills` hint without enforcement led to thin test coverage — implementers would write "1 test for happy path" and call it done. The spec reviewer had no authority to reject on coverage grounds because "adequate test coverage" was a single checkbox with no definition.

**Result of this fix**: Every implementer now gets explicit, numbered TDD steps in context. Every spec reviewer must verify edge-case coverage (≥2 tests per function). Zero%-covered functions = automatic rejection.

### With requesting-code-review

The two-stage review process IS the code review. For final integration review, use the requesting-code-review skill's review dimensions.

### With systematic-debugging

If a subagent encounters bugs during implementation:
1. Follow systematic-debugging process
2. Find root cause before fixing
3. Write regression test
4. Resume implementation

## Example Workflow

```
[Read plan: docs/plans/auth-feature.md]
[Create todo list with 5 tasks]

--- Task 1: Create User model ---
[Dispatch implementer subagent]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, 3/3 tests passing, committed.

[Dispatch spec reviewer]
  Spec reviewer: ✅ PASS — all requirements met

[Dispatch quality reviewer]
  Quality reviewer: ✅ APPROVED — clean code, good tests

[Mark Task 1 complete]

--- Task 2: Password hashing ---
[Dispatch implementer subagent]
  Implementer: No questions, implemented, 5/5 tests passing.

[Dispatch spec reviewer]
  Spec reviewer: ❌ Missing: password strength validation (spec says "min 8 chars")

[Implementer fixes]
  Implementer: Added validation, 7/7 tests passing.

[Dispatch spec reviewer again]
  Spec reviewer: ✅ PASS

[Dispatch quality reviewer]
  Quality reviewer: Important: Magic number 8, extract to constant
  Implementer: Extracted MIN_PASSWORD_LENGTH constant
  Quality reviewer: ✅ APPROVED

[Mark Task 2 complete]

... (continue for all tasks)

[After all tasks: dispatch final integration reviewer]
[Run full test suite: all passing]
[Done!]
```

## Remember

```
DELEGATE EVERY PLAN TASK — never implement inline (it WILL cause a compaction stall)
Load test-driven-development skill (MANDATORY)
Paste TDD checklist into every implementer context
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST — including test coverage
Code quality SECOND — reject zero%-covered functions
Never skip reviews
Catch issues early
Detect commit divergence with `git log --oneline -10` after each dispatch
Prefer orchestrator write_file over re-dispatch for divergence recovery
Verify test failures are new (not pre-existing) before treating as regressions
```

**Quality is not an accident. It's the result of systematic process.**

## Further reading (load when relevant)

When the orchestration involves significant context usage, long review loops, or complex validation checkpoints, load these references for the specific discipline:

- **`references/context-budget-discipline.md`** — Four-tier context degradation model (PEAK / GOOD / DEGRADING / POOR), read-depth rules that scale with context window size, and early warning signs of silent degradation. Load when a run will clearly consume significant context (multi-phase plans, many subagents, large artifacts).
- **`references/gates-taxonomy.md`** — The four canonical gate types (Pre-flight, Revision, Escalation, Abort) with behavior, recovery, and examples. Load when designing or reviewing any workflow that has validation checkpoints — use the vocabulary explicitly so each gate has defined entry, failure behavior, and resumption rules.
- **`references/csv-amount-parsing-pitfalls.md`** — Commas in thousands separators, currency symbols, quoted amount fields, and signed-vs-unsigned conventions from real bank CSV exports. Load when reviewing any CSV data ingestion pipeline — the reviewer should check for these.
- **`references/frontend-xss-esc-pitfall.md`** — Missing single-quote escape in `esc()` function allows XSS when user data is embedded in JavaScript strings inside HTML onclick attributes. Add `.replace(/'/g, "&#39;")`. Load as part of every code quality review for Jinja/HTML templates with inline JS event handlers.
- **`references/sql-join-count-pitfall.md`** — `COUNT(*)` on LEFT JOIN + GROUP BY counts untagged/null rows as 1 instead of 0. Fix: use `COUNT(junction_table.pk)` instead. Load when reviewing any stats/aggregation endpoint or data pipeline code with LEFT JOINs.
- **See `brainstorming` skill → `references/data-pipeline-implementation-pitfalls.md`** — Seven common ETL/data-pipeline bugs caught during code review: `float(None)` from NULL columns, `date.fromisoformat()` crash on corrupt dates, dry-run flag breaking on missing tracking tables, feature-flag setup that skips dependent infrastructure, unvalidated numeric casts, and PRAGMA writes to read-only source databases. **Load this reference as part of every code quality review for ETL/sync/import code.** The quality reviewer should check the candidate implementation against each pitfall.
- **`references/fixture-test-fix-patterns.md`** — Decision matrix for direct-patch vs subagent-dispatch when fixing tests after schema migrations. Common failure categories (column renames, model removals, route changes, data threshold drift). Subagent discovery bonus patterns (redundant inserts causing UNIQUE violations, .gitignore fixture silencing, cross-test interference). **Load when executing SDD plans that include test-suite-fix tasks.**
- **`references/model-comparison-parallel-worktrees.md`** — Setup and methodology for comparing two AI models head-to-head on the same implementation plan. Covers parallel worktree creation, Kanban-driven dispatch, metrics to compare (tokens, API calls, duration, test pass rate, code similarity), and the key finding that plan quality dominates model choice.
- **`references/kanban-sdd-execution-getchas.md`** — Shell quoting pitfall when creating kanban tasks via `--body "$(cat file)"`, skill loading ambiguity (`skill_view` refuses to guess matching names; use full categorized path), forcing skills into workers with `--skill`, and dispatch monitoring patterns.

- **`references/inline-execution-evidence.md`** — Empirical data from 5 runs across 2 models: SDD loaded in all, zero subagents dispatched in 4 of 5. Covers diagnostic methodology for comparing kanban logs to session transcripts, model-specific compaction behavior (Qwen35B 11 compactions → stall, DSv4Flash 0 compactions), and the plan-content temptation effect (copy-pasteable code blocks push agents toward inline execution). **Load when diagnosing "why is this kanban worker stuck on compaction?" or comparing model performance on the same plan.**

All references adapted from gsd-build/get-shit-done (MIT © 2025 Lex Christopherson). The CSV amount parsing pitfalls file documents a real-world bug discovered during this session.
