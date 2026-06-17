---
name: external-coding-agents
description: "Delegate coding to external AI agent CLIs (Claude Code, Codex, OpenCode): one-shot tasks, interactive sessions, PR reviews, parallel work."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude-Code, Codex, OpenCode, Code-Review, Refactoring, PR]
    related_skills: [hermes-agent]
---

# External Coding Agent CLIs

Delegate coding tasks to external autonomous coding agent CLIs. Covers **Claude Code**, **Codex (OpenAI)**, and **OpenCode** — three provider-agnostic coding agents you can orchestrate via Hermes terminal/process tools.

## When to Use

- User explicitly names one of the three CLI tools
- Task is coding-heavy and benefits from a full autonomous agent reading/writing code
- PR review, refactoring, feature implementation, bug fixing at scale

### Tool Selection Guide

| Scenario | Best Choice |
|----------|-------------|
| Most tasks, best overall quality | Claude Code (`claude`) |
| Already have OpenAI key / need Codex workflow | Codex (`codex`) |
| Open-source / provider-agnostic needed | OpenCode (`opencode`) |
| CI automation, structured output | Claude Code print mode (best JSON/schema support) |
| Scratch work without git repo | Codex (supports `mktemp -d && git init` pattern) |

## Shared Patterns

All three agents share these orchestration patterns:

### 1. One-Shot Tasks (preferred for automation)

Run a bounded task and exit when done:

```bash
# Claude Code print mode
claude -p 'Refactor auth module to use JWT' --allowedTools Read,Edit,Bash --max-turns 10

# Codex one-shot
codex exec 'Add dark mode toggle to settings' --full-auto

# OpenCode one-shot
opencode run 'Add retry logic to API calls and update tests'
```

**Always set workdir** to keep the agent focused on the right project. Use `--max-turns` in print mode to prevent runaway costs.

### 2. Interactive Sessions (multi-turn iteration)

For tasks requiring follow-up prompts, use background PTY sessions:

```bash
# Claude Code via tmux
tmux new-session -d -s claude-work -x 140 -y 40 && \
tmux send-keys -t claude-work "cd /path/to/project && claude" Enter

# Codex with PTY
terminal(command="codex", workdir="/path/to/project", background=true, pty=true)

# OpenCode with PTY
terminal(command="opencode", workdir="/path/to/project", background=true, pty=true)
```

Monitor progress: `process(action="poll")` / `process(action="log")`

### 3. Parallel Work

Run multiple coding agents simultaneously in isolated workdirs or git worktrees:

```bash
# Create parallel worktrees
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main

# Launch agents in each (independently)
terminal(command="claude -p 'Fix issue #78' --max-turns 10", workdir="/tmp/issue-78")
terminal(command="codex exec 'Fix issue #99' --full-auto", workdir="/tmp/issue-99", pty=true)

# Monitor all with process(action="list")
```

### 4. PR Review Pattern

All three support PR review via diff or PR number:

```bash
# Claude Code: review a diff
git diff main...feature-branch | claude -p 'Review this diff for bugs, security issues, and style problems.' --max-turns 1

# Codex: review PR from number
codex exec 'Review PR #42' --from-pr 42 --base origin/main

# OpenCode: built-in PR command
opencode pr 42
```

### 5. Session Management

All three support session resumption:

```bash
# Claude Code: resume most recent or specific ID
claude -p 'Continue work' --continue --max-turns 5
claude -p 'Continue work' --resume <session_id> --fork-session --max-turns 5

# Codex: continues session automatically when run in same directory

# OpenCode: list sessions, continue specific one
opencode session list
opencode -c  # continue last
opencode -s ses_abc123  # specific session
```

### 6. Context & Configuration Files

All three use project-level configuration files:

| Agent | Project Config | User Config | Auto-Memory |
|-------|---------------|-------------|-------------|
| Claude Code | `.claude/settings.json` | `~/.claude/settings.json` | `~/.claude/projects/<proj>/memory/` |
| Codex | `.codex/settings.json` (if any) | `~/.codex/auth.json` | N/A |
| OpenCode | N/A | Provider env vars | Session-based via `-c` flag |

Use project config to persist rules, allowed tools, MCP servers, etc.

### 7. Safety & Permission Controls

All three have permission/whitelist mechanisms:

```bash
# Claude Code: restrict tools
claude -p 'task' --allowedTools "Read,Bash(git *)" --dangerously-skip-permissions

# Codex: sandbox levels
codex exec 'task' --full-auto   # auto-approve in workspace
codex exec 'task' --yolo        # no sandbox, no approvals

# OpenCode: model-level safety is default; use --variant high for careful reasoning
```

