#!/Users/yitang/.hermes/profiles/coder/venv/bin/python3
"""Export TRX4 power data and analysis for the llm_local_vs_cloud report."""

import sqlite3
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

# Paths
OUTPUT = os.path.expanduser("~/dev/llm_local_vs_cloud")
DB = os.path.expanduser("~/.hermes/profiles/coder/data/tapo-power.db")
os.makedirs(OUTPUT, exist_ok=True)

GBP_PER_KWH = 0.25


def query(sql):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows


def write_csv(filename, headers, rows):
    path = os.path.join(OUTPUT, filename)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")
    return path


# ─── 1. Daily totals: last month ───────────────────────────────

rows = query("""
    SELECT SUBSTR(timestamp,1,10) as day,
           ROUND(AVG(power_w) * 24 / 1000, 3) as kwh,
           ROUND(AVG(power_w) * 24 / 1000 * 0.25, 2) as cost_gbp,
           ROUND(AVG(power_w) * 24 / 1000 * 2.3, 2) as cost_cny,
           ROUND(AVG(power_w)) as avg_w,
           COUNT(*) as samples
    FROM power_samples
    WHERE device = 'TRX4'
      AND timestamp >= '2026-05-17' AND timestamp < '2026-06-17'
      AND timestamp LIKE '%:00:00' AND SUBSTR(timestamp,15,2) = '00'
      AND power_w IS NOT NULL
    GROUP BY day ORDER BY day
""")
write_csv("trx4_daily_totals.csv",
          ["date", "kwh", "cost_gbp", "cost_cny", "avg_w", "samples"], rows)

# ─── 2. Hourly breakdown: June 11-16 ──────────────────────────

rows = query("""
    SELECT SUBSTR(timestamp,1,16) as ts,
           ROUND(power_w, 1) as w,
           CASE WHEN power_w < 10 THEN 'off'
                WHEN power_w > 350 THEN 'busy'
                ELSE 'idle' END as state
    FROM power_samples
    WHERE device = 'TRX4'
      AND timestamp >= '2026-06-11' AND timestamp < '2026-06-17'
      AND power_w IS NOT NULL
      AND timestamp LIKE '%:00:00' AND SUBSTR(timestamp,15,2) = '00'
    ORDER BY timestamp
""")
write_csv("trx4_hourly_states.csv",
          ["timestamp", "watts", "state"], rows)

# ─── 3. Busy/idle/off by day (June 11-16) ─────────────────────

rows = query("""
    SELECT SUBSTR(timestamp,1,10) as day,
           SUM(CASE WHEN power_w < 10 THEN 1 ELSE 0 END) as off_h,
           SUM(CASE WHEN power_w BETWEEN 10 AND 350 THEN 1 ELSE 0 END) as idle_h,
           SUM(CASE WHEN power_w > 350 THEN 1 ELSE 0 END) as busy_h,
           ROUND(SUM(CASE WHEN power_w > 350 THEN power_w ELSE 0 END) / 1000.0, 2) as busy_kwh,
           ROUND(SUM(CASE WHEN power_w BETWEEN 10 AND 350 THEN power_w ELSE 0 END) / 1000.0, 2) as idle_kwh,
           ROUND(SUM(CASE WHEN power_w < 10 THEN power_w ELSE 0 END) / 1000.0, 2) as off_kwh,
           ROUND(SUM(power_w) / 1000.0, 2) as total_kwh
    FROM power_samples
    WHERE device = 'TRX4'
      AND timestamp >= '2026-06-11' AND timestamp < '2026-06-17'
      AND power_w IS NOT NULL
      AND timestamp LIKE '%:00:00' AND SUBSTR(timestamp,15,2) = '00'
    GROUP BY day ORDER BY day
""")
write_csv("trx4_daily_breakdown.csv",
          ["date", "off_h", "idle_h", "busy_h",
           "busy_kwh", "idle_kwh", "off_kwh", "total_kwh"], rows)

# ─── 4. All three devices: last month totals ───────────────────

devices = ["TRX4", "B760", "iMac"]
all_rows = []
for dev in devices:
    r = query(f"""
        SELECT ROUND(AVG(power_w) * 24 / 1000, 2),
               ROUND(AVG(power_w))
        FROM power_samples
        WHERE device = '{dev}'
          AND timestamp >= '2026-05-17' AND timestamp < '2026-06-17'
          AND timestamp LIKE '%:00:00' AND SUBSTR(timestamp,15,2) = '00'
          AND power_w IS NOT NULL
    """)
    all_rows.append((dev, r[0][0], r[0][1]))
write_csv("all_devices_monthly.csv",
          ["device", "kwh_month", "avg_w"], all_rows)

# ─── 5. Monthly totals for TRX4 (from monthly Sheet 2) ────────

rows = query("""
    SELECT SUBSTR(timestamp,1,7) as month,
           ROUND(power_w * 30 * 24 / 1000, 1) as kwh,
           ROUND(power_w) as avg_w
    FROM power_samples
    WHERE device = 'TRX4'
      AND LENGTH(timestamp) = 10
      AND power_w IS NOT NULL
      AND power_w > 0
    ORDER BY timestamp
""")
write_csv("trx4_monthly_totals.csv",
          ["month", "kwh", "avg_w"], rows)

# ─── 6. Raw DB data: all TRX4 samples last month ──────────────

rows = query("""
    SELECT timestamp, ip, device, model, power_w
    FROM power_samples
    WHERE device = 'TRX4'
      AND timestamp >= '2026-05-17'
    ORDER BY timestamp
""")
write_csv("trx4_raw_samples.csv",
          ["timestamp", "ip", "device", "model", "power_w"], rows)

# ─── Summary ───────────────────────────────────────────────────

print(f"\nExported to: {OUTPUT}")
