---
name: sqlite-visualization
description: Build Plotly HTML visualizations from SQLite with zero pip dependencies — hand-rolled JSON + CDN.
---

# SQLite → Plotly Visualization (Zero Dependencies)

Generate interactive Plotly HTML charts directly from SQLite queries. No pip installs needed — build the figure dict by hand and embed Plotly via CDN `<script>` tag.

## When to use

- Need an interactive chart from SQLite data but `pip install plotly` is unavailable or undesirable
- Building faceted/multi-panel charts (subplots) from grouped query results
- Want a self-contained HTML file that works in any browser (no server)
- The project already uses this pattern (e.g., `plot_nw.py` in personal-finance-data)

## Core pattern

### 1. Query → pivot → build traces dict

```python
import sqlite3, json

conn = sqlite3.connect("finance.db")
rows = conn.execute("""
    SELECT category, x_val, y_val
    FROM data
    WHERE category IN (?, ?, ?)
    ORDER BY category, x_val
""", cats).fetchall()
conn.close()

# Pivot into per-series arrays
data = defaultdict(lambda: {"x": [], "y": []})
for cat, x, y in rows:
    data[cat]["x"].append(x)
    data[cat]["y"].append(y)

# Build trace dicts
traces = []
for cat, d in data.items():
    traces.append({
        "type": "scatter",
        "name": cat,
        "x": d["x"],
        "y": d["y"],
        "mode": "lines+markers",
        "line": {"color": COLOR_MAP.get(cat, "#999"), "width": 2},
        "hovertemplate": f"<b>{cat}</b><br>%{{x}}<br>%{{y:,.2f}}<extra></extra>",
        "showlegend": True,
    })
```

### 2. Build layout dict

```python
layout = {
    "title": {"text": "Chart Title", "font": {"size": 20}},
    "template": "plotly_white",
    "hovermode": "x unified",
    "height": 600,
    "margin": {"l": 80, "r": 30, "t": 60, "b": 40},
    "xaxis": {"title": "X Axis", "type": "category"},
    "yaxis": {"title": "£", "tickformat": ",.0f"},
}
```

### 3. Embed in HTML with CDN

```python
html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><title>Chart</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>body{{font-family:sans-serif;margin:20px;background:#f8f9fa}}
#chart{{width:100%;height:{height}px}}</style>
</head><body>
<div id="chart"></div>
<script>
Plotly.newPlot("chart", {json.dumps(traces)}, {json.dumps(layout)}, {{responsive:true}});
</script></body></html>
"""

with open("chart.html", "w") as f:
    f.write(html)
```

### 4. Faceted subplots (manual axis config)

When building multi-panel charts without `plotly.subplots.make_subplots`, configure axes manually:

```python
n = len(panels)
DOMAIN_HEIGHT = 1.0 / n

for i, name in enumerate(panels, start=1):
    suffix = "" if i == 1 else str(i)
    y0 = 1.0 - (i * DOMAIN_HEIGHT)
    y1 = 1.0 - ((i - 1) * DOMAIN_HEIGHT)

    layout[f"yaxis{suffix}"] = {
        "title": "£", "tickformat": ",.0f",
        "domain": [y0 + 0.04, y1 - 0.04],
    }
    layout[f"xaxis{suffix}"] = {
        "domain": [0.05, 0.95],
        "anchor": f"y{suffix}",
        "type": "category",  # CRITICAL for string x-values like months
        "tickangle": -45,
        "nticks": 15,
    }

    # Each trace must reference its axes:
    traces.append({
        ...,
        "xaxis": f"x{suffix}",
        "yaxis": f"y{suffix}",
    })

    # Zero reference line per panel:
    layout.setdefault("shapes", []).append({
        "type": "line",
        "xref": f"x{suffix}", "yref": f"y{suffix}",
        "x0": 0, "x1": 1, "y0": 0, "y1": 0,
        "line": {"dash": "dot", "color": "#999", "width": 0.8},
    })

    # Subplot title as annotation:
    layout.setdefault("annotations", []).append({
        "text": f"<b>{name}</b>",
        "xref": "paper", "yref": "paper",
        "x": 0.01, "y": y1 - 0.02,
        "showarrow": False,
        "font": {"size": 13},
    })
```

### 5. Two-panel layout (bars + cumulative line)

A common pattern: top panel shows monthly breakdown (stacked bars), bottom shows running cumulative. This requires sharing the same x-axis across both panels but with independent y-axes and y-domains:

