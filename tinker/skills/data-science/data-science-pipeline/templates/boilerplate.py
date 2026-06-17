#!/usr/bin/env python3
"""Boilerplate: SQLite → Plotly HTML chart (zero dependencies).

Copy this, modify the SQL query, trace builder, and layout config.
"""
import sqlite3, json
from collections import defaultdict

DB = "data.db"
OUT = "chart.html"

# ── 1. Query ────────────────────────────────────────────────────────
conn = sqlite3.connect(DB)
rows = conn.execute("""
    SELECT category, x_val, y_val
    FROM some_table
    ORDER BY category, x_val
""").fetchall()
conn.close()

# ── 2. Pivot into per-series arrays ──────────────────────────────────
data = defaultdict(lambda: {"x": [], "y": []})
for cat, x, y in rows:
    data[cat]["x"].append(x)
    data[cat]["y"].append(y)

# ── 3. Build traces dicts ────────────────────────────────────────────
COLORS = {"A": "#198754", "B": "#0d6efd", "C": "#dc3545"}

traces = []
for cat, d in data.items():
    traces.append({
        "type": "scatter",
        "name": cat,
        "x": d["x"],
        "y": d["y"],
        "mode": "lines+markers",
        "line": {"color": COLORS.get(cat, "#999"), "width": 2.5},
        "marker": {"size": 5},
        "hovertemplate": f"<b>{cat}</b><br>%{{x}}<br>%{{y:,.2f}}<extra></extra>",
        "showlegend": True,
    })

# ── 4. Layout ────────────────────────────────────────────────────────
layout = {
    "title": {"text": "Chart Title", "font": {"size": 20}},
    "template": "plotly_white",
    "hovermode": "x unified",
    "height": 600,
    "margin": {"l": 80, "r": 30, "t": 60, "b": 40},
    "xaxis": {"title": "X Axis", "type": "category", "tickangle": -45, "nticks": 20},
    "yaxis": {"title": "£", "tickformat": ",.0f"},
}

# ── 5. Generate HTML ─────────────────────────────────────────────────
height = layout["height"]
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Chart</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         margin: 20px; background: #f8f9fa; }}
  #chart {{ width: 100%; height: {height}px; }}
</style>
</head>
<body>
<div id="chart"></div>
<script>
var data = {json.dumps(traces)};
var layout = {json.dumps(layout)};
Plotly.newPlot("chart", data, layout, {{ responsive: true }});
</script>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(html)
print(f"Written: {OUT}")
