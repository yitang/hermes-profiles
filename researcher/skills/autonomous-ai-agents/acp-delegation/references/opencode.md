# OpenCode — CLI-Specific Reference

## Installation & Auth

```bash
npm i -g opencode-ai@latest
# or brew install anomalyco/tap/opencode
opencode auth login          # Configure provider
opencode auth list           # Verify providers configured
```

## One-Shot Tasks (`opencode run`) — No PTY needed

```bash
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach context files:
```bash
terminal(command="opencode run 'Review config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

Show model thinking:
```bash
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

Force a specific model:
```bash
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## Interactive Sessions (Background PTY)

For iterative multi-turn work:

```bash
terminal(command="opencode", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow")
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")
# Exit — Ctrl+C (NOT /exit!)
process(action="write", session_id="<id>", data="\x03")
```

**Important:** `/exit` is NOT valid — it opens an agent selector. Use Ctrl+C or `kill`.

### TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit message (press twice if needed) |
| `Tab` | Switch agents (build/plan) |
| `Ctrl+P` | Command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+C` | Exit OpenCode |

### Resuming Sessions

```bash
opencode -c                           # Continue last session
opencode -s ses_abc123                # Continue specific session
```

## Common Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue last session |
| `--session <id>` / `-s` | Continue specific session |
| `--agent <name>` | Choose agent (build or plan) |
| `--model provider/model` | Force specific model |
| `--format json` | Machine-readable output |
| `--file <path>` / `-f` | Attach file(s) |
| `--thinking` | Show model thinking blocks |
| `--variant <level>` | Reasoning effort (high, max, minimal) |

## PR Review

```bash
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Or diff-based review:
```bash
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main' -f $(git diff origin/main --name-only | head -20)", pty=true)
```

## Session & Cost Management

```bash
opencode session list        # List past sessions
opencode stats               # Token usage and costs
opencode stats --days 7 --models anthropic/claude-sonnet-4
```

## Pitfalls

1. Interactive TUI requires `pty=true`; `opencode run` does NOT need pty
2. `/exit` is NOT valid — use Ctrl+C
3. Enter may need to be pressed twice in TUI
4. PATH mismatch — use `which -a opencode` to check
5. Avoid sharing one workdir across parallel sessions
