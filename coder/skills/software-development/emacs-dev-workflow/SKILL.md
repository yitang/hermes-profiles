---
name: emacs-dev-workflow
description: "Patch, extend, and contribute Emacs packages in local dev repos. Covers shadowed ELPA packages, byte-compilation, checkdoc, commit conventions, and PR submission patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Emacs Development Workflow

Use when the user wants to patch, extend, or contribute code to an Emacs package — especially when the package exists both in ELPA (installed) AND in a local git repo that shadows it via `:load-path`.

## Pattern: Shadowed ELPA Package

**CRITICAL: Always check if the package is shadowed before editing.** If the user's init has a `:load-path` pointing to a local directory for an installed package, that local copy takes precedence — ELPA gets loaded as fallback. Editing the ELPA copy (e.g. `~/.emacs.d/elpa/foo-VERSION/`) means patches vanish on next `M-x package-update`.

**How to detect:**
1. Search init.el (or config.org) for `:load-path` or `(require 'PACKAGE)` near a local directory path
2. Look for `use-package PACKAGE :load-path "/some/path" :ensure t` — the `:load-path` shadows ELPA
3. If present, ALWAYS edit files in the `:load-path` target, NOT the ELPA directory

**User's common pattern:**
```elisp
(use-package agent-shell
  :load-path "/home/tangyi/server-files/local_llm/agent-shell"
  :ensure t          ; fallback only — load-path shadows this
  :demand t)
```

## Patching Workflow (Step-by-Step)

1. **Identify the target file** — find the relevant `.el` in the local repo, NOT the ELPA copy
2. **Read the existing code** to understand the pattern used by similar features
3. **Apply changes with `patch` tool** (fuzzy matching, auto-syntax check)
4. **Byte-compile** from within the package's directory:
   ```bash
   emacs -Q --batch \
     -L /path/to/package/dir \
     -L /path/to/deps/shell-maker \
     -L /path/to/deps/acp \
     -f batch-byte-compile target.elc 2>&1
   ```
   Replace `target.elc` with the `.el` source filename — byte-compile will generate/rename the `.elc`.
5. **Fix any compilation warnings** (docstring width, void functions, etc.)
6. **Commit in the local repo:**
   ```bash
   git add target.el
   git commit -m "type: subject

   Body explaining what and why."
   ```
7. **Do NOT edit ELPA directories** unless the user explicitly has no local dev copy

## Adding Missing Features to Agent Integrations (agent-shell pattern)

When adding a feature that exists for other agents (claude, openai, opencode, etc.) but is missing in one:

1. **Check existing agent files** — grep or read `agent-shell-anthropic.el`, `agent-shell-openai.el`, etc. to find the established pattern
2. Mirror the exact parameter name and wire format (e.g., `:default-session-mode-id (lambda () variable-name)`)
3. Add a `defcustom` with appropriate `:type`, `:group 'agent-shell`
4. The lambda form `(lambda () VAR)` is the standard pattern — avoids eval at load time

Common missing patterns in agent files:
- `-default-session-mode-id` (ACP session mode for edit approval)
- `-acp-command` (custom command path)
- `-environment` (env vars for the subprocess)

## Commit Convention

Follow the project's conventions. For agent-shell and similar projects:

```
type: concise subject line

Optional body explaining what changed and why.
```

Types: `fix:` (bug), `feat:` (new feature), `refactor:` (restructure), `docs:` (documentation)

## Byte-Compilation

Emacs packages should be byte-compiled before committing or testing. Use `batch-byte-compile`:

```bash
emacs -Q --batch -L /pkg/dir -f batch-byte-compile file.el
```

If dependencies aren't in the package dir, add `-L` for each dependency directory:
```bash
emacs -Q --batch \
  -L . -L /deps/shell-maker -L /deps/acp \
  -f batch-byte-compile agent-shell-hermes.el
```

Watch for docstring width warnings (>80 chars) — keep docstrings within the limit.

## Checkdoc

Before committing, run `M-x checkdoc` on the edited file to catch:
- Docstring formatting issues
- Missing periods
- Inconsistent capitalization
- Word choice problems

## Contributing Upstream (PR Submission)

When patching a package with an upstream repo (e.g., xenodium/agent-shell):
1. Commit locally first
2. Push to your fork/branch
3. Create PR following CONTRIBUTING.org guidelines
4. The maintainer prefers human-written PR descriptions, not AI-generated ones
5. Run `checkdoc` + byte-compile before pushing (per CONTRIBUTING)
