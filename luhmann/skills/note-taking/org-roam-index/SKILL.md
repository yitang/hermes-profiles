---
name: org-roam-index
description: Maintain an org-roam Zettelkasten knowledge base — generate topic indexes, audit notes against Zettelkasten methodology, and link orphan notes with contextual inline links.
category: note-taking
trigger:
  - "Create an index for my org-roam notes"
  - "Update the notes index"
  - "generate index.org"
  - "audit my notes"
  - "link orphan notes"
  - "Zettelkasten audit"
  - "how do my notes measure up"
  - "link related notes"
---

# org-roam-index

Maintain an org-roam Zettelkasten knowledge base: generate topic-entry-point indexes, audit notes against Zettelkasten methodology, and link orphan notes with contextual inline links.

This skill covers three workflows:
1. **Index generation** — create or update `index.org` as topic entry points
2. **Zettelkasten audit** — evaluate your note collection against Luhmann's principles
3. **Linking orphan notes** — add contextual inline links that explain WHY the connection matters

## When to use

- User asks for a notes index, "index.org", or "Zettelkasten index"
- A batch of new notes was just added and the index needs updating
- Starting work with an org-roam vault for the first time

## Workflow

### 1. Survey the notes directory

```bash
find ~/matrix/tools/meta-tools/notes -type f -name '*.org' | wc -l     # total count
ls ~/matrix/tools/meta-tools/notes/*.org | head -20                     # sample names
```

### 2. Read note contents to discover topics (not just titles)

Use a script like this to dump title + first line of each note — the body often reveals the topic where the title is ambiguous:

```python
import os, re, pathlib

notes_dir = os.path.expanduser("~/matrix/tools/meta-tools/notes")
for f in sorted(pathlib.Path(notes_dir).glob("*.org")):
    if f.name == "index.org":
        continue
    content = f.read_text()
    m = re.search(r'#\+title:\s*(.*)', content)
    title = m.group(1).strip() if m else f.stem
    m2 = re.search(r':CREATED:\s*\[([^\]]+)\]', content)
    created = m2.group(1).strip() if m2 else ""
    # first body lines after title/properties
    body = []
    seen_title = False
    for line in content.split('\n'):
        if line.startswith('#+title:'):
            seen_title = True; continue
        if seen_title and line.strip() and not line.strip().startswith(':') and not line.strip().startswith('#+'):
            body.append(line.strip())
        if len(body) >= 2: break
    summary = ' '.join(body)[:120]
    print(f"{title:40s}  {summary}")
```

### 3. Organize into Zettelkasten-style topic sections

**DO NOT** create an alphabetical list. Group notes thematically by domain:

- **Emacs Lisp Programming** — data structures, control flow, functions, file I/O, buffers, timestamps
- **Emacs Configuration** — startup, modes, keymaps, local variables, packages
- **GPG & Encryption** — all GPG notes together
- **Bash Scripting** — core constructs, parameter expansion, options
- **Ledger (Accounting)** — all ledger subcommands
- **SSH & Remote Access** — SSH, port forwarding, SFTP, Tramp
- **System Administration** — Debian, systemd, docker, monitoring, backup, GPU
- **Networking & Connectivity** — Tailscale, VPS, nmap, USB boot
- **Git & Version Control** — origin, upstream, reset, worktree
- **AI Agents & Local LLMs** — Hermes, ACP, JSON-RPC, llama.cpp, vLLM, GGUF, Discord
- **Email (mu4e)**
- **Development Tools** — IPython, uv, HomeBrew

### 4. Write index.org

Use org-mode syntax with:

```org
#+title: Notes Index
#+filetags: :index:

* Emacs Lisp Programming
:PROPERTIES:
:ID:       UUID-FOR-CROSS-LINKING
:END:

** Data Structures
- [[file:20240116175149-car_and_cdr.org][car and cdr]]
- [[file:20240116190225-association_list_alist.org][association list (alist)]]
```

- Use `:PROPERTIES:` drawers with `:ID:` for cross-linking between sections
- Use subheadings (**) for sub-topics within a section
- A note CAN appear in two sections if relevant to both (e.g. `membership` under both Data Structures and Packages & Tools)
- Links use `[[file:<filename>.org][<title>]]` — the org-roam format for file links

