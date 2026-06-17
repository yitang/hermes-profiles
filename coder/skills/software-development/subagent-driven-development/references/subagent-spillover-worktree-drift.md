# Subagent Spillover — Writing to Main Repo from Worktree

**Symptom:** After a subagent completes (exit_reason = max_iterations/timeout), `git status` on master shows dirty files. The subagent was dispatched from a worktree but modified files in both the worktree AND the main repo checkout.

**Cause:** Subagents receive an absolute file path in their context (e.g. `/home/tangyi/dev/personal-finance/pfin-api/pfin_api/routes/web.py`). But this path exists in two places — the worktree at `.worktrees/<name>/` and the main repo. The subagent has no context about which is the "real" one.

**Detection:**
```bash
# On master, check if files the subagent was supposed to touch are dirty
git status --short
# If M pfin-api/pfin_api/routes/web.py appears, the subagent leaked to master
```

**Fix recipe:**
```bash
# Stash the leaked changes before merging the worktree branch
cd /path/to/main-repo
git stash push -m "subagent leaked changes to main repo"
git merge feat/<name>
git stash drop
```

**Prevention:** In subagent context, state the workspace path explicitly and instruct to only edit files under that path.

**Related:** When a subagent also modifies tests in test_bug_fixes.py, check that the test helper `_make_test_db` is updated in ALL copies across test files (see pfin-debugging Pattern 17).

## Patch Tool Path Resolution in Worktrees

When using the `patch` tool from the **orchestrator session** (not a subagent) while a worktree exists, the tool resolves relative file paths against the **current working directory** — not the worktree path. If the worktree branch was already merged to master and you're patching from the main repo's CWD, `patch` writes to the main repo's copy, which is correct post-merge. But if you intend to edit the worktree's copy (before merge), the path may resolve to the wrong checkout.

**Symptom:** You patch a file, `git diff` shows no changes, but the file on disk has the new content. The patch went to a different copy than the one git tracks in your worktree.

**Fix:** After a merge, always use absolute paths from the main repo root — the worktree is disposable and fixes belong on master. Before a merge, use absolute paths under `.worktrees/<name>/` to target the worktree copy.
