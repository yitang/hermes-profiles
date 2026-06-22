# Reference: Hobbies Domain Audit (2026-06-10)

## Repo Topology

Root `~/matrix/hobbies/` is **not a git repo** but contains 3 independent sub-repos:

| Sub-repo | Last commit | Status | Active TODOs in main.org? |
|----------|-------------|--------|--------------------------|
| `hobbies/.git` | 2026-06-01 | ACTIVE | Yes — visa, open plan materials |
| `computers/.git` | 2026-04-23 | QUIESCENT | Yes — 10Gb ethernet, Local LLM Emacs |
| `selfhosted-services/.git` | 2026-02-11 | QUIESCENT (119d stale) | Yes — disk full, ebook service, scanner |

Each sub-repo has its own `.gitignore` conventions: only `hobbies/` has one. The other two rely on default git ignore (nothing).

## Dirty State Snapshot

### `hobbies/` — 172 deletions uncommitted
Entire `notes/` org-roam directory deleted (files from 2023–2024: power meters, Dell Optiplex, garden tools, lawn care, PC builds). These notes were likely migrated to PARA `3_resources/` but not committed. Working tree: **172 D + 3 ??**

### `computers/` — 1 modified file
`debian.org` uncommitted (no deletions, no untracked). Minor edit.

### `selfhosted-services/` — 1 modified file
`main.org` uncommitted (still has TODOs: disk full, ebook service). Recent edits to main.org not committed.

## Org-Download Bloat

| Directory | Size | Git status |
|-----------|------|------------|
| `hobbies/assets/org-download/` | **211 MB** | TRACKED (`!assets/org-download/*.png` un-excludes in .gitignore) |
| `computers/assets/org-download/` | 96 KB | Tracked (no negated gitignore; defaults apply) |

The 211MB in `hobbies/` is the largest non-git artifact in this domain. These are screenshots captured by org-download during Emacs editing sessions. The `.gitignore` explicitly un-excludes them, so they accumulate in git history.

## LaTeX Artifacts

`garden_studio.org` exports to `garden_studio.tex`. Build artifacts sit in same directory:
- `garden_studio.aux` — 32 bytes (Jul 2025)
- `garden_studio.log` — 3.8 KB (Jul 2025)
- `garden_studio.tex` — 4.6 KB (Mar 2026, actively maintained)

The `.aux` and `.log` are stale build outputs that should not be committed but aren't excluded by any .gitignore.

## Notable Files Outside Conventions

| File | Location | Oddity |
|------|----------|--------|
| `hobbies/main.py` | hobbies/ root | Frame calculator for wall cabinets — Python script mixed with org files |
| `hobbies/open_plan.ledger` | hobbies/ root | Ledger bookkeeping file (not .org) |
| `computers/notes/org-roam.db` | computers/notes/ | Org-roam database; only 1 actual roam note file |
| `selfhosted-services/ollama/*.el` | selfhosted-services/ollama/ | Emacs Lisp packages (chatgpt-shell.el, ollama.el) — likely upstream clones, not config files |
| `.projectile` | 2 locations | In `project_management_agent/` and `wall_cabinets/` but parent domain lacks .dir-locals.el linkage for these |

## AGENTS.md Status

Root-level `~/matrix/hobbies/AGENTS.md` (66 lines) covers the cross-domain overview. No per-repo AGENTS.md exists — only `hobbies/projects/wall_cabinets/AGENTS.md`. The parent repo docs should be updated to reflect nested-repo topology and commit hygiene expectations.
