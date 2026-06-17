---
name: inference-cost-comparison
description: Compare local vs cloud API LLM inference costs using real power measurements and usage data.
version: 1.0.0
author: user
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [cost-analysis, local-inference, api-pricing, power-measurement, electricity-cost, gpu]
---

# Inference Cost Comparison (Local vs API)

Use this skill when the user asks whether running a model locally or using a cloud API is more cost-effective. Covers the full methodology: power measurement, API pricing lookup, and cost breakdown.

## When to use

- User asks "should I run locally or use the API?"
- User wants to calculate real cost of their local inference setup
- User shares power meter / kWh data and wants a cost analysis
- Evaluation of a new API provider's pricing against existing local hardware

## Cost comparison methodology

### 1. Gather API usage data

Pull actual usage from the API provider's dashboard or billing:

```
API Provider    Cache Hit  Cache Miss  Output
DeepSeek V4     X tokens   Y tokens    Z tokens
```

Official DeepSeek V4 Flash RMB pricing (current as of mid-2026):

| Category | Price / 1M tokens |
|---|---|
| Input (cache hit) | 0.02 元 |
| Input (cache miss) | 1.00 元 |
| Output | 2.00 元 |

For other providers, check `https://api-docs.deepseek.com/zh-cn/quick_start/pricing` (Chinese) or `https://pricepertoken.com/` (multi-provider comparison).

### 2. Measure local power consumption

Ask for the total kWh over a known time period. Then decompose into idle vs load.

**Quick method — Tapo smart plug + Hermes cron (recommended for ongoing tracking):**

If the server is plugged into a Tapo P110/P115 smart plug, set up automated logging that polls every 15 minutes and stores to SQLite. This gives you real power data without manual export/import.

```bash
pip3 install python-kasa
kasa discover             # find the plug's IP
kasa --ip <ip> emeter     # verify: returns W, V, A, Wh
```

See the [tapo-power-monitoring](references/tapo-power-monitoring.md) reference for the full Hermes cronjob setup: polling → SQLite → daily summary → idle alert.

**Ad-hoc method — nvidia-smi + turbostat (one-shot measurement):**

```bash
# GPU power draw (real-time, per GPU)
nvidia-smi --query-gpu=index,name,power.draw --format=csv,noheader,nounits

# Continuous monitoring
nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits -l 1

# CPU + DRAM package power (Threadripper/AMD RAPL supported)
sudo turbostat --show PkgWatt,CorWatt,GFXWatt,RAMWatt --interval 10
```

Choose the Tapo method if the server has a smart plug and you want persistent data. Choose nvidia-smi/turbostat for quick spot-checks or when there's no smart plug.

### 3. Estimate idle vs load power

Typical component-level power for a headless Linux LLM server:

| Component | Idle (W) | LLM Load (W) |
|---|---|---|
| TRX4 mobo + CPU (Threadripper) | 80-100 | 100-130 |
| DDR5 RAM (8 sticks) | 15-25 | 15-25 |
| RTX 3080 (headless) | 25-35 | 280-320 |
| RTX 3090 (headless) | 30-40 | 320-350 |
| Fans, NVMe, PSU loss | 20-30 | 30 |
| **RTX 3080 + 3090 total** | **~200** | **~780** |

**Validated real-world thresholds (TRX4 + 3080 + 3090, from smart plug data):**

| State | Power range | Typical | Meaning |
|---|---|---|---|
| Off | <10W | 6W | Server off, plug idle draw only |
| Idle | 10-350W | ~200W | System on, GPUs powered but idle |
| Busy (inference) | >350W | ~500W (avg) to ~780W (peak, both GPUs loaded) |

The 200W idle figure matches the ~200W GPU-only draw (idle GPUs) plus ~100W
platform. The 500W average during inference (vs 780W theoretical peak) suggests
only one GPU is fully loaded at a time in typical llama.cpp usage.

Use these as starting estimates. Refine with actual smart plug data (see
[tapo-power-monitoring](references/tapo-power-monitoring.md)).

**Solve for inference hours:**

```
total_kWh = load_W × load_hours + idle_W × (total_hours - load_hours)
load_hours = (total_kWh - idle_W × total_hours) / (load_W - idle_W)
```

### 4. Costs breakdown

| Component | Calculation | Daily cost |
|---|---|---|
| API usage | (cache_hit_tokens × cache_hit_price + cache_miss_tokens × cache_miss_price + output_tokens × output_price) / 1M | 元/day |
| Local idle | idle_W × total_hours × electricity_price / 1000 | 元/day |
| Local inference | load_extra_W × load_hours × electricity_price / 1000 | 元/day |
| Hardware depreciation | total_hardware_cost / (expected_lifespan_years × 365) | 元/day |

### 5. Compare

