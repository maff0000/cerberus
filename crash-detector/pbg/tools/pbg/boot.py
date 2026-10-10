"""The boot path.

    Hi PL  ->  pl_boot()  ->  the Project Lead runs the application through PBG.

There is one. PBG is the Project Lead's tooling, not an actor to be addressed or booted, and work
on PBG itself is an ordinary Engineer dispatch whose writable scope names framework paths. See the
note at the foot of this module for what was removed and why.

Every fact carries where it came from. A fact that cannot be derived is reported UNAVAILABLE with
the reason -- never defaulted, never inferred from a plausible neighbour, never carried over from a
previous run. That is the whole discipline here: boot reports what the canonical artefacts say, and
says so when they say nothing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from . import burden, continuity, controls as controls_mod, verification, versioning

# --- fact states -------------------------------------------------------------------------------- #

DERIVED = "DERIVED"
UNAVAILABLE = "UNAVAILABLE"
CONTRADICTED = "CONTRADICTED"

# --- contexts ----------------------------------------------------------------------------------- #

CANONICAL_FRAMEWORK_SOURCE = "CANONICAL_FRAMEWORK_SOURCE"
INSTALLED_SNAPSHOT = "INSTALLED_SNAPSHOT"
CONSUMING_PROJECT = "CONSUMING_PROJECT"
UNKNOWN_CONTEXT = "UNKNOWN_CONTEXT"

#: Product Authority s16. The eighteen facts a normal Project Lead boot must derive.
PL_REQUIRED_FACTS = (
    "project_identity", "product_authority", "assigned_role", "pid_identity",
    "blueprint_identity", "roadmap_identity", "repository", "branch", "worktree",
    "observed_sha", "continuity_state", "current_phase", "current_work", "held_actions",
    "actor_actions", "blocking_failures", "human_decisions", "next_safe_action",
)


@dataclass
class Fact:
    name: str
    value: object
    source: str
    state: str = DERIVED

    @property
    def known(self) -> bool:
        return self.state == DERIVED


@dataclass
class BootVerdict:
    path: str                       # PROJECT_LEAD -- the only boot path
    context: str
    verdict: str                    # GREEN | AMBER | RED
    facts: dict[str, Fact] = field(default_factory=dict)
    blocking: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    unit_interface: str = "UNIT INTERFACE  (not resolved)"

    def value(self, name: str):
        f = self.facts.get(name)
        return f.value if f and f.known else None

    def missing(self) -> list[str]:
        return [n for n, f in self.facts.items() if not f.known]

    def render(self) -> str:
        # The bound unit goes FIRST and unmissable. An operator in the wrong terminal should see
        # it in the opening lines, not three paragraphs down.
        project = self.value("project_identity") or "(unresolved)"
        pid = self.value("pid_identity") or "(no PID)"
        root = self.value("worktree") or "(unresolved)"
        lines = [
            "PROJECT LEAD BOOT VERDICT",
            "",
            f"  PROJECT        {project}",
            f"  PID            {pid}",
            f"  PROJECT_ROOT   {root}",
            f"  {self.unit_interface}",
            "",
            f"Context   : {self.context}", f"Verdict   : {self.verdict}", ""]
        for name, f in self.facts.items():
            mark = " " if f.known else "!"
            lines.append(f"{mark} {name:28} {f.value}")
            if not f.known:
                lines.append(f"  {'':28} ({f.state}: {f.source})")
        if self.blocking:
            lines += ["", "BLOCKING:"] + [f"  - {b}" for b in self.blocking]
        if self.notes:
            lines += ["", "NOTES:"] + [f"  - {n}" for n in self.notes]
        return "\n".join(lines)


# --- context detection -------------------------------------------------------------------------- #

def detect_context(root: Path) -> str:
    """Canonical source, installed snapshot, or a project that consumes one.

    Distinguished by what is PRESENT, not by directory name -- a directory called `pbg` proves
    nothing, which is the same reasoning that made framework identity digest-based rather than
    path-based.
    """
    root = Path(root)
    develops_the_framework = (
        (root / "docs" / "architecture").is_dir()
        and (root / "tests").is_dir()
        and (root / "controls").is_dir()
    )
    if develops_the_framework:
        return CANONICAL_FRAMEWORK_SOURCE
    if (root / "RELEASE_MANIFEST").is_file() and (root / "controls").is_dir():
        return INSTALLED_SNAPSHOT
    if find_framework(root) is not None:
        return CONSUMING_PROJECT
    return UNKNOWN_CONTEXT


def find_framework(project_root: Path) -> Path | None:
    """Locate the pinned snapshot inside a consuming project."""
    for candidate in (project_root / "pbg", project_root / "governance" / "pbg"):
        if (candidate / "VERSION").is_file() and (candidate / "controls").is_dir():
            return candidate
    return None


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _artefact_fact(name: str, path: Path, label: str) -> Fact:
    if not path.is_file():
        return Fact(name, None, f"{label} not found at {path.name}", UNAVAILABLE)
    return Fact(name, f"{path.name}@{_digest(path)}", f"{label} read from {path.name}")


def _read_authority(project_root: Path) -> tuple[dict | None, str]:
    """The durable authority record. Never a role file, never a greeting (PBG-BOOT-002)."""
    auth_dir = project_root / "governance" / "authority"
    if not auth_dir.is_dir():
        return None, f"no authority directory at {auth_dir}"
    records = sorted(auth_dir.glob("*.yaml"))
    if not records:
        return None, f"no authority record in {auth_dir}"
    active = []
    for path in records:
        try:
            doc = continuity.parse_strict(path.read_text(encoding="utf-8"))
        except continuity.ContinuityError as exc:
            return None, f"authority record {path.name} is unparseable: {exc}"
        if str(doc.get("status", "")).upper() == "ACTIVE":
            active.append((path, doc))
    if not active:
        return None, "authority records exist but none is ACTIVE"
    if len(active) > 1:
        return None, f"{len(active)} ACTIVE authority records; ambiguous assignment"
    path, doc = active[0]
    return doc, f"authority record {path.name}"


# --- the normal path ---------------------------------------------------------------------------- #

def pl_boot(project_root: Path) -> BootVerdict:
    """Boot the application Project Lead. The only boot there is."""
    project_root = Path(project_root)
    v = BootVerdict(path="PROJECT_LEAD", context=detect_context(project_root), verdict="GREEN")

    # Resolved FIRST, from THIS project's own artefact, and never from a neighbouring directory or
    # from the directory's name. It is independent of the framework snapshot and of the PID, so a
    # degraded boot must still say which unit it is pointed at — that is when it matters most.
    from . import unit_interface as ui_mod
    v.unit_interface = ui_mod.summary_line(project_root)
    if ui_mod.load(project_root) is None:
        v.notes.append("no unit interface declared — the unit states no external contract")

    # --- project instruction boundary (independent Assurance finding F21) ------------------------------------------------ #
    #
    # Resolved BEFORE the framework snapshot, and deliberately before the early return below. The
    # audit's finding was that PBGv2 shipped a working contamination detector and never pointed it
    # at its own root; putting it after the `fw is None` return would reproduce that exactly — the
    # canonical framework source is the one root that takes the early exit.
    #
    # An instruction file grants nothing (PBG-BOOT-001). What matters here is WHOSE bytes an agent
    # would be reading: a runtime that walks upward inherits host doctrine the project never
    # declared, and a run that looks disciplined because a parent file supplied the discipline is
    # worse than a failed run, because it reads as a pass.
    from . import instructions as instr_mod
    ires = instr_mod.resolve(project_root)
    v.facts["project_instructions"] = Fact(
        "project_instructions", str(ires.path) if ires.path else None, ires.detail,
        DERIVED if ires.usable else UNAVAILABLE)
    if ires.contaminated:
        v.notes.append(
            "instruction files ABOVE PROJECT_ROOT would be inherited by an upward-walking "
            "runtime, and none of them are this project's: " + "; ".join(ires.inherited))
        if v.verdict == "GREEN":
            v.verdict = "AMBER"

    fw = find_framework(project_root)
    if fw is None:
        v.facts["project_identity"] = Fact(
            "project_identity", None, "no pinned pbg/ snapshot found", UNAVAILABLE)
        v.blocking.append("no pinned framework snapshot — this is not a governed project")
        v.verdict = "RED"
        for name in PL_REQUIRED_FACTS:
            v.facts.setdefault(name, Fact(name, None, "framework not located", UNAVAILABLE))
        return v

    # --- product artefacts --------------------------------------------------------------------- #
    pid = project_root / "PID.md"
    v.facts["pid_identity"] = _artefact_fact("pid_identity", pid, "PID")
    v.facts["blueprint_identity"] = _artefact_fact(
        "blueprint_identity", project_root / "BLUEPRINT.md", "Blueprint")
    v.facts["roadmap_identity"] = _artefact_fact(
        "roadmap_identity", project_root / "ROADMAP.md", "Roadmap")

    if not pid.is_file():
        v.blocking.append("PID_DISCOVERY_REQUIRED — existing code is evidence of current "
                          "implementation, not authorised product intent (PBG-PID-003)")
        v.verdict = "AMBER"

    install = project_root / "governance" / "pbg-installation.yaml"
    project_name = None
    product_authority = None
    if install.is_file():
        try:
            rec = continuity.parse_strict(install.read_text(encoding="utf-8"))
            project_name = rec.get("project_name") or rec.get("project")
            product_authority = rec.get("product_authority")
        except continuity.ContinuityError as exc:
            v.notes.append(f"installation record unparseable: {exc}")

    v.facts["project_identity"] = (
        Fact("project_identity", project_name, "installation record")
        if project_name else
        Fact("project_identity", None, "no project name in installation record", UNAVAILABLE))
    v.facts["product_authority"] = (
        Fact("product_authority", product_authority, "installation record")
        if product_authority else
        Fact("product_authority", None,
             "no product authority declared in the installation record", UNAVAILABLE))

    # --- role, from the durable record only ---------------------------------------------------- #
    auth, auth_src = _read_authority(project_root)
    if auth and auth.get("assigned_role"):
        v.facts["assigned_role"] = Fact("assigned_role", auth["assigned_role"], auth_src)
        if auth["assigned_role"] != "PROJECT_LEAD":
            v.notes.append(
                f"authority assigns {auth['assigned_role']}, not PROJECT_LEAD — "
                f"boot the contract that was actually assigned")
    else:
        v.facts["assigned_role"] = Fact("assigned_role", None, auth_src, UNAVAILABLE)
        v.blocking.append("no valid role assignment — boot fails closed (PBG-BOOT-002, non-waivable)")
        v.verdict = "RED"

    # --- observed repository state ------------------------------------------------------------- #
    try:
        obs = continuity.observe(project_root)
        v.facts["repository"] = Fact("repository", obs.get("repository") or str(project_root),
                                     "git observation")
        v.facts["branch"] = Fact("branch", obs.get("branch"), "git observation")
        v.facts["worktree"] = Fact("worktree", str(project_root), "filesystem")
        v.facts["observed_sha"] = (
            Fact("observed_sha", obs.get("current_sha"), "git observation")
            if obs.get("current_sha") else
            Fact("observed_sha", None, "no commits in this repository", UNAVAILABLE))
    except Exception as exc:                                  # pragma: no cover - defensive
        for name in ("repository", "branch", "worktree", "observed_sha"):
            v.facts[name] = Fact(name, None, f"git unavailable: {exc}", UNAVAILABLE)

    # --- continuity ---------------------------------------------------------------------------- #
    aw_path = project_root / "governance" / "engineering" / "ACTIVE_WORK.yaml"
    try:
        res = continuity.resume(project_root, framework_root=fw)
        v.facts["continuity_state"] = Fact(
            "continuity_state", f"{res.continuity_class}/{res.resume_verdict}", "pbg resume")
        if res.resume_verdict == "RESUME_BLOCKED":
            v.blocking.append(f"continuity invalid: {res.continuity_class} — read-only diagnosis "
                              f"permitted, normal boot blocked (PBG-CONT-006)")
            v.verdict = "RED"
        elif res.resume_verdict == "RESUME_AMBER" and v.verdict == "GREEN":
            v.verdict = "AMBER"
    except Exception as exc:
        v.facts["continuity_state"] = Fact(
            "continuity_state", None, f"continuity unreadable: {exc}", UNAVAILABLE)
        v.blocking.append("continuity could not be evaluated")
        v.verdict = "RED"

    aw = {}
    if aw_path.is_file():
        try:
            aw = continuity.parse_strict(aw_path.read_text(encoding="utf-8"))
        except continuity.ContinuityError as exc:
            v.notes.append(f"Active Work unparseable: {exc}")

    def from_aw(name: str, key: str, label: str) -> Fact:
        if key in aw and aw[key] not in (None, "", [], {}):
            return Fact(name, aw[key], f"Active Work: {key}")
        return Fact(name, None, f"Active Work has no {key}", UNAVAILABLE)

    v.facts["current_phase"] = from_aw("current_phase", "current_phase", "phase")
    v.facts["current_work"] = from_aw("current_work", "current_block", "bounded work")
    v.facts["next_safe_action"] = from_aw("next_safe_action", "next_safe_action", "next action")
    v.facts["held_actions"] = Fact(
        "held_actions", [h.get("id") for h in (aw.get("held_actions") or [])],
        "Active Work: held_actions")
    v.facts["human_decisions"] = Fact(
        "human_decisions", list(aw.get("open_decisions") or []), "Active Work: open_decisions")

    # --- actor view ---------------------------------------------------------------------------- #
    try:
        work_type = aw.get("work_type") or "TASK"
        if work_type not in ("TASK", "CHANGE", "CONTROLLED_ACTION", "INCIDENT"):
            work_type = "TASK"
        scenario = burden.Scenario(
            name="boot", work_type=work_type,
            objective=str(aw.get("objective") or "current bounded work"))
        view = burden.actor_view(fw, scenario)
        v.facts["actor_actions"] = Fact("actor_actions", sorted(view.actions),
                                        "control burden actor view")
        blocking_controls = sorted(view.blocking)
        v.facts["blocking_failures"] = Fact("blocking_failures", blocking_controls,
                                            "control burden actor view")
        if blocking_controls and v.verdict == "GREEN":
            v.verdict = "AMBER"
        v.facts["human_decisions"] = Fact(
            "human_decisions",
            sorted(set(view.human_decisions) | set(map(str, aw.get("open_decisions") or []))),
            "actor view + Active Work open_decisions")
    except Exception as exc:
        for name in ("actor_actions", "blocking_failures"):
            v.facts[name] = Fact(name, None, f"actor view unavailable: {exc}", UNAVAILABLE)

    for name in PL_REQUIRED_FACTS:
        v.facts.setdefault(name, Fact(name, None, "not derived", UNAVAILABLE))
    return v


# --------------------------------------------------------------------------------------------- #
# There is no second boot path.
#
# An earlier design shipped `maintenance_boot()` behind a `Hi PBG` greeting, with its own modes,
# authority records and verdict shape. Product Authority removed it 2026-07-30: it was a second
# chain of command wearing a boot path's clothes, and a consuming project would have inherited an
# authority layer it never needed.
#
# PBG is the Project Lead's tooling. When PBG itself needs work, that is ordinary bounded Engineer
# work under an authority record whose writable_scope happens to include framework paths -- the
# existing scope model already expresses it, so no mode, greeting or role is required.
# --------------------------------------------------------------------------------------------- #
