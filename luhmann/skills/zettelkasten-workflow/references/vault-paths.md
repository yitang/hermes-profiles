# Vault Paths (discovered 2026-06-14)

All vaults live under `~/matrix/{domain}/meta-{domain}/notes/`. Each is
a self-contained git repo.

| Repo path | Notes count | Git remote |
|---|---|---|
| `~/matrix/ds/meta-ds/notes` | ~129 org | local only |
| `~/matrix/finance/meta-finance/notes` | 2 org | local only |
| `~/matrix/health/meta-health/notes` | 7 org | local only |
| `~/matrix/hobbies/meta-hobbies/notes` | ~176 org | local only |
| `~/matrix/learning/meta-learning/notes` | ~26 org | local only |
| `~/matrix/tools/meta-tools/notes` | ~169 org | local only |

**Total:** 6 repos, ~500+ org notes.

## Quick discovery command

```bash
for d in /home/tangyi/matrix/*/meta-*/notes; do
  [ -d "$d" ] || continue
  count=$(ls "$d"/*.org 2>/dev/null | wc -l)
  printf "%-50s %s\n" "${d#/home/tangyi/}" "$count notes"
done
```

## Note for Hermes agents

`$HOME` is overridden to `/home/tangyi/.hermes/profiles/luhmann/home/`
in the Hermes profile. Always use the explicit `/home/tangyi/` path
when walking these vaults, not `~/` or `$HOME/`.
