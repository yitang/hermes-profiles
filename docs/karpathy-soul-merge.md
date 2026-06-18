# Karpathy SOUL.md Merge — Analysis and Decisions

## Source

[andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) by
forrestchang — 177k star repo distilling Andrej Karpathy's LLM coding pitfalls into
a single CLAUDE.md (70 lines, 4 principles).

## Context: existing workflow

The coder profile's SOUL.md drives a stack of superpower skills:

1. Brainstorming → pin down spec from vague idea
2. Git worktrees → isolated workspace
3. Writing plans → task list with verify steps
4. SDD (subagent-driven development) → implementer + spec reviewer + quality reviewer
5. Finishing a development branch → merge/PR/discard

## Overlap analysis against Karpathy's 4 principles

| Principle | Our coverage | Gap |
|-----------|-------------|-----|
| Think Before Coding | Brainstorming skill + SDD clarification pattern | None meaningful |
| Simplicity First | Spec reviewer checks "no extras" | Medium — catches feature creep but not architectural overcomplication |
| Surgical Changes | "No scope creep" in workflow item 4 | High — too vague to catch formatting/comments/style/dead-code scope creep |
| Goal-Driven Execution | Plan verify steps + TDD enforcement + verification-before-completion | None — fully covered and stronger than Karpathy version |

## Key insight: architectural difference

Karpathy's CLAUDE.md = prompt-level constraint inside one agent (self-regulation).
Our SDD stack = orchestration-level constraint externalized into separate agents
(implementer doesn't self-review; spec reviewer and quality reviewer are different agents).

Our approach is more robust for covered cases but has a blind spot: anything not
explicitly checked by the orchestration layer is never caught. The Karpathy file's
strength is providing concretely worded self-checks for the moments between explicit
gates.

## Changes made to SOUL.md

### Change 1: "No scope creep" → "Surgical changes" (Development Workflow item 4)

Replaced the vague "don't add features" with the specific Karpathy enumeration:

> Every changed line should trace directly to the user's request. Don't reformat
> adjacent code, refactor things that aren't broken, or change comments unrelated
> to the task. Match existing style even if you'd do it differently. If you notice
> unrelated dead code, mention it — don't delete it. Clean up imports/variables
> YOUR changes made unused, but don't touch pre-existing orphan code unless asked.

This addresses the primary gap: the most common form of LLM collateral damage that
the old "no scope creep" rule failed to catch.

### Change 2: Simplicity first (Coding Conventions)

> Before finalising, ask yourself: would a senior engineer say this is
> overcomplicated? If yes, simplify. No abstractions for single-use code, no
> "flexibility" that wasn't requested.

This provides a concrete self-check against architectural overcomplication, which
the spec reviewer cannot catch (it only checks feature-level scope).

### Change 3: "Present alternatives" (Development Workflow item 1)

Appended to existing "Understand first" rule:

> If multiple interpretations exist, present them — don't pick silently.

Forces surfacing ambiguity before committing code to an interpretation.

## Scope boundary: SOUL.md only

These changes apply to the orchestrator agent (the session lead). They do not
automatically propagate to SDD subagents. The two-stage review loop (spec + quality)
is trusted to catch downstream violations. If subagent scope violations appear in
practice, the Karpathy rules can be injected into SDD task contexts as a follow-up.

## Tradeoff note

These rules bias toward caution over speed. For trivial changes (1-line fixes, obvious
typos), judgement applies — the full rigor is for non-trivial work where the cost
of a mistake exceeds the cost of careful execution.
