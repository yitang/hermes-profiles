# OSM Overpass API — Spike Reference

Quick-reference for querying OpenStreetMap data via the Overpass API in spikes.

## Endpoint

```
POST https://overpass-api.de/api/interpreter
Content-Type: application/x-www-form-urlencoded
```

Query is passed as `data` parameter (URL-encoded Overpass QL).

## Rate Limiting

- **1 req/sec** is safe for 5-10 query bursts
- **3s breather** every 5 queries avoids 429s
- After a 429 response, wait **60s** before retrying
- Use a meaningful `User-Agent` header (e.g. `MyAppSpike/1.0`)

## Basic Query Template (Python)

```python
import urllib.request, urllib.parse, json

query = f"""
[out:json][timeout:15];
(
  way(around:{radius_m},{lat},{lon})["key"];
  node(around:{radius_m},{lat},{lon})["key"];
);
out body;
"""

data = urllib.parse.urlencode({"data": query}).encode()
req = urllib.request.Request(
    "https://overpass-api.de/api/interpreter",
    data=data,
    headers={"User-Agent": "ParkWiseSpike/1.0"}
)
with urllib.request.urlopen(req, timeout=20) as resp:
    result = json.loads(resp.read().decode())
```

## UK Parking Tags

UK on-street parking restrictions use a specific tagging scheme:

| Tag pattern | Example value | Meaning |
|-------------|---------------|---------|
| `parking:condition:left/right/both` | `ticket` / `residents` / `loading` / `disabled` / `free` / `no_stopping` / `no_parking` | Primary restriction type |
| `parking:condition:left/right/both:default` | `ticket` | Default restriction when time conditions don't apply |
| `parking:condition:left/right/both:time_interval` | `Mo-Fr 08:00-18:30` | When the restriction is active |
| `parking:condition:left/right/both:maxstay` | `2 hours` | Maximum parking duration |
| `parking:condition:left/right/both:vehicle` | `residents` | Vehicle type restriction |
| `parking:left/right/both` | `lane` / `street_side` / `no_parking` | Physical parking lane type |
| `parking:lane:left/right/both` | `parking_lane` | Whether it's a marked lane |
| `maxstay` | `2 hours` | Global max stay for the way |
| `fee` | `yes` / `no` | Whether parking is paid |

### UK-Specific Overpass Query

```python
query = f"""
[out:json][timeout:15];
(
  way(around:{radius_m},{lat},{lon})["highway"]["parking:left"];
  way(around:{radius_m},{lat},{lon})["highway"]["parking:right"];
  way(around:{radius_m},{lat},{lon})["highway"]["parking:condition:left"];
  way(around:{radius_m},{lat},{lon})["highway"]["parking:condition:right"];
  way(around:{radius_m},{lat},{lon})["highway"]["parking:condition:both"];
  node(around:{radius_m},{lat},{lon})["amenity"="parking"];
  way(around:{radius_m},{lat},{lon})["amenity"="parking"];
);
out body;
"""
```

## Important Notes

- **OSM coverage is inconsistent.** Some UK boroughs have excellent parking tagging; others have none. The D-TRO (Digital Traffic Regulation Order) mandate is gradually improving coverage as councils publish machine-readable data.
- **parking:condition:* is the primary UK tagging scheme**, not parking:restriction:*. The condition tags carry the actual restriction data; the base parking:left/right/both just describes the physical lane type.
- **search radius of 100m** is a good default for curbside parking queries
- **HERE On-Street Parking API** is OEM-only (automotive manufacturers) — not viable for consumer apps
- **AppyWay Kerbside** covers 500+ UK towns but requires commercial partnership
