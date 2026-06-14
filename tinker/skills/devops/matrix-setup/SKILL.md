---
name: matrix-setup
description: Understand and work with the ~/matrix/ directory structure — domain layout, meta-* projects, .dir-locals.el org-roam vault wiring, notes directories, and conventions. Load this skill when the task involves any path under ~/matrix/.
---

# Matrix Setup

## Overview

`~/matrix/` is the root for all personal projects, organized into 7 domains.
Each domain is a top-level directory under `~/matrix/`. Every domain has:

1. **Multiple project repos** — independent git repos for specific work
2. **A `meta-*` project** — the "meta" layer managing that domain's notes/knowledge base
3. **A `.dir-locals.el`** at the domain root — wires Emacs org-roam to the meta-* notes/
4. **A `notes/` folder** inside `meta-*/` — flat org-roam vault with `.org` files

## The 7 Domains

| Domain | Path | meta-* dir | dir-locals.el | notes/ files | DB? |
|--------|------|------------|---------------|--------------|-----|
| Data Science | `ds/` | `meta-ds/` | `ds/.dir-locals.el` | 128 | yes |
| Finance | `finance/` | `meta-finance/` | missing | 0 (6 .org scattered) | no |
| Health | `health/` | `meta-health/` | `health/.dir-locals.el` | 5 | yes |
| Hobbies | `hobbies/` | `meta-hobbies/` | `hobbies/.dir-locals.el` | 174 | yes |
| Learning | `learning/` | `meta-learning/` | `learning/.dir-locals.el` | 25 + 318 vocab | yes |
| Reflect | `reflect/` | none | missing | 0 (plain org-capture) | no |
| Tools | `tools/` | `meta-tools/` | `tools/.dir-locals.el` | 148 | yes |

Total: ~800 org-roam notes across 5 wired vaults + vocabulary.

## How .dir-locals.el Wires Org-Roam

.dir-locals.el files sit at the **domain root** (e.g. `~/matrix/tools/.dir-locals.el`),
NOT inside meta-* projects. They use `locate-dominating-file` to walk UP from whatever
file you're editing, then point into the meta-* subdirectory:

```elisp
((nil . ((eval . (progn
           (setq-local project-dir (file-name-concat
             (locate-dominating-file default-directory ".dir-locals.el")
             "meta-<domain>"))
           (setq-local note-dir (file-name-concat project-dir "notes/"))
           (setq-local org-roam-directory note-dir)
           (setq-local org-roam-db-location
             (file-name-concat note-dir "org-roam.db"))
           (setq-local projectile-project-root project-dir)
           (setq-local org-download-image-dir
             (file-name-concat project-dir "assets/org-download"))
           )))))
```

This means editing any file under `~/matrix/tools/` activates the tools vault.
You don't need to be inside `meta-tools/` specifically.

## Context-Dependent Org-Roam Capture

Since `org-roam-directory` is NEVER set globally, you need to let-bind it when
capturing outside a domain context. Standard pattern:

```elisp
(let ((org-roam-directory (expand-file-name "notes/" meta-dir))
      (org-roam-db-location (expand-file-name "org-roam.db"
                              (expand-file-name "notes/" meta-dir))))
  (org-roam-node-find))
```

This respects existing roam capture templates, ID generation, and db sync.
Do NOT manually create `.org` files with `with-temp-file` — that bypasses everything.

## Active Tooling: yt-matrix.el

The old matrix-setup system (main.org → Python → transient_python.el — 4 files,
2 languages, 27 archived projects) is replaced by a single file:

`~/para/1_projects/org-roam-anywhere/yt-matrix.el`
(also saved as `references/yt-matrix.el` in this skill)

**What it provides:**
- `C-c m` → transient popup with 6 meta-* domains + 4 reflect projects
- Pick a domain → action menu (TODO, Note, Journal, Roam, Dired, Agenda)
- `C-c r` → direct roam dispatch: prompt for domain, then `org-roam-node-find`
- `C-c c` → `r` → `rd`/`rf`/`rh`/`rH`/`rl`/`rt` — per-domain roam via org-capture dispatch
- Roam action opens `org-roam-node-find` in that domain's vault (via let-binding)
- Capture templates and agenda commands auto-generated from the data

