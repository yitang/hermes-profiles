# Reference: 7-Domain Matrix Workspace

A real-world example of a multi-project workspace organized into 7 domains (called "matrices"), each with its own AGENTS.md documentation.

## Structure Overview

```
~/matrix/
├── ds/          # Data Science
├── finance/     # Finance
├── health/      # Health
├── hobbies/     # Hobbies (DIY, selfhosted services, computers)
├── learning/    # Learning (books, meta-learning, blog)
├── reflect/     # Reflect (diaries, personal finance, reviews)
└── tools/       # Tools (dotfiles, Emacs, dev scripts, meta-tools)
```

## Per-Domain Detail

### 1. ds/ — Data Science (9 projects)
- `meta-ds/` — Career management: CV (LaTeX), interview prep, journal
- `2022-May-amex-default-prediction/` — Kaggle: LGB tuning
- `dlsys/` — Deep learning systems coursework
- `jigsaw-community-rules-2025/` — Kaggle: toxic comment classification
- `llm_diy_cost/` — LLM cost estimation research
- `mcts_2024/` — Monte Carlo Tree Search with Snakemake
- `strctrual_break/` — Structural break analysis
- `train_llm/` — LLM training/fine-tuning (TRL, PEFT, W&B)
- `yi_kaggle_lib/` — Reusable Kaggle library

**Conventions:** Python primary, `src/`+`tests/` structure, per-project Git, Snakemake workflows in `workflow/`.

### 2. finance/ — Finance (3 projects)
- `meta-finance/` — Study notes + reference PDFs (Grinold & Kahn, Jegadeesh & Titman)
- `Advanced-Portfolio-Management/` — Course notes
- `reimaging-price-trend/` — Price trend analysis

**Conventions:** Org-mode for notes, LaTeX reports, per-project Git.

### 3. health/ — Health (3 projects)
- `exercise_every_day/` — Daily exercise tracking
- `health/` — Health notes
- `health_data/` — Health metrics data

**Conventions:** `data/`+`scripts/` structure, per-project Git.

### 4. hobbies/ — Hobbies (3 nested repos)
**Topology note:** `~/matrix/hobbies/` is itself non-git but contains 3 independent sub-repos:

- `hobbies/.git` — Last commit 2026-06-01. Active DIY/home improvement projects with PARA management at `projects/project_management_agent/`. Org-mode primary. Has `.gitignore` (excludes org-download pngs, .aider/, .agent-shell/).
- `computers/.git` — Last commit 2026-04-23. Computing hobbies, notes, org-roam. No per-repo .gitignore.
- `selfhosted-services/.git` — Last commit 2026-02-11. Docker services (HASS, Calibre, Paperless, Ollama, Media Server). No per-repo .gitignore.

**Conventions:** Org-mode for notes in all sub-repos. DIY uses metric units, 12V DC LED systems, 18mm plywood, UK suppliers (Screwfix/Amazon/Banggood). PARA + Kanban + GTD framework in hobbies sub-repo. Each sub-repo manages its own git hygiene independently — stale commits do not indicate abandoned work (org files are often edited without structural commits).

See `references/matrix-hobbies-domain-audit.md` for detailed audit findings.

### 5. learning/ — Learning (3 areas)
- `books/` — 15+ book summaries (Atomic Habits, Deep Work, Psychology of Money, etc.)
- `meta-learning/` — Learning process management (vocabulary, transcripts, RSS)
- `mywebsite/` — Personal blog at yitang.uk (Jekyll + Org-mode export, 4 sub-agents)

**Conventions:** Org-mode book notes, British English for blog.

### 6. reflect/ — Reflect (3 areas)
- `diaries/` — Personal diary entries
- `personal_finance/` — Financial tracking
- `reviews/` — Weekly reviews + Org-mode clocktables

**Conventions:** Primarily read/query, sensitive content, per-project Git.

### 7. tools/ — Tools (6 areas)
Identified simplification issues in this domain:
- `emacs/` vs `.emacs.d/` naming collision (study content vs config)
- `dotfiles/` grab-bag with stale/redundant files
- `python/` stale (2 projects from 2022)
- `meta-tools/notes/` (141 files) — correct consolidation point

## AGENTS.md Format Used

Each AGENTS.md follows this structure:
1. **Domain Overview** — one-paragraph summary
2. **Project Index** — table of subdirectories with type + description
3. **Conventions** — domain-specific rules (tooling, git, structure, suppliers)
4. **Agent Guidelines** — actionable rules for future agents

## Key Patterns Observed

1. **Meta-directories** (`meta-ds`, `meta-finance`, `meta-learning`, `meta-tools`): Each domain's "control panel" — career, study management, or knowledge base for that domain.
2. **Per-project Git**: Almost every sub-project has its own `.git/` — not a monorepo.
3. **Org-mode dominance**: Plans, notes, journals, and study material are primarily Org-mode files.
4. **AGENTS.md as the single markdown exception**: Only AGENTS.md files are markdown; everything else is `.org`.
5. **Flat structure**: Domains are peers under `~/matrix/` — no deep nesting of domain directories.
