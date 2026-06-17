#!/Users/yitang/.hermes/profiles/coder/venv/bin/python3
"""Print daily power summary for all monitored devices.

Reads from the same SQLite DB as tapo-log.py.
Designed for cron (no_agent mode): output is the report itself.
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
from collections import defaultdict

PROFILE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROFILE_DIR / "data" / "tapo-power.db"

# UK electricity rate (can be overridden via env var)
GBP_PER_KWH = float(os.environ.get("UK_ELECTRICITY_RATE", "0.25"))


def load_env():
    """Load KEY=VALUE from profile .env for potential future config vars."""
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
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    # Get unique devices
    cursor.execute("SELECT DISTINCT ip, device, model FROM power_samples")
    devices = cursor.fetchall()

    lines = []
    total_kwh = 0
    total_cost_gbp = 0

    for ip, name, model in devices:
        label = f"{name} ({ip})" if name != ip else ip

        cursor.execute("""
            SELECT
                COUNT(*) as samples,
                ROUND(AVG(power_w), 1) as avg_w,
                ROUND(MAX(power_w), 1) as max_w,
                ROUND(MIN(power_w), 1) as min_w,
                ROUND(MAX(total_wh) - MIN(total_wh), 0) as delta_wh
            FROM power_samples
            WHERE ip = ? AND timestamp >= ?
        """, (ip, yesterday))

        row = cursor.fetchone()
        if not row or row[0] < 2:
            lines.append(f"  {label}: insufficient data")
            continue

        samples, avg_w, max_w, min_w, delta_wh = row
        kwh = delta_wh / 1000.0 if delta_wh and delta_wh > 0 else 0
        cost = round(kwh * GBP_PER_KWH, 2)
        total_kwh += kwh
        total_cost_gbp += cost

        # Estimate idle vs load (threshold: 100W = anything above is active)
        cursor.execute("""
            SELECT COUNT(*) FROM power_samples
            WHERE ip = ? AND timestamp >= ? AND power_w > 200
        """, (ip, yesterday))
        loaded_samples = cursor.fetchone()[0] or 0
        loaded_pct = round(loaded_samples / max(samples, 1) * 100)

        lines.append(f"  {label}")
        lines.append(f"    Avg {avg_w}W | Max {max_w}W | Min {min_w}W")
        lines.append(f"    {kwh:.1f} kWh @ £{cost}")
        lines.append(f"    >200W: {loaded_pct}% of samples")

    conn.close()

    # Build report
    total_cost_cny = round(total_cost_gbp * 9.3, 1)
    print(f"⚡ Power Report — {yesterday}")
    print(f"Devices: {len(devices)}")
    for l in lines:
        print(l)
    print(f"---")
    print(f"Total: {total_kwh:.1f} kWh")
    print(f"Cost: £{total_cost_gbp:.2f} / ¥{total_cost_cny}")


if __name__ == "__main__":
    main()
