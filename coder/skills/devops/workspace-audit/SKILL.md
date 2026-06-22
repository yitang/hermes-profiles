---
name: workspace-audit
description: "Explore, document, and analyze multi-project workspaces — systematically audit directory structures, write AGENTS.md documentation for each domain, and identify simplification/consolidation opportunities."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [workspace, audit, documentation, directory-structure, exploration, consolidation]
    related_skills: [project-management, codebase-inspection]
---

# Workspace Audit — Explore, Document & Simplify

A systematic methodology for exploring unfamiliar multi-project workspaces, writing structured AGENTS.md documentation for each domain, and identifying structural improvements.

## When to Use

- User introduces you to a multi-project/multi-repository workspace and asks you to understand it
- User asks you to "document" or "write AGENTS.md" for workspace domains
- User asks "is there anything that can be done to simplify this?"
- User says "explore and tell me what's here"
- User mentions a "matrix" of directories/domains
- Any time you're dropped into a new project workspace and need to orient yourself

## Core Methodology

### Phase 1: Rapid Exploration

Start broad, then go deep. Avoid reading every file — focus on structure and key signal files.

**Step 1 — Surface inventory:**
```bash
# Top-level contents
ls -la <workspace-root>

# All immediate children (depth 1 only)
find <workspace-root> -maxdepth 1 -type d | sort

# Check for any existing documentation patterns
find <workspace-root> -name 'AGENTS.md' -o -name 'README.*' -o -name 'main.org' | head -30
```

**Step 2 — Read existing documentation:**
- If AGENTS.md files exist, read them first — they're the canonical orientation docs
- If `.dir-locals.el` exists in a directory, check it for Emacs project settings (org-roam paths, projectile roots) — they reveal how the user organised the space
- Check `setup.org` files for environment context

**Step 3 — Structure mapping (depth 2):**
```bash
# Full depth-2 directory tree, skipping .git internals
for d in <workspace-root>/*/; do
  echo "=== $(basename "$d") ==="
  find "$d" -maxdepth 2 -type d -not -path '*/.git/*' | sort
  echo
done
```

**Step 4 — Identify conventions per domain:**
- Git status per sub-project (`ls -d */.git` to find repos)
- File types present (.org, .py, .md, .sh, .yaml, .tex, .csv)
- Common directory patterns (`src/`, `tests/`, `notebooks/`, `data/`, `scripts/`, `notes/`, `assets/`)
- Look for `meta-*` directories — these are often the "meta-layer" managing the domain
- Look for PARA-style numbered directories (`1_projects/`, `2_areas/`, etc.)

### Phase 2: Write AGENTS.md Documentation

Each workspace domain gets a structured AGENTS.md at its root. Use this template:

```markdown
# AGENTS.md — <Domain Name>

## Domain Overview

<One paragraph: what this domain is, what kind of work lives here.>

## Project Index

| Directory | Type | Description |
|-----------|------|-------------|
| `<dir>/` | `<Project/Research/Config/Meta/Study/etc>` | <Brief description> |

## Conventions

- **Tool/language conventions** (e.g. "Python is primary", "Org-mode for notes")
- **Git conventions** (per-project repos or mono-repo?)
- **Structure conventions** (src/tests pattern, notes/assets pattern)
- **Domain-specific policies** (suppliers, measurement units, design choices)

## Agent Guidelines

- <Rule for agent behavior in this domain>
- <What to reference for current status>
- <What NOT to touch or edit>
```

**Key principles:**
1. **Project Index** — Every subdirectory gets one row. Shows what exists at a glance.
2. **Conventions** — Surface the implicit rules. These save agents from repeating mistakes.
3. **Agent Guidelines** — Actionable rules for future agents working here. Prefer positive guidance ("read X for status") over negative ("don't Y").
4. **Link to sub-AGENTS.md** — If sub-projects have their own AGENTS.md, mention them.

### Phase 2b: Activity-Based Classification (NEW)

Before presenting findings or proposing moves, classify every repo by actual activity — not just directory names. This prevents mis-categorizing dead repos as active and vice versa.

