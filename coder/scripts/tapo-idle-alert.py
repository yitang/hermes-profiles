#!/Users/yitang/.hermes/profiles/coder/venv/bin/python3
"""Alert if TRX4 has been idle (power < 150W) for >2h during working hours.

Reads from the same SQLite DB as tapo-log.py.
Silent (no output) when all is normal — only prints alert when triggered.
"""
import sys
import site
import os

# Ensure the venv's site-packages are available (cron uses a different Python)
VENV_SITE = os.path.expanduser("~/.hermes/profiles/coder/venv/lib/python3.14/site-packages")
if os.path.isdir(VENV_SITE):
    site.addsitedir(VENV_SITE)
    if VENV_SITE not in sys.path:
        sys.path.insert(0, VENV_SITE)

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROFILE_DIR / "data" / "tapo-power.db"

# TRX4 IP
TRX4_IP = "192.168.1.239"

# Thresholds
IDLE_POWER_THRESHOLD = 150  # watts — below this = idle
WORKING_HOURS_START = 8     # 8am
WORKING_HOURS_END = 21      # 9pm
IDLE_WARN_MINUTES = 120     # alert if idle this long


def load_env():
    env_file = PROFILE_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


def main():
    load_env()
    now = datetime.now()
    hour = now.hour

    # Only check during working hours
    if hour < WORKING_HOURS_START or hour >= WORKING_HOURS_END:
        return  # silent outside working hours

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Get recent samples (last 2.5 hours = 10 samples at 15-min intervals)
    cutoff = (now - timedelta(hours=2.5)).isoformat()
    cursor.execute("""
        SELECT timestamp, power_w
        FROM power_samples
        WHERE ip = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (TRX4_IP, cutoff))

    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 4:  # not enough data yet
        return

    # Check if all recent samples are idle
    idle_count = sum(1 for _, pw in rows if pw is not None and pw < IDLE_POWER_THRESHOLD)
    total_samples = len(rows)

    if idle_count == total_samples:
        # All recent samples show idle — TRX4 has been off/inactive
        last_seen = rows[0][0]
        first_idle = rows[-1][0]
        duration_min = int((now - datetime.fromisoformat(first_idle)).total_seconds() / 60)

        if duration_min >= IDLE_WARN_MINUTES:
            print(f"⚠️  TRX4 idle alert")
            print(f"Idle since {first_idle[:16]}")
            print(f"~{duration_min} min of low power (<{IDLE_POWER_THRESHOLD}W)")
            print(f"Latest reading: {rows[0][1]}W at {last_seen[:16]}")
            print(f"Waste so far: ~£{duration_min / 60 * 0.15:.2f}")


if __name__ == "__main__":
    main()
