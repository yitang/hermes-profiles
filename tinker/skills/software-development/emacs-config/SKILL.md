---
name: emacs-config
description: Understand the user's Emacs 30.2 configuration — file layout, config.org vs emacs_config.org split, tangling, loading order, custom functions, and keybindings.
---

# Emacs Configuration

## Invocation

Emacs 30.2 is compiled and installed at `~/bin/emacs30.2/`. Always invoke with:

```bash
~/bin/emacs30.2/bin/emacs --init-directory=~/.config/emacs/emacs.d_30.2
```

The init dir overrides `user-emacs-directory` to a dedicated path. Without this flag,
packages install to `~/.emacs.d/elpa/` instead of the correct path.

## File Layout

```
~/.config/emacs/emacs.d_30.2/
├── config.org              ← PUBLIC config (source of truth, git-tracked)
├── custom.el               ← Customize-saved settings (auto-generated)
├── lisp/                   ← Tangled .el files from config.org
│   ├── general.el
│   ├── org-mode.el
│   ├── refile.el
│   ├── scripting.el
│   └── ... (10+ files)
├── elpa/                   ← Installed packages
│   ├── org-roam-*/         ← Org-roam v2
│   ├── transient-*/        ← Transient menus
│   ├── consult-*/          ← Completion
│   └── ...                 ← Other MELPA packages
├── notes/                  ← Org-roam documentation notes
└── load_config.el          ← Loads all lisp/*.el files

~/matrix/tools/dotfiles/
├── .emacs                  ← Main init file (symlinked to ~/.emacs)
├── emacs_config.org        ← PRIVATE config (not in public git)
└── emacs_config.el         ← Tangled from emacs_config.org

~/para/1_projects/org-roam-anywhere/
└── yt-matrix.el            ← Matrix setup (loaded explicitly)
```

## Loading Order

`~/.emacs` orchestrates everything in this order:

1. **`custom.el`** — user-customized settings (loaded automatically by Emacs)
2. **Package system** — `(package-initialize)` adds MELPA, installs packages
3. **`load_config.el`** — loads all `lisp/*.el` files tangled from `config.org`
4. **`emacs_config.el`** — private config tangled from `emacs_config.org`
5. **`yt/execute-src-org-file`** — (was old matrix-setup, now disabled)
6. **`~/para/emacs-para.el`** — PARA inbox capture (C-c c p)
7. **`my-org-roam-note-type.el`** — note type tags (fleeting/literature/permanent)
8. **`yt-matrix.el` via `(yt/meta-enable)`** — matrix setup, roam dispatch, capture templates

### Important

`org-capture-templates` is built incrementally across steps 3-8:
- `config.org` → `lisp/general.el` uses `setq` (replaces)
- `emacs_config.org` → `emacs_config.el` uses `setq` (replaces again)
- `yt-matrix.el` uses `append` (additive)

## Config Split: config.org vs emacs_config.org

| Aspect | config.org | emacs_config.org |
|--------|-----------|-----------------|
| Git repo | `yitang/.emacs.d` (public) | `yitang/dotfiles` (private) |
| Content | Packages, keybinds, org, org-roam, programming modes | Personal capture templates: t/n (PARA inbox), jD (daily plan via beorg), R (reading) |
| Sections | ~80 sections, ~4300 lines | 3 sections, ~140 lines |
| Tangle target | `lisp/*.el` (10+ files) | `emacs_config.el` (single file) |

The split was originally motivated by keeping personal captures (diary paths, encrypted notes)
out of the public `.emacs.d` repo. After simplification, little sensitive content remains,
but the separation is kept for now.

## Keybindings

