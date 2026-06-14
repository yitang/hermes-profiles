---
name: matrix-repo-audit
description: Domain-by-domain audit of the ~/matrix/ PARA repository and proposal for migration to ~/para/. Covers structure inventory, git activity analysis, artifact detection, and PARA classification mapping.
---

# Matrix Repository Audit

Use this skill when auditing any domain under `~/matrix/` (ds, finance, health, hobbies, learning, reflect, tools) and proposing migration into the `~/para/` workspace.

## Core Principles

- **Observe first, act never.** Present findings for approval before any structural change.
- **Distinguish activity from volume.** A large repo full of old notebooks is NOT "active" just because it's big.
- **Brain dump ≠ project.** Scattered `.org` files without clear scope, deadline, or next action are reference material or archive — not active work.
- **Preserve history.** Git repos remain intact; migration is about organization, not deletion of history.
- **User copies manually, doesn't trust auto-move scripts.** Offer clear instructions with copy commands and verification steps.

## Phase 1: Domain Survey

### Step 1: Structure Inventory
```bash
find ~/matrix/<domain> -maxdepth 2 -not -path '*/.git/*' -not -name '*.db-wal' -not -name '*.db-shm' | sort
du -sh ~/matrix/<domain>/*/ 2>/dev/null | sort -rh
```

### Step 2: AGENTS.md Check
Before diving into git, check for `AGENTS.md` at the domain root. It often encodes:
- Active projects and their current status
- PARA-style project management frameworks in use
- Naming conventions and supplier preferences
- Agent guidelines that inform classification decisions

### Step 3: Git Activity Analysis (for every `.git` directory found)
```bash
cd ~/matrix/<domain>/<subdir>
git log -1 --format='%ai %s'                # last commit timestamp + message
git log --since='90 days ago' --oneline | wc -l   # recent commit count
git status --short                          # uncommitted changes (staged, modified, untracked)
```

Key signals to watch:
- **Staged deletions** (` D`) — files already removed from disk but still in git index; these will cause confusion if not committed. Check whether files landed somewhere else (e.g., moved to para).
- **Untracked files** (`??`) — content that was never committed; may exist only as agent-side cache or draft.
- **Deleted-from-git directories** — check the deletion commit: `git diff --name-status <commit>^..<commit>` to see everything removed in one sweep. Search git history for content that was tracked before deletion.

### Step 4: Artifact Detection
Flag these non-org files mixed with source:

| Artifact | What it is | Action |
|----------|-----------|--------|
| `.aux`, `.log` (LaTeX) | Build artifacts from `garden_studio.tex` etc. | Remove or gitignore |
| `.aider.*`, `.agent-shell/` | AI/cache files | Gitignore (not content to migrate) |
| `assets/org-download/` | Screenshot caches from org-download.el | Evaluate — most are stale web screenshots worth offloading |
| `.db-shm`, `.db-wal` | SQLite temp files | Should already be gitignored |
| `*.db-wal` in root domain dirs | Database write-ahead logs | Clean before migration |
| PDFs inside project dirs | Downloaded plans/specs (e.g., LSWW furniture plans) | Reference artifacts; evaluate for 3_resources/ move |
| `.dir-locals.el` at multiple depths | Orphaned emacs config — check if any are projectile roots | Keep if useful, remove if orphaned |

### Step 5: Git Deletion Forensics
When content disappears from git (e.g., in a cleanup commit):

```bash
# What was deleted in a specific commit?
git diff --name-status <commit>^..<commit> | grep '^D'

# Is the deleted content still tracked in HEAD?
git ls-tree -r HEAD --name-only | grep '<path>'

# Was it ever committed to git (vs. filesystem-only)?
git log --all --oneline -- "**/<filename>*" 

# Check if it landed in a migration target
find ~/para -name "*<keyword>*" 2>/dev/null
```

**Critical pattern:** Untracked directories (like `.agent-shell/transcripts/`) exist only on disk. If the parent directory was deleted from both disk and git, that content is gone — there is no recovery path. AGENTS.md may reference such directories as if they were tracked.

## Phase 2: Classification

Label each subdirectory using these criteria:

| Label | Criteria | PARA Destination |
|-------|----------|-----------------|
| `ACTIVE` | Commits ≤30 days ago, or uncommitted edits in `.org` files | `1_projects/` (if scoped) or `2_areas/` |
| `SEMI-ACTIVE` | Last commit 30–180 days ago, some recent mtime changes | `3_resources/notes/<category>/` |
| `ARCHIVE-LIKE` | Last commit >180 days, no uncommitted edits, stale `.org` content | `7_archive/` or `3_resources/` (if still useful) |
| `LEARNING/STUDY` | Academic material, course notes, homework, slides | `2_areas/learning-and-development/` or `3_resources/` |
| `BRAIN-DUMP` | No clear scope, mixed topics, no next actions | `4_inbox/` for review, then classify |

## Phase 3: PARA Migration Mapping

Typical mappings for matrix domains:

| Matrix Domain | Proposed PARA Placement | Rationale |
|--------------|------------------------|-----------|
| DIY projects (wall-cabinets, led-lighting) | `1_projects/` | Active, scoped, deadline-driven |
| Computing notes / hardware reviews | `3_resources/computing/` or `2_areas/computing-infrastructure/` | Reference material |
| Self-hosted services config | Keep as-is or `2_areas/self-hosting/` | Infrastructure domain, not PARA project |
| Garden/studio projects | `1_projects/<project-name>/` or `3_resources/` depending on status | Check completion state |
| Workshop/diy reference notes | `2_areas/workshop-maintenance/` | Ongoing area, not single project |
| Video games / hobbies | `3_resources/gaming/` | Reference hobby |
| Domain root with double-nested name (`hobbies/hobbies/`) | Rename to `meta-*` (e.g., `meta-hobbies/`), then apply mapping above | Avoids confusing directory naming; relative org links survive the rename automatically |

## Pre-Migration Checklist

Before proposing any move, run through these:
1. **Asset audit**: Has `assets/org-download/` been classified with the asset-audit-and-archive skill? Are orphaned images identified?
2. **Git hygiene**: Any staged deletions (` D`) committed? Any build artifacts in index?
3. **AGENTS.md sanity check**: Do referenced projects actually exist in git history, or are they filesystem-only agent outputs?
4. **Naming convention audit**: Are there double-nested directories like `domain/domain/` that should be renamed to `meta-*`?

## Phase 4: Output Format

Always produce findings in this structure:

```markdown
## <DOMAIN> Audit

### Structure
<ASCII tree of subdirs with size indicators>

### Activity Classification
| Subdir | Last Commit | Recent Commits | Uncommitted | Classification |

### Issues Found
- **N**: Issue name — evidence | why it matters
- ...

### Cleanup Proposal
1. Commit: <what>
2. Clean: <artifacts to remove>
3. Consolidate: <merge candidates>
4. Archive: <inactive repos>

### PARA Migration Mapping
| Current Location | PARA Destination | Action |
|-----------------|-----------------|--------|
```

Then present a summary table of all domains and ask which to tackle first. Never execute moves without explicit user instruction.

## Pitfalls

1. **Don't assume large = active.** A 3GB repo from 2022 is archival, not current.
2. **Don't treat every `.org` file as a project.** Brain dumps are reference material.
3. **Don't touch `reflect/` diaries** — personal journaling predates PARA and serves a different cognitive purpose. Flag for user decision only.
4. **Never use `rm -rf`.** Use `find` with `-print` to show what would be deleted, let user approve.
5. **AGENTS.md may reference directories/files that were never committed.** Always verify with `git log --all` before reporting something as "in git" or "deleted from git".
6. **Staged deletions (` D` in git status) mean files are gone from disk but not yet removed from the index.** They need to be committed, not ignored. If the user says they've moved the content elsewhere (to para), verify the destination first.
7. **Asset directories can balloon silently.** `org-download/` screenshots accumulate rapidly and dominate repo size — flag for review during every audit.
8. **.dir-locals.el at multiple depths may be orphaned config.** Not all are projectile roots; check whether any subdirectory is actually a projectile root before treating them as intentional.
9. **Double-nested directory names** like `hobbies/hobbies/` indicate the domain itself has the same name as its contents. This can be resolved by renaming the inner directory to use a `meta-*` prefix (e.g., `hobbies/meta-hobbies/`). When renaming, org `[[file:assets/...]]` relative references survive automatically since both the org file and asset directories move together; only hardcoded absolute paths need updating.
10. **Content may exist on disk but never be committed to git.** Agent-generated directories (`.agent-shell/`, tool-output-only dirs like `project_management_agent/`) exist as filesystem state but have no commit history. If a parent directory is deleted from both disk and git, that content is unrecoverable — AGENTS.md or skill descriptions may reference such directories as if they were tracked. Always verify with `git log --all` before reporting content status.
