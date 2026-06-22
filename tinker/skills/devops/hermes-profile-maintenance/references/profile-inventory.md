# Profile Inventory

Authoritative roster of tracked Hermes profiles in
`~/para/1_projects/hermes-profiles/`. All six profiles run the same
model (deepseek-v4-flash via API) with identical `config.yaml` (v29).
Differentiation comes from SOUL.md (persona), memories/USER.md (user
profile), and curated skill selection.

**Bloat warning (2026-06-17)**: All profiles (except luhmann) were
carrying 74-85 skills — the same 70+ shared template. Profiles become
clones if skills aren't curated against the SOUL.md persona. A pruning
pass was done and is documented per profile below. See the SKILL.md
section "Profile differentiation: the skill audit workflow" for the
methodology.

## Profiles

### coder — primary daily driver

- **Purpose**: Software development, refactoring, debugging, code review
- **Model**: deepseek-v4-flash via custom:deepseek-v4-flash
- **Skills**: ~57 curated coding skills — plan, TDD, systematic-debugging,
  code-review, git-workflow, modular-etl-refactor, inference-cost-comparison,
  codebase-audit, profile-authoring, coding-agent-architecture
- **Persona**: Precise, concise, direct. Plan-first workflow. No scope
  creep. Commit discipline via conventional-commits format.
- **Bloat (before pruning)**: 85 skills. Pruned ~28 irrelevant: apple/*,
  media/*, creative/non-diagram, most research/* (kept llm-wiki),
  red-teaming, smart-home, yuanbao, dogfood.

### researcher — deep research

- **Purpose**: Product comparison, literature review, information synthesis
- **Model**: deepseek-v4-flash
- **Skills**: research/arxiv, blogwatcher, llm-wiki, polymarket,
  research-paper-writing, note-taking/obsidian, creative/humanizer,
  creative/architecture-diagram, email/himalaya, github/*, hermes-agent,
  codex, llama-cpp, vllm, productivity/notion, airtable, google-workspace
- **Persona**: Clarification-first. Structured reports with citation rules.
  Saves to `~/para/3_resources/research/` by default.
- **Built-in skills** (not git-tracked, but referenced in SOUL.md):
  `iterative-research`, `deep-research` — loaded from Hermes plugin bundle.
- **Bloat (before pruning)**: 78 skills. Pruned ~44: apple/*, media/*,
  creative/* except humanizer+arch-diagram, most mlops/*, most
  software-dev/* (kept plan), most productivity/* (kept notion, airtable,
  google-workspace), red-teaming, smart-home, social-media, yuanbao.

### tinker — experimental / system admin

- **Purpose**: Emacs config, dotfiles, Debian dev setup, system admin
- **Model**: deepseek-v4-flash
- **Skills**: emacs-config, emacs-configuration, kanban-workflow,
  kanban-management, matrix-setup, csv-data-pipeline, data-science-pipeline,
  sqlite-visualization, pkb-organization, master-strategy,
  software-dev-methodology, github-workflow, grill-me
- **Persona**: Environment-aware — knows Emacs config.org tangling,
  dotfiles symlink conventions, Debian setup scripts. Careful with
  destructive commands.
- **Bloat (before pruning)**: 84 skills. Pruned ~27: apple/*, media/*,
  creative/non-diagram, most mlops/* (kept llama-cpp), most research/*
  (kept llm-wiki), red-teaming, smart-home, yuanbao, dogfood,
  social-media.

### luhmann — learning / zettelkasten

- **Purpose**: Note-taking, concept extraction, knowledge synthesis
- **Model**: deepseek-v4-flash
- **Persona**: Patient, precise, Socratic. Named after Niklas Luhmann.
  Guides fleet→literature→permanent note processing. Periodically audits
  vaults for orphans and broken links.
- **Skills**: zettelkasten-workflow, commit-and-push-notes,
  note-taking/obsidian, note-taking/org-roam-index (4 total)
- **Bloat**: None — already clean. 4 skills, all aligned.

### ackman — personal finance

- **Purpose**: Bank statement import, account reconciliation, spending
  analysis, golden source database maintenance
- **Model**: deepseek-v4-flash
- **Persona**: Direct, data-driven, no-nonsense (Bill Ackman-inspired).
  OFX/QBO over CSV when available. Dedup via (date, amount,
  description_lower). Sign convention: negative = spend.
  Backward-wind balance computation.
- **Skills**: finance/personal-finance-data, csv-data-pipeline,
  data-science-pipeline, sqlite-visualization, jupyter-live-kernel,
  ocr-and-documents, nano-pdf, google-workspace, maps, notion, airtable,
  email/himalaya, github-auth, github-pr-workflow
- **Bloat (before pruning)**: 74 skills. Pruned ~44: apple/*, media/*,
  all creative/*, most mlops/*, most software-dev/* (kept plan), most
  research/* (kept llm-wiki), red-teaming, smart-home, kanban, dogfood,
  social-media, note-taking/obsidian.

### hobbies — DIY / self-hosted

- **Purpose**: Woodworking, home improvement, self-hosted services
- **Model**: deepseek-v4-flash
- **Persona**: Metric units only. 18mm plywood, 12V LED. Knows UK
  suppliers (Banggood, Screwfix, Amazon UK, Solmer).
- **Skills**: plan, systematic-debugging, spike, excalidraw, sketch,
  email/himalaya, smart-home/openhue, research/llm-wiki, blogwatcher,
  osmo-hardwax-oil (unique)
- **Bloat (before pruning)**: 75 skills. Pruned ~44: apple/*, media/*,
  most creative/* (kept excalidraw, sketch), most mlops/*, most
  research/* (kept llm-wiki, blogwatcher), most software-dev/* (kept
  plan, spike, debugging), most productivity/* (kept google-workspace,
  teams-meeting-pipeline, ppt), red-teaming, social-media, yuanbao,
  dogfood, note-taking/obsidian.
- **Thinness note**: This is the thinnest profile — `osmo-hardwax-oil`
  is the only truly unique skill. Evaluate whether the DIY domain
  justifies a whole profile vs being handled by `tinker` or `coder`.

## Structural invariants

1. All config.yaml files are byte-identical (v29, same model/provider)
2. .gitignore excludes: state.db*, sessions/, logs/, cache/, cron/,
   lsp/, plans/, .usage.json, .bundled_manifest, .curator_state,
   .env, auth.json, audio_cache/, image_cache/, sandboxes/
3. External skill dirs shared across profiles:
   - ~/.agents/skills
   - ~/para/2_areas/agents/skills
4. Built-in Hermes skills (iterative-research, deep-research, etc.)
   are NOT in git — they load from the Hermes plugin bundle at runtime
5. Per-profile identity lives in SOUL.md + memories/USER.md + skill
   curation — NOT in config.yaml differences
6. The `coder` profile has the most comprehensive skill set; other
   profiles are subsets or thematic specialisations

## When to create a new profile vs reuse an existing one

- **New domain with unique model/provider**: New profile needed
- **New domain, same model**: Assess if it fits an existing profile's
  persona (coding → coder, research → researcher, notes → luhmann,
  finance → ackman, admin → tinker). Only create a new profile if the
  persona would be jarringly mismatched.
- **Sandbox/experimentation**: Use `tinker` profile (it's the
  designated playground).
- **Before creating**: Check whether the built-in Hermes skills already
  cover the need. Many skills (iterative-research, deep-research,
  etc.) are always available regardless of profile.
