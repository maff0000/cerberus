"""The compute unit's external contract, and the comparison of it against runtime truth.

    THE PROJECT ROOT IS THE UNIT.

A PBG product is a compute unit: it lives in one directory, exposes ports and APIs, and gets bolted
into a larger application. Everything it owns is inside its root. Move the directory and the unit
moves; delete it and the unit is gone.

The governing doctrine is positive, not defensive:

    DECLARE THE PERMITTED INTERFACE
    DENY EVERYTHING ELSE

Enumerating escape routes is unbounded and never provably finished -- nobody listed the Docker
data-root before a unit wrote to it and a README claimed it hadn't. Under default-deny that write
would have had to be declared in order to occur.

ENFORCEMENT TRUTH. This module reports what it can actually establish and refuses to dress up the
rest. Outbound network behaviour in particular is NOT_VERIFIED: absence of egress cannot be proven
from container metadata, and claiming otherwise would be the same defect the enforcement-truth
programme removed from the control corpus.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# --- enforcement truth ---------------------------------------------------------------------------- #

DECLARED = "DECLARED"            # the unit says so; nothing has checked
OBSERVED = "OBSERVED"            # compared against the running unit
ENFORCED = "ENFORCED"            # a mechanism makes the alternative impossible
NOT_VERIFIED = "NOT_VERIFIED"    # no honest way to establish this yet

ARTEFACT_NAME = "unit-interface.yaml"

#: Declares that the unit sets no user and the image's own USER applies.
IMAGE_DEFAULT_USER = "IMAGE_DEFAULT"

#: Machine-readable ownership. Names give humans clarity; labels give tooling authority. Neither
#: substitutes for the other -- a correct label does not excuse a name that breaks the prefix rule,
#: and a matching name is not evidence of ownership.
LABEL_APPLICATION = "pbg.application"
LABEL_INSTANCE = "pbg.instance"
LABEL_CONTRACT = "pbg.unit-interface"

_DNS_LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
_SEPARATORS = re.compile(r"[\s._/-]+")

#: Credential shapes. The declaration says durable state EXISTS; it never carries what is in it.
#: Same rule as every other governed record, applied before this artefact becomes the place people
#: keep connection strings "just for reference".
_CREDENTIAL = re.compile(
    r"(?i)(://[^/\s:]+:[^@\s]+@|-----BEGIN [A-Z ]*PRIVATE KEY|"
    r"\b(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S{6,})")

_PLACEHOLDER = re.compile(r"(?i)(REDACTED|EXAMPLE|PLACEHOLDER|CHANGE[_-]?ME|<[^>]+>|\$\{[^}]+\})")


class AmbiguousApplicationName(Exception):
    """The commissioned name cannot be mapped to a runtime prefix without inventing an identity."""


def normalise_application_name(raw: str) -> str:
    """Map a commissioned application name to a deterministic runtime prefix.

    Separators become hyphens and case is folded. Anything else that would have to be DROPPED is
    refused rather than silently removed: "NEO" -> "neo" is the same identity, but "neo (staging)"
    -> "neo" is a different one, and a governance tool must not quietly decide that for you.
    Product Authority decides; this function only reports that it cannot.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise AmbiguousApplicationName("application name is empty")
    candidate = _SEPARATORS.sub("-", raw.strip().lower()).strip("-")
    if not candidate:
        raise AmbiguousApplicationName(f"{raw!r} normalises to nothing")
    dropped = sorted({c for c in candidate if not (c.isalnum() and c.isascii()) and c != "-"})
    if dropped:
        raise AmbiguousApplicationName(
            f"{raw!r} cannot be mapped unambiguously: would have to drop {dropped}. "
            "Surface for Product Authority decision rather than inventing an identity.")
    if len(candidate) > 63:
        raise AmbiguousApplicationName(f"{raw!r} normalises to more than 63 characters")
    return candidate


def expected_prefix(decl: dict) -> str:
    """<appname> or <appname>-<instance>. The instance is DECLARED, never read off the path."""
    ident = decl.get("identity") or {}
    prefix = str(ident.get("runtime_prefix", ""))
    instance = ident.get("instance")
    return f"{prefix}-{instance}" if instance else prefix


@dataclass
class Finding:
    check: str
    ok: bool
    evidence_class: str
    detail: str


