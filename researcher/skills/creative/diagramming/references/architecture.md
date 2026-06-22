# Architecture Diagrams (Dark SVG/HTML)

Generate professional, dark-themed technical architecture diagrams as standalone HTML files with inline SVG. No external tools, no API keys.

## Core Pattern

Write a self-contained HTML file with inline SVG. The `templates/template.html` provides a complete starter with:
- Dark theme (JetBrains Mono font, `#020617` background)
- Grid background, arrow markers
- Color-coded component types
- Info cards for metadata

## Element Types

| Type | Fill | Stroke | Opacity | Use For |
|------|------|--------|---------|---------|
| Frontend | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan) | 0.4 | React/Vue apps, browser, mobile |
| Backend | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald) | 0.4 | API servers, services |
| Cloud Service | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber) | 0.3 | AWS/GCP/Azure services |
| Database | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet) | 0.4 | PostgreSQL, Redis, etc. |
| Security | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose) | 0.4 | Auth providers, firewalls |

## SVG Building Blocks

```svg
<!-- Box component -->
<rect x="100" y="200" width="110" height="50" rx="6"
      fill="rgba(8, 51, 68, 0.4)" stroke="#22d3ee" stroke-width="1.5"/>
<text x="155" y="220" fill="white" font-size="11" font-weight="600" text-anchor="middle">Label</text>
<text x="155" y="236" fill="#94a3b8" font-size="9" text-anchor="middle">Subtitle</text>

<!-- Arrow -->
<line x1="210" y1="225" x2="260" y2="225" stroke="#22d3ee"
      stroke-width="1.5" marker-end="url(#arrowhead)"/>

<!-- Dashed boundary (region/security group) -->
<rect x="180" y="80" width="600" height="300" rx="12"
      fill="rgba(251, 191, 36, 0.05)" stroke="#fbbf24"
      stroke-width="1" stroke-dasharray="8,4"/>
<text x="192" y="98" fill="#fbbf24" font-size="10" font-weight="600">Region / Boundary</text>

<!-- Curved path -->
<path d="M 80 140 L 80 200 Q 80 220 100 220 L 200 220 Q 220 220 220 240 L 220 278"
      fill="none" stroke="#fb7185" stroke-width="1.5" stroke-dasharray="5,5"/>

<!-- Multi-line component -->
<rect x="200" y="380" width="110" height="100" rx="6"
      fill="rgba(120, 53, 15, 0.3)" stroke="#fbbf24" stroke-width="1.5"/>
<text x="255" y="400" fill="white" font-size="11" font-weight="600" text-anchor="middle">S3 Buckets</text>
<text x="255" y="420" fill="#94a3b8" font-size="8" text-anchor="middle">• bucket-one</text>
<text x="255" y="434" fill="#94a3b8" font-size="8" text-anchor="middle">• bucket-two</text>
```

## Layout Strategy

1. **Top-down or left-right flow** depending on data direction
2. **Region boundaries** as dashed rectangles with `fill: rgba(<color>, 0.05)`
3. **200px spacing** between nodes horizontally, 100px vertically
4. **Legend in bottom-right or top-right corner**

## Verification

Open the `.html` file in any browser. Check:
- All labels visible (text fits inside boxes)
- Arrows connect properly (x2 vs x1 match)
- No overlapping elements
- Legend matches the components used
