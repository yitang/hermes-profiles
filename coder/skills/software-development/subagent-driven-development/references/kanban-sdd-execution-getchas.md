# Kanban + SDD Execution Gotchas

## Task creation: shell quoting pitfall

When creating a kanban task with `--body` containing multi-line content, bash `$()` with `$(cat file)` still fails if the body contains nested single quotes inside double-quoted strings. The error manifest is:

```
/usr/bin/bash: eval: line N: syntax error near unexpected token '('
```

**Fix:** Write the task body to a temp file first (avoiding problematic nesting), then create the kanban task with `--body "$(cat file)". Use the `write_file` tool to create the temp file, which avoids shell quoting entirely.

## Skill loading: ambiguous names

`skill_view(name='subagent-driven-development')` may fail with:

```
Ambiguous skill name 'X': 2 skills match across your local skills dir and external_dirs.
Refusing to guess — load one explicitly by categorized path.
```

**Fix:** Always use the full categorized path (e.g., `software-development/subagent-driven-development`, not just `subagent-driven-development`). List candidates from the error message and pick the right one.

## Skill loading: silent wrong-skill selection (superpowers collision)

Even when no ambiguity error fires, an agent may silently load the wrong version of a skill.
This happened when both `~/.hermes/skills/software-development/subagent-driven-development/`
(Hermes v1.3+, 31KB, self-contained) and `~/para/2_areas/agents/skills/superpowers/skills/subagent-driven-development/`
(older, 12.5KB, template-based) existed. The agent called `skill_view` on the superpowers
version, loaded its 3 separate prompt-template files, and the friction of assembling
subagent prompts pushed it toward inline execution. Result: 11 compactions in 20 min,
0 commits, process frozen on `futex_wait_queue_`.

**6 known collisions** between Hermes (`~/.hermes/skills/`) and superpowers
(`~/para/2_areas/agents/skills/superpowers/skills/`):

| Skill | Hermes | Superpowers |
|---|---|---|
| `brainstorming` | 17KB v1.0.0 | 10.6KB |
| `requesting-code-review` | 8.5KB v2.0.0 | 2.8KB |
| `subagent-driven-development` | 31KB v1.3.0 | 12.5KB |
| `systematic-debugging` | 10.5KB v1.1.0 | 9.9KB |
| `test-driven-development` | 9.6KB v1.1.0 | 9.9KB |
| `writing-plans` | 29.9KB v2.0.0 | 7KB |

Hermes versions are consistently larger and versioned. **Fix: remove the superpowers copies**
or add `skills/superpowers/` to `.gitignore` in the parent repo and remove the entry from
`skills.external_dirs` in config. When Hermes local skills take precedence (per
`prompt_builder.py:1101`), but the agent can still explicitly load the external version
via `skill_view`, the fix is to remove the stale copy entirely.

## Force-loading skills into kanban workers

Kanban workers only get built-in `kanban-worker` skill. To force-load additional skills, use the `--skill` flag on create:

```bash
hermes kanban --board <slug> create \
  "Title" \
  --assignee dsv4f \
  --workspace worktree:/path \
  --max-runtime 2h \
  --skill subagent-driven-development \
  --body "$(cat /tmp/body.txt)"
```

Multiple skills: `--skill skill-a --skill skill-b` (repeat the flag).

## Worker dispatch and monitoring

After creating a task, the gateway dispatcher auto-promotes it to `ready` and spawns workers if capacity allows. Verify with:

```bash
hermes kanban --board <slug> list
# Look for ● (running) vs ? (ready) status indicators
```

Use `hermes kanban log <task_id>` or the gateway's real-time event stream to monitor progress.

## Fragmented multi-run handoff (anti-pattern)

When a kanban worker completes only 1 task of a 10-task plan and posts the remaining 9 as `kanban_comment` follow-ups, this is NOT a valid SDD execution. Symptoms:
- A task marked `done` with summary "Task 1 complete" but comments describe Tasks 2-10 in detail
- A second task (different ID) later completes the remaining work on the same worktree
- Duplicate commits (same change committed twice by different runs)
- The user sees the first task as "complete" but has to dig through comments to find the rest

**This pattern indicates the worker gave up early and delegated to prose instead of dispatching subagents.** The correct behavior: a single run dispatches all 10 tasks via `delegate_task`, commits each, then calls `kanban_complete` once.

**Detection:** Check comments on a `done` task. If comments describe work not captured in the run's `latest_summary`, the task fragmented. Check for duplicate commits with the same message on the worktree branch.
