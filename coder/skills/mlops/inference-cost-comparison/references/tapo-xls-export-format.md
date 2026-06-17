# Tapo XLS Export Format

When exporting from the Tapo app, each device produces 2 `.xls` files:

## Energy Usage.xls (3 sheets)

| Sheet | Content | Format | Rows |
|---|---|---|---|
| 0 | Hourly kWh, last ~7 days | `2026/06/11 00:00:00`, `0.053` | 163 |
| 1 | Daily kWh, from first connection | `2026/04/01`, `2.859` | 79 |
| 2 | Monthly kWh, from install | `2025/07`, `58.178` | 13 |

## Power.xls (2 sheets)

| Sheet | Content | Format | Rows |
|---|---|---|---|
| 0 | 5-min power (W), last ~24h **only** | `2026/06/16 17:10:00`, `70.0` | 290 |
| 1 | Hourly avg power (W), last 7 days | Same timestamps as Energy sheet 0 | 163 |

## Device matching by power signature

Files are unlabeled (no device name in filename). Match by reading Sheet 0:

- **~500W → 6W after a few hours** = inference machine that was turned off (TRX4)
- **70-510W throughout** = mid-range workstation (B760)
- **70-85W throughout** = desktop with low draw (iMac)
- **Always 6-7W** = network device / always-on low-power (router/RP4)

## Import

Use `tapo-import.py` at `~/.hermes/profiles/coder/scripts/tapo-import.py`.
Reads all 6 XLS files, maps to devices by hardcoded IP labels, deduplicates by
fuzzy timestamp within 30 seconds.