**Roam dispatch approaches (two complementary paths):**

1. **Direct key** (`C-c r`): uses `read-multiple-choice` to pick domain, then opens roam.
   Best when you know you want to roam and just need to pick where.

2. **Via org-capture** (`C-c c` → `r` → `rd`/etc.): each domain has a capture entry with
   a `(function ...)` target that calls `org-roam-node-find`. The function returns
   `(current-buffer)` so org-capture doesn't error. Template body is empty string `""`.

   Per-domain roam entries used to be defined by a macro, but the refactored version
   uses **lambda closures** — the domain key is captured in the closure at template
   generation time:

   ```elisp
   ;; In the capture template generator loop:
   (push `(entry (function (lambda ()
                    (yt/meta--roam-capture
                     (nth 3 (car (nthcdr 2 (assoc ,domain-key yt/meta-projects)))))))
               "") templates)
   ```

   This avoids creating 6 separate named functions. The lambda is closed over
   `domain-key` at the time the template list is built. Works because `push`
   captures the current value of `` domain-key`` in each iteration.

   **Important:** `org-capture` with `(function ...)` target calls the function with
   no arguments. The function must visit a file and return the buffer. The pattern:
   ```elisp
   (defun my-capture-fn (dir)
     (let ((org-roam-directory (expand-file-name "notes/" dir)))
       (org-roam-node-find))        ;; opens file
     (current-buffer))              ;; return buffer to org-capture
   ```

**Loading:**
```elisp
(load "~/para/1_projects/org-roam-anywhere/yt-matrix.el")
(yt/meta-enable)
```

**Architecture (refactored — data-driven):**
- `yt/meta-projects` — flat alist. **Single source of truth.** Edit this to add/remove.
- `yt/matrix3` — main transient (domain selection), built dynamically at load time
- `yt/meta--action-transient` — second transient (action selection)
- Context passed between transients via `yt/meta--cur` variable (see technique below)
- Generic `yt/meta--select-by-key` — ONE function for all domain selection (no per-domain macros)
- `yt/meta--capture-templates` generates org-capture templates from the data
- `yt/meta--agenda-commands` generates org-agenda commands from the data

**Data-driven transient pattern — avoid hardcoding menu entries:**
```elisp
;; WRONG — hardcoded, must update when data changes
(transient-define-prefix yt/matrix3 ()
  ["Matrix"
   [("d" "Data Science" yt/meta--select/d)
    ("f" "Finance"      yt/meta--select/f)]])

;; RIGHT — built from data at load time
(eval
 `(transient-define-prefix yt/matrix3 ()
    "Quick access."
    ["Matrix"
     ,(vconcat
       (cl-loop for d in yt/meta-projects
                collect
                `(,(nth 0 d) ,(nth 1 d)
                  (lambda () (interactive)
                    (yt/meta--select-by-key ,(nth 0 d))))))]))
```

`cl-loop` inside `transient-define-prefix` fails due to eager macro-expansion.
The `eval` + backquote pattern defers expansion to runtime, letting `cl-loop`
produce the suffix entries. `vconcat` converts the list into a vector for the
transient group syntax. This is also how reflect project listings are built.

**Context-passing technique (state variable pattern):**
```elisp
(defvar yt/meta--cur nil "Current project for the action transient.")