**Step: Run commit + mtime analysis on all git repos:**
```bash
for domain in workspace_root/*/; do
  for repo in "$domain"*/; do
    [ -d "$repo/.git" ] || continue
    
    # Last commit date
    last_commit=$(cd "$repo" && git log -1 --format='%ai' 2>/dev/null)
    
    # Most recent file mtime (excluding .git)
    latest_mtime=$(find "$repo" -not -path '*/.git/*' -type f -printf '%T@ %p\n' | sort -rn | head -1)
    
    # Commits in last 30 days
    commits_30d=$(cd "$repo" && git log --since='30 days ago' --oneline 2>/dev/null | wc -l)
    
    echo "$(basename "$repo") | commit=$last_commit | mtime=$(echo "$latest_mtime" | cut -d' ' -f1-) | commits_30d=$commits_30d"
  done
done
```

**Classification table:**

| Category | Signal | Action in audit |
|----------|--------|-----------------|
| **ACTIVE** | Commits ≤7 days old, or commits_30d ≥5 | Keep as live repo; this is what the user actually uses |
| **MONTHLY/QUARTERLY** | Last commit 7–90 days ago, low but non-zero frequency | Mark as semi-active; may warrant consolidation if only used for reference |
| **ARCHIVE** | Last commit >90 days ago, commits_30d = 0 | Target for archival — not being worked on |
| **SUSPECT (uncommitted edits)** | Last commit >60 days ago BUT file mtime <30 days ago | Files were modified without committing. User may be actively working here but git is stale. Do NOT archive this repo based on commit date alone. Investigate: are there `.org` notes being written? Is this a diary, a local draft, or abandoned work? |

**Pitfall for this signal:** A repo with stale commits but active mtime is NOT necessarily "abandoned" — the user may be working locally and committing in batches. Always verify by checking file contents (e.g., recent `.org` notes, diary entries) before classifying as archive.

### Phase 3: Identify Simplification Opportunities

When asked to review a workspace for simplification, apply this analysis framework:

**Signal 1 — Naming collisions:**
- Two directories with similar names serving different purposes? (e.g., `.emacs.d/` = config vs `emacs/` = study notes)
- The naming collision causes ambiguity — rename or relocate one.

**Signal 2 — Grab-bag directories:**
- A directory containing config files, scripts, notes, AND empty directories?
- Classify each file into: **core value** vs **stale** vs **misplaced** vs **empty**

| Category | Characteristic | Action |
|----------|---------------|--------|
| **Core value** | Essential, actively used | Keep in place |
| **Stale** | No activity >1 year, abandoned projects | Archive or delete |
| **Misplaced** | Belongs in a different domain | Move to correct domain |
| **Redundant** | Duplicates content elsewhere (e.g., config duplicated in two repos) | Delete copy, keep canonical source |
| **Empty** | Empty directories, near-empty files | Remove |

**Signal 3 — Cross-domain misplacement:**
- Study/learning content stored in a tools directory? → Belongs under `learning/`
- Data science code stored in a tools directory? → Belongs under `ds/` or `projects/`
- Step back: does every file's *purpose* match the *domain name*?

**Signal 4 — Overlapping concerns:**
- Two directories both holding notes about the same topic?
- Scripts scattered across multiple directories when one would do?
- Multiple "notes/" directories with no clear boundary between them?

**Signal 5 — Redundant documentation files:**
- Multiple `README.org`, `main.org`, `AGENTS.md` at the same level competing for attention?
- Empty or near-empty documentation files that were never filled in?

### Presentation format for simplification analysis

When presenting findings, use this structure:

```
## Current Structure
<ASCII tree of the domain>

## Observations

### N. <Issue name> — concise
<Evidence> | <Why it's a problem> | <Recommended action>

...

## Simplification Proposal
<Proposed new structure as ASCII tree>
<Key moves: what stays, what moves, what's removed>
```

This lets the user see the problem and the solution side by side.

## Pitfalls

1. **Don't read every file** — focus on structure indicators (ls, find) and signal files (AGENTS.md, .dir-locals.el, README). Reading individual source files is usually wasted effort in the exploration phase.
2. **Don't move things without confirming** — always present the analysis first, let the user approve before executing structural changes.
3. **Don't infer Git topology from session memory** — always run `ls -d */.git` to find repos. Session memory may describe a past state.
4. **Don't assume all .org files are notes** — some may be configuration or tangled code. Check if there's a `#+PROPERTY: header-args :tangle` line to distinguish.
5. **Don't skip empty directories** — they're a signal. An empty `src/` or empty `notes/` directory suggests either an unfinished intention or a cleanup opportunity.
6. **Don't treat meta-directories as clutter** — `meta-*` dirs (meta-ds, meta-tools, meta-learning) are the user's PARA-style meta-layer for managing that domain's direction. They are intentionally separate.

