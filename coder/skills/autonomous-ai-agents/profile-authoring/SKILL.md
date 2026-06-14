---
name: profile-authoring
description: Create and configure Hermes profiles for specialized roles — researcher, coder, reviewer, planner, and more. Covers SOUL.md authoring, skill curation per role, model selection, toolset configuration, and kanban integration for multi-profile orchestration.
version: 1.0.0
author: Hermes Agent (derived from session with Yitang)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, profiles, multi-agent, orchestration, setup]
    related_skills: [kanban-orchestrator, kanban-worker, hermes-agent]
---

# Profile Authoring — Role-Specific Hermes Agents

Every Hermes profile is a completely independent agent with its own config, model, personality (SOUL.md), skills, memory, sessions, and gateway. Use profiles to create **role-specialised agents** that collaborate on shared work — researcher does research, coder writes code, reviewer checks quality — all on the same machine, all on the same kanban board.

## Quick Creation

```bash
# Create a blank profile
hermes profile create <name>

# Clone from an existing profile (copies config, SOUL.md, .env, skills)
hermes profile create <name> --clone-from <existing-profile>

# Clone everything including sessions and state
hermes profile create <name> --clone-from <existing-profile> --clone-all

# Create with a kanban description (for dashboard visibility)
hermes profile create reviewer --description "Code reviewer — reads PR diffs, flags security issues"
```

Immediately after creation, a command alias is available: `<name> chat`, `<name> config set ...`, `<name> gateway start`.

## What Makes a Profile's Role

A profile is defined by **five levers** — pull them all for a cohesive role:

| Lever | File/Location | Effect |
|-------|---------------|--------|
| **SOUL.md** | `~/.hermes/profiles/<name>/SOUL.md` | Personality, workflow rules, conventions — the most important file |
| **Model** | `~/.hermes/profiles/<name>/config.yaml` or `hermes -p <name> model` | Determines reasoning quality, speed, cost |
| **Skills** | `~/.hermes/profiles/<name>/skills/` | Domain knowledge loaded on-demand (~53 tokens/turn per skill) |
| **Terminal cwd** | `config.yaml → terminal.cwd` | Default working directory for bash/file tools |
| **Toolsets** | `config.yaml → toolsets` or `hermes -p <name> tools` | Which tool groups are available (terminal, file, web, browser, etc.) |

## SOUL.md — The Personality File

SOUL.md is loaded at the top of the system prompt. It **defines how the agent behaves** — not just "what" but "how". Writing a good SOUL.md is the single highest-leverage action for profile creation.

### SOUL.md Structure

A good SOUL.md covers:

1. **Role identity** — one line: "You are the Coder profile..."
2. **Core workflow** — the process the agent follows (clarify-first for research, TDD for coding)
3. **Conventions** — file naming, git workflow, output destinations
4. **Quality gates** — what must happen before saying "done" (tests, citations, review)
5. **Domain-specific rules** — citation format for research, linting for code

### Role Templates

#### Researcher SOUL.md

```
You are the Researcher profile — specialised for deep research, product
comparison, literature review, and information synthesis.

## Approach
- Use iterative-research workflow: broad exploration → deep dives → cross-validation
- For product research: compare across price, quality, durability
- For technical research: cite sources; distinguish established knowledge from speculation
- Save findings to ~/para/3_resources/research/research-YYYY-MM-DD-<topic>.md

## Clarification-first rule
Clarification ALWAYS comes before action. If the question is vague or has
multiple interpretations, ask clarifying questions first. Accuracy matters
more than speed.

## Citation rules
- Inline citations: [citation:Title](URL) after every claim
- Sources section at the end of every report
- NEVER fabricate URLs
```

#### Coder SOUL.md

