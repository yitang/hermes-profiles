#!/Users/yitang/.hermes/profiles/coder/venv/bin/python3
"""Parse all Tapo export XLS files and display their structure."""
import xlrd
import os

DATA_DIR = "/Users/yitang/Downloads/p110-data"

files = [f for f in sorted(os.listdir(DATA_DIR)) if f.endswith(".xls")]

for fname in files:
    path = os.path.join(DATA_DIR, fname)
    wb = xlrd.open_workbook(path)
    print(f"\n=== {fname} ({os.path.getsize(path)} bytes) ===")
    for s in range(wb.nsheets):
        sheet = wb.sheet_by_index(s)
        print(f"  Sheet {s}: {sheet.nrows} rows x {sheet.ncols} cols")
        if sheet.nrows > 0:
            # Print header row
            headers = [str(sheet.cell_value(0, c)) for c in range(sheet.ncols)]
            print(f"  Header: {headers}")
            # Check if first col is date-based
            for r in range(1, min(4, sheet.nrows)):
                row = [str(sheet.cell_value(r, c)) for c in range(sheet.ncols)]
                print(f"  Row {r}: {row}")
            # Last few rows
            if sheet.nrows > 10:
                print(f"  ... ({sheet.nrows-3} rows total)")
                for r in range(max(1, sheet.nrows-3), sheet.nrows):
                    row = [str(sheet.cell_value(r, c)) for c in range(sheet.ncols)]
                    print(f"  Row {r}: {row}")
