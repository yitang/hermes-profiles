# Plan to Kanban Integration

## Workspace header → kanban dispatch

When a plan file has a `Workspace:` header, the kanban orchestrator reads it and passes `workspace_kind="worktree:<path>"` on every `kanban_create` call. This routes all workers to the same feature branch worktree.

```
Plan header:
  Workspace: /home/tangyi/dev/project/.worktrees/feat-name (branch: feature/name)
  Git root: /home/tangyi/dev/project
  Kanban board: finance
  Epic: EPIC-PREFIX

Orchestrator action:
  kanban_create(..., workspace_kind="worktree:/home/tangyi/dev/project/.worktrees/feat-name")
```

Without this header, workers default to `scratch` workspace — their commits are garbage-collected after completion.

## Multi-repo dependency ordering

When two plans have a dependency (e.g., data-layer source_id must complete before app-layer migration can start), the orchestrator should:

1. Dispatch the dependency plan first
2. Wait for all tasks to complete (kanban workers finish)
3. Run `finishing-a-development-branch` to merge + clean up the dependency
4. Then dispatch the dependent plan

The workspace headers make this chainable — each plan self-documents which repo and worktree it targets.

## Kanban Mapping table

The table at the end of every plan maps task numbers to kanban IDs with parent arrays. The orchestrator uses this to create linked tickets with correct dependency chains. The `Epic:` field in the header maps to the epic parent task.
