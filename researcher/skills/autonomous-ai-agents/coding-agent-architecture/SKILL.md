---
name: coding-agent-architecture
description: "Design principles and patterns for building effective autonomous coding agents. Covers architecture (simple while-loops, not complex DAGs), tool design (bash > custom APIs), skills engineering, context management, evaluator-optimizer feedback loops, and anti-patterns. Use when architecting or evaluating any coding agent system — Claude Code, Cursor, Codex, Hermes, or custom-built."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Coding Agent Architecture — Design Principles

General patterns for building effective autonomous coding agents. Derived from production deployments (Prompt Layer, Anthropic SWE-bench) and authoritative research (Anthropic Research, Martin Fowler/Thoughtworks).

## 1. Core Architecture: Keep It Stupidly Simple

The breakthrough in coding agents isn't complex DAGs or RAG systems — it's a **basic while-loop + tool calling** paired with increasingly capable models.

```
while there are tool calls:
    run the tool
    give results back to the model
repeat until no tool calls remain
ask the user for next steps
```

**"Less scaffolding, more model."** Custom routing code written to workaround model limitations becomes technical debt as models improve. The Zen of Python applies: flat, simple architectures outperform nested, heavily engineered ones.

## 2. Five Composable Patterns (Anthropic)

Don't build one monolithic architecture. Combine based on use case:

| Pattern | When to Use | Coding Example |
|---------|-------------|----------------|
| **Prompt Chaining** | Fixed subtasks | Write tests → confirm fail → implement → verify pass (TDD) |
| **Routing** | Distinct input categories | Easy fixes → Haiku, complex refactors → Sonnet/Opus |
| **Parallelization** | Independent subtasks, speed critical | Run linter + test suite + security scan simultaneously |
| **Orchestrator-Workers** | Unpredictable subtasks | Central agent breaks feature into files, delegates each to worker |
| **Evaluator-Optimizer** | Clear evaluation criteria exist | Writer produces code → reviewer critiques → fix loop (most important) |

The **evaluator-optimizer pattern** is the single most critical pattern for coding agents. One model writes code, another reviews it. Without this feedback loop, code "looks right" but contains subtle bugs.

## 3. Tool Design: Model Strengths First

### Bash Is the Universal Adapter
Models perform better on bash than custom tool interfaces due to vastly larger training data. A coding agent's most powerful tools aren't `read_file` or `write_file` APIs — they're `grep`, `find`, and shell commands.

### Unified Diffs Over Full Rewrites
Analogous to red-pen corrections: the model shows exactly what changes, uses less context, reduces errors. Full file rewrites waste tokens and introduce more failure surface.

### grep/glob > Embeddings for Code Search
Matches how human developers actually work. Avoid vector DB overhead for codebase navigation.

### Tools Matter More Than Prompts
From Anthropic's SWE-bench research: they spent **more time optimizing tools than the overall prompt**. The key is to run example inputs, observe mistakes, and iterate on tool definitions.

## 4. Skills Engineering (Context Leverage)

Skills are the most important performance lever for agent design. They use **progressive disclosure** — only name + description (~53 tokens/turn) are always loaded; full content reads on-demand.

### Skill Design Rules

- Keep SKILL.md under 500 lines, treat it as a Table of Contents
- Match specificity to task fragility: high freedom for code reviews, low for DB migrations
- Every token must justify its cost — if the model already knows Python syntax, don't explain it
- Provide utility scripts rather than telling the agent to generate them (more reliable, saves tokens)

### Skill Categories for Coding Agents

| Category | Purpose | Examples |
|----------|---------|----------|
| **Process discipline** | Enforce workflows | TDD, systematic debugging, spike experiments |
| **Review & verification** | Catch errors | Code review with security scan, independent subagent reviewer |
| **Planning** | Before large changes | Implementation plans, architecture sketches |
| **Communication** | Document decisions | Code documentation, architecture diagrams |
| **Debugging** | Systematic root cause | 4-phase debugging, log analysis patterns |

### Skill Loading Mechanics (Hermes)

The progressive-disclosure model has two tiers, and understanding both is critical:

| Tier | What's in the prompt | Token cost | When |
|------|---------------------|------------|------|
| **Index (always loaded)** | ALL skill names + descriptions in `<available_skills>` block | ~1,500-2,000 tokens for 77 skills (~20-25 tokens/skill) | Every session start |
| **Content (lazy-loaded)** | Full SKILL.md body | Variable (often 2-5K per skill) | Only when `skill_view()` or `/skill-name` is called |

**The nuance:** Every skill's name and description IS in every system prompt, not just the ones you'll use. The lazy-loading applies only to the SKILL.md body, not the index.

**Prompt caching mitigates the cost.** Most providers (OpenRouter, Anthropic, OpenAI) cache the system prompt after the first request. Subsequent turns pay a cache-hit rate (~10% of normal). The 1,500 tokens are paid once per session, not every turn.

