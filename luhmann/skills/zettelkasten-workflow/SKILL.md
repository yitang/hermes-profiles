---
name: zettelkasten-workflow
description: "Procedures and reference for Zettelkasten workflow: capture, processing, literature notes, permanent notes, PARA inbox audit, and vault discovery. Core principles are in the Luhmann SOUL.md."
version: 1.2.0
author: yitang
tags: [org-roam, zettelkasten, note-taking, knowledge-management, para]
---

# Zettelkasten Workflow

Three note types, distinguished by `#+filetags:`:

| Tag            | Type        | Description                            |
|----------------+-------------+----------------------------------------|
| `:fleet:`      | Raw capture | Scribbles from reading, half-formed    |
| `:literature:` | Source ref  | Citation + summary of a single source  |
| (none)         | Permanent   | Your own words, linked, final          |

> Core note-writing principles (atomicity, surgical edits, done criteria) are in
> the Luhmann profile's SOUL.md. This skill covers procedures and reference material.

## Vault discovery

Do NOT assume a single `notes/` folder in CWD. The user's vaults may be
spread across multiple git repos. For this user, the vaults live at:

```
~/matrix/{domain}/meta-{domain}/notes/
```

Discovery: walk `~/matrix/*/meta-*/notes/` looking for `*.org` files.
See `references/vault-paths.md` for the precise list and per-vault stats.

Use a shell glob:

```bash
for d in /home/tangyi/matrix/*/meta-*/notes; do
  [ -d "$d" ] || continue
  echo "$d — $(ls "$d"/*.org 2>/dev/null | wc -l) notes"
done
```

## Distinguishing TODOs from fleet notes

A fleet note captures a *thought* or *observation*. A TODO captures an
*action*. They look similar in org-mode but have different fates:

| This is a fleet note                          | This is a TODO masquerading as a note       |
|-----------------------------------------------+---------------------------------------------|
| "Kanban visualises WIP limits implicitly"     | "add literature notes on kanban"            |
| "I notice I over-research when stressed"      | "ask agent to analyse my matrix setup"      |
| FATE: process into permanent note             | FATE: add to your GTD inbox, delete the note|

Rule of thumb: if the entire note could be a `[ ] TODO` checkbox item,
it doesn't belong in the Zettelkasten. Move it to your task system.

## Workflow 0: PARA inbox audit (NEW)

Before capturing fleet notes, the user's raw material often sits in a
PARA inbox at `~/para/4_inbox.org`. Audit it first to separate genuine
note candidates from TODOs, bookmarks, and stale items.

### 0.1 Read the inbox

```bash
read_file ~/para/4_inbox.org
```

Each entry has a date and a `[ ]` checkbox followed by a topic heading
and a body. The body may contain developed thoughts, questions, or just
a title.

### 0.2 Classify each item

For every item, ask: **What is this?**

| Class | Definition | Action |
|-------|------------|--------|
| **Fleet note** | A developed thought with a concept worth extracting. Body contains reasoning, an observation, a principle. | Extract → cluster → process into permanent note |
| **TODO** | An action instruction ("create a skill for...", "integrate X") | Move to task system. Delete from inbox. |
| **Question** | An open question with no answer ("what is Pydantic model?", "what is monolithic architecture?") | Either research + answer + turn into a note, or move to task system as a research task. |
| **Bookmark** | A reference to something (a skill path, a file) with no content or idea attached | Delete — the reference belongs in the relevant directory, not the inbox. |
| **Stale / already-encoded** | The idea has been processed into a Hermes skill or permanent note since the item was written | Mark done, delete. Cross-reference skill names. |
| **Trivial** | A naming decision, a one-liner reaction ("this is gonna be very good") | Delete — no knowledge left on the table. |

**Stale-item detection (important):** When the body describes something
that sounds like a finished Hermes skill (e.g. "agent load balance",
"spike workflow", "batch-debugging"), check whether a skill already
exists:

```bash
ls /home/tangyi/.hermes/profiles/luhmann/skills/*/SKILL.md 2>/dev/null | grep -i "spike\|load-balance\|batch-debug"
```

