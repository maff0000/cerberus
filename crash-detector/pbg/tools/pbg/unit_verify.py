"""The product path for compute-unit verification.

    declaration + real Docker observation + effective runtime identity + whole-unit verification

The runtime half of the verifier once had no product consumer: `tools/` never imported
`docker_observe`; the only product `verify()` call passed no containers, no inventory and no
identities, so the healthy unit and a root-running unit returned identical results through the
product path. Every runtime check was reachable only from the test suite.

That is the same shape as the `check_declared_mounts_present` defect repaired two candidates
earlier — a mechanism that exists, works, and is wired to nothing. Building the mechanism is not
the deliverable; putting it in the path that actually runs is.

This module is that path, and nothing more. It is deliberately not a Docker management surface:
observation stays in `docker_observe` behind its read-only allowlist, judgement stays in
`unit_interface`, and this composes the two.
"""

from __future__ import annotations

from pathlib import Path

from . import unit_interface as ui


def verify_unit(project_root: Path, use_runtime: bool = True) -> tuple[ui.UnitVerdict, dict]:
    """Verify a compute unit against its declaration AND its running self.

    Returns (verdict, context). `context` records what runtime evidence was actually obtained, so
    a caller can tell a unit that passed from a unit that was never looked at — a distinction the
    product path previously could not make.
    """
    root = Path(project_root)
    context: dict = {"runtime_observed": False, "identities_observed": False,
                     "containers": [], "reason": None}

    decl = ui.load(root)
    if decl is None:
        return ui.verify(root), {**context, "reason": "no unit interface declared"}

    if not use_runtime:
        return ui.verify(root), {**context, "reason": "runtime observation not requested"}

    try:
        from . import docker_observe as dob
    except ImportError as exc:                        # pragma: no cover - defensive
        return ui.verify(root), {**context, "reason": f"observation unavailable: {exc}"}

    if not dob.available():
        return ui.verify(root), {**context, "reason": "no Docker engine available"}

    observation = dob.observe(decl)
    containers = observation["containers"]
    identities = dob.observe_identities(containers)
    context.update({
        "runtime_observed": True,
        "identities_observed": all(v is not None for v in identities.values()) and bool(identities),
        "containers": sorted(containers),
        "identities": identities,
    })
    verdict = ui.verify(root, containers=containers, inventory=observation["inventory"],
                        identities=identities)
    return verdict, context


def render(verdict: ui.UnitVerdict, context: dict) -> str:
    """Human-readable result, leading with what was actually observed."""
    lines = [verdict.render(), ""]
    if context.get("runtime_observed"):
        lines.append(f"  runtime observed : {len(context['containers'])} container(s) "
                     f"{context['containers']}")
        for name, identity in sorted((context.get("identities") or {}).items()):
            if identity is None:
                lines.append(f"    {name:32} identity NOT ESTABLISHED")
            else:
                lines.append(f"    {name:32} uid={identity['effective_uid']} "
                             f"gid={identity['effective_gid']} "
                             f"is_root={str(identity['is_root']).lower()}")
    else:
        lines.append(f"  runtime observed : NO — {context.get('reason')}")
        lines.append("    the declaration was checked; the running unit was not. Nothing here is "
                     "evidence about runtime behaviour.")
    return "\n".join(lines)