- **Total local cost** = idle + inference + depreciation
- **Marginal local cost** = inference only (only when server is multipurpose)
- **API cost** = direct from provider billing

## Validated monthly finding (real 31-day trace)

From 31 days of continuous TRX4 (3080+3090) power monitoring with cross-referenced Hermes session data:

| Metric | Value |
|---|---|
| Server electricity | **109 kWh / £27.26 / ¥250 per month** |
| Daily average | 3.6 kWh / £0.90 |
| DeepSeek API cost (same month) | ~¥200 (estimated from session data) |
| Idle waste (% of on-time) | **~50%** — server left on between work sessions |
| Hermes usage while TRX4 idle | **47% of all sessions** — could have used local model |

**Bottom line: The cloud API costs less per month AND delivers a larger, faster model.** The breakeven point never shifts in local's favour — GPU throughput is physically bounded and cloud models keep getting cheaper.

## Decision framework

Start here, not with the hardware:

```
User query: should I run this locally or use an API?
                │
        Can data leave your network?
           │                │
         YES                NO
           │                │
   Can data be sent to      └──→ Run local. (Cost doesn't matter —
   this specific provider?        privacy is the requirement.)
       │            │
      YES           NO
       │            │
  Use API.     Can you use a
  (Cheaper,    different provider?
  better         │           │
  model.)      YES          NO
                 │           │
            Use API.    Run local.
            (Same cost  (Accept the
             benefit.)   cost/quality
                         penalty for
                         privacy.)

```

## Non-cost factors — when local makes sense anyway

**Bottom-line verdict: privacy/control, not cost.** The API wins on every measurable dimension (cost per token, model capability, context window, speed). Local only wins when you **can't or won't** send data externally.

Even then, the hardware investment needed for a decent local model (≥RTX 3090, ~£3,000 system) costs more than **years** of API usage. The privacy constraint must be genuine — not speculative.

Rank these honestly with the user:

| Factor | Local win | API win |
|---|---|---|
| **Privacy** | Strong — zero data leaves your network | Weak — sent to provider (Chinese company for DeepSeek, US for OpenAI/Anthropic) |
| **Data sensitivity** | Proprietary code, PII, trade secrets, NDA'd work | Only for non-sensitive content |
| **Latency** | No network hop, purely PCIe/VRAM-bound | Adds ~100-500ms round-trip |
| **Reliability** | No rate limits, no deprecation, no outages | Can throttle, deprecate, or go down |
| **Model quality** | Constrained by VRAM (e.g. Qwen 3.6-35B-A3B: ~3B active) | Much larger (DS V4 Flash: 13B active, 284B total) |
| **Context window** | Typically 32K-128K | DS V4 Flash: 1M |
| **Version pinning** | Exact commit you control | Silent updates by provider |

**Decision tree:**

```
Can data leave your network? → NO → Run local
                              → YES → Can data be sent to [provider]?
                                      → YES → Use API (cheaper, better)
                                      → NO  → Run local
```

If the user already owns the server hardware and it runs other services (NAS, Docker, Plex), the marginal cost of running LLM locally is much smaller — only the extra GPU power draw. This can tip borderline cases toward local.

## Environment-specific quirks (captured from real setup)

### macOS: Hermes gateway launchd fails with symlinked profiles

If `~/.hermes/profiles` is a symlink (e.g., to a git repo), the launchd gateway service crashes at start with "Profile 'X' does not exist." The fix:

```bash
hermes gateway run --force   # runs foreground, survives while terminal is open
```

The underlying cause is that the plist's `HERMES_HOME` path resolves differently for launchd vs the shell. Using `--force` bypasses the service check.

### python-kasa on ARM Linux (RP4): authentication fails

python-kasa's AES transport fails consistently on Raspberry Pi 4 running Debian 12 Bookworm (Python 3.11, 64-bit ARM). The same python-kasa version works on macOS. The device is reachable (port 80 responds HTTP 200, ping works) but the KLAP/AES handshake returns `LOGIN_ERROR(-1501)` on every device.

