# Branch Divergence Diagnosis — Session Reference

Diagnosis performed on `feat/preserve-message-timestamps` in `yitang/hermes-agent`.

## Symptoms

```
git status
# → Your branch and 'origin/feat/preserve-message-timestamps' have diverged,
#   and have 8187 and 9005 different commits each, respectively.
```

## Diagnostic Sequence

1. `git remote -v` — check origin protocol (was HTTPS, switched to SSH)
2. `git worktree list` — found stale worktree on macOS path
3. `git merge-base feat/preserve-message-timestamps origin/feat/preserve-message-timestamps` — empty output
4. `git log --oneline feat/preserve-message-timestamps | tail -1` — shows last local commit
5. `git log --oneline origin/feat/preserve-message-timestamps | tail -1` — shows last remote commit

## Conclusion

- No common ancestor (empty merge-base)
- Remote branch starts at "initial commit", local branch starts at a recent main commit
- Cause: remote was force-pushed/reset, creating a completely different history under the same branch name

## Cleanup

- Worktree: `git worktree prune` would remove the stale macOS entry
- Branch: local version would need `git push --force-with-lease` if it's the canonical version
