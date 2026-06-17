#!/Users/yitang/.hermes/profiles/coder/venv/bin/python3
"""Cross-reference Hermes activity with TRX4 power draw.

Usage: python3 cross-reference-power-and-sessions.py

Outputs: data/trx4_vs_hermes_hourly.csv with columns:
  day, hour, trx4_w, trx4_state, hermes_msgs

Requires:
- ~/dev/llm_local_vs_cloud/raw/state.db (Hermes sessions from other machine)
- ~/.hermes/profiles/coder/data/tapo-power.db (power samples)
"""

import sqlite3
import csv
import os

HERMES_DB = os.path.expanduser("~/dev/llm_local_vs_cloud/raw/state.db")
POWER_DB = os.path.expanduser("~/.hermes/profiles/coder/data/tapo-power.db")
OUTPUT = os.path.expanduser("~/dev/llm_local_vs_cloud/data")
os.makedirs(OUTPUT, exist_ok=True)

conn = sqlite3.connect(HERMES_DB)
cur = conn.cursor()
cur.execute("""
    SELECT DATE(timestamp, 'unixepoch') as day,
           STRFTIME('%H', timestamp, 'unixepoch') as hour,
           COUNT(*) as assistant_msgs
    FROM messages
    WHERE role = 'assistant'
      AND timestamp >= strftime('%s', '2026-06-11')
      AND timestamp < strftime('%s', '2026-06-17')
    GROUP BY day, hour
    ORDER BY day, hour
""")
hermes_rows = cur.fetchall()
conn.close()

conn = sqlite3.connect(POWER_DB)
cur = conn.cursor()
cur.execute("""
    SELECT SUBSTR(timestamp,1,10) as day,
           SUBSTR(timestamp,12,2) as hour,
           ROUND(AVG(power_w)) as avg_w,
           CASE WHEN AVG(power_w) > 350 THEN 'busy'
                WHEN AVG(power_w) > 10 THEN 'idle'
                ELSE 'off' END as state
    FROM power_samples
    WHERE device = 'TRX4'
      AND timestamp >= '2026-06-11' AND timestamp < '2026-06-17'
      AND timestamp LIKE '%:00:00' AND SUBSTR(timestamp,15,2) = '00'
      AND power_w IS NOT NULL
    GROUP BY day, hour
    ORDER BY day, hour
""")
power_rows = cur.fetchall()
conn.close()

hermes_lookup = {(d, h): c for d, h, c in hermes_rows}
merged = [(d, h, w, s, hermes_lookup.get((d, h), 0)) for d, h, w, s in power_rows]

path = os.path.join(OUTPUT, "trx4_vs_hermes_hourly.csv")
with open(path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["day", "hour", "trx4_w", "trx4_state", "hermes_msgs"])
    w.writerows(merged)

print(f"{path}: {len(merged)} rows")

busy_msgs = sum(r[4] for r in merged if r[3] == "busy")
idle_msgs = sum(r[4] for r in merged if r[3] == "idle")
off_msgs  = sum(r[4] for r in merged if r[3] == "off")
total = busy_msgs + idle_msgs + off_msgs
print(f"\nHermes vs TRX4 state:")
print(f"  While busy: {busy_msgs:4d} ({busy_msgs*100//total}%)")
print(f"  While idle: {idle_msgs:4d} ({idle_msgs*100//total}%)")
print(f"  While off:  {off_msgs:4d} ({off_msgs*100//total}%)")
