---
name: kanban-management
description: Complete Kanban workflow skill — orchestrator decomposition playbook (routing, anti-temptation rules, task graph planning) AND worker execution patterns (workspace handling, heartbeats, claiming cards, summary shapes). Load when managing or working with Hermes Kanban boards.
version: 1.0.0
platforms: [linux, macos, windows]
related_skills: [kanban-profile-routing, yitang:sdd-in-kanban]
---

# Kanban Management — Complete Workflow

This skill merges the two halves of the Hermes Kanban workflow: **Orchestrator** (planning/routing) and **Worker** (execution).

> **How this fits with other kanban skills:**
> - `kanban-profile-routing` — profile assignment, model tiering, domain-specific routing. Decide *which* profile gets *which* task.
> - **Kanban Dispatcher** (daemon) — the background process that polls boards, claims ready cards, and spawns worker processes. Not a skill; auto-routes to assigned profile.
>
> Orchestrator = planning/routing layer. Dispatcher = execution plumbing. Worker = task executor.

---

## Section 1: Orchestrator Playbook (decomposition & routing)

### Profiles are user-configured — not a fixed roster

Hermes setups vary widely. Before fanning out, discover available profiles:

```bash
hermes profile list          # print configured profiles
kanban_list(assignee="name")  # sanity-check single name
# Or just ask the user: "What profiles do you have set up?"
```

**Critical:** The dispatcher silently fails to spawn unknown assignees. Cards assigned to nonexistent profiles sit in `ready` forever.

### When to use Kanban (vs. delegate_task or direct answer)

Create Kanban tasks when:
1. Multiple specialists are needed
2. Work should survive a crash/restart
3. User might want to interject (human-in-the-loop)
4. Subtasks can run in parallel
5. Review/iteration is expected
6. Audit trail matters

### The anti-temptation rules

Your job: route, don't execute.
- **Do not execute the work yourself.** If you find yourself "fixing quickly" — stop and create a task.
- **Every concrete task → Kanban card + assignee.** Every single time.
- **Split multi-lane requests** before creating cards. Extract lanes, one card per lane.
- **Run independent lanes in parallel.** No parent links for independent work.
- **Never create dependent work as independent ready cards.** Pass `parents=[...]` in the original `kanban_create`.
- **If no specialist fits, ask the user.** Don't invent profile names.
- **Decompose, route, and summarize — that's the whole job.**

### Decomposition playbook (5 steps)

**Step 1 — Understand the goal:** Ask clarifying questions if ambiguous.

**Step 2 — Sketch the task graph:** Draft out loud. Map lanes to profiles. Decide independent vs gated. Show graph to user before creating cards.

**Step 3 — Create tasks and link:**
```python
t1 = kanban_create(
    title="research: cost analysis",
    assignee="<profile-A>",
    body="...")["task_id"]

t2 = kanban_create(
    title="research: performance analysis",
    assignee="<profile-A>")["task_id"]   # parallel with t1

t3 = kanban_create(
    title="synthesize recommendation",
    assignee="<profile-B>",
    parents=[t1, t2])["task_id"]           # waits for both research
```

**Step 4 — Complete your own task:** If spawned as a planner:
```python
kanban_complete(
    summary="decomposed into T1-T4: 2 parallel research, 1 synthesis, 1 prose draft",
    metadata={"task_graph": {...}})
```

**Step 5 — Report back:** Plain prose naming actual profiles and task IDs.

### Common patterns

- **Fan-out + fan-in:** N research cards → 1 synthesis card (parents=[all])
- **Parallel implementation + validation:** implementer + explorer/researcher in parallel → reviewer
- **Pipeline with gates:** planner → implementer → reviewer (each parents=[previous])
- **Same-profile queue:** N tasks, same assignee, no dependencies — serialized by dispatcher
- **Human-in-the-loop:** Any task `kanban_block()` → wait for input → operator `/unblock` → respawn

### Goal-mode cards (persistent workers)

For multi-step open-ended tasks, pass `goal_mode=True`:
```python
kanban_create(
    title="Translate docs to French",
    body="Acceptance: every page translated, no English left, links intact.",
    assignee="<translator>",
    goal_mode=True,
    goal_max_turns=15)  # optional budget
```

Write **explicit acceptance criteria** — the judge evaluates against title + body.

### Pitfalls (orchestrator-specific)

- **Inventing profile names:** Dispatcher silently drops unknown assignees. Discover first.
- **Bundling independent lanes:** Two outcomes → two cards, not one.
- **Over-linking from wording:** "Finally check X" may still be parallel if X is static config/docs.
- **Forgetting dependency links:** Use parent links so tasks cannot run before inputs exist.
- **Reassignment vs new task:** If reviewer blocks with "needs changes," create NEW task — don't re-run same task.
- **Argument order for links:** `kanban_link(parent_id=..., child_id=...)` — parent first.
- **Tenant inheritance:** Pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create`.

---

## Section 2: Worker Execution Patterns (pitfalls, examples, edge cases)

> The KANBAN_GUIDANCE block is auto-injected into every worker's system prompt. This section adds deeper detail for specific scenarios.

### Workspace handling

| Kind | What it is | How to work |
|---|---|---|
| `scratch` | Fresh tmp dir, yours alone | Read/write freely; GC'd when task archived |
| `dir:<path>` | Shared persistent directory | Other runs read what you write. Treat as long-lived state. Path guaranteed absolute. |
| `worktree` | Git worktree at resolved path | If `.git` doesn't exist, run `git worktree add <path> ${HERMES_KANBAN_BRANCH:-wt/$HERMES_KANBAN_TASK}` from main repo first, then cd and work normally |

### Tenant isolation

If `$HERMES_TENANT` is set, prefix memory entries:
- Good: `business-a: Acme is our biggest customer`
- Bad (leaks): `Acme is our biggest customer`

### Good summary + metadata shapes

**Coding task:**
```python
kanban_complete(
    summary="shipped rate limiter — token bucket, keys on user_id with IP fallback, 14 tests pass",
    metadata={
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14, "tests_passed": 14,
        "decisions": ["user_id primary, IP fallback for unauthenticated requests"],
    })
