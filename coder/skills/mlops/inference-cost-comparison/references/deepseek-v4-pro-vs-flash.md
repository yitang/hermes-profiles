# DeepSeek Model Tier Cost Analysis — v4-Pro vs v4-Flash

## Pricing comparison

Official DeepSeek V4 pricing (RMB, as of mid-2026):

| Category | V4 Flash | V4 Pro |
|---|---|---|
| Input (cache hit) | 0.02 元 / 1M | 0.025 元 / 1M |
| Input (cache miss) | 1.00 元 / 1M | 3.00 元 / 1M |
| Output | 2.00 元 / 1M | 6.00 元 / 1M |

V4 Pro is ~3x more expensive than V4 Flash at every tier.

## Real cost data (from Hermes sessions DB)

Over 31 days (May 17 – Jun 16, 2026), a user's actual cost breakdown:

| Model | Sessions | Est. Cost USD | Effective $/session |
|---|---|---|---|
| deepseek-v4-pro | 10 | $16.60 | $1.66 |
| Qwen3.6-35B-A3B (local) | 198 | $0.69 | $0.003 |
| deepseek-chat (→v4-flash alias) | 70 | $0.005 | $0.00007 |
| deepseek-v4-flash | 22 | $0.00* | — |
| qwen-35-9b (local) | 26 | $0.00 | $0.00 |

*\*Estimated cost for v4-flash may show $0 due to Hermes not pricing custom providers.*

**Key finding: v4-Pro was 10% of API sessions but drove ~99.9% of API cost.**  
The user ran 10 v4-Pro sessions at $1.66/session vs 92 v4-Flash sessions at near-zero cost.

## When to recommend each tier

| Use case | Recommended tier | Rationale |
|---|---|---|
| Daily coding, simple agents | V4 Flash | Cheap enough to leave running. 13B active parameters handle most agent tasks. |
| Complex reasoning, heavy refactoring | V4 Pro | 49B active params. Use sparingly — cost adds up fast. |
| Prototyping / testing | V4 Flash | Iterate cheaply, switch to Pro for the final run. |
| Long-context work (up to 1M) | Both | Both support 1M context. Pro for quality, Flash for cost. |

## Cost control strategies

- **Use v4-Flash as default, v4-Pro only for hard problems.** This single change
  can reduce API spend from ~$10/day to ~$0.50/day.
- **Cache-aware prompting.** System prompts, tool definitions, and large context
  documents trigger cache hits (0.02 元/1M for Flash). Structure requests to
  maximize reuse.
- **Check Hermes sessions table** before assuming costs. In one real trace, the
  user thought their daily cost was ~6.6元 (v4-flash). The actual $10.11 day was
  driven entirely by v4-Pro sessions they weren't tracking separately.
