# Codex (OpenAI) — CLI-Specific Reference

## Installation & Auth

```bash
npm install -g @openai/codex
# Auth: either OPENAI_API_KEY or Codex OAuth credentials
```

**Must run inside a git repository** — Codex refuses to run outside one.

## One-Shot Tasks

```bash
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work:
```bash
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

**Always use `pty=true`** — Codex is an interactive terminal app.

## Background Mode (Long Tasks)

```bash
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Monitor
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")
process(action="submit", session_id="<id>", data="yes")
process(action="kill", session_id="<id>")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed, auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |
| `--sandbox danger-full-access` | No sandbox; use when bubblewrap fails in gateway context |

## Hermes Gateway Caveat

When running from a Hermes gateway context (e.g., Telegram-driven sessions), Codex sandboxing may fail with bubblewrap errors. Prefer:
```bash
codex exec --sandbox danger-full-access "<task>"
```

## PR Reviews

```bash
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```bash
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="codex --yolo exec 'Fix issue #78'", workdir="/tmp/issue-78", background=true, pty=true)
```

## Rules

1. Always use `pty=true` — Codex hangs without PTY
2. Git repo required — `mktemp -d && git init` for scratch
3. Use `exec` for one-shots; `--full-auto` for building
4. Background for long tasks; monitor with `poll`/`log`
5. Parallel is fine — run multiple Codex processes at once
