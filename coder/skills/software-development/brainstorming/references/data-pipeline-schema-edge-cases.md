# Data Pipeline Schema Edge Cases — Worked Example

**Date:** 2026-06-05
**Context:** Designing an inbox-to-SQLite pipeline for personal finance data. Users
drops bank CSVs into `inbox/`, an import script parses and appends to a SQLite
database. During the spec review, the user pushed back on three things the agent
got wrong. This document captures those corrections so future sessions don't repeat them.

## Correction 1: Write schemas from real data, not placeholders

**What happened:** The agent wrote "Lloyds — determined during implementation" as
a placeholder, expecting to fill it in later. User asked: "why can't you have a
look of the files and design the schema for now?"

**Lesson:** When spec'ing a project with existing data files, inspect actual CSV
samples (column headers, value formats, row counts) before writing the schema
section. Don't defer data-driven decisions to "implementation time."

**Signal phrase from user:** "why can't you have a look of the files..."

## Correction 2: Enumerate all edge cases, not just the first one

**What happened:** The agent wrote a "Schema evolution" section that only covered
one scenario (header labels change). User asked about header positions, columns
added, columns removed — four more scenarios the agent hadn't considered.

**Lesson:** Any spec section about "handling change" or "format variation" needs
an exhaustive enumeration of every concrete scenario:
- Labels renamed vs positions shuffled (different fixes)
- Columns added at end vs in middle (same fix — both fine with name-based lookup)
- Columns removed (stays in inbox, needs parser update)
- Complete format change (stays in inbox, needs new parser)

**Signal phrase from user:** "schema can be changed in many different ways..."

## Correction 3: Preserve unknown data by default

**What happened:** The agent wrote that extra columns would be "silently
discarded." User pushed back: "additional columns can be useful."

**Lesson:** In data pipeline specs, the default should be preserve-all-data. If
a bank adds a new column (like native category), that data is valuable. Design
a catch-all mechanism (e.g. an `extra` JSON column) so nothing is lost even from
columns you don't have a named mapping for yet.

**Signal phrase from user:** "the information is useful"
