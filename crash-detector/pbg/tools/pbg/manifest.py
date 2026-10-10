"""Project manifest resolution and weakening detection.

Implements PBG-CTRL-004: a manifest may describe HOW a control is satisfied. It may never decide
WHETHER a mandatory control applies.

A configurable gate that a manifest can quietly empty is the mirror-image of PBGv1's failure —
where a rigid gate forced a project to build a 330-line adapter. Both end in a control that does
not run.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import controls as controls_mod
from . import validation as vld
from . import evidence_resolution as er

#: Assurance levels, ordered. A manifest may raise; it may never lower.
ASSURANCE_ORDER = ["L0", "L1", "L2", "L3", "L4"]


@dataclass(frozen=True)
class ManifestIssue:
    field: str
    reason: str
    severity: str = "RED"

    def render(self) -> str:
        return f"[{self.severity}] manifest.{self.field}: {self.reason}"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# --------------------------------------------------------------------------------------------- #
# Resolution, bounded to PROJECT_ROOT (independent Assurance finding F19)
#
# THE DEFECT. Resolution searched `root/pbg-manifest.yaml`, then `root/governance/pbg-manifest.yaml`,
# then `root.parent/pbg-manifest.yaml`. The third is parent-directory inheritance of a GOVERNANCE
# ARTEFACT. A well-formed manifest belonging to somebody else, sitting one directory up, was fully
# consumed: PBG-CTRL-004 reported PASS having validated a file the project does not own, and its
# digest was recorded as this project's evidence. A malformed one aborted `pbg validate` with a raw
# AttributeError.
#
# Neither could grant authority or turn a failing check green, so the blast radius was bounded. What
# it could do is report a control as satisfied on the strength of a foreign artefact, which is a
# false green, and let a file the project does not own crash the project's own validation.
#
# THE RULE. A project's governance comes from inside the project. There is no upward search, no
# `/srv` fallback, no sibling lookup and no ambient current-working-directory influence. What cannot
# be found inside PROJECT_ROOT is ABSENT — a controlled, named state — not something to go looking
# for elsewhere.
# --------------------------------------------------------------------------------------------- #

#: The ONLY locations a project manifest is read from, both PROJECT_ROOT-relative.
#:
#: `governance/` is retained as an implementation choice and recorded as one: projects that keep
#: governance artefacts together were already using it, it is inside PROJECT_ROOT, and removing it
#: would be a breaking change that F19 does not require. What F19 requires is that every location is
#: INSIDE the project, and both of these are.
MANIFEST_LOCATIONS = ("pbg-manifest.yaml", "governance/pbg-manifest.yaml")

RESOLVED = "RESOLVED"
ABSENT = "ABSENT"
MALFORMED = "MALFORMED"
OUTSIDE_PROJECT_ROOT = "OUTSIDE_PROJECT_ROOT"


@dataclass(frozen=True)
class ManifestResolution:
    """Where the manifest came from, what ELSE was there, and whether it is usable.

    A-4. Two in-root locations are permitted, and when both existed the root file won SILENTLY: the
    shadowed copy was read by nobody and mentioned to nobody. Independent Assurance placed that in
    the same class as the nested-field defect — a second copy nobody watches — and the class is what
    gets closed. `shadowed` names every further permitted location that also exists, and `findings`
    carries the sentence a human reads — including, when two copies exist whose bytes DISAGREE, that
    they do.
    """
    status: str
    path: Path | None
    detail: str
    manifest: dict | None = None
    shadowed: tuple = ()
    findings: tuple = ()

    @property
    def usable(self) -> bool:
        return self.status == RESOLVED

    @property
    def blocking(self) -> bool:
        """ABSENT is a legitimate state; a project need not ship a manifest.

        MALFORMED and OUTSIDE_PROJECT_ROOT are not. Something exists, it was meant to govern this
        project, and it cannot be read or does not belong — that is a refusal, not a shrug.

        A SHADOWED sibling is neither: the canonical source is declared, so which file governs is a
        rule rather than an accident. It is REPORTED in `findings` and surfaced by `pbg validate`,
        which is what "never silently ignored" requires.
        """
        return self.status in (MALFORMED, OUTSIDE_PROJECT_ROOT)

    def render(self) -> str:
        lines = [f"{self.status}: {self.detail}"]
        lines += [f"  - {f}" for f in self.findings]
        return "\n".join(lines)


def _contained(path: Path, project_root: Path) -> bool:
    """True only if `path` is genuinely inside PROJECT_ROOT once every link is followed.

    `resolve()` before comparing, so a symlink pointing out of the tree — or a `..` segment — is
    judged by where it LANDS rather than by how it is spelled.
    """
    try:
        path.resolve().relative_to(project_root.resolve())
        return True
    except ValueError:
        return False


def resolve(project_root: Path, override: Path | None = None) -> ManifestResolution:
    """Resolve the project manifest from inside PROJECT_ROOT, or say precisely why not.

    `override` is the `--project-manifest` flag. It changes WHICH of the permitted locations is
    used; it does not lift the boundary. A flag that can point the manifest check at another
    project's file would reintroduce F19 through the command line.
    """
    project_root = Path(project_root)

    if override is not None:
        candidate = Path(override)
        if not candidate.is_absolute():
            candidate = project_root / candidate
        if not _contained(candidate, project_root):
            return ManifestResolution(
                OUTSIDE_PROJECT_ROOT, candidate,
                f"--project-manifest {candidate} resolves outside PROJECT_ROOT "
                f"{project_root}; a project's manifest is part of the project. Refusing rather "
                "than validating a foreign artefact as if it were this project's own.")
        if not candidate.is_file():
            return ManifestResolution(
                ABSENT, candidate,
                f"--project-manifest {candidate} does not exist")
        return _read(candidate)

    # A-4: ENUMERATE the permitted locations rather than returning the first that exists. The
    # selection rule is unchanged — `MANIFEST_LOCATIONS` is a declared preference order and moving
    # which file wins would be a breaking change nobody asked for. What changes is that the losers
    # are named, and that two copies whose bytes differ say so.
    found = er.resolve_canonical_file("project manifest", project_root, MANIFEST_LOCATIONS)
    if found.status == er.ABSENT:
        searched = ", ".join(str(project_root / loc) for loc in MANIFEST_LOCATIONS)
        return ManifestResolution(
            ABSENT, None,
            f"no project manifest inside PROJECT_ROOT {project_root} (searched: {searched}). "
            "No parent directory, sibling project or host location is consulted.")

    location, candidate = found.selected_location, found.selected
    if not _contained(candidate, project_root):
        return ManifestResolution(
            OUTSIDE_PROJECT_ROOT, candidate,
            f"{location} resolves to {candidate.resolve()}, which is outside PROJECT_ROOT "
            f"{project_root.resolve()} — a symlink or traversal escape. Refused.",
            shadowed=tuple(found.shadowed), findings=tuple(found.findings))

    # DECLARED CANONICAL, not first-past-the-post. `MANIFEST_LOCATIONS` is a declared precedence and
    # the root file still wins — that is the "one canonical source is DECLARED" half of the required
    # repair, and changing which file wins would break projects for no finding's sake. What is
    # repaired is the SILENCE: the shadow is named in `findings`, surfaced at default verbosity by
    # `pbg validate`, and a shadow whose bytes DISAGREE says so in the same breath. A refusal here
    # was considered and rejected: with a declared precedence, selecting the canonical copy is a
    # rule, not path order, and refusing would break a project that legitimately keeps both.
    result = _read(candidate)
    return ManifestResolution(result.status, result.path, result.detail, result.manifest,
                              shadowed=tuple(found.shadowed), findings=tuple(found.findings))


def _read(path: Path) -> ManifestResolution:
    """Parse one manifest. Every failure mode becomes a status, never a traceback."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ManifestResolution(MALFORMED, path, f"{path} cannot be read: {exc}")
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return ManifestResolution(
            MALFORMED, path, f"{path} is not valid YAML: {str(exc).splitlines()[0]}")
    if parsed is None:
        # An empty file declares nothing, which is exactly what no manifest declares.
        return ManifestResolution(RESOLVED, path, f"manifest found at {path} (empty)", {})
    if not isinstance(parsed, dict):
        return ManifestResolution(
            MALFORMED, path,
            f"{path} parsed as {type(parsed).__name__}, not a mapping; a manifest is a mapping of "
            "configuration blocks. Previously this reached the checker and aborted `pbg validate` "
            "with a raw AttributeError.")
    return ManifestResolution(RESOLVED, path, f"manifest found at {path}", parsed)


