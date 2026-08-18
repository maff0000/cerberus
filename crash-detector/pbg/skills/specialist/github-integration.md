---
skill_id: SKILL-GITHUB-INTEGRATION
title: GitHub integration
version: 1
roles: [PROJECT_LEAD, ENGINEER]
triggers: [pull request, branch protection, CI configuration, release]
prerequisites: [repository access, provider authority recorded]
required_inputs: [repository, branch, required checks]
related_controls: [PBG-GIT-002, PBG-GIT-003, PBG-GIT-004, PBG-CI-001, PBG-PORT-001]
references: [SRC-OPENSSF, SRC-SLSA]
---

# GitHub integration

GitHub is an optional integration, never a dependency. **Everything governed must work with the
provider unreachable** — a project whose governance requires an API call cannot boot offline, and
PBG's whole continuity model assumes it can.

## Capability is not authority

`PBG-GIT-004`. Holding a token that can change branch protection is not permission to. Repository
settings are a **Controlled Action** with their own authority record, never a side effect of other
work.

## Pull requests

Body carries the work item ID, the exact SHA, evidence references and the Assurance verdict where
one exists. A reviewer should not have to ask what authorised this.

Merged is not deployed. A merge changes the default branch; it does not change a runtime.

## Branch protection

Require review, require status checks, and include administrators. A control that depends on
someone documenting their own bypass after the event is not a control.

Requiring a check by name means the name must be stable. A renamed workflow silently stops being
required — the protection still reads as enabled while enforcing nothing. Verify by reading the
current protection state from the provider, not by remembering that it was set.

## CI

Pin action versions by SHA, not by tag; a mutable tag is arbitrary code executing with your
repository's permissions. Grant the workflow the narrowest token scope.

CI is evidence, not authority. A green pipeline demonstrates the checks ran; it does not authorise
a release, and it is not independent Assurance.

## Offline behaviour

Every governed operation degrades honestly: report the provider as unreachable, mark
provider-dependent facts `UNAVAILABLE`, and continue with what Git alone can establish. Never
substitute an assumption for an unreachable provider fact.

## Evidence

PR reference; branch protection state read from the provider with its retrieval time; workflow run
identity; pinned action SHAs.
