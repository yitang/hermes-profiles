# GitHub Issue as Proto-Spec

## The Pattern

When a GitHub issue already contains a clear feature description (what to build, why, how), it's serving as an informal spec. The project convention is `docs/spec-YYYY-MM-DD-*.md` — flat files in the repo, versioned alongside the code. GitHub issues are external and don't follow this convention.

## Conversion Workflow

1. Read the issue body — if it has enough detail to serve as requirements, proceed
2. Write a proper `docs/spec-YYYY-MM-DD-<topic>.md` with the standard sections (Scope, Requirements, Decisions, Non-goals)
3. Commit the spec to master
4. Close the issue with a comment referencing the spec file path: "Replaced by spec at docs/spec-YYYY-MM-DD-<topic>.md"
5. Proceed with the normal pipeline: worktree → plan → execute

## When to Skip Conversion

If the issue is a genuine bug report (not a feature spec), use the `bug-reporting` skill's flat-file format (`docs/bugs-YYYY-MM-DD-<topic>.md`) instead. Issues that are questions, discussions, or placeholders don't need conversion — just close them.

## Why

- Specs live in the repo, get versioned, and survive repo moves
- GitHub issues can be deleted, repos can be archived — files are permanent
- The `docs/` convention means any session can find the spec without querying the GitHub API
- The pipeline (brainstorming → spec → plan) assumes files in `docs/`, not external URLs
