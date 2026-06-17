# Worktree Removal — pip Install Drift

## Symptom

After removing a git worktree with `git worktree remove`, the server fails to start:

```
ModuleNotFoundError: No module named 'pfin_db'
```

Or the server starts but loads stale code from site-packages instead of the main repo checkout.

## Root Cause

`pip install -e` creates an editable install pointing at an absolute path. When the worktree is removed, that path no longer exists. Reinstalling only the top-level package (`pip install -e pfin-api/`) doesn't pull in its dependencies (`pfin-core`, `pfin-data`) because `--no-deps` was used during the initial install and pip's dependency resolver gets confused by the conflicting constraints.

## Fix

Always reinstall ALL editable packages together after worktree removal:

```bash
pip install --break-system-packages --force-reinstall --no-deps \
  -e pfin-data/ -e pfin-core/ -e pfin-api/
```

The `--force-reinstall` is critical — without it, pip may think the package is already installed (pointing at the deleted worktree path) and skip it.

## Verification

```bash
python3 -c "import pfin_api; print(pfin_api.__file__)"
# Should print: /home/tangyi/dev/personal-finance/pfin-api/pfin_api/__init__.py
# NOT: /home/tangyi/dev/personal-finance/.worktrees/.../pfin-api/pfin_api/__init__.py
```

## Prevention

After every `git worktree remove` in a project with editable installs, run the full reinstall command. This is part of the `finishing-a-development-branch` merge step.
