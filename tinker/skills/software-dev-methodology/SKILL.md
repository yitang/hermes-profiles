---
name: software-dev-methodology
description: "Core development methodologies: systematic debugging, test-driven development (TDD), and master strategy execution. Class-level patterns for reliable software engineering."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, TDD, testing, methodology, refactoring, audit, implementation, strategy-execution]
---

# Software Development Methodology

Three complementary methodologies for reliable software engineering: systematic debugging (find root cause before fixing), test-driven development (write tests before code), and master strategy execution (implement documented plans with verification).

## When to Use

- **Systematic debugging:** Any bug, test failure, unexpected behavior, or performance issue. Especially use when under time pressure or after multiple failed fix attempts.
- **TDD:** New features, bug fixes, refactoring. Always — no exceptions without user permission.
- **Master strategy:** Implementing a documented plan against an existing codebase (e.g., `docs/plan-*.md` files, pipeline redesigns, migrations).

---

## Labeled Subsections: Three Methodologies

### 1. Systematic Debugging (4-phase root cause investigation)

**Iron Law:** NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST. Symptom fixes are failure.

#### The Four Phases
1. **Root Cause Investigation** — Read errors carefully, reproduce consistently, check recent changes, gather evidence across component boundaries, trace data flow to origin. For multi-component systems: log what enters AND exits each boundary, verify environment/config propagation.
2. **Pattern Analysis** — Find working examples in the codebase, read reference implementations COMPLETELY (not just skimming), identify differences between working and broken.
3. **Hypothesis and Testing** — Form a single specific hypothesis, test minimally (one variable at a time), verify before continuing. Don't stack fixes.
4. **Implementation** — Create failing test case first, implement single fix for root cause, verify with full suite. If 3+ fixes failed: STOP and question the architecture.

#### Critical Debugging Pitfalls

**Don't blame data quality before checking values.** The "sparse data" or "data gaps" explanation is the most common wrong root cause — it sounds plausible but masks real algorithm bugs. Always verify by reading actual values first. A correctly implemented algorithm on sparse data produces boring-but-correct results, not -£114k from £-22k with simple transaction sums.

**Sign convention errors in accumulation algorithms.** When debugging running totals or backward-wind calculations, check sign convention before anything else. Walking backwards FLIPS sign semantics: `balance[t-1] = balance[t] + txn[t]` is correct; subtracting reverses direction. Test with a known-good sequence as an identity check.

**Header collision in data routing.** Two different accounts producing CSVs with identical headers → detection logic matches both → wrong parser → wrong table. Fix by adding distinguishing columns or filename-based pre-detection. Simulate detection chains against actual headers rather than adding print statements.

#### Red Flags (Stop and Return to Phase 1)
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- Proposing solutions before tracing data flow
- "One more fix attempt" (after 2+ failures)

#### The Rule of Three
After 3 failed fixes: STOP. Each fix revealing a new problem in a different place = architectural problem, not individual bugs. Question fundamentals. Discuss with user before attempting more fixes.

### 2. Test-Driven Development (RED-GREEN-REFACTOR)

**Iron Law:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST. If you didn't watch the test fail, you don't know if it tests the right thing.

#### The Cycle
1. **RED — Write Failing Test.** One minimal test showing what should happen. Clear descriptive name, real code (not mocks unless truly unavoidable), one behavior per test. **MANDATORY:** Watch it fail before proceeding.
2. **GREEN — Minimal Code.** Write the simplest code to pass. Hardcode returns, copy-paste, skip edge cases — we'll fix it in REFACTOR. Cheating is OK in GREEN.
3. **REFACTOR — Clean Up.** Remove duplication, improve names, extract helpers, simplify expressions. Keep tests green throughout. If tests fail during refactor: undo immediately.

#### Why Order Matters
Tests written after code pass immediately, proving nothing. They might test the wrong thing or miss edge cases you forgot. Test-first forces you to see the test fail, proving it actually tests something. Tests-after answer "What does this do?" Tests-first answer "What should this do?"

#### Testing Anti-Patterns
- Testing mock behavior instead of real behavior
- Testing implementation details (internal method calls) rather than behavior/results
- Happy path only — always test edge cases, errors, boundaries
- Brittle tests that break on refactoring

#### When TDD Is Hard
| Problem | Solution |
|---------|----------|
| Don't know how to test | Write the wished-for API. Assert first. Ask the user. |
| Test too complicated | Design too complicated. Simplify the interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify the design. |

### 3. Master Strategy Execution (Plan-vs-Reality)

**When:** A documented master plan exists (`docs/plan-*.md` or equivalent) for a project refactor, pipeline redesign, or migration.

#### Steps (in order)
1. **Read the plan + scan the repo.** Find and read the strategy document. Do a directory listing to understand real current state. Note mismatches immediately — these are implementation gaps.
2. **Identify header collisions and routing bugs.** (Domain-specific: applies to data pipeline projects.) Two accounts produce identical column headers → filename-based routing MUST be added.
3. **Fix schema first.** Ensure all tables referenced by any parser exist in the schema file, including aggregate views. Verify with dry-run DB creation.
4. **Fix routing in import/parsing layer.** Add filename-based detection at top of `detect_account()`. Register new parsers in PARSERS dict and TABLE_NAMES mapping.
5. **Clean historical data before rebuild.** Run clean.py on raw historical data. Verify output: correct number of cleaned CSVs, audit trail generated.
6. **Rebuild database from scratch.** Remove old DB → create fresh schema → import all clean CSVs → verify row counts, routing, and dates match plan expectations.
7. **Update documentation.** Update README with current state (row counts, dates, supported formats).

#### Plan-vs-Reality Audit Checklist
For each phase of the plan:
1. **Check existence** — Does the required artifact exist? (files, tables, functions)
2. **Check correctness** — Does it produce expected output? (row counts, dates, routing)
3. **Check fidelity** — Did you follow the plan's approach, or deviate? Document any deviation with reason.

Use three severity levels: PASS ✅, WARNING ⚠️ (justified deviation), FAIL ❌.

#### Common Plan-vs-Reality Drift Patterns
- **Key name drift:** Config uses `start_date` while parser reads `start`. Grep every key referenced in the plan across all consumers.
- **Loop break-after-yield (off-by-one):** Generator yields BEFORE checking termination condition — emits one extra row. Check: boundary must be verified BEFORE yield.
- **Cross-validation gap:** Numbers don't add up between entities. Re-run the specific numerical checks the plan lists — code may work but produce wrong numbers. >1% deviation is a red flag.
- **Name string mismatch:** DB contains rows with names differing from what the plan calls them. Run `SELECT DISTINCT name FROM table` after any data generation.

#### Acceptable Deviations (must be documented)
- Header collision breaks routing → filename-based routing added (justified)
- Missing init_schema.py → CREATE one rather than baking SQL inline (justified)
- Balance computation on CSV-only accounts falls back to zeros → data availability, not implementation bug

---

## Verification Checklist (apply all that are relevant)

### Debugging
- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Root cause identified and hypothesis formed
- [ ] Single fix attempted with verification
- [ ] If 3+ failures: architecture questioned

### TDD
- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass, output pristine

### Master Strategy
- [ ] All accounts from plan have their own database table
- [ ] No cross-contamination between account data
- [ ] Total row count matches or exceeds plan expectations
- [ ] inbox/ is empty and ready for new drops
- [ ] Documentation reflects actual current state

## Related Skills

- **sqlite-visualization** — Generate charts from SQLite (for visualizing results after fixing)