---
skill_id: SKILL-PBG-ENGINEERING
title: Engineering on PBG itself
version: 1
roles: [ENGINEER]
triggers: [framework defect, adapter work, deliberate upgrade, dispatched PBG work]
prerequisites: [a dispatch whose writable scope names framework paths]
required_inputs: [authority record, target PBG identity, writable scope, rollback route]
related_controls: [PBG-FWK-013, PBG-FWK-020, PBG-PORT-003, PBG-CTRL-004]
references: [SRC-SLSA, SRC-SEMVER]
---

# Engineering on PBG itself

Working on the utility rather than through it. Ordinary Engineer work with an unusual target.

## No special path

There is no PBG greeting, mode or role. You are here because a dispatch put framework paths in your
writable scope, and `roles/engineer.md` governs you exactly as it would for application work.

A failed boot, a failing control, an old version or an unavailable command are reasons to
**recommend** work on PBG. None of them authorises it, and none of them entitles you to widen your
own scope to reach it.

Developing framework doctrine inside a project's pinned copy is how one project's requirements
contaminate core. If a change belongs in PBG generally, it belongs in canonical source with Product
Authority approval — not in the snapshot in front of you.

## Both scopes, declared

```
writable      the exact framework paths this activity may change
protected     the application scope it must not touch
```

Stated separately, never inferred as each other's complement. **Framework repair is never authority
to alter application source.** Where a maintenance task genuinely needs an application-side change,
that is a second authorisation, obtained separately.

## Before mutating

Record installation identity, previous and target version, source release or SHA, expected and
observed digest, changed framework files, project extensions, **rollback route** and validation
expectation. A mutating activity without a rollback route is not governed.

## After

```bash
PYTHONPATH=tools python3 -m pytest tests/ -q
PYTHONPATH=tools python3 -B -m pbg.cli validate
PYTHONPATH=tools python3 -B -m pbg.cli log validate
python3 tools/build_dist.py
```

Then dispatch **independent** Assurance. You cannot certify your own repair (`PBG-SOD-001`).

## Discipline

- Never edit the snapshot to make a failing control pass. That is a bypass wearing a repair's
  clothes, and it is the specific failure `PBG-FWK-013` exists to prevent.
- Prefer clarifying an existing control over adding one. The control-growth freeze is a product
  requirement, not a mood.
- Never claim authenticity from internal self-consistency. A snapshot cannot vouch for its own
  origin.
- No project upgrades silently. Write migration guidance; never push it.

## Evidence

Maintenance boot verdict; both declared scopes; digests before and after; test and validate output;
independent Assurance verdict.

## Failure behaviour

Without framework paths in your writable scope you may inspect and report only. Return the finding
and the proposed repair; do not perform it.
