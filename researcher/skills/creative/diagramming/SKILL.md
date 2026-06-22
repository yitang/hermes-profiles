---
name: diagramming
description: "Create architectural and conceptual diagrams: dark-themed SVG/HTML architecture diagrams (inline SVG, no deps) and hand-drawn Excalidraw JSON diagrams (drag-and-drop onto excalidraw.com)."
version: 1.0.0
author: Hermes Agent (consolidated from architecture-diagram + excalidraw)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Diagrams, Architecture, Visualization, SVG, Excalidraw, Flowcharts, Infrastructure]
    related_skills: [sketch, ascii]
---

# Diagramming — Architecture & Conceptual Diagrams

Two diagramming approaches, chosen by style and audience:

| Approach | Style | Best For | Output |
|----------|-------|----------|--------|
| **Architecture Diagram** | Dark-themed, polished SVG | Cloud/infra architecture, system design docs | Standalone HTML file with inline SVG |
| **Excalidraw** | Hand-drawn, sketch-like | Flowcharts, wireframes, conceptual diagrams | `.excalidraw` JSON (drag-drop onto excalidraw.com) |

## 1. Architecture Diagrams (Dark SVG/HTML)

Generate professional, dark-themed technical architecture diagrams as standalone HTML files with inline SVG. No external tools, no API keys — just write the HTML file and open it in a browser.

See `templates/template.html` for a starter template and `references/architecture.md` for detailed element types and layout strategies.

## 2. Excalidraw Diagrams (Hand-Drawn JSON)

Create diagrams by writing standard Excalidraw element JSON and saving as `.excalidraw` files. Drag-and-drop onto [excalidraw.com](https://excalidraw.com) for viewing and editing.

See `references/excalidraw.md` for the full element reference, color palette, and dark mode setup.

## Quick Decision

- **Team doc / presentation** → Architecture Diagram (SVG/HTML, self-contained)
- **Whiteboard / brainstorming** → Excalidraw (hand-drawn look, easily editable)
- **Both** → Create both: architecture diagram for the final doc, excalidraw for the exploration phase
