---
name: kanban-workflow
description: "Decompose tasks into kanban cards, dispatch workers across profiles, manage claim/reclaim lifecycle, and handle pitfall-driven execution."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, task-decomposition, workflow-orchestration, multi-profile, scheduling]
---

# Kanban Workflow

Orchestrate complex tasks across multiple Hermes profiles using a kanban-based decomposition pattern. One orchestrator skill decomposes and dispatches; worker skills execute cards with pitfall-aware patterns.

## When to Use

- User has a task too large for one session (e.g., "migrate this codebase", "rewrite the auth module")
- Tasks can be broken into independent subtasks
- Multiple profiles are available for parallel execution
- The task requires iterative coordination between components

## Architecture Overview

```
User Request → Orchestrator Session (decompose → create cards → dispatch)
                   ↓
              Worker Sessions (execute one card each in parallel)
                   ↓
            Status updates → Orchestrator (check → reassign → continue/complete)
```

### Profile Discovery

**CRITICAL:** The orchestrator MUST discover available profiles via `hermes profile list` or ask the user. Never guess assignee names. If you don't know what profiles exist:
1. Run `hermes profile list` to see all available profiles
2. Ask the user which ones are relevant to the task

### Workspace Routing

Workers run in isolated environments controlled by `$HERMES_KANBAN_WORKSPACE`:

| Value | Meaning | Use Case |
|-------|---------|-----------|
| `scratch` (default) | One temp dir per worker, cleaned up when done | Isolated one-off tasks |
| `dir:<path>` | Shared directory across workers | Tasks needing shared state |
| `worktree` | Git worktree isolation | Code changes in a repo |

Workers may use `$HERMES_TENANT` prefix to avoid cross-tenant memory collisions.

## Orchestrator Patterns (Dedicated Skill)

For the **full decompose → dispatch → monitor → complete lifecycle**, load the `kanban-orchestrator` skill which contains:
- Multi-profile discovery and card creation (`hermes kanban create`)
- Dispatch logic with model hints and parallel scheduling
- Heartbeat checks via `process(action="list")` and `cronjob action="list"`
- Claim/reclaim/reassign recovery paths
- Anti-temptation rules (don't do the work yourself!)
- Profile discovery protocol (never guess assignees)

The orchestrator skill is self-contained — load it when you need the full orchestration workflow.

## Worker Pitfall Patterns (Dedicated Skill)

For **worker execution best practices**, load the `kanban-worker` skill which contains:
- Workspace kind pitfall handling
- Common worker mistakes and recovery patterns
- Metadata reporting format for completion
- Handling of blocked/failed cards

Load this skill when you're writing or reviewing a worker's execution logic.

## Quick Start (Single Profile)

For small tasks within one profile:

```bash
# 1. Create kanban board (if not exists)
hermes kanban init

# 2. Decompose manually — or use the orchestrator skill for automation

# 3. Workers execute cards in parallel cron sessions
hermes kanban claim <card_id>
hermes kanban complete <card_id> status="done" notes="summary"
```

## Key Anti-Patterns

- **Don't do the work yourself** — The orchestrator decomposes and dispatches, workers execute. Breaking this defeats the parallelism benefit.
- **Don't hardcode profile names** — Always discover profiles first.
- **Don't share state via filesystem unless intentional** — Use workspace routing to control isolation.
- **Don't dispatch cards without clear acceptance criteria** — Each card should have a specific, verifiable output.

## Related Skills

- **kanban-orchestrator** — Full orchestrator lifecycle: decompose, dispatch, heartbeat, recover, complete
- **kanban-worker** — Worker pitfall patterns and execution best practices