If the concept is already documented, the inbox item is stale — mark it
done and move on.

### 0.3 Cluster by topic

Group fleet-note candidates by domain. This session's inbox yielded:

- **Psychology / Behaviour** — control displacement, substitution coping, attention narrowing under stress
- **Personal Finance (concepts)** — equity as subtraction, credit card exclusion from balance sheet
- **Personal Finance (data architecture)** — canonical vs per-bank schema, ETL/UI separation pattern
- **Hermes workflow** — (mostly stale — already in skills)

### 0.4 Report to the user

Give a structured summary with:
- Cluster headings, each item's type, and a ✅/❌/⚠️ Zettelkasten recommendation
- Counts: how many items total, how many are genuine note candidates
- Which TODO items need to be moved to their task system
- Which items are stale/bookmarked/trivial and should be deleted

### 0.5 Offer to process

Ask which cluster or item they want to start with. Do not process
everything unasked — the user said they're "half way through it."

## Workflow

### 1. Capture (fleet)

When reading docs or exploring a new tool, create a note immediately with a `:fleet:` tag:

```
#+title: Hermes Router Notes
:PROPERTIES:
:ID:       <generate>
:CREATED:  [2026-06-08 Mon]
:END:
#+filetags: :fleet:hermes:

per-lane routing: assign different model per channel
config inheritance: top-down defaults, merge bottom-up
gateway setup via hermes gateway setup
```

Fragments, bullets, questions — no need for full sentences.

### 2. Process

Find all fleet notes by searching for `:fleet:` within the vault that
needs processing. For each one:

1. **Read and identify** — Read the scribbles. How many distinct ideas are there? If >1, plan N permanent notes.

2. **Split by atomicity** — Create one permanent note file per idea. Do not leave two ideas in one file.

3. **Rewrite** — Each permanent note in your own words, proper sentences. If you're quoting, it's not permanent yet.

4. **Link** — Every permanent note needs at least one link: back to the source literature note AND forward to related permanent notes. An unlinked permanent note is an orphan.

5. **Promote the original** — Remove `:fleet:`, add `:literature:`. This is the source reference.

**Processing checklist (for each fleet note):**

- [ ] How many ideas here? (one → one file, many → N files)
- [ ] Is this actually an idea, or a TODO? (TODO → move to task system, delete note)
- [ ] Rewritten in your own words? (citations/quotations → belongs in literature, not permanent)
- [ ] Linked to ≥1 existing permanent note? (zero links = orphan)
- [ ] Original note retagged to `:literature:`? (fleeting tag removed)
- [ ] If the fleet note was a question, have you answered it? (unanswered questions don't graduate)

### 3. Literature note (source reference)

The original fleet note becomes the source reference. Remove `:fleet:`, add `:literature:`:

```
#+title: Hermes Agent — Routing
:PROPERTIES:
:ID:       <same ID>
:CREATED:  [2026-06-08 Mon]
:END:
#+filetags: :literature:hermes:
#+source: https://hermes-agent.nousresearch.com/docs

Read 2026-05-05. Configuration guide.

Concepts expanded in:
- [[file:2026xxxx-per_lane_routing.org][Per-Lane Routing]]
- [[file:2026xxxx-config_inheritance.org][Config Inheritance]]
```

### 4. Permanent notes

Each idea becomes its own note with no special tag:

```
#+title: Per-Lane Routing
:PROPERTIES:
:ID:       <new ID>
:CREATED:  [2026-06-08 Mon]
:END:

Hermes Agent allows routing different communication channels to
different language models... Configured under `gateway.channels`.

Source: [[file:2026xxxx-hermes-router.org][Hermes Agent — Routing]]
```

Permanent notes have:
- No `:fleet:` or `:literature:` tag
- A source link back to the literature note
- Internal `[[id:...]]` links to related permanent notes

## Finding unprocessed notes

```bash
# across all vaults
for d in /home/tangyi/matrix/*/meta-*/notes; do
  [ -d "$d" ] || continue
  grep -rl "filetags.*fleet" "$d" 2>/dev/null && echo "  → in $d"
done
```

Every fleet note must be processed. If a `:fleet:` note sits unprocessed for
