---
name: asset-audit-and-archive
category: note-taking
description: Systematic audit and archival of orphaned image/media assets in matrix repos — find unreferenced files, move to archive, clean broken org links. Reusable across all ~/matrix/ domains.
related_skills: [knowledge-migration, matrix-repo-audit]
---

# Asset Audit and Archive

Systematic audit of embedded image/media assets (org-download, data/, etc.) against active org file references. Used before PARA migration or during repo cleanup to identify orphaned files and reduce repository bloat.

## Trigger Conditions

- Before migrating any matrix repo to PARA
- When a repo has an `assets/` directory with significant size (>50MB)
- After deleting a notes/ or docs/ directory that had image references
- During periodic repository maintenance/cleanup

## Step 1: Inventory

```bash
# List all asset files and sizes
find <repo>/assets -type f | sort
echo "---"
du -sh <repo>/assets
du -sh <repo>/data 2>/dev/null

# Count org files outside assets/ and data/
find <repo> -name '*.org' -not -path '*/assets/*' -not -path '*/data/*' | wc -l
```

## Step 2: Reference Analysis

Run the audit script to find which asset files are referenced by current org files. This uses regex matching on org markup patterns like `[[file:assets/...]]`, `#+attr_org: :file assets/...`, and bare `assets/` or `data/` path mentions in `.org` content.

## Step 3: Classification

