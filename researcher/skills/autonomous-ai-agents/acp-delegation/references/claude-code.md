# Claude Code — CLI-Specific Reference

## Installation & Auth

```bash
npm install -g @anthropic-ai/claude-code
claude          # Run once to log in (browser OAuth for Pro/Max)
claude auth login --console   # API key billing
claude auth login --sso       # Enterprise SSO
claude auth status            # JSON; add --text for human-readable
claude doctor                 # Health check
claude --version              # Requires v2.x+
```

## Print Mode (`-p`) — No PTY Needed

```
terminal(command="claude -p 'Add error handling to all API calls' --allowedTools 'Read,Edit' --max-turns 10", workdir="/project", timeout=120)
```

### Key Flags

| Flag | Purpose |
|------|---------|
| `-p "task"` | Print mode (non-interactive) |
| `--max-turns <n>` | Cap agentic loops (print mode only) |
| `--max-budget-usd <n>` | Cap API spend |
| `--allowedTools "Read,Edit"` | Whitelist tools |
| `--output-format json` | Structured JSON result (has session_id, cost, usage) |
| `--json-schema "..."` | Force structured output matching a schema |
| `--bare` | Fastest startup (skip hooks, plugins, MCP, CLAUDE.md) |
| `--fallback-model haiku` | Auto-fallback when overloaded |
| `--model sonnet\|opus\|haiku` | Model selection |

### JSON Output Format

```json
{
  "type": "result",
  "subtype": "success",
  "result": "The analysis text...",
  "session_id": "75e2167f-...",
  "num_turns": 3,
  "total_cost_usd": 0.0787,
  "usage": { "input_tokens": 5, "output_tokens": 603 }
}
```

### Session Continuation
```bash
# Continue most recent session in current dir
claude -p "continue task" --continue
# Resume specific session
claude -p "continue task" --resume <session_id>
# Fork a new session ID from an old one
claude -p "try alternative" --resume <id> --fork-session
```

## Interactive Mode (PTY + tmux)

Claude Code is a full TUI app. Orchestrate with tmux:

```bash
# Start tmux session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")

# Launch Claude Code
terminal(command="tmux send-keys -t claude-work 'cd /project && claude' Enter")

# Handle dialogs
# Dialog 1: Workspace Trust — press Enter (default is "Yes, trust")
terminal(command="sleep 4 && tmux send-keys -t claude-work Enter")
# Dialog 2: Permissions (only with --dangerously-skip-permissions) — Down then Enter
terminal(command="sleep 3 && tmux send-keys -t claude-work Down && sleep 0.3 && tmux send-keys -t claude-work Enter")

# Send task
terminal(command="sleep 2 && tmux send-keys -t claude-work 'Refactor auth to use JWT tokens' Enter")

# Monitor
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -50")

# Exit
terminal(command="tmux send-keys -t claude-work '/exit' Enter")
```

### TUI Status Indicators
- `❯` = waiting for input (Claude done or asking)
- `●` = actively using tools
- `< 70% context` = healthy; `70-85%` = consider `/compact`; `> 85%` = high hallucination risk

### Slash Commands
| Command | Purpose |
|---------|---------|
| `/review` | Code review of current changes |
| `/compact` | Compress context to save tokens |
| `/clear` | Wipe conversation history |
| `/cost` | View token usage breakdown |
| `/model` | Switch models mid-session |
| `/effort` | Set reasoning depth (low/medium/high/max) |
| `/exit` | End session |

## Parallel Claude Instances with tmux

```bash
terminal(command="tmux new-session -d -s task1 -x 140 -y 40 && tmux send-keys -t task1 'cd ~/project && claude -p \"Fix auth bug\" --allowedTools \"Read,Edit\" --max-turns 10' Enter")
terminal(command="tmux new-session -d -s task2 -x 140 -y 40 && tmux send-keys -t task2 'cd ~/project && claude -p \"Write integration tests\" --allowedTools \"Read,Write,Bash\" --max-turns 15' Enter")
```

## CLAUDE.md — Project Context

Claude Code auto-loads `CLAUDE.md` from the project root. Rules directory: `.claude/rules/*.md`.

## Custom Subagents

Define in `.claude/agents/<name>.md`:
```markdown
---
name: security-reviewer
model: opus
---
You are a senior security engineer. Review code for vulnerabilities.
```

## Hooks — Automation on Events

Configure in `.claude/settings.json`:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write(*.py)",
      "hooks": [{"type": "command", "command": "ruff check --fix $CLAUDE_FILE_PATHS"}]
    }]
  }
}
```

## MCP Integration

```bash
claude mcp add -s user github -- npx @modelcontextprotocol/server-github
claude mcp add postgres -- npx @anthropic-ai/server-postgres --connection-string postgresql://localhost/mydb
```

## Cost & Performance Tips

- `--max-turns` in print mode (start with 5-10)
- `--effort low` for simple tasks, `high`/`max` for complex reasoning
- `--bare` for CI (skip plugin/hook discovery)
- `--no-session-persistence` in CI (avoid saved sessions on disk)
- `--fallback-model haiku` to gracefully handle overload
- Use `/compact` when context exceeds 70%

## Pitfalls

1. Interactive mode REQUIRES tmux — `pty=true` alone is insufficient
2. `--dangerously-skip-permissions` dialog defaults to "No" — must send Down then Enter
3. `--max-turns` is print-mode only (ignored in interactive)
4. `--max-budget-usd` minimum is ~$0.05
5. Background tmux sessions persist — clean up with `tmux kill-session -t <name>`
