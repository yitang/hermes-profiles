# Collector Script Pattern — X API Monitoring

Captured from a real session: building a read-only X data collector for investment signal tracking with Hermes cron (2026-06-21).

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth method | Bearer token (not OAuth 1.0a/2.0) | OAuth 2.0 callback URL rejected by portal; OAuth 1.0a gave "Something went wrong" on X's side. Bearer token worked immediately. |
| CLI | curl (not xurl) | xurl auth was unreliable for this user; the `--bearer-token` flag was missing in their version. curl is simpler and always available. |
| Token storage | config.yaml (file on disk) | Not hardcoded in script. User edits config.yaml once, script reads it. Warn about .gitignore. |
| State tracking | JSON file with `since_id` per handle | Only fetch new posts. X API deduplicates within 24h UTC. No need for a database. |
| Handle → ID resolution | Cache in state.json | `/2/users/by/username/{handle}` costs $0.01/call. Resolve once, reuse forever. |

## The Script (Python)

```python
#!/usr/bin/env python3
"""X Investment Signal Collector - no_agent cron mode"""
import json, os, subprocess, yaml
from datetime import datetime, timezone

BASE = os.path.expanduser("~/.hermes/scripts/x-investment")
CONFIG = os.path.join(BASE, "config.yaml")
STATE = os.path.join(BASE, "state.json")
DAILY = os.path.join(BASE, "daily")

os.makedirs(DAILY, exist_ok=True)

with open(CONFIG) as f:
    config = yaml.safe_load(f)

token = config["bearer_token"]
users = config["tracked_users"]
portfolio = config["portfolio"]
auth_header = f"Authorization: Bearer {token}"

state = {"seen_ids": {}, "user_ids": {}}
if os.path.exists(STATE):
    with open(STATE) as f:
        state = json.load(f)

seen_ids = state.get("seen_ids", {})
user_ids = state.get("user_ids", {})
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
new_posts = []

for user in users:
    handle = user["handle"].lstrip("@")

    # Resolve handle -> user ID (cached after first run)
    if handle not in user_ids:
        r = subprocess.run(
            ["curl", "-s", f"https://api.x.com/2/users/by/username/{handle}",
             "-H", auth_header],
            capture_output=True, text=True, timeout=15)
        data = json.loads(r.stdout)
        if "data" not in data:
            continue
        user_ids[handle] = data["data"]["id"]

    uid = user_ids[handle]

    # Fetch recent posts, only new ones since last run
    url = f"https://api.x.com/2/users/{uid}/tweets?max_results=5&tweet.fields=created_at,public_metrics,entities"
    if handle in seen_ids:
        url += f"&since_id={seen_ids[handle]}"

    r = subprocess.run(
        ["curl", "-s", url, "-H", auth_header],
        capture_output=True, text=True, timeout=15)
    data = json.loads(r.stdout)
    posts = data.get("data", [])
    if not posts:
        continue

    # Track newest post ID for next run
    max_id = max(int(p["id"]) for p in posts)
    seen_ids[handle] = str(max_id)

    for p in posts:
        entities = p.get("entities", {})
        cashtags = [c["tag"] for c in entities.get("cashtags", [])]
        new_posts.append({
            "user": handle,
            "label": user["label"],
            "id": p["id"],
            "text": p["text"],
            "created": p.get("created_at", ""),
            "cashtags": cashtags,
            "url": f"https://x.com/{handle}/status/{p['id']}"
        })

# Save state
state["seen_ids"] = seen_ids
state["user_ids"] = user_ids
with open(STATE, "w") as f:
    json.dump(state, f, indent=2)

# Output JSON if posts found, nothing if silent
if new_posts:
    daily_file = os.path.join(DAILY, f"{today}.json")
    with open(daily_file, "w") as f:
        json.dump({"date": today, "posts": new_posts}, f, indent=2)

    output = {
        "date": today,
        "posts": new_posts,
        "portfolio": {k: v for k, v in portfolio.get("tickers", {}).items()}
    }
    print(json.dumps(output, indent=2))
```

## config.yaml Template

```yaml
bearer_token: "YOUR_BEARER_TOKEN"

tracked_users:
  - handle: "username"
    label: "Display Name"
    focus: ["sector1", "sector2"]

portfolio:
  tickers:
    TICKER:
      aliases: ["TICKER", "$TICKER", "Full Name"]
      sector: "sector"
      weight: "core holding"
```

## Cron Job Setup

```bash
# Job A: data collector (no_agent, runs at 7am)
hermes cron create "0 7 * * *" \
  --no-agent \
  --script x-investment/collect.py \
  --name "x-signal-collect" \
  --deliver local

# Job B: agent briefing (runs at 8am, chained to Job A)
hermes cron create "0 8 * * *" \
  --context-from <job_a_id> \
  --prompt "..." \
  --name "x-morning-briefing" \
  --deliver telegram
```

## Error States Encountered

| API Response | Meaning | Fix |
|--------------|---------|-----|
| `CreditsDepleted` | No balance | Buy credits in Developer Console |
| `Unauthorized` (401) | After buying credits | App may have reset; check Production mode or regen token |
| `Something went wrong` on OAuth | Wrong app type or callback URL | Use bearer token instead |
| curl works, xurl auth fails | xurl version/flag mismatch | Use curl — simpler for read-only |
