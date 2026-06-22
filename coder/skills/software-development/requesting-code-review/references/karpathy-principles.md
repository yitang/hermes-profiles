# Karpathy Coding Principles — Code Review Reference

A condensed reference of the four principles from
[andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
(Forrest Chang, MIT, 177k+ stars), distilled from Andrej Karpathy's observations
on LLM coding pitfalls. Apply these as additional quality lenses during review.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementation, the agent should:
- State assumptions explicitly. If uncertain, ask.
- Present multiple interpretations when ambiguity exists — don't pick silently.
- Push back if a simpler approach exists.
- Stop when confused. Name what's unclear. Ask.

**Review angle:** Was the solution the *only* viable one, or did the agent
silently pick one path? Does the code suggest unstated assumptions about
environment, scale, or usage patterns?

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If 200 lines could be 50, rewrite it.

**Test:** Would a senior engineer say this is overcomplicated?

**Review angle:** Does every abstraction pay for itself right now? Is there an
interface/strategy/hierarchy that only exists "in case we need it later"? Could
a plain function replace a three-file module?

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

**Test:** Every changed line should trace directly to the user's request.

**Review angle:** Compare the diff to the stated goal. Count lines that are not
strictly necessary. Style drift? Collateral reformatting? Comment changes on
unchanged code? These are surgical violations.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform imperative tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, each step should have an explicit verification check.

**Review angle:** Does the commit message or PR description state what was
verified? Are there tests that prove the bug is fixed or the feature works?
Or is it "trust me, it works"?

## Applying in Review

When a reviewer evaluates a diff, run through in order:

1. **Surgical** — Scan every changed line. Does each trace to the request?
   Flag formatting-only changes, style drift, or collateral edits.

2. **Simplicity** — For each new function/class, ask: is this the simplest
   expression of the requirement? If there's an abstraction that serves
   no immediate purpose, flag it.

3. **Think** — Did the solution expose any unstated assumptions the user
   should know about? If so, surface them in the review notes.

4. **Goal** — Is there a verification trail? Tests, screenshots, logs,
   or at minimum a clear description of what was verified and how.
