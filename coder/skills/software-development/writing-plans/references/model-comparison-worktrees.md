# Two-Worktree Model Comparison

**Technique:** Create two identical git worktrees with the same plan, then dispatch different AI models to implement the plan in parallel. Compare results objectively.

## When to Use

- Evaluating which model produces better code for a given domain
- Comparing cost vs quality trade-offs between models
- Testing whether a plan is detailed enough (if both models produce different-but-working code, the plan is good; if neither works, the plan is under-specced)

## Setup

```bash
# 1. Create two worktrees from the same master commit
cd /path/to/main-repo
git worktree add .worktrees/<feature>-modelA -b feat/<feature>-modelA
git worktree add .worktrees/<feature>-modelB -b feat/<feature>-modelB

# 2. Install deps in both
cd .worktrees/<feature>-modelA && pip install -e pfin-data/ pfin-core/ pfin-api/
cd .worktrees/<feature>-modelB && pip install -e pfin-data/ pfin-core/ pfin-api/

# 3. Write the plan once with a workspace header placeholder
# 4. Copy to both worktrees, fix the workspace header per worktree
# 5. Commit the plan in both
```

## Run

- Open two Hermes sessions
- Switch each to a different model
- Feed each the plan file path in its respective worktree
- Run them in parallel (they don't conflict — separate worktrees)

## Comparison Metrics

| Metric | How to measure |
|--------|---------------|
| **Tests passed** | `pytest pfin-api/tests/ -q` in each worktree |
| **Test coverage written** | `wc -l pfin-api/tests/test_cpp.py` or similar |
| **Plan compliance** | `diff` the key output files between worktrees |
| **Bug count** | New failures vs pre-existing baseline |
| **Code quality** | Manual review — do the pages render? Do edge cases work? |
| **Token usage** | Session totals (proxy for cost) |

## Interpretation

- **Both work, one has more tests** → the test-heavy model is more thorough
- **Both work, code nearly identical** → plan is well-specced
- **Neither works** → plan is under-specced (descriptions, not code) — see writing-plans pitfall
- **One works, one doesn't** → the working model is better for this domain

## Example (2026-06-16, pfin cash/people/projects feature)

| Metric | Qwen 3.5 35B | DeepSeek V4 Flash |
|--------|-------------|-------------------|
| Tests passed | 93 | 82 |
| New test lines | 228 | 107 |
| Failures | 8 (6 pre-existing) | 4 (2 pre-existing) |
| API files identical? | 3 of 4 identical | 3 of 4 identical |
| Templates identical? | Only escaping differs | Only escaping differs |

**Verdict:** Both produced functionally identical code. Qwen wrote twice the tests. DeepSeek had fewer pre-existing test cleanup failures.
