"""The adoption gate, stated as an explainable expression rather than a boolean.

    component completeness  !=  behavioural acceptance  !=  independent Assurance  !=  adoption

A distribution can contain every required component and still have never been booted by anything.
`suitable_for_adoption` is therefore computed from named gates, each of which can be reported as a
blocker in its own words -- because "false" without a reason is a dead end for whoever has to fix
it (Product Authority ruling 2026-07-30 s3, s28).

Nothing here can be overridden manually. A candidate that Product Authority wants to inspect early
is inspected while the status honestly says false (s16).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# --- gate vocabularies --------------------------------------------------------------------------- #

COMPONENT_STATUSES = ("COMPLETE", "INCOMPLETE", "INVALID")

BEHAVIOURAL_STATUSES = ("NOT_YET_RUN", "HARNESS_READY", "RUNNING", "PASS", "PASS_WITH_LIMITATIONS",
                        "FAIL", "BLOCKED_BY_RUNTIME")

ASSURANCE_STATUSES = ("NOT_YET_RUN", "AMBER", "PASS", "RED")

RUNTIME_SUPPORT_LEVELS = ("SUPPORTED", "SUPPORTED_WITH_LIMITATIONS", "EXPERIMENTAL", "UNSUPPORTED",
                          "UNPROVEN")

#: Behavioural acceptance is per path, per runtime. One passing path never promotes a runtime (s27).
BEHAVIOURAL_PATHS = ("pl_boot", "engineer_dispatch", "assurance_dispatch")

#: The runtimes that MUST be accounted for. Declared, never discovered from the record.
#:
#: independent Assurance finding F-2: the gate used to iterate whatever the acceptance file happened to contain, so a
#: runtime declaring pl_boot: FAIL blocked adoption and DELETING those four lines promoted the
#: candidate to adoption-ready. Absence read as silence rather than as an unproven runtime. It
#: failed closed against declared failure and open against selective removal, which is the wrong
#: way round -- the easier action was the one that produced the better answer.
REQUIRED_RUNTIMES = ("claude-code", "opencode")

PASSING_BEHAVIOURAL = {"PASS", "PASS_WITH_LIMITATIONS"}


@dataclass(frozen=True)
class CandidateIdentity:
    """What the acceptance record must be about. Supplied by the builder, never by the record."""
    source_sha: str
    distribution_digest: str


@dataclass
class AdoptionVerdict:
    component_status: str
    framework_validation: str
    continuity_validation: str
    behavioural_acceptance: str
    assurance_status: str
    runtime_support: dict = field(default_factory=dict)
    held_actions_intact: bool = True
    red_findings: list = field(default_factory=list)
    suitable_for_adoption: bool = False
    adoption_blockers: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "component_status": self.component_status,
            "framework_validation": self.framework_validation,
            "continuity_validation": self.continuity_validation,
            "behavioural_acceptance": self.behavioural_acceptance,
            "assurance_status": self.assurance_status,
            "runtime_support": self.runtime_support,
            "held_actions_intact": self.held_actions_intact,
            "red_findings": self.red_findings,
            "suitable_for_adoption": self.suitable_for_adoption,
            "adoption_blockers": self.adoption_blockers,
        }

    def render(self) -> str:
        lines = [
            f"  component        : {self.component_status}",
            f"  framework valid  : {self.framework_validation}",
            f"  continuity valid : {self.continuity_validation}",
            f"  behavioural      : {self.behavioural_acceptance}",
            f"  assurance        : {self.assurance_status}",
        ]
        for runtime, level in sorted(self.runtime_support.items()):
            lines.append(f"    runtime {runtime:<14} {level}")
        lines.append(f"  adoption ready   : {self.suitable_for_adoption}")
        lines += [f"    blocked by     : {b}" for b in self.adoption_blockers]
        return "\n".join(lines)


def read_acceptance(root: Path) -> dict:
    """The behavioural acceptance record, or an honest empty one.

    Absent means NOT_YET_RUN. It never means pass, and it is never inferred from the presence of a
    harness -- a harness that exists is not a harness that has been run.
    """
    path = Path(root) / "docs" / "behavioural" / "ACCEPTANCE.yaml"
    if not path.is_file():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return {"_malformed": str(exc)}


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_acceptance(root: Path, acceptance: dict, candidate: "CandidateIdentity | None") -> list[str]:
    """Check that the acceptance record is evidence, not an assertion.

    independent Assurance finding F-1, and it is the finding that matters most. The gate read a file the implementer writes.
    A hand-authored ACCEPTANCE.yaml saying independent_assurance: PASS, with evidence: [],
    candidate_sha: null and runtime_version: null, returned suitable_for_adoption: True. Nothing
    ran, and nothing checked that anything had. PBG-SOD-001 -- non-waivable, "nothing certifies
    itself" -- defeated by the exact mechanism that gates adoption.

    The same class was already solved once for the framework snapshot: PROVENANCE could not vouch
    for itself, so the install record was moved OUTSIDE the snapshot. That reasoning was written
    down, tested, and then not applied here. Guard-the-instance-not-the-class, on a prior fix.

    Honest limit, stated rather than implied: everything below still lives in a repository the
    implementer can write. This raises forgery from "type a word" to "fabricate consistent
    artefacts and digests", which is a real increase and not a proof. Genuine independence needs
    an anchor outside this tree -- see the provider-neutral assurance interface. The gate must
    never present in-repo consistency as external verification.
    """
    problems: list[str] = []
    if not acceptance:
        return ["no acceptance record — nothing has been run"]
    if "_malformed" in acceptance:
        return [f"acceptance record is malformed and cannot be trusted: {acceptance['_malformed']}"]

    # Identity: the record must name the candidate it is about, and match it.
    declared_sha = acceptance.get("candidate_sha")
    declared_digest = acceptance.get("distribution_digest")
    if not declared_sha:
        problems.append("acceptance record declares no candidate_sha")
    if not declared_digest:
        problems.append("acceptance record declares no distribution_digest")
    if candidate is not None:
        if declared_sha and declared_sha != candidate.source_sha:
            problems.append(
                f"acceptance record is about {declared_sha[:12]}, this candidate is "
                f"{candidate.source_sha[:12]}")
        if declared_digest and declared_digest != candidate.distribution_digest:
            problems.append("acceptance distribution_digest does not match this candidate")
    else:
        problems.append("candidate identity was not supplied; acceptance cannot be bound to it")

    # Independence: the actor who assured must not be the actor who implemented.
    implementer = acceptance.get("implementer_actor")
    assurer = acceptance.get("assurance_actor")
    if not assurer:
        problems.append("acceptance record names no assurance_actor")
    if not implementer:
        problems.append("acceptance record names no implementer_actor")
    if assurer and implementer and str(assurer).strip().lower() == str(implementer).strip().lower():
        problems.append(
            f"assurance_actor and implementer_actor are the same identity ({assurer}) — "
            f"PBG-SOD-001 is non-waivable")

    # Evidence: a declared PASS must point at an artefact that exists and matches its digest.
    for runtime, record in sorted((acceptance.get("runtimes") or {}).items()):
        if not isinstance(record, dict):
            problems.append(f"runtime {runtime}: malformed record")
            continue
        if not record.get("runtime_version"):
            problems.append(f"runtime {runtime}: no runtime_version recorded")
        paths = record.get("paths") or {}
        evidence = record.get("evidence") or []
        claimed_pass = [p for p in BEHAVIOURAL_PATHS if str(paths.get(p)) in PASSING_BEHAVIOURAL]
        if claimed_pass and not evidence:
            problems.append(
                f"runtime {runtime}: claims {claimed_pass} passed with no evidence recorded")
        for item in evidence:
            if not isinstance(item, dict) or not item.get("path") or not item.get("digest"):
                problems.append(f"runtime {runtime}: evidence entry lacks path or digest")
                continue
            ev_path = Path(root) / item["path"]
            if not ev_path.is_file():
                problems.append(f"runtime {runtime}: evidence {item['path']} does not exist")
            elif _digest(ev_path) != item["digest"]:
                problems.append(f"runtime {runtime}: evidence {item['path']} digest does not match")

    if str(acceptance.get("independent_assurance")) == "PASS" and not acceptance.get("assurance_evidence"):
        problems.append("independent_assurance claims PASS with no assurance_evidence reference")

    return problems


def summarise_behavioural(acceptance: dict) -> tuple[str, dict, list]:
    """Reduce per-path, per-runtime results to one status without hiding the detail."""
    runtimes = acceptance.get("runtimes") or {}
    support: dict[str, str] = {}
    # Every REQUIRED runtime is evaluated whether or not the record mentions it. A runtime absent
    # from the file is UNPROVEN, not exempt (independent Assurance finding F-2).
    for required in REQUIRED_RUNTIMES:
        if required not in runtimes:
            support[required] = "UNPROVEN"
    if not runtimes:
        return "NOT_YET_RUN", support, [
            f"{r}: not present in the acceptance record" for r in REQUIRED_RUNTIMES]

    notes: list[str] = []
    any_fail = False
    any_pending = False
    any_limited = False

    for runtime, record in sorted(runtimes.items()):
        paths = record.get("paths") or {}
        missing = [p for p in BEHAVIOURAL_PATHS if p not in paths]
        results = {p: str(paths.get(p, "NOT_YET_RUN")) for p in BEHAVIOURAL_PATHS}

        if any(r == "FAIL" for r in results.values()):
            support[runtime] = "UNSUPPORTED"
            any_fail = True
            notes.append(f"{runtime}: "
                         f"{[p for p, r in results.items() if r == 'FAIL']} failed")
        elif missing or any(r in ("NOT_YET_RUN", "HARNESS_READY", "RUNNING") for r in results.values()):
            support[runtime] = "UNPROVEN"
            any_pending = True
            notes.append(f"{runtime}: paths not yet run "
                         f"{[p for p, r in results.items() if r in ('NOT_YET_RUN', 'HARNESS_READY', 'RUNNING')]}")
        elif any(r == "BLOCKED_BY_RUNTIME" for r in results.values()):
            support[runtime] = str(record.get("declared_level", "EXPERIMENTAL"))
            any_limited = True
        elif all(r == "PASS" for r in results.values()):
            support[runtime] = str(record.get("declared_level", "SUPPORTED"))
        else:
            support[runtime] = str(record.get("declared_level", "SUPPORTED_WITH_LIMITATIONS"))
            any_limited = True

    for required in REQUIRED_RUNTIMES:
        if required not in runtimes:
            any_pending = True
            notes.append(f"{required}: not present in the acceptance record — unproven, not exempt")

    if any_fail:
        overall = "FAIL"
    elif any_pending:
        overall = "NOT_YET_RUN"
    elif any_limited:
        overall = "PASS_WITH_LIMITATIONS"
    else:
        overall = "PASS"
    return overall, support, notes


def evaluate(
    root: Path,
    *,
    component_status: str,
    candidate: CandidateIdentity | None = None,
    framework_validation: str = "UNKNOWN",
    continuity_validation: str = "UNKNOWN",
    held_actions_intact: bool | None = None,
) -> AdoptionVerdict:
    """Compute adoption readiness and, more usefully, why it is not ready.

    `held_actions_intact` defaults to None -- UNKNOWN -- and UNKNOWN blocks. It used to default to
    True and no caller ever passed it, so the held-action blocker could not fire in production
    (independent Assurance finding F-3). A safety check that is unreachable is worse than one that is absent, because the
    absent one does not appear in the verdict as though it had passed.
    """
    acceptance = read_acceptance(root)
    evidence_problems = validate_acceptance(root, acceptance, candidate)
    behavioural, support, notes = summarise_behavioural(acceptance)
    if evidence_problems:
        # An unverifiable record proves nothing, whatever it claims.
        behavioural = "NOT_YET_RUN" if behavioural in PASSING_BEHAVIOURAL else behavioural
    assurance = str(acceptance.get("independent_assurance", "NOT_YET_RUN"))
    red = list(acceptance.get("release_blocking_red") or [])

    blockers: list[str] = []
    if component_status != "COMPLETE":
        blockers.append(f"component status is {component_status}")
    if framework_validation not in ("GREEN", "UNKNOWN"):
        blockers.append(f"framework validation is {framework_validation}")
    elif framework_validation == "UNKNOWN":
        blockers.append("framework validation has not been observed by this build")
    if continuity_validation != "GREEN":
        blockers.append(f"continuity validation is {continuity_validation}")
    if evidence_problems:
        blockers.append("acceptance evidence does not verify")
        blockers += [f"  {p}" for p in evidence_problems]
    if behavioural not in PASSING_BEHAVIOURAL:
        blockers.append(f"behavioural acceptance is {behavioural}")
        blockers += [f"  {n}" for n in notes]
    for runtime, level in sorted(support.items()):
        if level in ("UNPROVEN", "UNSUPPORTED"):
            blockers.append(f"runtime {runtime} is {level}")
    if assurance != "PASS":
        blockers.append(f"independent assurance is {assurance}")
    if red:
        blockers.append(f"{len(red)} release-blocking RED finding(s): {red}")
    if held_actions_intact is None:
        blockers.append("held-action state was not observed by this build — unknown, not assumed")
    elif not held_actions_intact:
        blockers.append("a held Controlled Action is no longer held")

    return AdoptionVerdict(
        component_status=component_status,
        framework_validation=framework_validation,
        continuity_validation=continuity_validation,
        behavioural_acceptance=behavioural,
        assurance_status=assurance,
        runtime_support=support,
        held_actions_intact=bool(held_actions_intact),
        red_findings=red,
        suitable_for_adoption=not blockers,
        adoption_blockers=blockers,
    )
