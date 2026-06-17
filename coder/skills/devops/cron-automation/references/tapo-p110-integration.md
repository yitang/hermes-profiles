# Tapo P110 Integration (python-kasa)

## Connection Parameters

Tapo P110(UK) devices require AES encryption and explicit connection parameters:

```python
from kasa import (
    DeviceFamily, DeviceEncryptionType, DeviceConnectionParameters,
    DeviceConfig, Credentials, Discover, Device
)

conn_params = DeviceConnectionParameters(
    device_family=DeviceFamily.SmartTapoPlug,
    encryption_type=DeviceEncryptionType.Aes,
    login_version=2,
    https=False,
    http_port=80,
)

config = DeviceConfig(
    host=ip,
    credentials=Credentials(email, password),
    connection_type=conn_params,
)
dev = await Device.connect(config=config)  # NOT host= + config= together
```

**Don't** pass both `host=` and `config=` to `Device.connect()` — the library
rejects it with "One of host or config must be provded and not both".

## Two-Phase Connection

Discovery + individual connection works most reliably:

```python
devices = await Discover.discover(username=email, password=password, timeout=8)
for ip in devices:
    config = DeviceConfig(host=ip, credentials=Credentials(email, password), connection_type=conn_params)
    dev = await Device.connect(config=config)
    await dev.update()
```

## Reading Power Data

The `Energy` module is often missing from `dev.modules` on P110. Use
`internal_state` directly:

```python
state = dev.internal_state
emeter = state.get("get_emeter_data", {})
if emeter:
    power_w = emeter.get("power_mw", 0) / 1000.0
    voltage_v = emeter.get("voltage_mv", 0) / 1000.0
    current_a = emeter.get("current_ma", 0) / 1000.0
    total_wh = emeter.get("energy_wh", 0)
```

Raw field names: `current_ma`, `voltage_mv`, `power_mw`, `energy_wh`.

## Historical Stats

The `Energy` module (when available) has:

```python
energy = dev.modules["Energy"]
today_wh = energy.consumption_today
month_wh = energy.consumption_this_month
total_wh = energy.consumption_total
current_w = energy.current_consumption

# Per-day stats for a month
daily = await energy.get_daily_stats(year=2026, month=6)

# Per-month stats for a year
monthly = await energy.get_monthly_stats(year=2026)
```

The device stores cumulative daily/monthly energy totals onboard.
Granular time-series (per-minute) is only in the Tapo cloud.

## Device Aliases

The device nicknames are base64-encoded in the raw response at
`state['get_device_info']['nickname']`. python-kasa's `dev.alias` or
`dev.get_device_info()` returns the decoded value.

## Rate Limiting

Tapo P110 devices have a per-connection auth rate limit — ~1 successful
connection per 30s minimum. Exceeding it returns `LOGIN_ERROR(-1501)`.
Cron at 15-min intervals is well within limits.

## ARM Linux (Raspberry Pi 4) Auth Failure

python-kasa 0.10.2 **does not work** on Raspberry Pi 4 running Debian 12
Bookworm (Python 3.11, aarch64). All Tapo P110 devices return
`LOGIN_ERROR(-1501)` during the AES transport handshake, even though:

- The device is reachable on the network (ping, port 80 HTTP)
- The same credentials work from macOS
- UDP discovery successfully finds the device
- All crypto primitives test correctly (ECDH, AES-CBC, SHA1)
- All connection parameter variations fail: KLAP (gets HTML response),
  AES v1/v2/v3, HTTPS on/off, login_version 1/2/3

### Debugging steps attempted (all failed)

| Attempt | Result |
|---------|--------|
| Direct `Device.connect()` with AES params | LOGIN_ERROR(-1501) |
| `Discover.discover()` then individual connect | LOGIN_ERROR(-1501) |
| `Discover.discover_single()` with credentials | LOGIN_ERROR(-1501) |
| KLAP encryption | HTML response instead of handshake |
| Different login versions (1, 2, 3) | Same LOGIN_ERROR |
| HTTPS (port 443) | Timeout (device has no HTTPS) |
| Raw TCP handshake to port 80 | Device doesn't respond to binary |
| Paused Mac cron to eliminate session contention | Same LOGIN_ERROR |
| Wait 30s between attempts | Same LOGIN_ERROR |
| Downgraded python-kasa to 0.9.0 | Same LOGIN_ERROR |
| Cryptography lib check (ECDH, AES) | All work correctly |
| Time/clock sync check | NTP synced, correct |

**Root cause unknown.** Suspected possibilities:
- Cryptography library ABI mismatch between ARM and x86_64 (cryptography's Rust
  bindings)
- Device-side MAC-based auth cache limiting connections to known clients
- ARM-specific timing issue in the AES handshake sequence

**Workaround:** Run Tapo polling on a machine that already authenticates
successfully (e.g., a Mac). The RP4 can still run Hermes for API-only tasks
that don't need Tapo access.

## Firmware

The P110(UK) units seen use firmware `1.1.6 Build 221114 Rel.203339`.

## See Also

- `devops/cron-data-pipeline` skill — covers the full power-monitoring pipeline
  including the poll → SQLite → daily summary → alert pattern
- `devops/cron-data-pipeline/references/tapo-p110-power-monitoring.md` — export
  format and historical data import from Tapo app XLS files
