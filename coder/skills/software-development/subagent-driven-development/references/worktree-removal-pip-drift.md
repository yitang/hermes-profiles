# Worktree — pip Install Drift

Editable installs (`pip install -e`) store absolute paths. When worktrees are
created, removed, or reused, these paths can drift. Two distinct scenarios:

## Scenario A: Deleted Worktree (removal drift)

### Symptom (server) — pip install fails with stale path

After removing a git worktree, the server fails to start:
```
ModuleNotFoundError: No module named 'pfin_db'
```
Or the server starts but loads stale code from site-packages instead of the
main repo checkout.

## Symptom (install) — relative file: dependencies resolve to wrong directory

```
pip install -e pfin-api/
...
ERROR: ... No such file or directory: '/home/tangyi/dev/personal-finance/.worktrees/pfin-core'
```

This happens when `pyproject.toml` has `pfin-core @ file:../pfin-core` and pip
resolves `../pfin-core` from the CWD or repo root instead of from the subpackage
directory.

### Root cause A: Deleted Worktree (removal drift)

`pip install -e` creates an editable install pointing at an absolute path.
When the worktree is removed, that path no longer exists. Reinstalling only
the top-level package doesn't pull in its dependencies because `--no-deps`
was used during the initial install.

`pip install -e` creates an editable install pointing at an absolute path.
When the worktree is removed, that path no longer exists. Reinstalling only
the top-level package doesn't pull in its dependencies because `--no-deps`
was used during the initial install.

### Fix: cd into subpackage before installing

When `pip install -e pfin-api/` fails with a stale resolved path even after
uninstall, install from inside the subpackage directory. Pip resolves `file:`
dependencies relative to the pyproject.toml's directory, not the CWD:

```bash
# Don't do this (may resolve ../pfin-core from repo root):
pip install -e /path/to/repo/pfin-api/

# Do this instead (resolves ../pfin-core from pfin-api/):
cd /path/to/repo/pfin-api/
pip install -e .
```

### Fix: stale editable finders from old worktrees

If `__editable__*.pth` or `__editable__*_finder.py` files in site-packages
still reference a deleted worktree path, delete them before reinstalling:

```bash
rm -rf ~/.local/lib/python3.13/site-packages/__editable__*
pip install --no-cache-dir --break-system-packages -e pfin-core/
pip install --no-cache-dir --break-system-packages -e pfin-api/
pip install --no-cache-dir --break-system-packages -e pfin-data/
```

The `--no-cache-dir` flag is important here because pip's wheel cache may
hold the stale path even after the dist-info is removed.

A quicker check: inspect the `__editable__*.pth` file for the stale path
and delete only the relevant entries. But when in doubt, nuke them all and
reinstall everything in order (bottom-up by dependency: core → api → data).

## Scenario B: Wrong Active Worktree (cross-worktree drift)

### Symptom

Tests or server running from worktree B serve stale templates/code from
worktree A. For example, you're working in `.worktrees/sync-page/pfin-api/`
but `pip show pfin-api` shows the editable install pointing at
`.worktrees/cash-account/pfin-api/`.

The old template renders (no new features), but the worktree's file on disk
has the new content.

### Root cause

A previous subagent or session in a different worktree ran `pip install -e`
on that worktree's package. Pip only stores one editable install per package
name. When the second worktree's `pip install --no-deps -e .` runs, it may
skip re-registration if pip considers the package "already installed" —
the old editable project path survives. The app imports from the old path,
serving stale code/templates.

## Common Fix (both scenarios)

Reinstall ALL editable packages from the correct checkout:

```bash
pip uninstall -y pfin-api --break-system-packages
pip install --break-system-packages --no-deps -e pfin-api/
```

For projects with relative `file:` dependencies that break from worktrees,
pre-install the dependency from its actual path first:

```bash
pip install --break-system-packages --no-deps -e /abs/path/to/pfin-core/
pip install --break-system-packages --no-deps -e pfin-api/
```

The `--force-reinstall` (instead of uninstall-then-install) may skip a stale
entry if the old path no longer exists. The uninstall → install sequence is
more reliable for Scenario A.

## Verification

```bash
pip show pfin-api | grep "Editable project location"
# Should point at the CURRENT checkout, not a stale worktree path

python3 -c "import pfin_api; print(pfin_api.__file__)"
# Should print: /home/tangyi/dev/personal-finance/pfin-api/pfin_api/__init__.py
# NOT: /home/tangyi/dev/personal-finance/.worktrees/.../pfin-api/pfin_api/__init__.py
```

## Prevention

1. **After every `git worktree remove`**, run the full reinstall command
   (Scenario A). This is part of the `finishing-a-development-branch` merge
   step.

2. **After dispatching subagents** that may have run `pip install -e` in a
   worktree, verify `pip show <pkg>` points to the correct checkout. Add
   this to the post-subagent checklist. (Scenario B detection.)

3. **When `pytest` serves stale templates** and the template file on disk
   has new content, check editable install drift first — it's faster than
   debugging template caching.

4. **For new worktrees**: before running tests, run `pip show` on all
   editable packages to confirm they resolve to paths inside the current
   worktree, not a sibling worktree.