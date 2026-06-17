#!/usr/bin/env python3
"""Example: Combined stacked-bar chart from SQLite — income vs expense across accounts.

Shows the pattern of income bars above zero (stacked by account), expense bars
below zero (negated, stacked by account), and a total net line through the middle.
Pure stdlib + Plotly CDN.
"""
import sqlite3, json
from collections import defaultdict

DB = "finance.db"
OUT = "viz_combined.html"

ACCOUNTS = ["Barclays", "HSBC"]
COLORS = {"Barclays": "#198754", "HSBC": "#0d6efd"}

conn = sqlite3.connect(DB)
rows = conn.execute("""
    SELECT account, strftime('%Y-%m', date) AS month,
           ROUND(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 2) AS income,
           ROUND(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 2) AS expense,
           ROUND(SUM(amount), 2) AS net
    FROM v_combined
    WHERE account IN ({})
    GROUP BY account, month ORDER BY month, account
""".format(",".join("?" for _ in ACCOUNTS)), ACCOUNTS).fetchall()
conn.close()

all_months = sorted(set(r[1] for r in rows))

by_acct = defaultdict(lambda: defaultdict(lambda: {"income": 0, "expense": 0, "net": 0}))
for acct, month, inc, exp, net in rows:
    by_acct[acct][month] = {"income": inc, "expense": exp, "net": net}

traces = []
total_net = []

# Income bars (stacked above zero)
for acct in ACCOUNTS:
    d = by_acct[acct]
    traces.append({
        "type": "bar", "name": acct,
        "x": all_months,
        "y": [d[m]["income"] for m in all_months],
        "marker": {"color": COLORS.get(acct, "#999"), "opacity": 0.85},
        "hovertemplate": f"<b>{acct} income</b><br>%{{x}}<br>£%{{y:,.2f}}<extra></extra>",
        "legendgroup": "income",
        "legendgrouptitle": {"text": "Income"},
    })

# Expense bars (stacked below zero — negate the positive values from SQL)
for acct in ACCOUNTS:
    d = by_acct[acct]
    traces.append({
        "type": "bar", "name": acct,
        "x": all_months,
        "y": [-d[m]["expense"] for m in all_months],  # negate for below-zero
        "marker": {"color": COLORS.get(acct, "#999"), "opacity": 0.4},
        "hovertemplate": f"<b>{acct} expense</b><br>%{{x}}<br>£%{{y:,.2f}}<extra></extra>",
        "legendgroup": "expense",
        "legendgrouptitle": {"text": "Expense"},
        "showlegend": False,
    })

# Net line overlay
for m in all_months:
    total_net.append(sum(by_acct[a][m]["net"] for a in ACCOUNTS))

traces.append({
    "type": "scatter", "name": "Net total",
    "x": all_months, "y": total_net,
    "mode": "lines+markers",
    "line": {"color": "#212529", "width": 2.5},
    "marker": {"size": 5, "color": "#212529"},
    "hovertemplate": "<b>Net total</b><br>%{x}<br>£%{y:,.2f}<extra></extra>",
    "showlegend": True,
})

layout = {
    "title": {"text": "Combined Monthly Balance", "font": {"size": 20}},
    "barmode": "stack",
    "template": "plotly_white",
    "hovermode": "x unified",
    "height": 550,
    "margin": {"l": 80, "r": 40, "t": 60, "b": 80},
    "xaxis": {"type": "category", "tickangle": -45, "nticks": 30},
    "yaxis": {"title": "£", "tickformat": ",.0f"},
    "legend": {
        "orientation": "v",
        "yanchor": "top", "y": 0.98,
        "xanchor": "left", "x": 1.01,
    },
    "shapes": [{
        "type": "line", "xref": "paper", "yref": "y",
        "x0": 0, "x1": 1, "y0": 0, "y1": 0,
        "line": {"dash": "dot", "color": "#999", "width": 0.8},
    }],
}

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><title>Combined Balance</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         margin: 20px; background: #f8f9fa; }}
  #chart {{ width: 100%; height: 550px; }}
</style>
</head>
<body>
<div id="chart"></div>
<script>
Plotly.newPlot("chart", {json.dumps(traces)}, {json.dumps(layout)}, {{responsive: true}});
</script>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(html)
print(f"Written: {OUT}")
