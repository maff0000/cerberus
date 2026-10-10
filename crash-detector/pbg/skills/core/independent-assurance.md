---
skill_id: SKILL-INDEPENDENT-ASSURANCE
title: Independent Assurance
version: 1
roles: [ASSURANCE_ENGINEER]
triggers: [Assurance dispatch received, close gate, release candidate]
prerequisites: [exact target identified, independence from the implementation]
required_inputs: [exact target, permitted observations, expected verdict form]
related_controls: [PBG-SOD-001, PBG-SOD-004, PBG-ASSURE-001, PBG-ASSURE-010, PBG-EVID-001, PBG-FWK-003]
references: [SRC-NIST-SSDF, SRC-NIST-AI-RMF, SRC-ISO-27001]
---

# Independent Assurance

Assessing a bounded target you did not build, and being precise about what you did not establish.

## Before you start

Confirm you did not implement any part of the target. If you did, return `INDEPENDENCE_CONFLICT`
and hand the dispatch back — this is non-waivable (`PBG-SOD-001`).

Confirm the target is exact. "The latest", "the current branch" and "the deployed version" are not
targets. Return `TARGET_UNSPECIFIED`.

## Procedure

1. **Pin the target.** Exact SHA, digest or runtime identity. Record it before you look at anything.
2. **Establish reachability.** For each check, can you reach the authentic target? Where you cannot,
   that check is `UNSUPPORTED` — decide this before you start, so it is not a conclusion you reach
   under pressure to deliver a verdict.
3. **Try to refute.** Work the claim as something you expect to be wrong. Confirmation is easy to
   manufacture and tells you little.
4. **Work the adversarial themes deliberately** rather than waiting for them to surface:
   guard-the-instance-not-the-class · self-reference and self-vouching · authentic-target
   substitution · control bypass · capability mistaken for authority · continuity recovery ·
   control burden · portability.
5. **Separate verdict from continuation.** What is true, and what is safe to do next, are different
   calculations.
6. **Record what you did not examine**, and why. This is the part that protects everyone later.

## Judging mutation by effect

An observation that writes a cache, takes a lock or triggers a rebuild has mutated the target,
whatever the command was called (`PBG-RT-001`). Observe a lock; never take it.

## Verdicts

| Verdict | Use when |
|---|---|
| `PASS` | verified against the authentic target, within the stated scope |
| `AMBER` | materially sound, with named conditions or gaps |
| `RED` | the claim is not supported, or a control is bypassed |
| `UNSUPPORTED` | the authentic target could not be reached — never a dressed-up PASS |
| `NOT_APPLICABLE` | genuinely does not apply; recorded, never silent |

Qualify every verdict with confidence and scope. An unscoped PASS is a liability.

## Evidence

Target identity; per-check evidence and its independence; the not-examined list.

## Failure behaviour

An honest AMBER beats a confident PASS resting on an unexamined assumption. Your standing is the
product; protect it by being precise about the limits of what you established.
