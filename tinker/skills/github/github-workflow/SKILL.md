---
name: github-workflow
description: Manage GitHub workflows — authentication setup, code review, issue management, PR lifecycle, and repository administration via gh CLI or git/curl REST API fallbacks. Load when working with any aspect of GitHub management.
version: 1.0.0
platforms: [linux, macos, windows]
---

# GitHub Workflow — Complete Guide

Class-level skill covering all GitHub management operations in a single workflow family. Each section below is self-contained and can be loaded independently for its domain.

## Shared Prerequisites & Authentication

### Auth Detection Chain (applies to ALL sections)

Always detect auth before proceeding:

```bash
# 1. Check ~/.hermes/.env first
if grep -q "^GITHUB_TOKEN=" ~/.hermes/.env 2>/dev/null; then
    GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | sed 's/^GITHUB_TOKEN=//')
# 2. Fall back to ~/.git-credentials
elif head -1 ~/.git-credentials 2>/dev/null | grep -q github; then
    GITHUB_TOKEN=$(sed -n 's|https://[^:]*:\([^@]*\)@.*|\1|p' ~/.git-credentials 2>/dev/null | head -1)
fi
```

### gh CLI Setup (Primary Interface)

```bash
gh auth login   # Interactive — select GitHub.com, paste token, https protocol
gh auth status  # Verify
```

**Without `gh`:** Use `curl` with `$GITHUB_TOKEN` for REST API calls. Every `gh` command below has a documented REST equivalent.

### Remote Extraction (shared utility)

```bash
REMOTE_URL=$(git remote get-url origin | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$REMOTE_URL" | cut -d/ -f1)
REPO=$(echo "$REMOTE_URL" | cut -d/ -f2)
```

## Section 1: Authentication Setup (github-auth)

### gh CLI Authentication

```bash
gh auth login --with-token <<< "$GITHUB_TOKEN"
gh auth status   # Verify
```

### Git Credential Helper

For operations outside `gh`:

```bash
git config --global credential.helper store          # Plain text (~/.git-credentials)
# OR for macOS keychain:
git config --global credential.helper osxkeychain
# OR for Linux (requires libsecret):
git config --global credential.helper libsecret
```

### SSH Key Setup

```bash
ssh-keygen -t ed25519 -C "hermes-agent"  # Generate
cat ~/.ssh/id_ed25519.pub                 # Copy to GitHub → Settings → SSH Keys
gh auth setup-git                         # Verify HTTPS+SSH pair
```

### Pitfalls & Troubleshooting

- Token must have `repo` scope for private repos, `read:org` for org operations
- `gh auth login --hostname=github.com` explicitly avoids GHES issues
- After changing tokens, run `gh auth setup-git` to re-sync git credential helper
- If `gh` complains about missing credentials, check both `~/.hermes/.env` AND `~/.git-credentials`

### REST API Equivalents (when gh unavailable)

| gh Command | curl Equivalent |
|---|---|
| `gh auth status` | `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/` |
| `gh pr view <num>` | `curl ... /repos/$OWNER/$REPO/pulls/<num>` |
| `gh issue list` | `curl ... /repos/$OWNER/$REPO/issues?state=all` |

## Section 2: Code Review (github-code-review)

### Local Diff Review (Pre-Submit)

```bash
# View current changes
git diff --stat HEAD~1          # File-level summary
git diff HEAD~1                 # Full diff
git log --oneline -5            # Recent commits
```

### PR Pull & Review via Remote Branch

```bash
gh pr checkout <PR_NUM>         # Fetch PR branch locally
git log --oneline -10           # See what the PR contains
git diff origin/main...HEAD     # Compare against base
```

### Structured Feedback Template (use for every review)

See `templates/review-template.md` or use inline format:

```markdown
## Code Review: PR #<N> — <Title>

### Critical 🔴
- [Issue]: [Explanation + suggested fix]

### Warnings ⚠️
- [Issue]: [Explanation]

### Suggestions 💡
- [Suggestion]: [Reasoning]

### Looks Good ✅
- [Positive observation]
```

