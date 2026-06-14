# Claude Code Skill Authoring Best Practices (Source Summary)

## Source: Anthropic Documentation (Claude Code v2.x)

### Skills vs Slash Commands

| Aspect | Skills | Slash Commands |
|--------|--------|----------------|
| Invocation | Auto-invoked by natural language | Manually invoked with `/command` |
| Trigger | Natural language matching user task description | Exact command name |
| File Location | `.claude/skills/` or `~/.claude/skills/` | `.claude/commands/` or `~/.claude/commands/` |
| Use Case | Recurring task patterns ("when reviewing auth...") | User-initiated workflows (`/deploy production`) |

### Skill Design Principles

- **Natural Language Trigger:** Write so the model can recognize when to apply it without explicit invocation.
- **Task-Specific:** Each skill should cover one coherent pattern, not be a general guide.
- **Structured Content:** Clear heading, ordered steps, specific examples over vague advice.
- **Progressive Disclosure Model (Hermes-specific):** Only name + description loaded per turn; full content reads on-demand.

### Example Skill Trigger Pattern

```markdown
# database-migration.md
When asked to create or modify database migrations:
1. Use Alembic for migration generation
2. Always create a rollback function
3. Test migrations against a local database copy
```

The skill activates when the model sees "create a migration" or "modify the schema" — it matches on task intent, not exact keywords.

### Related Files in `.claude/` Directory

- `CLAUDE.md` — Global project memory (always loaded)
- `.claude/rules/*.md` — Modular rules (loaded when specified, like skills)
- `.claude/agents/` — Subagent definitions
- `.claude/skills/` — Auto-invoked skill guides
- `.claude/commands/` — Manual slash commands
- `.claude/settings.json` — Project-level configuration
