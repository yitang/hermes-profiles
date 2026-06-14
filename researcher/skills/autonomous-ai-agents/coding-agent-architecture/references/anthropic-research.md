# Anthropic: Building Effective Agents (Source Summary)

## Key Definitions & Facts

- **Agentic Systems:** Umbrella term for all LLM-driven task execution systems.
- **Workflows:** LLMs/tools orchestrated through *predefined code paths*.
- **Agents:** LLMs that *dynamically direct* their own processes and tool usage.
- **Augmented LLM:** Base building block enhanced with retrieval, tools, and memory.

## Recommended Models for Routing

| Use Case | Model | Rationale |
|----------|-------|-----------|
| Easy/common queries | Claude Haiku 4.5 | Low cost, sufficient capability |
| Hard/unusual queries | Claude Sonnet 4.5 | Higher reasoning capacity |

## Pattern Selection Guide

### When to Use Each Pattern

| Approach | Best For | Trade-offs |
|----------|----------|------------|
| Single LLM Call + Retrieval | Most standard applications | Lowest latency/cost; start here |
| Workflows | Well-defined tasks requiring predictability | Higher latency, controlled execution |
| Agents | Open-ended problems, unpredictable step counts | Higher cost, compounding error risk |

**Rule of Thumb:** Find the simplest solution. Only increase complexity when it measurably improves outcomes.

### Pattern Details

1. **Prompt Chaining** — Sequential steps with programmatic gates. Trade latency for accuracy.
2. **Routing** — Classify input → direct to specialized task/prompt/toolset. Requires accurate classification.
3. **Parallelization** — Sectioning (independent subtasks) or Voting (same task, diverse outputs). Critical when speed matters.
4. **Orchestrator-Workers** — Central LLM dynamically breaks down tasks, delegates, synthesizes. Use when subtasks are unpredictable.
5. **Evaluator-Optimizer** — Loop where one LLM generates, another evaluates/provides feedback. Sign of fit: human feedback improves output AND the LLM can replicate that feedback.

## SWE-Bench Findings

- Agents now solve real GitHub issues from PR descriptions alone (SWE-bench Verified).
- **More time optimizing tools than the overall prompt** — test how the model uses YOUR tools, not generic examples.
- The core insight: "the models are good now" — the differentiator is context and harness quality.