@dataclass
class UnitVerdict:
    unit: str
    findings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(f.ok for f in self.findings)

    def render(self) -> str:
        lines = [f"UNIT INTERFACE — {self.unit}", ""]
        for f in self.findings:
            mark = "ok  " if f.ok else "FAIL"
            lines.append(f"  [{mark}] {f.check:34} {f.evidence_class:14} {f.detail}")
        lines.append("")
        lines.append(f"  verdict: {'PASS' if self.ok else 'FAIL'}")
        return "\n".join(lines)


def load(project_root: Path) -> dict | None:
    """Read the unit's declaration, or None if it has none."""
    import yaml
    path = Path(project_root) / "governance" / ARTEFACT_NAME
    if not path.is_file():
        path = Path(project_root) / ARTEFACT_NAME
    if not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# --- static checks: no running unit required ------------------------------------------------------ #

def _declared_mounts(decl: dict) -> list[dict]:
    out = []
    state = (decl.get("state") or {}).get("durable")
    if isinstance(state, list):
        out += state
    mounts = (decl.get("runtime") or {}).get("mounts")
    if isinstance(mounts, list):
        out += mounts
    return out


def _escapes_root(host_source: str) -> bool:
    """Does this relative source resolve outside the project root?

    Absolute is the obvious spelling. `../srv` is the other one — relative, schema-shaped, and it
    leaves the unit just as completely. Guard the class, not the instance.
    """
    source = str(host_source)
    if source.startswith("/"):
        return True
    depth = 0
    for segment in source.split("/"):
        if segment in ("", "."):
            continue
        depth += -1 if segment == ".." else 1
        if depth < 0:
            return True
    return False


def check_no_absolute_host_sources(decl: dict) -> Finding:
    """A host source must be relative AND stay inside the root. Both, or the unit is not a unit."""
    bad = [m["host_source"] for m in _declared_mounts(decl)
           if _escapes_root(m.get("host_source", ""))]
    return Finding(
        "no_absolute_host_sources", not bad, OBSERVED,
        "every declared host source is relative and resolves inside the project root" if not bad
        else f"host source(s) leaving the project root, the unit is not relocatable: {bad}")


def check_explicit_none(decl: dict) -> Finding:
    """A missing section is not permission. It is an incomplete declaration."""
    missing = [k for k in ("inbound", "outbound", "dependencies") if k not in decl]
    state = decl.get("state") or {}
    missing += [f"state.{k}" for k in ("durable", "ephemeral") if k not in state]
    runtime = decl.get("runtime") or {}
    missing += [f"runtime.{k}" for k in ("user", "privileged", "network_mode", "mounts")
                if k not in runtime]
    return Finding(
        "explicit_none_not_absence", not missing, OBSERVED,
        "every section is declared, including explicit NONE" if not missing
        else f"absent sections are not permission — declare NONE explicitly: {missing}")


def check_no_credentials(decl: dict) -> Finding:
    """The declaration states that state exists. It never carries what is in it."""
    import yaml
    blob = yaml.safe_dump(decl, sort_keys=False)
    hits = [m.group(0) for m in _CREDENTIAL.finditer(blob)
            if not _PLACEHOLDER.search(m.group(0))]
    return Finding(
        "no_credential_material", not hits, OBSERVED,
        "declaration carries no credential-shaped material" if not hits
        else f"{len(hits)} credential-shaped value(s) — reference, never reproduce")


def check_config_paths_relative(project_root: Path, config_files=("docker-compose.yml",
                                                                  "docker-compose.yaml",
                                                                  "compose.yml")) -> Finding:
    """Scan the unit's own runtime configuration for absolute bind-mount sources.

    Statically decidable, before anything is built. Catches the failure at authoring time rather
    than at audit.
    """
    root = Path(project_root)
    offenders, scanned = [], []
    for name in config_files:
        path = root / name
        if not path.is_file():
            continue
        scanned.append(name)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip().lstrip("- ").strip('"\'')
            if ":" not in stripped or stripped.startswith("#"):
                continue
            source = stripped.split(":", 1)[0]
            if source.startswith("/"):
                offenders.append(f"{name}:{lineno} {source}")
    if not scanned:
        return Finding("config_paths_relative", True, NOT_VERIFIED,
                       "no unit runtime configuration file present to scan")
    return Finding(
        "config_paths_relative", not offenders, OBSERVED,
        f"scanned {scanned}: all bind sources relative" if not offenders
        else f"absolute bind source(s): {offenders}")


