# Reference: MVP CLI Project Plan Example — Xtralnvest

This is a real-world example of an MVP plan for a Python CLI project that tracks X (Twitter) users for investment ideas. Use this as a template for planning similar CLI + SQLite + external API projects.

## What makes this plan a good example

### 1. Clear MVP Scope
The plan has an explicit **Out of Scope** section listing what's cut from MVP. This prevents scope creep and sets expectations.

### 2. Requirements Mapping Table
A table mapping each user requirement to the task(s) that deliver it. This lets the user approve the plan at a glance without reading every detail.

### 3. Data model first
The SQL schema is defined upfront in the plan, before any implementation details. This anchors the rest of the system.

### 4. Bite-sized tasks
Each task is a focused deliverable (DB layer, fetcher, CLI, etc.) with:
- Exact file paths
- Exact function signatures
- Dependencies between tasks noted

### 5. Risks & Open Questions
A dedicated section at the end for things that could block execution. Keeps them visible, not buried.

## Structure template

```
## Data Model
[SQL schema or class definitions]

## Tasks
### Task N: Name
**Objective:** One sentence
**Files:** Create/Modify paths with line numbers
**Implementation notes:** Key design decisions
**Verification:** Exact command + expected output

## Requirements Mapping
| Requirement | Task(s) |
|---|---|

## Out of Scope (MVP cuts)
[bullet list]

## Risks & Open Questions
[bullet list]
```

## When to use this template

- Any CLI-first project with SQLite persistence
- Projects that call external APIs (X, GitHub, etc.)
- MVP phases where scope control matters
- Any plan that needs user buy-in before implementation
