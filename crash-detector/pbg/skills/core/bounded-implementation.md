---
skill_id: SKILL-BOUNDED-IMPLEMENTATION
title: Bounded implementation
version: 1
roles: [ENGINEER]
triggers: [Engineer dispatch received]
prerequisites: [valid dispatch, boot verdict declared, baseline SHA reconciled]
required_inputs: [objective, writable scope, protected scope, baseline SHA, work type, skills]
related_controls: [PBG-WORK-001, PBG-WORK-004, PBG-SOD-003, PBG-EVID-002, PBG-CONT-005]
references: [SRC-DORA, SRC-ISO-25010, SRC-OWASP-ASVS]
---

# Bounded implementation

Delivering exactly what was dispatched, and returning honestly.

## Procedure

1. **Check the dispatch is complete** before writing anything. Objective, writable scope, protected
   scope, baseline SHA, work type, expected return. Missing writable scope means nothing is
   writable — return `DISPATCH_INCOMPLETE`.
2. **Reconcile the baseline.** If observed HEAD is not the dispatched baseline, that is drift.
   Report it; do not start from wherever the tree happens to be.
3. **Plan against the Blueprint**, not against the first design that occurs to you. Where the
   Blueprint is silent, that is an implementation choice and it is yours to make.
4. **Implement the smallest coherent change** that satisfies the objective. Resist the adjacent
   improvement; note it and return it as a finding.
5. **Test as you go**, at the seam the behaviour actually lives. See
   [`test-and-evidence-production`](test-and-evidence-production.md).
6. **Check the boundary before committing.** `git status` against your writable scope. A file
   outside it is either a mistake or an escalation.
7. **Return with the exact SHA**, what you did, what you deliberately did not, and what you found
   but did not act on.

## Deciding versus escalating

| Question | Yours |
|---|---|
| which data structure, which library already present, how to factor this | yes |
| naming, error handling shape, test structure | yes |
| what the feature should do when the requirement is silent | **no** |
| whether a requirement still applies | **no** |
| whether to touch a file outside your scope | **no** |

Deciding level-1 questions is as much a requirement as escalating the others. An Engineer who
escalates implementation choices is as unhelpful as one who resolves product meaning.

## Evidence

Diff; test output with its command line; the exact SHA; the findings list.

## Failure behaviour

Return the precise blocked state. Never widen scope, guess intent, or weaken a test to finish.
