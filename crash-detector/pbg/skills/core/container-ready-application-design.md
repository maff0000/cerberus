---
skill_id: SKILL-CONTAINER-READY-APPLICATION-DESIGN
title: Container-ready application design
version: 1
roles: [ENGINEER]
triggers: [new service, deployment target defined, containerisation requested]
prerequisites: [Blueprint states the runtime shape]
required_inputs: [configuration surface, data classification, signals and ports]
related_controls: [PBG-RT-012, PBG-RT-013, PBG-DEPLOY-001, PBG-OBS-001]
references: [SRC-TWELVE-FACTOR, SRC-OCI, SRC-SRE, SRC-CIS]
---

# Container-ready application design

Designing so containerisation is a packaging decision, not a rewrite.

## Container-ready is a property of the application

Not of the Dockerfile. An application is container-ready when it can run in one **without changing
its own code**.

## The requirements

**Configuration from the environment.** No host-specific absolute paths, no config file the app
expects at a fixed location outside its own tree, no hostname assumptions.

**Three storage classes, distinguished** (`PBG-RT-013`):

| Class | Property | Container consequence |
|---|---|---|
| read-only code | immutable at runtime | belongs in the image |
| ephemeral state | recreatable | tmpfs or a scratch volume |
| durable data | must survive restart | a named volume or external store |

An application that writes durable data into its own code directory cannot be containerised safely.

**Non-root, least-privileged user** (`PBG-RT-012`). Declared explicitly, not inherited from a base
image's default.

**Signal handling.** `SIGTERM` means shut down cleanly within the grace period. A process that
ignores it gets killed, and whatever it was midway through becomes a recovery problem.

**Liveness and readiness separated.** Liveness: the process is functioning. Readiness: it can serve
now. Conflating them causes restarts during warm-up and traffic during outages. A probe must test
what it claims — one returning 200 because the HTTP layer is up while its database is unreachable
manufactures confidence, which is worse than having no probe.

**Stateless where possible.** Session state in a shared store, not in process memory, or the second
replica behaves differently from the first.

**Logs to stdout/stderr.** The platform collects them. An application managing its own log rotation
inside a container is fighting the platform.

## Identity

Images are identified by **digest**, never by tag. A tag is a mutable pointer. Pin base images by
digest so the build is reproducible.

## Evidence

The three storage classes documented; runtime user observed on a running container; probe behaviour
observed with its dependency removed; clean `SIGTERM` shutdown demonstrated.

## Failure behaviour

If the application cannot meet these without code change, that is a finding for the Blueprint, not
something to paper over in the Dockerfile.
