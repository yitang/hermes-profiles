# DeepSeek V4 Pricing

Official pricing from DeepSeek API Docs. Updated as of June 2026.

## Official sources

- Chinese (RMB): https://api-docs.deepseek.com/zh-cn/quick_start/pricing
- Multi-provider comparison: https://pricepertoken.com/pricing-page/provider/deepseek
- Release notes: https://api-docs.deepseek.com/news/news260424

## DeepSeek V4 Flash

284B total parameters, 13B active. 1M context, 384K max output.

### RMB pricing (official, Chinese mainland users)

| Category | Price / 1M tokens |
|---|---|
| Input (cache hit) | 0.02 元 |
| Input (cache miss) | 1.00 元 |
| Output | 2.00 元 |

### USD pricing (official, rest of world)

| Category | Price / 1M tokens |
|---|---|
| Input (cache hit) | $0.0028 |
| Input (cache miss) | $0.098 |
| Output | $0.197 |

Note: these are DeepSeek's own API prices. Third-party providers (OpenRouter, Fireworks, DeepInfra, etc.) may add their own markup or discount.

## DeepSeek V4 Pro

1.6T total parameters, 49B active. 1M context.

| Category | Price / 1M tokens (RMB) | Price / 1M tokens (USD) |
|---|---|---|
| Input (cache hit) | 0.025 元 | $0.0036 |
| Input (cache miss) | 3.00 元 | $0.435 |
| Output | 6.00 元 | $0.870 |

## Real-world example

Heavy daily coding-agent usage:

| Metric | Value |
|---|---|
| Cache hit input | 100M tokens |
| Cache miss input | 3M tokens |
| Output | 700K tokens |
| **Total RMB** | ~6.4 元 |
| **Total USD** | ~$0.90 |

## Model retirement note

`deepseek-chat` and `deepseek-reasoner` model names retire 2026-07-24. Migrate to `deepseek-v4-flash` (non-thinking maps to deepseek-chat; thinking mode = deepseek-reasoner).
