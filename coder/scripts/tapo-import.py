#!/Users/yitang/.hermes/profiles/coder/venv/bin/python3
"""Import Tapo app CSV/Excel exports into the power monitoring DB.

Maps export files to devices based on power signature patterns.
"""
import xlrd
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/.hermes/profiles/coder/venv/lib/python3.14/site-packages"))
DATA_DIR = "/Users/yitang/Downloads/p110-data"

PROFILE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROFILE_DIR / "data" / "tapo-power.db"

DEVICE_LABELS = {
    "192.168.1.230": "TRX4",
    "192.168.1.239": "B760",
    "192.168.1.165": "iMac",
}

# The 3 export file pairs map to devices in the order they were exported
# Power-2 has 500W spikes then 6W = TRX4 (was running inference, now off)
# Power-1 has 70-500W range = B760
# Power has 73-85W range = iMac
FILE_TO_IP = {
    "Power.xls": "192.168.1.165",           # iMac
    "Power-1.xls": "192.168.1.239",         # B760
    "Power-2.xls": "192.168.1.230",         # TRX4
}
ENERGY_TO_IP = {
    "Energy Usage.xls": "192.168.1.165",
    "Energy Usage-1.xls": "192.168.1.239",
    "Energy Usage-2.xls": "192.168.1.230",
}


def get_db_conn():
    conn = sqlite3.connect(str(DB_PATH))
    return conn


def timestamp_exists(conn, ts_str, ip):
    """Check if a sample at this timestamp+ip already exists (fuzzy match)."""
    cursor = conn.cursor()
    # Match within 30 seconds
    cursor.execute(
        "SELECT COUNT(*) FROM power_samples WHERE ip = ? AND timestamp LIKE ?",
        (ip, ts_str[:16] + "%")
    )
    return cursor.fetchone()[0] > 0


def parse_xls_date(val):
    """Parse a date/time value from the XLS (could be string or xlrd datetime)."""
    if isinstance(val, float):
        # xlrd date format
        try:
            dt = xlrd.xldate_as_tuple(val, 0)
            return datetime(*dt)
        except:
            return None
    if isinstance(val, str):
        val = val.strip()
        for fmt in ["%Y/%m/%d %H:%M:%S", "%Y/%m/%d", "%Y/%m"]:
            try:
                return datetime.strptime(val, fmt)
            except:
                continue
    return None


def import_power(power_file, ip):
    """Import 5-min power data (Sheet 0) and hourly power (Sheet 1)."""
    path = os.path.join(DATA_DIR, power_file)
    if not os.path.exists(path):
        print(f"  SKIP: {power_file} not found")
        return 0, 0

    wb = xlrd.open_workbook(path)
    conn = get_db_conn()
    inserted = 0
    skipped = 0
    label = DEVICE_LABELS[ip]

    # Sheet 0: 5-min interval power (W)
    sheet = wb.sheet_by_index(0)
    for r in range(1, sheet.nrows):
        ts_val = sheet.cell_value(r, 0)
        power_val = sheet.cell_value(r, 1)

        dt = parse_xls_date(ts_val)
        if dt is None:
            continue

        # Skip '/' or non-numeric values
        if isinstance(power_val, str) and power_val.strip() in ("/", "", "-"):
            continue
        try:
            power_w = float(power_val)
        except (ValueError, TypeError):
            continue

        ts_str = dt.isoformat()
        if timestamp_exists(conn, ts_str, ip):
            skipped += 1
            continue

        conn.execute(
            "INSERT INTO power_samples (timestamp, ip, device, model, power_w) VALUES (?, ?, ?, 'P110', ?)",
            (ts_str, ip, label, power_w)
        )
        inserted += 1

    # Sheet 1: hourly average power (W)
    if wb.nsheets > 1:
        sheet = wb.sheet_by_index(1)
        for r in range(1, sheet.nrows):
            ts_val = sheet.cell_value(r, 0)
            power_val = sheet.cell_value(r, 1)

            dt = parse_xls_date(ts_val)
            if dt is None:
                continue

            if isinstance(power_val, str) and power_val.strip() in ("/", "", "-"):
                continue
            try:
                power_w = float(power_val)
            except (ValueError, TypeError):
                continue

            ts_str = dt.isoformat()
            if timestamp_exists(conn, ts_str, ip):
                skipped += 1
                continue

            conn.execute(
                "INSERT INTO power_samples (timestamp, ip, device, model, power_w) VALUES (?, ?, ?, 'P110', ?)",
                (ts_str, ip, label, power_w)
            )
            inserted += 1

    conn.commit()
    conn.close()
    return inserted, skipped