def digest(manifest: dict) -> str:
    """Stable digest of the resolved configuration. Goes into every attestation.

    An auditor can then detect a manifest quietly loosened between closes.
    """
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def mandatory_control_ids(framework_root: Path) -> set[str]:
    return {
        cid
        for cid, rec in controls_mod.all_controls(framework_root).items()
        if rec.get("mandatory_or_conditional") == "MANDATORY" and rec.get("status") == "ACTIVE"
    }


def check(framework_root: Path, manifest: dict,
          *, source: str = "pbg-manifest.yaml") -> list[ManifestIssue]:
    """Reject a manifest that weakens the framework. This is the whole point of PBG-CTRL-004.

    independent Assurance finding N4. Every structural access below goes through `validation`, which cannot raise. The
    previous code used `manifest.get("project", {}).get(...)`, and the `or {}` idiom beside it, and
    both guard against None and NOT against a scalar: `"hello" or {}` is `"hello"`, and the next
    `.get` was an unhandled AttributeError — a raw traceback and exit 1 where a governed diagnosis
    belonged.

    A try/except at that one line would repair the instance and leave the class, which is the
    pattern this cycle has now met four times. A project that writes the wrong SHAPE into any block
    of its manifest now gets a finding naming the exact field and the type found, from one shared
    mechanism.
    """
    issues: list[ManifestIssue] = []
    mandatory = mandatory_control_ids(framework_root)

    def structural(findings) -> None:
        for finding in findings:
            issues.append(ManifestIssue(finding.field or "(root)", finding.detail))

    structural(vld.root_must_be_mapping(manifest, path=source))
    if not isinstance(manifest, dict):
        return issues                                      # refused whole; nothing below can read it

    controls_block, findings = vld.mapping_at(manifest, "controls", path=source)
    structural(findings)

    # 1. A manifest may not remove a mandatory control.
    raw_disabled, findings = vld.sequence_at(controls_block, "disabled", path=source,
                                             field="controls.disabled")
    structural(findings)
    disabled = set(raw_disabled)
    for cid in sorted(disabled & mandatory):
        issues.append(ManifestIssue("controls.disabled", f"{cid} is mandatory and cannot be disabled"))
    for cid in sorted(disabled - mandatory):
        issues.append(
            ManifestIssue(
                "controls.disabled",
                f"{cid} disabled without an exception record — use controls.exceptions",
                severity="AMBER",
            )
        )

    # 2. A manifest may not mark an applicable mandatory control not applicable.
    raw_forced, findings = vld.sequence_at(controls_block, "force_not_applicable", path=source,
                                           field="controls.force_not_applicable")
    structural(findings)
    forced_na = set(raw_forced)
    for cid in sorted(forced_na & mandatory):
        issues.append(
            ManifestIssue(
                "controls.force_not_applicable",
                f"{cid} is mandatory; applicability is derived by the framework, not declared",
            )
        )

    # 3. A manifest may not reinterpret a required outcome.
    overrides, findings = vld.mapping_at(controls_block, "required_outcome_overrides",
                                         path=source,
                                         field="controls.required_outcome_overrides")
    structural(findings)
    for cid in sorted(overrides):
        issues.append(
            ManifestIssue(
                "controls.required_outcome_overrides",
                f"{cid}: a project may not reinterpret a control's required outcome",
            )
        )

    # 4. Exceptions must be time-bounded, authorised, and never applied to a non-waivable control.
    non_waivable = {
        cid
        for cid, rec in controls_mod.all_controls(framework_root).items()
        if rec.get("exception_policy") == "NON_WAIVABLE"
    }
    exceptions, findings = vld.sequence_at(controls_block, "exceptions", path=source,
                                           field="controls.exceptions")
    structural(findings)
    for exc in exceptions:
        if not isinstance(exc, dict):
            issues.append(ManifestIssue(
                "controls.exceptions",
                f"each exception must be a mapping; found {type(exc).__name__}"))
            continue
        cid = exc.get("control_id", "?")
        if cid in non_waivable:
            issues.append(
                ManifestIssue("controls.exceptions", f"{cid} is NON_WAIVABLE and cannot be excepted")
            )
        for required in ("reason", "approved_by", "expires_utc", "compensating_controls", "residual_risk"):
            if not exc.get(required):
                issues.append(
                    ManifestIssue("controls.exceptions", f"{cid}: exception missing {required}")
                )

    # 5. A manifest may raise assurance levels, never lower a mandatory one.
    levels, findings = vld.mapping_at(manifest, "assurance_levels", path=source)
    structural(findings)
    for work_type, level in levels.items():
        floor = FRAMEWORK_ASSURANCE_FLOOR.get(work_type)
        if floor is None:
            continue
        if level not in ASSURANCE_ORDER:
            issues.append(ManifestIssue("assurance_levels", f"{work_type}: unknown level {level!r}"))
        elif ASSURANCE_ORDER.index(level) < ASSURANCE_ORDER.index(floor):
            issues.append(
                ManifestIssue(
                    "assurance_levels",
                    f"{work_type}: {level} is below the framework floor {floor}",
                )
            )

    # 6. A manifest may not authorise role self-assignment.
    roles_block, findings = vld.mapping_at(manifest, "roles", path=source)
    structural(findings)
    if roles_block.get("allow_self_assignment"):
        issues.append(
            ManifestIssue("roles.allow_self_assignment", "role self-assignment is never permitted (PBG-BOOT-002)")
        )

    # 7. A manifest may not create cross-project write authority.
    #
    # THE REPORTED CRASH SITE. `manifest.get("project", {}).get(...)` with a scalar `project` key
    # raised AttributeError here.
    project_block, findings = vld.mapping_at(manifest, "project", path=source)
    structural(findings)
    refs, findings = vld.sequence_at(project_block, "read_only_reference_projects", path=source,
                                     field="project.read_only_reference_projects")
    structural(findings)
    for ref in refs:
        if isinstance(ref, dict) and ref.get("writable"):
            issues.append(
                ManifestIssue(
                    "project.read_only_reference_projects",
                    f"{ref.get('name', '?')}: reference projects are read-only; write authority "
                    f"comes from the PID and the authority record, never the manifest",
                )
            )

    return issues