### 5. Verify coverage

After writing, verify all notes are indexed:

```python
from pathlib import Path
import re

notes_dir = Path("~/matrix/tools/meta-tools/notes").expanduser()
index_content = (notes_dir / "index.org").read_text()
indexed = set(re.findall(r'\[\[file:([^\]]+\.org)\]', index_content))
all_notes = set(f.name for f in notes_dir.glob("*.org") if f.name != "index.org")
missing = all_notes - indexed
if missing:
    print(f"MISSING ({len(missing)}):")
    for fname in sorted(missing):
        content = (notes_dir / fname).read_text()
        m = re.search(r'#\+title:\s*(.*)', content)
        print(f"  {fname:50s}  {m.group(1) if m else '?'}")
else:
    print(f"All {len(all_notes)} notes indexed. ✓")
```

## Pitfalls

- **Do not sort alphabetically** — the user wants thematic Zettelkasten entry points, not a phonebook.
- **Reading only titles is misleading** — a file name like `membership` could be Elisp data structures *or* org-roam membership checks. Read the body to disambiguate.
- **A note can belong to two sections** — don't force a single category when a note genuinely bridges domains. Just note it appears in both.
- **Don't miss newly-created notes** — always run a coverage check at the end when appending to an existing index.
- **Retain existing sections** — when updating an existing index.org, preserve the section structure the user already has. Only add new sections for notes that genuinely don't fit existing topics.
- **Inline links need context** — adding `[[id:...][name]]` without explaining WHY the connection matters is noise. Always pair each link with a phrase explaining the relationship.
- **Don't auto-generate a keyword index** — a computer-generated keyword list has no Zettelkasten value. The Keyword Register (Luhmann's third card type) was a thinking ritual: each time Luhmann added a card, he hand-walked to the register and wrote the ID. That act of visiting forced constant review of the collection. A script gives you a static snapshot with none of the craft. If the user has modern full-text search, auto-generated keywords are strictly worse than search. Only offer this if they explicitly ask, and then explain the trade-off.
- **Filename prefixes (`bash_*`, `gpg_*`) are not a keyword register** — they group files in directory listings but a note can only have one prefix, they don't aid search, and they don't reveal gaps or serendipitous connections.
- **A structure note (hub) is not a separate card type** — in Luhmann's original system, all cards are "Zettels" (main notes). A hub is just an ordinary Zettel whose content happens to be "links for topic X." Same format, same ID rules, same linking rules.

---

## Workflow 2: Zettelkasten Audit

Audit a note collection against Zettelkasten principles (Luhmann system) to identify gaps.

### 2.1 Research the methodology first

Before auditing, research the methodology to anchor the evaluation. Key sources:
- zettelkasten.de/introduction — core principles (atomicity, hypertext, structure notes)
- Sönke Ahrens, "How to Take Smart Notes" — note types (fleeting, literature, permanent, project)
- Bob Doto / writing.bobdoto.computer — atomicity is for writing velocity, not just "making connections"

### 2.2 Audit dimensions to check

Use an analysis script that evaluates each note on:

| Dimension | What to measure | Ideal |
|---|---|---|
| **Atomicity** | Word count per note | 50–300 words, one idea per note |
| **Linking** | [[id:...]] links per note | 2–5+ links to related notes |
| **Orphan rate** | % of notes with zero links | <20% (ideally 0%) |
| **Unique IDs** | org-roam UUID in :PROPERTIES: | Every note has one |
| **Your own words** | First-person, conversational style | Not verbatim quotes |
| **Structure notes** | Hub/index notes that aggregate topic entries | At least 1 per major topic |
| **Source tracking** | External URLs or #+bibliography lines | Present when note derives from reading |
| **Link context** | Explanatory text around each link | Absent links are noise |
| **Broken links** | [[id:...]] targeting non-existent IDs | 0 broken links |
| **Note type mix** | Fleeting (<30w), permanent, literature | Mostly permanent; fleeting should be expanded |

