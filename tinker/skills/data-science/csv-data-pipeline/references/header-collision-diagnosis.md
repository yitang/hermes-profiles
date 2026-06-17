# Header Collision Diagnosis

## Problem
Two different account types produce CSV files with identical column headers. The detection/routing logic uses header matching and cannot distinguish them, causing silent misrouting of all rows into the wrong database table.

## Diagnostic Steps

### 1. List all cleaned output CSV headers

```bash
for f in data/cleaned/*.csv; do echo "$(basename $f): $(head -1 "$f")"; done
```

### 2. Identify collisions
Look for groups of filenames that share **identical** header strings. Any group with 2+ members is a collision.

### 3. Simulate the detection chain

If you have the detect_account() function, run this in Python:

```python
import csv, os

for fpath in ['data/cleaned/amex_ba.csv', 'data/cleaned/amex_gold.csv']:
    with open(fpath) as f:
        reader = csv.reader(f)
        header = next(reader)
        cols = [c.strip().lower() for c in header]
    
    # Simulate each detection branch against this header
    # ... replicate the if/elif logic from detect_account()
```

### 4. If both files match the same branch → collision confirmed

## Fix Strategy

**Best: Filename-based routing as PRIORITY check.** Every cleaned CSV has an account marker in its filename (e.g., `amex_ba.csv`, `lloyds_cleaned.csv`). Check filenames first:

```python
def detect_account(filepath):
    fname = os.path.basename(filepath).lower()
    
    # Priority 1: filename patterns (deterministic)
    if any(kw in fname for kw in ['amex_ba', 'ba_premium']):
        return 'amex_ba_cleaned'
    if 'lloyds_cleaned' in fname:
        return 'lloyds_cleaned'
    
    # Priority 2: header matching (fallback only)
    ...
```

**Alternative: Add a distinguishing annotation column.** If filenames can't be relied upon, have clean.py add a synthetic `source_account` column to every CSV. Detection then checks for this extra column.

## Verification After Fix

1. Run detection simulation on all cleaned CSVs — each must return its own unique account
2. Check DB: row counts per table should match manifest.md raw→clean counts
3. Verify no account has zero rows when it should have data
