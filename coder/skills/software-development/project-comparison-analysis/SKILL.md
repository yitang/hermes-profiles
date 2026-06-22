---
name: project-comparison-analysis
description: "Systematically compare two or more projects/codebases — architecture, features, code patterns, styling philosophy, and origin. Produces a structured cross-project comparison report."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [comparison, analysis, codebase, audit, review]
    related_skills: [codebase-inspection, consulting-analysis]
---

# Project Comparison Analysis

Systematic methodology for comparing two or more projects side by side. Use when the user asks to "compare", "contrast", "analyse differences between", or "which one should I keep/merge" for two or more directories or repos.

## When to Use

- User asks to compare two projects or directories
- User is deciding which of two implementations to keep/merge
- User wants to understand how two projects differ structurally
- Post-mortem: understanding why two implementations of the same concept diverged

## Methodology

### Phase 1: Discover the Relationship

Before doing any detailed comparison, **establish the relationship between the projects**. Do NOT assume shared origin just because they share a spec file or directory name.

| Question | How to check |
|---|---|
| Do they share the same spec? | Compare spec/docs files byte-for-byte |
| Do they share the same plan? | Compare implementation plan files |
| Was one built from the other? | Check git history, commit messages |
| Do they have independent origins? | Check different research docs, bug reports, timestamps |
| Does one predate the other? | Check git log, file timestamps, tech stack versioning |

**⚠️ Pitfall:** Identical spec files do NOT mean identical origins. A spec may have been retroactively added to an older project to document it. Verify by checking:
- Does the plan's file structure match the actual code structure?
- Do research/docs describe project A's features or project B's?
- Which project has bug reports referencing its code?

### Phase 2: Structural Scan

Map the directory tree of each project:

```bash
find /path/to/project -not -path '*/.git/*' -not -path '*/__pycache__/*' \
  -not -path '*.egg-info/*' -not -name '*.pyc' | sort
```

Answer these structural questions:

| Dimension | What to look for |
|---|---|
| Package layout | Monorepo vs single package? How many packages? |
| Top-level dirs | What lives at root level? (docs/, src/, tests/, scripts/) |
| Template structure | How are templates organised? Flat vs subdirs? |
| Static assets | CSS in separate file or inline? Framework used (Bootstrap/Tailwind/custom)? |
| Test structure | Tests alongside code or in separate dir? Co-located or centralised? |

### Phase 3: Architecture & Tech Stack

Compare across:

| Aspect | Examples to note |
|---|---|
| DB layer | Sync vs async SQLAlchemy? Raw SQL? ORM pattern? |
| Auth | Cookie session vs token vs none? Provider/library? |
| Frontend framework | Bootstrap 5 / Tailwind / custom CSS / CDN-only |
| JS libraries | HTMX version, Alpine.js, Chart.js usage patterns — conservative or bleeding edge? |
| Async pattern | async/await in routes? sync only? |
| Model layer | Pydantic vs dataclasses vs raw SQLAlchemy? Enums (StrEnum vs Python Enum)? |

### Phase 4: Feature Inventory

Create a feature matrix. Read the actual route handlers and templates, not just file names:

```markdown
| Feature | Project A | Project B |
|---|---|---|
| Dashboard | ... | ... |
| Auth | Yes (cookie) | No |
| Reports | Chart.js line (monthly cashflow) | 4 dedicated report types |
| Budget | Basic form | Model + progress bars |
```

**Check for ghost features** — items in a sidebar nav that don't have a working route.

### Phase 5: Code Pattern & Style Analysis

Read actual source files (templates, routes, models) and note:

- **HTMX usage depth**: proper hx-target swaps vs raw fetch() calls
- **Empty state handling**: dedicated empty state UI vs bare "no results" text
- **Error handling**: global interceptors vs per-route
- **Styling philosophy**: utility classes (Bootstrap) vs custom CSS with design tokens
- **Template size**: monolithic or composed from partials
- **Consistency**: are HTMX patterns the same across all routes, or are some pages using different approaches?

### Phase 6: Synthesise Comparison Report

Organise the findings into a comparison by these dimensions:

1. **Architecture split** — layout, DB, auth, static assets
2. **Features present** — side-by-side matrix
3. **Styling & UX philosophy** — visual identity, component patterns
4. **Code differences in detail** — interesting divergences in models, patterns, template approaches
5. **Origin story** — which came first, which was built from what
6. **Summary / recommendation** — which to keep, what to merge, what's worth porting

### Phase 7: Verify Before Concluding

**Always check the plan and research docs before stating the relationship between projects.** If two projects share a spec file but have radically different codebases, the spec may have been retroactively added to the older one. Verify by checking:

- Plan file structure vs actual code layout (does the plan describe project A's layout or project B's?)
- Research files (which project's features do they describe?)
- Bug reports (which codebase do they reference?)
- Git/history (commit messages, timestamps)
- Extra files unique to each project (e.g. USER_MANUAL.md in one but not the other)

## Reference Examples

- `references/pfin-comparison-2026-06-04.md` — Worked example comparing two personal finance web apps (older monorepo vs spec-built DSv4). Demonstrates all 7 phases including the origin-discovery trap.

## Pitfalls

1. **Spec identity ≠ origin identity.** Two projects can have the same spec for different reasons (one built from it, one documented by it). Always verify the relationship independently.
2. **Don't stop at the file tree.** Two projects can have the same file names but completely different implementations inside. Always read the actual template + route + model source.
3. **Don't skip the research/plan/docs directory.** These files tell the origin story — which project was built from scratch, which was documented after the fact, what features were consciously left out.
4. **Ghost nav items.** A sidebar can have links to pages that don't exist or routes that return 404. Cross-reference sidebar links against actual route registrations.
5. **Empty pfin-web packages.** A monorepo may have a web package that's scaffold-only. Don't report it as a feature difference — actually check if it has source files.
6. **HTMX consistency gap.** Some projects use HTMX for some operations and raw fetch() for others. This is a quality signal — note it when comparing frontend patterns.