```python
n = 2
DOMAIN_GAP = 0.04

layout["xaxis"] = {
    "domain": [0.05, 0.90], "anchor": "y",
    "type": "category", "showticklabels": False,  # hide on top panel
}
layout["yaxis"] = {
    "domain": [0.42, 0.95], "anchor": "x",
    "title": "Monthly £", "tickformat": ",.0f",
}
layout["xaxis2"] = {
    "domain": [0.05, 0.90], "anchor": "y2",
    "type": "category", "tickangle": -45, "nticks": 30,
}
layout["yaxis2"] = {
    "domain": [0.02, 0.38], "anchor": "x2",
    "title": "Cumulative £", "tickformat": ",.0f",
}

# Each trace references its panel: "xaxis": "x2", "yaxis": "y2"
```

Build cumulative from the same monthly data:
```python
cumulative = []
running = 0.0
for m in all_months:
    running += net_by_month[m]
    cumulative.append(round(running, 2))
```

Add a filled area to the cumulative line for visual punch:
```python
{"type": "scatter", "fill": "tozeroy",
 "fillcolor": "rgba(25,135,84,0.15)", ...}
```

Add panel titles as `layout["annotations"]` with `xref: "paper", yref: "paper"` for placement.

Complete working example: `references/two-panel-cumulative.py` — full standalone script.

## Critical pitfalls

- **String x-values get parsed as numbers**: Month strings like `"2022-01"` get auto-detected as year 2022 and the axis shows decades. Always set `"type": "category"` on x-axes when x values are date-like strings.
- **`hovermode: "x unified"` needs consistent x-axis**: Works best when all traces on a panel share the same x values. If x-arrays differ in length, hover may misalign.
- **Plotly CDN version**: Pin to a specific version (`2.35.0`) — auto-latest can break on API changes.
- **json.dumps on large arrays**: Plotly figure dicts can be large (hundreds of KB). `json.dumps` handles this fine; don't try to pretty-print or indent — it bloats the HTML.
- **`barmode: "stack"` with mixed sign data**: Stacked bars work correctly when negative = expense (red) and positive = income (green). Convert expense amounts to positive values with `ABS()` in SQL before passing to the bar trace.

### 6. Stacked area chart (assets + liabilities + net worth line)

For net worth over time: stack assets above zero (green tones) and liabilities below zero (red tones) using `stackgroup`, then overlay a bold net-worth line.

```python
# Assets as stacked areas
for acct in asset_accounts:
    traces.append({
        'type': 'scatter', 'name': acct,
        'x': months, 'y': values,
        'mode': 'lines', 'stackgroup': 'assets',
        'line': {'color': GREEN, 'width': 1},
    })

# Liabilities as stacked areas (below zero)
for acct in liability_accounts:
    traces.append({
        'type': 'scatter', 'name': acct,
        'x': months, 'y': values,  # already negative
        'mode': 'lines', 'stackgroup': 'liabilities',
        'line': {'color': RED, 'width': 1},
    })

# Net worth line overlay
traces.append({
    'type': 'scatter', 'name': 'Net Worth',
    'x': months, 'y': net_worth,
    'mode': 'lines', 'line': {'color': '#000', 'width': 3},
})

# Layout: zero reference line + horizontal legend
layout = {
    'shapes': [{'type': 'line', 'xref': 'paper', 'yref': 'y',
                'x0': 0, 'x1': 1, 'y0': 0, 'y1': 0,
                'line': {'dash': 'dot', 'color': '#999', 'width': 1}}],
    'legend': {'orientation': 'h', 'y': -0.15, 'x': 0.5},
}
```

When accounts start/end at different times, pad arrays to equal length with forward-fill for active accounts and zeros before/after inactive ones. Set `'type': 'category'` on the x-axis to prevent Plotly from parsing month strings as year numbers.
- **Staggered time series (accounts joining/leaving at different dates)**: When plotting multiple accounts over time, each trace must have the SAME array length matching the x-axis. If accounts appear or disappear mid-chart, naive pivoting produces ragged arrays → IndexError. Use the forward-fill pattern in `references/staggered-forward-fill.md` to pad every account to the full month range: 0 before first data, forward-fill within active range, 0 after account closure. Detect closure vs active accounts by comparing last-data-month to chart end date (≤ 93 days apart = still active; forward-fill to end).

## Tips

- Use `marker: {"color": "rgba(R,G,B,0.7)"}` for semi-transparent bars so the net line is visible behind them
- For dense category axes (>50 labels), set `nticks: 15` and `tickangle: -45` to keep labels readable
- Always add a zero reference line (`hline` via shapes) — it's cheap and provides instant visual orientation
- Terminal summary: print a quick stats table alongside the HTML so the user gets immediate numbers without opening the browser

## Complete working examples

See `references/combined-chart-example.py` — a complete script generating stacked-bar income/expense chart with net line overlay, directly from SQLite monthly aggregation. Copy and modify for your own queries.

See `references/forward-fill-time-series.md` — handling multi-account time series where accounts start/end at different dates. Covers forward-fill, dead-account detection, and active-account bridging.
