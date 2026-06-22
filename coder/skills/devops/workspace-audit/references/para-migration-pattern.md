# PARA Migration — Moving from Domain-Based to Purpose-Based Organization

When a user has a domain-structured workspace (like `~/matrix/` with `ds/`, `finance/`, `health/`, etc.) and wants to migrate to PARA, use this mapping approach.

## Decision Framework

### What moves where:

| Source pattern | PARA destination | Why |
|---------------|-----------------|-----|
| Completed projects (no future plan) | `7_archive/` or keep as read-only in source location | Done work stays as reference, not live workspace |
| Notes + learning materials from any repo | `3_resources/<topic>/` | Knowledge is purpose-based, not domain-based |
| Active ongoing passion/hobby log | `2_areas/<name>/` (keep as git repo) | Ongoing responsibility, no end date |
| Uncommitted diary/reflection writing | `2_areas/diary/` (plain org files, no git) | Personal reflection, doesn't need version control |
| Active research under exploration | `0_ideas/<name>/` | Incomplete, not yet a committed build |

### Key rules from practice:

1. **Use the source domain directory as the archive**, not PARA. The old structure becomes a read-only historical reference. PARA is only for what you *actively work on now*.
2. **Extract content, don't move entire repos.** Copy `.org`/`.md` files into PARA's `3_resources/`, preserving topic-based subdirectories. Leave original repos intact in the source until user confirms extraction.
3. **Merge functionally identical repos** before migration (e.g., `.emacs.d` + `dotfiles` → one config repo). Do this *before* extracting notes — it simplifies what stays behind.
4. **Keep git history for active hobby/project logs** even after moving into PARA. A 362-commit DIY log is valuable versioned history.
5. **Diaries and personal writing** — plain org files, no git. They're personal, not shared infrastructure.

## Execution Order (tested pattern)

```
1. Merge overlapping repos (.emacs.d → dotfiles)   ← highest value first
2. Extract notes to 3_resources/                     ← copy, don't move
3. Move active repos into PARA structure             ← git mv + reconfigure remote
4. Write archive README explaining what's behind     ← preserves traceability
```

## Copy vs Move Decision

**Default to COPY first.** Migration is destructive in one direction only — you can't undo a move that corrupted a git history. After user verifies PARA extraction is complete and correct, then do the move (or leave originals as read-only archive).

From the 2026-06-08 migration: user chose this approach explicitly — "use matrix as archive for historical projects."
