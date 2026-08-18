---
skill_id: SKILL-PROJECT-DISCOVERY
title: Project discovery
version: 1
roles: [PROJECT_LEAD]
triggers: [no PID exists, PID_DISCOVERY_REQUIRED, adopting an existing codebase]
prerequisites: [framework booted, read access to the codebase]
required_inputs: [repository, any existing documentation, Product Owner availability]
related_controls: [PBG-PID-001, PBG-PID-003, PBG-PID-004, PBG-BP-001]
references: [SRC-NIST-AI-RMF]
---

# Project discovery

Establishing what a project is *for* when the record does not say.

## The trap

**Existing code is evidence of current implementation, not authorised product intent**
(`PBG-PID-003`). A codebase tells you what someone built. It cannot tell you what they were asked
to build, what they abandoned, or what was a workaround for a constraint that no longer exists.

Reading intent out of implementation and writing it into a PID converts an accident into doctrine.

## Procedure

1. **Establish the boundary.** What repositories, services, data and environments are in scope, and
   what is explicitly outside. Record both.
2. **Inventory what exists.** Entry points, services, data stores, external integrations, deployment
   targets, tests. Observed, not assumed.
3. **Separate observation from inference.** Two columns: what the code demonstrably does, and what
   you think it is for. Never let the second column silently become the first.
4. **Collect the questions.** Every place where intent is genuinely unclear becomes an explicit
   question for the Product Owners, not a guess.
5. **Draft the PID with gaps visible.** Mark unresolved sections `AMBIGUOUS_PENDING_OWNER` rather
   than filling them plausibly.
6. **Return for authorisation.** A PID is authorised by Product Authority. A drafted PID is a
   proposal.

## Evidence

Discovery report separating observation from inference; the question list; the PID draft with its
unresolved sections marked.

## Failure behaviour

If Product Owners are unavailable, deliver the draft with gaps marked and stop. Do not resolve
product meaning to keep moving — an invented requirement is harder to remove than a missing one,
because it acquires dependents.
