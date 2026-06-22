---
name: git-diagnostics
description: Diagnose and resolve git repository state issues — remote URL configuration, branch divergence analysis, worktree inspection, and common root-cause patterns.
---

# Git Diagnostics

Diagnose and fix git repository state problems. Covers remote URL management, branch divergence analysis, worktree troubleshooting, and interpreting common divergence patterns.

## Remote URL Configuration

Check current remotes:

```bash
git remote -v
```

Switch between protocols:

```bash
# HTTP → SSH
git remote set-url origin git@github.com:<user>/<repo>.git

# SSH → HTTP
git remote set-url origin https://github.com/<user>/<repo>.git
```

Multiple remotes (origin vs upstream) can have different protocols — handle each independently.

## Branch Divergence Diagnostics

When `git status` shows "have diverged" with large commit counts, use these steps:

**Step 1: Check the numbers**
```
Your branch and 'origin/branch-name' have diverged,
and have 8187 and 9005 different commits each, respectively.
```

Large divergence with different commit counts almost always means the histories are unrelated — not a rebase scenario.

**Step 2: Check common ancestor**

```bash
git merge-base <branch-name> origin/<branch-name>
```

- Returns a commit hash → normal divergence (branches share an ancestor, can be merged/rebased)
- Returns **empty** → completely divergent histories (the branch names share no parentage at all; something reset or replaced the remote branch)

**Step 3: Compare first commits**

```bash
echo "local:" && git log --oneline <branch-name> | tail -1
echo "remote:" && git log --oneline origin/<branch-name> | tail -1
```

- Different first commits with no merge-base → the remote was **force-pushed/reset** (or the local branch was based on a different base than what's on the remote)
- Same first commit → normal divergence from parallel work

**Step 4: Check worktrees**

```bash
git worktree list
```

Stale worktree entries (especially from another machine, e.g. macOS on a Linux host) show as `prunable`. These don't cause divergence but can confuse the picture.

## Interpreting Divergence Patterns

| Pattern | merge-base | first commits | Likely cause |
|---------|-----------|---------------|--------------|
| Normal divergence | hash | same | Both sides have new commits |
| Remote reset | empty | different | Remote was force-pushed from a different base |
| Rebase | hash | same, local ahead | Local was rebased, remote unchanged |
| Fork divergence | empty | different | Branches were created from different origins entirely |

## Common Fixes

Once diagnosed:

- **Unrelated histories** — you generally need to force-push the local version if it's the current state: `git push --force-with-lease origin <branch-name>`
- **Normal divergence** — merge or rebase normally
- **Stale worktree** — `git worktree prune` to clean up
