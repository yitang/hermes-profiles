---
name: hermes-profile-maintenance
description: "Sync, compare, upgrade, and deploy Hermes profiles between live ~/.hermes/profiles/ and a git repo."
author: Hermes Agent
platforms: [linux, macos]
---

# Hermes Profile Maintenance

Use this skill when maintaining a git-versioned directory of Hermes profiles — syncing live state into the repo, reviewing diffs, upgrading config formats, deleting unused profiles, and deploying via symlink.

## Workflow

### 1. Understand the landscape

Before touching anything, understand what's tracked vs ignored:

```bash
# Check if symlink or real directory
file ~/.hermes/profiles

# Compare profile lists
ls ~/.hermes/profiles/
ls ~/para/1_projects/hermes-profiles/
# Note any profiles in live that aren't in repo (and vice versa)
```

For an authoritative roster of tracked profiles, their personas,
exclusive skills, and structural invariants, see the reference file:
`references/profile-inventory.md`. All six profiles run the same model
(deepseek-v4-flash) with identical config.yaml — differentiation is
purely SOUL.md + USER.md + curated skill selection.

The `.gitignore` usually handles:
- Runtime state: `state.db*`, `cron/`, `sessions/`, `logs/`, `plans/`
- Auto-generated curator metadata: `.usage.json`, `.bundled_manifest`, `.curator_state`
- Secrets: `.env`, `auth.json`
- Session data: `sessions/`, `.hermes_history`
- Temp/cache: `cache/`, `audio_cache/`, `image_cache/`

### 2. Sync live → repo with rsync

When live profiles have accumulated changes (Hermes curator updates, config tweaks, new skills) and you want to bring them into git:

```bash
rsync -av --exclude='.git/' ~/.hermes/profiles/ ~/para/1_projects/hermes-profiles/
```

This copies ALL files including runtime artifacts, but `.gitignore` prevents them from being tracked.

### 3. Remove profiles that shouldn't be in the repo

Delete profiles the user no longer wants:

```bash
git rm -r <profile-name>
rm -rf <profile-name>/
```

### 4. Review diffs & cherrypick

```bash
git status --short
# M = modified tracked file
# D = staged for deletion
# ?? = new untracked file
```

For each modified file, decide: keep the repo version or accept the live version?

**Common diff categories:**

| Diff type | Typical cause | Decision |
|-----------|-------------|----------|
| `config.yaml` format change | Hermes auto-wrote different format | Prefer repo if it's the target version |
| `SOUL.md` → generic boilerplate | Hermes overwrote custom persona | **Revert** (`git checkout --`) |
| `skills/*/SKILL.md` deletions | Hermes curator pruned bundled skills | User preference — revert or accept |
| API keys in config | Placeholder vs real key | Never commit real keys — use `.env` |
| `memories/USER.md` | Agent updated user profile | Accept if accurate |

Revert a file to repo version:
```bash
git checkout -- <file>
```

### 5. Delete unused profiles

```bash
git rm -r <profile-name>
rm -rf <profile-name/
```

### 6. Upgrade configs to target format

When upgrading config formats (e.g., v23/v27/no-version → v29), use the most up-to-date profile's config as a template:

```bash
cp coder/config.yaml <target-profile>/config.yaml
```

This replaces the entire config. Key settings that are universal:
- `model.default`, `model.provider` — same across all profiles
- `custom_providers` — provider definitions
- `providers` — name mappings

Per-profile customization stays in `SOUL.md` and skill selection.

### 7. Commit changes

```bash
git add -A
git commit -m "descriptive message"
```

### 8. Deploy via symlink

Replace the live profiles directory with a symlink to the repo:

```bash
# Backup first
cp -a ~/.hermes/profiles ~/.hermes/profiles.bak

# Switch to symlink
rm -rf ~/.hermes/profiles
ln -sf ~/para/1_projects/hermes-profiles ~/.hermes/profiles
```

After symlink, Hermes writes runtime state (cron, sessions, state.db) into the repo working tree — gitignored, so `git status` stays clean of runtime noise.

### 9. Handle the default profile

The default profile lives at `~/.hermes/` (not inside `profiles/`). It's the fallback when no `--profile` is specified. To track it:

```bash
mkdir -p ~/para/1_projects/hermes-profiles/default
cp ~/.hermes/config.yaml ~/para/1_projects/hermes-profiles/default/
cp ~/.hermes/SOUL.md ~/para/1_projects/hermes-profiles/default/
cp ~/.hermes/memories/USER.md ~/para/1_projects/hermes-profiles/default/memories/
rsync -a ~/.hermes/skills/ ~/para/1_projects/hermes-profiles/default/skills/
```

May need to set `hermes profile use <name>` to make a named profile the sticky default.

## Skill sources: built-in vs curated

Hermes loads skills from multiple sources. Understanding this prevents confusion about why some skills are in the profiles repo and others aren't:

