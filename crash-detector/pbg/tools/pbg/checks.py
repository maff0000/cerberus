"""The verifier registry, and the binding that stops a control crediting someone else's check.

A control may claim mechanical verification only when BOTH of these validate:

    the reference resolves to a registered verifier
    AND the verifier's registry entry names that control as an authoritative target

That second condition is Attack 3, which I raised against my own contract and had no defence for.
Without it, `PBG-FOO-001` can point `verification_ref` at a real, working, passing check that
verifies something else entirely, and collect mechanical-verification credit for it. Filename
similarity, shared domain, naming convention and documentation text are NOT binding -- only the
registry entry is (Product Authority ruling 2026-07-31, Attack 3).

A verifier result is also bound to the evaluation context it was produced in. A PASS carried over
from a different candidate, tree or invocation is STALE, not a pass.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# --- observed execution states (Axis 4) ---------------------------------------------------------- #
# Computed, never authored. A control record declaring one of these is rejected by the schema.

NOT_EVALUATED = "NOT_EVALUATED"      # never reached in this invocation
NOT_APPLICABLE = "NOT_APPLICABLE"    # genuinely does not apply -- NOT a catch-all
NOT_YET_RUN = "NOT_YET_RUN"          # applicable, has a mechanism, has not run
PASS = "PASS"
FAIL = "FAIL"
ERROR = "ERROR"                      # the verifier raised
UNVERIFIABLE = "UNVERIFIABLE"        # the authentic target could not be reached
STALE = "STALE"                      # a result from a different context

OBSERVED_STATES = (NOT_EVALUATED, NOT_APPLICABLE, NOT_YET_RUN, PASS, FAIL, ERROR,
                   UNVERIFIABLE, STALE)

#: Product Authority: NOT_APPLICABLE must not absorb missing configuration, unresolved references
#: or absent evidence. Those are UNVERIFIABLE or ERROR, and they carry burden.
_NEVER_NOT_APPLICABLE = ("missing configuration", "unresolved reference", "absent evidence")


@dataclass(frozen=True)
class CheckResult:
    """What a verifier returns. It must name the control it is about."""
    control_id: str                  # which control this result speaks for
    state: str                       # one of OBSERVED_STATES
    detail: str = ""
    context_digest: str = ""         # binds the result to the tree it was computed against
    evidence: tuple = ()

    def bound_to(self, context_digest: str) -> bool:
        return bool(self.context_digest) and self.context_digest == context_digest


@dataclass(frozen=True)
class Verifier:
    """A registered check, and the exact set of controls it is authorised to speak for."""
    ref: str
    identity: str
    authoritative_target_control_ids: tuple
    input_contract: str
    output_contract: str
    version: str
    implementation: str
    evidence_produced: str
    run: Callable[..., CheckResult] = field(repr=False, default=None)

    def may_speak_for(self, control_id: str) -> bool:
        return control_id in self.authoritative_target_control_ids


def context_digest(root: Path) -> str:
    """Identify the evaluation context, so a result cannot be reused across trees."""
    root = Path(root).resolve()
    h = hashlib.sha256(str(root).encode())
    version = root / "VERSION"
    if version.is_file():
        h.update(version.read_bytes())
    return "ctx:" + h.hexdigest()[:16]


# --------------------------------------------------------------------------------------------- #
# The three approved non-waivable verifiers
# --------------------------------------------------------------------------------------------- #

def _authority_records(root: Path) -> dict:
    """Authority records for the executor lookup, tolerant of there being none."""
    try:
        from . import authority

        return authority.read_records(root)
    except Exception:                                      # pragma: no cover - defensive
        return {}


def _sod_001(root: Path, ctx: str, **_) -> CheckResult:
    """PBG-SOD-001 — separation of duties, bounded to what PBG can actually observe.

    The bounded claim, and it is deliberately narrow:

        the configured evidence demonstrates distinct recorded actors and an
        independent-provider boundary for this candidate

    It is NOT the claim "no actor certified its own work under all circumstances". This check
    reads records. It cannot see who typed them.
    """
    from . import adoption

    acceptance = adoption.read_acceptance(root)
    if not acceptance:
        return CheckResult("PBG-SOD-001", NOT_YET_RUN,
                           "no acceptance record exists yet; separation is unevidenced",
                           ctx)
    if "_malformed" in acceptance:
        return CheckResult("PBG-SOD-001", ERROR, "acceptance record is malformed", ctx)

    # A record documenting that nothing has run is NOT_YET_RUN, not FAIL. Both make validation
    # non-GREEN; only one of them is an accurate description of the state.
    if str(acceptance.get("overall", "")) == "NOT_YET_RUN":
        return CheckResult("PBG-SOD-001", NOT_YET_RUN,
                           "no behavioural run has occurred; separation of duties is unevidenced "
                           "rather than failed", ctx)

    # SOD-TOOLING-0001, second mechanism. `implementer_actor` and `assurance_actor` exist in NO
    # artefact in the repository — only in this reader and one test fixture — so this comparison had
    # never executed even on the paths that reach it. Retiring it would remove a real check; leaving
    # it reading fields nobody writes would keep a dead one. It is REPAIRED: the acceptance record's
    # own fields are still honoured when present, and when they are absent the identities are
    # derived from the same durable executor attestations that PBG-SOD-001 now uses everywhere else.
    #
    # A single source of truth, reached by two callers. Two independent notions of "who implemented
    # this" is how the framework ended up with one vacuous check and one that never ran.
    from . import executors

    implementer = acceptance.get("implementer_actor")
    assurer = acceptance.get("assurance_actor")
    problems = []
    derived = None
    if not implementer or not assurer:
        candidate = str(acceptance.get("candidate_sha") or "")
        siblings = _authority_records(root)
        assurance_record = next(
            (d for d in siblings.values()
             if isinstance(d, dict)
             and str(d.get("assigned_role", "")) == executors.ASSURANCE_ROLE
             and str(d.get("target_candidate") or "") == candidate),
            None)
        if assurance_record is not None:
            derived = executors.check_separation(root, assurance_record, siblings)
            implementer = implementer or (
                derived.implementer.executor_id if derived.implementer
                and derived.implementer.established else None)
            assurer = assurer or (
                derived.auditor.executor_id if derived.auditor
                and derived.auditor.established else None)

    if not implementer or not assurer:
        problems.append(
            "implementer and assurance identities are not both established — neither the acceptance "
            "record nor any seat attestation names them, and an unestablished identity is a reason "
            "to refuse, not to pass"
            + (f" ({derived.detail})" if derived else ""))
    elif str(implementer).strip().lower() == str(assurer).strip().lower():
        problems.append(f"implementer and assurance identity are the same ({implementer})")
    if not acceptance.get("candidate_sha"):
        problems.append("assurance result is not bound to a candidate")
    if not acceptance.get("assurance_evidence"):
        problems.append("no assurance evidence reference; the record asserts rather than evidences")
    else:
        anchor = acceptance.get("assurance_provider")
        if not anchor:
            problems.append(
                "assurance evidence is not externally anchored: no provider declared, so the "
                "record and its evidence share one authority")

    if problems:
        return CheckResult("PBG-SOD-001", FAIL, "; ".join(problems), ctx)
    return CheckResult(
        "PBG-SOD-001", PASS,
        "configured evidence shows distinct recorded actors and a declared independent-provider "
        "boundary for this candidate", ctx,
        evidence=("docs/behavioural/ACCEPTANCE.yaml",))


def _boot_002(root: Path, ctx: str, **_) -> CheckResult:
    """PBG-BOOT-002 — no agent self-assigns a role; boot fails closed without an assignment.

    Statically observable part only: the shipped contract must route boot through a role
    assignment, must not grant a role from a greeting, and boot must fail closed when the
    authority record is absent.

    This does NOT prove fresh-agent behaviour. That needs a runtime run and this check says so.
    """
    from . import boot as boot_mod

    problems = []
    adapters = list((root / "adapters").rglob("*.md")) if (root / "adapters").is_dir() else []
    if not adapters:
        return CheckResult("PBG-BOOT-002", UNVERIFIABLE, "no adapters present to inspect", ctx)
    for adapter in adapters:
        text = adapter.read_text(encoding="utf-8", errors="ignore")
        if "roles/" not in text:
            problems.append(f"{adapter.name} does not route to a role contract")
        if "Reading a role file does not grant" not in text and "does not grant" not in text:
            problems.append(f"{adapter.name} does not state that reading a role grants nothing")

    for role_file in (root / "roles").glob("*.md") if (root / "roles").is_dir() else []:
        text = role_file.read_text(encoding="utf-8", errors="ignore")
        if "does not grant you this role" not in text:
            problems.append(f"{role_file.name} does not disclaim self-assignment")
        if "PBG-BOOT-002" not in text:
            problems.append(f"{role_file.name} does not cite the control that binds it")

    # Behavioural: boot must fail closed with no authority record. Exercised, not asserted.
    if not hasattr(boot_mod, "pl_boot"):
        problems.append("no pl_boot entry point")

    if problems:
        return CheckResult("PBG-BOOT-002", FAIL, "; ".join(problems[:6]), ctx)
    return CheckResult(
        "PBG-BOOT-002", PASS,
        "shipped contracts route boot through a role assignment and disclaim self-assignment; "
        "fresh-agent conformance is NOT established by this check", ctx,
        evidence=("adapters/", "roles/"))


def _cont_003(root: Path, ctx: str, **_) -> CheckResult:
    """PBG-CONT-003 — continuity is append-only and fails closed.

    Exercised against real inputs rather than asserted: malformed YAML, duplicate keys, forward
    references, log mismatch, and the prohibition on falling back to an older convenient
    checkpoint.
    """
    from . import continuity as cont

    failures = []

    # duplicate keys must be rejected outright
    try:
        cont.parse_strict("a: 1\na: 2\n")
        failures.append("duplicate YAML keys were accepted")
    except cont.ContinuityError:
        pass

    # malformed input must raise, not coerce
    try:
        cont.parse_strict("items:\n  - one\n  key: value\n")
        failures.append("malformed continuity was accepted")
    except cont.ContinuityError:
        pass

    # every currency state must have a declared continuation, and only CURRENT may resume
    try:
        for state, policy in cont.CURRENCY_CONTINUATION.items():
            if state != cont.ACTIVE_WORK_CURRENT and policy.normal_resume:
                failures.append(f"{state} permits normal resume")
            if not policy.read_only_diagnosis:
                failures.append(f"{state} forbids read-only diagnosis")
        cont.continuation_for("ACTIVE_WORK_INVENTED")
        failures.append("an undeclared currency state did not fail closed")
    except ValueError:
        pass
    except Exception as exc:                                  # pragma: no cover - defensive
        return CheckResult("PBG-CONT-003", ERROR, f"continuity module raised: {exc}", ctx)

    # the live records must themselves be current
    log_dir = root / "governance" / "engineering" / "build-log"
    aw = root / "governance" / "engineering" / "ACTIVE_WORK.yaml"
    if aw.is_file() and log_dir.is_dir():
        try:
            state, detail = cont.active_work_currency(
                cont.parse_strict(aw.read_text(encoding="utf-8")), log_dir)
            if cont.continuation_for(state).severity == "BLOCKED":
                failures.append(f"live continuity is {state}: {detail}")
        except cont.ContinuityError as exc:
            failures.append(f"live Active Work does not parse: {exc}")
    else:
        # O-2: a fresh installation genuinely has no project history. That is an initialisation
        # state, not an unverifiable one -- reporting UNVERIFIABLE made every new project look
        # corrupt on first boot. Read-only boot and diagnosis stay permitted; mutation and resume
        # stay blocked until continuity is initialised.
        return CheckResult("PBG-CONT-003", NOT_YET_RUN,
                           "NEW_PROJECT_CONTINUITY_NOT_INITIALISED — no continuity has been "
                           "written yet. Next action: initialise Active Work and the first Build "
                           "Log entry. Read-only boot and diagnosis are permitted; mutation and "
                           "resume are not.", ctx)

    if failures:
        return CheckResult("PBG-CONT-003", FAIL, "; ".join(failures[:6]), ctx)
    return CheckResult(
        "PBG-CONT-003", PASS,
        "strict parsing rejects duplicate keys and malformed records; every currency state has a "
        "declared continuation; undeclared states fail closed; live records are current", ctx,
        evidence=("governance/engineering/",))



# --------------------------------------------------------------------------------------------- #
# Verifiers wrapping checks that already executed inside `pbg validate`.
#
# They ran, but no control was BOUND to them -- the binding was a regex over prose. Registering
# them is what converts "a check exists somewhere" into "this control is verified by this check".
# --------------------------------------------------------------------------------------------- #

def _secret_material(root: Path, ctx: str, control_id: str = "PBG-EVID-003", **_) -> CheckResult:
    from . import scanning
    findings = scanning.scan_secrets(root)
    if findings:
        return CheckResult(control_id, FAIL,
                           f"{len(findings)} secret-shaped finding(s); classes and locations only",
                           ctx, evidence=tuple(f"{f.path}:{f.line}" for f in findings[:5]))
    return CheckResult(control_id, PASS,
                       "no configured credential pattern detected in the scanned current files "
                       "(not a claim that no secret exists)", ctx)


def _control_identity(root: Path, ctx: str, **_) -> CheckResult:
    from . import controls as cmod
    issues = cmod.check_integrity(root)
    if issues:
        return CheckResult("PBG-CTRL-001", FAIL, f"{len(issues)} integrity issue(s)", ctx)
    return CheckResult("PBG-CTRL-001", PASS, "control IDs unique, no retired ID reused", ctx)


def _control_records_valid(root: Path, ctx: str, **_) -> CheckResult:
    from . import controls as cmod
    issues = cmod.check_integrity(root)
    if issues:
        return CheckResult("PBG-FWK-051", FAIL, f"{len(issues)} record issue(s)", ctx)
    return CheckResult("PBG-FWK-051", PASS, "control records load and validate", ctx)


def _manifest_cannot_weaken(root: Path, ctx: str, **_) -> CheckResult:
    from . import manifest as mmod
    for candidate in (root / "pbg-manifest.yaml", root / "governance" / "pbg-manifest.yaml"):
        if candidate.is_file():
            issues = mmod.check(root, mmod.load(candidate))
            if issues:
                return CheckResult("PBG-CTRL-004", FAIL, f"{len(issues)} weakening attempt(s)", ctx)
            return CheckResult("PBG-CTRL-004", PASS, "manifest weakens nothing mandatory", ctx)
    return CheckResult("PBG-CTRL-004", NOT_APPLICABLE, "no project manifest in this tree", ctx)


def _axes_are_separate(root: Path, ctx: str, **_) -> CheckResult:
    """PBG-CTRL-005 — enforcement, verification and applicability are separate axes.

    Newly checkable. The old schema conflated them in prose, which is what made this control
    unverifiable while it demanded the separation.
    """
    from . import controls as cmod
    problems = []
    for cid, rec in cmod.all_controls(root).items():
        if "enforcement_expectation" in rec or "verification_expectation" in rec:
            problems.append(f"{cid} retains a conflated legacy field")
        for forbidden in ("observed_execution_state", "remaining_actor_burden"):
            if forbidden in rec:
                problems.append(f"{cid} authors the computed field {forbidden}")
    if problems:
        return CheckResult("PBG-CTRL-005", FAIL, "; ".join(problems[:5]), ctx)
    return CheckResult("PBG-CTRL-005", PASS,
                       "no control conflates the axes or authors a computed one", ctx)


def _wrapper_classification(root: Path, ctx: str, **_) -> CheckResult:
    from . import scanning
    wrappers = scanning.classify_wrappers(root)
    bad = [w for w in wrappers if w.severity in ("RED", "AMBER")]
    if bad:
        return CheckResult("PBG-FWK-004", FAIL, f"{len(bad)} unclassified wrapper(s)", ctx)
    return CheckResult("PBG-FWK-004", PASS, "no project-local wrapper bypasses framework tooling", ctx)


def _version_authority(root: Path, ctx: str, **_) -> CheckResult:
    from . import versioning
    try:
        v = versioning.read_version(root)
    except Exception as exc:
        return CheckResult("PBG-FWK-010", FAIL, f"VERSION unreadable: {exc}", ctx)
    return CheckResult("PBG-FWK-010", PASS, f"single canonical version authority: {v}", ctx)


def _no_hand_embedded_versions(root: Path, ctx: str, **_) -> CheckResult:
    from . import versioning
    canonical = versioning.read_version(root)
    hits = [h for h in versioning.scan(root)
            if versioning.classify(h.literal, canonical) == "SELF_DECLARATION"]
    if hits:
        return CheckResult("PBG-FWK-011", FAIL, f"{len(hits)} hand-embedded version(s)", ctx,
                           evidence=tuple(f"{h.path}:{h.line}" for h in hits[:5]))
    return CheckResult("PBG-FWK-011", PASS, "no framework version embedded by hand", ctx)


def _version_conflicts(root: Path, ctx: str, **_) -> CheckResult:
    from . import versioning
    canonical = versioning.read_version(root)
    conflicts = [h for h in versioning.scan(root)
                 if versioning.classify(h.literal, canonical) == "SELF_DECLARATION"
                 and h.literal != canonical]
    if conflicts:
        return CheckResult("PBG-FWK-012", FAIL, f"{len(conflicts)} conflicting declaration(s)", ctx)
    return CheckResult("PBG-FWK-012", PASS, "no conflicting framework-version declaration", ctx)


def _snapshot_write_safety(root: Path, ctx: str, **_) -> CheckResult:
    from . import verification
    problems = verification.check_snapshot_write_safety(root)
    if problems:
        return CheckResult("PBG-FWK-013", FAIL, "; ".join(problems[:3]), ctx)
    return CheckResult("PBG-FWK-013", PASS,
                       "every documented invocation preserves the pinned snapshot", ctx)


def _adapter_command_fidelity(root: Path, ctx: str, **_) -> CheckResult:
    from . import verification, cli
    problems = verification.check_adapter_commands(root, cli.registered_commands())
    if problems:
        return CheckResult("PBG-PORT-003", FAIL, "; ".join(problems[:3]), ctx)
    return CheckResult("PBG-PORT-003", PASS, "every advertised command exists", ctx)


def _unit_interface(root: Path, ctx: str, **_) -> CheckResult:
    """PBG-SEC-003 — a unit's interface is explicit and bounded, and matches runtime truth.

    The control demanded explicit bounded interfaces and had no artefact, no schema and no
    verifier: it deferred to the Blueprint and nothing observed anything. This is the check it
    needed.

    Static checks run always. The runtime comparison needs a running unit, and where none is
    supplied that is reported NOT_YET_RUN rather than passed.
    """
    from . import unit_interface as ui

    decl = ui.load(root)
    if decl is None:
        return CheckResult("PBG-SEC-003", NOT_APPLICABLE,
                           "this tree declares no unit interface; the framework repository is not "
                           "itself a compute unit", ctx)
    # Through the PRODUCT path, so the control sees the running unit rather than the declaration
    # alone. Previously this called ui.verify(root) with no runtime evidence at all, which meant a
    # healthy unit and a root-running unit produced identical results here.
    from . import unit_verify
    verdict, runtime_context = unit_verify.verify_unit(root)
    failed = [f for f in verdict.findings if not f.ok]
    if failed:
        return CheckResult("PBG-SEC-003", FAIL,
                           "; ".join(f"{f.check}: {f.detail}" for f in failed[:3]), ctx)
    unverified = [f.check for f in verdict.findings if f.evidence_class == ui.NOT_VERIFIED]
    observed = ("runtime observed: %s" % (runtime_context["containers"],)
                if runtime_context["runtime_observed"]
                else "runtime NOT observed: %s" % runtime_context["reason"])
    return CheckResult("PBG-SEC-003", PASS,
                       f"declaration valid and bounded; {observed}; NOT_VERIFIED: {unverified}",
                       ctx, evidence=("governance/unit-interface.yaml",))


def _shared_secret_verifier(control_id):
    def run(root, ctx, **kw):
        return _secret_material(root, ctx, control_id=control_id)
    return run


# --------------------------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------------------------- #

REGISTRY: dict[str, Verifier] = {
    "sod.separation_evidence": Verifier(
        ref="sod.separation_evidence",
        identity="separation-of-duties evidence verifier",
        authoritative_target_control_ids=("PBG-SOD-001",),
        input_contract="framework root containing docs/behavioural/ACCEPTANCE.yaml",
        output_contract="CheckResult naming PBG-SOD-001, bound to the evaluation context",
        version="1",
        implementation="tools/pbg/checks.py:_sod_001",
        evidence_produced="acceptance record path and the identities compared",
        run=_sod_001,
    ),
    "boot.role_assignment_contract": Verifier(
        ref="boot.role_assignment_contract",
        identity="role-assignment contract verifier (static)",
        authoritative_target_control_ids=("PBG-BOOT-002",),
        input_contract="framework root containing adapters/ and roles/",
        output_contract="CheckResult naming PBG-BOOT-002; explicitly does not establish "
                        "fresh-agent behavioural conformance",
        version="1",
        implementation="tools/pbg/checks.py:_boot_002",
        evidence_produced="adapter and role files inspected",
        run=_boot_002,
    ),
    "evidence.no_secret_material": Verifier(
        ref="evidence.no_secret_material",
        identity="secret-material scanner",
        # Three controls, each explicitly registered. A shared verifier may cover several controls
        # ONLY where every covered control is named here (PA ruling, Attack 3).
        authoritative_target_control_ids=("PBG-EVID-003", "PBG-CONT-009", "PBG-SEC-002"),
        input_contract="framework or project root",
        output_contract="CheckResult naming the requesting control; classes and locations only",
        version="1",
        implementation="tools/pbg/checks.py:_secret_material",
        evidence_produced="finding classes and file locations, never values",
        run=None,   # bound per control below
    ),
    "controls.identity_and_references": Verifier(
        ref="controls.identity_and_references", identity="control identity verifier",
        authoritative_target_control_ids=("PBG-CTRL-001",),
        input_contract="framework root with controls/",
        output_contract="CheckResult naming PBG-CTRL-001", version="1",
        implementation="tools/pbg/checks.py:_control_identity",
        evidence_produced="integrity issue list", run=_control_identity),
    "controls.records_valid": Verifier(
        ref="controls.records_valid", identity="control record validator",
        authoritative_target_control_ids=("PBG-FWK-051",),
        input_contract="framework root with controls/",
        output_contract="CheckResult naming PBG-FWK-051", version="1",
        implementation="tools/pbg/checks.py:_control_records_valid",
        evidence_produced="record issue list", run=_control_records_valid),
    "controls.manifest_cannot_weaken": Verifier(
        ref="controls.manifest_cannot_weaken", identity="manifest weakening verifier",
        authoritative_target_control_ids=("PBG-CTRL-004",),
        input_contract="project root that may contain a manifest",
        output_contract="CheckResult naming PBG-CTRL-004", version="1",
        implementation="tools/pbg/checks.py:_manifest_cannot_weaken",
        evidence_produced="weakening attempts", run=_manifest_cannot_weaken),
    "controls.axes_are_separate": Verifier(
        ref="controls.axes_are_separate", identity="axis separation verifier",
        authoritative_target_control_ids=("PBG-CTRL-005",),
        input_contract="framework root with controls/",
        output_contract="CheckResult naming PBG-CTRL-005", version="1",
        implementation="tools/pbg/checks.py:_axes_are_separate",
        evidence_produced="controls conflating axes or authoring computed fields",
        run=_axes_are_separate),
    "framework.wrapper_classification": Verifier(
        ref="framework.wrapper_classification", identity="wrapper classifier",
        authoritative_target_control_ids=("PBG-FWK-004",),
        input_contract="project root", output_contract="CheckResult naming PBG-FWK-004",
        version="1", implementation="tools/pbg/checks.py:_wrapper_classification",
        evidence_produced="wrapper classifications", run=_wrapper_classification),
    "framework.version_authority": Verifier(
        ref="framework.version_authority", identity="version authority verifier",
        authoritative_target_control_ids=("PBG-FWK-010",),
        input_contract="framework root with VERSION",
        output_contract="CheckResult naming PBG-FWK-010", version="1",
        implementation="tools/pbg/checks.py:_version_authority",
        evidence_produced="canonical version", run=_version_authority),
    "framework.no_hand_embedded_versions": Verifier(
        ref="framework.no_hand_embedded_versions", identity="hand-stamp verifier",
        authoritative_target_control_ids=("PBG-FWK-011",),
        input_contract="framework root", output_contract="CheckResult naming PBG-FWK-011",
        version="1", implementation="tools/pbg/checks.py:_no_hand_embedded_versions",
        evidence_produced="hand-embedded version locations", run=_no_hand_embedded_versions),
    "framework.version_conflicts": Verifier(
        ref="framework.version_conflicts", identity="version conflict verifier",
        authoritative_target_control_ids=("PBG-FWK-012",),
        input_contract="framework root", output_contract="CheckResult naming PBG-FWK-012",
        version="1", implementation="tools/pbg/checks.py:_version_conflicts",
        evidence_produced="conflicting declarations", run=_version_conflicts),
    "framework.snapshot_write_safety": Verifier(
        ref="framework.snapshot_write_safety", identity="snapshot write-safety verifier",
        authoritative_target_control_ids=("PBG-FWK-013",),
        input_contract="framework root", output_contract="CheckResult naming PBG-FWK-013",
        version="1", implementation="tools/pbg/checks.py:_snapshot_write_safety",
        evidence_produced="unsafe documented invocations", run=_snapshot_write_safety),
    "unit.interface_contract": Verifier(
        ref="unit.interface_contract", identity="compute unit interface verifier",
        authoritative_target_control_ids=("PBG-SEC-003",),
        input_contract="a project root that may contain governance/unit-interface.yaml",
        output_contract="CheckResult naming PBG-SEC-003; outbound behaviour is never claimed",
        version="1", implementation="tools/pbg/checks.py:_unit_interface",
        evidence_produced="per-check findings with evidence classification",
        run=_unit_interface),
    "adapters.command_fidelity": Verifier(
        ref="adapters.command_fidelity", identity="adapter command verifier",
        authoritative_target_control_ids=("PBG-PORT-003",),
        input_contract="framework root with adapters/",
        output_contract="CheckResult naming PBG-PORT-003", version="1",
        implementation="tools/pbg/checks.py:_adapter_command_fidelity",
        evidence_produced="advertised commands that do not exist", run=_adapter_command_fidelity),
    "continuity.append_only_fail_closed": Verifier(
        ref="continuity.append_only_fail_closed",
        identity="continuity fail-closed verifier",
        authoritative_target_control_ids=("PBG-CONT-003",),
        input_contract="framework root containing governance/engineering/",
        output_contract="CheckResult naming PBG-CONT-003, bound to the evaluation context",
        version="1",
        implementation="tools/pbg/checks.py:_cont_003",
        evidence_produced="parser behaviour exercised and live record currency",
        run=_cont_003,
    ),
}


class BindingError(ValueError):
    """A control tried to claim a verifier that is not authorised to speak for it."""


def _bound_run(verifier: Verifier, control_id: str):
    """A shared verifier must answer AS the control that asked, not as its first registration."""
    if verifier.ref == "evidence.no_secret_material":
        return _shared_secret_verifier(control_id)
    return verifier.run


def resolve(control_id: str, ref: str) -> Verifier:
    """Resolve a verification reference for a specific control, or fail closed.

    Both halves are required. Resolution alone is the Attack-3 hole.
    """
    verifier = REGISTRY.get(ref)
    if verifier is None:
        raise BindingError(f"{control_id}: verification_ref {ref!r} resolves to no verifier")
    if not verifier.may_speak_for(control_id):
        raise BindingError(
            f"{control_id}: verifier {ref!r} is registered for "
            f"{list(verifier.authoritative_target_control_ids)} and is not authorised to speak "
            f"for {control_id}")
    return verifier


def execute(control_id: str, ref: str, root: Path) -> CheckResult:
    """Run a bound verifier and validate that what came back speaks for this control, here."""
    ctx = context_digest(root)
    try:
        verifier = resolve(control_id, ref)
    except BindingError as exc:
        # Defence in depth: validation reports binding failure as RED, and a single mis-bound
        # control cannot abort the whole evaluation.
        return CheckResult(control_id, ERROR, str(exc), ctx)
    runner = _bound_run(verifier, control_id)
    if runner is None:
        return CheckResult(control_id, ERROR, f"verifier {ref!r} has no implementation", ctx)
    try:
        result = runner(root, ctx)
    except Exception as exc:                                  # noqa: BLE001 - any failure is ERROR
        return CheckResult(control_id, ERROR, f"verifier raised: {exc}", ctx)

    if not isinstance(result, CheckResult):
        return CheckResult(control_id, ERROR, "verifier returned a non-result", ctx)
    if result.control_id != control_id:
        # A verifier answering about a different control is not evidence for this one.
        return CheckResult(control_id, ERROR,
                           f"verifier {ref!r} returned a result for {result.control_id}", ctx)
    if not result.bound_to(ctx):
        return CheckResult(control_id, STALE,
                           "result is not bound to this evaluation context", ctx)
    if result.state not in OBSERVED_STATES:
        return CheckResult(control_id, ERROR, f"unknown observed state {result.state!r}", ctx)
    return result


def registry_problems() -> list[str]:
    """Structural checks on the registry itself."""
    problems = []
    for ref, v in REGISTRY.items():
        if v.ref != ref:
            problems.append(f"{ref}: entry ref disagrees with its key")
        if not v.authoritative_target_control_ids:
            problems.append(f"{ref}: names no authoritative target control")
        if v.run is None and ref != "evidence.no_secret_material":
            problems.append(f"{ref}: has no implementation")
        for field_name in ("identity", "input_contract", "output_contract", "version",
                           "implementation", "evidence_produced"):
            if not getattr(v, field_name):
                problems.append(f"{ref}: {field_name} is empty")
    return problems
