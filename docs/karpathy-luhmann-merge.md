# Karpathy Principles — Luhmann Profile Injection

## Source

Same as coder profile: [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills),
Karpathy's four LLM coding principles translated for knowledge work.

## Key architectural change

The zettelkasten-workflow skill was a mix of behavioral rules, procedures,
reference commands, and diagnostics. Core principles now live in SOUL.md
(the identity layer, loaded every turn); the skill retains only procedures
and reference material (loaded for specific tasks).

## What moved from skill → SOUL.md

| Section from skill | New home in SOUL.md |
|---|---|
| Core principle: atomicity (14 lines) | Note-writing principles (4 bullets) |
| Why this workflow (3 lines) | Removed (rationale implicit in framing) |
| Key rule (1 line) | Key rule section |
| Self-review diagnostics (29 lines) | Quality gates section |

## New content in SOUL.md (adapted from Karpathy)

### Note-writing principles (4 bullets)

Maps Karpathy's coding principles to zettelkasten equivalents:

| Karpathy principle | Zettelkasten equivalent |
|---|---|
| Simplicity First | Atomic — one idea per note, no speculative links |
| Think Before Coding | Think before writing — surface ambiguity before encoding |
| Surgical Changes | Surgical edits — every changed line traces to the task |
| Goal-Driven Execution | Define "done" — verifiable processing criteria |

### Key rule

Every fleet note must be processed within a week — from Karpathy's "no
unvalidated execution" principle applied to knowledge processing.

### Quality gates

Adapted from the skill's self-review checklist. 8 verifiable checks across
per-note and vault-level dimensions.

## File size changes

```
                       Before    After    Change
SOUL.md                29 lines  58 lines  +29
zettelkasten-workflow  267 lines 217 lines  -50
Total                  296      275        -21 (net)
```

## Tradeoff note

Promoting principles to SOUL.md means they're active from session start
rather than discovered when loading the skill. The risk is SOUL.md bloat;
at 58 lines this is still lean.

Drift risk: if behavioral rules are updated, both SOUL.md and the skill's
processing steps must be consistent. Mitigated by keeping the skill's
processing as `procedure-driven` (following SOUL.md principles without
redefining them).
