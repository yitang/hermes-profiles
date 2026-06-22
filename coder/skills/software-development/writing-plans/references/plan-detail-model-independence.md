# Plan Detail and Model Independence

**Observed:** 2026-06-16 | Two models compared: Qwen3.6-35B-A3B vs DeepSeek V4 Flash

## Finding

A plan with complete copy-pasteable code for every task makes the model choice nearly irrelevant. Both models produce equivalent output when the plan leaves no room for interpretation.

## First plan (under-specced) — rejected
- Tasks 5-7 (page templates): paragraph descriptions only, no HTML/JS code
- API tasks 3-4: "similar pattern" references instead of full code
- User flagged: "does it matter if I use SDD to implement?"

## Second plan (fully-specced) — accepted
- Every API route: complete file with all endpoints
- Every template: complete HTML + JS, copy-pasteable
- Every test: exact assertions
- Result: both models produced near-identical code (cosmetic escape-char differences only)
- Qwen: 228 lines of tests, 93 passed. DeepSeek: 107 lines, 82 passed. Both correct.

## Rule

When writing plans: **every task must contain complete code**. Paragraph descriptions = model divergence. Copy-pasteable code = model independence. The implementer should be a transcription service, not a designer.

## Implementation

Add this as a checklist item in the plan review step (Step 6):
- [ ] Every code task contains complete copy-pasteable code (not "similar pattern" or paragraph descriptions)
