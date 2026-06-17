#!/usr/bin/env python3
"""Example: Two-panel chart — monthly stacked bars + cumulative net.

Top panel: income (stacked above zero) and expense (negated, stacked below zero)
per account, with total net line overlay.

Bottom panel: cumulative sum of monthly net across all accounts, with
green filled area and per-account dotted cumulative lines.

Manual axis-domain config — no plotly import needed.
"""
import sqlite3, json
from collections import defaultdict

DB = "finance.db"
OUT = "viz_two_panel.html"

ACCOUNTS = ["Barclays", "HSBC", "Lloyds"]
COLORS = {"Barclays": "#198754", "HSBC": "#0d6efd", "Lloyds": "#0dcaf0"}

# ── Query ──────────────────────────────────────────────────────────

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

# ── Pivot ──────────────────────────────────────────────────────────

all_months = sorted(set(r[1] for r in rows))
by_acct = defaultdict(lambda: defaultdict(lambda: {"income": 0, "expense": 0, "net": 0}))
for acct, month, inc, exp, net in rows:
    by_acct[acct][month] = {"income": inc, "expense": exp, "net": net}

# ── Cumulative ─────────────────────────────────────────────────────

total_net = []
cumulative = []
running = 0.0
for m in all_months:
    net_m = sum(by_acct[a][m]["net"] for a in ACCOUNTS)
    total_net.append(net_m)
    running += net_m
    cumulative.append(round(running, 2))

# ── Top panel traces: stacked bars + net line ──────────────────────

traces = []

for acct in ACCOUNTS:
    d = by_acct[acct]
    inc = [d[m]["income"] for m in all_months]
    exp = [d[m]["expense"] for m in all_months]
    c = COLORS.get(acct, "#999")

    traces.append({
        "type": "bar", "name": f"{acct}",
        "x": all_months, "y": inc,
        "marker": {"color": c, "opacity": 0.85},
        "legendgroup": "income",
        "legendgrouptitle": {"text": "Income"},
        "xaxis": "x", "yaxis": "y",
        "hovertemplate": f"<b>{acct} income</b><br>%{{x}}<br>£%{{y:,.2f}}<extra></extra>",
    })
    traces.append({
        "type": "bar", "name": f"{acct}",
        "x": all_months, "y": [-v for v in exp],
        "marker": {"color": c, "opacity": 0.4},
        "legendgroup": "expense",
        "legendgrouptitle": {"text": "Expense"},
        "showlegend": False,
        "xaxis": "x", "yaxis": "y",
        "hovertemplate": f"<b>{acct} expense</b><br>%{{x}}<br>£%{{y:,.2f}}<extra></extra>",
    })

traces.append({
    "type": "scatter", "name": "Net total",
    "x": all_months, "y": total_net,
    "mode": "lines+markers",
    "line": {"color": "#212529", "width": 2.5},
    "marker": {"size": 4, "color": "#212529"},
    "xaxis": "x", "yaxis": "y",
    "hovertemplate": "<b>Net</b><br>%{x}<br>£%{y:,.2f}<extra></extra>",
})

# ── Bottom panel traces: cumulative line + account breakdowns ──────

traces.append({
    "type": "scatter", "name": "Cumulative net",
    "x": all_months, "y": cumulative,
    "mode": "lines",
    "line": {"color": "#198754", "width": 2},
    "fill": "tozeroy",
    "fillcolor": "rgba(25,135,84,0.15)",
    "xaxis": "x2", "yaxis": "y2",
    "hovertemplate": "<b>Cumulative net</b><br>%{x}<br>£%{y:,.2f}<extra></extra>",
})

# Per-account cumulative (dotted)
for acct in ACCOUNTS:
    cum_a = []
    ra = 0.0
    for m in all_months:
        ra += by_acct[acct][m]["net"]
        cum_a.append(round(ra, 2))
    traces.append({
        "type": "scatter", "name": f"{acct} (cum.)",
        "x": all_months, "y": cum_a,
        "mode": "lines",
        "line": {"color": COLORS.get(acct, "#999"), "width": 1, "dash": "dot"},
        "opacity": 0.6,
        "showlegend": False,
        "xaxis": "x2", "yaxis": "y2",
        "hovertemplate": f"<b>{acct} cum.</b><br>%{{x}}<br>£%{{y:,.2f}}<extra></extra>",
    })

# ── Layout: two panels via manual axis domains ─────────────────────

layout = {
    "title": {"text": "Monthly Balance + Cumulative Net", "font": {"size": 20}},
    "barmode": "stack",
    "template": "plotly_white",
    "hovermode": "x unified",
    "height": 750,
    "margin": {"l": 80, "r": 40, "t": 60, "b": 80},

    "xaxis":  {"domain": [0.05, 0.90], "anchor": "y",
               "type": "category", "tickangle": -45, "nticks": 30,
               "showticklabels": False},
    "yaxis":  {"domain": [0.42, 0.95], "anchor": "x",
               "title": "Monthly £", "tickformat": ",.0f"},

    "xaxis2": {"domain": [0.05, 0.90], "anchor": "y2",
               "type": "category", "tickangle": -45, "nticks": 30},
    "yaxis2": {"domain": [0.02, 0.38], "anchor": "x2",
               "title": "Cumulative £", "tickformat": ",.0f"},

    "legend": {"orientation": "v", "yanchor": "top", "y": 1.0,
               "xanchor": "left", "x": 1.01},

    "annotations": [
        {"text": "<b>Monthly income / expense</b>",
         "xref": "paper", "yref": "paper", "x": 0.01, "y": 0.96,
         "showarrow": False, "font": {"size": 13, "color": "#333"}},
        {"text": "<b>Cumulative net cash flow</b>",
         "xref": "paper", "yref": "paper", "x": 0.01, "y": 0.40,
         "showarrow": False, "font": {"size": 13, "color": "#333"}},
    ],
    "shapes": [{
        "type": "line", "xref": "x", "yref": "y",
        "x0": 0, "x1": 1, "y0": 0, "y1": 0,
        "line": {"dash": "dot", "color": "#999", "width": 0.8},
    }],
}

# ── HTML ───────────────────────────────────────────────────────────

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><title>Two-Panel Chart</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         margin: 20px; background: #f8f9fa; }}
  #chart {{ width: 100%; height: 750px; }}
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
print(f"Written: {OUT}  ({len(all_months)} months)")