**Root cause unknown** — possibly a cryptography library version mismatch on ARM, a device-side MAC-based auth cache, or an ARM-specific timing issue in the AES handshake. **Workaround:** run the Tapo cron on a different machine (e.g., a Mac that's always on). The RP4 is fine for API-only Hermes tasks that don't need Tapo access.

### Hermes on Raspberry Pi 4 — full setup

See the [hermes-rp4-setup](references/hermes-rp4-setup.md) reference for the
complete head-to-toe setup process: venv creation, profile + config, API key,
skills sync, color fix over SSH, and known limitations.

### Hermes colors broken over SSH

When running `hermes chat` over an interactive SSH session (especially from macOS to Raspberry Pi), Rich may output no colors (plain white text) or garbled escape sequences even though `TERM=xterm-256color` is set. The root cause is that the default Hermes skin uses 24-bit truecolor escape codes which some SSH/terminal combinations render incorrectly. Rich's `Console().color_system` may return `None` even with a valid `TERM`.

**Primary fix:** Switch Hermes skin to the daylight theme, which uses standard ANSI colors:
```
/skin daylight
```
Make it permanent in config.yaml:
```yaml
skin: daylight
```

**Secondary fix:** If the skin switch alone doesn't work, set `RICH_FORCE_COLORS=true`:
```bash
export RICH_FORCE_COLORS=true
hermes chat
```
Or permanently:
```bash
echo 'export RICH_FORCE_COLORS=true' >> ~/.bashrc
```
Note that `RICH_FORCE_COLORS=true` alone is often insufficient — the skin change is what actually resolves the issue.

### Hermes skills discovery on fresh install

On a freshly installed Hermes, the `skills/` directory may exist with SKILL.md files but `hermes skills list` shows nothing (or only 1-2 hub-installed skills). This happens because Hermes does NOT auto-discover local skills from the profile's `skills/` directory — it only picks them up if they're listed in a `skills.external_dirs` config entry.

**Fix:** Add the skills directory to `config.yaml`:
```yaml
skills:
  external_dirs:
  - ~/.hermes/profiles/default/skills
```

Without this, local skills are invisible. The `skills install` command does not support local file paths — only HTTP URLs are accepted. After adding `external_dirs`, run `hermes skills list` to verify all skills appear.

### Cron no_agent mode uses uv-managed Python

On macOS, Hermes cron no_agent mode runs scripts with `~/.local/share/uv/python/cpython-3.11.../bin/python3`, not the system Python or the profile's venv python. This Python can't load C extensions from a different Python version's site-packages. **Workaround:** use a shell wrapper (.sh) that `exec`s the correct venv Python, and point the cron `--script` at the `.sh` file instead of the `.py` file.

## Common pitfalls

- **Forgetting idle cost** — the server draws power even when idle. In a real 31-day trace (May 17-Jun 16), a TRX4 with 3080+3090 consumed **109 kWh costing £27.26**. On June 16 alone, 7h idle at ~200W wasted £0.35 — 31% of the day's total. If it runs 12h/day just for LLM, idle can be >50% of total electricity cost.
- **Including unrelated server costs** — if the server does other things (NAS, Docker, Plex), only count the *marginal* extra draw from the GPU under load.
- **Using average power instead of idle/load split** — 367W average over 12h hides the real cost structure. Always decompose.
- **GPU idle power on Linux** — headless Linux can idle 3090 at 30-40W, but with monitors attached or certain driver bugs, it can spike to 80-115W.
- **UK electricity price** — ~0.25 GBP/kWh (~2.3 元/kWh at mid-2026). Adjust for the user's location. Note the conversion rate matters — £0.25 ≈ 2.3 元, not 3 元.
- **Exchange rates** — DeepSeek publishes in RMB and USD. UK users pay DeepSeek in USD on the official API, but Chinese users via api-docs.deepseek.com pay in RMB at a different price tier.
- **`cache_read_tokens` is KV cache size, not cached prompt tokens** — in the Hermes sessions table, `cache_read_tokens` can be 100× larger than `input_tokens` (e.g. 432M cache vs 1.27M input). It represents the total KV cache read, not the number of prompt tokens served from cache. Don't use it to calculate cost savings from caching; the DeepSeek billing page provides actual cache hit/miss breakdown.\n- **No hourly token breakdown available** — neither DeepSeek API nor Hermes session logs provide hourly token counts. The Hermes messages.token_count DB column exists but is never populated. Use the sessions table instead (input_tokens, output_tokens, estimated_cost_usd per session). See [hermes-session-cost-schema](references/hermes-session-cost-schema.md).
- **v4-Pro cost shock** — a real trace showed 10 v4-Pro sessions (out of 102) drove $16.60 in API cost while 92 v4-Flash sessions cost near-zero. Always check model-level breakdown in the sessions table before declaring API costs. See [deepseek-v4-pro-vs-flash](references/deepseek-v4-pro-vs-flash.md).
- **Cross-referencing Hermes sessions with power data** — even without token counts, you can correlate activity by joining timestamp ranges between the Hermes state.db (messages table, unix epoch timestamp) and the power DB (power_samples table, ISO timestamp). This reveals what % of Hermes usage occurred while the server was busy vs idle vs off. See `scripts/cross-reference-power-and-sessions.py` and [hourly-cost-correlation](references/hourly-cost-correlation.md).
- **Validated 31-day finding: idle waste equals inference cost** — across 31 days of continuous smart plug monitoring, the TRX4 consumed 109 kWh (£27.26). Of the hours the server was on, ~50% were idle. The idle cost (~£13.63) roughly equalled the inference cost (~£13.63). Every month you pay roughly twice — once for actual work, once for keeping the server warm between sessions.
- **GPU-only power vs full-system power** — `nvidia-smi` reports GPU board power only (~280-350W at load), not the full system (~500W at load for TRX4). The missing ~150-200W is CPU, RAM, fans, chipset, and PSU loss. Always add platform overhead. Smart plug data captures the true total.
- **XLS file ordering** — Tapo app export files are unlabeled (no device name in filename). Match them by power signature, not file order. See [tapo-xls-export-format](references/tapo-xls-export-format.md) for the format and matching method.
- **TAPO_PASSWORD via shell** — when setting TAPO_PASSWORD in `.env` via SSH heredoc or echo, the password can be truncated if it contains special characters. Verify with `od -c` not just `grep`, since terminal output masking (`***`) hides the actual value. Use `sed -i` or `nano` for reliable edits.
- **RP4 SSH inherits host TERM** — when SSH-ing from macOS to RP4, the terminal type is forwarded from the Mac, but Rich may still fail to detect colors. The fix is `RICH_FORCE_COLORS=true`. See the environment quirk above.
- **Hermes estimated_cost_usd is unreliable** — never trust `estimated_cost_usd` in the sessions table. It uses a generic pricing model that doesn't match actual DeepSeek billing. Use the user's DeepSeek billing page numbers or recalculate from raw token counts using the correct pricing formula. The `actual_cost_usd` column is always NULL — Hermes never populates it.
- **cache_read_tokens ≠ cached prompt tokens** — `cache_read_tokens` in the Hermes sessions table represents total KV cache read size, not the number of prompt tokens served from cache. It can be 100× larger than input_tokens (e.g. 432M cache vs 1.27M input). Don't use it to calculate cost savings from caching. Use the DeepSeek billing page for actual cache hit/miss breakdown.
- **No hourly token breakdown available** — neither DeepSeek API nor Hermes session logs provide hourly token counts. The `messages.token_count` DB column exists but is never populated by Hermes. Use the `sessions` table (input_tokens, output_tokens per session) for daily/weekly aggregation. For hourly correlation with power data, join by timestamp ranges — but you'll get message counts, not token counts.
- **Cryptography on ARM is not always identical to x86** — python-kasa's AES transport uses `cryptography.hazmat.primitives.ciphers` which works differently on ARM Linux. Test crypto primitives with a standalone script before debugging Tapo auth on RP4.

## References\n\n- **[trx4-power-estimates.md](references/trx4-power-estimates.md)** — Power draw estimates for TRX4 + RTX 3080/3090 + Threadripper, validated against real 4.4 kWh / 12h measurement\n- **[deepseek-v4-pricing.md](references/deepseek-v4-pricing.md)** — Official DeepSeek V4 Flash and Pro pricing, links to authoritative sources\n- **[deepseek-v4-pro-vs-flash.md](references/deepseek-v4-pro-vs-flash.md)** — Real cost data from Hermes sessions DB showing v4-Pro drove 99.9% of API spend despite being 10% of sessions. Cost control strategies.\n- **[hourly-cost-correlation.md](references/hourly-cost-correlation.md)** — How to correlate power data with API cost without per-hour token data; SQL patterns for kWh calculation from mixed-interval data\n- **[tapo-power-monitoring.md](references/tapo-power-monitoring.md)** — Full setup guide for automated Tapo P110 smart plug power monitoring: python-kasa connection quirks, Hermes cron setup with shell wrappers, gateway scheduler, XLS export import, and SQL patterns for state breakdown\n- **[tapo-xls-export-format.md](references/tapo-xls-export-format.md)** — Tapo app XLS export file structure: which sheets contain hourly/daily/monthly data, 5-min power vs hourly avg, and how to match unlabeled files to devices by power signature\n- **[hermes-session-cost-schema.md](references/hermes-session-cost-schema.md)** — Hermes state.db sessions table schema: token count columns (input_tokens, output_tokens, cache_read_tokens, reasoning_tokens), cost columns (estimated_cost_usd, actual_cost_usd), model name, timestamps. Useful SQL queries for daily/hourly cost breakdowns.\n\n### Full analysis report (June 2026)\n\nA complete end-to-end analysis comparing DeepSeek V4 Flash API vs Qwen 3.6-35B on a TRX4 (3080+3090) is at:\n`~/dev/llm_local_vs_cloud/REPORT.md`\n\nContains: 31 days of smart plug data, hourly cross-reference with Hermes sessions, real API billing costs, and the final verdict that the cloud API is cheaper and better than local hardware for daily coding work.