def check_runtime_prefix(decl: dict) -> Finding:
    """The prefix must exist, be syntactically usable, and agree with the commissioned name."""
    ident = decl.get("identity") or {}
    app = ident.get("application_name")
    prefix = ident.get("runtime_prefix")
    instance = ident.get("instance")
    problems = []
    if not app:
        problems.append("identity.application_name is absent — there is no commissioned identity "
                        "to derive ownership from")
    if not prefix:
        problems.append("identity.runtime_prefix is absent")
    for label, value in (("runtime_prefix", prefix), ("instance", instance)):
        if value is not None and not _DNS_LABEL.match(str(value)):
            problems.append(f"identity.{label} {value!r} is not usable by container tooling "
                            "(lowercase, letters/digits/hyphens, alphanumeric at both ends)")
    if app and prefix and not problems:
        try:
            derived = normalise_application_name(str(app))
        except AmbiguousApplicationName as exc:
            problems.append(str(exc))
        else:
            if derived != prefix:
                problems.append(
                    f"identity.runtime_prefix {prefix!r} is not the normalisation of "
                    f"application_name {app!r} (which gives {derived!r}) — the prefix must trace "
                    "to the commissioned identity, not be chosen alongside it")
    return Finding(
        "runtime_prefix_valid", not problems, OBSERVED,
        f"runtime prefix {expected_prefix(decl)!r} derives from the commissioned application name"
        if not problems else "; ".join(problems))


def _artefact_name(entry) -> str:
    """An artefact entry is a bare name or an object carrying one."""
    return entry if isinstance(entry, str) else str((entry or {}).get("name", ""))


def _declared_artefacts(decl: dict) -> dict:
    art = (decl.get("runtime") or {}).get("artefacts") or {}
    return {kind: [_artefact_name(n) for n in names]
            for kind, names in art.items() if isinstance(names, list)}


def check_declared_artefact_names(decl: dict) -> Finding:
    """Every name the unit declares must carry its prefix. Generic names are host-visible."""
    prefix = expected_prefix(decl)
    if not prefix:
        return Finding("declared_artefact_names", False, OBSERVED,
                       "no runtime prefix declared, so no name can be checked against it")
    offenders = [f"{kind}:{_artefact_name(name)}" for kind, names in _declared_artefacts(decl).items()
                 for name in names if not str(_artefact_name(name)).startswith(f"{prefix}-")]
    total = sum(len(v) for v in _declared_artefacts(decl).values())
    return Finding(
        "declared_artefact_names", not offenders, OBSERVED,
        f"all {total} declared artefact name(s) carry the {prefix!r} prefix" if not offenders
        else f"declared name(s) without the {prefix!r} prefix: {offenders}")


def _owned(artefact: dict, decl: dict) -> bool:
    """Does observed provenance evidence attribute this artefact to THIS commissioned instance?"""
    ident = decl.get("identity") or {}
    labels = artefact.get("labels") or {}
    if labels.get(LABEL_APPLICATION) != ident.get("application_name"):
        return False
    if str(labels.get(LABEL_INSTANCE) or "") != str(ident.get("instance") or ""):
        return False
    return True


def _in_scope(artefact: dict, decl: dict, declared_names: set) -> bool:
    """Association BEFORE judgement.

    Every image on the host is not this unit's problem. An artefact enters scope only through
    declared configuration, provenance labels, or Compose project metadata — never through the
    mere fact of existing.
    """
    if artefact.get("name") in declared_names:
        return True
    if _owned(artefact, decl):
        return True
    return artefact.get("compose_project") == expected_prefix(decl)


