# Karpathy Principles — Tinker Profile Injection

## Changes to SOUL.md

Two additions to the Conventions section:

1. **Present alternatives** — appended "If multiple valid approaches exist,
   present them — don't pick silently" to the first convention bullet
   (read AGENTS.md before changes).

2. **Surgical changes** — new bullet with tinker-specific examples:
   - Don't reformat adjacent config.org blocks or "improve" unrelated
     use-package declarations when editing Emacs config
   - Don't restyle the entire script when fixing one line
   - Match existing style even if you'd do it differently

These address the primary Karpathy gaps for tinker's domains (config
files, scripts, system admin) where collateral scope creep is common.
