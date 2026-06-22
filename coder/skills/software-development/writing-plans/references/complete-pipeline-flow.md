# Complete Pipeline Flow

The full gated workflow established for this project. All steps must be followed sequentially for non-trivial features.

```
brainstorming → spec → worktree → plan (with header) → kanban dispatch → execute → finishing-a-development-branch → merge + cleanup
```

## Step 1: Brainstorming

Load `software-development/brainstorming` skill. Do NOT write code. Explore intent, requirements, constraints. Present 2-3 approaches. Get explicit approval.

## Step 2: Spec

Save approved design as `docs/spec-YYYY-MM-DD-<topic>.md` on master. Commit. Self-review for placeholders, consistency, and ambiguity before presenting.

## Step 3: Worktree

Create a feature branch inside a git worktree — never on master. Ensures the stable baseline is isolated.

```bash
cd /path/to/repo
git worktree add -b feature/<short-name> .worktrees/<short-name> master
```

## Step 4: Plan (with workspace header)

Load `software-development/writing-plans` skill. Write plan in the worktree. Include workspace header at the very top so kanban workers can route to the correct checkout:

```markdown
Workspace: <absolute-path-to-worktree> (branch: feature/<name>)
Git root: <absolute-path-to-git-root>
Kanban board: finance
Epic: <EPIC-PREFIX>
Plan created: YYYY-MM-DD
```

Use `pwd` or `git worktree list` to get the absolute path. Commit plan to the feature branch.

## Step 5: Kanban Dispatch

Create kanban tasks with:
- `workspace_kind="worktree:<worktree-path>"` — all tasks on the same epic use the exact same path
- Parent links for dependency chaining
- Assign to appropriate profile (heavy/35B for complex logic, fast/9B for mechanical tasks)

Author profiles on this setup:
- `tinker` (35B Qwen) — complex Python/logic changes
- `fast` (9B Qwen) — simple mechanical tasks (add source_id to parsers, schema migration scripts, unit test additions)
- `default` (35B Qwen) — general purpose

## Step 6: Execute

Workers pick up tasks, write code, test, commit. Orchestrator monitors parent → child handoffs and unblocks as needed. See `kanban-orchestrator` skill for full lifecycle.

## Step 7: Finish Branch

Load `finishing-a-development-branch` skill. Verify tests, detect environment, present 4 options, execute choice, cleanup worktree + branch.

## Dependent multi-repo pipeline

When a feature spans two repos with a dependency, run both in parallel:

```
Data layer (personal-finance-data):
  spec → worktree (feature/source-id) → plan → kanban dispatch → execute → merge + cleanup

App layer (personal-finance):
  spec → worktree (feature/pfin-migration) → plan → kanban dispatch → execute → merge + cleanup
```

The app layer tasks can start immediately (they'll complete naturally after the data layer's source_id is available). Be explicit in the planning phase about which repo each epic targets.

## Common pitfalls

- **Skipping the workspace header.** Without it, kanban workers default to `scratch` workspace and commits vanish.
- **Task too broad.** A task that touches 3+ files or rewrites existing logic should be 2-3 sub-tasks. See `writing-plans` step 6.7 for the granularity rule.
- **Wrong profile assignment.** Complex logic (schema changes, rewrite sync loops) needs 35B. Mechanical changes (add column to parsers, migration scripts) can go to 9B.
- **Not unblocking after parent completes.** Children with `parents=[...]` stay in `todo` until the orchestrator explicitly unblocks them.
