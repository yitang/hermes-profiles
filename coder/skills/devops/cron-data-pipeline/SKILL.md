---
name: cron-data-pipeline
description: "Set up automated data collection pipelines using Hermes cron jobs: poll IoT/smart-home devices via local Python scripts, log to SQLite, generate daily summaries, and fire idle-waste alerts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [cron, data-collection, iot, monitoring, sqlite, tapo, power-monitoring]
    related_skills: [software-development/plan]
---

# Cron Data Pipeline

## When to use

The user wants to automatically collect, store, and report data from a local device or API — power monitoring, temperature sensors, disk usage, service health, financial data, etc. The result is a repeatable pipeline: poll → store → summarize → alert.

## Architecture pattern

```
cronjob (--no-agent --script)
    │
    ▼
Python script (specialised venv)
    │
    ├── reads .env for secrets
    ├── polls device(s) via local protocol
    └── writes to SQLite DB
          │
          ├── daily summary cron (second job)
          └── idle/alert cron (third job)
```

## Step-by-step

### 1. Set up the script environment

On macOS 3.14+: PEP 668 blocks system-wide pip. Create a dedicated venv:

```bash
python3 -m venv ~/.hermes/profiles/<profile>/venv
~/.hermes/profiles/<profile>/venv/bin/pip install <dependencies>
```

Scripts directory (auto-resolved by Hermes cron):

```bash
mkdir -p ~/.hermes/profiles/<profile>/scripts
mkdir -p ~/.hermes/profiles/<profile>/data
```

### 2. Write the poll script

Place at `~/.hermes/profiles/<profile>/scripts/<name>.py`.

Key conventions for `--no-agent` cron scripts:
- **stdout**: normal output (JSON or summary). Non-empty stdout is delivered to the user.
- **stderr**: error messages only. Write to `sys.stderr` so cron can signal failures.
- **Exit codes**: 0 = success, non-zero = error (triggers Hermes alert).
- **Secrets**: read from `~/.hermes/profiles/<profile>/.env` using `os.environ.get()`.
- **Data directory**: `~/.hermes/profiles/<profile>/data/` for SQLite DBs.

Always prefix the script shebang with the venv python path:

```python
#!/usr/bin/env python3
```

**Crucially, Hermes cron's `--no-agent` mode does NOT honour the script's shebang.** It runs the script with Hermes' own Python (uv-managed, often 3.11), which won't have venv-only dependencies. **Use a shell wrapper instead:**

Create a `.sh` file alongside the `.py` script:

```bash
#!/bin/bash
exec /path/to/profile/venv/bin/python3 /path/to/profile/scripts/script.py "$@"
```

Make it executable and point the cron at the `.sh` wrapper:

```bash
chmod +x ~/.hermes/profiles/<profile>/scripts/<name>.sh
hermes cron create --name "<job>" --schedule "*/15 * * * *" \
  --script ~/.hermes/profiles/<profile>/scripts/<name>.sh --no-agent
```

This forces the script to run against the correct Python with all dependencies.

### 3. Register the poll cron (no-agent mode)

```bash
hermes cron create --name "<job-name>" --schedule "*/15 * * * *" \
  --script ~/.hermes/profiles/<profile>/scripts/<script>.py --no-agent
### 3. Register the poll cron (no-agent mode)

**⛔ Version note: CLI syntax differs between Hermes versions.**

On Hermes v0.16.0 and later, `--schedule` is NOT a valid flag. The schedule expression is a **positional argument** at the end:

```bash
hermes cron create --name "<job>" "*/15 * * * *" --script <script> --no-agent
```

On earlier versions, `--schedule` IS a flag:

```bash
hermes cron create --name "<job>" --schedule "*/15 * * * *" --script <script> --no-agent
```

Check which syntax your Hermes version expects:
```bash
hermes cron create --help | grep schedule
# If it shows --schedule, use flag syntax
# If schedule is listed under "positional arguments", use positional syntax
```

`--no-agent` means: run the script directly, skip the LLM. The script's stdout becomes the delivered message. Empty stdout = silent (nothing sent to user). This is ideal for routine polls where only anomalies should produce output.

### 4. Write summary / alert scripts (additional cron jobs)

- **Daily summary**: `--schedule "0 9 * * *"` — query the DB, compute averages/totals/costs, print human-readable report.
- **Idle alert**: every 30m during working hours — check recent samples, if all below a threshold for N consecutive samples, fire a notification.

Both use the same SQLite DB as the poll script, so they're trivially decoupled.

### 5. Test the pipeline

```bash
# Test poll script directly
~/.hermes/profiles/<profile>/venv/bin/python3 ~/.hermes/profiles/<profile>/scripts/<poll>.py

