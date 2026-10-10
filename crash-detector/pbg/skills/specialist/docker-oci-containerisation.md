---
skill_id: SKILL-DOCKER-OCI-CONTAINERISATION
title: Docker and OCI containerisation
version: 1
roles: [ENGINEER, ASSURANCE_ENGINEER]
triggers: [building an image, deploying a container, auditing a running container]
prerequisites: [application is container-ready, registry identified]
required_inputs: [base image digest, runtime user, ports, volumes, signals]
related_controls: [PBG-RT-012, PBG-RT-013, PBG-CI-004, PBG-CI-005, PBG-DEPLOY-003]
references: [SRC-OCI, SRC-CIS, SRC-TWELVE-FACTOR]
---

# Docker and OCI containerisation

Packaging a container-ready application. If the application is not container-ready, fix that first
— see [`container-ready-application-design`](../core/container-ready-application-design.md).

## Identity is the digest

```
myimage:latest                          a mutable pointer, not an identity
myimage@sha256:abc...                   an identity
```

Pin base images by digest. Record the built digest and compare it at deploy. **What was tested and
what runs must be the same artefact**, not the same description of one.

## Image construction

**Multi-stage.** Build tooling belongs in the build stage; the final image carries the runtime and
the application, nothing else. A compiler in a production image is an attack surface with no
purpose.

**Layer for cache correctness, not just speed.** Dependency manifests copied and installed before
application source, so a source change does not invalidate the dependency layer.

**Explicit non-root user** (`PBG-RT-012`):

```dockerfile
RUN useradd --system --uid 10001 --no-create-home app
USER 10001
```

Numeric UID, because some orchestrators enforce `runAsNonRoot` by inspecting the UID and cannot
resolve a name.

**Declare the contract.** `EXPOSE`, `VOLUME` for durable paths, `WORKDIR`, and an `ENTRYPOINT` in
exec form — shell form makes the shell PID 1, and the shell does not forward `SIGTERM`.

**Read-only root filesystem** where the platform supports it, with explicit writable mounts for
ephemeral state. This is where an application that writes into its own code directory fails, which
is exactly the design defect worth surfacing.

**No secrets in the image.** Build arguments and layers persist; a secret in any layer is in the
image regardless of later deletion.

**`.dockerignore`** covering `.git`, local environment files and build output. Without it, the
build context carries the repository history into the daemon.

## Auditing a running container

Verify against the running target, not the Dockerfile:

```bash
docker inspect --format '{{.Image}} {{.Config.User}} {{.HostConfig.ReadonlyRootfs}}' <container>
docker exec <container> id
```

The Dockerfile states intent. The running container states fact, and they diverge — an overridden
`USER`, an injected mount, a different tag resolved at pull time.

## Evidence

Base image digest; built image digest; observed runtime UID from the running container; probe
behaviour with the dependency removed; clean `SIGTERM` shutdown.