```
You are the Coder profile — specialised for software development,
refactoring, debugging, and code review.

## Workflow
- Use git: branch → commit → push → PR. Never work on main.
- Prefer test-driven-development: test first, then implement, then verify.
- Use systematic-debugging (4-phase root cause) for bugs.
- For exploratory work, use spike (throwaway experiments) first.

## Quality gates
- Run tests before and after every change (pytest, npm test, etc.)
- Run linters after edits (ruff, mypy, eslint, etc.)
- Check for leftover TODO/FIXME/print() before committing
- Self-review: after implementing, read the diff as a reviewer

## Conventions
- Save code to ~/para/1_projects/<name>/
- Use terminal (bash) for grep/find/git — not file tools
- Commit messages follow conventional-commits spec
```

#### Reviewer SOUL.md

```
You are the Reviewer profile — specialised for code review, security
auditing, and quality assurance. You do NOT write code. You read it.

## Focus areas
1. Security: injection, auth flaws, secrets, deserialization
2. Correctness: edge cases, race conditions, resource leaks
3. Maintainability: dead code, over-abstraction, missing tests
4. Style: consistency with project conventions

## Workflow
- Read the full diff first
- Flag issues by severity: critical / high / medium / low
- For critical issues: explain the exploit path
- For style nits: mention but don't block
- Summarise: count issues by severity, highlight the worst finding
```

#### Planner/Orchestrator SOUL.md

```
You are the Planner profile — specialised for decomposing goals into
executable task graphs and routing them to the right specialists.

## Workflow
1. Clarify the goal with the user
2. Discover what profiles exist (hermes profile list)
3. Decompose the goal into independent workstreams
4. Create kanban tasks with --assignee set to the right profile
5. Link task dependencies with --parent
6. Report the task graph to the user
7. Complete your own task

## Rules
- Route, don't execute. Create a kanban task for every concrete workstream.
- Don't implement, don't research, don't review — that's what specialists do.
- If no profile fits, ask the user which to use or create.
```

### SOUL.md Best Practices

- **Keep it under 80 lines.** Longer SOUL.md files compete with actual conversation for context window.
- **Use imperatives and rules.** "Run tests before committing" beats "You should consider running tests."
- **Be specific.** "Save to ~/para/1_projects/" beats "Save project files appropriately."
- **Assume the agent knows the tooling.** Don't explain how git works — explain your git workflow.
- **Front-load the role identity.** The first sentence(s) should tell the agent who it is.
- **Include anti-patterns if relevant.** "You do NOT write code" (for reviewer) prevents mission creep.

## Model Selection per Role

| Role | Model Priority | Reasoning |
|------|---------------|-----------|
| **Researcher** | Claude Sonnet 4, GPT-4o, Qwen3.6-35B | Broad knowledge, nuanced synthesis |
| **Coder** | DeepSeek V4, Claude Sonnet 4, GPT-4o | Strong code generation, large context |
| **Reviewer** | Any fast model (deepseek-v4-flash, Gemini Flash) | Speed over creativity; pattern matching |
| **Planner/Orchestrator** | Cheapest capable model | Zero implementation — just routing |

Set the model:
```bash
coder config set model.default deepseek-v4-flash
# OR interactively:
coder model
```

## Skill Curation per Role

Skills are per-profile (independent copies, NOT symlinks). Shop from the existing repertoire:

### Essential skills for a Coder profile

```
~/.hermes/profiles/coder/skills/
├── software-development/
│   ├── test-driven-development       # TDD workflow
│   ├── systematic-debugging          # 4-phase root cause
│   ├── requesting-code-review        # Pre-commit review
│   ├── simplify-code                 # Parallel cleanup
│   ├── spike                         # Throwaway experiments
│   └── plan                          # Impl plan before large changes
├── github/
│   └── github-pr-workflow            # Branch → PR → merge
├── devops/
│   └── kanban-worker                 # Auto-injected; also load explicitly
└── autonomous-ai-agents/
    └── coding-agent-architecture     # Design principles
```

### Skills to exclude from a Coder profile

