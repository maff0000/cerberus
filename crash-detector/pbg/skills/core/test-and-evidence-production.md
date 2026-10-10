---
skill_id: SKILL-TEST-AND-EVIDENCE-PRODUCTION
title: Test and evidence production
version: 1
roles: [ENGINEER, ASSURANCE_ENGINEER]
triggers: [any implementation, any verification, any close]
prerequisites: [the authentic target is reachable, or its unreachability is known]
required_inputs: [the target, the claim being evidenced]
related_controls: [PBG-ASSURE-017, PBG-EVID-001, PBG-EVID-002, PBG-CI-001]
references: [SRC-NIST-SSDF, SRC-OWASP-ASVS]
---

# Test and evidence production

Producing something that would change a reader's mind, rather than something that agrees with you.

## The three questions

1. **What exactly is the claim?** "It works" is not a claim. "Endpoint X returns 409 on a duplicate
   key, verified against the built image at digest D" is.
2. **What is the authentic target?** The running thing, the built artefact, the exact commit — not a
   reconstruction, a copy, or a wrapper written to make verification convenient.
3. **Would this evidence exist if the claim were false?** If not, it is decoration.

## Mutation: the test that matters

A test proves nothing until you have seen it fail for the right reason.

```
break the behaviour at its own seam  →  run the test  →  it must fail
restore                              →  run the test  →  it must pass
```

**At its own seam.** A test that fails because you deleted the whole function has told you the
function is called, not that the behaviour is guarded. Break the specific condition the check
claims to cover.

## Discipline

- A test that can skip is not evidence. A conditional skip is a hole with a comment in it.
- A suite passing against unchanged behaviour is a rumour.
- Guard the class, not the instance. A fix for the reported input that leaves its siblings broken
  has not been tested.
- Evidence must be independent of what it certifies. A manifest that vouches for itself, a log
  written by the process under audit, a fixture asserted by the code that built it — none count.
- Capture the command line with the output. Output alone cannot be reproduced.
- Where the authentic target cannot be reached, return `UNSUPPORTED`. Never a substitute.

## Correcting a defective test

Permitted, and recorded: why the test was wrong, what requirement it should express, what evidence
supports the correction, and whether product intent is affected. Where the correction materially
benefits your own implementation, it needs a second pair of eyes.

## Evidence

Command line plus output; the mutation result; the target's exact identity.

## Failure behaviour

Report the failure. Never adjust the test, the tolerance, the fixture or the criterion to obtain a
pass — a green obtained by moving the goalposts is the most expensive kind of false evidence,
because everything downstream now rests on it.
