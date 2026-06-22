# Stub Detection

A reference for identifying stub notes in vault audits. Created [2026-06-19].

## Signs of a stub

- <15 content words (excluding PROPERTIES drawers and headings)
- Just a flag/command name with no explanation: "use the -f"
- A bare link with no connecting phrase: "see [[id:...][note]]"
- Title says more than the body: title = "Bash Test File Exists", body = "use -f"
- Could be replaced entirely by a `:ROAM_ALIASES:` on another note

## Real examples from meta-tools vault (June 2026)

| File | Body | Verdict |
|------|------|---------|
| `bash_test_file_exists` | "use the -f, see [[id:...][Bash if-else]]" | Stub — merged into if-else note |
| `bash_test_empty_string` | "use the -z" + code block example | Stub — merged into if-else note |

## What to recommend

1. **Expand** — if the concept deserves its own note (it's non-trivial and
   not covered elsewhere), write 3-5 sentences explaining the principle.
2. **Merge** — if the content is an aspect of a larger note (e.g. "-f test"
   is just one option in `bash_if_else`), fold it in. Add the old title
   as `:ROAM_ALIASES:` on the parent so org-roam search still resolves it.
3. **Delete** — if neither, it's clutter.

The user decides; the agent flags.
