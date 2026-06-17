# Worked Example: Addressing PR #28840 Review Feedback

This reference documents the exact commands and thought process from addressing
review feedback on PR #28840 (preserve message timestamps through fork/compress/branch).

## Context

- **PR**: https://github.com/NousResearch/hermes-agent/pull/28840
- **Reviewer**: @teknium1
- **Review comment**: https://github.com/NousResearch/hermes-agent/pull/28840#issuecomment-4722970402
- **Fork branch**: `feat/preserve-message-timestamps`

## Review Feedback Summary

1. **Unrelated `.gitignore` hunk** — drop it
2. **Stale call sites** — `cli.py`/`gateway/run.py` hunks target old code; current main has
   branch copy in `hermes_cli/cli_commands_mixin.py` and `gateway/slash_commands.py`
3. **Core approach approved** — `append_message(timestamp=...)` + `replace_messages`
   dict-`get` is the right fix

## Commands Used

### 1. Fetch the review

```bash
web_extract(urls=["https://github.com/...pull/28840#issuecomment-4722970402"])
```

### 2. Clone the fork (not the live install)

```bash
mkdir -p ~/dev
git clone https://github.com/yitang/hermes-agent.git ~/dev/hermes-agent
cd ~/dev/hermes-agent
git checkout feat/preserve-message-timestamps
```

### 3. Add upstream remote and compare

```bash
git remote add upstream https://github.com/NousResearch/hermes-agent.git
git fetch upstream main --depth=10

# Check which PR files already exist on upstream main
git diff upstream/main --stat
# → .gitignore, cli.py, gateway/run.py hunks show as stale

# Check if hermes_state.py timestamp logic is already upstream
git show upstream/main:hermes_state.py | grep -n "timestamp"
# → Already has `timestamp: Any = None` on append_message!
```

### 4. Check moved call sites

```bash
# Find where branch copy code lives now
git show upstream/main:hermes_cli/cli_commands_mixin.py | grep -n "append_message"
git show upstream/main:gateway/slash_commands.py | grep -n "append_message"

# View the exact context
git show upstream/main:hermes_cli/cli_commands_mixin.py | sed -n '870,900p'
```

### 5. Check if the other call sites already forward timestamp

```bash
git show upstream/main:run_agent.py | grep -B2 -A2 "timestamp=msg.get"
# → Already forwarded

git show upstream/main:gateway/session.py | grep -B2 -A2 "timestamp=message.get"
# → Already forwarded
```

### 6. Verify upstream test coverage

```bash
git show upstream/main:tests/test_hermes_state.py | grep -n "timestamp" -i
# → 1 test exists (`test_append_message_accepts_explicit_timestamp`)
# → PR adds 8 richer tests — worth keeping
```

## Outcome

| Hunk | Status |
|------|--------|
| `.gitignore` | Drop (unrelated) |
| `cli.py` | Drop (code moved to `hermes_cli/cli_commands_mixin.py`) |
| `gateway/run.py` | Drop (code moved to `gateway/slash_commands.py`) |
| `hermes_state.py` | Already on main (via different commit `bd7fc8fdc`) |
| `run_agent.py` | Already on main |
| `gateway/session.py` | Already on main |
| `tui_gateway/server.py` | Still missing — keep |
| `gateway/mirror.py` | Not needed (synthetic messages) |
| `tests/test_hermes_state.py` | Keep (8 tests > 1 upstream test) |

**New work needed**: Add `timestamp=msg.get("timestamp")` forwarding at:
- `hermes_cli/cli_commands_mixin.py:884`
- `gateway/slash_commands.py:3051`
