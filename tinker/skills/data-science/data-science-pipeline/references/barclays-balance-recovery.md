---
session_date: 2026-06-10
project: personal-finance-data
---

# Barclays Balance Recovery — Debugging the Coverage Check

## Background

Barclays had zero balances in `finance.db` despite having:
- OFX anchor: £4,020.87 on 2026-06-02 (from `barclays_2025_07_05_2026_06_05.ofx`)
- Last CSV transaction: 2026-06-02 (exact same day as anchor)
- Total rows: ~1,600 txns over 9 years

The old `_has_large_gaps()` function blocked it via the **80% coverage check**.

## Coverage analysis

| Metric | Value | Old check | New check |
|---|---|---|---|
| Inter-txn max gap | 24 days | — | Passes (≤30) ✅ |
| Gap to anchor | 0 days | — | Passes (≤10) ✅ |
| Coverage | 30.6% (946/3092 days) | **BLOCKED** <80% | Ignored ✅ |

## Root cause of false positive

The 80% coverage check was designed for HSBC-level sparsity (1 txn every ~111 days), where it correctly blocks backward-wind. But Barclays is the opposite — reasonably dense, with no gap exceeding 24 days between any two consecutive transactions. For a current account, this means no silent activity can accumulate, so backward-wind from the anchor is trustworthy regardless of whether you cover every calendar day.

## Fix applied

Removed the blanket coverage check from `_has_large_gaps()`. The only remaining guardrails:
1. Gap to OFX anchor ≤ 10 days
2. Max inter-txn gap ≤ 30 days

These are sufficient and no longer produce false negatives for dense accounts with long spans.
