# TRX4 Power Estimates

Validated breakdown for a headless TRX4 server with RTX 3080 + RTX 3090 running llama.cpp for LLM inference. Based on a real 4.4 kWh / 12h measurement (8am-9pm).

## Component-level estimates

| Component | Idle (W) | LLM Load (W) | Notes |
|---|---|---|---|
| TRX4 mobo + Threadripper CPU | 80-100 | 100-130 | RAPL PkgWatt; idle includes chipset, fans |
| DDR5 RAM (8 sticks) | 15-25 | 15-25 | RAMWatt stable regardless of LLM load |
| RTX 3080 (headless Linux) | 25-35 | 280-320 | Headless = no monitors; nvidia-smi power.draw |
| RTX 3090 (headless Linux) | 30-40 | 320-350 | Same; 3090 has higher TDP (350W vs 320W) |
| NVMe drives, PSU losses, case fans | 20-30 | 30 | Higher under load due to GPU heat = faster fans |
| **Total** | **~200** | **~780** | Idle-to-load delta: ~580W |

## Decomposing a 4.4 kWh / 12h reading

```
load_hours × 780W + (12 - load_hours) × 200W = 4400 Wh
load_hours × 580W = 4400 - 2400
load_hours ≈ 3.45h
```

Result: ~3.5h inference, ~8.5h idle.

## Cost breakdown (UK electricity @ 0.25 GBP/kWh ≈ 3 元/kWh)

| Component | kWh | 元/day | 元/month (30d) |
|---|---|---|---|
| Idle base (200W × 12h) | 2.4 | 5.6 | 168 |
| Inference delta (580W × 3.5h) | 2.0 | 4.7 | 141 |
| **Total** | **4.4** | **10.3** | **309** |

## Key takeaway

Idle cost (~54% of total) dominates. If the server stays on 12h/day regardless of LLM use, that 5.6 元/day is pure waste when not running inference. Powering down or suspending between sessions cuts this to near zero.

## See also

- [deepseek-v4-pricing.md](deepseek-v4-pricing.md) — DS V4 Flash pricing for cost comparison