**Impact order for profile-based role separation (from most to least impactful):**
1. **SOUL.md (personality)** — changes agent behaviour on every turn. Defines tone, workflow, quality gates.
2. **Model selection** — different models have different coding strengths. deepseek-v4-flash vs Qwen changes capability.
3. **Working directory** — default to project root saves typing and context mentions.
4. **Skills curated subset** — minor token savings (~800 tokens saved pruning 77→30), slightly better signal-to-noise. The model ignores irrelevant skills most of the time, but "eager" models may try to apply vaguely-matching skills and waste extra turns.

**Bottom line for profile design:** Invest in SOUL.md first, pick the right model second, and don't over-invest in skill curation. Pruning saves a small percentage of context — the real lever is what the SOUL.md tells the agent to do on every turn.

**Lazy loading the skill index doesn't exist yet.** Two open Hermes issues propose it:
- [#2045: Remove skill listing from system prompt, use on-demand tool](https://github.com/NousResearch/hermes-agent/issues/2045)
- [#37227: Category-aware smart skill indexing with lazy loading](https://github.com/NousResearch/hermes-agent/issues/37227)
Neither is implemented in the current codebase. When either ships, the token cost of a large skill index drops to near-zero.

## 5. Context Management: The Real Bottleneck

### Principles

- Start small — models improve rapidly, older verbose prompts become obsolete
- Use skills (not agent.md files) for everything except truly universal rules
- CLAUDE.md / AGENTS.md should only contain project conventions that apply to every task
- Monitor context fill-rate and compact proactively before hard limits

### When Models Get "Stupid"

When context fills up: the model's performance degrades measurably. Not a gradient decline — there's often a cliff. This is why context monitoring is essential for production agents.

## 6. Sub-Agents for Isolation, Not Complexity

Sub-agents fork isolated contexts to prevent pollution and enable parallelism. Use when:
- Multiple independent files need changes simultaneously
- One task needs different model capabilities (e.g., reviewer with stricter instructions)
- Parallel execution speed matters

**But:** start with one agent handling everything, build reliable skills first, then add sub-agents. Jumping straight to multi-agent architectures optimizes for what looks cool rather than what is productive.

## 7. Agent Separation Strategies: Profiles vs External Subprocesses

When you want a "dedicated coding agent," there are two fundamentally different approaches. Confusing them is the most common architectural mistake — they solve different problems:

### Approach A: Profile-Based Separation (same harness, different identity)

Hermes profiles are fully independent agent instances sharing the same Hermes installation. Each has its own `SOUL.md`, `config.yaml`, `.env`, skills, memory, sessions, and model.

**What you control per profile:**
| Knob | Effect | Example |
|------|--------|---------|
| `SOUL.md` | Personality, tone, workflow rules | "TDD, run tests before commits, save to 1_projects/" |
| `config.yaml` | Model, toolsets, working directory | deepseek-v4-flash for code, Qwen for research |
| Skills directory | Curated subset, isolated from other profiles | 30 dev skills vs 77 mixed skills |
| Memory/sessions | Separate cross-session context per role | Coder remembers past builds, not research notes |
| Terminal cwd | Default working directory | `~/para/1_projects/` vs `.` |

**When to use profiles:**
- You want different personality/rules per role (researcher → "cite sources", coder → "run tests first")
- You want a different model per role (cheap model for research, strong model for complex code)
- You want to isolate memory and sessions between roles
- You want all agents managed by the same Hermes instance (single update, shared infrastructure)
- Profiles collaborate via Kanban (durable task board in SQLite)

**How profiles collaborate (Kanban pattern):**
```bash
# Create tasks assigned to specific profiles
hermes kanban create "Research RAG approaches" --assignee researcher --board finance
hermes kanban create "Implement RAG pipeline" --assignee coder \
  --parent <research-task-id> --board finance

# Auto-promotion: when researcher completes, coder's task unblocks
# Dispatcher spawns the coder profile automatically
# Worker calls kanban_complete(summary="...") when done
```

Kanban is a durable SQLite task board (`~/.hermes/kanban.db`) — every status change is auditable, tasks survive crashes, and auto-promotion chains work without glue code. The dispatcher (runs in the gateway) claims `ready` tasks and spawns the assigned profile as a full OS process.

**Profile setup pattern:**
```bash
hermes profile create coder --clone-from researcher
$EDITOR ~/.hermes/profiles/coder/SOUL.md   # replace personality
coder config set model.default deepseek-v4-flash
coder config set terminal.cwd /Users/you/para/1_projects/
# Curate skills: remove creative/media/research, keep dev
rm -rf ~/.hermes/profiles/coder/skills/creative/*
```

### Approach B: External Subprocess (different harness, terminal orchestration)

Orchestrate a completely different agent harness (Claude Code, Codex CLI, OpenCode) via Hermes terminal tools. Each is a separate binary with its own model, tools, and skills system.

**When to use external subprocesses:**
- You need a harness with fundamentally different capabilities (Claude Code's worktree mode, Codex's sandbox, OpenCode's multi-agent system)
- You want parallel work on the same repo with git worktree isolation
- You want to use specialized models only available through that agent's provider
- The task is large enough to justify the overhead of spawning a full subprocess

**External agent integration pattern:**
```bash
# Claude Code in print mode (cleanest integration)
claude -p 'Add retry logic to all API calls' \
  --allowedTools 'Read,Edit' --max-turns 10 --output-format json

# Codex one-shot
codex exec 'Fix the TypeError in auth.py'

# OpenCode run
opencode run 'Add OAuth refresh flow'
```

### Decision Matrix

| Factor | Profile-Based | External Subprocess |
|--------|--------------|-------------------|
| Identity | Same agent, different personality | Completely different agent harness |
| Model | Any Hermes-supported model | Agent-specific models |
| Skills | Shared skill format, curated subset | Agent's own skill system |
| Memory | Separate per-profile SQLite | Agent-specific session store |
| Cost | Single API overhead | Each agent pays its own API cost |
| Parallelism | Via Kanban dispatcher | Via terminal background + worktrees |
| Crash recovery | Kanban auto-reclaims tasks | Worktree isolation, manual cleanup |
| Setup time | Minutes (clone + edit SOUL.md) | Install+auth each binary |
| Collaboration | Kanban board (shared SQLite) | Manual relay (Hermes reads output, passes to next) |

**Rule of thumb:** Start with profile-based separation. It's simpler, shares infrastructure, and Kanban handles orchestration. Only reach for external subprocesses when you need capabilities Hermes doesn't have (a specific sandbox model, a unique tool like Codex's `apply_patch`, or mass parallelism).

## 8. System Prompt Design Patterns (Borrowed from Other Agents)

SOUL.md is Hermes's equivalent of a coding agent's system prompt. The following patterns from production coding agents provide a design vocabulary for writing effective SOUL.md files. Full text and analysis in `references/system-prompts-from-other-agents.md`.

| Pattern | Source | Hermes SOUL.md Equivalent |
|---------|--------|--------------------------|
| **Concise identity** | All four agents state identity in 1-2 sentences | Opening line of SOUL.md |
| **Tone guidance** | Codex: "concise, direct, friendly"; Claude Code: "brief is good" | "You communicate efficiently" |
| **Coding conventions** | Claude Code: "default to no comments"; Codex: "fix root cause" | "TDD, run tests, git workflow" |
| **Project context first** | All: check CLAUDE.md/AGENTS.md before acting | "Load the project's AGENTS.md first" |
| **Test discipline** | All: validate before and after changes | "Run pytest before and after" |
| **Edit workflow** | Codex: apply_patch only; Claude Code: Read before Edit | "Use terminal for grep/find, file tools for edits" |
| **Output style** | Claude Code output styles; DeerFlow report templates | Section headings in SOUL.md |

See `references/system-prompts-from-other-agents.md` for the full collected prompts from Claude Code, Codex CLI, OpenCode agents, and DeerFlow v1/v2.

## 9. Anti-Patterns (What NOT to Do)

| Anti-Pattern | Why It Fails |
|--------------|-------------|
| Complex DAG orchestrators for simple tasks | Over-engineering; simpler agents outperform on identical benchmarks |
| Embedding-based code search | Vector DB overhead + poor accuracy vs grep/glob |
| Full file rewrites instead of diffs | More tokens, more error surface, slower iteration |
| Massive CLAUDE.md / AGENTS.md files | Burns tokens every turn; degrades performance as context fills |
| RAG for codebases | Adds latency with marginal benefit over grep + skill on-demand loading |
| One mega-agent for everything | Context pollution; use sub-agents or fresh sessions for distinct tasks |
| Prompt engineering over tool engineering | Tools matter more than prompts |

## 10. Evaluation & Testing Strategies

- **End-to-end integration tests:** Run agents against full tasks; verify final output
- **Point-in-time snapshots:** Capture mid-conversation state to test specific tool-call expectations
- **Backtests with historical traces:** Rerun production execution logs for regression testing
- **"Agent smell" metrics:** Track tool calls, retries, duration, and token usage to flag anomalies
- **Tool testing:** Treat tools like functions — unit-test deterministic tools, E2E test sub-agent tools

## 11. Related Skills

- `hermes-agent` — Hermes setup, configuration, spawning processes (the platform)
- `profiles` — Creating, cloning, managing Hermes profiles
- `kanban-orchestrator` — Multi-profile collaboration via task board
- `claude-code` — Claude Code CLI orchestration guide (external subprocess approach)
- `codex` — OpenAI Codex CLI orchestration guide (external subprocess approach)
- `opencode` — OpenCode CLI orchestration guide (external subprocess approach)
- `requesting-code-review` — Pre-commit code review workflow
- `test-driven-development` — TDD enforcement
- `systematic-debugging` — 4-phase root cause debugging

## References

Supporting reference files with sourced research, API documentation excerpts, and production case studies. See `references/` directory.
