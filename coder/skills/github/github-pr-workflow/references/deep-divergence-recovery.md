# Deep Divergence Recovery — Worked Example

When an old PR branch has diverged from upstream by thousands of commits
(e.g. the fork predates upstream's history squash/rebase), a plain
`git rebase upstream/main` replays every commit from the repo root
and fails on the initial commit. This document shows the recovery
pattern used on PR #28840 (8172 commits diverged).

## Symptoms

- `git rebase upstream/main` starts at "Rebasing (1/8172)" or similar
  triple-digit count
- Conflict on "initital commit" or root-level commits unrelated to your PR
- `git merge-base upstream/main HEAD` returns the repo root, not the
  branch point

## Recovery Steps

### 1. Check divergence scope

```bash
# Count commits that upstream doesn't have
git rev-list --count --right-only --no-merges upstream/main...HEAD
# If this is 5000+, you have deep divergence
```

### 2. Create a clean branch from latest upstream/main

```bash
git checkout -b my-feature-clean upstream/main
```

### 3. Identify your feature commits

```bash
# List the commits unique to your branch (most recent first)
git log --oneline --right-only --no-merges upstream/main...@{-1} | head -10
```

You want only the commits that represent YOUR changes — not pre-existing
upstream commits that happen to differ in SHA due to history rewriting.
Typically the last 3–5 commits.

### 4. Cherry-pick feature commits onto the clean branch

```bash
git cherry-pick <hash-of-feature-1> <hash-of-feature-2> ...
```

Order matters: cherry-pick the oldest feature commit first (the one
closest to the branch point), then newer ones.

### 5. Resolve conflicts

When both the old branch and upstream/main have similar code (e.g.
test files), the cherry-pick will conflict. For test additions that
exist in both versions:

```bash
git checkout --theirs tests/conflicting_test.py
git add tests/conflicting_test.py
git cherry-pick --continue
```

Use `--theirs` when the clean branch (based on latest upstream/main)
has the version you want. Use `--ours` when the cherry-picked commit's
version is correct.

### 6. Verify everything works

```bash
# Check all forwarding sites or key logic is present
grep -rn "timestamp=msg.get" --include='*.py' <relevant-files>
# Run the relevant tests
python3 -m pytest tests/test_suite.py -q -k "relevant-keyword"
```

### 7. Update the PR branch

```bash
# Option A: Reset old branch to clean branch (simplest, but destroys old history)
git checkout feat/old-pr-branch
git reset --hard feat/old-pr-branch-clean
git push origin feat/old-pr-branch --force-with-lease

# Option B: Cherry-pick from clean branch onto old branch (preserves old history)
git checkout feat/old-pr-branch
git cherry-pick <commit-from-clean-branch>
git push origin feat/old-pr-branch
```

**Option B pitfall — overlapping changes cause conflicts:** If the old branch already
has similar changes from its original feature commits (e.g., same test additions
or same code forwarding lines), the cherry-pick will conflict on those files even
though the changes are substantively the same. Resolution pattern:

```bash
# Accept the clean branch version (--theirs) since it's based on latest upstream
git checkout --theirs tests/conflicting_test.py
git add tests/conflicting_test.py
git cherry-pick --continue --no-edit
```

Files that *don't* conflict (e.g., files the old branch already has the change for
and the clean branch also has it) merge silently and correctly — git skips them.

### Pitfalls

**Worktree directory trap with `git add -A`:** If the repo root contains a
`.worktree/` directory from `git worktree add`, `git add -A` stages every
file under it — potentially thousands of unintended files (full codebase
copies, node_modules, build artifacts). Always check `git status` after
`git add -A` and unstage any `.worktree/` cruft:

```bash
git reset .worktree/
```

Or better, use targeted `git add <file1> <file2> ...` instead of `-A`.

**Stale upstream/main ref:** If you fetched `upstream/main` earlier in the
session and the user asks you to rebase, the ref may have moved. Always
re-fetch immediately before rebasing — don't trust a prior fetch:

```bash
git fetch upstream main
git rebase upstream/main
```

## Why this happens

When upstream squashes or rebases its main branch history, the commit
SHAs change. A feature branch that was created before this squash will
have the old SHAs in its ancestry. Git's merge-base resolves to the
repo root because none of the upstream/main commits (with new SHAs)
appear in the branch's ancestry. A plain `rebase upstream/main` then
tries to replay every commit from the root, most of which already
exist on upstream with different SHAs — leading to false conflicts.
