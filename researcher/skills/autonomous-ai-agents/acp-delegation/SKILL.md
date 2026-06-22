---
name: acp-delegation
description: "Delegate coding tasks to external ACP coding agents (Claude Code, Codex, OpenCode) via Hermes terminal. Covers shared orchestration patterns, then provides per-CLI references for tool-specific flags and behavior."
version: 1.0.0
author: Hermes Agent (consolidated from claude-code + codex + opencode)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, ACP, Delegation, Claude, Codex, OpenCode, Refactoring, Code-Review, PTY]
    related_skills: [hermes-agent, coding-agent-architecture]
---

# ACP Delegation — External Coding Agent Orchestration

Delegate coding tasks to external **ACP (Agent Communication Protocol)** coding agents. Three CLIs are supported — each has its own `references/<cli>.md` with tool-specific flags, but the orchestration pattern is shared.

## Supported CLIs

| CLI | Install | Auth | Reference |
|-----|---------|------|-----------|
| **Claude Code** (Anthropic) | `npm install -g @anthropic-ai/claude-code` | Browser OAuth or `ANTHROPIC_API_KEY` | `references/claude-code.md` |
| **Codex** (OpenAI) | `npm install -g @openai/codex` | `codex auth` or `OPENAI_API_KEY` | `references/codex.md` |
| **OpenCode** (open-source) | `npm i -g opencode-ai` or `brew install anomalyco/tap/opencode` | `opencode auth login` or provider env vars | `references/opencode.md` |

## When to Use

- User asks to build a feature, refactor code, or fix bugs
- User explicitly asks to "use Claude Code" / "use Codex" / "use OpenCode"
- You need an external coding agent to review PRs or batch-fix issues
- The task is long-running and would benefit from an isolated agent

## Before Delegating

Verify the tool is installed and authenticated:

```bash
# Generic check — adapt to the CLI you're using
terminal(command="<cli> --version")
terminal(command="<cli> auth status")
```

Must run inside a **git repository** (required by all three CLIs). For scratch work:
```bash
terminal(command="cd $(mktemp -d) && git init && <cli> exec 'task'", pty=true)
```

## Shared Orchestration Pattern

All three CLIs support two modes. Choose based on the task.

### Mode 1: Print Mode / One-Shot (PREFERRED for most tasks)

One-shot execution that returns the result and exits. No PTY needed (OpenCode's `run` also avoids PTY). Cleanest integration.

```
terminal(command="<cli> <run-command> 'Add retry logic to API calls'", workdir="/path/to/project", timeout=120)
```

**When to use:**
- Bounded coding tasks (fix a bug, add a feature, refactor a file)
- CI/CD automation
- Code reviews against a diff
- Any task where you don't need multi-turn conversation

### Mode 2: Interactive / Background Mode — Multi-Turn Sessions

Open a full conversational session for iterative work. Requires `pty=true` and `background=true`. The key difference from print mode is you can send follow-up prompts.

```
terminal(command="<cli>", workdir="/path/to/project", background=true, pty=true)
# Returns session_id

# Send a task
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up
process(action="submit", session_id="<id>", data="Now add error handling")

# Exit (CLI-specific — check the reference)
process(action="write", session_id="<id>", data="\x03")  # Ctrl+C for most
```

**When to use:**
- Multi-turn iterative work (refactor → review → fix → test cycle)
- Tasks requiring the user's input mid-work
- Exploratory coding sessions

## PR Review Pattern

```
terminal(command="<cli> <review-command>", workdir="/path/to/repo", pty=true)
```

Or pipe a diff for quick review:
```bash
terminal(command="git diff main...HEAD | <cli> -p 'Review this diff for bugs and security issues'", timeout=60)
```

## Parallel Work with Worktrees

For batch issue fixing, use separate git worktrees:

```bash
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

terminal(command="<cli> <run-command> 'Fix issue #78'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="<cli> <run-command> 'Fix issue #99'", workdir="/tmp/issue-99", background=true, pty=true)
```

## Shared Rules

1. **Prefer one-shot mode** for single tasks — cleaner exit, no dialog handling
2. **Always set `workdir`** — keep the agent focused on the right directory
3. **CLI must be in a git repo** — Codex and OpenCode refuse to run outside one
4. **Avoid sharing one workdir across parallel sessions** — use worktrees
5. **Report outcomes** — after the agent finishes, summarize changes, test results, and any remaining risks
6. **Check the per-CLI reference** for CLI-specific flags, dialog handling, and pitfalls

## Pitfalls

- PTY mode is required for interactive sessions with Claude Code and Codex; OpenCode `run` does NOT need pty
- Some CLIs (Codex) have sandbox issues in Hermes gateway contexts — prefer `--sandbox danger-full-access` when needed
- Interactive sessions accumulate costs — use `--max-turns` where available in print mode
- PATH mismatch can select the wrong binary — use `which -a <cli>` to verify
