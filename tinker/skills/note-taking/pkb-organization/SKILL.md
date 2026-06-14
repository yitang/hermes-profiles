---
name: pkb-organization
description: Restructure personal knowledge bases (PKBs) — org-mode, Obsidian vaults, markdown note collections — from flat/unstructured dumps into navigable systems. Covers the archive-to-practice transformation and "find-by-nature" structuring strategies. Use when user has a notes repository with timestamped flat files, wants to reorganize their knowledge base, or says they need to "clean up my notes."
---

## Purpose

Users often build **knowledge archives** (dumping unstructured notes into flat directories) but never engage in **knowledge practice** (studying/reviewing them). This skill addresses the structural root cause: flat timestamped files are impossible to browse meaningfully.

## Restructuring Strategies

### 1. Category-First
Group by domain/tool: `emacs-notes/`, `bash-notes/`, `docker-notes/`, `devops-notes/`. Best when you think of tools as your mental model. Sub-topics under each tool get subdirectories.

### 2. Hierarchy Tree
Top-level → tool/topic → specific subject. Example:
```
gpg/
├── agent.org
├── export-keys.org
└── configuration.org
bash/
├── source-builtin.org
└── variable-scope.org
```
Best when each note is about a narrow concept under a broader tool.

### 3. Index-Driven
Keep flat files but maintain a central `main.org` or `README.org` that acts as the navigation index. All exploration goes through the index; notes are found via org-roam-like backlinks, not filesystem browsing. Best when you already use Org Roam and want minimal structure changes.

### 4. Mixed (recommended for most cases)
- **Keep** small tool-specific notes under the tool's folder (e.g., `gpg/`, `bash/`)
- **Archive** dated exercises into a separate `exercises/archive/` directory organized by date, or consolidate into larger theme-based org files
- **Preserve everything** — stale, outdated, or no-longer-used notes stay where they are. Signal extraction from noise is the goal, not curation-by-deletion. Index cards and recency filters surface what's relevant now without destroying history.

## Decision Procedure

1. **Inventory first** — run `find . -type f | wc -l`, check file sizes. Know what you're dealing with before moving anything. See `references/inventory-checklist.md` for the audit steps.
2. **Audit each note** — is it still relevant? Does the user want to study it, or just keep it as reference? Preserve everything unless explicitly asked to delete; surface relevance via filtering mechanisms (index cards, recency, tags) instead of deletion.
3. **Choose a strategy** — ask the user which mental model fits (the 5 options above), don't guess. Note: if the user explicitly wants preservation-only and zero-maintenance discovery, recommend Strategy 5 (Auto-generated index cards) over any approach that suggests removing notes.
4. **Move in batches** — move related notes together to their new location. Never move files in isolation; always move clusters that belong together.
5. **Verify navigation** — after restructuring, simulate browsing: can you find `gpg agent config` without knowing the exact filename?

### 5. Auto-generated Index Cards (recommended for org-roam users with flat notes)
Keep all flat timestamped files untouched. Generate index cards that cluster notes by topic keyword extracted from filenames + tags, ordered by recency. Two implementations:

**(A) Inline dynamic elisp** — `index-git.org` contains a `#+begin_src elish{}` block that queries org-roam for recently-modified notes matching a keyword group. Updates every time the file is opened in Emacs. Always fresh, zero maintenance. Best if Emacs is your primary lookup method.

**(B) Generated static files** — A script runs and writes real `id:` links to recent notes. Grep-able from terminal, version-controllable. Requires running generator periodically (cron, emacs hook, or manual).

**Grouping mechanism**: Hybrid approach — filename keyword extraction (e.g., `bash_source` → bash cluster) as primary signal, tags inside note body (`#+TAGS: :git:`) as override/fallback for accuracy. Works when filenames are ambiguous or a note spans multiple topics.

**Recency signals**: Use `:CREATED:` property from org PROPERTIES block when filesystem mtime is unreliable (e.g., after git clone, all files share same mtime). Check for `:LAST-CAPTURED:` first — it's the most accurate if present, but flat timestamped notes rarely have it. If neither org-roam DB nor database functions are available from src block context, scan files directly to extract `:CREATED:` and `:ID:` properties.

**Filename keyword extraction**: Strip leading date prefix (`YYYYMMDD` or `YYYYMMDDHHMMSS`), take the first underscore-separated segment, lowercase. Examples: `20250820100958-bash_source` → `bash`; `20260505112647-hermes_agent` → `hermes`. Documented in full detail at `references/filename-keyword-extraction.md`.

