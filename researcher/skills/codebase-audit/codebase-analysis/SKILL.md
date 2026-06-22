---
name: codebase-analysis
description: "Analyze codebases: quantitative (LOC metrics, language breakdown via pygount) and qualitative (architectural audit — patterns, gaps, improvement opportunities)."
version: 1.0.0
author: Hermes Agent (consolidated from codebase-audit + codebase-inspection)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-analysis, LOC, audit, architecture, review, pygount, metrics]
    related_skills: [requesting-code-review, plan]
---

# Codebase Analysis — Quantitative & Qualitative

Two approaches to analyzing a codebase, chosen by question type:

| Approach | When | Tool |
|----------|------|------|
| **Quantitative** | "How big is this repo?", "What languages?", "Code vs comments?" | pygount LOC metrics |
| **Qualitative** | "Review my architecture", "What patterns are missing?", "How should I improve?" | 3-phase architecture audit |

## 1. Quantitative: pygount Metrics

Quick language-level statistics:

```bash
pip install pygount
pygount --format=summary --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next" .
```

Columns: Language, Files, Code lines, Comment lines, Percentage.

### Common Filters

```bash
# Python only
pygount --suffix=py --format=summary .
# Python + YAML
pygount --suffix=py,yaml,yml --format=summary .
# JSON output
pygount --format=json .
```

Always exclude `.git`, `node_modules`, `venv` — without this, pygount hangs on large dep trees.

## 2. Qualitative: Architecture Audit (3 Phases)

### Phase 1: Read — Examine Actual Files

Read core files (entry points, data layer, schema definitions, supporting scripts).

### Phase 2: Map — Identify Patterns Present and Missing

Compare against standard architectural concepts, adapted to scale. Key questions:
- Does the system silently accept garbage?
- Can you safely re-run (idempotent)?
- When upstream changes format, is there a clear signal?
- Are computed values current or stale?

### Phase 3: Recommend — Prioritised Findings

**Already solid** → **Priority 1** (high impact, low effort) → **Priority 2** (medium effort) → **Nice-to-have**.

Each recommendation includes: why it matters, how to implement, effort estimate.

### Pitfalls

- Don't recommend enterprise tooling for single-user problems
- Don't recommend without reading the actual code
- Don't dismiss what's working
