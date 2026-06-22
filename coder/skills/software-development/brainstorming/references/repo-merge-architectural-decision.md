# Repo Merge Architectural Decision — Anti-Pattern

## The Trap

When two repos are tightly coupled — e.g., a data pipeline repo and an app repo where the
app's sync layer has per-bank mapping functions — the instinct is to merge them. "One PR
can update both sides atomically." This is recency-bias-driven and often wrong.

## The Right Question

**Is the coupling structural or accidental?**

- **Structural:** The pipeline's output IS the per-bank format. The app genuinely needs
  bank-specific knowledge. No amount of pipeline work can remove it. Merging makes sense.
- **Accidental:** The app is compensating for the pipeline not finishing its job. The
  pipeline dumps raw per-bank tables; the app re-normalizes them into a canonical format.
  The coupling is self-inflicted.

## The Fix: Move Normalization Upstream

If the coupling is accidental, the fix is NOT to merge repos. The fix is to make the
pipeline produce canonical output (`transactions`, `investment_trades`, `balance_sheet`)
instead of per-bank tables. Then the app sync becomes a thin incremental copy — ~100 lines
instead of ~1100.

The test: after the fix, does the app still need to know about Barclays vs AMEX column
layouts? If not, the repos are genuinely independent.

## When Merging IS Correct

- The pipeline has exactly one consumer and will never have another
- The coupling is structural (both sides need the same domain knowledge)
- The coordination tax of separate repos exceeds the cost of extraction later

Extraction is a one-time exercise (git filter-repo). Ongoing split cost is permanent.

## User Signals

If the user says "this does not sound right at all" when you describe their own
architecture, you've misdiagnosed. Step back. Ask what they intended. The gap between
their intent and the current code is where the real problem lives.
