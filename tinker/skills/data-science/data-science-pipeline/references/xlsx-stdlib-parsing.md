---
session_date: 2026-06-11
project: personal-finance-data
---

# XLSX Parsing with Python Standard Library

When pip is unavailable (no openpyxl) and sudo is blocked, parse `.xlsx` files as ZIP archives using `zipfile` + `xml.etree.ElementTree`.

## Why

- No `pip`, no `sudo`, no `openpyxl`, no `duckdb`
- `.xlsx` is a ZIP of XML files — stdlib handles it
- Works in any Python 3.6+ environment, zero dependencies

## Architecture of an .xlsx file

```
LoadDocstore.xlsx (ZIP)
├── xl/sharedStrings.xml   ← all text strings, indexed
├── xl/styles.xml          ← cell formatting
├── xl/workbook.xml        ← sheet names
├── xl/worksheets/
│   ├── sheet1.xml         ← first sheet data
│   ├── sheet2.xml         ← second sheet data
│   └── sheet3.xml         ← third sheet data
└── xl/_rels/workbook.xml.rels  ← sheet ID → filename mapping
```

## Parsing steps

### 1. Read shared strings (text lookup table)

```python
import zipfile, xml.etree.ElementTree as ET

zf = zipfile.ZipFile('file.xlsx')
sst_xml = zf.read('xl/sharedStrings.xml')
sst_root = ET.fromstring(sst_xml)
ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

shared_strings = []
for si in sst_root.findall('.//main:si/main:t', ns):
    shared_strings.append(si.text.strip() if si.text else '')
```

### 2. Read a worksheet and resolve cell values

```python
sheet_xml = zf.read('xl/worksheets/sheet1.xml')
root = ET.fromstring(sheet_xml)

def cell_value(cell_elem):
    """Resolve a <c> element to its display value."""
    t = cell_elem.get('t', '')
    v_el = cell_elem.find('.//main:v', ns)
    
    if t == 's' and v_el is not None:
        # Shared string: <v> is an index into sharedStrings.xml
        idx = int(v_el.text)
        return shared_strings[idx]
    
    if v_el is not None and v_el.text:
        raw = v_el.text.strip()
        # Detect Excel date serial numbers (30000-60000 range)
        try:
            nv = int(raw)
            if 30000 < nv < 60000:
                from datetime import datetime, timedelta
                dt = datetime(1899, 12, 30) + timedelta(days=nv)
                return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
        return raw
    
    if t == 'inlineStr':
        is_el = cell_elem.find('.//main:is/main:t', ns)
        if is_el is not None and is_el.text:
            return is_el.text.strip()
    
    return ''
```

### 3. Cell reference parsing

Cell references like `A1`, `B12` map column letters to positions:
```python
def col_letter(ref):  # 'A12' → 'A', 'B' → 'B'
    return ''.join(ch for ch in ref if ch.isalpha())
```

### 4. Multi-section parsing

Some sheets have multiple logical sections separated by header rows
(e.g., Vanguard has "Cash Transactions" then "Investment Transactions"
within the same sheet, sharing column headers but different row counts).

**Pattern: section-based state machine**
```python
section = None  # None, 'cash', 'investment'
headers = None

for row_elem in rows:
    cells = parse_row(row_elem)
    first_val = list(cells.values())[0]
    
    if first_val == 'Cash Transactions':
        section = 'cash'
        continue
    elif first_val == 'Investment Transactions':
        section = 'investment'
        continue
    elif first_val == 'Date':
        headers = sorted(cells.keys())
        continue
    
    if section == 'cash' and headers:
        cash_rows.append(row_for_headers(cells, headers))
    elif section == 'investment' and headers:
        inv_rows.append(row_for_headers(cells, headers))
```

### 5. Filtering summary/footer rows

Vanguard statements have footer rows like `Cost    29769.68` at the end
of investment sections. Check the first column for known footer patterns
and skip them:
```python
if date_str in ('Cost', 'Balance') or date_str.lower() == 'cost':
    continue
```

## Pitfalls

- **Date serial numbers**: Excel dates 1-60 map to Jan 1900 (including the
  leap-year bug). Values 61+ map correctly. The heuristic `30000 < nv < 60000`
  covers dates from ~1982 to ~2064 — safe for financial data.
- **Empty cells**: XML may omit cells that are empty. Don't assume every row
  has every column — use `.get(c, '')` with a default.
- **Shared string indices**: Some cells reference string indices beyond the
  sharedStrings list (empty cells with formatting). Guard with
  `if idx < len(shared_strings)`.
- **Section boundaries**: The section-detect text strings are case-sensitive
  and language-dependent. For Vanguard UK, they're in English.