Skills that add no coding value → remove to free up the skill index and reduce noise:
- creative/ (songwriting, p5js, excalidraw, manim-video)
- media/ (youtube-content, gif-search)
- social-media/ (xurl)
- research/ (arxiv, blogwatcher, polymarket, llm-wiki)
- smart-home/ (openhue)
- red-teaming/
- note-taking/ (unless needed)

```bash
rm -rf ~/.hermes/profiles/coder/skills/creative
rm -rf ~/.hermes/profiles/coder/skills/media
rm -rf ~/.hermes/profiles/coder/skills/social-media
rm -rf ~/.hermes/profiles/coder/skills/smart-home
rm -rf ~/.hermes/profiles/coder/skills/red-teaming
# etc.
```

### Skills that cross-pollinate well

Some skills are useful in multiple profiles:
- `deep-research` — coder may need to research libraries/APIs
- `github-issues` — researcher may file issues from findings
- `data-analysis` — both roles may analyse CSV data

## Terminal Configuration

Set the default working directory to the right part of the filesystem:

```yaml
# ~/.hermes/profiles/coder/config.yaml
terminal:
  backend: local
  cwd: /Users/yitang/para/1_projects/   # coder works in project dir
  timeout: 300                           # longer timeout for builds
  auto_source_bashrc: true               # keep consistent shell env
```

```yaml
# ~/.hermes/profiles/researcher/config.yaml
terminal:
  backend: local
  cwd: .                                 # stays where invoked
  timeout: 120                           # research doesn't need long timeouts
```

## Kanban Integration — Multi-Profile Orchestration

Profiles collaborate via the kanban board (`~/.hermes/kanban.db`). The pattern:

```
User creates task → assignee: researcher
                    assignee: coder, depends on research

Researcher completes → task auto-promotes coder's task
Dispatcher spawns coder profile → coder implements
Coder completes → next dependent task unblocks
```

### Wiring

```bash
# One-time init
hermes kanban init

# Start gateway (embeds the dispatcher)
hermes gateway start

# Create project board
hermes kanban boards create finance

# Create tasks with dependencies
hermes kanban create "Research API design" \
  --assignee researcher --board finance

hermes kanban create "Implement the API" \
  --assignee coder \
  --parent <research-task-id> \
  --board finance

hermes kanban create "Write integration tests" \
  --assignee coder \
  --parent <implement-task-id> \
  --board finance
```

When the researcher completes its task (`kanban_complete`), the coder's task auto-promotes from `blocked` to `ready`, the dispatcher spawns the coder profile with a fresh session, and the coder reads the researcher's handoff from the parent task's summary/metadata fields.

### Profile Discovery for Orchestrators

When acting as an orchestrator/planner, always discover what profiles exist before creating tasks:

```bash
hermes profile list
```

The kanban-orchestrator skill (loaded separately) has the full decomposition playbook. This skill covers how to create the profiles that orchestrator dispatches to.

## Verification

```bash
# Confirm the alias works
coder --version

# Confirm the right model
coder config get model.default

# Confirm SOUL.md loaded
coder chat -q "Who are you? Describe your role."

# Smoke test the kanban board
hermes kanban list --board finance

# Create a test task to verify dispatching
hermes kanban create "Smoke test: coder profile" \
  --assignee coder --board finance --body "Respond with 'CODER_SMOKE_OK'"
hermes kanban watch --board finance
```

## Sources

- [Hermes Profiles Docs](https://hermes-agent.nousresearch.com/docs/user-guide/profiles)
- [Hermes Kanban Docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban)
- [kanban-orchestrator Skill](file:///Users/yitang/.hermes/profiles/researcher/skills/devops/kanban-orchestrator/SKILL.md) — Decomposition playbook for routing work
- [kanban-worker Skill](file:///Users/yitang/.hermes/profiles/researcher/skills/devops/kanban-worker/SKILL.md) — Worker lifecycle pitfalls
