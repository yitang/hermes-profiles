#!/Users/yitang/.hermes/profiles/coder/venv/bin/python3
"""Poll all Tapo P110 plugs and log power data to SQLite.

Reads TAPO_EMAIL and TAPO_PASSWORD from the profile's .env file.
Runs as a cron job (no-agent mode): outputs JSON on success, errors to stderr.
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

import asyncio
import json
import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path

DEVICE_LABELS = {
    "192.168.1.230": "TRX4",
    "192.168.1.239": "B760",
    "192.168.1.165": "iMac",
}
PROFILE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = PROFILE_DIR / ".env"
DB_PATH = PROFILE_DIR / "data" / "tapo-power.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS power_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    ip TEXT NOT NULL,
    device TEXT,
    model TEXT,
    power_w REAL,
    voltage_v REAL,
    current_a REAL,
    total_wh REAL
);
CREATE INDEX IF NOT EXISTS idx_ts ON power_samples(timestamp);
CREATE INDEX IF NOT EXISTS idx_device ON power_samples(ip);
"""


def load_env():
    """Load KEY=VALUE lines from .env, skipping comments."""
    if not ENV_FILE.exists():
        print("ERROR: .env not found at", ENV_FILE, file=sys.stderr)
        sys.exit(1)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    return conn


async def poll_all():
    from kasa import DeviceFamily, DeviceEncryptionType, DeviceConnectionParameters, Discover, Credentials, DeviceConfig

    email = os.environ.get("TAPO_EMAIL")
    password = os.environ.get("TAPO_PASSWORD")
    if not email or not password:
        print("ERROR: TAPO_EMAIL and TAPO_PASSWORD must be set in .env", file=sys.stderr)
        sys.exit(1)

    # Discover devices on LAN
    raw_devices = await Discover.discover(username=email, password=password, timeout=8)
    if not raw_devices:
        print("ERROR: No Tapo devices found", file=sys.stderr)
        sys.exit(1)

    # Connection parameters for Tapo P110 (AES, HTTP port 80)
    conn_params = DeviceConnectionParameters(
        device_family=DeviceFamily.SmartTapoPlug,
        encryption_type=DeviceEncryptionType.Aes,
        login_version=2,
        https=False,
        http_port=80,
    )

    # Connect to each device individually with credentials
    ips = list(raw_devices.keys())
    results = []
    for ip in ips:
        try:
            config = DeviceConfig(host=ip, credentials=Credentials(email, password), connection_type=conn_params)
            from kasa import Device
            dev = await Device.connect(config=config)
            await dev.update()

            # Read energy data from internal state (most reliable for Tapo P110)
            power = voltage = current = total = None
            state = dev.internal_state
            emeter = state.get("get_emeter_data", {}) if isinstance(state, dict) else {}
            if emeter:
                power = emeter.get("power_mw", 0) / 1000.0 if emeter.get("power_mw") else None
                voltage = emeter.get("voltage_mv", 0) / 1000.0 if emeter.get("voltage_mv") else None
                current = emeter.get("current_ma", 0) / 1000.0 if emeter.get("current_ma") else None
                total = emeter.get("energy_wh", 0) if emeter.get("energy_wh") else None

            results.append({
                "timestamp": datetime.now().isoformat(),
                "ip": ip,
                "device": DEVICE_LABELS.get(ip, getattr(dev, "alias", None) or ip),
                "model": getattr(dev, "model", None),
                "power_w": power,
                "voltage_v": voltage,
                "current_a": current,
                "total_wh": total,
            })
        except Exception as e:
            print(f"WARNING: Failed to poll {ip}: {e}", file=sys.stderr)
            results.append({
                "timestamp": "",
                "ip": ip,
                "device": ip,
                "model": None,
                "power_w": None,
                "voltage_v": None,
                "current_a": None,
                "total_wh": None,
                "error": str(e),
            })
    return results


async def main():
    load_env()
    results = await poll_all()
    conn = init_db()

    for r in results:
        conn.execute(
            "INSERT INTO power_samples (timestamp, ip, device, model, power_w, voltage_v, current_a, total_wh) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (r["timestamp"], r["ip"], r["device"], r["model"],
             r["power_w"], r["voltage_v"], r["current_a"], r["total_wh"])
        )
    conn.commit()
    conn.close()

    # Output JSON for diagnostic / cron pickup
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
