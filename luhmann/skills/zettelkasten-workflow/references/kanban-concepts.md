# Kanban Concepts for Note Processing

Domain reference for processing Kanban-related fleeting notes in the user's vault.
Emerged from interrogation session (2026-06-21) on the claim "when tasks pile up,
you can see the bottleneck."

## WIP Limits Are the Core Mechanism

Not visualisation. Not columns. WIP limits are the lever that makes Kanban work.

- A WIP limit is a predefined cap per column (e.g. Testing = 2)
- When a column hits its limit, upstream **cannot pull** — the chain stops
- This forces the bottleneck into visibility: idle developers upstream = attention on the constrained step
- Without WIP limits, the board is just a to-do list with columns

## Push vs. Pull

| Push (common but broken) | Pull (Kanban proper) |
|--------------------------|----------------------|
| Completed work auto-moves downstream | Downstream signals "ready" — upstream hands over |
| Bottleneck accumulates invisibly | Bottleneck blocks upstream immediately |
| Everyone looks busy | Idle time is visible and creates urgency |
| Lead times are long but no one measures | Constraint is forced into the open |

Most teams run on implicit WIP = ∞. The auto-move habit is the exact thing Kanban rejects.

## Bottleneck Visibility

With WIP limits, a bottleneck shows up as **upstream blockage**, not as a pile in the constrained column.

Example: Testing WIP = 2. Tester has A (in progress) and B (queued). Dev finishes
C. C cannot enter Testing (limit reached). C stays in Dev column. Dev cannot pull
a new card from Design. The chain stops.

Without WIP limits: C auto-moves to Testing. Testing grows to 5+ cards. Dev starts
working on D. Everyone is busy. The tester is drowning but nobody sees a blockage
because nothing blocked.

## Key Terms

- **WIP (Work In Progress):** A limit on cards in a column, not a measurement of output
- **Pull:** The downstream column initiates the handover
- **Push:** The upstream column initiates the handover (defeats WIP limits)
- **Swarm:** Developers idle upstream go help the constrained step (cross-functional response to blockage)
- **Lead time:** Time from card creation to completion (grows without WIP limits)

## References

- David J. Anderson, *Kanban: Successful Evolutionary Change for Your Technology Business*
- The Toyota Production System concept of *kanban* (a signalling card) is related but distinct from the Kanban Method for knowledge work
