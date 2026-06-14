---
name: knowledge-migration
description: Systematic audit and migration of matrix-style personal knowledge repos into PARA structure. Covers domain-by-domain survey, activity classification, artifact detection, and structured migration proposals.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [para, matrix, migration, audit, knowledge-management]
    related_skills: [asset-audit-and-archive, org-mode-emacs, obsidian]
---

# Knowledge System Migration

Systematic audit and migration of matrix-style personal knowledge repos into PARA structure. Covers domain-by-domain survey, activity classification, artifact detection, and structured migration proposals.

## Trigger Conditions

- User says "audit my <domain>", "check <matrix-subdir>", "how should I migrate <folder> to PARA", or similar phrasing about reorganizing a personal knowledge repo
- Any task involving restructuring `~/matrix/` subdirectories into `~/para/`
- When asked to review what's in a domain before deciding whether to move it

## Phase 1: Domain-by-Domain Survey

### Step 1: Structure Inventory
```bash
find ~/matrix/<domain> -maxdepth 2 -not -path '*/.git/*' \
  -not -name '*.db-wal' -not -name '*.db-shm' | sort
du -sh ~/matrix/<domain>/*/ 2>/dev/null | sort -rh
```

### Step 2: Git Activity Analysis (for every .git directory found)
```bash
cd ~/matrix/<domain>/<subdir>
git log -1 --format='%ai %s'          # last commit timestamp + message
git log --since='90 days ago' --oneline | wc -l   # recent commit count
git status --short | head -20        # uncommitted/staged changes
```

### Step 3: Classification — Label each subdirectory

| Label | Criteria | PARA Destination |
|-------|----------|-----------------|
| `ACTIVE` | Commits ≤30 days ago, or uncommitted `.org` edits | `1_projects/` (if scoped) or `2_areas/` |
| `SEMI-ACTIVE` | Last commit 30–180 days ago, some recent mtime changes | `3_resources/notes/<category>/` |
| `ARCHIVE-LIKE` | Last commit >180d, no uncommitted edits, stale `.org` content | `7_archive/` or `3_resources/` |
| `LEARNING/STUDY` | Academic material, course notes, slides | `2_areas/learning-and-development/` or `3_resources/` |
| `BRAIN-DUMP` | No clear scope, mixed topics, no next actions | `4_inbox/` for review, then classify |

### Step 4: Artifact Detection — Flag non-org files mixed with source
- **LaTeX build artifacts** (`.aux`, `.log`, `.out`) — clean before commit/migrate
- **Aider/AI caches** (`.aider.*`, `.agent-shell/`)
- **Org-download screenshots** (`assets/org-download/`) — often stale web screenshots from years ago; run the `asset-audit-and-archive` skill on these repos to systematically classify as active (referenced by current org files) vs. orphaned, before migration
- **PDF textbooks / data files** — move to `3_resources/` or archive
- **Backup files** (`*.el~`, `*.orig`) — noise, flag for removal
- **Empty placeholder files** (0-byte `.org`) — likely abandoned

## Phase 1.5: Asset Audit (Prerequisite for repos with `assets/`)

Before migration, run the `asset-audit-and-archive` skill on any repo with an `assets/` directory. Org-download screenshots accumulate rapidly and can dominate repo size (e.g., a 463MB hobbies repo where ~150MB was stale screenshots). The audit classifies assets as "active" (referenced by current org files) vs. "orphaned" (never referenced, or only referenced by deleted/moved org files). Only move orphaned files — moving an active file breaks org image links. See `asset-audit-and-archive` skill for the full procedure and Python audit script.

## Phase 2: Cross-Domain Pattern Analysis

Look for these systemic issues across all domains being audited:
1. **Duplicated structure** — e.g., every subdir has its own `main.org`, `.gitignore`, `.dir-locals.el`. Is intentional organization or accidental duplication?
2. **Orphaned config** — `.dir-locals.el` files scattered in subdirs that aren't projectile roots
3. **Name collisions** — e.g., `meta-finance/` vs `finance/`; double-nesting like `hobbies/hobbies/` (domain named "hobbies" with a subdir also named "hobbies")
4. **Size outliers** — repos disproportionately large relative to activity (e.g., 3GB repo with last commit from 2022)