### 2.3 Run the audit

Two options:

**Option A — Bash (fast, self-contained):**
```bash
bash scripts/audit.sh ~/path/to/notes
```
Runs in a single terminal() call. Reports orphans, word count distribution, filetags, oversized/small notes, source tracking, linking stats, and hub notes. No Python dependencies. Adjust the path or pass it as the first argument. The script is in `scripts/audit.sh` under this skill directory.

**Option B — Python (execute_code, more flexible):**
Write an analysis script (see `references/audit-script.md` for a template) that:

1. Collects all notes and parses their metadata (title, ID, created date, tags)
2. Counts all link types (internal [[id:...]], file [[file:...]], external URLs)
3. Identifies orphan notes and broken links
4. Estimates note types by word count and source metadata
5. Produces a structured scorecard

### 2.4 Write an audit document

Save the results as `notes/ZETTELKASTEN_AUDIT.org` with:

- **Core Principles summary** — what the methodology says
- **Audit Results by dimension** — GOOD / AREA FOR IMPROVEMENT / MISSING
- **Summary Scorecard** — table with Status column per principle
- **Concrete Recommendations** — numbered, actionable items ordered by impact

---

## Workflow 3: Linking Orphan Notes

The single biggest Zettelkasten gap is almost always orphans (notes with zero internal links). Fixing them transforms a flat file pile into a connected knowledge web.

### 3.1 Identify orphan clusters

Group orphans by topic (many orphans naturally cluster — all GPG notes together, all Bash notes together, etc.). The content dump from Workflow 1 step 2 gives you summaries to spot clusters at a glance.

### 3.2 Build a connection map

For each orphan cluster, map out natural connections. Example: the Bash cluster (8 notes):

| Note | Connected to | Why |
|---|---|---|
| function arguments | parameter substitution | $1 is a form of ${} substitution |
| function arguments | if-else | validate args with if-else |
| function arguments | source | source + args pattern |
| if-else | file test, empty string test | conditions used in if |
| if-else | for-loop | conditionals inside loops |
| for-loop | function arguments | `for arg in "$@"` |
| for-loop | set -x | debugging loop iterations |
| empty string test | if-else, file test | -z lives in if-else; companion -f |
| parameter substitution | function arguments, source, set -u | $1 is substitution; $( ) vs source; -u catches undefined |
| set options | parameter substitution, for-loop | -u + ${}; set -x + loops |
| source | parameter substitution, set -e | $( ) vs source; -e + source = dangerous |

### 3.3 Add links inline with context

**Golden rule**: every link must explain WHY. Never append a bare link list at the bottom.

- **Inline at the natural point** — where the concept is first mentioned or where the reader would benefit from the connection
- **Use a connecting phrase**: "Contrast with...", "See the companion...", "Related: ...", "This is a form of..."
- **Establish the relationship in ~5-15 words** before or after the link

Good: `Contrast \`$(...)\` (subshell) with [[id:...][source]], which runs in the current shell and can modify the parent environment.`
Bad: `See also [[id:...][source]].`

### 3.4 Editing technique

For each note, use `patch` via `skill_manage` with `old_string`/`new_string` — not execute_code or terminal/sed on single files. This gives you a clean diff and catches syntax errors. Edit one note at a time and verify each diff.

### 3.5 Verify

After linking, re-run the analysis to confirm:
- Previously orphan notes now have 1+ links (count links per note)
- No broken links were introduced (all [[id:...]] target existing UUIDs — check every link resolves to a real :ID: in the notes directory)
- Link distribution: each note should have at least 1-2 links; clusters should be fully connected (e.g. 8 Bash notes with 20+ links among them)

---

## References

### support files

- `references/zettelkasten-principles.md` — condensed Zettelkasten methodology reference (core principles, note types, Luhmann's original system, scoring rubric)
- `references/audit-script.md` — reusable Python analysis script that evaluates all audit dimensions and produces the scorecard
- `scripts/audit.sh` — fast self-contained bash audit script. Usage: `bash scripts/audit.sh ~/path/to/notes`. Reports orphans, word counts, filetags, source tracking, and linking stats in one pass.
