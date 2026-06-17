# Hermes Session DB Cost Schema

**File:** `~/.hermes/profiles/<profile>/state.db`

## Tables relevant to cost tracking

### `sessions` table — the primary source for token counts

| Column | Type | Populated? | Notes |
|--------|------|-----------|-------|
| `model` | TEXT | Always | Model name (e.g. `deepseek-v4-flash`, `Qwen3.6-35B-A3B`) |
| `input_tokens` | INTEGER | Usually | Total input/prompt tokens for the session |
| `output_tokens` | INTEGER | Usually | Total output/completion tokens |
| `cache_read_tokens` | INTEGER | Usually | KV cache read size — **NOT** cached prompt tokens |
| `reasoning_tokens` | INTEGER | Sometimes | Thinking/reasoning tokens (only for thinking-mode models) |
| `estimated_cost_usd` | REAL | Usually | **UNRELIABLE** — uses a generic pricing model that doesn't match actual provider billing |
| `actual_cost_usd` | REAL | Always NULL | Hermes never populates this |
| `started_at` | REAL | Always | Unix epoch timestamp (seconds since 1970) |
| `ended_at` | REAL | Usually | Session end time |

### `messages` table — individual message logs

| Column | Type | Populated? | Notes |
|--------|------|-----------|-------|
| `role` | TEXT | Always | `user`, `assistant`, `tool`, `session_meta` |
| `token_count` | INTEGER | **Always NULL** | Hermes never writes to this column despite the schema having it |
| `content` | TEXT | Always | Raw message content |
| `timestamp` | REAL | Always | Unix epoch timestamp |
| `finish_reason` | TEXT | Usually | `stop`, `tool_calls`, etc. |

## Critical warnings

- **`token_count` in `messages` table is always NULL.** Never rely on it. Use `sessions.input_tokens` / `sessions.output_tokens` instead.
- **`estimated_cost_usd` is wrong for DeepSeek.** It uses a generic provider pricing model that doesn't match DPSeek's actual per-model pricing (cache hit vs miss tiers, different models at different rates). Get real costs from the DeepSeek billing web page.
- **`actual_cost_usd` is never populated.** The field exists but Hermes doesn't write to it. It may in a future version.
- **`cache_read_tokens` is NOT cached prompt tokens.** It's KV cache size. For DeepSeek V4 Pro, this can be 432M for a session with only 1.27M input tokens. Don't divide by pricing to get cost — use the billing page instead.

## Useful queries

### Daily token usage by model

```sql
SELECT DATE(started_at, 'unixepoch') as day,
       model,
       SUM(input_tokens) as in_tok,
       SUM(output_tokens) as out_tok,
       COUNT(*) as sessions
FROM sessions
WHERE started_at >= strftime('%s', '2026-06-01')
  AND input_tokens > 0
GROUP BY day, model
ORDER BY day, model;
```

### Hourly session count (for power cross-reference)

```sql
SELECT STRFTIME('%H', started_at, 'unixepoch') as hour,
       COUNT(*) as sessions,
       SUM(input_tokens + output_tokens) as total_tokens
FROM sessions
WHERE started_at >= strftime('%s', '2026-06-15')
  AND started_at < strftime('%s', '2026-06-16')
  AND input_tokens > 0
GROUP BY hour
ORDER BY hour;
```

### Most expensive sessions

```sql
SELECT STRFTIME('%Y-%m-%d %H:%M', started_at, 'unixepoch') as ts,
       model,
       input_tokens,
       output_tokens,
       estimated_cost_usd
FROM sessions
WHERE estimated_cost_usd > 1
ORDER BY estimated_cost_usd DESC
LIMIT 20;
```