## Phase 3: PARA Migration Proposal

Map findings to PARA destinations using this decision logic:

| Current Pattern | Proposed Destination | Rationale |
|----------------|---------------------|-----------|
| Scoped project with clear scope/deadline (e.g., wall cabinets, kitchen LED lighting) | `1_projects/<name>/` | Fits PARA's end-dated project model |
| Ongoing domain/area (self-hosting, computing, workshop maintenance) | `2_areas/<category>/` | Recurring responsibility, no deadline |
| Reference material / notes | `3_resources/<topic>/` | Learning/reference content |
| Completed/abandoned projects | `7_archive/` | Historical record |
| Scattered brain dumps, unclear scope | `4_inbox/` pending review | Unknown classification until triaged |

## Phase 4: Cleanup Recommendations

For each domain, propose:
1. **Commit** — uncommitted but valuable changes (staged deletions, small edits)
2. **Clean** — build artifacts, caches, empty dirs, backup files
3. **Consolidate** — merge similar subdirs, flatten deep nesting
4. **Archive** — move completed/abandoned repos to `7_archive/`
5. **Migrate** — copy (not move) to para, then verify

## Pitfalls

1. **Don't assume large = active.** A 3GB repo from 2022 is archival, not current. Always check git log timestamps.
2. **Don't treat every `.org` file as a project.** Brain dumps are reference material until scope/deadline/next-action is established.
3. **Don't touch personal journaling/diaries** (e.g., `reflect/`) — they serve different cognitive purposes than PARA projects. Flag for user decision only.
4. **Never use `rm -rf`.** Use `find` with `-print` to show what would be deleted, let user approve.
5. **User copies manually, doesn't trust auto-move scripts.** Offer clear instructions with copy commands and verification steps.
6. **Always verify post-user-cleanup state.** When the user says they moved/deleted things, re-scan before proceeding — don't assume from the original audit. The domain may have changed significantly between audit and execution.
7. **Staged git deletions** (`git status --short` shows ` D filename`) are already gone from disk but still in the index. These need a commit to clean up, rather than leaving dangling state.
8. **Verify files landed in PARA after user reports moves.** Don't trust "I moved X" without checking the destination directory exists and has content.
9. **Content may live on disk but never be committed to git.** Agent-generated directories like `.agent-shell/`, `projects/project_management_agent/`, or other tool-output-only dirs exist only as filesystem state. If a parent dir is deleted from both disk and git, that content is unrecoverable — no commit history exists for it. AGENTS.md may reference such directories as if they were tracked; always verify with `git log --all` before assuming something was in the repo.
10. **Staged deletions (` D` in git status) are already gone from disk but still in the index.** They need a commit to clean up — not just ignored or forgotten. The user may have moved content to PARA and run a cleanup commit that removed those files from both locations; verify post-user state before acting on stale git status output.

## Output Format

Always produce findings structured as:
```
## <DOMAIN> Audit

### Structure
<ASCII tree of subdirs with size indicators>

### Activity Classification
| Subdir | Last Commit | Recent Commits (90d) | Staged/Uncommitted | Classification |

### Issues Found
- **N**: Issue name — evidence | why it matters

### Cleanup Proposal
1. Commit: <what>
2. Clean: <artifacts to remove>
3. Consolidate: <merge candidates>
4. Archive: <inactive repos>

### PARA Migration Mapping
| Current Location | PARA Destination | Action |
```

## Verification After User Actions

After any reported migration step, always run:
```bash
# Confirm source is clean
git status --short
# Confirm destination has content
ls -la ~/para/<target>/
# Verify no files were lost in transit
find <source> -type f | wc -l   # vs original count
```
