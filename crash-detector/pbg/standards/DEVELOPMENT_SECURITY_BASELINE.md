---
artefact: DEVELOPMENT_SECURITY_BASELINE
version: 1
status: DRAFT
authority: PBGV2-FOUNDATION-0001
consumed_by: [PROJECT_LEAD, ENGINEER, ASSURANCE_ENGINEER]
consumption: once per role boot, verified current
---

# Development and Security Standards Baseline

The default engineering conduct expected of every agent doing governed work, whatever it is
building.

**Read this once at role boot, not once per task.** It is deliberately short. It is not a second
control graph: controls specify governed outcomes and boundaries, this specifies ordinary
engineering behaviour, and skills specify how to do a particular thing well. Where a subject needs
depth, the depth lives in a skill.

Sources are recorded in [`STANDARDS_SOURCE_REGISTER.yaml`](STANDARDS_SOURCE_REGISTER.yaml). PBG
interprets those sources; referencing one is not a claim of certification against it.

---

## 1. Secure and maintainable design

Design for the person who arrives after you with none of your context. Prefer the boring
construction that fails obviously over the clever one that fails quietly.

Make the safe path the easy path. Where a mistake would be expensive, make it hard to express:
a type, a required parameter, a check at the boundary — not a comment asking for care.

Keep trust boundaries explicit and few. Name what crosses each one.

## 2. Authority and least privilege

An identity gets the narrowest permission that lets it do its job, for the shortest time it needs.

**Capability is not authority** (`PBG-GIT-004`). Being able to write a path, call an API or restart
a service is not permission to. Check the authority record, not the file mode.

Default to deny. An unstated permission is absent, not implied — an empty scope means *nothing*, not
*everything*.

## 3. Exact source and artefact identity

Refer to things by identity, never by convenience: an exact commit SHA, a digest, an immutable tag.
`latest`, `main` and "the current build" are not identities.

Record what you actually observed, not what you expected to observe. A remembered SHA is a claim; a
read one is an observation.

Verify contents, never names. A file, branch or image named correctly proves nothing about what is
inside it.

## 4. Input and data validation

Validate at the boundary, once, against an explicit schema. Reject what does not conform rather
than coercing it into something that nearly does.

Treat all external input as hostile: user input, API responses, file contents, environment
variables, and the output of other agents. Trust is a property of the boundary, not of the source's
reputation.

Parse into a typed structure early so the rest of the code cannot receive a shape it does not
expect. Where you must accept a range of shapes, enumerate them — a shape guard is only as wide as
the shapes you have actually met.

## 5. Secrets and sensitive data

**Secrets are referenced, never reproduced.** Not in code, Git, logs, evidence, records,
documentation, error messages, test fixtures or chat.

Read them from the environment or a secret store at the point of use. Never log a secret's value,
and never print a matched value when scanning for them — report class and location only.

Rotate on any suspicion of exposure. Treat a secret that was ever committed as compromised
regardless of subsequent deletion; history is not erased by a later commit.

Personal data gets the same discipline: collect the minimum, state where it lives, and never move it
somewhere it was not authorised to go.

## 6. Dependency and supply-chain safety

Pin dependencies to exact versions and record their identity. A lockfile is part of the source.

Prefer fewer dependencies. Every one is code you did not write, cannot fully review, and must
nonetheless vouch for.

Verify what you fetch where a verification mechanism exists — digest, signature, or a trusted
release record. A download that succeeded is not a download that was authentic.

Vendored or copied code carries its origin and version with it.

## 7. Test integrity and evidence

A test that can skip is not evidence. A suite that passes against unchanged behaviour is a rumour.

**Prove the check fails when the thing it checks is broken**, at that check's own seam
(`PBG-ASSURE-017`). A guard that stops the reported case but not its class has not been tested.

Never weaken a test, tolerance, fixture or acceptance criterion to obtain a pass. If a test is
genuinely wrong, correct it and record why it was wrong, what requirement it should express, and
what evidence supports the correction.

Evidence is produced independently of what it certifies (`PBG-EVID-001`) and names its authentic
target (`PBG-EVID-002`). Command output with its command line beats a summary of that output.

## 8. Failure handling and fail-safe behaviour

