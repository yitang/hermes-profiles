# PKB Inventory Checklist

## Step 1 — File Count & Size Audit
```bash
# Total files
find . -type f ! -path '*/.git/*' | wc -l

# Files by extension
find . -type f ! -path '*/.git/*' | sed 's/.*\\.//' | sort | uniq -c | sort -rn

# Largest directories
du -sh */ | sort -rh | head -20

# Flat top-level files (no directory nesting)
find . -maxdepth 1 -type f ! -path './.git*' ! -name 'README*' | wc -l
```

## Step 2 — Timestamp Pattern Check
```bash
# List timestamped directories/files
find . -type f -regex '.*/[0-9]\{8\}[0-9]\{6\}.*' | head -20
```
Flag: >50 files with ISO timestamps in name = flat dump pattern. Needs restructuring.

## Step 3 — Empty/Mini Files
```bash
# Files under 1KB (likely ephemeral one-liners)
find . -type f -size -1k ! -path '*/.git/*' | wc -l

# Files under 5 lines
find . -type f -exec sh -c '[ $(wc -l < "$1") -lt 5 ] && echo "$1"' _ {} \; | head -20
```
Flag: >30% of files are tiny = high signal-to-noise ratio problem.

## Step 4 — Dated Exercise Audit
```bash
# List exercise directories by date
find . -path '*/exercises/*' -type d | sed 's|.*/\([0-9-]*\)/.*|\1|' | sort | head -20
```
Flag: dated exercises spanning years = candidates for consolidation into theme-based files.

## Step 5 — Multi-Vault Org-Roam Audit

### 5a — Find all vaults
```bash
# Find notes/ directories (the vault convention)
find ~ -name "notes" -type d ! -path '*/.git/*' | sort

# Also find org-roam.db files — these mark active org-roam vaults
find ~ -name "org-roam.db" ! -path '*/.git/*' | sort

# Check for flat vaults that don't use notes/ convention
# (e.g., vocabulary/ directories with roam-format files)
find ~/matrix ~/para -maxdepth 3 -name "*.org" -path '*/vocabulary/*' 2>/dev/null
```

### 5b — Per-vault wiring check
```bash
# Check each vault for .dir-locals.el at parent levels
for vault in /home/user/matrix/*/notes; do
  echo "=== $vault ==="
  ls "$vault"/*.org 2>/dev/null | wc -l
  test -f "$vault/org-roam.db" && echo "DB: yes" || echo "DB: no"

  # Walk up looking for .dir-locals.el
  dir=$(dirname "$vault")
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/.dir-locals.el" ]; then
      echo "dir-locals: $dir/.dir-locals.el"
      break
    fi
    dir=$(dirname "$dir")
  done
  echo ""
done
```

### 5c — Naming pattern analysis
Two org-roam file naming conventions signal different capture-template eras:
- `YYYYMMDD_HHMMSS-slug.org` — current capture template (with `_`)
- `YYYYMMDDHHMMSS-slug.org` — older / org-roam v1 (no `_`)

```bash
vault=/path/to/notes
echo "With underscore (current): $(ls "$vault"/*_.org 2>/dev/null | wc -l)"
echo "Without underscore (old):  $(ls "$vault"/*.org 2>/dev/null | grep -v "_" | wc -l)"
```

### 5d — Custom property tags check
Some vaults embed domain classifiers like `:matrix:` in note PROPERTIES:
```bash
vault=/path/to/notes
total=$(ls "$vault"/*.org 2>/dev/null | wc -l)
tagged=$(grep -l ":matrix:" "$vault"/*.org 2>/dev/null | wc -l)
echo "Total: $total | With :matrix: $tagged"
```

### 5e — Dir-locals wiring pattern
The user's matrix convention uses parent-level `.dir-locals.el`:
```elisp
(setq-local project-dir (file-name-concat
  (locate-dominating-file default-directory ".dir-locals.el") "meta-{domain}"))
(setq-local note-dir (file-name-concat project-dir "notes/"))
(setq-local org-roam-directory note-dir)
(setq-local org-roam-db-location (file-name-concat note-dir "org-roam.db"))
```
Always check the PARENT directory of the vault, not just the vault itself.

### 5f — DB freshness
```bash
ls -la /path/to/notes/org-roam.db
```
DB updated today = autosync is live. Stale DB + no dir-locals = orphaned vault.

## Step 6 — Report Format
Summarize:
- Total files: N
- Timestamped flat files: M (% of total)
- Tiny/ephemeral files: T (<1KB or <5 lines)
- Date range of oldest/newest note: Y to Y
- Top-level domains detected (by filename clustering): list
- Org-roam vaults found: list each with files/DB/wiring status

Use this report before proposing any restructuring strategy.
