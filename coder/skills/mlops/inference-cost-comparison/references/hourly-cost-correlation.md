# Hourly Cost Correlation (Power vs API Usage)

## The limitation

Neither DeepSeek's API nor Hermes session logs provide hourly token breakdowns:

| Source | Data available | Granularity |
|---|---|---|
| DeepSeek API billing page | Cumulative total only | Lifetime |
| DeepSeek API response | Per-request token count | Per-message (not persisted) |
| Hermes sessions DB | `token_count` column | Always NULL — not populated |
| Tapo power DB | Real-time W, cumulative Wh | 5-min or 15-min intervals |

You cannot directly compute "X tokens at hour Y cost Z yuan and consumed W kWh"
without additional instrumentation.

## Practical workaround — power-spike-to-work-session estimation

Power data shows clear inference spikes (~500W) separated by idle troughs (~200W)
or offline periods (~6W). Correlate inference windows with known working sessions.

Example from real data (TRX4, June 16):

```
Inference windows (>350W):
  09:00-09:00  454W  (1h)
  11:00-13:00  ~500W (3h)
  17:00-17:30  ~500W (0.5h)
  18:55-19:05  ~500W (10min)
  21:10-21:30  ~500W (20min)
  Total: ~5h inference / 24h day

  Total API cost that day: ~6.6 元
  Cost per inference hour: ~1.3 元/h

Idle windows (10-350W):
  10:00       202W  (1h)
  14:00-16:00 ~200W (3h)
  17:40-18:50 ~200W (1h)
  19:10-21:05 ~200W (2h)
  Total: ~7h idle — server left on but not doing work

Idle cost: ~200W × 7h × £0.25/kWh = £0.35 wasted
```

### Validated from real monthly data (May 17 – Jun 16, TRX4)

A 31-day continuous trace validated the methodology:

| Metric | Value |
|---|---|
| Total consumption | **109 kWh** |
| Total electricity cost | **£27.26 / ¥62.70** |
| Daily average | 3.6 kWh / £0.90 |
| Max day | Jun 13 — 6.19 kWh (6h inference, 12h idle, 6h off) |
| Min day | Jun 1 — 0 kWh (server off) |
| Idle waste across month | ~33% of on-time — server left running between work sessions |

## Validated TRX4 power thresholds (from real measurements)

| State | Power range | Typical | Meaning |
|---|---|---|---|
| Off | <10W | 6W | Server powered down, plug idle draw only |
| Idle | 10-350W | ~200W | System on, GPUs powered but idle |
| Busy (inference) | >350W | ~500W | GPUs loaded, llama.cpp inference |

## SQL: Computing kWh from hourly data (cleanest)

```sql
-- Only :00:00 hourly timestamps to avoid double-counting with 5-min data
WITH hourly AS (
  SELECT power_w FROM power_samples
  WHERE device = 'TRX4' AND timestamp LIKE '2026-06-16%'
    AND power_w IS NOT NULL
    AND timestamp LIKE '%:00:00'
    AND SUBSTR(timestamp,15,2) = '00'
)
SELECT 
  ROUND(SUM(power_w) / 1000.0, 2) as total_kwh,
  ROUND(SUM(CASE WHEN power_w > 350 THEN power_w ELSE 0 END) / 1000.0, 2) as inference_kwh,
  ROUND(SUM(CASE WHEN power_w BETWEEN 10 AND 350 THEN power_w ELSE 0 END) / 1000.0, 2) as idle_kwh,
  ROUND(SUM(CASE WHEN power_w < 10 THEN power_w ELSE 0 END) / 1000.0, 2) as offline_kwh
FROM hourly;
```

## Better approach — log at application layer

Not implemented yet. Would require intercepting API responses in Hermes and
writing token counts to a `token_usage` table alongside the power data.

## Cross-referencing Hermes sessions with power data

Even without token counts, you can correlate *activity*: when were you using
Hermes vs when was the server busy/idle/off. This reveals what % of your
LLM usage could have run locally vs was purely remote.

### SQL: Join Hermes state.db with power DB by hour

```sql
-- Hermes sessions per hour (assistant messages = AI responses)
SELECT DATE(m.timestamp, 'unixepoch') as day,
       STRFTIME('%H', m.timestamp, 'unixepoch') as hour,
       COUNT(*) as msg_count
FROM messages m
WHERE m.role = 'assistant'
  AND m.timestamp >= strftime('%s', '2026-06-11')
  AND m.timestamp < strftime('%s', '2026-06-17')
GROUP BY day, hour;

-- Power state per hour (from cron pipeline)
SELECT SUBSTR(ts,1,10) as day,
       SUBSTR(ts,12,2) as hour,
       ROUND(AVG(power_w)) as avg_w,
       CASE WHEN AVG(power_w) > 350 THEN 'busy'
            WHEN AVG(power_w) > 10 THEN 'idle'
            ELSE 'off' END as state
FROM power_samples
WHERE device = 'TRX4'
  AND timestamp >= '2026-06-11' AND timestamp < '2026-06-17'
  AND timestamp LIKE '%:00:00'
  AND SUBSTR(timestamp,15,2) = '00'
  AND power_w IS NOT NULL
GROUP BY day, hour;

-- Then join in application code (or a cross-DB script)
```

### Real result (Jun 11-16, TRX4)

| TRX4 state | Hermes msgs | % of total |
|---|---|---|
| Busy (>350W) | 2,348 | 30% |
| Idle (~200W) | 3,696 | 47% |
| Off (<10W) | 1,691 | 21% |
| **Total** | **7,735** | **100%** |

47% of Hermes usage happened while the TRX4 was sitting at 200W doing nothing.
Those sessions could have run on the local model, or the server could have been off,
saving £0.35/day in idle waste.

See the cross-reference script at `scripts/cross-reference-power-and-sessions.py`
in this skill for a reusable tool that does all of the above in one command.