Fail loudly, early, and in a state a human can act on. A caught exception that returns a default is
a decision to continue with wrong data; make that decision deliberately or not at all.

Distinguish *cannot determine* from *determined to be absent*. They lead to different actions, and
collapsing them is how a check comes to report success it never established.

Where partial failure is possible, decide explicitly what happens to the partial work. Leave the
system in a state you would be willing to resume from.

Never construct state so a check appears to pass when the authentic target was not verified.

## 9. Logging, observability and UTC

Everything is UTC, in ISO-8601, with the offset stated. Local time belongs in the display layer and
nowhere else.

Log the facts needed to reconstruct what happened: identity, inputs by reference, decisions taken,
outcome. Not secrets, not personal data, not a narrative.

Make failure observable before you make success pretty. An action with no trace did not happen as
far as anyone else is concerned.

## 10. Data persistence and migrations

Migrations are append-only and forward-only. A migration that mutates a previous migration destroys
the ability to reason about any environment that already ran it.

Every migration states its rollback, or states plainly that it has none — an irreversible migration
is a Controlled Action, not a Task.

Separate read-only code, ephemeral state and durable data (`PBG-RT-013`). Know which of the three
each path is, because the recovery behaviour differs for all three.

Configuration that affects a result belongs in a run-level snapshot, so the result can be explained
later.

## 11. Concurrency and idempotency

Make operations idempotent where you can; a retried request that duplicates an effect is worse than
one that fails.

Serialise mutation of shared state, or prove it does not need serialising. Do not assume a single
writer because you have only seen one.

Observe a lock; never take one you do not need. Where an operation takes a lock, say so — an
apparently read-only command that locks has mutated availability.

Timeouts and retries are part of the design, not an afterthought. An unbounded wait is an outage
with extra steps.

## 12. Container-ready application design

An application must be able to run in a container without changing its own code: configuration from
the environment, no host-specific absolute paths, no assumption of a writable code directory.

Run as a **non-root, least-privileged user** (`PBG-RT-012`). Declare the ports, the volumes and the
signals it handles.

Handle `SIGTERM` and shut down cleanly within the platform's grace period. A process that ignores
`SIGTERM` will be killed, and whatever it was midway through will be your recovery problem.

Build reproducibly: pinned base image by digest, no network-dependent build steps that can drift,
and the same source producing the same image.

## 13. Health and readiness

Distinguish **liveness** (the process is functioning) from **readiness** (it can serve traffic
now). Conflating them causes restarts during warm-up and traffic during outages.

A health probe must actually test the thing it claims to. A probe returning 200 because the HTTP
layer is up, while the dependency it needs is unreachable, is worse than no probe: it manufactures
confidence.

Probes are cheap, bounded and free of side effects.

## 14. Deployment, rollback and recovery

Every deployment states its rollback route before it starts, not after it fails.

Deploy an artefact you have verified, identified by digest. What ran in the test environment and
what runs in production must be the same artefact, not the same description of one.

Never assert that something is live from anything other than the running production's own bytes.
Deployment intent is not runtime truth.

Recovery is tested, not assumed. A backup that has never been restored is a hypothesis.

## 15. Documentation and continuity

Record decisions where the next agent will look: in the governed record, not in a conversation.

State what you did, what you deliberately did not, and what you could not. The omissions are the
part that saves someone else a day.

Records are generated from structured meaning, not hand-formatted. A hand-edited canonical record
fails silently and looks fine.

Keep documents that describe behaviour next to the behaviour, and let anything derivable be derived
rather than restated.

## 16. Independent Assurance

Nothing certifies itself. Not a manifest, not a test written by the implementation, not an agent
reporting on its own work (`PBG-SOD-001`, non-waivable).

The verdict and the continuation implication are separate calculations. What is *true* and what is
*safe to do next* are different questions.

Where a check cannot reach its authentic target, it returns `UNSUPPORTED` — never a pass against a
substitute.

---

## Applying this baseline

You are not expected to recite it. You are expected to work this way, and to notice when a task
pushes against one of these defaults — that friction is usually the signal that the task needs an
explicit decision rather than a quiet exception.

Where a control and this baseline appear to conflict, the control wins and the conflict is a
finding worth reporting.
