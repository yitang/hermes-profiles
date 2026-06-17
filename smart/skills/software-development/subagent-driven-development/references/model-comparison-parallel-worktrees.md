# Model Comparison via Parallel Worktrees

**When to use:** Comparing two AI models on the same implementation plan to evaluate quality, token efficiency, speed, and cost.

## Setup

1. Create two worktrees from the same clean baseline commit (before any feature code):

```bash
cd /path/to/repo
git worktree add .worktrees/<feature>-modelA -b feat/<feature>-modelA <baseline-commit>
git worktree add .worktrees/<feature>-modelB -b feat/<feature>-modelB <baseline-commit>
```

2. Install dependencies in both:
```bash
cd .worktrees/<feature>-modelA && pip install -e .
cd .worktrees/<feature>-modelB && pip install -e .
```

3. Write the implementation plan ONCE, then copy to both worktrees. Fix the workspace header in each to point to the correct absolute path:

```markdown
Workspace: /path/to/.worktrees/<feature>-modelA (branch: feat/<feature>-modelA)
```

## Execution

**Manual comparison (two sessions):** Start a session with model A, feed it the plan in its worktree. Start another session with model B, feed it the same plan in its worktree. Run in parallel.

**Kanban-driven comparison (automatic):** Create two kanban tasks, each assigned to a different profile/model. Each task body says "Using SDD, implement the plan at `.worktrees/<feature>-modelX/docs/plan-....md`". The kanban dispatcher runs them in parallel since they're in different worktrees.

## Metrics to Compare

After both complete:

| Metric | How to check |
|--------|-------------|
| Token usage | `/usage` command in each session |
| API calls | `/usage` output |
| Duration | Session duration in `/usage` |
| Tests passed | `pytest -q --tb=no` in each worktree |
| Commits | `git log --oneline` count |
| Code similarity | `diff` key files between worktrees |
| Test coverage | `wc -l` on new test files |

## Key Finding

**Plan quality dominates model choice.** A detailed plan with complete copy-pasteable code and explicit file paths produces near-identical output across different models. The models differ only in cosmetic details (variable naming, escape handling, defensive checks). The plan is the leverage point — invest effort there, not in model selection.

When the plan was vague ("add a projects page with budget tracking"), models produced wildly different implementations. When the plan had exact HTML/JS/Python code for every task, both Qwen 3.5 35B and DeepSeek V4 Flash produced identical functionality with only cosmetic whitespace/escape differences.

## Real Example (2026-06-16)

Comparing Qwen 3.6 35B vs DeepSeek V4 Flash on a 10-task pfin plan:

| Metric | Qwen 3.6 35B | DeepSeek V4 Flash |
|---|---|---|
| Total tokens | 6,946,811 | 4,590,743 |
| API calls | 92 | 55 |
| Duration | 1h 15m | 17m |
| Tests passed | 93 | 82 |
| Test coverage | 228 lines | 107 lines |
| Code diff | 3 minor diffs | — |

DeepSeek was 4.4x faster and used 34% fewer tokens. Both produced working features. The only functional difference: Qwen added a 404 existence check on update_entry that DeepSeek missed.