# Check DB has data
sqlite3 ~/.hermes/profiles/<profile>/data/<db>.db "SELECT COUNT(*) FROM samples;"

# Test run the cron immediately
hermes cron run <job-name>

# List active jobs
hermes cron list
```

## Tapo P110 specifics

See `references/tapo-p110-power-monitoring.md` for device-specific details: discovery, authentication, emeter fields, and troubleshooting.

## SQLite schema template

Use a lightweight schema with no foreign keys (polling contexts don't need them):

```sql
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device TEXT NOT NULL,
    field1 REAL,
    field2 REAL,
    field3 REAL
);
CREATE INDEX IF NOT EXISTS idx_ts ON samples(timestamp);
CREATE INDEX IF NOT EXISTS idx_device ON samples(device);
```

## 6. (Optional) Historical import from Tapo app exports

After the cron pipeline is running, you can backfill historical data by exporting from the Tapo app:

1. Tapo app → Device → Settings → Energy Monitoring → Export Data
2. This produces `.xls` files per device (Power.xls + Energy Usage.xls)
3. Save to a local directory
4. Run an import script that reads the XLS files and inserts into the same SQLite DB

The import script needs `xlrd` to parse `.xls` files:

```bash
~/.hermes/profiles/<profile>/venv/bin/pip install xlrd
```

**File-to-device mapping**: The Tapo app doesn't embed device names in the export filenames. Map by power signature:
- High power bursts (400-800W) = desktop/server
- Moderate (70-200W) = workstation  
- Consistent low (6-10W) = router/pi

Hardcode the mapping in a `DEVICE_LABELS` dict for reliability — the Tapo app's device aliases may not reflect physical identities.

See `references/tapo-p110-power-monitoring.md` for detailed export format.

## Pitfalls

- **Python environment mismatch (critical)** — cron `--no-agent` mode ignores the shebang line and runs scripts with Hermes' uv-managed Python (often 3.11). Dependencies installed in a profile venv (Python 3.14+) won't be available. Use a shell wrapper `.sh` that explicitly calls the venv python. See the shell wrapper pattern above.
- **PEP 668 on macOS**: always install dependencies in a profile venv, not system python. System pip will be blocked.
- **Gateway not running** — cron jobs won't fire unless the Hermes gateway is active. Check with `hermes cron status`. On macOS, install as launchd service: `hermes gateway install` (or use `hermes gateway run --force` for foreground mode).
- **Gateway profile resolution with symlinked profiles** — if `~/.hermes/profiles` is a symlink (e.g. to a git repo), the launchd gateway service may fail with "Profile 'X' does not exist." Use `hermes gateway run --force` in a terminal session as a workaround, or verify the plist's WorkingDirectory and HERMES_HOME point to the resolved path.
- **Tapo authentication**: requires Tapo app credentials (email + password) in `.env`, NOT just local device creds. Incorrect creds give LOGIN_ERROR(-1501).
- **Discovery reliability**: UDP broadcast discovery may fail across VLANs or bridges. Fallback: use direct IP connection.
- **PSU efficiency at low load**: desktop PSUs are inefficient below ~20% load. A 1000W PSU at 150W system idle may waste 20-30W as heat. Consider this in cost estimates.
- **SQLite concurrency**: at 15-min intervals, no contention risk. For sub-minute polling, use WAL mode (`PRAGMA journal_mode=WAL`).
- **Time zones**: store UTC in DB; convert on display in summary scripts.
