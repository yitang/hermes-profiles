# Zettelkasten Principles — Condensed Reference

## Origin

- Invented by **Niklas Luhmann** (German sociologist, 1927–1998)
- Published 50+ books, 600+ articles using this system
- Maintained ~90,000 handwritten cards across two independent slip-boxes
- Luhmann stated that working with the Zettelkasten consumed more of his time than the actual book writing — that was the point
- Averaged only 6 notes per day over 40 years

## Core Principles

### 1. Atomicity — one idea per note
- Each note = one discrete knowledge building block
- Makes notes easy to recombine (connect single idea → many single ideas)
- Ideal: 50–300 words
- "A thought might span a book; a Zettel is a single thought."

### 2. Unique Identifiers
- Every note must have a stable ID so it can be addressed in links
- Luhmann: hierarchical alphanumeric (1, 1a, 1a1) — Folgezettel (follow-up notes)
- Digital: timestamps, UUIDs, or incremental numbers
- Changing an ID breaks all links — use permanent IDs

### 3. Hypertext — connection over collection
- The web of links is the value, not any individual note
- "It is not important where you place a new note as long as you can link to it."
- Each link must state WHY the connection was made — bare links are noise
- Backlinks recorded on both sides (in digital = automatic)

### 4. Your own words
- Notes must be your own processing, not verbatim quotes
- The act of reformulating forces understanding
- Quotes are OK *on top of* your interpretation, not instead of it

### 5. Structure Notes (Hub Notes / Entry Notes / Übersichtszettel)
- A meta-note: a note about other notes and their relationships
- Acts as table of contents / navigation hub for a topic
- "The Money Is in the Hubs" — Johannes Schmidt (Luhmann archivist)
- Luhmann had Zettels with extensive link lists acting as "highways between topics"
- Structure notes grow organically as you add new notes

**Important: a structure note is not a separate card type.** In Luhmann's system, every card is a "Zettel" (main note). A structure note is just an ordinary Zettel whose *content* happens to be "here are the links for topic X." The same card format, the same ID system, the same linking rules. This was a clarification that came up in conversation — don't treat hubs as a special category.

### 6. Source Tracking
- When a note derives from external material, record the source
- Reference manager (Zotero, BibDesk) + cite keys recommended
- A note with no reference = assumed to be your own original thought

## Luhmann's Original System — 3 Card Types

Luhmann's actual physical system had only three kinds of cards:

1. **Main Notes (Zettels)** — The core. One idea per card, written in your own words, with a unique alphanumeric ID. ~90,000 total across both boxes. Some of these were "entry notes" / "overview notes" that aggregated links to other notes (what modern guides call structure notes/hubs — but same card type).

2. **Literature Notes (Bibliographic Notes)** — Short summaries of a book or article on one side, full citation on the other. ~30,000 total. These are not the idea itself — they're a digest of the source, a pointer back to the original.

3. **Keyword Register (Register)** — An alphabetical list of keywords on a separate card. Each keyword points to the ID of the entry point note(s) for that topic. This is what Luhmann consulted *first* when searching — his paper-based search engine. It was hand-written and updated manually whenever he added a new note.

**The 4-type taxonomy (Ahrens)** — fleeting, literature, permanent, project — is a later pedagogical reframing. It's useful for teaching but was not Luhmann's own system. When auditing a collection, prefer the original 3-type system.

## Note Types (Sönke Ahrens / "How to Take Smart Notes" — pedagogical, not Luhmann's own)

### Fleeting Notes
- Temporary capture of a thought or highlight
- Short, incomplete — meant to be processed within 1–2 days
- If kept permanently without expansion, they become dead weight

### Literature Notes
- Notes about a specific external source (book, article, video)
- Written in your own words summarizing the source
- Includes full bibliographic reference
- Stays in reference manager or as a standalone note

### Permanent Notes (Zettels)
- The core of the Zettelkasten
- Self-contained, atomic, written for your future self
- Connected to other notes via links with context
- No project-specific framing — meant to outlive any single project

### Project Notes
- Notes tied to a specific writing project or output
- Can be discarded or archived after the project ends
- Not filed into the permanent Zettelkasten

## Luhmann's Original System Details

- Two independent slip-boxes, rarely cross-linked
- First: ~24,000 cards + 1,800 bibliographic entries
- Second: ~66,000 cards + 16,000 bibliographic entries
- Organized by "big departments" (historical interest areas)
- New Zettels placed based on connection to the previous Zettel
- Topics were deliberately spread out — variability enables far-fetched connections
- Folgezettel (sequential branching) was a physical-workaround technique, not a core principle

## Keyword Register — Why Hand-Crafted Matters

The keyword register is the most misunderstood part of Luhmann's system. It was **not** an index that he later consulted — it was a **thinking ritual**.

Every time Luhmann added a new note, he would walk to the register card, find the right keyword, and physically write the note's ID. That act of visiting the register meant he was constantly reviewing his collection — re-discovering old notes, noticing gaps, seeing unexpected connections.

**A computer-generated keyword index has zero value.** It's a snapshot you don't learn from. The value was in the writing, not the artifact. If you're not writing it by hand as you add notes, skip it — modern full-text search is faster and better.

**Filename prefixes** like `bash_*`, `gpg_*`, `emacs_*` are not equivalent to a keyword register. They group notes visually in directory listings but:
- A note can only have one filename (a note about `git_worktree` relevant to `backup` can't sit in both)
- They don't help you *find* anything — they're cosmetic
- They don't reveal gaps or foster serendipity

## Digital Adaptation

- Search replaces the need for physical ordering
- Folgezettel is optional — linking is sufficient
- Hubs become more important (no physical topography to navigate)
- "The method should bend around your thinking and not the other way around."

## Common Pitfalls / Misconceptions

- Zettelkasten is NOT primarily for "making connections" — it's a **writing tool** (Bob Doto)
- Atomic notes exist because it's easier to connect single ideas to many others, not because of space constraints
- It takes years before the system "unfolds its magic" (Luhmann knew this was a lifetime project)
- Zettelkasten does not make you a productivity machine — it leverages your efforts
- **Auto-generated indexes are worthless** — the craft is in hand-curating the connections
- **Don't confuse filename prefixes with a keyword register** — they solve different problems
- **A hub note is not a separate card type** — it's an ordinary Zettel whose purpose is navigation

## Audit Scoring Rubric

| Principle | Excellent | Good | Needs Work | Missing |
|---|---|---|---|---|
| Atomicity | Most notes 50-300w, one idea each | Most <500w, few multi-idea | Many >500w or <10w | Notes are book chapters |
| Unique IDs | org-roam UUIDs + timestamps | UUIDs present | Some missing | No IDs |
| Your words | Clear personal voice, no quotes | Mostly own words | Mix of own/copied | Verbatim quotes |
| Linking (density) | 3+ links avg, <10% orphans | 1-2 links avg | <1 link avg, many orphans | No links at all |
| Structure notes | 1 hub per major topic | 1 general index | Only an index | None |
| Source tracking | Every derived note has source | Most do | Some do | None |
| Link context | All links explain WHY | Most do | Some do | No context |
| Broken links | 0 | 1-2 | 3-10 | >10 |
