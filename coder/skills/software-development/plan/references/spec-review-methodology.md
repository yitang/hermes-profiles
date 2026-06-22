# Spec Review Methodology

Systematic section-by-section review of a SPEC.md to identify issues before writing the implementation plan. Use when the user has a spec draft and wants feedback, or as step 2 of the design-first workflow.

## Review Categories

For each spec section, check these dimensions:

| Category | Question | Example |
|---|---|---|
| **Ambiguity** | Can this be interpreted multiple ways? | "topics" — tickers or concepts? |
| **Inconsistency** | Does this contradict another section? | Data flow mentions a query function not listed in component spec |
| **Missing detail** | Is a boundary case or failure mode undefined? | "context_snippet" — which occurrence? What if at start of text? |
| **Numbering/formatting** | Are sections ordered logically? Headers consistent? | Sections 10 and 11 swapped |
| **Cross-cutting** | Is a behaviour documented where it's most relevant? | Deduplication on fetch — stated in schema but not in fetch section |

## Process

1. **Read the full spec** — get the whole picture before nitpicking
2. **Go section by section** — present findings grouped under each section heading
3. **State what's fine** — "Section 1: Fine. Clear, scoped." builds trust and saves time
4. **Be specific** — quote the exact text that's wrong, not a paraphrase
5. **Propose the fix inline** — don't just flag problems, state the correction
6. **After full review, ask before applying** — "Want me to fix these in the SPEC?"
7. **Apply fixes with targeted `patch` calls** — one per logical change, not batch rewrites

## Issue Severity

- **Bug-level**: copy-paste errors, contradictory statements, broken references — fix immediately
- **Design-level**: missing constraints, underspecified behaviour, ambiguous defaults — flag for decision
- **Polish**: numbering, formatting, wording — fix without debate

## When NOT to Deep-Review

- The spec is clearly a rough draft and the user wants direction, not line-editing
- The user explicitly says "just give me high-level feedback"
- The spec is under 20 lines — it's a sketch, not a spec

## Pitfalls

- Don't bikeshed wording when the meaning is clear
- Don't propose architecture changes — spec review is about correctness and completeness, not redesign
- Don't report issues you're not confident about — "I think this might be wrong" wastes the user's time