#: The framework's own floor. A project may raise these; never lower them.
FRAMEWORK_ASSURANCE_FLOOR = {
    "TASK": "L1",
    "CHANGE": "L2",
    "CONTROLLED_ACTION": "L4",
    "INCIDENT": "L2",
}


# --------------------------------------------------------------------------------------------- #
# Manifest truth (independent Assurance finding F-5)
#
# Lives HERE, inside the shipped package, so a consuming project validates its own manifest. The
# generator entry point is a thin wrapper in tools/ that is not distributed; the validation is not.
# --------------------------------------------------------------------------------------------- #

# O-1: the manifest credited tools/generate_manifest.py, which is a development entry point and
# is NOT distributed -- so a consuming project started RED referencing an absent generator by
# design. The provenance now names the shipped mechanism that actually performs the work; the thin
# wrapper in tools/ remains for convenience in this repository.
GENERATOR = "tools/pbg/manifest.py"


def measurements(root: Path) -> dict:
    from . import controls as cm, floor, versioning
    corpus = cm.all_controls(root)
    return {
        "framework_version": versioning.read_version(root),
        "domains": sorted({cid.split("-")[1] for cid in corpus}),
        "control_count": len(corpus),
        "mandatory_control_count": sum(
            1 for r in corpus.values() if r.get("mandatory_or_conditional") == "MANDATORY"),
        "non_waivable_controls": sorted(floor.REQUIRED_FLOOR),
    }