**.dir-locals.el setup**: Org-roam indexes notes under `org-roam-directory`. For per-repo setup, create `.dir-locals.el` with:
```elisp
((nil . ((eval . (progn
                  (setq-local note-dir "~/matrix/tools/meta-tools/notes/")
                  (setq-local org-roam-directory note-dir)
                  (setq-local org-roam-db-location 
                              (file-name-concat note-dir "org-roam.db")))))))
```
Index files go **inside** the org-roam directory (same as flat notes). Org-roam auto-indexes them, backlinks work, graph view includes them.

See `references/filename-keyword-extraction.md` for the full filename keyword extraction algorithm with examples and edge cases.

## Multi-Vault Org-Roam Auditing

When auditing a user's org-roam ecosystem that uses per-project directory-local vaults (like the matrix-setup convention):

### Step 1 — Find All notes/ Directories
```bash
find ~/matrix -name "notes" -type d | sort
find ~/para -name "notes" -type d | sort
```
Also check for flat roam directories outside the notes/ convention (e.g., `vocabulary/` as a standalone vault).

### Step 2 — Per-Vault Inventory
For each notes/ directory, collect:
```bash
# Count org files
ls <vault>/*.org 2>/dev/null | wc -l

# Check for org-roam.db
test -f <vault>/org-roam.db && echo "DB" || echo "no-db"

# Check .dir-locals.el at PARENT levels (walk up)
cat <parent-of-notes>/.dir-locals.el 2>/dev/null
# Also check grandparent — locate-dominating-file can live several levels up
```

### Step 3 — Map the Dir-Locals Wiring
The critical relationships are:
- Which `.dir-locals.el` sets `org-roam-directory` for this vault?
- Does it set BOTH `org-roam-directory` and `org-roam-db-location`?
- Is `project-dir` computed via `locate-dominating-file` or hardcoded?

The user's convention: `~/matrix/{domain}/.dir-locals.el` sets:
```elisp
(setq-local project-dir (file-name-concat
  (locate-dominating-file default-directory ".dir-locals.el") "meta-{domain}"))
(setq-local note-dir (file-name-concat project-dir "notes/"))
(setq-local org-roam-directory note-dir)
(setq-local org-roam-db-location (file-name-concat note-dir "org-roam.db"))
```

### Step 4 — File Naming Pattern Analysis
Two distinct patterns signal different capture-template eras:
| Pattern | Example | Capture Source |
|---------|---------|---------------|
| YYYYMMDD_HHMMSS-slug | 20221217_174739-nonlinear.org | Current template with `_` |
| YYYYMMDDHHMMSS-slug  | 20221103114407-softmax.org  | Older/org-roam v1 |

Count ratio: `ls *_.org | wc -l` vs `ls *.org | grep -v "_" | wc -l`

### Step 5 — Check for Custom Property Tags
Look for non-standard properties like `:matrix:`:
```bash
grep -l ":matrix:" <vault>/*.org | wc -l
```
These are domain classifiers embedded during creation. Compare count vs total files.

### Step 6 — DB Freshness Check
```bash
ls -la <vault>/org-roam.db
```
DB updated today = autosync working. Old DB with notes but no dir-locals = stale.

### Step 7 — Summary Format
```
| Vault               | Files | DB   | Dir-Locals | Status          |
|---------------------+-------+------+------------+-----------------|
| meta-tools/notes    |   148 |  yes | parent ✓   | Working          |
| meta-ds/notes       |   128 |   no | parent ✓   | Needs DB rebuild |
| meta-health/notes   |     5 |   no | absent ✗   | Broken           |
```

See `references/inventory-checklist.md` for the full audit CLI commands.

## The Archive vs Practice Gap

Before restructuring, probe why notes weren't studied (see `references/knowledge-practice.md`). Restructuring alone won't help if the user still doesn't engage. Address both structure AND engagement habit simultaneously.

## Pitfalls

- **ALWAYS present design and get explicit go-ahead before writing any code.** The user has explicitly said "i want to talk about design and plan only" in the past. Never start implementing elisp, scripts, or file changes until the design is reviewed and confirmed. This applies to all PKB organization work — present the plan, describe what you'll create, and wait for approval.
- **Don't create deep hierarchies (>3 levels)** — it creates navigation friction worse than flat files.
- **Don't rename timestamps on sight** — they have context. Only restructure, don't rewrite unless asked.
- **Don't merge everything into one giant file** — breaks incremental reference and searchability.
- **Always get user buy-in on strategy before moving files** — different strategies suit different mental models.
- **When auditing org-roam vaults with directory-local config, check PARENT-level .dir-locals.el first.** The user's matrix convention is `~/matrix/{domain}/.dir-locals.el` (parent domain), not `~/matrix/{domain}/meta-{domain}/.dir-locals.el` (project root). `locate-dominating-file` walks UP from the current buffer, so dir-locals can live at any ancestor directory. Never assume they're in the immediate project root.