### Review Commands

```bash
# Get PR diff for review
gh pr diff <num> > /tmp/pr-diff.diff

# Comment on PR
gh pr comment <num> --body "Review comments below:"

# Create a draft PR initially, switch to ready-for-review when complete
gh pr create --draft --title "..." --body "..."

# Add reviewers (only if you have admin access)
gh pr review --request-review @reviewer1,@reviewer2 <num>
```

### Code Review Pitfalls

- **Always check the base branch**: `git fetch origin && git diff origin/<base>...HEAD`
- **Commit format**: Conventional Commits — `type(scope): description`. Types: feat, fix, refactor, docs, test, ci, chore, perf. Wrap at 72 chars. (See `references/conventional-commits.md`)
- **Review comments should be actionable**: State what to change and why, not just "this is wrong"
- **Approval criteria**: No Critical or Warning items → Approve. Any Critical/Warning → Request Changes with specific feedback

## Section 3: Issue Management (github-issues)

### Create Issues

```bash
gh issue create \
  --title "Brief description" \
  --body "## Context\n...\n## Steps to Reproduce\n...\n## Expected vs Actual\n..." \
  --label "bug,needs-triage" \
  --assignee @username
```

### Search & Filter Issues

```bash
# By label
gh issue list --label "bug" --state open

# By assignee
gh issue list --assignee @me

# By author
gh issue list --author username

# Combined filters
gh issue search --label "critical" --state open --limit 20
```

### Issue Triage Workflow

1. **New**: Assign `needs-triage` label
2. **Assess**: Determine severity (P0/P1/P2/P3) and component
3. **Label**: Add appropriate labels (`bug`, `feature`, `docs`, `enhancement`)
4. **Assign**: Set assignee or self-assign for triage
5. **Link**: Add related issue/PR numbers in body if applicable

### Issue Templates

See `templates/bug-report.md` and `templates/feature-request.md`.

### Pitfalls & Common Patterns

- Always include reproduction steps in bug reports
- Link related PRs: "Related to #123" in issue body
- Use milestones for tracking group-level progress
- Close resolved issues with reference to fix: "Fixed by <PR>"

## Section 4: PR Lifecycle (github-pr-workflow)

### Branch Management

```bash
# Create feature branch from main
git checkout -b feature/<name> origin/main

# Or in a worktree (isolated workspace)
gh pr checkout <num>   # For existing PRs
```

### Opening a PR

```bash
# Commit with conventional format
git commit -m "feat(module): brief description of change"

# Push and create PR
git push -u origin feature/<name>
gh pr create \
  --title "feat(module): description" \
  --body "$(cat <<'EOF'
## Summary
- What changed (2-3 bullets)

## Test Plan
- [ ] Step 1: <verification>
- [ ] Step 2: <verification>

## Related
- Closes/Relates to #<issue>
EOF
)"
```

### PR Review & CI Flow

```bash
# Check CI status
gh pr checks <num>

# View check logs
gh run view --job <job-id> --log

# Request review changes
gh pr comment <num> --body "Changes requested: [specific feedback]"

# Merge after approval
gh pr merge <num> --squash --delete-branch
```

### Branch & Commit Conventions

- **Branch naming**: `feature/<name>`, `fix/<name>`, `docs/<name>`
- **Commit format**: `type(scope): description` (feat, fix, refactor, docs, test, ci, chore, perf)
- **PR titles**: Follow commit message convention
- **Merge strategies**: Squash (default), Rebase (for linear history), Merge commit (for traceability)

### PR Templates

See `templates/pr-body-feature.md` and `templates/pr-body-bugfix.md`.

### CI Troubleshooting

See `references/ci-troubleshooting.md` for common CI failures and fixes.

### Pitfalls & Best Practices

