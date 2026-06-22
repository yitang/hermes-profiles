---
name: x-api-monitoring
description: "Set up read-only X API data collection pipelined into Hermes cron for automated monitoring — portfolio-aware signal tracking, user timeline scraping, and config-driven briefing generation. Covers registration pitfalls, bearer-token auth, the no_agent collector script pattern with since_id state tracking, and cost modeling."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [curl, python3]
  pip_packages: [pyyaml]
metadata:
  hermes:
    tags: [x, twitter, social-media-monitoring, cron, data-collection, api, investment]
    related_skills: [xurl, cronjob, iterative-research]
    homepage: ~
---

# x-api-monitoring — X API Read-Only Data Pipelines with Hermes Cron

Design and deploy a Hermes cron job that collects posts from a curated list of X accounts on a schedule, cross-references them against a configuration (portfolio watchlist, topic filters, etc.), and delivers a daily briefing — all via the X API pay-per-use model.

## When to Use

- User wants to track specific X accounts and get summaries/reports on a schedule
- The goal is monitoring/reading only — no posting, replying, or engagement
- The workload is low-volume (5-20 accounts, <200 reads/day) — fits X API pay-per-use
- User needs the pattern integrated with Hermes cron for automated delivery

Do NOT use for: high-volume scraping, training data collection, or any use case that would exceed 2M reads/month (X's hard cap).

## Architecture

Two-job chain:

```
 Job A: collect.py (no_agent, LLM-free)     Job B: Hermes agent
 ┌─────────────────────────────────┐         ┌─────────────────────┐
 │ xurl/curl fetches user posts    │ context │ reads collected      │
 │ stores last-seen ID per user    │────────>│ posts + config       │
 │ outputs JSON (empty=silent)     │         │ cross-refs filters   │
 │ cost: ~$0.26/day X API only     │         │ generates briefing   │
 └─────────────────────────────────┘         │ delivers to platform │
                                              └─────────────────────┘
```

**Why two jobs:** The no_agent collector costs zero LLM tokens per tick. The agent only fires when there's data. If collector output is empty, the agent prompt says `[SILENT]` and nothing is sent.

## Setup Sequence

### Phase 1: Register X API App (user does this — involves secrets)

Walk the user through:

1. Go to [developer.x.com](https://developer.x.com/en/portal/dashboard) → create Project + App
2. **App type**: MUST set to `Web App, Automated App or Bot` (NOT Native App)
3. **Redirect URI** (for OAuth 2.0): `http://localhost:8080/callback`
4. Copy **Client ID + Client Secret** (OAuth 2.0) OR **Consumer Key + Consumer Secret** (OAuth 1.0a) OR **Bearer Token** (app-only, simplest for read-only)

For the **use case / app description** field, recommend the user write:

```
Personal investment research assistant. Reads posts from a small curated list of public accounts. Cross-references against personal portfolio watchlist. Read-only, single-user, non-commercial. ~50-100 reads/day, ~1,500-3,000/month.
```

The review cares about: honesty, small scale, read-only, no data resale.

5. Buy credits (minimum ~$5-10) under **Billing** in the sidebar

### Phase 2: Choose Auth Method

| Method | When to Use | Auth Command |
|--------|-------------|--------------|
| **Bearer Token** (recommended) | Read-only, simplest setup. Works when OAuth callback URLs fail. | `xurl auth bearer` or use curl directly |
| **OAuth 2.0** | Need user context (posting, following, DMs). Auto-refreshes. | `xurl auth oauth2 --app my-app` then browser flow |
| **OAuth 1.0a** | Fallback if OAuth 2.0 callback URL isn't accepted by the portal. | `xurl auth apps add my-app --consumer-key X --consumer-secret Y` then `xurl auth oauth1` |

### Phase 3: The Collector Script Pattern

Create a Python script that:

1. Reads a `config.yaml` with bearer token + tracked users + portfolio/filters
2. Reads `state.json` tracking `last_seen_id` per user handle
3. For each user:
   - Resolve handle → user ID via `/2/users/by/username/{handle}` (cache in state)
   - Fetch posts via `/2/users/{id}/tweets?max_results=5&since_id={last_seen}&tweet.fields=created_at,entities,public_metrics`
   - Update `last_seen_id` to newest post ID
4. Output JSON to stdout (non-empty = posts found; empty = silent tick — no delivery)

**Key API endpoint** [citation:X API Get Posts](https://docs.x.com/x-api/users/get-posts):

```
GET /2/users/{id}/tweets?max_results=N&since_id={last_id}&tweet.fields=created_at,public_metrics,entities
```

**Important fields:**
- `tweet.fields=entities` — enables cashtag extraction (`$NVDA`, `$TSLA`)
- `since_id` — only fetch posts newer than this (saves API costs, deduped)
- `max_results` — 5-10 per user is sufficient for daily monitoring

**Bearer token safety**: Store in `config.yaml`, never hardcoded in the script. If the user pastes their token into the chat, tell them to **immediately regenerate it** in the developer portal.

### Phase 4: Create the Cron Jobs

Two cron jobs in Hermes:

**Job A (data collector)** — no_agent mode, runs before the briefing:
```
hermes cron create "0 7 * * *" \
  --no-agent \
  --script x-investment/collect.py \
  --name "x-signal-collect" \
  --deliver local
```

**Job B (agent briefing)** — runs after, reads Job A's output:
```
hermes cron create "0 8 * * *" \
  --context-from <job_a_id> \
  --prompt "<briefing prompt>" \
  --name "x-morning-briefing" \
  --deliver telegram
```

Prompt pattern for Job B (self-contained, no memory of past runs):

```
You are an investment signal analyst. Below is today's collected X posts
from tracked users.

TRACKED USERS:
<from config>

PORTFOLIO:
<from config>

TODAY'S POSTS:
<script_output>  {injected via context_from}

For each post mentioning a tracked ticker, produce:
🟢 BULLISH | 🟡 NEUTRAL | 🔴 BEARISH
$TICKER — by @user
Summary: <one-line takeaway>
Context: <why this matters>

If nothing matched, respond with: [SILENT]
```

### Phase 5: File Layout

```
~/.hermes/scripts/x-investment/
├── config.yaml       # bearer_token + tracked_users + portfolio (user edits)
├── state.json         # auto-managed: last_seen_ids + user_ids cache
├── collect.py         # data collector script
└── daily/             # optional: raw daily dumps for review
```

## Cost Modeling

X API pay-per-use pricing (default for new signups as of 2026) [citation:Postproxy Pricing](https://postproxy.dev/blog/x-api-pricing-2026):

| Resource | Unit Cost | 10 users × 5 posts/day | Monthly |
|----------|-----------|------------------------|---------|
| Post read | $0.005 | 50/day | $7.50 |
| User lookup | $0.01 | ~1/day (cached) | $0.30 |
| **X API total** | | $0.26/day | **~$7.80/mo** |
| LLM (agent cron, DeepSeek/Sonnet) | ~$0.005/run | 1/day | ~$0.15/mo |
| **Grand total** | | | **~$8/mo** |

Cap: 2M reads/month hard limit (X's ceiling — far above this use case).

**Savings mechanisms:**
- `since_id` — only pay for new posts, never re-read old ones
- X deduplicates same-post reads within 24h UTC window
- Silent ticks (empty output) cost $0 in LLM tokens

## Pitfalls

- **Bearer token in chat** — if the user pastes their token, tell them to regenerate it immediately. This happened in a real session and the fix is rotate-in-portal.
- **OAuth 2.0 callback URL rejected** — if the portal won't accept `http://localhost:8080/callback`, switch to OAuth 1.0a or bearer token approach
- **"CreditsDepleted"** error after first successful call — means auth works but user needs to top up credits in Billing
- **401 after buying credits** — check app is in "Production" mode, not Sandbox; if credentials changed during billing setup, re-auth
- **"Something went wrong"** on OAuth browser flow — usually wrong app type (must be "Web App" not "Native App") or callback URL mismatch
- **xurl `--bearer-token` flag missing** — older xurl versions don't support it. Use `xurl auth bearer` (interactive prompt) or curl directly
- **config.yaml has the token** — instruct the user to keep this file out of version control (`.gitignore` it)
- **Cron prompts must be self-contained** — the agent has zero memory across runs. Put the portfolio list and formatting instructions directly in the prompt

## Related Skills

- `xurl` (bundled, hub-installed) — CLI tool for the X API; this skill covers the monitoring workflow around it
- `cronjob` — Hermes cron tool; this skill covers the specific cron setup for X data pipelines
- `iterative-research` — use for scoping the user's monitoring requirements before building

## Reference Files

- `references/collector-script-pattern.md` — full Python collector script with state tracking, curl calls, and JSON output format
