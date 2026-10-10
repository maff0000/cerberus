---
skill_id: SKILL-INCIDENT-DIAGNOSIS
title: Incident diagnosis
version: 1
roles: [PROJECT_LEAD, ENGINEER]
triggers: [production defect, control bypass, corrupted continuity, security finding]
prerequisites: [incident declared, observation access]
required_inputs: [symptom, affected target, observation capability]
related_controls: [PBG-INC-001, PBG-INC-002, PBG-INC-003, PBG-RT-001, PBG-RT-005]
references: [SRC-SRE, SRC-NIST-CSF]
---

# Incident diagnosis

Finding out what is actually happening, before changing anything.

## Order of operations

**Stabilise, then diagnose, then repair.** Rolling back to a known-good state is usually cheaper
than diagnosing under pressure — and it preserves the evidence, provided you capture state first.

## Capture before you touch

Whatever you are about to change, record its current state first. Incident diagnosis routinely
destroys the evidence that would have identified the cause.

```bash
git rev-parse HEAD; git status --porcelain
# service state, image digest, config in effect, recent logs
```

## Diagnostic discipline

- **Every observation is pre-classified** (`PBG-RT-005`): does this read, or does it change
  something? A command that restarts, rebuilds, takes a lock or clears a cache is a mutation
  whatever its name suggests.
- **Distinguish "cannot determine" from "determined to be absent."** They lead to different actions,
  and collapsing them is how an incident gets closed against the wrong cause.
- **Read the actual state.** Not the deployment log, not the pipeline result, not the intent. The
  running system's own bytes.
- **Interrogate the cell you skipped.** The component everyone assumes is fine because it "hasn't
  changed" is where surprises live. Verify, do not assume.
- **The second guess wears the costume of the fix.** When your first hypothesis fails, the second
  arrives with the same confidence and less scrutiny. Slow down there.

## When you find it

Guard the **class**, not the instance. A fix for the exact reported input that leaves its siblings
broken has converted an incident into a recurring one.

Ask what else shares the defect's shape. A fix that unblocks a path also unblocks whatever defects
that path was hiding.

## Recording

Symptom, timeline in UTC, observations with their classification, hypotheses tried and rejected,
cause, remedy, class-level guard, and what would have caught it earlier.

## Evidence

Captured pre-change state; observations with their mutation classification; the failing case
reproduced before and after.

## Failure behaviour

If the cause cannot be established, say so. A closed incident with an unproven cause is an open
incident with worse records.