7. **Never run `rm -rf` on the terminal session's working directory.** If an operation would delete the current cwd, always `cd /tmp` (or another safe directory) first. After a CWD is deleted, all subsequent terminal commands fail with `FileNotFoundError: [Errno 2] No such file or directory` because the service can no longer resolve the session's working directory — there is no in-session recovery.

### Phase 4: Nested Repo Detection (NEW — from hobbies/ audit)

Some domain directories are **themselves non-git parents** that contain independent git repos. Example: `~/matrix/hobbies/` has no `.git`, but contains three sub-repos (`hobbies/.git`, `computers/.git`, `selfhosted-services/.git`).

**Detection:**
```bash
# Run from workspace-root (may not be a git repo itself)
find <root> -name '.git' -type d | sort
```

If more than one `.git` is found, **each sub-repo must be audited independently**:
- Last commit date per sub-repo
- Uncommitted changes per sub-repo (`cd $repo && git status --short`)
- Each may have different conventions (e.g., `hobbies/.gitignore` exists but `computers/` does not)

**Pitfall:** When running audit commands, always `cd` into the correct sub-repo before using `git`. Running `git log` from a non-git parent silently fails. The activity classification in Phase 2b must be run per-sub-repo, not aggregated.

### Phase 4b: Pre-Audit Clean State Check

**Before proposing any structural changes, verify each sub-repo's clean-state status.** A dirty working tree blocks commits and makes restructuring ambiguous (was file X deleted or moved?).

```bash
cd <repo-dir> && git status --short | awk '{print $1}' | sort | uniq -c | sort -rn
```

This outputs counts by change type: `D` (deleted), `M` (modified), `??` (untracked). **If deletions dominate** (e.g., 172 deletes, 0 modifies), the user likely bulk-moved files and left git dirty. Flag this prominently — structural changes cannot be cleanly committed until the deletion state is resolved.

### Phase 4c: Org-Download Bloat Detection

Org-mode's `org-download` extension tracks screenshots in `assets/org-download/`. The user's `.gitignore` contains a negated pattern (`!assets/org-download/*.png`) that **explicitly un-excludes** these images from git — meaning hundreds of megabytes of screenshots are tracked in repo history.

**Detection:**
```bash
find <root> -path '*/assets/org-download' -type d | while read d; do echo "$d: $(du -sh "$d" | cut -f1)"; done
# Also check .gitignore for negated org-download patterns
grep -rn '!.*org-download' <root>/ --include='.gitignore' 2>/dev/null
```

**Threshold:** >50 MB in any single org-download directory warrants flagging as a git maintenance concern. Recommended action: move to `~/data/` with symlinks, or convert to external storage. See `references/matrix-hobbies-domain-audit.md` for a real example (211MB tracked in `hobbies/assets/org-download/`).

### Phase 4d: LaTeX Build Artifact Detection

Org-mode exports `.tex` files via LaTeX export. Build artifacts (`.aux`, `.log`, `.toc`, `.out`) accumulate in the same directory as the source `.org` file but should not be tracked by git.

**Detection:**
```bash
find <root> -name '*.aux' -o -name '*.log' -o -name '*.toc' -o -name '*.out' 2>/dev/null | grep -v '.git'
```

Flag any that are newer than their parent `.org` file (indicating recent export but no cleanup). Recommend running `make clean` equivalent or adding to per-repo `.gitignore`.

### Phase 4e: Stale-When-Active Detection (Org-mode convention)

In org-mode-heavy workspaces, users often edit `.org` notes continuously but only commit when the *structure* changes (new files, moves, renames). This creates a disconnect: **a repo with stale commits may have actively edited `.org` files with actionable TODOs.**

**Detection:**
```bash
# For repos classified as ARCHIVE by Phase 2b, check for recent org edits
cd <repo-dir> && git diff --name-only HEAD -- '*.org' | head -5
```

If `main.org` or other org files are modified but uncommitted, classify the repo as **"QUIESCENT — notes still being maintained"** rather than ARCHIVE. Never archive a repo whose org TODOs reference active projects without verifying commit vs edit state first.
