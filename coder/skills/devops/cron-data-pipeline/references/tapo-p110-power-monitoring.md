# Tapo P110 Power Monitoring Reference

## Device discovery and authentication (python-kasa 0.10.2)

python-kasa 0.10.2 has a significantly different API from earlier versions. Tapo P110 devices require explicit connection parameters — the old `SmartPlug()` and `emeter_realtime` APIs are deprecated or removed.

**Correct connection pattern:**

```python
from kasa import (
    Discover, Credentials, DeviceConfig, Device,
    DeviceFamily, DeviceEncryptionType, DeviceConnectionParameters
)

# Connection parameters for Tapo P110 — AES encryption, HTTP port 80
conn_params = DeviceConnectionParameters(
    device_family=DeviceFamily.SmartTapoPlug,
    encryption_type=DeviceEncryptionType.Aes,
    login_version=2,
    https=False,
    http_port=80,
)

# Step 1: Discover devices on LAN
raw_devices = await Discover.discover(username=email, password=password, timeout=8)
# Returns {ip: SmartDevice, ...}

# Step 2: Connect to each device individually with full config
for ip in raw_devices:
    config = DeviceConfig(
        host=ip,
        credentials=Credentials(email, password),
        connection_type=conn_params,
    )
    dev = await Device.connect(config=config)   # NOT host= AND config= — one or the other
    await dev.update()

    # Energy data is in internal_state, NOT in dev.emeter_realtime or dev.modules["Energy"]
    state = dev.internal_state
    emeter = state.get("get_emeter_data", {})
    # emeter keys: power_mw, voltage_mv, current_ma, energy_wh
    power_w = emeter.get("power_mw", 0) / 1000.0
    voltage_v = emeter.get("voltage_mv", 0) / 1000.0
    current_a = emeter.get("current_ma", 0) / 1000.0
    total_wh = emeter.get("energy_wh", 0)
```

**IMPORTANT gotchas:**
- `Device.connect()` accepts EITHER `host=` OR `config=` — NOT both (library has a typo in the error: "proved" instead of "provided")
- `Discover.discover()` returns a dict `{ip: SmartDevice}` but you MUST reconnect with `Device.connect()` for full auth — the discovered objects can't `.update()` directly
- Connection type must match the device: Tapo P110 uses AES on HTTP port 80 (not xor/KLAP)
- The `nickname` field in `get_device_info` is base64-encoded. python-kasa's `.alias` property decodes it for you automatically
- Multi-device hint: you can poll all discovered devices in a loop. The cumulative `total_wh` helps identify which plug is which (highest = longest-running device)

## Authentication

- Uses Tapo app credentials (TP-Link cloud account email + password)
- Stored in `~/.hermes/profiles/<profile>/.env`:
  ```
  TAPO_EMAIL=user@example.com
  TAPO_PASSWORD=***
  ```
- python-kasa uses AES transport with login version 2 on HTTP port 80
- Error `LOGIN_ERROR(-1501)` = wrong credentials

## UK plug specifics

- Model: P110(UK) with energy monitoring
- Uses AES encryption (KLAP transport in older lib versions)
- HTTP port 80, no HTTPS
- No persistent connection needed — query and disconnect per sample

## Sample wiring (profile ``coder``)

```
~/.hermes/profiles/coder/
├── .env                          # TAPO_EMAIL, TAPO_PASSWORD
├── venv/                         # python-kasa installed here
├── scripts/
│   ├── tapo-log.py               # 15-min poll → SQLite
│   └── tapo-daily-summary.py     # 9am daily report
└── data/
    └── tapo-power.db             # power_samples table
```

## TRX4 power profile (for reference)

| State | Watts (3080+3090) |
|---|---|
| System idle (headless) | ~150-200W |
| Under LLM inference load | ~700-800W |
| Idle-vs-load threshold | ~300W (above = inference active) |

At UK rates: ~0.25 GBP/kWh → ~0.55 GBP/hr under load, ~0.04 GBP/hr idle.

## Historical data import (Tapo app XLS export)

The Tapo app (iOS/Android) can export device data to `.xls` files. Each device produces two files: `Power.xls` and `Energy Usage.xls`. When you export multiple devices, the app numbers them: `Power.xls`, `Power-1.xls`, `Power-2.xls` etc.

### Export format — `Power.xls`

| Sheet | Rows | Granularity | Date range | Content |
|---|---|---|---|---|
| 0 | ~290 | 5-minute | Last ~24h | Instantaneous power in Watts |
| 1 | ~163 | Hourly | Last 7 days | Hourly average power in Watts |

The 5-minute data (Sheet 0) is the most valuable — it captures actual load patterns including idle/inference transitions. Values marked `/` mean no data for that interval (plug was offline or just commissioned).

### Export format — `Energy Usage.xls`

| Sheet | Rows | Granularity | Date range | Content |
|---|---|---|---|---|
| 0 | ~163 | Hourly | Last 7 days | Hourly kWh |
| 1 | ~79 | Daily | From April 2026 | Daily kWh |
| 2 | ~13 | Monthly | From July 2025 | Monthly kWh |

The daily data (Sheet 1) goes back the furthest — up to when the plug was commissioned. Monthly data (Sheet 2) covers the full lifespan.

### File-to-device mapping

When exporting multiple devices from the Tapo app, the file numbering order is arbitrary (not directly tied to the Tapo alias). Map files to devices by analysing the power signature from each file:

- **High sustained power** (400-800W) with drops to off = desktop/server
- **Moderate power** (70-200W) = workstation/iMac
- **Consistent low power** (6-10W) = router/Raspberry Pi

Use a hardcoded `DEVICE_LABELS` dict in the poll script to override Tapo-assigned aliases:

```python
DEVICE_LABELS = {
    "192.168.1.230": "TRX4",
    "192.168.1.239": "B760",
    "192.168.1.165": "iMac",
}
```

### Import script pattern

Install `xlrd` in the venv to parse `.xls` files:

```bash
~/.hermes/profiles/<profile>/venv/bin/pip install xlrd
```

The import script reads each sheet row-by-row, parses timestamps with `xlrd.xldate_as_tuple()` or string parsing, converts kWh to average Watts (where needed), and inserts into the same SQLite DB.

Key dedup logic: check `timestamp LIKE 'YYYY-MM-DDTHH:%'` before inserting to avoid duplicating samples already captured by the cron.

See `scripts/tapo-import.py` in the coder profile for a working example.
