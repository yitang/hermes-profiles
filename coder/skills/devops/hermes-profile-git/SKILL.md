---
name: hermes-profile-git
description: "Version-control Hermes profiles with git. Covers initial repo setup, what to track vs ignore, config format migration noise, curator pruning churn, and maintaining a clean diff."
author: Hermes Agent
tags: [hermes, git, profiles, version-control, devops]
---

# Hermes Profile Git Management

Hermes profiles are symlinked directories (`~/.hermes/profiles/<name>/` → git repo). Every runtime write lands directly in the working tree. This skill keeps the repo clean.

## Setup

```bash
# One-time: clone profiles into your desired location
git clone git@github.com:yitang/hermes-profiles.git ~/para/1_projects/hermes-profiles

# The symlink (profiles will be read from here, not the canonical git dir)
# For Hermes, the symlink goes: ~/.hermes/profiles/ → your repo
ln -sf ~/para/1_projects/hermes-profiles ~/.hermes/profiles
```

## What to Track vs Ignore

### Tracked (meaningful diffs)
| Path | Why |
|---|---|
| `<profile>/config.yaml` | Model, provider, agent settings |
| `<profile>/memories/USER.md` | User profile — preferences, corrections |
| `<profile>/skills/<category>/<name>/SKILL.md` | User-created skill content |
| `<profile>/skills/<category>/<name>/references/` | Skill-specific reference material |
| `<profile>/skills/<category>/<name>/scripts/` | Re-runnable scripts |
| `<profile>/scripts/` | Profile-level scripts (e.g. cron scripts) |

### Ignored (gitignore)
| Pattern | Why noise |
|---|---|
| `.usage.json` | Changes every session — usage tracking |
| `.bundled_manifest`, `.curator_state` | Curator metadata — auto-generated |
| `channel_directory.json`, `gateway.*`, `response_store.db*` | Runtime PID / gateway state / DB WAL |
| `cron/jobs.json`, `cron/output/` | Cron definitions and execution logs |
| `lsp/` | LSP server node_modules (auto-installed) |
| `plans/` | Hermes-generated session plans |
| `memories/MEMORY.md` | Agent memory — auto-managed, changes every session |
| `.curator_backups/` | Curator pre-prune backups |
| `.env`, `auth.json`, `state.db*`, `sessions/`, `logs/` | Secrets and transient data |

### Minimal .gitignore (starter)
Add to your repo root's `.gitignore`:

```gitignore
# === Secrets & credentials ===
.env
auth.json

# === Runtime state & databases ===
state.db
state.db-shm
state.db-wal
response_store.db*
skill_store.db*
processes.json
*.lock

# === Cache & temp files ===
audio_cache/
image_cache/
cache/
*.cache
__pycache__/

# === Session & conversation data ===
sessions/
logs/
*.log

# === Model & provider caches ===
*models_cache.json
model_catalog.json

# === Sandboxes & checkpoints ===
sandboxes/
checkpoints/

# === Other runtime artifacts ===
.restart_*
.update_check
profile.yaml
skins/
bin/
.hub/

# === Profile-level runtime state ===
**/gateway.pid
**/gateway_state.json
**/channel_directory.json
**/cron/jobs.json
**/cron/output/
**/lsp/
**/plans/
**/memories/MEMORY.md
**/.curator_backups/

# === Curator metadata ===
**/.usage.json
**/.bundled_manifest
**/.curator_state
```

## Dealing with Common Noise Sources

### Config format migration
When Hermes upgrades, it rewrites `config.yaml` to a new format version (`_config_version: N+1`). The old flat format (~/.hermes v0.16) versus new nested format. This is a one-time diff per profile. After committing, subsequent upgrade diffs are small.

**Pitfall**: Don't review the full config diff line-by-line during migration. Verify critical fields (model, provider, agent settings) and commit. The structural reorganisation has same semantics, different layout.

### Curator pruning
The curator (`curator.prune_builtins: true`) periodically deletes bundled/built-in skills it considers stale. This generates:
- 30-60 deleted files (`D` in git status)
- Modified `.curator_state`, `.bundled_manifest` metadata
- Possible new replacement skills with similar references (git detects renames)

**Action**: Stage the deletions as a single commit. If the curator deleted something you wanted, restore from git history.

### Detecting important vs noise diffs
Before committing, ask:
- Did *I* change this? → likely noise
- Is it under `.usage.json`, `.curator_state`, `.bundled_manifest`? → noise
- Is it a skill SKILL.md with real content changes? → commit
- Is it config.yaml? → check: model/provider change (commit) or format migration (commit)
- Is it in `.gitignore`? → shouldn't appear in status

## Cross-Profile Shared Preferences

To avoid duplicating preferences across every profile's USER.md:

1. Create a skill in an `external_dirs` path:
   ```yaml
   # ~/.hermes/config.yaml
   skills:
     external_dirs:
     - ~/para/2_areas/agents/skills
   ```
2. Create `~/para/2_areas/agents/skills/<category>/<name>/SKILL.md` with frontmatter.
3. Reference it from each profile's `USER.md`:
   ```
   Preferences (editor, Python, Org mode): load skill_view(name="<skill-name>").
   ```

## Tracking Changes Over Time

The value of version control here is seeing:
- When you switched models/providers (config.yaml changes)
- What skills you created or removed
- How your preferences evolved (USER.md history)
- When the curator pruned something (restore if needed)
