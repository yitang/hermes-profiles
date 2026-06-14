# Account Registry

## Cash-flow accounts (in v_combined)

| DB Table | Account | Date Range | Balance? | Rows |
|---|---|---|---|---|
| barclays | Barclays Current | 2017-12 → 2026-06 | Yes | 1,842 |
| amex_gold | AMEX Gold | 2019-12 → 2026-06 | No | 2,172 |
| amex_ba | AMEX BA | 2024-05 → 2026-06 | No | 950 |
| hsbc | HSBC Current | 2020-03 → 2026-05 | Yes | 492 |
| hsbc_credit | HSBC Credit Card | 2026-01 → 2026-02 | Yes | 3 |
| lloyds | Lloyds (closed) | 2017 | Yes (stale) | 5,349 |

## Balance-sheet accounts

| DB Table | Account | Kind | First → Last | Months |
|---|---|---|---|---|
| vanguard_isa_cash | Vanguard ISA Cash | asset | 2019-05 → 2026-06 | 86 |
| vanguard_isa_investment | Vanguard ISA Investment | asset | 2019-05 → 2026-06 | 86 |
| vanguard_pension_cash | Vanguard Pension Cash | asset | 2022-03 → 2026-06 | 52 |
| vanguard_pension_investment | Vanguard Pension Investment | asset | 2022-03 → 2026-06 | 52 |
| mortgage (NatWest) | NatWest Mortgage | liability | 2019-11 → 2024-10 | 60 |
| mortgage (Barclays) | Barclays Mortgage | liability | 2024-11 → 2045-02 | 244 |

## Investment holdings (current)

| Account | Fund | Units | Price | Value |
|---|---|---|---|---|
| Vanguard ISA | LifeStrategy 100% Equity Acc | 104.2414 | £486.33 | £50,695.72 |
| Vanguard Pension | Target Retirement 2055 Acc | 25.4348 | £253.81 | £6,455.61 |

## NatWest → Barclays handoff

- NatWest loan: £545,000 at 1.97%, £2,302.05/mo, 2019-11 to 2024-10
- Computed end balance: £456,337.23 (60 months)
- Barclays loan: £461,054.79
- Gap: -£4,717.56 (remortgage fees/charges, known and accepted)