| Source | Lives in | Tracked in git? | Example |
|--------|----------|-----------------|---------|
| **Built-in / plugin** | Hermes agent installation (`~/.hermes/profiles/<profile>/skills/.bundled_manifest`) | No (gitignored auto-generated) | `iterative-research`, `deep-research`, `web-design-guidelines` |
| **External dirs** | `~/.agents/skills/`, `~/para/2_areas/agents/skills/` | No (separate repo) | Shared skills used across profiles |
| **Profile curated** | `<profile>/skills/<category>/<name>/SKILL.md` | Yes (git-tracked) | `emacs-config`, `personal-finance-data`, `osmo-hardwax-oil` |

**Built-in skills** (like `iterative-research` and `deep-research`) are available to every profile automatically. You don't need to add them to a profile's `skills/` directory. The SOUL.md can reference them freely — they'll resolve at runtime.

**Curated skills** in the git repo are additive — they extend the built-in set. This is where per-profile specialisation lives.

## Profile differentiation: the skill audit workflow

Profiles naturally bloat over time — rsync copies everything, Hermes curator adds curated skills, and soon every profile carries the same 70+ skills regardless of persona. This dilutes the multi-profile value.

### Audit method (what we did this session)

1. **Inventory tracked skills** per profile:
   ```bash
   git ls-files -- '*/skills/*/SKILL.md' | sed 's|/SKILL.md$||' | while read d; do
     echo "${d#*/skills/}"
   done | sort
   ```

2. **Map each skill against the profile's SOUL.md** — does the skill's domain match the intended persona? Ask: "Would a finance agent need Apple Notes? Would a woodworking agent need ML model serving?"

3. **Categorise each skill**: Keep / Prune / Consider. Prune aggressively — the built-in skills are always available as fallback. Consider means "marginal — keep for now, flag for next audit."

4. **Prune in a worktree** for safe review:
   ```bash
   git worktree add -b skill-prune /tmp/hermes-profiles-prune
   cd /tmp/hermes-profiles-prune
   git rm -rq --ignore-unmatch <profile>/skills/<category>/<name>
   # Review: git diff --stat / git status
   ```

### Decision rules

| If the skill is... | Then... |
|--------------------|---------|
| From the shared template (apple/*, media/*, creative/*, mlops/*, research/*) | Prune unless it directly supports the SOUL.md persona |
| Unique to one profile (osmo-hardwax-oil, emacs-config, personal-finance-data) | **Keep** — this is the differentiation |
| A core workflow skill (plan, systematic-debugging, hermes-agent) | Consider keeping in all profiles — lightweight and universally useful |
| Red-teaming/godmode, yuanbao, dogfood | Prune — experimental or platform-specific |

### Key principle

> Multi-profile differentiation comes from DIFFERENT skills, not the same skills with a different SOUL.md. If two profiles load the same 70 skills, switching between them changes nothing.

### After pruning

1. Remove orphaned DESCRIPTION.md files from now-empty category dirs:
   ```bash
   git rm --ignore-unmatch <profile>/skills/creative/DESCRIPTION.md
   ```
2. Commit with a message like `chore(<profile>): prune skills to match SOUL.md persona`
3. The user can review the diff before merging from the worktree:
   ```bash
   cd /tmp/hermes-profiles-prune
   git diff main --stat
   ```

## Pitfalls

- **Don't symlink mid-session.** The running Hermes process may have file handles open to the old profiles directory. Changes take effect on next session start.
- **Recursive path trap.** If a profile has a `home/` directory containing a recursive `.hermes/profiles/` pointer, `mv` will fail. Use `rm -rf` instead of `mv` when replacing the profiles directory.
- **state.db mismatch.** After symlink, the repo's state.db is used (copied from live during rsync). If the live session is running, its state.db may be newer. Copy it over before switching:
  ```bash
  cp ~/.hermes/profiles/coder/state.db ~/para/1_projects/hermes-profiles/coder/state.db
  ```
- **Secrets (.env, auth.json) are gitignored.** After rsync, they exist in the repo worktree but won't commit. After symlink, Hermes reads them from the repo location. Copy them over if missing.
- **Config format changes are destructive.** When you `cp coder/config.yaml` to another profile, you lose any profile-specific settings. The main thing you get is the model/provider setup. Profile identity comes from SOUL.md, not config.yaml.
- **Git tracking metadata files.** Files like `.bundled_manifest`, `.usage.json`, `.curator_state` change every session. Keep them gitignored.

## Staying aware of upstream changes

After the symlink is in place, Hermes curator writes changes through the symlink into the repo working tree. To see what changed:

```bash
cd ~/para/1_projects/hermes-profiles
git status
git diff --stat
```

Optionally set up a weekly cron to report changes:
```bash
cronjob action=create schedule="0 9 * * 1" \
  name="profile-diff-report" \
  workdir=/home/tangyi/para/1_projects/hermes-profiles \
  prompt="Check git status and show a summary of what changed in the hermes-profiles repo this week."
```
