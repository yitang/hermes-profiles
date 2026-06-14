# Context Engineering for Coding Agents (Source Summary)

## Source: Martin Fowler/Thoughtworks, Birgitta Böckeler (Feb 2026)

### Core Definition
"Context engineering is curating what the model sees so that you get a better result." — Bharani Subramaniam

### Context Configuration Categories

1. **Reusable Prompts**
   - Instructions: Task-specific commands
   - Guidance/Rules/Guardrails: General conventions (e.g., "always write independent tests")

2. **Context Interfaces** (How the LLM fetches additional context)
   - Tools: Built-in capabilities (bash, file search)
   - MCP Servers: Custom programs via Model Context Protocol
   - Skills: On-demand resources, docs, scripts, instructions
   - Workspace Files: Codebase itself

### Context Size Management

- **Larger context ≠ better performance.** Overloading degrades effectiveness and increases costs.
- **Build iteratively.** Models improve rapidly; older verbose prompts become obsolete.
- **Monitor fill-rate** — track context usage to maintain optimal balance.

### Illusion of Control Warning
> "In spite of the name, ultimately this is not really engineering… Once the agent gets all these instructions and guidance, execution still depends on how well the LLM interprets them!"

Phrases like "ensure it does X" or "prevent hallucination" are probabilistic, not deterministic. Design for verification, not perfect compliance.
