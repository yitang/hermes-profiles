# Inline Execution Evidence: SDD Loaded, No Subagents Dispatched

Documented 2026-06-16 from a model-comparison run (Qwen35B vs DeepSeekV4Flash) executing the same 10-task plan via kanban and CLI session.

## The data

| Run | Model | Env | SDD loaded? | delegate_task calls | Compactions | Result |
|-----|-------|-----|------------|---------------------|-------------|--------|
| Session `084757_3b8557` | deepseek-v4-flash | CLI | Yes (v1.1.0) | **0** | 0 | All 10 tasks done inline, 9:50 |
| Kanban `t_53ed0bfd` | deepseek-v4-flash | dsv4f profile | Yes | **0** | 0 | Task 1 only, 9:09 |
| Kanban `t_6c007974` | deepseek-v4-flash | dsv4f profile | Yes | **0** | 0 | Tasks 2-10 inline, 2:15 |
| Session `095205_b24bd8` | Qwen3.6-35B-A3B | CLI | Yes (v1.3.0) | **10+** (via compaction summary) | 1 | All 10 tasks done, 37 min |
| Kanban `t_cc92bc90` | Qwen3.6-35B-A3B | smart profile | Yes (superpowers, older) | **0** | **11** → stall | 3 files written, 0 committed, frozen |

## Key findings

1. **SDD loaded ≠ SDD used.** All 5 runs loaded the skill. Only the CLI session (Qwen35B) actually dispatched subagents. The kanban workers and the DSv4F session all went inline. Even when the task body explicitly said "use delegate_task" (t_6c007974), the agent ignored it.

2. **Model context size determines survival.** Qwen35B went inline → 11 compactions → futex stall. DeepSeek v4 Flash went inline → 0 compactions → finished cleanly. The SDD skill vs inline choice is a survivability question for smaller-context models. For large-context models (DSv4Flash 128K+), inline execution works but still produces sloppier results (duplicate commits, split across runs).

3. **Plans with copy-pasteable code blocks are the strongest temptation.** The plan (`plan-2026-06-16-cash-people-projects.md`) contained full code for every task. Agents read the plan, saw ready-to-use code, and concluded "I can write these files faster than dispatching subagents." Even explicit instruction to dispatch subagents in the task body did not overcome this temptation.

4. **Skill name collision compounds the problem.** The Qwen35B kanban worker loaded `superpowers/subagent-driven-development` (older, template-based) instead of `software-development/subagent-driven-development` (v1.3.0, self-contained). The older version requires loading 3 separate prompt-template files before dispatching — friction that pushed the agent toward inline.

5. **Fragmented multi-run handoffs are a failure pattern.** The DSv4Flash kanban execution split across two tasks: t_53ed0bfd completed only Task 1 (9 min), then posted the remaining 9 tasks as `kanban_comment` follow-ups rather than continuing. A separate task t_6c007974 (2 min) picked up Tasks 2-10. This produced duplicate commits (tests at `95fc4fe` + `2bea4f9`, transaction page at `f557c01` + `d32806f`) and required the user to redo the exercise. **Single-run execution is the only valid test of kanban SDD fidelity.** Split runs with comments-as-handoffs are not a substitute — they indicate the worker gave up early and delegated to prose.

## Diagnostic methodology

To determine whether a run used SDD or inline:

```bash
# Count delegate_task mentions in kanban worker log
grep -c "delegate_task\|dispatch" ~/.hermes/kanban/boards/<board>/logs/<task_id>.log

# The log only shows text mentions, not actual tool calls.
# For actual dispatch count, check the session transcript.
```

For a session (CLI run): use `session_search` with the session ID, or inspect the compaction summary for `[tool: delegate_task]` markers.

For comparing two runs:
1. Count compactions: `grep "compacting context\|compressed" <log>`
2. Count file writes: `grep "write_file\|patch" <log>`
3. Check process state: `cat /proc/<pid>/wchan` (futex_wait_queue = compaction stall)
4. Check syscall: `cat /proc/<pid>/syscall` (202 = futex = stall)
5. Compare git log: commits vs uncommitted files on disk
6. Check which skill version was loaded: `grep "skill.*subagent" <log>` — look for `software-development/` (Hermes v1.3+) vs `superpowers/` (older)