def check_artefact_naming(decl: dict, inventory: dict) -> list:
    """Compare observed project-created artefacts against the declared naming contract.

    `inventory` maps kind -> [{name, labels, compose_project}], supplied by the caller so the
    checks are testable against runtime shapes that must never be created on a real host.
    """
    prefix = expected_prefix(decl)
    declared = _declared_artefacts(decl)
    declared_all = {n for names in declared.values() for n in names}
    findings, unprefixed, mismatched, collisions = [], [], [], []

    for kind, artefacts in (inventory or {}).items():
        for artefact in artefacts or []:
            name = artefact.get("name", "")
            in_scope = _in_scope(artefact, decl, declared_all)
            if in_scope and not name.startswith(f"{prefix}-"):
                unprefixed.append(f"{kind}:{name}")
            # a name that LOOKS like ours but whose provenance says otherwise
            if name.startswith(f"{prefix}-") and not _owned(artefact, decl) \
                    and name not in declared_all:
                collisions.append(f"{kind}:{name}")
        observed_names = {a.get("name") for a in artefacts or []}
        for name in declared.get(kind, []):
            # `if observed_names and ...` meant a wholly absent kind produced no mismatch at all,
            # so a unit with nothing running agreed with its own declaration. Absence IS the
            # mismatch; guarding against the empty set turned the check off exactly when it
            # mattered.
            if name not in observed_names:
                mismatched.append(f"{kind}:{name} declared, not observed")

    findings.append(Finding(
        "observed_artefact_prefix", not unprefixed, OBSERVED,
        f"every in-scope artefact carries the {prefix!r} prefix" if not unprefixed
        else f"project-created artefact(s) without the {prefix!r} prefix: {unprefixed}"))
    for kind, names in declared.items():
        if names and not (inventory or {}).get(kind):
            mismatched.append(f"{kind}: declared {names}, none observed")
    findings.append(Finding(
        "declared_matches_observed", not mismatched, OBSERVED,
        "declared artefact names agree with runtime identity" if not mismatched
        else f"declaration disagrees with runtime: {mismatched}"))
    findings.append(Finding(
        "no_prefix_collision", not collisions, OBSERVED,
        f"no unrelated artefact occupies the {prefix!r} namespace" if not collisions
        else f"name(s) in our namespace without our provenance — NOT ours to touch: {collisions}"))
    return findings


def cleanup_candidates(decl: dict, inventory: dict) -> list:
    """Artefacts this unit may remove.

    Deleting is the one operation with no undo, so it needs BOTH halves: the unit must have
    declared the artefact, AND observed provenance must attribute it to this instance. A matching
    textual prefix is a coincidence until a label says otherwise. Never delete a pre-existing
    resource merely because its name starts the same way.
    """
    declared = {n for names in _declared_artefacts(decl).values() for n in names}
    out = []
    for kind, artefacts in (inventory or {}).items():
        for artefact in artefacts or []:
            if artefact.get("name") in declared and _owned(artefact, decl):
                out.append((kind, artefact["name"]))
    return sorted(out)


def check_compose_project_naming(project_root: Path, decl: dict,
                                 config_files=("docker-compose.yml", "docker-compose.yaml",
                                               "compose.yml")) -> Finding:
    """Compose must not be left to derive host-visible names from the directory.

    Directory-derived naming makes ownership a function of where the unit is parked, so relocating
    it silently renames everything it owns. The prefix has to be governed in the file.
    """
    import yaml
    root, prefix = Path(project_root), expected_prefix(decl)
    for name in config_files:
        path = root / name
        if not path.is_file():
            continue
        spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        problems = []
        if spec.get("name") != prefix:
            problems.append(f"top-level `name:` is {spec.get('name')!r}, expected {prefix!r} — "
                            "without it Compose falls back to the directory name")
        for svc, body in (spec.get("services") or {}).items():
            cname = (body or {}).get("container_name")
            if cname and not str(cname).startswith(f"{prefix}-"):
                problems.append(f"service {svc}: container_name {cname!r} lacks the prefix")
            # Compare against the RESOLVED root. Comparing against the caller's `root` string
            # flagged `pbgfix-live-app` under a relative root of `pbgfix`, because the check was
            # really asking "does the name contain this substring" and calling it a path.
            if cname and (str(root.resolve()) in str(cname) or "/" in str(cname)):
                problems.append(f"service {svc}: container_name {cname!r} embeds a filesystem path "
                                "— the name would change when the unit is relocated")
        return Finding(
            "compose_project_naming", not problems, OBSERVED,
            f"{name} names its project {prefix!r} deterministically" if not problems
            else f"{name}: " + "; ".join(problems))
    return Finding("compose_project_naming", True, NOT_VERIFIED,
                   "no Compose file present; host-visible naming not established from configuration")


# --- observed checks: compared against a running unit --------------------------------------------- #

