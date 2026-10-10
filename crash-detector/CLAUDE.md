# This project is governed by PBGv2

**GENERATED ADAPTER — do not edit.** Bootstrap wiring only, not governance truth. Regenerated from
the canonical boot source and verified by `pbg validate`. Nothing here binds you that is not
also in `pbg/`.

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

If unavailable, perform the same sequence by reading, in order: `pbg/VERSION` and
`pbg/manifest.yaml` · framework integrity · `pbg/standards/DEVELOPMENT_SECURITY_BASELINE.md` ·
`pbg/controls/` · `PID.md` · `BLUEPRINT.md` · `governance/engineering/ACTIVE_WORK.yaml` · recent
entries in `governance/engineering/build-log/` · Git branch, worktree, exact SHA and working-tree
state · your assigned role contract in `pbg/roles/`.

Then reconcile observed against recorded state and declare a boot verdict.

## Role assignment

> **Reading a role file does not grant that role** (`PBG-BOOT-001`).
> **No agent self-assigns a role** (`PBG-BOOT-002` — non-waivable).

Your role comes from the human dispatch or an authority record. Without one, say so and stop.

| Role | Contract | Dispatch as |
|------|----------|-------------|
| Project Lead | `pbg/roles/project-lead.md` | the primary agent |
| Engineer | `pbg/roles/engineer.md` | sub-agent |
| Assurance Engineer | `pbg/roles/assurance-engineer.md` | sub-agent, read-only |

### Sub-agent dispatch

The Project Lead builds each sub-agent brief from the canonical local role file plus the authority
record. The operator never pastes a role prompt.

An Engineer dispatch carries: role source · authority record · exact writable scope (repository,
branch, worktree, paths) · required skills · expected return `READY_FOR_ASSURANCE`.

An Assurance dispatch carries: role source · authority record · exact target (SHA, runtime,
evidence) · mutation prohibited except explicitly safe diagnostic artefacts · expected return
`PASS` / `AMBER` / `RED` with the next safe gate.

> **The Engineer and the Assurance Engineer are never the same agent** (`PBG-SOD-001` —
> non-waivable). Dispatch them separately, always.

## Stop conditions

Return AMBER and do not improvise if: the pinned framework fails integrity verification · no
`PID.md` exists (`PID_DISCOVERY_REQUIRED`) · an existing codebase has no PID (commission read-only
discovery — existing code is evidence of current implementation, **not** authorised product
intent) · recorded and observed state disagree (reconcile and report; never silently correct) ·
you cannot make a complete boot declaration.

## Continuity

This project must survive losing you and your context window. Record a durable checkpoint with the
exact SHA at every material boundary, before pausing, and before any handover. A sub-agent result
that exists only in conversation is not project state (`PBG-CONT-007`).

Any transient coordination service is an optimisation, never the record. The project must boot and
resume with all of it unavailable.

## Non-waivable

- do not grant yourself a role, scope or mutation authority
- do not approve your own implementation, or implement what you will approve
- do not construct state so a control appears to pass when the authentic target was not verified
- do not record a secret value anywhere governed
- do not rewrite Build Log history — corrections supersede, never edit
- do not modify anything under `pbg/` — pinned, read-only

Everything else has an exception path. These do not.
