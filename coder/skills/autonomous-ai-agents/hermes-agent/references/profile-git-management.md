# Version-Controlling Hermes Profiles with Git

Hermes profiles are stored in `~/.hermes/profiles/<name>/`. If you symlink that
directory to a git repo, every runtime write lands in your working tree. This
reference explains what to track, what to ignore, and how to keep diffs clean.

## Setup

```bash
# One-time: clone profiles into PARA (or wherever)
git clone git@github.com:<user>/hermes-profiles.git ~/para/1_projects/hermes-profiles

# Replace the default profile dir with the repo
mv ~/.hermes/profiles ~/.hermes/profiles.bak
ln -s ~/para/1_projects/hermes-profiles ~/.hermes/profiles
```

Each subdirectory in the repo is a profile (coder, tinker, researcher, etc.).
The profile name _is_ the directory name.

## What to Track

| File | Why |
|------|-----|
| `<profile>/config.yaml` | Model, provider, agent settings — meaningful changes |
| `<profile>/memories/USER.md` | User profile preferences |
| `<profile>/skills/<category>/<name>/SKILL.md` | User-created skills (the valuable part) |
| `<profile>/skills/<category>/<name>/references/` | Skill reference material |
| `<profile>/script s/*` | Cron scripts, automation scripts |
| `<profile>/skills/<category>/<name>/scripts/` | Skill-owned runnable scripts |

## What to Ignore (runtime / auto-generated)

Add these patterns to `.gitignore`:

```gitignore
# === Runtime artifacts ===
**/gateway.pid
**/gateway_state.json
**/channel_directory.json
**/response_store.db*
**/skill_store.db*
**/cron/jobs.json
**/cron/output/
**/lsp/
**/plans/
**/memories/MEMORY.md
**/.curator_backups/

# === Curator metadata (changes every session) ===
**/.usage.json
**/.bundled_manifest
**/.curator_state
```

Run `git rm --cached` on any of the metadata files that are already tracked
before adding the gitignore patterns — otherwise gitignore won't suppress them.

## Config Format Migration

When Hermes upgrades, it may rewrite `config.yaml` to a new format version
(`_config_version: N`). The diff looks huge (complete rewrite) but the
semantics are usually identical. This is a one-time noise event per upgrade.

To detect:
```bash
git diff <profile>/config.yaml | head
# Look for: -model:\n-  default: ...\n+_config_version: 29
```

These rewrites are safe to commit — they're the current format Hermes expects.

## Curator Operations

The Hermes curator (`hermes curator run`) prunes unused bundled skills and
reorganises others. When it runs, you'll see in `git status`:

- **D** entries — deleted bundled skills the curator pruned
- **M** entries — surviving skills with minor metadata updates
- **??** entries — new consolidated skills the curator created

This is noisy on first curator run after cloning. After one commit to sync,
subsequent curator runs produce fewer changes (only genuine additions/removals).

The curator only touches skills with `created_by: "agent"` provenance. It
never deletes — max action is archive under `~/.hermes/skills/.curated/`.
Pinned skills are exempt.

## Keeping Diffs Clean

1. Commit promptly after import — noise compounds across sessions
2. Gitignore the metadata files before first commit
3. When curator runs, review: were skills you used deleted? pin them first:
   `hermes curator pin <skill-name>`
4. `**/plans/` contains auto-generated plans from sessions — track meaningful
   plans in your project repo's `docs/` or `.hermes/plans/` instead

## Summary

The delta you actually care about day-to-day:
- Skills you created or modified (your work)
- Config changes (model switches, provider changes)
- USER.md updates
- Cron script changes

Everything else is Hermes housekeeping.
