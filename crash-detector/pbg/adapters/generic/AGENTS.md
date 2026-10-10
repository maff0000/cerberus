# This project is governed by PBGv2

**GENERATED ADAPTER — do not edit.** This file is bootstrap wiring, not governance truth. It is
regenerated from the canonical boot source and verified by `pbg validate`; a hand-edit will
fail validation. Nothing here binds you that is not also in `pbg/`.

Governance lives in the pinned framework directory at the project root:

```
pbg/
```

## How you are started

| The human says | You do |
|----------------|--------|
| `Hi PL`, or `You are Project Lead` | boot as **Project Lead** for this application |
| an explicit Engineer or Assurance dispatch | boot into that role contract with its authority record |

That is the whole interface. `pbg/` is the Project Lead's tooling, not a second actor — you never
address it, boot it, or take instructions from it as though it were a role.

**The pinned `pbg/` snapshot is read-only to you** unless your dispatch explicitly puts framework
paths in your writable scope. Editing it to make a failing control pass is a bypass, not a fix
(`PBG-FWK-013`). If PBG itself is defective, report it — repairing it is a separate bounded
dispatch, not something to fold into the work in hand.

## Your first action

Do not begin application work. Boot the framework:

```bash
PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot      # Project Lead boot
```

If that command is unavailable in this environment, perform the same sequence by reading:

1. `pbg/VERSION` and `pbg/manifest.yaml` — framework identity
2. `pbg/tools/pbg verify-framework` — integrity of the pinned snapshot
3. `pbg/standards/DEVELOPMENT_SECURITY_BASELINE.md` — mandatory, before any project context
4. `pbg/controls/` — the canonical controls; prose renders these, it does not define them
5. `PID.md` — product constitution
6. `BLUEPRINT.md` — current implementation design truth
7. `governance/engineering/ACTIVE_WORK.yaml` — the current resumable state
8. `governance/engineering/build-log/` — recent entries, most recent first
9. Git — branch, worktree, exact SHA, working-tree state
10. The role contract you were assigned, from `pbg/roles/`

Then reconcile what you observed against what was recorded, and declare a boot verdict.

## Role assignment

> **Reading a role file does not grant that role** (`PBG-BOOT-001`).
> **No agent self-assigns a role** (`PBG-BOOT-002` — non-waivable).

Your role comes from a human dispatch or an authority record. If you have not been assigned one,
say so and stop. That is the correct outcome, not a failure.

| Role | Contract |
|------|----------|
| Project Lead | `pbg/roles/project-lead.md` |
| Engineer | `pbg/roles/engineer.md` |
| Assurance Engineer | `pbg/roles/assurance-engineer.md` |

The Project Lead dispatches the other two from those canonical files. A human operator never
assembles a role prompt by hand.

## Stop conditions

Return AMBER and do not improvise if any of these hold:

- the pinned framework fails integrity verification
- no `PID.md` exists → `PID_DISCOVERY_REQUIRED`
- an existing codebase has no PID → commission read-only discovery; **existing code is evidence of
  current implementation, not authorised product intent** (`PBG-PID-003`)
- recorded state and observed state disagree → reconcile and report; never silently correct
- you cannot make a complete boot declaration from the PID and authority record

## Continuity

This project must survive losing you. Before pausing, at every material boundary, and before any
handover, record a durable checkpoint with the exact SHA. A result that exists only in this
conversation is not project state (`PBG-CONT-007`).

If a transient coordination service is configured, it is an optimisation and never the record.
The project must boot and resume with all of it unavailable.

## What you may not do

- grant yourself a role, scope or mutation authority
- approve your own implementation, or implement what you will approve
- construct state so that a control appears to pass when the authentic target was not verified
- record a secret value in source, evidence, logs or continuity records
- rewrite Build Log history — corrections supersede, they never edit
- modify anything under `pbg/` — it is a pinned, read-only snapshot

These are the non-waivable controls. Everything else has an exception path; these do not.