def check_against_runtime(decl: dict, inspect: dict, project_root: Path) -> list[Finding]:
    """Compare the declaration with `docker inspect` output for the running unit.

    `inspect` is injected rather than fetched so the checks are testable against synthetic runtime
    shapes -- including the escaping ones that must never exist on a real host.
    """
    findings: list[Finding] = []
    root = Path(project_root).resolve()
    cfg = inspect.get("Config") or {}
    host = inspect.get("HostConfig") or {}
    net = inspect.get("NetworkSettings") or {}
    runtime = decl.get("runtime") or {}

    # containment: every bind source must resolve inside the project root. THE check.
    escaped = []
    for mount in inspect.get("Mounts") or []:
        if mount.get("Type") != "bind":
            continue
        src = Path(os.path.realpath(mount.get("Source", "")))
        if not (src == root or root in src.parents):
            escaped.append(f"{mount.get('Source')} -> {mount.get('Destination')}")
    findings.append(Finding(
        "mount_sources_inside_project_root", not escaped, OBSERVED,
        "every bind source resolves inside the project root" if not escaped
        else f"bind mount(s) escape the unit: {escaped}"))

    # undeclared mounts
    declared = {m["container_path"] for m in _declared_mounts(decl)}
    observed = {m.get("Destination") for m in (inspect.get("Mounts") or [])
                if m.get("Type") == "bind"}
    undeclared = sorted(observed - declared)
    findings.append(Finding(
        "no_undeclared_mounts", not undeclared, OBSERVED,
        "observed mounts all declared" if not undeclared
        else f"mount(s) present at runtime but not declared: {undeclared}"))

    # published ports
    declared_ports = ({str(i["port"]) for i in decl["inbound"]}
                      if isinstance(decl.get("inbound"), list) else set())
    observed_ports = set()
    for spec, bindings in (net.get("Ports") or {}).items():
        if bindings:
            observed_ports.add(spec.split("/")[0])
    undeclared_ports = sorted(observed_ports - declared_ports)
    findings.append(Finding(
        "no_undeclared_ports", not undeclared_ports, OBSERVED,
        f"published ports match the declaration {sorted(declared_ports) or 'NONE'}"
        if not undeclared_ports else f"published but undeclared: {undeclared_ports}"))

    # effective user
    declared_user = str(runtime.get("user", ""))
    observed_user = str(cfg.get("User") or "")
    user_ok = observed_user == declared_user
    findings.append(Finding(
        "effective_user", user_ok, OBSERVED,
        f"runs as {observed_user!r} as declared" if user_ok
        else f"declared {declared_user!r}, observed {observed_user!r}"))

    # privileged
    declared_priv = bool(runtime.get("privileged", False))
    observed_priv = bool(host.get("Privileged", False))
    findings.append(Finding(
        "privileged_mode", declared_priv == observed_priv, OBSERVED,
        f"privileged={observed_priv} as declared" if declared_priv == observed_priv
        else f"declared privileged={declared_priv}, observed {observed_priv}"))

    # network mode
    declared_net = str(runtime.get("network_mode", ""))
    observed_net = str(host.get("NetworkMode") or "")
    findings.append(Finding(
        "network_mode", declared_net == observed_net, OBSERVED,
        f"network mode {observed_net!r} as declared" if declared_net == observed_net
        else f"declared {declared_net!r}, observed {observed_net!r}"))

    # outbound: stated honestly, never dressed up
    findings.append(Finding(
        "outbound_behaviour", True, NOT_VERIFIED,
        "absence of egress cannot be established from container metadata; declaration is "
        "DECLARED only and this check asserts nothing about actual network behaviour"))

    return findings


def container_role(name: str, prefix: str) -> str:
    """The role suffix. `pbgfix-live-sql` under prefix `pbgfix-live` is the `sql` container."""
    return name[len(prefix) + 1:] if name.startswith(f"{prefix}-") else name


def declared_containers(decl: dict) -> list[dict]:
    """Every container the unit declares, with its effective runtime posture.

    An entry may be a bare name or an object carrying per-container overrides. Unit-level
    `runtime.user/privileged/network_mode` supply the defaults, because `privileged` and
    `network_mode` are genuinely unit-wide invariants while `user` legitimately differs per
    container -- an app image running as 10001 alongside a database image running as its own user
    is normal, and forcing one value would have made the declaration lie.
    """
    runtime = decl.get("runtime") or {}
    prefix = expected_prefix(decl)
    defaults = {"user": runtime.get("user"), "privileged": runtime.get("privileged"),
                "network_mode": runtime.get("network_mode")}
    out = []
    for entry in ((runtime.get("artefacts") or {}).get("containers") or []):
        spec = {"name": entry} if isinstance(entry, str) else dict(entry)
        name = spec.get("name", "")
        merged = dict(defaults)
        merged.update({k: v for k, v in spec.items() if v is not None})
        merged["name"] = name
        merged.setdefault("role", container_role(name, prefix))
        out.append(merged)
    return out