;; Selector: look up project from data, set state, open next transient
(defun yt/meta--select-by-key (key)
  (interactive)
  (let ((domain (assoc key yt/meta-projects)))
    (when domain
      (setq yt/meta--cur (car (nthcdr 2 domain)))
      (transient-setup 'yt/meta--action-transient))))

;; Action: read state, dispatch to the correct dir/vault/capture
(defun yt/meta--action/roam ()
  (interactive)
  (let ((org-roam-directory (expand-file-name "notes/" (nth 3 yt/meta--cur))))
    (org-roam-node-find)))
```

**The user's most-used actions are Dired and Roam.** The TODO/Note/Journal/Agenda
actions exist but are rarely reached for.

## AGENTS.md Files

Each domain has an `AGENTS.md` at the domain root documenting its matrix setup
details. These were updated in 2026-06 to include the .dir-locals.el wiring
and org-roam vault status. Key ones:

- `~/matrix/tools/AGENTS.md` — most detailed, covers all 6 tools projects
- `~/matrix/learning/AGENTS.md` — documents the vocabulary vault split
- `~/matrix/finance/AGENTS.md` — notes that setup is incomplete

## Note File Format

All org-roam notes use v2 format. Files in `notes/` are flat (no subdirectories):

```org
:PROPERTIES:
:ID:       B64DC53E-A959-4F00-8B5C-C937EF799C95
:matrix:   <domain>
:END:
#+title: Note Title
#+filetags: :tag1:tag2:
```

The `:matrix:` property is a custom classifier on older notes. File naming:
- Newer: `20221217_174739-nonlinear.org` (with underscore, from capture template)
- Older: `20221103114407-softmax.org` (no underscore)

## Special Cases

- **vocabulary/** — 318 notes at `learning/meta-learning/vocabulary/` (flat, no notes/ subfolder).
  Uses `yt/add-vocabulary` capture flow in `emacs_config.org`. **macOS-only** — guarded by
  `(when (bound-and-true-p is-macos) ...)`. On Linux the code compiles out silently.

- **finance/** — No `.dir-locals.el`. 6 study .org files scattered in subdirs, not in a notes/ vault.

- **reflect/** — No meta-* project. Uses plain org-capture, not org-roam. Diaries, personal
  finance, reviews are all plain org files.

## Org-Capture Template Landscape

Capture templates are **not** in a single file — they accumulate from three sources in a specific load order.

### Loading Order

1. **`config.org` (→ `lisp/general.el`)** — loaded via `load_config.el`. Contains general-purpose templates.
2. **`emacs_config.org` (→ `emacs_config.el`)** — loaded from `.emacs`. Contains personal/journal/reading templates.
3. **`yt-matrix.el`** — loaded explicitly. Uses `append` so it never overwrites.

Since sources 1 and 2 both use `setq` (which replaces the entire variable), the later one wins. Source 3 uses `append` so it's additive.

### Audit Pattern

When simplifying a capture template set, follow this sequence:

1. **List all templates** — run Emacs batch mode and print `org-capture-templates`. 204 templates means cruft; <40 means lean.

2. **Group by functionality** — classify as: inbox capture, journaling, data tracking, accounting, reading, roam notes, project management.

3. **Check target files** — for each template, verify the target file exists on disk and has recent content:
   ```bash
   ls -la ~/path/to/target.org
   wc -l ~/path/to/target.org
   ```
   A file with 4 lines and no recent edits is dead. A file with 6000 lines and recent timestamps is active.

4. **Analyze content** — for journal/diary files, check:
   - Number of entries per year (`grep -c '^* 2025' diary.org`)
   - Whether entries have actual text or just timestamps
   - Last entry date to see if the user is still journaling

5. **Remove dead templates** — kill templates whose target files don't exist, are tiny (<20 lines), or are clearly abandoned.

6. **Re-tangle after editing** — `emacs_config.org` and `config.org` are org-mode source files. After editing, regenerate the .el files:
   ```bash
   emacs --batch --eval "(progn (require 'org) (find-file \"...emacs_config.org\") (org-babel-tangle))"
   ```
   Or in Emacs: `C-c C-v t` on the source file.

### Syntax Gotcha: org-roam vs org-capture

Org-roam capture templates and regular org-capture templates use **different syntax**:

```elisp
;; WRONG — org-roam expansions in regular org-capture (loads silently, fails at runtime)
("h" "hobbies" plain "%?"
 :target "~/path/%<%Y%m%d_%H%M%S>-${slug}.org"
 :headline "${title}")

;; RIGHT — use explicit template expansions for org-capture
("h" "Hobbies TODO" entry
 (file+headline "~/path/main.org" "TODOs")
 "* TODO %?\n%U\n")
```

`${slug}` and `${title}` are org-roam template variables — they only work in
`org-roam-capture-templates`. In regular `org-capture-templates`, they're literal text.

### Current State (2026-06)

After simplification: **39 templates** across 3 groups:

```  
C-c c Roam group (7):
  r    Roam              (group heading)
  rd   Data Science      → org-roam-node-find in ds/meta-ds/notes/
  rf   Finance           → org-roam-node-find in finance/meta-finance/notes/
  rh   Health            → org-roam-node-find in health/meta-health/notes/
  rH   Hobbies           → org-roam-node-find in hobbies/meta-hobbies/notes/
  rl   Learning          → org-roam-node-find in learning/meta-learning/notes/
  rt   Tools             → org-roam-node-find in tools/meta-tools/notes/

yt-matrix.el (24):
  Domain-level:  d f h H l t  (group headings)
  Per-project:  {key}t (TODO), {key}n (Note), {key}j (Journal)

emacs_config.org (8):
  t  Inbox TODO     → ~/para/4_inbox.org
  n  Inbox Note     → ~/para/4_inbox.org
  j  Journal        (group)
  jd Diary          → ~/matrix/reflect/diaries/diary.org  (effectively unused — 6K lines of brain dump)
  jD Daily Plan     → ~/git/beorg/daily_plan.org          (active via beorg mobile)
  R  fore reading   (group)
  Rn reading notes
  Rv reading vocabulary
```

## Pitfalls

- `org-roam-directory` is NEVER set globally. `C-c n f` from a non-domain buffer won't work.
- Domain-level `.dir-locals.el` only activates when you open a file inside that domain tree.
- Missing DBs can be rebuilt with `M-x org-roam-db-sync` from any file in the domain.
- `read-multiple-choice` returns `(CHAR . LABEL-STRING)`, not the original alist entry.
  Always use `assoc` + `char-to-string` to look up the original entry.
- **`cl-loop` inside `transient-define-prefix` fails**: The eager macro-expansion at load time
  can't handle `cl-loop` as a body element. Use `eval` + backquote instead
  (see data-driven transient pattern above).
- **`(function ...)` capture target doesn't receive args**: If you use `(function my-fn)`
  in an org-capture template, `my-fn` is called with no arguments. For parameterized
  captures (e.g. writing to different directories), use a state variable instead,
  or call `org-capture` from a wrapper function rather than defining it as a capture target.
- **`defvar` forward declaration needed for let-bound package variables**:
  If you use `(let ((org-roam-directory ...)) ...)` before `org-roam` has loaded,
  the byte-compiler sees `org-roam-directory` as lexical and errors when the package later
  declares it as dynamic (`defvar`). Fix by adding an empty `defvar` at the top of your file:
  ```elisp
  (defvar org-roam-directory)     ;; forward declaration
  (defvar org-roam-db-location)
  ```
  Place these after `require` statements and before any function that uses them in a
  `let` binding. Applies to any variable defined by a package loaded later.
- **`package-user-dir` is set before `.emacs` runs**: Emacs auto-calls `package-initialize`
  at startup (27+) before loading the init file. Setting `user-emacs-directory` inside
  `.emacs` is too late to change where packages install. Use `--init-directory` flag to
  set it before init fires. This is why the user's alias passes the flag.
- **Cross-platform Emacs config with `is-macos`**: The user's `.emacs` sets
  `(setq is-macos (equal system-type 'darwin))` at the top. macOS-specific code
  (e.g. osx-dictionary integration, screencapture for org-download) is guarded with
  `(when (bound-and-true-p is-macos) ...)`. Follow this pattern when adding
  platform-dependent features. Don't use `(eq system-type 'darwin)` inline —
  the centralized variable makes it easy to add other platforms later.
- When testing elisp in batch mode, pass `-l ~/.emacs` if the file depends on packages
  (transient, org-roam, org) — batch mode doesn't load user config by default.
- For reflect domain, don't try to set up org-roam — the user uses plain org-capture there.
- **Hermes `HOME` override breaks `~` expansion in terminal**: When running under a Hermes
  profile, the `HOME` environment variable is set to `~/.hermes/profiles/<profile>/home`,
  NOT the user's real `/home/tangyi`. This means `~` expansion and `os.path.expanduser('~')`
  resolve to the wrong directory. Always use absolute paths (`/home/tangyi/...`) or
  `HOME=/home/tangyi` prefix when running terminal commands that reference user paths.
  This is NOT an Emacs issue — it affects all subprocesses under the Hermes profile.
