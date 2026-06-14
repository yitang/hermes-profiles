---
name: commit-and-push-notes
description: Use when the user asks to commit, push, or back up all Zettelkasten notes across their meta-* vaults. Runs git commit + push on every ~/matrix/*/meta-*/notes/ directory and reports a change summary.
---

# Commit and Push Notes

Walks every `~/matrix/*/meta-*/notes/` directory, commits any changed
notes, pushes to the remote, and prints a summary of how many repos
and files were affected.

The actual work is done by `commit-and-push-notes.sh` in this skill
directory. The skill document explains when to use it and how it
works.

## Bash Script Location

```
skills/commit-and-push-notes/commit-and-push-notes.sh
```

Run directly:

```bash
./commit-and-push-notes.sh                        # auto date message
./commit-and-push-notes.sh "my custom commit msg"  # custom message
```

Or invoke by path:

```bash
bash /home/tangyi/.hermes/profiles/luhmann/skills/commit-and-push-notes/commit-and-push-notes.sh
```

## Which Repos It Covers

| Path | Notes count |
|---|---|
| `~/matrix/tools/meta-tools/notes` | ~169 org files |
| `~/matrix/hobbies/meta-hobbies/notes` | ~176 org files |
| `~/matrix/learning/meta-learning/notes` | ~26 org files |
| `~/matrix/ds/meta-ds/notes` | ~129 org files |
| `~/matrix/finance/meta-finance/notes` | ~2 files |
| `~/matrix/health/meta-health/notes` | ~7 files |

**Total:** 6 repos, ~500+ org notes across all vaults.

## What It Does

For each repo with changes in `notes/`:

1. `git add notes/` — stages all changes in the notes folder
2. `git commit -m "..."` — commits with your message or auto date
3. `git push origin <branch>` — pushes the current branch

## What It Reports

After running, you get:

```
  ✓ meta-health — clean, nothing to commit
  → meta-tools — 3 file(s) changed
  → meta-learning — 1 file(s) changed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Summary: 2 / 6 repos had changes
  Total files/notes changed: 4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## When to Use

- After a session of taking notes across multiple vaults
- Before shutting down or switching machines
- When the user says "commit my notes" or "push my vault"
- As part of a periodic backup habit
