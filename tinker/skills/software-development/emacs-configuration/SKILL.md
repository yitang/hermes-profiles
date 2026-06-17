---
name: emacs-configuration
description: Work with Yi Tang's Emacs setup — init directory, config split, tangling, loading order, package dir, keybindings, and org-roam integration. Load this skill when any task involves editing, understanding, or running the Emacs configuration.
---

# Emacs Configuration

## Invocation

```bash
~/bin/emacs30.2/bin/emacs --init-directory=~/.config/emacs/emacs.d_30.2
```

The `--init-directory` flag is **required** — without it, Emacs uses `~/.emacs.d/` which has the wrong package directory and config files. This flag sets both:
- `user-emacs-directory` → `~/.config/emacs/emacs.d_30.2/`
- `package-user-dir` → `~/.config/emacs/emacs.d_30.2/elpa/`

Setting `user-emacs-directory` from inside `.emacs` is **too late** — `package-initialize` fires before init runs, so the package directory gets locked in at the default.

## Config File Split

| File | Content | Tangles to |
|------|---------|------------|
| `~/matrix/tools/.emacs.d/config.org` | Public config — package setup, org-roam, UI, helpers, keybindings | `lisp/*.el` (via `load_config.el`) |
| `~/matrix/tools/dotfiles/emacs_config.org` | Private config — personal capture templates, journaling, reading notes, vocabulary | `emacs_config.el` |
| `~/para/1_projects/org-roam-anywhere/yt-matrix.el` | Matrix setup — domain menus, org-roam dispatch, capture/agenda generators | Direct load |

Loading order in `~/.emacs`:

```
.emacs
├── load "custom.el"
├── (package-initialize)           ← auto-run before init, but re-called here
├── (require 'transient)
├── load-file "load_config.el"     ← loads config.org tangled lisp files
├── load-file "emacs_config.el"    ← private config
├── yt/execute-src-org-file ...    ← OLD matrix-setup (now disabled)
├── load "emacs-para.el"           ← PARA inbox/agenda
├── load "my-org-roam-note-type.el" ← note type tagging
└── load "yt-matrix.el"            ← NEW matrix setup (manual, or via yt/meta-enable)
```

## Tangling

Both `.org` config files use `:tangle` headers. After editing the `.org` source, re-tangle:

```bash
emacs --batch --eval "(progn (require 'org) (find-file \"path/to/config.org\") (org-babel-tangle))"
```

Or within Emacs: `C-c C-v t` on the source file.

Key property in `emacs_config.org` header:
```org
#+PROPERTY: header-args :tangle emacs_config.el
```

Run `M-x yt/meta-enable RET` after loading yt-matrix.el to activate bindings.

## Keybindings

| Binding | Command | Purpose |
|---------|---------|---------|
| `C-c c` | `org-capture` | Capture dispatch: t (inbox TODO), n (inbox note), jD (daily plan via beorg), r* (roam), R* (reading) |
| `C-c m` | `yt/matrix3` | Matrix domain selection → action menu: TODO, Note, Journal, Roam, Dired, Agenda |
| `C-c r` | `yt/meta--roam-dispatch` | Direct roam dispatch: pick domain → org-roam-node-find |
| `C-c n t` | `my/org-roam-set-note-type` | Set note type tag on current roam buffer (literature/fleeting/permanent) |
| `C-c n f` | `org-roam-node-find` | Standard roam find (works if .dir-locals.el context active) |
| `C-c n i` | `org-roam-node-insert` | Insert roam link |
| `C-c n l` | `org-roam-buffer-toggle` | Toggle backlinks buffer |
| `C-c n d` | `org-roam-dailies-map` | Daily notes menu |

## Config Split Detail

| File | Content | Git repo | Tangles to |
|------|---------|----------|------------|
| `config.org` (~/.config/emacs/emacs.d_30.2/) | Public config — packages, keybinds, org-roam, programming modes (~80 sections, ~4300 lines) | yitang/.emacs.d (public) | `lisp/*.el` (10+ files via load_config.el) |
| `emacs_config.org` (~/matrix/tools/dotfiles/) | Private config — personal capture templates, journaling, reading notes (~140 lines, 3 sections) | yitang/dotfiles (private) | `emacs_config.el` (single file) |

Split originally motivated by keeping diary paths and encrypted notes out of public repo. Kept for convention now.

## Org-Roam Integration

