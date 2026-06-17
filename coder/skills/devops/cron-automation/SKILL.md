---
name: cron-automation
description: >-
  Build Hermes cron jobs for automated data collection, polling, monitoring,
  and alerting. Covers no_agent script patterns, shell wrapper workaround
  for PEP 668 / uv Python mismatch, SQLite logging, credential management
  via .env, gateway setup, and output conventions.
---

# Cron Automation

## Overview

Hermes cron jobs can run scripts on a schedule without LLM inference
(no_agent mode). This skill covers the full lifecycle: writing the script,
setting up dependencies, registering the cron, and handling output.

## Architecture

```
script.py (or .sh wrapper) → no_agent cron → stdout → delivered to user
                                        ↓
                                   SQLite DB (local)
```

Silent on success, noisy on failure — the default no_agent contract.

## Script Structure

### No-Agent Script Requirements

- **Exit code:** 0 = success, non-zero = error (error output delivered)
- **Stdout:** non-empty = delivered to user; empty = silent (nothing sent)
- **Stderr:** captured on error, sent with failure notification
- **Shebang:** `/Users/yitang/.hermes/profiles/coder/venv/bin/python3`
  (but see Shell Wrapper below)

### Shell Wrapper Pattern (Mandatory for venv deps)

Hermes cron's no_agent mode runs scripts with its own Python 3.11 (uv-managed).
If your script depends on packages only available in the profile's dedicated
venv (Python 3.14), the C extensions won't load and the script fails with
`ModuleNotFoundError` or `symbol not found in flat namespace`.

**Fix:** Create a `.sh` wrapper that explicitly calls the venv Python:

```bash
#!/bin/bash
exec /Users/yitang/.hermes/profiles/coder/venv/bin/python3 \
    /Users/yitang/.hermes/profiles/coder/scripts/your-script.py "$@"
```

Register the cron with `script: your-script.sh` (not the `.py` directly).

Make sure it's executable: `chmod +x scripts/your-script.sh`

### Credential Loading

Put credentials in the profile root `.env` file as `KEY=VALUE` pairs.
The script reads them with:

```python
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

def load_env():
    if not ENV_FILE.exists():
        print("ERROR: .env not found", file=sys.stderr); sys.exit(1)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())
```

### SQLite Storage

Best practice for persistent data:

```python
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "my-stats.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("CREATE TABLE IF NOT EXISTS samples (...)")
    return conn
```

DB files live at `~/.hermes/profiles/coder/data/<name>.db`.

## Cron Registration

### Create

```bash
hermes cron create \
  --name "my-job" \
  --schedule "*/15 * * * *" \
  --script my-script.sh \
  --no-agent
```

`--script` resolves relative to `~/.hermes/profiles/coder/scripts/`.

### Schedule formats

| Example | Meaning |
|---------|---------|
| `*/15 * * * *` | Every 15 minutes |
| `0 9 * * *` | Daily at 9am |
| `*/30 8-21 * * *` | Every 30 min, 8am-9pm |

### Deliver

- **Omit** `--deliver` → auto-delivers to current chat (default)
- `--deliver origin` → deliver to origin chat
- `--deliver local` → local only, no delivery (use for silent loggers)

### Update

```bash
hermes cron update <job-id> --script new-script.sh
```

### Test-run

```bash
hermes cron tick    # Run all due jobs once
```

### List / Status

```bash
hermes cron list
hermes cron status  # Shows if gateway/scheduler is running
```

## Gateway / Scheduler

Cron jobs require the Hermes gateway to be running as a background service:

```bash
hermes gateway install      # Install launchd service (macOS)
hermes gateway restart      # Restart the service
hermes gateway run --force  # Run in foreground (bypass launchd)
```

**Troubleshooting:** If `hermes gateway install` creates a plist that crashes
with "Profile 'coder' does not exist" — this is a known issue with symlinked
`~/.hermes/profiles` directories. Workaround: `hermes gateway run --force`
in a background terminal.

Check gateway logs:
```bash
cat ~/.hermes/profiles/coder/logs/gateway.log
cat ~/.hermes/profiles/coder/logs/gateway.error.log
```

## Output Convention

### Silent Logger (deliver: local, no stdout)

- Script: no_agent with `deliver: local`
- Stdout: **must be empty** — print() in the script produces output that gets saved locally
- Use `sys.stderr` for debug logging when you need it
- Never spams the user