def _observed_network_mode(payload: dict, expected: str) -> str:
    """Compose reports NetworkMode as the service alias; the declaration names the real network.

    Resolve to the attached network's actual name when the container IS attached to the declared
    one. When it is not, the raw mode is returned and the comparison fails -- which is the point.
    """
    attached = list(((payload.get("NetworkSettings") or {}).get("Networks") or {}).keys())
    if expected in attached:
        return expected
    return str((payload.get("HostConfig") or {}).get("NetworkMode") or "")


def _effective_identity_finding(spec: dict, identity: dict | None, tag: str) -> Finding:
    """What PID 1 ACTUALLY runs as, judged — not merely reported.

    IMAGE_DEFAULT means the IMAGE selects the configured user. It has never meant that any
    effective runtime identity is acceptable, but the previous branch returned ok=True
    unconditionally when no expectation was declared, so a container genuinely running as root
    passed. The strength of the control was chosen by the party being audited, and omission became
    permission — the exact failure the explicit-NONE doctrine exists to prevent, in a schema that
    states that doctrine three sections earlier.

    Resolution is one of:

        NON_ROOT_OBSERVED           observed, non-root, matches policy
        ROOT_EXPLICITLY_AUTHORISED  root, and allow_effective_root is declared true
        NOT_VERIFIED                no identity evidence — never PASS
        FAIL                        root without authorisation, or a declared mismatch
    """
    name = spec["name"]
    if identity is None:
        return Finding(
            f"effective_runtime_identity{tag}", False, NOT_VERIFIED,
            f"NOT_VERIFIED — effective runtime identity of {name} could not be established. The "
            "configured user proves nothing about what PID 1 runs as. Absent evidence never PASSes.")

    uid, gid, is_root = identity["effective_uid"], identity["effective_gid"], identity["is_root"]
    state = (f"effective_uid={uid} effective_gid={gid} is_root={str(is_root).lower()} "
             f"(source: {identity['effective_user_source']})")
    allow_root = bool(spec.get("allow_effective_root", False))

    # Root is judged BEFORE any expectation is considered. An undeclared expectation must not be
    # the thing that lets root through.
    if is_root and not allow_root:
        return Finding(
            f"effective_runtime_identity{tag}", False, OBSERVED,
            f"FAIL — {state}. PID 1 runs as root and allow_effective_root is not declared true. "
            "Root permission cannot arise through omission: declare it explicitly for this "
            "container role, or fix the image.")

    expected_uid = spec.get("effective_uid")
    if expected_uid is not None:
        if uid != int(expected_uid):
            return Finding(f"effective_runtime_identity{tag}", False, OBSERVED,
                           f"FAIL — expected effective_uid={expected_uid}, observed {state}")
        expected_gid = spec.get("effective_gid")
        if expected_gid is not None and gid != int(expected_gid):
            return Finding(f"effective_runtime_identity{tag}", False, OBSERVED,
                           f"FAIL — expected effective_gid={expected_gid}, observed {state}")
        resolution = "ROOT_EXPLICITLY_AUTHORISED" if is_root else "NON_ROOT_OBSERVED"
        return Finding(f"effective_runtime_identity{tag}", True, OBSERVED, f"{resolution} — {state}")

    declared_user = str(spec.get("user") or "")
    if declared_user and declared_user != IMAGE_DEFAULT_USER and declared_user.isdigit():
        if uid != int(declared_user):
            return Finding(
                f"effective_runtime_identity{tag}", False, OBSERVED,
                f"FAIL — configured user {declared_user!r} but PID 1 runs as {state}; "
                "configuration and runtime disagree")
        return Finding(f"effective_runtime_identity{tag}", True, OBSERVED,
                       f"NON_ROOT_OBSERVED — {state}")

    if is_root and allow_root:
        return Finding(f"effective_runtime_identity{tag}", True, OBSERVED,
                       f"ROOT_EXPLICITLY_AUTHORISED — {state}")

    # IMAGE_DEFAULT with no expectation. The schema now forbids this shape; if one reaches here it
    # is an unverified claim, and an unverified claim does not pass.
    return Finding(
        f"effective_runtime_identity{tag}", False, NOT_VERIFIED,
        f"NOT_VERIFIED — {state}. user is IMAGE_DEFAULT and no effective_uid is declared, so there "
        "is nothing to verify the observation against. IMAGE_DEFAULT alone is not a user check.")


