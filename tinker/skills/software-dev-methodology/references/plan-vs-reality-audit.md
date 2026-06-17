# Plan-vs-Reality Audit Template

Use this structured comparison to verify whether a plan has been faithfully implemented before declaring completion. Run through every phase of the plan, not just the last one.

## How to audit each phase

For each plan section (Phase N / Step N):

1. **Check existence** — Does the required artifact exist? (files, tables, functions)
2. **Check correctness** — Does it produce the expected output? (row counts, dates, routing)
3. **Check fidelity** — Did you follow the plan's stated approach, or did you deviate? Document any deviation with reason.

## Output format

For each item in the plan:

```
| Item | Plan requirement | Reality | Status |
|------|-----------------|---------|--------|
| Phase 0: Merge archive/ | git mv archive/ data/raw/ | Done ✓ | PASS |
| import.py unchanged | No modifications | Modified (see below) | FAIL ⚠️ |
```

Use three severity levels:
- **PASS** ✅ — exactly matches plan
- **WARNING** ⚠️ — deviated from plan but deviation is justified (document WHY)
- **FAIL** ❌ — missing, broken, or unjustified deviation

## Key things to check beyond "does it work"

1. **init_schema.py creation** — If the plan assumes this file exists but it doesn't, note that you CREATED it rather than finding it.
2. **Balance computation scope** — Only accounts with OFX LEDGERBAL anchors get real balances. CSV-only accounts will have `balance=0` (data-availability limitation). This is correct behavior, not a bug.
3. **Header collision verification** — Simulate detect_account() on ALL cleaned CSV pairs to confirm no collisions remain.
4. **v_combined view completeness** — Every table must appear in the union view. A missing `UNION ALL` means queries against the combined view silently skip that account's data.
5. **Git history vs reality** — Files may exist on disk but not be tracked by git. Check `git status --short` alongside filesystem listings.

## Common deviation justifications (record these)

- Header collision between two accounts' CSV outputs → filename-based routing added to detect_account()
- Missing init_schema.py in original codebase → created new schema file
- Balance computation on CSV-only accounts falls back to zeros → data availability issue, not implementation bug
- OFX anchor tag (`<LEDGERBAL>`) absent from exported OFX → balance stays at zero for that account