```

**Coding task needing review (review-required):**
```python
import json

kanban_comment(
    body="review-required handoff:\n" + json.dumps({
        "changed_files": [...],
        "tests_run": 14, "tests_passed": 14,
        "diff_path": "/path/to/worktree",
        "decisions": [...]}, indent=2))

kanban_block(
    reason="review-required: rate limiter shipped, 14/14 tests — needs eyes on user_id/IP fallback choice")
```

**Research task:**
```python
kanban_complete(
    summary="3 competing libraries reviewed; vLLM wins on throughput, SGLang on latency",
    metadata={"sources_read": 12, "recommendation": "vLLM",
              "benchmarks": {"vllm": 1.0, "sglang": 0.87}})
```

**Review task:**
```python
kanban_complete(
    summary="reviewed PR #123; 2 blocking issues (SQL injection, missing CSRF)",
    metadata={
        "pr_number": 123,
        "findings": [{"severity": "critical", "file": "api/search.py", "line": 42}],
        "approved": False})
```

### Claiming cards you created

If your run produced new tasks via `kanban_create`, pass ids in `created_cards`:

```python
c1 = kanban_create(title="remediate SQL injection", assignee="security-worker")
c2 = kanban_create(title="fix CSRF middleware", assignee="web-worker")

kanban_complete(
    summary="Review done; spawned remediations for both findings.",
    created_cards=[c1["task_id"], c2["task_id"]])
```

**Only list ids from successful `kanban_create` return values.** Never invent ids. Phantom ids block completion and are permanently recorded.

### Block reasons

**Bad:** `"stuck"` — human has no context.
**Good:** One sentence naming the specific decision needed + longer context in a comment:
```python
kanban_comment(body="Full context: Cloudflare headers, but NAT behind thousands of peers...")
kanban_block(reason="Rate limit key choice: IP (simple, NAT-unsafe) or user_id (requires auth)?")
```

### Heartbeats

Good: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`
Bad: `"still working"`, empty notes, sub-second intervals. Every few minutes max; skip for tasks under ~2 minutes.

### Retry scenarios

If `kanban_show` shows prior runs with closed statuses:
- **timed_out:** Hit `max_runtime_seconds`. Chunk work or shorten it.
- **crashed:** OOM/segfault. Reduce memory footprint.
- **spawn_failed:** Missing credential or bad PATH. Block for human via `kanban_block`.
- **reclaimed:** Task archived out from under previous run. Check status carefully.
- **blocked:** Previous attempt blocked; unblock comment should be in thread.

### Notification routing

Configure in `~/.hermes/config.yaml`:
```yaml
notification_sources: ['*']           # all profiles
notification_sources: ['default', 'zilor-ppt']  # specific profiles (comma-separated or list)
# omit for default (profile isolation)
```

### CLI fallback (for human operators/scripts)

| Tool | CLI equivalent |
|---|---|
| `kanban_show` | `hermes kanban show <id> --json` |
| `kanban_complete` | `hermes kanban complete <id> --summary "..." --metadata '{...}'` |
| `kanban_block` | `hermes kanban block <id> "reason"` |
| `kanban_create` | `hermes kanban create "title" --assignee <profile>` |

Use tools from inside agents; CLI exists for humans at terminal.

### Do NOT

- **Call `delegate_task` as substitute for `kanban_create`.** `delegate_task` = short reasoning subtasks in your run; `kanban_create` = cross-agent handoffs outliving one API loop.
- **Call `clarify` to ask the human.** You're headless — no live user answers. Times out ~120s, task sits silently in `running`. Use `kanban_comment` + `kanban_block(reason=...)` instead.
- **Modify files outside `$HERMES_KANBAN_WORKSPACE`** unless the task says to.
- **Create follow-up tasks assigned to yourself.** Assign to the right specialist.
- **Complete a task you didn't actually finish.** Block it instead.

### Additional Pitfalls

- **Task state changes between dispatch and startup.** Always `kanban_show` first. If `blocked` or `archived`, stop.
- **Workspace may have stale artifacts** from previous runs (especially `dir:`/`worktree`). Read comment thread for context.
- **Don't rely on CLI when guidance is available.** `kanban_*` tools work across all backends (Docker, Modal, SSH). `hermes kanban <verb>` fails in containerized backends. Use the tools.

---

## When to Use This Skill

Load when:
- Decomposing a goal into Kanban tasks and assigning profiles (**Section 1**)
- Running as a worker executing a Kanban card (**Section 2**)
- Managing a Kanban board (viewing, blocking, unblocking, recovering)
- Debugging a stuck or failed Kanban task