**Best practice**: Use `--allowedTools` (Claude Code) or `--full-auto` (Codex) to minimize approval friction. Always verify output afterwards — autonomous agents may introduce bugs.

## Verification Checklist

After any coding agent completes:

- [ ] Review `git diff` for correctness
- [ ] Run project tests / linting
- [ ] Check that the agent didn't modify files it shouldn't have
- [ ] Confirm commit history is clean (agent should not leave uncommitted mess)

---

## Labeled Subsections: Individual Tool Reference

### Claude Code (`claude`) — Detailed CLI Reference

**Install:** `npm install -g @anthropic-ai/claude-code`

**Auth:** `claude auth login --console` (OAuth) or set `ANTHROPIC_API_KEY`

#### Print Mode (one-shot, preferred for automation)
```bash
claude -p 'task description' --allowedTools "Read,Edit" --max-turns 10
# Returns JSON with session_id, num_turns, cost, stop_reason
```

Key flags: `--output-format json|stream-json`, `--json-schema <schema>`, `--bare` (skip hooks/plugins), `--fallback-model haiku`

#### Interactive Mode (tmux orchestration)
- Requires tmux for reliable session management
- First launch shows two dialogs: workspace trust (Enter = Yes) and permissions (Down+Enter = accept)
- Monitor with `tmux capture-pane -t <session> -p -S -50`
- Look for `❯` prompt to know when Claude is waiting

#### Context Files
- `CLAUDE.md` at project root — auto-loaded by every session
- `.claude/rules/*.md` — modular rules (one per .md file)
- `~/.claude/CLAUDE.md` — global, applies to all projects

#### Cost Management
- Use `--max-turns 5-10` for bounded tasks
- Use `--max-budget-usd` for cost caps (minimum ~$0.05 for cache creation)
- Use `--effort low` for simple tasks; `high`/`max` for complex reasoning
- Pipe input instead of reading files when you just need analysis

#### Pitfalls
1. Interactive mode REQUIRES tmux — Claude Code is a TUI app
2. Permissions dialog defaults to "No, exit" — send Down then Enter
3. Trust dialog only appears once per directory
4. Session resumption requires same working directory
5. Context degradation above 70% — use `/compact` proactively

### Codex (`codex`) — Detailed CLI Reference

**Install:** `npm install -g @openai/codex`

**Auth:** `OPENAI_API_KEY` env var or Codex OAuth from login flow

#### Key Flags
| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot, exits when done |
| `--full-auto` | Auto-approve file changes in sandbox |
| `--yolo` | No sandbox, no approvals |
| `--sandbox danger-full-access` | Disables bubblewrap sandbox (for gateway/container contexts) |

#### Requirements
- **Must run inside a git repo** — Codex refuses outside one
- Always use `pty=true` in Hermes terminal calls — it's an interactive TUI app
- For scratch work: `mktemp -d && git init && codex exec 'task'`

#### Gateway/CX Context Pitfall
In gateway/service contexts, bubblewrap user-namespace errors may occur. Use:
```bash
codex exec --sandbox danger-full-access "task"
```

### OpenCode (`opencode`) — Detailed CLI Reference

**Install:** `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`

**Auth:** `opencode auth login` or set provider env vars (OPENROUTER_API_KEY, etc.)

#### Key Commands
| Command | Effect |
|---------|--------|
| `opencode run 'prompt'` | One-shot execution and exit |
| `-f <file>` | Attach context file(s) |
| `--thinking` | Show model thinking blocks |
| `--model provider/model` | Force specific model |

#### Interactive Mode (TUI, background + PTY)
- Ctrl+C to exit (NOT `/exit` — that opens agent selector!)
- Enter may need to be pressed twice to submit in TUI
- Use `process(action="submit")` for answering questions
- Resuming: `opencode -c` or `-s ses_abc123`

#### Binary Resolution Pitfall
Different PATH resolutions may find different OpenCode binaries. Pin explicitly if needed:
```bash
$HOME/.opencode/bin/opencode run 'task'
```

#### Verification
Smoke test: `opencode run "Respond with exactly: OPENCODE_SMOKE_OK"`

---

## Related Skills

- **hermes-agent** — Configure Hermes itself to use these agents (model providers, etc.)
- **github-pr-workflow** — Create PRs after agent commits changes