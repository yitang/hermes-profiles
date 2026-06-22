# Worked Example: pfin Project Comparison

**Date:** 2026-06-04
**Domain:** Personal finance web apps (FastAPI + HTMX + SQLite)

## Setup

Two directories:
- `~/dev/personal-finance/`  (older, 3-package monorepo)
- `~/dev/personal-finance-hermes-dsv4/` (new, built from spec by DeepSeek V4 Flash)

## Phase 1: Origin Discovery

**What I found (and the trap I almost fell into):**

Both projects had an identical spec file at `docs/spec-2026-06-04-personal-finance-web-app.md`. Byte-for-byte identical. Easy to conclude "same spec → same origin."

**What actually happened:** When I checked the plans, the DSv4 project's plan (`plan-2026-06-04-personal-finance-web-app.md`) matched its code structure 1:1 — it described `pfinweb/` package layout, async SQLAlchemy, aiosqlite, 5 models. The older project's plan described a `pfinweb/` structure that didn't match its actual code (it had `pfin-core/`, `pfin-api/`, `pfin-web/`). The older project also had a `USER_MANUAL.md` and a `docs/2026-06-04-pfin-web-dashboard.md` (older plan) that the DSv4 didn't have. The DSv4 had research reports, bug reports, and a blind-spots analysis describing its own features in detail.

**Conclusion:** The spec was retroactively added to the older project. The DSv4 project was built **from** the spec; the older project predated the spec.

## Phase 2: Structural Scan

| Aspect | personal-finance/ | personal-finance-hermes-dsv4/ |
|---|---|---|
| Layout | 3 packages: pfin-core, pfin-api, pfin-web | Single pfinweb/ package |
| DB | Sync SQLAlchemy + separate pfin_db | Async SQLAlchemy (aiosqlite) |
| Auth | Cookie-based (auth.py, login/logout) | None |
| Static | Bootstrap 5 + FontAwesome (CDN) | Custom ~130-line CSS (no framework) |
| Tests | In-package (pfin_api/tests/) | Centralised (tests/) |
| Docs | spec, plan, dashboard plan, USER_MANUAL | spec, plan, 3 research docs, bug report |

## Phase 3: Architecture & Stack

Both use FastAPI + Jinja2 + HTMX + Alpine.js + Chart.js + SQLite. Key divergences:

- **DB pattern:** Older uses sync ORM with `Database.get()` / `Database.query()` helpers and `Session` for writes. DSv4 uses async `AsyncSession` with `await db.execute(select(...))`.
- **Auth:** Older has full cookie-session auth with `/login`, `get_optional_user`, logout. DSv4 rebuilt from scratch with no auth.
- **Static assets:** Older uses Bootstrap 5 (utility classes, modals, standard table styling). DSv4 uses custom CSS with CSS custom properties (design tokens), no framework.

## Phase 4: Feature Matrix

| Feature | Older (personal-finance/) | DSv4 (personal-finance-hermes-dsv4/) |
|---|---|---|
| Dashboard | Big stats, accounts table, spending list, Chart.js line (cashflow), portfolio | Big numbers, Chart.js pie, recent txn table |
| Accounts CRUD | Modal via inline JS + API calls | HTMX quick-add form + modal |
| Transactions | Search via JS fetch() + API, edit via HTMX modal | HTMX search bar (keyup delay), expandable filter panel, inline HTMX edit/delete, CSV export |
| Trades | Dedicated page (grouped by account) | Not present (ticker in transactions) |
| People | Full page + transfer dialog | Not present |
| Categories | Hierarchy (parent_id), tree view | Flat list |
| Reports | None | 4 types: spending, cashflow, net worth, portfolio |
| Budget | Sidebar link only | Model + monthly progress bars |
| Import | Wizard page | Import CSV script |

## Phase 5: Code Pattern Differences

- **HTMX consistency:** DSv4 uses HTMX consistently everywhere (hx-get, hx-delete, hx-trigger="keyup changed delay:500ms"). Older project mixes HTMX with raw fetch() calls and inline JS for search results and CRUD modals.
- **Empty states:** DSv4 has proper empty states with emoji icons on every screen. Older project has "No accounts yet" bare text.
- **Styling:** DSv4 uses CSS custom properties (design tokens: --bg-primary, --accent, --radius). Older uses Bootstrap classes directly.
- **Models:** Older uses StrEnum account types (checking/savings/cash/credit_card/investment) with uuid4().hex[:16] IDs. DSv4 uses Python Enum (bank/credit/investment/cash) with full UUIDs.
- **Extra domain objects:** Older has People, Trades, Transfers. DSv4 has Budget model, Holding model.

## Phase 6: Summary

The older project is more feature-complete (auth, people, trades, import wizard, cleaner architecture) but has inconsistent HTMX usage and Bootstrap-light styling. The DSv4 project is a more polished frontend (dark theme, consistent HTMX, empty states, reports section) but has fewer domain models and no auth.

**Recommendation:** Port DSv4's frontend patterns (dark theme, HTMX consistency, empty states, reports section) into the older project infrastructure for the best of both worlds.
