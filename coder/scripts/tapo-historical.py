#!/Users/yitang/.hermes/profiles/coder/venv/bin/python3
"""Query and display historical daily/monthly stats from a Tapo P110 plug.

Usage: ./tapo-historical.py <IP>
Example: ./tapo-historical.py 192.168.1.239
"""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/.hermes/profiles/coder/venv/lib/python3.14/site-packages"))

PROFILE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = PROFILE_DIR / ".env"

DEVICE_LABELS = {
    "192.168.1.230": "TRX4",
    "192.168.1.239": "B760",
    "192.168.1.165": "iMac",
}


def load_env():
    if not ENV_FILE.exists():
        print("ERROR: .env not found", file=sys.stderr)
        sys.exit(1)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


async def main():
    load_env()
    email = os.environ.get("TAPO_EMAIL")
    password = os.environ.get("TAPO_PASSWORD")

    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.239"
    label = DEVICE_LABELS.get(ip, ip)

    from kasa import DeviceFamily, DeviceEncryptionType, DeviceConnectionParameters, DeviceConfig, Credentials, Device

    conn_params = DeviceConnectionParameters(
        device_family=DeviceFamily.SmartTapoPlug,
        encryption_type=DeviceEncryptionType.Aes,
        login_version=2, https=False, http_port=80,
    )
    config = DeviceConfig(host=ip, credentials=Credentials(email, password), connection_type=conn_params)
    dev = await Device.connect(config=config)
    await dev.update()

    print(f"=== {label} ({ip}) ===")
    print(f"Model: {dev.model}")
    print()

    if "Energy" not in dev.modules:
        print("No Energy module available")
        return

    energy = dev.modules["Energy"]
    now = datetime.now()

    # Monthly stats for the last 3 years
    print("--- Monthly Stats ---")
    all_monthly = {}
    for year in range(now.year - 2, now.year + 1):
        try:
            monthly = await energy.get_monthly_stats(year=year)
            if monthly:
                all_monthly[year] = monthly
                for m in monthly:
                    print(f"  {year}-{m['month']:02d}: {m.get('value', m.get('energy', 0))} Wh")
        except Exception as e:
            print(f"  {year}: error: {e}")

    print()

    # Daily stats for current year
    print("--- Daily Stats (this year) ---")
    total_days = 0
    for month in range(1, now.month + 1):
        try:
            daily = await energy.get_daily_stats(year=now.year, month=month)
            if daily:
                total_days += len(daily)
                # Just show summary per month
                vals = [d.get('value', d.get('energy', 0)) for d in daily]
                print(f"  {now.year}-{month:02d}: {len(daily)} days, total {sum(vals)} Wh, avg {sum(vals)/len(vals):.0f} Wh/day")
        except Exception as e:
            print(f"  {now.year}-{month:02d}: error: {e}")

    print(f"\nTotal: {total_days} daily records")


if __name__ == "__main__":
    asyncio.run(main())
