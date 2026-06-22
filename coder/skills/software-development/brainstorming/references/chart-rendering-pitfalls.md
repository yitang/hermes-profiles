# Chart Rendering Pitfalls (Discovered Post-Launch)

## Bug 1: Jinja Condition on JSON String

**Context:** `networth.html` template checked `{% if chart_data.labels %}` to conditionally show the chart. The router passed `chart_data` as `json.dumps(chart_data)` so it was a string, not a dict.

**Root cause:** Accessing `.labels` on a Python string in Jinja2 returns `undefined`/falsy regardless of content. The chart block was always hidden despite valid data in the string.

**Fix:** Pass separate `labels` and `data_values` lists from the router into the template context, and check those directly:

```python
# router
return templates.TemplateResponse(..., context={
    "chart_data": json.dumps(chart_data),   # for script tag
    "labels": labels,                        # for Jinja conditions
    "data_values": data,                     # for Jinja table rendering
})
```

```jinja
{% if labels %}
  <canvas id="networthChart"></canvas>
  {% for label in labels %}
    <td>{{ data_values[loop.index0] }}</td>
  {% endfor %}
{% endif %}
```

**Key lesson:** Never use `{% if json_string.key %}` in Jinja. Always pass raw Python objects for conditional checks and template rendering, even when you also need the JSON-serialized version for JavaScript.

---

## Bug 2: Chart.js `defer` vs Inline Script Race

**Context:** Chart.js was loaded in `<head>` with `defer`. Cashflow and spending templates had inline `<script>` tags that called `new Chart(ctx, ...)` immediately at parse time — before Chart.js had finished loading.

**Root cause:** `defer` scripts execute after HTML parsing but **before** `DOMContentLoaded`. Inline `<script>` blocks without `defer` or `async` execute **synchronously during parsing** — before deferred scripts have loaded. So `Chart` was `undefined` when the inline script ran, and the chart silently failed with no error visible to the user.

**Fix:** Wrap all chart initialization in `DOMContentLoaded`:

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('myChart').getContext('2d');
    new Chart(ctx, { ... });
});
</script>
```

**Key lesson:** Any JS library loaded with `defer` cannot be used by inline `<script>` blocks unless those blocks also wait for `DOMContentLoaded`. The net worth template already had this wrapper; cashflow and spending didn't.

---

## Bug 3: Chart.js Vertical Stretch with `maintainAspectRatio: false`

**Context:** Net worth chart had `maintainAspectRatio: false` to make it responsive. Combined with an unbounded parent container, Chart.js stretched the canvas vertically to fill unlimited space.

**Root cause:** When `maintainAspectRatio: false` and the parent container has no max-height, Chart.js overrides the inline CSS `height: 400px` and computes height from available space — which in a card layout is unconstrained.

**Fix:** Use `maintainAspectRatio: true` (default) so Chart.js preserves the aspect ratio defined by the canvas element's inline height:

```javascript
new Chart(ctx, {
    options: {
        responsive: true,
        maintainAspectRatio: true,  // respects inline height: 400px
    }
});
```

**Key lesson:** Only use `maintainAspectRatio: false` when the canvas is inside a container with an explicit max-height.

---

## Bug 4: Default Date Ranges Missing Data

**Context:** Spending report defaulted to "current month" and cashflow to "last 12 months from today". When the latest transaction was 18 months ago, both defaults showed empty charts.

**Fix:** Query the actual data range as a fallback:

```python
# If the default range has no data, shift to cover the most recent data
latest_date = await db.execute(select(func.max(Transaction.date))).scalar()
if latest_date and (end <= latest_date - timedelta(days=365) or start > latest_date):
    end = latest_date + timedelta(days=1)
    start = latest_date - timedelta(days=365)
```

Also bumped cashflow default from 12→24 months for wider coverage.

**Key lesson:** Default date ranges should be data-aware. When displaying historical data, use the actual data boundaries as a fallback rather than assuming "today" is meaningful.
