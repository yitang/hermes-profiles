# Greenfield Spec Example: Xtralnvest

> This is a real-world SPEC.md written for a greenfield CLI project. Use it as a template when the user says "let's design an app" — write a spec at this level of detail before touching any code.

## Project: Xtralnvest

A CLI tool to track a curated list of X (Twitter) users and understand their collective sentiment toward specific topics (e.g. "GLM 5.2", "$AAPL", "Bitcoin") via LLM analysis.

### What the spec covers

- **Problem statement** — why this tool exists
- **User stories** — 5 MVP stories in "As a… I want… so that…" format
- **Explicit non-goals** — what's NOT being built (price tracking, web UI, cron, backtesting, charts, notifications)
- **Data model** — 4 SQLite tables (users, topics, tweets, topic_mentions) with full column definitions, types, constraints, and indexes. Topics table is the key differentiator — users register keywords to scan for, rather than just parsing cashtags.
- **Architecture** — ASCII component diagram + data flow for each CLI command
- **CLI interface** — exact command signatures, exit codes, output conventions
- **LLM integration** — provider config, prompt design, batching strategy
- **Error handling philosophy** — fail fast on config, graceful on data errors
- **File layout** — exact directory structure
- **Future roadmap** — what comes in v0.2+

### Key patterns to reuse

1. **Non-goals section** — explicitly states what's deferred. Prevents scope creep and sets expectations.
2. **User stories first** — before any architecture or data model, define who uses it and what they do.
3. **Architecture diagram** — even a simple ASCII box diagram clarifies data flow and module boundaries.
4. **Data model before code** — column-by-column table definitions with types, constraints, and indexes. No ORM.
5. **LLM prompt design** — exact prompt text, expected JSON response format, batching, error handling.
6. **Error handling philosophy** — a short paragraph that guides implementation decisions without dictating every case.

### Source

Full text at `~/para/1_projects/xtrainvest/SPEC.md`.