**Important:** In no_agent mode, `deliver: local` prevents delivery even if the script produces stdout, but the output is still saved to `~/.hermes/profiles/coder/cron/output/<job-id>/`. If you truly want nothing stored, ensure the script produces no stdout at all. The typical pattern is to write to SQLite and never call `print()`.

### Periodic Summary (scheduled delivery)
- Script: no_agent with `deliver: origin`
- Stdout: concise report (kWh, costs, alerts)
- Only non-empty output is delivered

### Alert Script (conditional delivery)
- Script: no_agent with `deliver: origin`
- Stdout: empty when OK, non-empty only when alert condition met
- This is the default no_agent behaviour — empty stdout = silent

## Sample: Minimal Logger

```python
#!/usr/bin/env python3
import sqlite3, json, os
from pathlib import Path
from datetime import datetime

DB = Path.home() / ".hermes" / "profiles" / "coder" / "data" / "sensor.db"
DB.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(str(DB))
conn.execute("""CREATE TABLE IF NOT EXISTS readings (
    ts TEXT, sensor TEXT, value REAL
)""")

value = 42.0  # replace with actual reading
conn.execute("INSERT INTO readings VALUES (?, ?, ?)",
             (datetime.now().isoformat(), "temp", value))
conn.commit()
conn.close()
# No print() = silent
```

## Pitfalls

- **PEP 668 + uv Python mismatch** — macOS/uv Python 3.11 can't load venv's
  Python 3.14 C extensions. Always use the shell wrapper pattern above.
- **Python version mismatch** — cron uses `~/.local/share/uv/python/cpython-3.11.15-.../bin/python3`,
  not the venv python. Pure Python packages load fine from venv's site-packages,
  but compiled C extensions (cryptography, numpy) will crash with ABI errors.
  Shell wrapper is the only reliable fix.
- **Rate limiting** — devices like Tapo P110 have per-connection auth rate limits
  (~1 connection per 30s minimum). Cron's 15-min intervals stay well clear.
- **aiohttp unclosed sessions** — `Device.connect()` creates internal aiohttp
  sessions. They produce warnings but don't affect functionality in cron.
- **Gateway not running** — cron jobs won't fire unless the gateway is active.
  Always verify with `hermes cron status`.
- **Launchd plist with symlinked profiles** — `hermes gateway install` sets
  `HERMES_HOME` to the symlink target, which can confuse profile resolution.
  Use `hermes gateway run --force` as fallback.
- **Rich/terminal color detection on Raspberry Pi 4** — when running Hermes on
  a Pi (aarch64 Debian Bookworm), `rich.Console().color_system` may return
  `None` even with `TERM=xterm-256color`. The terminal works fine but colours
  render oddly. Fix: `export RICH_FORCE_COLORS=true` or `export
  FORCE_COLOR=1` before starting Hermes. Or set permanently in `.bashrc`.
  Underlying cause: Rich's terminal detection falls through on some ARM Linux
  configurations despite proper terminfo files being present. Setting
  `RICH_FORCE_COLORS=true` bypasses the detection entirely.
  See `references/rp4-hermes-setup.md` for the full installation guide.
- **python-kasa auth failure on ARM Linux (Raspberry Pi 4)** — The same
  python-kasa version (0.10.2) that works on macOS consistently fails with
  `LOGIN_ERROR(-1501)` on Raspberry Pi 4 running Debian 12 Bookworm (Python
  3.11, aarch64), even with correct Tapo credentials. The device is reachable
  (port 80 responds HTTP 200, ping works, UDP discovery finds it) but the
  AES transport handshake fails with `LOGIN_ERROR(-1501)` on every P110 device
  tested. KLAP encryption also fails (gets HTML response instead of
  handshake data). **Root cause unknown** — possibly a cryptography library
  ABI mismatch on ARM, a device-side MAC-based auth cache, or an ARM-specific
  timing issue in the AES handshake. Workaround: run Tapo polling from a
  different machine that already authenticates successfully.

## References

- `references/tapo-p110-integration.md` — Tapo P110 python-kasa details
- `references/rp4-hermes-setup.md` — Full Hermes installation guide for Raspberry Pi 4 (aarch64 Debian)

## Historical backfill

A cron pipeline captures data forward-only. To backfill missing data before the cron was set up:

1. Export from the source app (Tapo, Home Assistant, etc.)
2. Write a one-shot import script that reads the export format and inserts into the same SQLite DB
3. Deduplicate by checking timestamp prefixes (`LIKE 'YYYY-MM-DDTHH%'`)
4. Map device IDs/labels to match the cron's DB schema

See `devops/cron-data-pipeline` for a worked example with Tapo P110 XLS exports.