| Keybinding | Command | Purpose |
|-----------|---------|---------|
| `C-c c` | `org-capture` | Capture dispatch: t (inbox TODO), n (inbox note), jD (daily plan), r* (roam), R* (reading) |
| `C-c m` | `yt/matrix3` | Matrix domain selection → action menu |
| `C-c r` | `yt/meta--roam-dispatch` | Roam dispatch — pick domain → `org-roam-node-find` |
| `C-c n t` | `my/org-roam-set-note-type` | Set note type tag on current roam buffer (literature/fleeting/permanent) |
| `C-c n f` | `org-roam-node-find` | Org-roam browse (works with `.dir-locals.el` scoped to current domain) |
| `C-c n i` | `org-roam-node-insert` | Insert roam link |
| `C-c n l` | `org-roam-buffer-toggle` | Toggle backlinks buffer |
| `C-c n d` | `org-roam-dailies-map` | Daily notes menu |

## Additional Files Loaded From ~/.emacs

**`~/.hermes/profiles/tinker/workspace/my-org-roam-note-type.el`** — note type tag manager.
Defines `my/org-roam-set-note-type` which prompts for `:literature:`, `:fleeting:`, or
`:permanent:` and sets the buffer's FILETAGS. Mutually exclusive — picking one removes
the others. Loaded via `(load ...)` at the end of `.emacs`. Binds `C-c n t` in
`org-mode-map` via `with-eval-after-load 'org-roam`.

## Matrix Setup (yt-matrix.el)

All domain data lives in `yt/meta-projects` — an alist of 6 domains (ds, finance, health,
hobbies, learning, tools) + 4 reflect projects.

From `C-c m`:
- Pick a domain → action menu: TODO, Note, Journal, Roam, Dired, Agenda
- **Roam** calls `(let ((org-roam-directory ...)) (org-roam-node-find))` — opens roam in that vault
- **Dired** opens the project directory

From `C-c r`:
- Prompts "Roam to domain:" → opens `org-roam-node-find` in that vault

From `C-c c` `r`:
- Sub-keys `rd`, `rf`, `rh`, `rH`, `rl`, `rt` — per-domain roam capture
- Each uses a `(function ...)` lambda that returns `(current-buffer)` to satisfy org-capture

## Per-Domain Org-Roam Vaults

Each domain under `~/matrix/` has a `.dir-locals.el` at the domain root that wires
`org-roam-directory` to `meta-<domain>/notes/`. The pattern uses `locate-dominating-file`
to walk UP from the current file. This means editing ANY file under `~/matrix/tools/`
activates the tools vault — you don't need to be inside `meta-tools/`.

Vaults are NEVER set globally. `C-c n f` from outside a domain tree won't work unless
you let-bind `org-roam-directory`.

## Batch Testing

```bash
HOME=/home/tangyi /home/tangyi/bin/emacs30.2/bin/emacs \
  --init-directory=~/.config/emacs/emacs.d_30.2 \
  --batch -l ~/.emacs \
  --eval "(progn (load-file \"~/para/1_projects/org-roam-anywhere/yt-matrix.el\") (yt/meta-enable) (message \"OK\"))"
```

Always pass `-l ~/.emacs` when testing code that depends on packages (transient, org-roam)
because batch mode doesn't load the user config by default.

## Pitfalls

- **Package directory** — `package-user-dir` is computed from `user-emacs-directory` BEFORE
  `.emacs` runs. Setting `user-emacs-directory` inside the init file is too late. Use
  `--init-directory` flag or the correct default path.
- **`config.org` vs `emacs_config.org` `setq`** — both use `setq` for `org-capture-templates`.
  The later one wins. Only `yt-matrix.el` uses `append`. If templates disappear, check the
  load order.
- **Org-roam expansions in org-capture** — `${slug}` and `${title}` only work in
  `org-roam-capture-templates`. In regular `org-capture-templates` they're literal text.
- **`(function ...)` target** — org-capture calls function targets with NO arguments.
  To parameterize, use closure (lambda capturing the needed value) or a state variable.
- **`read-multiple-choice`** returns `(CHAR . LABEL-STRING)`, not the original alist entry.
  Always use `(assoc (char-to-string (car result)) data)` to look up.
- **`cl-loop` in `transient-define-prefix`** — triggers eager macro-expansion errors.
  Use `eval` + backquote to build transients dynamically at runtime.
