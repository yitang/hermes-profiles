---
name: github
description: "Interact with GitHub repositories via gh CLI or git + curl: authentication, repo management, PR workflow, code review, issues, and codebase analysis."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, gh-CLI, Git, PR, Issues, Code-Review, Authentication, Repository]
---

# GitHub Workflow

Interact with GitHub repositories using the `gh` CLI (preferred) or `git` + `curl` (fallback). Covers authentication, repo management, PR lifecycle, code review, issue management, and codebase analysis.

## When to Use

- User asks to interact with a GitHub repository
- Need to create/clone/fork repos, manage PRs, write issues
- Code review of diffs or PRs
- CI/troubleshooting involving GitHub Actions

---

## Labeled Subsections: GitHub Operations

### 1. Authentication (github-auth)

**Detection flow — run first when user asks about GitHub:**
```bash
git --version && gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
```

**Decision tree:**
1. `gh auth status` shows authenticated → use `gh` for everything
2. `gh` installed but not authenticated → use gh CLI login or token
3. `gh` not installed → use git-only HTTPS with PAT (no sudo needed)

#### Git-Only Method: HTTPS with Personal Access Token
```bash
git config --global credential.helper store
# Prompt triggers — enter username + PAT (not GitHub password)
git ls-remote https://github.com/<username>/<repo>.git
git config --global user.name "Name" && git config --global user.email "email@example.com"
```

#### SSH Key Method
```bash
ssh-keygen -t ed25519 -C "email@example.com" -f ~/.ssh/id_ed25519 -N ""
# Add public key at https://github.com/settings/keys
ssh -T git@github.com  # verify: "Hi <username>! You've successfully authenticated..."
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

#### gh CLI Method
```bash
gh auth login              # browser OAuth (desktop)
# OR token-based: echo "<TOKEN>" | gh auth login --with-token
gh auth setup-git           # configure git credentials through gh
gh auth status             # verify
```

#### Token Extraction Fallback
```bash
# Extract from git credential store
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

### 2. Repository Management (github-repo-management)

#### Clone, Create, Fork
```bash
gh repo clone owner/repo-name          # Clone
gh repo create my-project --public     # Create + clone
gh repo fork owner/repo-name           # Fork
```

From local directory: `cd /path/to/proj && gh repo create name --source . --public --push`

#### Repo Settings & Info
```bash
gh repo view owner/repo                # Details
gh repo edit --description "Updated"   # Edit settings
gh repo list --limit 20                # List repos
gh search repos "machine learning"     # Search repos
```

#### Releases
```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release list                       # List releases
gh release download v1.0.0            # Download assets
```

#### GitHub Actions / CI
```bash
gh workflow list && gh run list --limit 10      # List workflows + runs
gh run view <RUN_ID>                            # View run details
gh run rerun <RUN_ID>                           # Re-run
gh workflow run deploy.yml -f env=staging       # Trigger manual dispatch
```

#### Secrets (GitHub Actions)
```bash
gh secret set API_KEY --body "value"    # Set
gh secret list                          # List names only
gh secret delete API_KEY                # Remove
# curl fallback requires encryption with repo public key via PyNaCl
```

### 3. PR Workflow (github-pr-workflow)

#### Branch & PR Lifecycle
```bash
# Create branch from main
git checkout -b feature/my-branch main

# Make changes, commit
git add . && git commit -m "feat: add new feature"

# Push and create PR
git push -u origin feature/my-branch
gh pr create --title "feat: add new feature" \
  --body "@$(cat templates/pr-body-feature.md)" \
  --base main --head feature/my-branch
```

#### Conventional Commits
Use `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:` prefixes for commit messages. Use `--revert` for automatic revert commits. See `references/conventional-commits.md` for full grammar.

#### PR Body Templates
- `templates/pr-body-feature.md` — Feature PR template (what changed, why, testing)
- `templates/pr-body-bugfix.md` — Bug fix template (issue reference, root cause, fix)

#### CI Troubleshooting
See `references/ci-troubleshooting.md` for common CI failure patterns: flaky tests, timeout issues, environment variable misconfiguration, and branch protection failures.

### 4. Code Review (github-code-review)

#### Quick PR Review
```bash
# View diff via gh
gh pr diff 42 | head -200

# Deep review in a clean worktree
gh pr checkout 42
# Then analyze the diff manually or with coding tools
```

#### Review Output Format
Follow structured format: `Overall Assessment → Critical Issues → Suggestions → Nitpicks`. See `references/review-output-template.md` for the full template.

### 5. Issue Management (github-issues)

#### Create & Manage Issues
```bash
# Create issue
gh issue create --title "Bug: description" --body "@$(cat templates/bug-report.md)"

# Create feature request
gh issue create --title "Feature: description" --body "@$(cat templates/feature-request.md)"

# List and search issues
gh issue list --state open
gh search issues "label:bug is:open" --limit 20
```

#### Issue Templates
- `templates/bug-report.md` — Bug report template (reproduction steps, expected/actual)
- `templates/feature-request.md` — Feature request template (use case, acceptance criteria)

### 6. Codebase Analysis (codebase-inspection)

Analyze repositories with `pygount` for LOC, language breakdown, and code-vs-comment ratios:
```bash
pip install pygount
pygount --format=summary --folders-to-skip=".git,node_modules,venv" .
# JSON output: pygount --format=json .
```

Always exclude `.git`, `node_modules`, `venv` to avoid crawling dependencies.

---

## Quick Reference: Common Commands

| Action | gh CLI | Fallback (git + curl) |
|--------|--------|----------------------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create PR | `gh pr create --title "..."` | Push branch + API call to /pulls |
| View PR | `gh pr view 42` | `curl .../repos/o/r/pulls/42` |
| Review diff | `gh pr diff 42` | Clone + `git diff` |
| List issues | `gh issue list --state open` | `curl .../repos/o/r/issues?state=open` |
| Create release | `gh release create v1.0` | API POST /releases |
| Check CI | `gh run list --limit 10` | `curl .../actions/runs` |

## Pitfalls

- **gh vs git credential mismatch:** Setting up gh auth doesn't automatically configure git credentials in all cases — always verify with `git push` after setup.
- **Branch protection blocks force-pushes:** Don't force-push to protected branches unless you've temporarily disabled protection or have admin rights.
- **PR closed + merged = no editing:** Merged PRs can't be edited through the GitHub UI; you'll need to open a new PR for corrections.
- **Rate limits without auth:** Unauthenticated API calls are limited to 60/hour. Always authenticate first.

## Related Skills

- **github-pr-workflow** — Labeled subsection above (PR lifecycle)
- **github-code-review** — Labeled subsection above (review patterns)