# Tapo Smart Plug Power Monitoring

Full setup guide for polling Tapo P110/P115 power data into Hermes cron + SQLite.

## Requirements

- Tapo P110(UK) or P115 smart plug
- TAPO_EMAIL / TAPO_PASSWORD in profile `.env`
- python-kasa installed in a dedicated venv:
  ```bash
  python3 -m venv ~/.hermes/profiles/coder/venv
  ~/.hermes/profiles/coder/venv/bin/pip install python-kasa xlrd
  ```

## Device discovery

```bash
~/.hermes/profiles/coder/venv/bin/kasa discover --username <email> --password <pw>
```

Labels from Tapo app are often wrong. Use hardcoded `DEVICE_LABELS` map keyed by IP.

## python-kasa connection quirks (v0.10.2)

### Connection parameters

Tapo P110 uses AES encryption on HTTP port 80, not XOR on port 9999:

```python
conn_params = DeviceConnectionParameters(
    device_family=DeviceFamily.SmartTapoPlug,
    encryption_type=DeviceEncryptionType.Aes,
    login_version=2, https=False,
    # http_port=80  # ← NOT available on ARM builds of kasa 0.10.2
    #                #   (Python 3.11, aarch64). Defaults to 80 anyway.
)
config = DeviceConfig(host=ip, credentials=Credentials(e, pw), connection_type=conn_params)
dev = await Device.connect(config=config)  # config= ONLY, not host= + config=
```

### Reading energy data

`emeter_realtime` deprecated in v0.10.2. Use internal_state:

```python
await dev.update()
emeter = dev.internal_state.get("get_emeter_data", {})
power_w = emeter.get("power_mw", 0) / 1000.0
voltage_v = emeter.get("voltage_mv", 0) / 1000.0
current_a = emeter.get("current_ma", 0) / 1000.0
total_wh = emeter.get("energy_wh", 0)
```

### Auth rate limiting

P110 has connection-rate limit — multiple connections within ~30s triggers
`LOGIN_ERROR(-1501)`. Cron's 15-min interval works. Discover-first pattern
(`Discover.discover()` then `Device.connect()` per IP) is more resilient.

### Historical stats NOT available locally

```python
await energy.get_daily_stats(year=2026, month=6)
# -> "Device does not support periodic statistics"
```

Use Tapo app XLS export instead (see below).

## Cron setup (Hermes)

Cron needs running gateway:
```bash
hermes cron status          # check
hermes gateway run --force  # start (use terminal(background=true))
```

Scripts need a shell wrapper — Hermes cron's no-agent mode uses uv Python 3.11,
ignoring the script's shebang, and PEP 668 blocks pip install there.

**tapo-log.sh:**
```bash
#!/bin/bash
exec /Users/yitang/.hermes/profiles/coder/venv/bin/python3 \
  /Users/yitang/.hermes/profiles/coder/scripts/tapo-log.py "$@"
```

Register:
```bash
hermes cron create --name "tapo-power-poll" --schedule "*/15 * * * *" \
  --script tapo-log.sh --no-agent
```

## Importing Tapo app XLS exports

Each device exports 2 files (unnumbered, -1, or -2):

| File | Sheets | Content |
|---|---|---|
| Power-N.xls | 0: ~290 rows | 5-min power (W), last ~24h |
| | 1: ~163 rows | Hourly avg power (W), last 7 days |
| Energy Usage-N.xls | 0: ~163 rows | Hourly energy (kWh) |
| | 1: ~79 rows | Daily energy (kWh), from April |
| | 2: ~13 rows | Monthly energy (kWh), from July 2025 |

Device matching by power signature: 6W→500W spikes→6W = TRX4 (inference machine); 70-510W = B760; 70-85W = iMac. This is more reliable than file order since Tapo app exports are unlabeled. Check the 5-min power data (Sheet 0): if the first ~30 rows show ~500W then drop to ~6W, it's the machine that was under load then powered off (TRX4). If values hover in the 70-200W range throughout, it's a lighter-workstation (B760). If mostly single-digit or low (<10W), it's a router/always-on-low-power device.

## SQL patterns

### kWh from hourly data (no overlap with 5-min data)

```sql
WITH hourly AS (
  SELECT power_w FROM power_samples
  WHERE device = 'TRX4' AND timestamp LIKE '2026-06-16%'
    AND power_w IS NOT NULL
    AND timestamp LIKE '%:00:00'
    AND SUBSTR(timestamp,15,2) = '00'
)
SELECT ROUND(SUM(power_w) / 1000.0, 2) as total_kwh FROM hourly;
```

### State breakdown

```sql
WITH hourly AS (
  SELECT power_w,
         CASE WHEN power_w < 10 THEN 'off'
              WHEN power_w > 350 THEN 'busy'
              ELSE 'idle' END as state
  FROM power_samples
  WHERE device = 'TRX4' AND timestamp LIKE '2026-06-16T%:00:00'
    AND SUBSTR(timestamp,15,2) = '00' AND power_w IS NOT NULL
)
SELECT state, COUNT(*) as hours,
       ROUND(SUM(power_w) / 1000.0, 2) as kwh
FROM hourly GROUP BY state;
```

TRX4 thresholds: off <10W, idle 10-350W (~200W), busy >350W (~500W).