def import_energy(energy_file, ip):
    """Import hourly (Sheet 0) and daily (Sheet 1) energy data.
    Since energy is cumulative kWh per interval, we store it as average power.
    """
    path = os.path.join(DATA_DIR, energy_file)
    if not os.path.exists(path):
        print(f"  SKIP: {energy_file} not found")
        return 0, 0, 0

    wb = xlrd.open_workbook(path)
    conn = get_db_conn()
    inserted_hourly = 0
    inserted_daily = 0
    inserted_monthly = 0
    label = DEVICE_LABELS[ip]

    # Sheet 0: hourly kWh — convert to average power: P(W) = kWh * 1000 / 1h
    sheet = wb.sheet_by_index(0)
    for r in range(1, sheet.nrows):
        ts_val = sheet.cell_value(r, 0)
        kwh_val = sheet.cell_value(r, 1)

        dt = parse_xls_date(ts_val)
        if dt is None:
            continue

        try:
            kwh = float(kwh_val)
        except (ValueError, TypeError):
            continue

        # Convert kWh to average power in Watts (over the hour)
        power_w = round(kwh * 1000, 1)
        ts_str = dt.isoformat()

        if not timestamp_exists(conn, ts_str, ip):
            conn.execute(
                "INSERT INTO power_samples (timestamp, ip, device, model, power_w) VALUES (?, ?, ?, 'P110', ?)",
                (ts_str, ip, label, power_w)
            )
            inserted_hourly += 1

    # Sheet 1: daily kWh — convert to average power
    if wb.nsheets > 1:
        sheet = wb.sheet_by_index(1)
        for r in range(1, sheet.nrows):
            ts_val = sheet.cell_value(r, 0)
            kwh_val = sheet.cell_value(r, 1)

            dt = parse_xls_date(ts_val)
            if dt is None:
                continue

            try:
                kwh = float(kwh_val)
            except (ValueError, TypeError):
                continue

            power_w = round(kwh * 1000 / 24, 1)  # daily average
            ts_str = dt.isoformat()

            if not timestamp_exists(conn, ts_str, ip):
                conn.execute(
                    "INSERT INTO power_samples (timestamp, ip, device, model, power_w) VALUES (?, ?, ?, 'P110', ?)",
                    (ts_str, ip, label, power_w)
                )
                inserted_daily += 1

    # Sheet 2: monthly kWh
    if wb.nsheets > 2:
        sheet = wb.sheet_by_index(2)
        for r in range(1, sheet.nrows):
            ts_val = sheet.cell_value(r, 0)
            kwh_val = sheet.cell_value(r, 1)

            dt = parse_xls_date(ts_val)
            if dt is None:
                continue

            try:
                kwh = float(kwh_val)
            except (ValueError, TypeError):
                continue

            # Use first day of month, convert to avg power
            days_in_month = 30  # approximate
            power_w = round(kwh * 1000 / (days_in_month * 24), 1)
            ts_str = dt.isoformat()

            if not timestamp_exists(conn, ts_str, ip):
                conn.execute(
                    "INSERT INTO power_samples (timestamp, ip, device, model, power_w) VALUES (?, ?, ?, 'P110', ?)",
                    (ts_str, ip, label, power_w)
                )
                inserted_monthly += 1

    conn.commit()
    conn.close()
    return inserted_hourly, inserted_daily, inserted_monthly


def main():
    print("Importing Tapo export data...\n")

    total_inserted = 0
    total_skipped = 0

    # Import power data
    for power_file, ip in FILE_TO_IP.items():
        label = DEVICE_LABELS[ip]
        print(f"\n  {power_file} -> {label} ({ip})")
        ins, skip = import_power(power_file, ip)
        total_inserted += ins
        total_skipped += skip
        print(f"    Power: {ins} inserted, {skip} skipped")

    # Import energy data
    for energy_file, ip in ENERGY_TO_IP.items():
        label = DEVICE_LABELS[ip]
        print(f"  {energy_file} -> {label} ({ip})")
        h, d, m = import_energy(energy_file, ip)
        total_inserted += h + d + m
        print(f"    Energy: {h} hourly, {d} daily, {m} monthly inserted")

    print(f"\nTotal: {total_inserted} records imported, {total_skipped} skipped")
    print(f"DB: {DB_PATH}")


if __name__ == "__main__":
    main()
