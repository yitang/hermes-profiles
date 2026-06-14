---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Structural/architectural audits — data-first approach
When grilling on a classification system (repo matrices, project categories, directory structures), **show hard numbers before asking conceptual questions**:
- List last commit dates for all items to establish activity tiers (active / semi-active / dormant)
- Count repos per category to show distribution imbalance
- Present findings in a simple table format so the user can see patterns at a glance

This grounds the conversation in reality and makes abstract structural questions concrete. Users will naturally propose reorganization once they see that 60% of their repos are dormant — you don't need to convince them.

## Challenge the classification principle itself
Don't just ask "which repos should move?" Ask: **what original principle governed this grouping, and does it still hold?** If items in a category are wildly heterogeneous (e.g., an active knowledge base alongside dead scripts and orphaned code), the category definition itself may be broken. Present that observation directly: "meta-tools is your most-active repo right now — but you put it in a directory with repos from 2024. What rule connects them?" This often unlocks better structural insights than simple re-shuffling.

## Multi-dimensional grilling
When the problem has several orthogonal axes (activity level × category membership × lifecycle stage), it's acceptable to:
1. Present all data in a summary table first
2. Pick the highest-priority axis and ask a focused question about it
3. Resolve one axis before moving to the next

The "one question at a time" rule applies to decision-branches within an axis, not to the initial data-sharing that makes those branches meaningful.

## User preference: preservation over deletion
When the user shares notes, repos, or knowledge bases — lead with structural improvements (indexing, tagging, navigation, org-roam links, discoverability) rather than suggesting deletion or pruning. The user prefers keeping old/outdated artifacts as long as important content can be extracted quickly. Never default to "delete this" as a first suggestion; always ask about the signal-vs-noise goal first.
