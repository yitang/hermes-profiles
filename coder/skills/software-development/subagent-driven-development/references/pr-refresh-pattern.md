# PR Refresh Pattern

Refresh an existing PR branch against upstream when the branch has accumulated stale
hunks, the target call sites moved, or upstream has already merged part of the fix.

## When to use

- An existing PR has been sitting open and upstream `main` has diverged significantly
- The reviewer flagged that call-site locations in the PR are stale (code moved to
  other files since the PR was authored)
- Upstream has already merged part of the fix, leaving only the call-site forwarding
  changes to keep
- The `git diff --stat upstream/main` shows thousands of files that shouldn't be there

## Workflow

### 1. Understand what the PR actually needs

Before touching anything, read the PR description and any reviewer feedback. Build
a table of every file the PR touches and its disposition:

| File | Action | Reason |
|------|--------|--------|
| `hermes_state.py` | Drop (already on upstream) | Core fix merged upstream |
| `.gitignore` | Drop (unrelated) | Was never part of the feature |
| `cli.py` | Drop (call site moved) | Code moved to `hermes_cli/cli_commands_mixin.py` |

### 2. Fetch upstream and check divergence

```bash
git fetch upstream main
git diff --stat upstream/main  # see what's actually different
git log --oneline HEAD..upstream/main | wc -l  # how far behind
```

Check the specific files from your action table:
```bash
git diff upstream/main -- <file1> <file2>
```

### 3. Drop stale hunks

Reset files that should have no changes to upstream/main:
```bash
git checkout upstream/main -- <file1> <file2> ...
```

This applies to:
- Files where upstream already has the fix
- Files with unrelated changes that crept in
- Files at old call-site locations that moved elsewhere

**Don't reset files that still carry necessary PR changes** (test files, forwarding
at the correct new call sites).

### 4. Commit the cleanup

```bash
git add -A
git commit -m "chore: drop stale hunks superseded by upstream main"
```

This commit marks the boundary between "things that were wrong about the branch"
and "the actual feature work."

### 5. Rebase onto upstream/main

```bash
git rebase upstream/main
```

**Conflict strategy:** The branch's own changes (feature commits) should generally
win over upstream's version of the same files. Use `-X theirs` to auto-accept the
branch version on conflicts, then manually verify correctness rather than fighting
every conflict:

```bash
git rebase upstream/main -X theirs
```

Common conflict types during PR refresh rebases:
- **add/add** — both sides added a file; accept branch version
- **modify/delete** — upstream deleted a file the branch modified; accept branch version
- **rename/rename** — file renamed differently in each; accept branch version
- **file location** — git can't figure out where a file went; point it manually

### 6. Find moved call sites

After rebase, some files the PR originally modified may have moved to new locations.
Search for the pattern the PR needs to add:

```bash
# Find where the branch-copy loop now lives (look for `append_message` calls)
grep -rn "append_message" --include="*.py" <dir>/ | head -20
```

Common places call sites move to:
- `cli.py` → `hermes_cli/cli_commands_mixin.py`
- `gateway/run.py` → `gateway/slash_commands.py`

### 7. Re-apply forwarding at new locations

Use `patch` to add the one-line change at each new call site. Verify each one:

```bash
grep -A1 "timestamp=msg.get" <file.py>
```

Expected output in context: the line appears in the right place within the
`append_message()` argument list, not floating elsewhere.

### 8. Verify against reviewer feedback

Go back to the original PR review and check every concern:

```bash
# Reviewer: "unrelated .gitignore hunk"
git diff upstream/main -- .gitignore  # should be empty

# Reviewer: "call site moved to cli_commands_mixin.py"
git diff upstream/main -- cli.py  # should be empty
grep -n "timestamp=msg.get" hermes_cli/cli_commands_mixin.py  # should exist
```

Keep a checklist markdown table in your response so the user can verify at a glance.

### 9. Run relevant tests

Run the test file(s) that cover the feature:

```bash
python3 -m pytest tests/test_<feature>.py -q -o addopts= -k "<keyword>"
```

Then run the full test file to check for regressions (but expect some pre-existing
failures due to the branch being based on a different base):

```bash
python3 -m pytest tests/test_<feature>.py -q -o addopts=
```

**Pre-existing failure detection:** If tests fail, check whether the failing test
file was modified by the feature commits:

```bash
git log --oneline <stale-drop-commit>..HEAD -- <failing-test-file>
```

If the file wasn't modified by any feature commit, the failure is pre-existing and
not caused by the refresh.

## Pitfalls

### Fork repo with different git history root (rebase impossible)

When the PR branch lives in a **fork** (`yitang/hermes-agent`) targeting an upstream
repo (`NousResearch/hermes-agent`), the fork's root commit may differ from upstream's.
This means `git rebase upstream/main` fails on the very first commit — no matter how
many times you retry or what merge strategy you use (`-X theirs` doesn't help on the
root commit). The symptom:

```
Rebasing (1/8172)
CONFLICT (content): Merge conflict in run_agent.py
Could not apply 7b060f57b... initital commit
```

**Recovery — clean-branch approach (do not retry the rebase):**

1. Create a fresh branch from the latest `upstream/main`:
   ```bash
   git checkout -b <branch-name>-clean upstream/main
   ```

2. Cherry-pick only the branch-specific commits that touch files NOT in upstream:
   ```bash
   # Check what files the feature commits changed vs upstream
   git diff <feature-commit>^..<feature-commit> --stat
   # Cherry-pick will likely conflict on files already on upstream
   # Instead, extract specific file content from the old commit:
   git show <feature-commit>:<file> > <file>   # careful — overwrites local
   ```

3. For files that cause cherry-pick conflicts (already on upstream), extract only
   the specific hunks you need using `git diff` or `git show`:
   ```bash
   git diff <base>..<feature-commit> -- <file>  # see the patch
   ```
   Then apply via `patch` tool with the exact insertion context.

4. For new additions (test files, new forwarding lines), apply directly:
   ```bash
   git show <feature-commit>:tests/new_test_file.py > tests/new_test_file.py
   ```

5. Delete the old branch only after confirming the clean branch is correct:
   ```bash
   git branch -D <old-branch-name>   # destructive — verify first
   ```

6. Apply unstaged changes (stashed additions) via `git stash pop`.

**When to skip the rebase entirely:** If `git rebase upstream/main` shows
`Rebasing (1/NNNN)` where N is in the thousands, check whether the very first
commit conflicts (`could not apply <sha>... initital commit`). If the root
commit differs between fork and upstream, skip the rebase and go straight to
the clean-branch approach. Waiting for a full rebase to fail is a waste of time.

### Verifying implementation against GitHub PR review comments

After applying changes, verify that every reviewer concern is addressed by
fetching the PR page and checking each point concretely:

```python
# Fetch the PR page to see review comments
web_extract(urls=["https://github.com/owner/repo/pull/NNNN"])

# Or jump to a specific review comment
web_extract(urls=["https://github.com/owner/repo/pull/NNNN#issuecomment-XXXX"])
```

Parse the reviewer's concerns and build a checklist. For each concern, run a
concrete terminal command to verify:

```bash
# Reviewer: "unrelated .gitignore hunk"
git diff upstream/main -- .gitignore | wc -l  # 0 = dropped

# Reviewer: "call site moved to cli_commands_mixin.py"
git diff upstream/main -- cli.py | wc -l  # 0 = dropped
grep -n "timestamp=msg.get" hermes_cli/cli_commands_mixin.py  # should exist

# Reviewer: "preserve platform_message_id / observed fields"
git diff upstream/main -- hermes_state.py | wc -l  # 0 = untouched
```

This is more reliable than guessing — it catches concerns you might have
misinterpreted from a quick read of the plan.

### The "don't commit" ambiguity

When a user says "just implement, don't commit," they usually mean **don't do the
final feature commit and push**. Intermediate structural commits (like the cleanup
commit after dropping stale hunks, or a rebase fixup) are part of the implementation
mechanics and are fine to perform. The subagent context should clarify:

```
Do NOT do the final commit (Task 7 in the plan). Do NOT push to remote.
Intermediate commits needed for the rebase/cleanup are OK.
```

### Rebasing onto vastly divergent main

If upstream/main has thousands of new commits since the PR was branched, the rebase
may replay hundreds of commits and produce a massive diff that includes all upstream
changes as "branch changes." This is expected — the PR's actual file changes will
still be correct. Focus on the PR-relevant files, not the raw stat count.

### Pre-existing test failures hide behind rebase

After rebase, schema version checks, API contract tests, and other tests that probe
internal state may fail because the branch's test expectations are from an older
base. These are not regressions caused by the refresh. Verify by checking git blame
on the failing assertions.

### Call-site search returns false matches

When searching for `append_message` after a rebase, you may find dozens of calls
that look similar. The right one is the **branch-copy loop** — a `for msg in history:`
or similar pattern that copies messages from one session to another. Quick
identifier: it passes `role`, `content`, and various `msg.get(...)` fields.

## Verification checklist template

```
- [ ] `.gitignore` no longer shows changes (dropped)
- [ ] `cli.py` no longer shows changes (dropped)
- [ ] `gateway/run.py` no longer shows changes (dropped)
- [ ] `hermes_state.py`, `gateway/session.py`, etc. no longer show changes (already on upstream)
- [ ] `<new-cli-file>` has `timestamp=msg.get("timestamp")` in branch copy loop
- [ ] `<new-gateway-file>` has `timestamp=msg.get("timestamp")` in branch copy loop
- [ ] `<existing-file>` still has `timestamp=msg.get("timestamp")` after rebase
- [ ] All relevant tests pass
```
