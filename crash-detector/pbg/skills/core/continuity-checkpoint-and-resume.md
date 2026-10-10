---
skill_id: SKILL-CONTINUITY-CHECKPOINT-AND-RESUME
title: Continuity checkpoint and resume
version: 1
roles: [PROJECT_LEAD, ENGINEER, ASSURANCE_ENGINEER]
triggers: [material boundary reached, before pause, before handover, session start]
prerequisites: [framework booted, repository observable]
required_inputs: [what happened, exact SHA, next safe action]
related_controls: [PBG-CONT-002, PBG-CONT-003, PBG-CONT-005, PBG-CONT-006, PBG-CONT-007, PBG-CONT-011]
references: [SRC-RFC3339, SRC-NIST-CSF]
---

# Continuity checkpoint and resume

Making the project survive losing you.

## Checkpoint

At every material boundary, before every pause, before every handover:

```bash
PYTHONPATH=pbg/tools python3 -B -m pbg.cli log validate
PYTHONPATH=pbg/tools python3 -B -m pbg.cli resume
```

Record: what happened, the exact SHA, tests run and their outcome, evidence references, blockers,
held actions, the next safe action and the next responsible role.

**Generate the record. Never hand-format it.** A hand-edited canonical record fails silently — a
substitution that matches nothing changes nothing and reports nothing, and the projection then
describes a state that no longer exists while every check stays green. That is not hypothetical;
it happened in this framework's own records and survived two commits.

## Resume

```bash
PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot
```

Read the classification rather than the vibe:

| State | Meaning | You may |
|---|---|---|
| `ACTIVE_WORK_CURRENT` | pointer matches the newest entry | resume |
| `ACTIVE_WORK_STALE` | describes a superseded state | reconcile, not mutate |
| `ACTIVE_WORK_FORWARD_REFERENCE` | promises an entry never written | diagnose the interrupted write |
| `ACTIVE_WORK_LOG_MISMATCH` | determinably inconsistent | diagnose |
| `ACTIVE_WORK_UNRESOLVED` | cannot determine | diagnose |
| `NEW_PROJECT_CONTINUITY_NOT_INITIALISED` | never written; not damaged | initialise |

Blocked resume always permits read-only diagnosis. Blocking the work must never block finding out
why the work is blocked.

## Reconciling drift

Recorded and observed disagree. Report the difference and reconcile deliberately. **Never silently
correct** — a silent correction destroys the only evidence that something went wrong.

## The test

Not whether you finished. Whether an agent with none of your context can pick this up from the
record alone. If the answer depends on something only you know, the checkpoint is incomplete.

## Evidence

Build Log entry with exact SHA; Active Work currency state; resume verdict.

## Failure behaviour

Invalid continuity blocks normal resume and permits diagnosis. Propose a repair; do not mutate on
the strength of a record you already know is wrong.
