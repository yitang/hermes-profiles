# Mortgage Amortization — Common Pitfalls (Session 2026-06-11)

Concrete examples of plan-vs-reality drift found when auditing a subagent-generated mortgage amortization implementation.

## Bug: Off-by-one in amortization loop break condition

**What happened**: `mortgage.py` line 60 checks `if end_date and d >= date.fromisoformat(end_date): break` AFTER the yield statement on line 58. This means when `d` equals the end date, it still yields that row before breaking. For NatWest (end: 2024-10-31), this produced a row for 2024-11-01 — one month past the stated boundary.

**Correct pattern**:
```python
for m in months:
    # compute interest/principal/balance
    yield (m, balance)   # emit BEFORE checking end
```
vs correct:
```python
for m in months:
    if m > last_valid_month:  # check boundary FIRST
        break
    yield (m, balance)
```

## Bug: Key name drift between config and parser

**Plan specified**: `start_date` / `end_date` keys  
**Code used**: `start` / `end` keys  

The config file (`mortgage_config.py`) was written with different key names than the parser expected. This doesn't crash (both files use whatever keys they define internally) but means:
- If either side changes and the other isn't updated, silently wrong values flow through
- Cross-referencing plan against code requires a full `grep` of every field name

## Bug: Name string mismatch in DB

**Plan**: "NatWest Mortgage" / "Barclays Mortgage"  
**Actual DB**: "NatWest" / "Barclays"  

Downstream queries using the full plan names will return zero rows. The fix is simple (update queries), but it's a common category of error — always verify `SELECT DISTINCT name FROM table` after any schema or data generation task.

## Bug: Unvalidated cross-check numbers

**Plan expected**: NatWest ending balance ≈ £461,055 (±£5)  
**Actual computed**: £456,337.23 (~£4,700 off)  

The subagent ran `python3 mortgage.py` successfully and reported row counts — but never actually queried the DB to confirm the critical handoff numbers matched expectations. The plan's validation section (Step 2: "should be very close to £461,054.79") was not re-executed in the audit phase.

## What to check first when auditing a financial data pipeline

1. `SELECT DISTINCT name FROM <table>` — do names match plan?
2. Min/max dates per entity — are they within stated boundaries?
3. Cross-entity boundary values — does Entity A's end match Entity B's start?
4. Row counts — do they match expected durations (e.g., 60 months for 5 years)?
5. Run the plan's own validation queries verbatim, don't just trust "import succeeded"
