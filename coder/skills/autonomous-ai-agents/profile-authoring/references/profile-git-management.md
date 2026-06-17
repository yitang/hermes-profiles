# Version-Controlling Hermes Profiles with Git

Reference for the `profile-authoring` skill — detailed `.gitignore`, setup, and common workflows.

## Full `.gitignore` for a Hermes Profiles Repo

```gitignore
# === Secrets & credentials ===
.env
auth.json

# === Runtime state & databases ===
state.db
state.db-shm
state.db-wal
processes.json
*.lock

# === Cache & temp files ===
audio_cache/
image_cache/
cache/
*.cache
__pycache__/
*.pyc
*.pyo

# === Session & conversation data ===
sessions/
logs/
*.log
.hermes_history
interrupt_debug.log
.skills_prompt_snapshot.json

# === Model & provider caches ===
models_dev_cache.json
ollama_cloud_models_cache.json
provider_models_cache.json
model_catalog.json

# === Sandboxes & checkpoints ===
sandboxes/
checkpoints/
pastes/
workspace/
home/

# === Other runtime artifacts ===
.restart_*
.update_check
auth.lock
profile.yaml
skins/
bin/
.hub/
node_modules/
yarn.lock
package-lock.json

# === Profile-level runtime state (per-profile) ===
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

# === Curator metadata (auto-generated, changes every session) ===
**/.usage.json
**/.bundled_manifest
**/.curator_state

# === Per-user preference: content tracked elsewhere ===
**/scripts/tapo-*
```

## Fixing Already-Tracked Metadata

If you imported profiles and metadata files are already tracked, they won't be suppressed by `.gitignore` until you `rm --cached`:

```bash
cd ~/para/1_projects/hermes-profiles
git rm --cached '**/.usage.json' '**/.bundled_manifest' '**/.curator_state'
git commit -m "chore: stop tracking curator metadata (auto-generated noise)"
```

## What Each Ignored Pattern Does

| Pattern | What it suppresses |
|---------|-------------------|
| `**/gateway.pid` | Gateway process ID (changes every restart) |
| `**/gateway_state.json` | Gateway connection state |
| `**/channel_directory.json` | Message platform routing table |
| `**/response_store.db*` | Response store SQLite + WAL |
| `**/skill_store.db*` | Skill store SQLite |
| `**/cron/jobs.json` | Cron job schedule definitions |
| `**/cron/output/` | Cron job output logs |
| `**/lsp/` | LSP language server dependencies (node_modules) |
| `**/plans/` | Auto-generated implementation plans |
| `**/memories/MEMORY.md` | Agent's own memory notes (auto-managed by Hermes) |
| `**/.curator_backups/` | Curator pre-prune backups |
| `**/.usage.json` | Per-skill usage tracking |
| `**/.bundled_manifest` | Curator's bundled skill manifest |
| `**/.curator_state` | Curator's current state |

## Config Format Migration

Hermes rewrites `config.yaml` to its current internal format when a profile is loaded. The old format (v0.16) had top-level `model:`, `providers:`, `fallback_providers:`, `toolsets:` keys. The new format nests everything under `_config_version: N` and `agent:`, `terminal:`, `gateway:` sections.

**This is a one-time diff per Hermes version upgrade.** Commit it — the semantics are identical.

## Detecting Curator Changes

To see only human-authored changes (skip auto-deleted bundled skills):

```bash
# Changes you made (excluding curator deletions/additions)
git diff --diff-filter=M --name-only

# What the curator pruned
git diff --diff-filter=D --name-only

# What the curator installed
git diff --diff-filter=A --name-only
```

## Common Workflows

```bash
# Check for new runtime artifacts after a session
cd ~/para/1_projects/hermes-profiles
git status

# Quick commit of config/USER.md/script changes only
git add -u ':!**/.usage.json' ':!**/.bundled_manifest' ':!**/.curator_state'
git commit -m "chore: sync profile changes"

# Preview what a full commit would look like
git diff --stat

# Revert accidental curator changes you don't want
git checkout -- tinker/skills/autonomous-ai-agents/claude-code/
```