- Always `git fetch` and check base branch before starting work on existing PRs
- Push early, push often — small commits are easier to review
- CI must pass before requesting final review
- Delete feature branches after merge to keep repo clean
- For large PRs: create as Draft PR first → get feedback → mark ready for review

## Section 5: Repository Management (github-repo-management)

### Repo Creation & Cloning

```bash
# Create new repo
gh repo create <name> --public --description "Description"
gh repo create <name> --private --copy --remote origin-new

# Clone existing
git clone git@github.com:owner/repo.git
# OR with HTTPS (credential helper needed):
git clone https://github.com/owner/repo.git
```

### Forking & Managing Remotes

```bash
gh repo fork owner/repo --clone=true
# Add upstream remote to track original
git remote add upstream git@github.com:owner/repo.git
git fetch upstream
```

### Releases & Tags

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Create GitHub release
gh release create v1.0.0 \
  --title "Version 1.0.0" \
  --notes "Release notes..." \
  ./dist/*                    # Attach artifacts
```

### Secrets & Environment Configuration

```bash
# Repository secrets
gh secret set NAME --body "value"
gh secret list               # List (names only, not values)
gh secret delete NAME

# Environment secrets (requires environment to exist first)
gh secret set NAME --env production --body "value"
```

### Pitfalls & Security

- Never hardcode tokens in scripts — use `$GITHUB_TOKEN` or environment variables
- Use `--repo` flag for cross-repo operations: `gh run list --repo owner/repo`
- For fork-based workflows: always push to your fork, open PR from fork → upstream
- Rate limits: API calls are limited to 5000/hour for authenticated users
- Personal Access Tokens should have minimum required scope only

### GitHub API Cheatsheet

See `references/github-api-cheatsheet.md` for the comprehensive REST API command reference.

## Quick Reference: gh → REST Command Matrix

| Operation | gh CLI | curl REST API |
|---|---|---|
| List issues | `gh issue list` | `curl -H "Authorization: token $T" https://api.github.com/repos/$O/$R/issues` |
| Create PR | `gh pr create` | `POST /repos/$O/$R/pulls` |
| Get PR #n | `gh pr view n` | `GET /repos/$O/$R/pulls/n` |
| Merge PR | `gh pr merge n --squash` | `PATCH /repos/$O/$R/pulls/n/merge` |
| List commits | `gh api repos/$O/$R/commits` | `GET /repos/$O/$R/commits` |

## When to Use This Skill

Load when any task involves:
- Setting up GitHub authentication or credentials
- Reviewing or creating pull requests
- Managing issues (create, triage, search, assign)
- PR lifecycle (branching, committing, pushing, merging)
- Repository administration (clone, create, fork, releases, secrets)

## Support Files

All sibling skills have been merged into this umbrella. Each section corresponds to a former skill:

| Section | Former Skill | Status |
|---|---|---|
| Section 1 | `github-auth` | ✅ Merged |
| Section 2 | `github-code-review` | ✅ Merged |
| Section 3 | `github-issues` | ✅ Merged |
| Section 4 | `github-pr-workflow` | ✅ Merged |
| Section 5 | `github-repo-management` | ✅ Merged |

### References
- `references/ci-troubleshooting.md` — CI failure diagnostics from `github-pr-workflow`
- `references/conventional-commits.md` — Commit convention reference from `github-pr-workflow`
- `references/github-api-cheatsheet.md` — REST API command reference from `github-repo-management`
- `references/review-output-template.md` — Review output format from `github-code-review`

### Templates
- `templates/bug-report.md` — Issue template for bugs (from `github-issues`)
- `templates/feature-request.md` — Issue template for features (from `github-issues`)
- `templates/pr-body-bugfix.md` — PR body template for bug fixes (from `github-pr-workflow`)
- `templates/pr-body-feature.md` — PR body template for features (from `github-pr-workflow`)

### Scripts
- `scripts/gh-env.sh` — GitHub env token extraction helper from `github-auth`
