---
owner-role: Project Lead
status: PLANNED
authority: <authority record>
---

# EPIC-NNN — <title>

**Epics name outcomes, not components.**

    Weak:   Build database
    Better: Persist and recover the user's canonical project state

| | |
|---|---|
| Product outcome | |
| PID requirement trace | REQ-… — every Epic must advance at least one |
| Why it matters | |
| In scope | |
| Out of scope | |
| Dependencies | |
| Constraints | |
| User or operator-visible result | |
| Assurance expectation | which assurance level, and what independent verification looks like |
| Status | |
| Evidence | |
| Recommended sequence | |

## Acceptance criteria

Observable and provable, inherited from the PID.

    Weak:   Continuity is robust.
    Better: A fresh Project Lead can recover project phase, authority, exact SHA, held actions
            and next safe action using only canonical artefacts and Git.

## Stories

| ID | Type | Outcome | Status |
|---|---|---|---|
| STORY-001 | USER STORY | | |

Several Stories may be delivered through **one** coherent bounded change where scope is clear, the
mutation boundary is clean, testing can be integrated and risk does not demand separation. A Story
does not automatically require its own branch, work order, audit or approval.

## No Epic exists solely because a technology is interesting

If this Epic cannot name the PID requirement it advances, it is not an Epic.