class FloorViolation(RuntimeError):
    """Regeneration refused: the corpus violates the shipped floor."""


def generate(root: Path) -> str:
    from . import floor
    import yaml

    # N-3: regeneration must not convert tampering into a new valid baseline. If the floor is
    # violated, the manifest is not rewritten -- the violation stays visible in the old one.
    violations = floor.check(root)
    if violations:
        raise FloorViolation(
            "refusing to regenerate the manifest while the non-waivable floor is violated:\n  "
            + "\n  ".join(violations))
    doc = {"_generated": f"by {GENERATOR} from the live corpus — do not edit by hand"}
    doc.update(measurements(root))
    existing = {}
    path = root / "manifest.yaml"
    if path.is_file():
        existing = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for carry in ("declared_adapters", "implemented_commands", "unimplemented_commands"):
        if carry in existing:
            doc[carry] = existing[carry]
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100)


def validate(root: Path) -> list[str]:
    """Every declared measurement, against the live corpus. Names field, declared and observed."""
    import yaml
    path = root / "manifest.yaml"
    if not path.is_file():
        return ["manifest.yaml is absent"]
    try:
        declared = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return [f"manifest.yaml is unreadable: {exc}"]

    problems = []
    gen = str(declared.get("_generated", ""))
    if GENERATOR in gen and not (root / GENERATOR).is_file():
        problems.append(f"manifest claims generation by {GENERATOR}, which does not exist")

    for field, observed in measurements(root).items():
        if field not in declared:
            problems.append(f"manifest omits the declared measurement {field}")
        elif declared[field] != observed:
            problems.append(
                f"manifest {field}: declared {declared[field]!r}, observed {observed!r}")
    return problems