def _per_container_findings(spec: dict, payload: dict, decl: dict, root: Path,
                            identity: dict | None = None) -> list:
    """Applicable checks for ONE container, each naming the container and its declared role."""
    name, role = spec["name"], spec.get("role", "?")
    tag = f"[{name} role={role}]"
    findings = []

    def add(check, ok, expected, observed, note=""):
        findings.append(Finding(
            f"{check}{tag}", ok, OBSERVED,
            f"as declared: {observed!r}" if ok else
            f"expected {expected!r}, observed {observed!r}{note}"))

    escaped = []
    for mount in payload.get("Mounts") or []:
        if mount.get("Type") != "bind":
            continue
        src = Path(os.path.realpath(mount.get("Source", "")))
        if not (src == root or root in src.parents):
            escaped.append(f"{mount.get('Source')} -> {mount.get('Destination')}")
    add("mount_containment", not escaped, f"all bind sources under {root}",
        escaped or "all bind sources inside the project root")

    declared_paths = {m["container_path"] for m in _declared_mounts(decl)}
    undeclared = sorted({m.get("Destination") for m in (payload.get("Mounts") or [])
                         if m.get("Type") == "bind"} - declared_paths)
    add("no_undeclared_mounts", not undeclared, "only declared mounts",
        undeclared or "only declared mounts")

    declared_ports = ({str(i["port"]) for i in decl["inbound"]}
                      if isinstance(decl.get("inbound"), list) else set())
    published = {spec_key.split("/")[0] for spec_key, bindings in
                 (((payload.get("NetworkSettings") or {}).get("Ports")) or {}).items() if bindings}
    undeclared_ports = sorted(published - declared_ports)
    add("no_undeclared_ports", not undeclared_ports, f"only {sorted(declared_ports) or 'NONE'}",
        undeclared_ports or "no undeclared publication",
        " — an internal service must not reach the host" if undeclared_ports else "")

    observed_user = str((payload.get("Config") or {}).get("User") or "")
    declared_user = str(spec.get("user") or "")
    # IMAGE_DEFAULT states that the unit sets no user and the image's own USER applies. Docker
    # reports that as an empty string. This is the CONFIGURED fact only — see below.
    expected_user = "" if declared_user == IMAGE_DEFAULT_USER else declared_user
    add("configured_user", observed_user == expected_user,
        declared_user or "(unset)", observed_user or "(image default)")
    findings.append(_effective_identity_finding(spec, identity, tag))

    observed_priv = bool((payload.get("HostConfig") or {}).get("Privileged", False))
    add("privileged_mode", observed_priv == bool(spec.get("privileged", False)),
        bool(spec.get("privileged", False)), observed_priv)

    expected_net = str(spec.get("network_mode") or "")
    add("network_mode", _observed_network_mode(payload, expected_net) == expected_net,
        expected_net, _observed_network_mode(payload, expected_net))
    return findings


def check_unit_runtime(decl: dict, containers: dict, project_root: Path,
                       identities: dict | None = None) -> list:
    """Evaluate the WHOLE unit, not its front door.

    The doctrine is that PROJECT_ROOT is the unit ownership boundary, and the unit is every
    container in it. Checking only the app container certified a unit whose database bind-mounted
    the host filesystem. Every declared container is required to be present, and every observed
    container is judged; no container's pass may absorb another's failure.
    """
    root = Path(project_root).resolve()
    findings: list[Finding] = []
    observed_names = set(containers or {})
    specs = declared_containers(decl)

    # Absence is a failure, never a silent pass. Nothing observed cannot mean nothing wrong.
    if not observed_names:
        findings.append(Finding(
            "unit_running", False, OBSERVED,
            f"no container of this unit is observed; {len(specs)} declared "
            f"({[s['name'] for s in specs]}). An empty scope proves nothing and passes nothing."))
        return findings
    findings.append(Finding("unit_running", True, OBSERVED,
                            f"{len(observed_names)} container(s) observed"))

    missing = [s["name"] for s in specs if s["name"] not in observed_names]
    findings.append(Finding(
        "declared_containers_present", not missing, OBSERVED,
        f"all {len(specs)} declared container(s) observed" if not missing
        else f"declared but absent at runtime: {missing}"))

    for spec in specs:
        payload = (containers or {}).get(spec["name"])
        if payload is None:
            continue
        findings += _per_container_findings(spec, payload, decl, root,
                                            (identities or {}).get(spec["name"]))

    # Anything observed in scope that the unit never declared is still the unit's problem.
    for name in sorted(observed_names - {s["name"] for s in specs}):
        findings += _per_container_findings(
            {"name": name, "role": "UNDECLARED",
             "user": (decl.get("runtime") or {}).get("user"),
             "privileged": (decl.get("runtime") or {}).get("privileged"),
             "network_mode": (decl.get("runtime") or {}).get("network_mode")},
            containers[name], decl, root, (identities or {}).get(name))

    findings.append(Finding(
        "outbound_behaviour", True, NOT_VERIFIED,
        "absence of egress cannot be established from container metadata; declaration is "
        "DECLARED only and this check asserts nothing about actual network behaviour"))
    return findings


