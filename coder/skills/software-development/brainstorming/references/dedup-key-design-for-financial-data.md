# Dedup Key Design for Financial Data Imports

**Context:** Every financial import pipeline needs a dedup strategy — the same CSV file might be imported multiple times. A weak dedup key loses data; an overly aggressive one silently drops valid records. This document captures lessons from designing dedup keys across multiple pension and investment accounts.

## The Common Mistake: Using `ABS(amount)` as a discriminator

**Scenario:** Dedup by `(date, amount, description)` or `(date, ABS(amount), description)`, reasoning that two transactions on the same day with the same description but different amounts must be duplicates.

**Bug:** Two different management charges on two different funds on the same day have identical descriptions:

```
2025-10-08,Management Charge,0,0.79,Diversified Fund,...
2025-10-08,Management Charge,0,3.44,L&G PMC Transitioning Fund A,...
```

If dedup uses `(date, LOWER(description))` alone, one is lost. If it uses `(date, ABS(amount), description)` where "amount" is misidentified, charges on different funds with similar fees could collide.

**Fix:** Include `fund_name` (or any provider-specific entity identifier) in the dedup key:
```python
dedup = (date, LOWER(description), fund_name)
```
This is cheap, deterministic, and never collides unless the same transaction genuinely appears twice.

## The Correct General Pattern

**Rule:** A dedup key must be **surjective** — different real-world transactions must always produce different keys. Build it from the union of all columns that *uniquely identify* a real transaction in the source data, not just any numeric column.

### Per-account examples:

| Account | Dedup Key | Why |
|---|---|---|
| Barclays current account | `(date, amount, description_lower)` | One row per debit/credit — amount distinguishes different transactions on the same day. No entity dimension needed because each transaction is inherently unique by monetary value. |
| Vanguard ISA investment | `(date, cost, description_lower)` | Same principle — `cost` (total spend/receipt) distinguishes multiple buys/sells on the same day. |
| L&G Workplace Pension | `(date, LOWER(description), fund_name)` | Charges repeat across funds; switches produce paired entries. `fund_name` is the distinguishing dimension. |
| AMEX cards | `(date, amount, description_lower)` | Similar to Barclays — credit card transactions are distinguished by amount. |

## Edge Cases That Break Naive Dedup

1. **Same day, same description, different funds** — Management charges applied to multiple fund holdings. Fixed by including `fund_name`.

2. **Fund switches produce paired rows** — A "Switched Out" and "Switched In" on the same date are two valid transactions. They differ in description so a basic key handles them, but only if fund_name is included to catch same-description charges on different funds.

3. **Orphan rows with missing descriptions** — Some exports produce rows where the description column is empty (usually auto-adjustments). They form unique keys because `(date, '', fund_name)` differs from `(date, 'Management Charge', fund_name)`.

4. **CSV exports with timestamps** — If a CSV includes time components, use the full timestamp in the dedup key. Date-only keys would collapse morning and afternoon transactions on the same day.

## Design Checklist for Dedup Keys

Before finalizing a dedup key:
1. Can two *different* real-world transactions produce the same key? (If yes → add a column)
2. Is the key deterministic across export formats?
3. Does it handle empty/null fields gracefully?
