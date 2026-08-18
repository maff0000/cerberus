"""Read-only observation of real Docker artefacts, converted to the verifier's input shapes.

STRICTLY READ-ONLY. This module runs `ps`, `inspect`, `network ls` and `volume ls`. It never
starts, stops, removes, relabels or reconfigures anything. Observation and deletion authority are
separate on purpose: the thing that decides what exists must not be the thing that can destroy it.

SCOPE BEFORE JUDGEMENT. The host this was written on runs twenty unrelated containers — ollama,
openclaw, MT5, ib-gateway, argus, helios. None of them are any unit's business. An artefact enters
scope only through the unit's declaration, its provenance labels, or its Compose project. Existing
on the host is not association, and a broad `docker ps` followed by a prefix match would be a
cleanup routine pointed at somebody else's production.

REDACTION. `docker inspect` returns credential-bearing content in more than one place. Config.Env
is the obvious one; the top-level .Path and .Args carry the same information a redacted Config.Cmd
was suppressing, so `redis-server --requirepass <secret>` reached durable evidence through the
field that was not on the list. Redaction here is STRUCTURAL: named fields are dropped whatever
they contain, because a secret detector only catches the shapes it already knows.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from . import unit_interface as ui

#: COMPLETE command shapes, not first tokens.
#:
#: The previous guard checked args[0] against a verb set that included the families `network`,
#: `volume` and `image` -- so `docker volume prune -f` and `docker network rm` passed it. Nothing
#: called them, which made the module read-only by discipline while its docstring claimed it was
#: read-only by construction. On this host `docker volume prune -f` would have targeted production
#: volumes. An allowlist of whole shapes closes the class rather than the instances: an unknown or
#: unlisted form is refused, so a future caller cannot quietly widen it.
ALLOWED_SHAPES = frozenset({
    ("version",),
    ("ps",),
    ("inspect",),
    ("network", "ls"), ("network", "inspect"),
    ("volume", "ls"), ("volume", "inspect"),
    ("image", "inspect"),
})

#: Verbs that take a subcommand. For these the shape is (family, subcommand).
_FAMILIES = frozenset({"network", "volume", "image", "container", "system", "compose",
                       "builder", "buildx", "context", "plugin", "swarm", "node", "service",
                       "secret", "config", "stack", "trust", "manifest", "checkpoint"})

#: Fields whose VALUES never leave this module. Config.Cmd was redacted while the top-level .Path
#: and .Args carried the same command content -- a credential passed as `--requirepass <secret>`
#: reached durable evidence through the field that was not on the list. Redaction is structural:
#: the field is dropped whatever is in it, rather than scanned for things that look secret.
REDACTED_CONFIG_FIELDS = ("Env", "Cmd", "Entrypoint", "Secrets", "Healthcheck")
REDACTED_TOP_LEVEL_FIELDS = ("Path", "Args")


class DockerUnavailable(Exception):
    """No usable Docker engine. Callers must fail closed, never assume a clean host."""


def command_shape(args: tuple) -> tuple:
    """The complete shape of a docker invocation, ignoring flags before the subcommand."""
    if not args:
        return ()
    verb = args[0]
    if verb not in _FAMILIES:
        return (verb,)
    for token in args[1:]:
        if not token.startswith("-"):
            return (verb, token)
    return (verb, "")


#: Tokens that must not appear ANYWHERE in an invocation.
#:
#: Defence in depth behind the allowlist. Shape extraction takes the first non-flag token as the
#: subcommand, so a flag's VALUE can be consumed in that position and a destructive token could
#: ride along later in a shape that still looks allowed. Rejecting the token outright removes the
#: ambiguity rather than reasoning about which flags take values.
MUTATING_TOKENS = frozenset({
    "rm", "rmi", "prune", "stop", "start", "restart", "kill", "pause", "unpause", "create",
    "run", "exec", "update", "down", "up", "remove", "delete", "commit", "push", "tag", "load",
    "import", "save", "export", "build", "attach", "cp", "rename", "wait",
})


def _docker(*args: str, timeout: int = 30) -> str:
    offending = sorted(set(args) & MUTATING_TOKENS)
    if offending:
        raise ValueError(f"refusing docker invocation containing mutating token(s) {offending}")
    shape = command_shape(args)
    if shape not in ALLOWED_SHAPES:
        raise ValueError(
            f"refusing docker command shape {shape}: not in the read-only allowlist. "
            f"This module observes; it never mutates.")
    try:
        result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise DockerUnavailable(str(exc)) from exc
    if result.returncode != 0:
        raise DockerUnavailable(f"docker {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def available() -> bool:
    try:
        _docker("version", "--format", "{{.Server.Version}}", timeout=10)
        return True
    except DockerUnavailable:
        return False


def _redact_fields(payload: dict, fields: tuple) -> dict:
    """Drop the named fields, keeping only bounded metadata about what was there.

    Structural, not pattern-based. A secret detector only finds shapes it already knows; dropping
    the field finds them all, including the one nobody has thought of yet.
    """
    out = {k: v for k, v in (payload or {}).items() if k not in fields}
    for field in fields:
        if field in (payload or {}):
            value = (payload or {})[field]
            out[f"{field}__redacted"] = (len(value) if isinstance(value, (list, tuple, dict))
                                         else True)
    return out


def _redact(config: dict) -> dict:
    return _redact_fields(config, REDACTED_CONFIG_FIELDS)


# --- bounded association -------------------------------------------------------------------------- #

def _scoped_container_ids(decl: dict) -> list[str]:
    """Container IDs associated with THIS unit, by declaration, label or Compose project.

    Three narrow queries rather than one broad listing. What is never returned here can never be
    judged, reported or proposed for deletion downstream.
    """
    ident = decl.get("identity") or {}
    app = ident.get("application_name")
    instance = ident.get("instance")
    prefix = ui.expected_prefix(decl)
    declared = {n for names in ui._declared_artefacts(decl).values() for n in names}

    ids: list[str] = []
    label_filters = [f"{ui.LABEL_APPLICATION}={app}",
                     f"com.docker.compose.project={prefix}"]
    for label in label_filters:
        if label.endswith("=None"):
            continue
        out = _docker("ps", "-a", "--no-trunc", "--filter", f"label={label}",
                      "--format", "{{.ID}}")
        ids += out.split()
    for name in sorted(declared):
        out = _docker("ps", "-a", "--no-trunc", "--filter", f"name=^{name}$", "--format", "{{.ID}}")
        ids += out.split()
    # a labelled artefact of a DIFFERENT instance is not ours
    kept = []
    for cid in dict.fromkeys(ids):
        payload = json.loads(_docker("inspect", cid))[0]
        labels = (payload.get("Config") or {}).get("Labels") or {}
        if labels.get(ui.LABEL_APPLICATION) == app and \
                str(labels.get(ui.LABEL_INSTANCE) or "") != str(instance or ""):
            continue
        kept.append(cid)
    return kept


def _artefact(name: str, labels: dict, compose_project=None) -> dict:
    return {"name": name, "labels": dict(labels or {}), "compose_project": compose_project}


def observe(decl: dict, include_unscoped_probe: bool = False) -> dict:
    """Collect real runtime facts for one declared unit.

    Returns {"inspect": <app container payload or None>, "inventory": {...}, "containers": {...}}.
    `inspect` is the container matching the unit's declared inbound interface — the one the
    declaration's runtime posture describes.
    """
    ident = decl.get("identity") or {}
    prefix = ui.expected_prefix(decl)
    containers, inventory_containers = {}, []

    for cid in _scoped_container_ids(decl):
        payload = json.loads(_docker("inspect", cid))[0]
        config = payload.get("Config") or {}
        labels = config.get("Labels") or {}
        name = (payload.get("Name") or "").lstrip("/")
        payload = _redact_fields(payload, REDACTED_TOP_LEVEL_FIELDS)
        payload["Config"] = _redact(config)
        payload["Config"]["Labels"] = labels
        containers[name] = payload
        inventory_containers.append(
            _artefact(name, labels, labels.get("com.docker.compose.project")))

    nets = []
    for line in _docker("network", "ls", "--filter",
                        f"label={ui.LABEL_APPLICATION}={ident.get('application_name')}",
                        "--format", "{{.Name}}").split():
        payload = json.loads(_docker("network", "inspect", line))[0]
        labels = payload.get("Labels") or {}
        nets.append(_artefact(line, labels, labels.get("com.docker.compose.project")))

    vols = []
    for line in _docker("volume", "ls", "--filter",
                        f"label={ui.LABEL_APPLICATION}={ident.get('application_name')}",
                        "--format", "{{.Name}}").split():
        payload = json.loads(_docker("volume", "inspect", line))[0]
        labels = payload.get("Labels") or {}
        vols.append(_artefact(line, labels, labels.get("com.docker.compose.project")))

    inventory = {"containers": inventory_containers, "networks": nets}
    if vols:
        inventory["volumes"] = vols

    # The app container is the one carrying the declared inbound interface.
    app_name = f"{prefix}-app"
    inspect = containers.get(app_name)
    if inspect is None and len(containers) == 1:
        inspect = next(iter(containers.values()))

    if include_unscoped_probe:
        # Evidence that scoping is doing work: how much of the host we did NOT look at.
        total = len(_docker("ps", "-a", "-q").split())
        inventory["__probe__"] = {"host_containers_total": total,
                                  "in_scope": len(inventory_containers)}
    return {"inspect": inspect, "inventory": inventory, "containers": containers}


# --- effective runtime identity: what PID 1 ACTUALLY runs as ------------------------------------- #

def effective_identity(container: str) -> dict | None:
    """The real UID/GID of PID 1 inside a running container. NO `docker exec`.

    `Config.User == ""` proves only that no user was CONFIGURED. It says nothing about what the
    image entrypoint did next, so a container running PID 1 as root passed while the verifier
    reported "as declared". That is a configured fact dressed up as a runtime observation.

    The engine already exposes State.Pid, and /proc/<pid>/status carries the real Uid and Gid
    lines. Reading them is read-only, needs no shell, takes no arguments from the caller beyond a
    container name, and cannot be reused as a general execution abstraction -- there is nothing
    here to execute. That is deliberate: adding `docker exec` for this one check would have handed
    the module the exact capability the allowlist exists to withhold.

    Returns None when identity cannot be established. Callers must report NOT_VERIFIED, never PASS.
    """
    try:
        pid = _docker("inspect", container, "--format", "{{.State.Pid}}").strip()
    except DockerUnavailable:
        return None
    if not pid.isdigit() or pid == "0":          # not running
        return None
    try:
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    except OSError:
        return None
    uid = gid = None
    for line in status.splitlines():
        if line.startswith("Uid:"):
            uid = int(line.split()[1])           # real UID
        elif line.startswith("Gid:"):
            gid = int(line.split()[1])
    if uid is None or gid is None:
        return None
    return {"effective_uid": uid, "effective_gid": gid,
            "effective_user_source": f"/proc/{pid}/status of container PID 1",
            "is_root": uid == 0}


def observe_identities(containers: dict) -> dict:
    """Effective identity for each observed container, or None where it cannot be established."""
    return {name: effective_identity(name) for name in containers or {}}


def normalise_network_mode(inspect: dict, decl: dict) -> dict:
    """Compose reports NetworkMode as the service key; the declaration names the real network.

    Rewrites the observed mode to the attached network's actual name so the comparison is against
    runtime truth rather than a Compose alias. If the container is attached to something other than
    the declared network, the substitution does NOT happen and the check fails, which is the point.
    """
    if not inspect:
        return inspect
    declared = str((decl.get("runtime") or {}).get("network_mode", ""))
    attached = list(((inspect.get("NetworkSettings") or {}).get("Networks") or {}).keys())
    if declared in attached:
        inspect = json.loads(json.dumps(inspect))
        inspect.setdefault("HostConfig", {})["NetworkMode"] = declared
    return inspect


def cleanup_plan(decl: dict, inventory: dict, run_authority: str | None) -> dict:
    """What may be removed, and by whose authority. Proposal only — this module removes nothing.

    Three conditions, all required: the unit declared it, observed provenance attributes it to this
    instance, and the current run holds authority. Prefix alone is never one of them.
    """
    if not run_authority:
        return {"authorised": [], "refused_no_authority": ui.cleanup_candidates(decl, inventory)}
    return {"authorised": ui.cleanup_candidates(decl, inventory), "run_authority": run_authority}