def check_declared_mounts_present(decl: dict, containers: dict) -> Finding:
    """Every declared mount must actually exist somewhere in the unit.

    The counterpart to no_undeclared_mounts, and it needs the WHOLE unit: durable state belongs to
    the SQL and Redis containers, so checking it against the app container alone would condemn a
    correct declaration. `containers` maps name -> inspect payload for the unit's containers.
    """
    declared = {m["container_path"] for m in _declared_mounts(decl)}
    observed = {m.get("Destination") for payload in (containers or {}).values()
                for m in (payload.get("Mounts") or []) if m.get("Type") == "bind"}
    missing = sorted(declared - observed)
    return Finding(
        "declared_mounts_present", not missing, OBSERVED,
        f"all {len(declared)} declared mount(s) observed across the unit" if not missing
        else f"declared but absent at runtime: {missing}")


def verify(project_root: Path, containers: dict | None = None,
           inventory: dict | None = None, identities: dict | None = None) -> UnitVerdict:
    """Full verification of the WHOLE unit.

    `containers` maps container name -> docker inspect payload for every container associated with
    this unit. It replaced a single `inspect` payload: passing one container meant containment,
    ports, user and privilege were verified on the app and assumed for the database, and a unit
    whose SQL container bind-mounted the host filesystem was certified PASS.
    """
    decl = load(project_root)
    if decl is None:
        return UnitVerdict("(none)", [Finding(
            "declaration_present", False, OBSERVED,
            f"no {ARTEFACT_NAME}; the unit declares no external contract")])

    unit = (decl.get("identity") or {}).get("unit", "(unnamed)")
    findings = [
        Finding("declaration_present", True, OBSERVED, f"{ARTEFACT_NAME} found"),
        check_explicit_none(decl),
        check_no_absolute_host_sources(decl),
        check_no_credentials(decl),
        check_config_paths_relative(project_root),
        check_runtime_prefix(decl),
        check_declared_artefact_names(decl),
        check_compose_project_naming(project_root, decl),
    ]
    # Two independent runtime sources. Each says NOT_VERIFIED in its own right when absent —
    # having one is not evidence about the other.
    if containers is not None:
        findings += check_unit_runtime(decl, containers, project_root, identities)
        # The counterpart to no_undeclared_mounts, and part of the PRODUCT verdict rather than a
        # helper the tests call. It existed and was never wired in, so the defect it was written
        # for was closed in the suite and open in the product.
        findings.append(check_declared_mounts_present(decl, containers))
    else:
        findings.append(Finding(
            "runtime_comparison", True, NOT_VERIFIED,
            "no running unit supplied; declaration not compared against runtime truth"))
    if inventory is not None:
        findings += check_artefact_naming(decl, inventory)
    else:
        findings.append(Finding(
            "artefact_naming_observed", True, NOT_VERIFIED,
            "no runtime inventory supplied; declared names not compared against host artefacts"))
    return UnitVerdict(unit, findings)


def summary_line(project_root: Path) -> str:
    """One line for the boot verdict."""
    decl = load(project_root)
    if decl is None:
        return "UNIT INTERFACE  (none declared)"
    ident = decl.get("identity") or {}
    prefix = expected_prefix(decl) or "(no prefix)"
    return (f"UNIT INTERFACE  {ident.get('unit','(unnamed)')} "
            f"[{ident.get('contract_id','?')} v{ident.get('declaration_version','?')}] "
            f"runtime={prefix}-* {decl.get('maturity','')}")