Org-roam vaults are per-domain, set by `.dir-locals.el` at domain roots:
`~/matrix/{ds,finance,health,hobbies,learning,tools}/.dir-locals.el`

**Pattern for per-vault roam capture:**
```elisp
(let ((org-roam-directory (expand-file-name "notes/" meta-dir))
      (org-roam-db-location (expand-file-name "org-roam.db" (expand-file-name "notes/" meta-dir))))
  (org-roam-node-find))
```

**Return buffer after roam-node-find** (for use with org-capture `(function ...)` target):
```elisp
(defun my-roam-capture (meta-dir)
  (let ((org-roam-directory (expand-file-name "notes/" meta-dir)) ...)
    (org-roam-node-find))
  (current-buffer))
```

## Package Installation

Packages land in `~/.config/emacs/emacs.d_30.2/elpa/<package>-<version>/`.
The `--init-directory` flag controls this — without it, packages go to `~/.emacs.d/elpa/` regardless of anything you set in `.emacs`.

## Matrix Setup (yt-matrix.el)

`~/para/1_projects/org-roam-anywhere/yt-matrix.el`

- Fully data-driven. Add/remove domains by editing `yt/meta-projects` alist only.
- Transient menus built dynamically with `eval` + backquote pattern:
  ```elisp
  (eval
   `(transient-define-prefix yt/matrix3 ()
      "Quick access."
      ["Matrix"
       ,(vconcat
         (cl-loop for d in yt/meta-projects
                  collect
                  `(,(nth 0 d) ,(nth 1 d)
                    (lambda () (interactive) (yt/meta--select-by-key ,(nth 0 d))))))]]))
  ```
  `cl-loop` inside `transient-define-prefix` fails due to eager macro-expansion.
  The `eval` + backquote defers expansion to runtime. `vconcat` converts list to vector.

- Context passed between transients via `yt/meta--cur` state variable pattern.
- `yt/meta--select-by-key` is a SINGLE generic selector — no per-domain macros needed.
- Lambda closures in the capture template generator capture `domain-key` at generation time, replacing 6 separate named functions.
- `(defvar org-roam-directory)` / `(defvar org-roam-db-location)` forward declarations needed at file top, before any `let` binds them — prevents "Defining as dynamic an already lexical var" byte-compile error.

## Testing Config Changes

Batch-mode verification:
```bash
HOME=/home/tangyi /home/tangyi/bin/emacs30.2/bin/emacs \
  --init-directory=~/.config/emacs/emacs.d_30.2 \
  --batch -l ~/.emacs \
  --eval "(progn (load-file \"~/para/1_projects/org-roam-anywhere/yt-matrix.el\") (yt/meta-enable) (message \"OK\"))"
```

Use `-l ~/.emacs` when the code depends on packages (transient, org-roam, org-capture) — batch mode doesn't load user config by default.

## Pitfalls

- `org-roam-directory` is NEVER set globally. `C-c n f` from a non-domain buffer won't work.
- Domain `.dir-locals.el` only activates when you open a file inside that domain tree.
- `read-multiple-choice` returns `(CHAR . LABEL-STRING)`, NOT the original alist entry — always look up with `assoc` + `char-to-string`.
- Setting `user-emacs-directory` inside `.emacs` is too late to affect package directory.
- After editing config.org or emacs_config.org, re-tangle to sync .el files.
- **`${slug}` and `${title}`** only work in `org-roam-capture-templates`. In regular `org-capture-templates` they're literal text — not expanded.
- **Both `config.org` → `lisp/general.el` AND `emacs_config.org` → `emacs_config.el` use `setq` for `org-capture-templates`**. The later one wins. Only `yt-matrix.el` uses `append`. If templates disappear, check load order.
- `(function ...)` capture targets receive NO arguments from org-capture. To parameterize, use closure (lambda) or a state variable.
- **`(defvar org-roam-directory)` / `(defvar org-roam-db-location)`** forward declarations needed at file top before any `let` binds them — prevents "Defining as dynamic an already lexical var" byte-compile error.
- **Batch testing**: Always pass `-l ~/.emacs` when testing code that depends on packages (transient, org-roam) because batch mode doesn't load user config by default. For non-matrix tests, run without `(yt/meta-enable)`:
  ```bash
  HOME=/home/tangyi ~/bin/emacs30.2/bin/emacs \
    --init-directory=~/.config/emacs/emacs.d_30.2 \
    --batch -l ~/.emacs \
    --eval "(message \"OK\")"
  ```
