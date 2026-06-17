# Worktree Pip Isolation — Recovery Sequence

## When pip install fails with "No such file or directory" pointing to an old worktree

**Symptom:** `pip install --break-system-packages -e pfin-api/` fails with:
```
Processing ../pfin-core (from pfin-api==0.1.0)
ERROR: Could not install packages due to an OSError: [Errno 2] No such file or directory:
  '/home/tangyi/dev/personal-finance/.worktrees/pfin-core'
```

The path referenced is an **old worktree** that no longer exists, not the current one.

**Root cause:** Previous `pip install -e` calls left behind `__editable__.pth` and `__editable___*_finder.py` files in `~/.local/lib/python3.13/site-packages/`. These files contain hardcoded absolute paths to the old worktree. When pip subsequently tries to resolve a `file:../pkg` dependency from pyproject.toml, its pip's internal dependency resolution picks up the stale path from one of these left-behind artifacts.

Even `--no-cache-dir` does not help — the stale path lives in the editable finder scripts, not the wheel cache.

## Recovery sequence

### Step 1: Identify all stale editable files

```bash
find ~/.local/lib/python3.13/site-packages -maxdepth 1 \( -name "*pfin*" -o -name "*editable*" \) 2>/dev/null
```

Look for three kinds of files:
- `__editable__.<package>-<version>.pth` — the pth loader
- `__editable___<package>_<version>_finder.py` — the finder script with hardcoded paths
- `<package>-<version>.dist-info/` — the package metadata directory

### Step 2: Delete ALL of them

```bash
rm -rf \
  ~/.local/lib/python3.13/site-packages/__editable__.*.pth \
  ~/.local/lib/python3.13/site-packages/__editable___*_finder.py \
  ~/.local/lib/python3.13/site-packages/*.dist-info
```

**This is a broad sweep** — it removes all editable-installed packages and their metadata, not just the stale ones. This is intentional because you cannot easily distinguish stale from current.

### Step 3: Reinstall from the worktree

```bash
# Always reinstall dependency-first (leaf packages first)
pip install --no-cache-dir --break-system-packages -e pfin-core/
pip install --no-cache-dir --break-system-packages -e pfin-api/
pip install --no-cache-dir --break-system-packages -e pfin-data/
```

Use `--no-cache-dir` to bypass any remaining stale wheel cache entries.

### Step 4: Verify imports resolve correctly

```bash
python3 -c "import pfin_core; print(pfin_core.__file__)"
# Expected: /home/tangyi/dev/personal-finance/.worktrees/<current>/pfin-core/pfin_core/__init__.py
# NOT: ~/.local/lib/python3.13/site-packages/... (would mean non-editable install leaked through)
```

## When even Step 3 fails — relative `file:` dependency issue

If step 3 still fails with a path pointing to a non-existent worktree, the issue is in how pip resolves `file:` URLs in pyproject.toml.

**The problem:** In a worktree at `.worktrees/<branch>/`, a dependency like:
```toml
dependencies = [
    "pfin-core @ file:../pfin-core",
]
```
is resolved relative to the **worktree root** (`.worktrees/<branch>/`), not relative to the subpackage directory (`.worktrees/<branch>/pfin-api/`). So `../pfin-core` becomes `.worktrees/pfin-core` instead of `../../pfin-core` (the main repo's version).

**Workaround:** Temporarily patch pyproject.toml to use an absolute path:

```python
# Patch the dependency to absolute path
"pfin-core @ file:/home/tangyi/dev/personal-finance/.worktrees/<current>/pfin-core",
```

Then install:
```bash
pip install --no-cache-dir --break-system-packages -e pfin-api/
```

Revert before committing:
```bash
git checkout -- pfin-api/pyproject.toml
```

**Alternative workaround:** Install the dependency package from the main repo path first:
```bash
pip install --break-system-packages -e /home/tangyi/dev/personal-finance/pfin-core
pip install --no-cache-dir --break-system-packages -e pfin-api/
```

**Simpler workaround (preferred):** `cd` into the subpackage before running pip. Pip resolves `file:../pkg` relative to the *current working directory*, not relative to the pyproject.toml file. So running from the right CWD makes the relative path resolve correctly:

```bash
cd pfin-api && pip install --no-cache-dir --break-system-packages -e .
cd ../pfin-core && pip install -e .
```

This avoids patching pyproject.toml entirely and works with no side effects. After this, verify the import resolves to the worktree:

```bash
python3 -c "import pfin_api; print(pfin_api.__file__)"
# Should show: .../.worktrees/<branch>/pfin-api/pfin_api/__init__.py
```

## Prevention

When creating a new worktree for Python projects with editable subpackage dependencies that use relative `file:` paths:

1. **Before dispatching any subagent**, verify that `pip install -e` works from the worktree:
   ```bash
   cd /home/tangyi/dev/personal-finance/.worktrees/<branch>
   pip install --break-system-packages -e pfin-api/ 2>&1
   ```
2. If it fails, follow the recovery sequence above first.
3. Then verify imports resolve to the worktree paths before starting implementation.

This is a one-time setup cost per worktree. Subagents in the same worktree should find packages already installed correctly.