| Category | Definition | Action |
|----------|-----------|--------|
| **Active** | Referenced by at least one current org file | Keep in place |
| **Orphaned** | Never referenced, or referenced only by deleted/moved org files | Move to archive subdir inside assets/ |
| **Build Artifacts** | `.aux`, `.log`, `.out` from LaTeX/Makefile builds | Remove immediately (don't commit) |
| **Cache/Temp** | `.aider.*`, `.agent-shell/`, editor backup `*.~`, `.DS_Store` | Add to .gitignore and clean |

## Step 4: Archive Execution

```bash
# Create archive destination (inside assets/)
mkdir -p <repo>/assets/orphaned-<category>/

# Move orphaned files with EXPLICIT listing (NEVER use bulk * or rm)
cd <repo>/assets/<source-dir>
mv file1.ext file2.ext ../orphaned-<category>/

# Verify counts match expected
ls ../orphaned-<category>/ | wc -l
```

## Step 5: Cleanup Broken References

After moving orphaned files, check org files for dead links that still reference the moved paths:

```bash
grep -rn 'file:assets/tmp/' <repo> --include=*.org
grep -rn 'file:assets/images/' <repo> --include=*.org
```

Remove dead `[[file:...]]` references from org source files. Common sources of dead links:
- macOS pasteboard exports (`tmp/TemporaryItems/PasteboardItemExports/`) — always dead, never existed in git
- External PDFs downloaded to non-repo paths
- Screenshots from deleted org files

## Step 6: Commit Strategy

1. First commit: broken-reference cleanups (dead links removed from org files)
2. Second commit: asset moves with message like "hobbies: archive orphaned assets, keep only images referenced by active org files"

## Audit Script

Save this to a script and run from the repo root to get a complete reference analysis. The script outputs: disk usage summary, referenced vs unreferenced counts (with file sizes), broken references per org file, and subdir breakdown.

**Usage:** `python3 audit_assets.py <repo_root>`

```python
#!/usr/bin/env python3
"""Asset audit script — finds which assets/data files are referenced by current org files."""

import os, re, sys
from collections import Counter

repo_root = sys.argv[1] if len(sys.argv) > 1 else "/home/tangyi/matrix/hobbies/hobbies"
assets_dir = os.path.join(repo_root, "assets")
data_dir = os.path.join(repo_root, "data")

# Collect all asset/data files on disk with sizes
all_files = {}  # path -> size in bytes
for d in [assets_dir, data_dir]:
    if not os.path.isdir(d):
        continue
    for root, _, files in os.walk(d):
        rel = os.path.relpath(root, repo_root)
        for f in files:
            fp = os.path.join(root, f)
            if rel == ".":
                all_files[f] = os.path.getsize(fp)
            else:
                all_files[os.path.join(rel, f)] = os.path.getsize(fp)

# Collect org files (excluding assets/ and data/)
skip_dirs = {"assets", "data"}
org_files = []
for root, _, files in os.walk(repo_root):
    for fname in files:
        if fname.endswith(".org") and not any(root.startswith(os.path.join(repo_root, sd)) for sd in skip_dirs):
            org_files.append(os.path.relpath(os.path.join(root, fname), repo_root))

# Find all asset/data paths referenced by current org files
referenced = set()
for org in org_files:
    content = open(os.path.join(repo_root, org)).read()
    refs = re.findall(r'(?:file:)?(assets|data)/([\w./\-_]+(?:\.[a-z0-9]+)+)', content, re.IGNORECASE)
    for d, f in refs:
        referenced.add(os.path.join(d, f))

# Classify
referenced_on_disk = [f for f in all_files if f in referenced]
unreferenced_on_disk = [f for f in all_files if f not in referenced]

print(f"Total files on disk: {len(all_files)}")
total_size = sum(all_files.values())
print(f"Total size: {total_size / (1024*1024):.1f} MB")
print(f"Referenced by org files: {len(referenced_on_disk)} ({sum(all_files.get(f, 0) for f in referenced_on_disk) / (1024*1024):.1f} MB)")
print(f"Unreferenced (orphaned): {len(unreferenced_on_disk)} ({sum(all_files.get(f, 0) for f in unreferenced_on_disk) / (1024*1024):.1f} MB)")

if unreferenced_on_disk:
    print("\n=== ORPHANED FILES ===")
    total_orphan = sum(all_files.get(f, 0) for f in unreferenced_on_disk)
    print(f"Total orphaned size: {total_orphan / (1024*1024):.1f} MB")
    for f in sorted(unreferenced_on_disk):
        size = all_files.get(f, 0)
        if size < 1024:
            print(f"  {f} ({size} B)")
        elif size < 1024*1024:
            print(f"  {f} ({size/1024:.1f} KB)")
        else:
            print(f"  {f} ({size/(1024*1024):.1f} MB)")

# Broken references in org files (referenced path not on disk)
print("\n=== BROKEN REFERENCES IN ORG FILES ===")
for org in sorted(org_files):
    content = open(os.path.join(repo_root, org)).read()
    refs = re.findall(r'(?:file:)?(assets|data)/([\w./\-_]+(?:\.[a-z0-9]+)+)', content, re.IGNORECASE)
    for d, f in refs:
        check = os.path.join(repo_root, d, f)
        if not os.path.exists(check):
            short = "/".join(f.split("/")[1:]) if "/" in f else f
            print(f"  {org} → {d}/{short}")

# Summary by subdir
print("\n=== SUMMARY BY SUBDIR ===")
all_subdirs = set()
for f in all_files:
    first = f.split("/")[0] if "/" in f else f
    all_subdirs.add(first)

for sd in sorted(all_subdirs):
    total_count = len([f for f in all_files if (f == sd or f.startswith(sd + "/"))])
    ref_count = len([f for f in referenced_on_disk if (f == sd or f.startswith(sd + "/"))])
    total_size_mb = sum(all_files.get(f, 0) for f in all_files if (f == sd or f.startswith(sd + "/"))) / (1024*1024)
    ref_size_mb = sum(all_files.get(f, 0) for f in referenced_on_disk if (f == sd or f.startswith(sd + "/"))) / (1024*1024)
    print(f"  {sd}: {total_count} files ({total_size_mb:.1f} MB), {ref_count} referenced ({ref_size_mb:.1f} MB)")
```

## Pitfalls

1. **Don't rely on git history** — org-download images were often added as untracked or in separate commits. The text search of current `.org` file content is the authoritative reference check.
2. **macOS pasteboard exports** (`tmp/TemporaryItems/PasteboardItemExports/`) are always dead — they never existed in git. Clean them out proactively.
3. **Preserve directory structure for referenced files** — org `file:` links resolve relative to the repo root. Moving a *referenced* file breaks its link. Only move unreferenced ones, or update all references simultaneously.
4. **Always verify counts after moving** — check that the moved file count matches the expected orphaned count from the audit before committing.
5. **Never use `rm` or bulk `mv *.ext`** — always list files explicitly in the command to prevent accidental data loss.
6. **Distinguish provenance metadata from actual file references** — org-download lines like `#+DOWNLOADED: file:/Users/...PasteboardItemExports/...` are provenance notes recording where an image came from (pasteboard URL, webpage URL). They are NOT broken links and do NOT point to local files in the repo. The actual image reference is via `[[file:assets/...]]` or `#+attr_org: :file assets/...`. Only audit the latter for missing files. The former can be kept or deleted at will — they carry zero rendering impact.
7. **Repo renames preserve relative links** — when renaming a directory (e.g., `hobbies/hobbies/` → `hobbies/meta-hobbies/`), all `[[file:assets/...]]` relative references continue to work because both the org file and the asset move together. Only hard-coded absolute paths (like `/home/tangyi/matrix/hobbies/hobbies/open_plan.ledger` in shell commands) need updating. Scan for these with a grep before renaming, update them explicitly, then perform the rename.

## PARA Migration Considerations

When migrating to PARA:
- **Referenced images** stay with their org files (in `1_projects/` subdirs)
- **Orphaned archives** go to `3_resources/assets/archive/` or `7_archive/` in PARA
- **Data directories** containing unreferenced PDFs/reference docs should go to `3_resources/reference/` in PARA
- **Build artifacts** (`.aux`, `.log`) should be removed entirely — they are transient compile outputs, not reference material
