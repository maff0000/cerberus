"""Control applicability and actor burden.

The decisive question for PBGv2:

    For a normal small task, how many of the 93 mandatory controls
    actually require an agent action?

"Mandatory" means a control cannot be silently removed when its applicability conditions are
satisfied. It does NOT mean every Task must manually address it. A mandatory control may
legitimately resolve as NOT_APPLICABLE, AUTOMATICALLY_ENFORCED, MECHANICALLY_VERIFIED or
INHERITED_FROM_PROJECT_BASELINE without costing the actor anything.

This module resolves which controls apply to a piece of work, and — more importantly — how many
of them a human or agent must actually think about.
"""

from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import controls as controls_mod

# --------------------------------------------------------------------------------------------- #
# Burden classes
# --------------------------------------------------------------------------------------------- #

NOT_APPLICABLE = "NOT_APPLICABLE"
AUTOMATICALLY_ENFORCED = "AUTOMATICALLY_ENFORCED"
MECHANICALLY_VERIFIED = "MECHANICALLY_VERIFIED"
INHERITED_FROM_PROJECT_BASELINE = "INHERITED_FROM_PROJECT_BASELINE"
AGENT_ACTION_REQUIRED = "AGENT_ACTION_REQUIRED"
EVIDENCE_ACTION_REQUIRED = "EVIDENCE_ACTION_REQUIRED"
HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"

#: Classes the actor must actually think about. Everything else is carried by the framework,
#: the tooling or a one-off project declaration.
BURDENSOME = {AGENT_ACTION_REQUIRED, EVIDENCE_ACTION_REQUIRED, HUMAN_DECISION_REQUIRED}

# --- Axis 5, remaining actor burden (PA ruling 2026-07-31) ------------------------------------ #
# Deliberately NOT reusing HUMAN_DECISION_REQUIRED: it already means something on the legacy
# applicability axis above, and reusing a name across two axes is how F-8/F-9 happened.
NO_ACTION = "NO_ACTION"
ACTION_REQUIRED = "ACTION_REQUIRED"
EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
DECISION_REQUIRED = "DECISION_REQUIRED"
ASSURANCE_REQUIRED = "ASSURANCE_REQUIRED"
REPAIR_REQUIRED = "REPAIR_REQUIRED"
BLOCKED_UNRESOLVED = "BLOCKED_UNRESOLVED"

BURDEN_VALUES = (NO_ACTION, ACTION_REQUIRED, EVIDENCE_REQUIRED, DECISION_REQUIRED,
                 ASSURANCE_REQUIRED, REPAIR_REQUIRED, BLOCKED_UNRESOLVED)

BURDEN_FREE = {NO_ACTION}

#: Classes an actor sees at all, even if only as a reported result.
VISIBLE = BURDENSOME | {MECHANICALLY_VERIFIED}

COGNITIVE_BANDS = (
    (0, 8, "LOW"),
    (9, 15, "MODERATE"),
    (16, 25, "HIGH"),
    (26, 10_000, "EXCESSIVE"),
)


def band(agent_action_required: int) -> str:
    for lo, hi, name in COGNITIVE_BANDS:
        if lo <= agent_action_required <= hi:
            return name
    return "EXCESSIVE"                                          # pragma: no cover


# --------------------------------------------------------------------------------------------- #
# Trait derivation — derived from the record, never asserted
# --------------------------------------------------------------------------------------------- #

@dataclass(frozen=True)
class DerivedTrait:
    trait: str
    value: bool
    rule: str
    source: str
    deterministic: bool = True


#: Each rule reads the work record rather than trusting a declaration. A record naming a migration
#: is touches_data whether or not anyone ticked a box (PBG-WORK-001).
_TRAIT_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("touches_data", "paths or summary reference migrations, schema or SQL",
     re.compile(r"(?i)\b(migration|alembic|schema|\.sql\b|CREATE TABLE|ALTER TABLE|DROP )")),
    ("touches_secrets", "paths or summary reference credential material",
     re.compile(r"(?i)\b(secret|credential|token|api[_-]?key|\.env\b|vault|rotate)")),
    ("creates_process", "paths or summary reference a long-running or scheduled process",
     re.compile(r"(?i)\b(systemd|service|daemon|worker|cron|scheduler|entrypoint|supervisor)")),
    ("reaches_runtime", "work invokes, observes or mutates a running system",
     re.compile(r"(?i)\b(deploy|restart|runtime|container|probe|health|endpoint|curl|http)")),
    ("deployable", "work changes code reached by a process, timer, cron or request path",
     re.compile(r"(?i)\b(deploy|release|image|dockerfile|compose|k8s|kubernetes|activation)")),
    ("cross_project", "work references another project's paths or repository",
     re.compile(r"(?i)\b(cross-project|another project|other repo|external repository)")),
    ("irreversible", "work performs a destructive or irreversible operation",
     re.compile(r"(?i)\b(delete|drop |purge|truncate|irreversible|destructive|rotate secret)")),
    ("introduces_methodology", "work introduces a formula, score or statistical method",
     re.compile(r"(?i)\b(formula|score|algorithm|statistic|methodology|model weights)")),
)


def derive_traits(work: dict) -> list[DerivedTrait]:
    """Derive traits from the work record's own content, with the rule and source recorded."""
    corpus = " ".join([
        str(work.get("objective", "")),
        str(work.get("action_summary", "")),
        " ".join(work.get("paths", []) or []),
        " ".join(work.get("changes", []) or []),
    ])
    derived = []
    for trait, rule, pattern in _TRAIT_RULES:
        match = pattern.search(corpus)
        derived.append(DerivedTrait(
            trait=trait, value=bool(match), rule=rule,
            source=f"matched {match.group(0)!r}" if match else "no matching evidence in record",
        ))
    # A declared trait may SUPPLEMENT derivation but never override contrary evidence.
    for declared in work.get("declared_traits", []) or []:
        if not any(d.trait == declared and d.value for d in derived):
            derived.append(DerivedTrait(declared, True, "declared by the authority record",
                                        "declaration", deterministic=False))
    return derived


def active_traits(work: dict) -> set[str]:
    return {d.trait for d in derive_traits(work) if d.value}


# --------------------------------------------------------------------------------------------- #
# Applicability
# --------------------------------------------------------------------------------------------- #

def applies(record: dict, work_type: str, traits: set[str]) -> tuple[bool, str]:
    """Does this control apply to this work? Returns (applies, derivation)."""
    app = record.get("applicability") or {}
    mode = app.get("mode")

    # Mode answers WHEN the control demands attention. It never weakens the control.
    if mode == "AUTHORING":
        return False, "AUTHORING — governs artefact authoring, not this work"
    if mode == "STANDING":
        # Inherited from the project baseline. Surfaces only where the work touches it.
        affected = set(app.get("surfaces_on_traits") or []) & traits
        if affected:
            return True, f"STANDING, surfaced by trait {sorted(affected)}"
        return True, "STANDING — inherited from project baseline"
    if mode == "EVENT_TRIGGERED":
        return True, "EVENT_TRIGGERED — fires on a lifecycle event, not per work item"
    if mode == "PER_WORK":
        return True, "PER_WORK"

    if app.get("always"):
        return True, "applicability.always (unmigrated)"

    wanted_types = app.get("work_types")
    wanted_traits = app.get("traits")

    if wanted_types and work_type in wanted_types:
        if not wanted_traits:
            return True, f"work_type {work_type} in {wanted_types}"
        if traits & set(wanted_traits):
            return True, f"work_type {work_type} and trait {sorted(traits & set(wanted_traits))}"
        return False, f"work_type matches but no trait from {wanted_traits}"

    if wanted_traits:
        hit = traits & set(wanted_traits)
        if hit:
            return True, f"trait {sorted(hit)}"
        return False, f"no trait from {wanted_traits}"

    if wanted_types:
        return False, f"work_type {work_type} not in {wanted_types}"

    if app.get("when"):
        # A conditional whose trigger is prose cannot be resolved mechanically. Reported, not
        # assumed either way — an unresolved conditional that silently defaults to "applies"
        # inflates burden, and one that defaults to "does not" hides a control.
        return False, f"conditional on: {app['when']} (not mechanically resolvable)"

    if app.get("control_class"):
        return False, "applies to control authoring, not to project work"

    return False, "no applicability criteria matched"


# --------------------------------------------------------------------------------------------- #
# Burden classification
# --------------------------------------------------------------------------------------------- #

#: Controls declared once at project setup and then carried, rather than re-decided per task.
_BASELINE_DOMAINS = {"SOV", "PORT", "FWK"}


EVENT_TRIGGERED_CLASS = "EVENT_TRIGGERED_NOT_NOW"

#: Legacy presentation classes, now derived STRUCTURALLY from the five-axis model.
#:
#: The regex that used to produce these is deleted. It read `verification_expectation` -- free
#: English -- and appending the sentence "pbg validate confirms this." to six control records drove
#: the small-task figure from 6 to 0 with no logic change (independent Assurance finding F-7). Nothing here reads prose.
#:
#: AUTOMATICALLY_ENFORCED is retired as a source class: a control is no longer discharged because
#: it declares itself enforced. It is discharged when something ran and passed, which is Axis 4.
_DISCHARGE_TO_CLASS = {
    "EXECUTING_CHECK": MECHANICALLY_VERIFIED,
    "HUMAN_DECISION": HUMAN_DECISION_REQUIRED,
    "INHERITED_BASELINE": INHERITED_FROM_PROJECT_BASELINE,
    "EVIDENCE_SUBMISSION": EVIDENCE_ACTION_REQUIRED,
    "INDEPENDENT_ASSURANCE": AGENT_ACTION_REQUIRED,
    "DEFINED_PROCEDURE": AGENT_ACTION_REQUIRED,
    "EXTERNAL_MECHANICAL_CHECK": AGENT_ACTION_REQUIRED,
    "NO_MECHANISM": AGENT_ACTION_REQUIRED,
}


def classify(record: dict, applicable: bool) -> str:
    """Legacy presentation class, derived from the structured axes only.

    `burden_partition()` is the authoritative calculation. This exists so the actor view keeps its
    grouping vocabulary, and it reads no free text.
    """
    if not applicable:
        return NOT_APPLICABLE
    if record.get("schema_version") != 2:
        # A v1 record cannot be classified on these axes and must not slip into a free bucket.
        return AGENT_ACTION_REQUIRED

    mode = (record.get("applicability") or {}).get("mode")
    if mode == "STANDING":
        return INHERITED_FROM_PROJECT_BASELINE
    if mode == "AUTHORING":
        return AUTHORING_CLASS
    if mode == "EVENT_TRIGGERED":
        return EVENT_TRIGGERED_CLASS

    return _DISCHARGE_TO_CLASS.get(record.get("discharge_mechanism"), AGENT_ACTION_REQUIRED)


@dataclass
class Scenario:
    name: str
    work_type: str
    objective: str
    paths: list[str] = field(default_factory=list)
    declared_traits: list[str] = field(default_factory=list)

    def as_work(self) -> dict:
        return {"objective": self.objective, "paths": self.paths,
                "declared_traits": self.declared_traits}


@dataclass
class BurdenReport:
    scenario: str
    work_type: str
    traits: list[str]
    total_controls: int
    counts: dict[str, int]
    applicable: int
    agent_visible: int
    agent_action_required: int
    cognitive_band: str
    burdensome_ids: list[str] = field(default_factory=list)

    def render(self) -> str:
        return (
            f"{self.scenario:<42} {self.work_type:<18} "
            f"applicable {self.applicable:>3}  visible {self.agent_visible:>3}  "
            f"action {self.agent_action_required:>3}  {self.cognitive_band}"
        )


def analyse(root: Path, scenario: Scenario) -> BurdenReport:
    flat = controls_mod.all_controls(root)
    traits = active_traits(scenario.as_work())
    counts: dict[str, int] = {}
    burdensome: list[str] = []

    for cid, record in flat.items():
        if record.get("status") != "ACTIVE":
            continue
        ok, _why = applies(record, scenario.work_type, traits)
        klass = classify(record, ok)
        counts[klass] = counts.get(klass, 0) + 1
        if klass in BURDENSOME:
            burdensome.append(cid)

    applicable = sum(n for k, n in counts.items() if k != NOT_APPLICABLE)
    visible = sum(n for k, n in counts.items() if k in VISIBLE)
    action = sum(n for k, n in counts.items() if k in BURDENSOME)

    return BurdenReport(
        scenario=scenario.name, work_type=scenario.work_type, traits=sorted(traits),
        total_controls=len(flat), counts=counts, applicable=applicable,
        agent_visible=visible, agent_action_required=action,
        cognitive_band=band(action), burdensome_ids=sorted(burdensome),
    )


#: The thirteen scenarios the Product Authority required.
SCENARIOS = (
    Scenario("1. trivial documentation Task", "TASK",
             "Correct a typographical error in the README."),
    Scenario("2. small isolated bug fix", "TASK",
             "Fix an off-by-one error in the pagination helper.", ["app/paging.py"]),
    Scenario("3. ordinary feature Task", "TASK",
             "Add a sort control to the results table.", ["app/ui/table.py"]),
    Scenario("4. architecture Change", "CHANGE",
             "Introduce a new reporting component with its own module boundary.",
             ["app/reporting/"]),
    Scenario("5. schema migration", "CHANGE",
             "Add a nullable column via an alembic migration.", ["migrations/0042_add_col.sql"]),
    Scenario("6. container image build", "CHANGE",
             "Build and scan the application container image.", ["Dockerfile", "compose.yaml"]),
    Scenario("7. development deployment", "CHANGE",
             "Deploy the built image to the development runtime and health-check it."),
    Scenario("8. production deployment", "CONTROLLED_ACTION",
             "Deploy the assured image to production and activate the service."),
    Scenario("9. secret rotation", "CONTROLLED_ACTION",
             "Rotate the database credential and update the secret reference."),
    Scenario("10. Incident diagnosis", "INCIDENT",
             "Diagnose why the runtime health endpoint reports ready while the database is down."),
    Scenario("11. Incident repair", "INCIDENT",
             "Repair the readiness check so it fails when a mandatory dependency is unavailable.",
             ["app/health.py"]),
    Scenario("12. existing host-bound adoption", "CHANGE",
             "Assess an existing systemd-deployed application for container readiness."),
    Scenario("13. greenfield bootstrap", "CHANGE",
             "Establish a new application skeleton with tests and configuration."),
)


def analyse_all(root: Path) -> list[BurdenReport]:
    return [analyse(root, s) for s in SCENARIOS]


# --------------------------------------------------------------------------------------------- #
# Actor views — lean by default, complete on request
# --------------------------------------------------------------------------------------------- #
#
# Burden reduction must never become opaque suppression. A control is absent from the default view
# ONLY while it is inherited-and-satisfied, mechanically verified, irrelevant, not awaiting a human
# decision, not stale, not contradicted and not blocking. The moment any of those ceases to hold it
# surfaces — and `explain` will say why, for any control, at any time.

CURRENT_ACTIONS = "CURRENT_ACTIONS"
BLOCKING_FAILURES = "BLOCKING_FAILURES"
HUMAN_DECISIONS = "HUMAN_DECISIONS"
CURRENT_VISIBLE_CONTROLS = "CURRENT_VISIBLE_CONTROLS"
INHERITED_STANDING_BASELINE = "INHERITED_STANDING_BASELINE"
AUTHORING_RULES = "AUTHORING_RULES"
AUTHORING_CLASS = "AUTHORING_NOT_NOW"
EVENT_TRIGGERED_RULES = "EVENT_TRIGGERED_RULES"
FULL_ASSURANCE_TRACE = "FULL_ASSURANCE_TRACE"

#: What a Project Lead or Engineer sees unless they ask for more.
DEFAULT_VIEWS = (CURRENT_ACTIONS, BLOCKING_FAILURES, HUMAN_DECISIONS)

#: Conditions under which a normally-hidden control MUST surface regardless of its mode.
SURFACING_CONDITIONS = ("stale", "contradicted", "failing", "blocking", "awaiting_human_decision",
                        "affected_by_this_work")


@dataclass
class ActorView:
    scenario: str
    actions: list[str] = field(default_factory=list)
    blocking: list[str] = field(default_factory=list)
    human_decisions: list[str] = field(default_factory=list)
    inherited_count: int = 0
    inherited_satisfied: int = 0
    inherited_affected: list[str] = field(default_factory=list)
    mechanical_count: int = 0
    authoring_count: int = 0
    event_count: int = 0
    not_applicable_count: int = 0
    inactive_count: int = 0
    #: Anything that matched no bucket. MUST stay empty -- independent Assurance finding F-8 was a silent fall-through here,
    #: where `elif klass == NOT_APPLICABLE and mode == "AUTHORING"` caught one case and dropped
    #: every other NOT_APPLICABLE into no bucket at all, leaving 46 of 127 unaccounted.
    unclassified: list[str] = field(default_factory=list)
    surfaced: list[tuple[str, str]] = field(default_factory=list)

    def partition_total(self) -> int:
        return (len(self.actions) + len(self.human_decisions) + self.inherited_count
                + self.mechanical_count + self.authoring_count + self.event_count
                + self.not_applicable_count + self.inactive_count + len(self.unclassified))

    grouped_actions: int | None = None

    @property
    def default_visible(self) -> int:
        """What the actor actually reads.

        The compact baseline line is one item, not 24. Where the actions group into coherent
        operational steps, the group count is what the actor works through — several mechanically
        checked predicates supporting one genuine action are one action, not several.
        """
        action_items = self.grouped_actions if self.grouped_actions is not None else len(self.actions)
        return action_items + len(self.blocking) + len(self.human_decisions) + len(self.surfaced)

    def render(self) -> str:
        lines = [f"{self.scenario}", ""]
        lines.append(f"CURRENT ACTIONS ({len(self.actions)})")
        lines += [f"  - {c}" for c in self.actions] or ["  none"]
        if self.blocking:
            lines += ["", f"BLOCKING FAILURES ({len(self.blocking)})"]
            lines += [f"  ! {c}" for c in self.blocking]
        if self.human_decisions:
            lines += ["", f"HUMAN DECISIONS ({len(self.human_decisions)})"]
            lines += [f"  ? {c}" for c in self.human_decisions]
        if self.surfaced:
            lines += ["", f"SURFACED FROM BASELINE ({len(self.surfaced)})"]
            lines += [f"  ^ {c} — {why}" for c, why in self.surfaced]
        lines += ["", "Inherited standing baseline: "
                  f"{self.inherited_count} controls, {self.inherited_satisfied} satisfied, "
                  f"{len(self.inherited_affected)} affected"]
        lines.append(f"Mechanically verified: {self.mechanical_count} · "
                     f"Authoring rules: {self.authoring_count} (not yours) · "
                     f"Lifecycle: {self.event_count}")
        lines.append(f"[default visible: {self.default_visible}]  "
                     f"full trace: pbg controls --assurance")
        return "\n".join(lines)


def actor_view(
    root: Path,
    scenario: Scenario,
    baseline_failures: set[str] | None = None,
    stale_evidence: set[str] | None = None,
) -> ActorView:
    """Build the default actor view.

    `baseline_failures` and `stale_evidence` come from the resolved project state. A standing
    control in either set surfaces despite being inherited — hidden must never mean ignored.
    """
    baseline_failures = baseline_failures or set()
    stale_evidence = stale_evidence or set()

    flat = controls_mod.all_controls(root)
    traits = active_traits(scenario.as_work())
    view = ActorView(scenario=scenario.name)

    for cid, record in flat.items():
        if record.get("status") != "ACTIVE":
            view.inactive_count += 1
            continue
        ok, why = applies(record, scenario.work_type, traits)
        klass = classify(record, ok)
        mode = (record.get("applicability") or {}).get("mode")

        if klass == HUMAN_DECISION_REQUIRED:
            view.human_decisions.append(cid)
        elif klass in (AGENT_ACTION_REQUIRED, EVIDENCE_ACTION_REQUIRED):
            view.actions.append(cid)
        elif klass == INHERITED_FROM_PROJECT_BASELINE:
            view.inherited_count += 1
            if cid in baseline_failures:
                view.blocking.append(cid)
                view.inherited_affected.append(cid)
            elif cid in stale_evidence:
                view.surfaced.append((cid, "standing evidence is stale"))
                view.inherited_affected.append(cid)
            elif "surfaced by trait" in why:
                view.surfaced.append((cid, why))
                view.inherited_affected.append(cid)
            else:
                view.inherited_satisfied += 1
        elif klass == MECHANICALLY_VERIFIED:
            if cid in baseline_failures:
                view.blocking.append(cid)
            elif mode == "EVENT_TRIGGERED":
                view.event_count += 1
            else:
                view.mechanical_count += 1
        elif klass == AUTOMATICALLY_ENFORCED:
            view.mechanical_count += 1
        elif klass == AUTHORING_CLASS:
            view.authoring_count += 1
        elif klass == EVENT_TRIGGERED_CLASS:
            view.event_count += 1
        elif klass == NOT_APPLICABLE:
            # ALL of them, not only the AUTHORING ones.
            if mode == "AUTHORING":
                view.authoring_count += 1
            else:
                view.not_applicable_count += 1
        else:
            # No silent remainder. A class with no bucket is a defect, and it says so.
            view.unclassified.append(cid)

    for lst in (view.actions, view.blocking, view.human_decisions, view.unclassified):
        lst.sort()
    if view.partition_total() != len(flat):        # pragma: no cover - guarded by test
        raise AssertionError(
            f"actor view partition is not exhaustive: {view.partition_total()} of {len(flat)}")
    return view


def explain(root: Path, control_id: str, scenario: Scenario,
            baseline_failures: set[str] | None = None) -> str:
    """Why is this control visible, or not? Burden reduction must be interrogable."""
    flat = controls_mod.all_controls(root)
    record = flat.get(control_id)
    if record is None:
        return f"{control_id}: no such control"

    traits = active_traits(scenario.as_work())
    ok, why = applies(record, scenario.work_type, traits)
    klass = classify(record, ok)
    mode = (record.get("applicability") or {}).get("mode", "(unmigrated)")
    view = actor_view(root, scenario, baseline_failures)
    visible = control_id in (view.actions + view.blocking + view.human_decisions
                             + [c for c, _ in view.surfaced])

    return "\n".join([
        f"Control            : {control_id} — {record['title']}",
        f"Applicability mode : {mode}",
        f"Current trigger    : {why}",
        f"Current actor      : {', '.join(record.get('roles') or [])}",
        f"Burden class       : {klass}",
        f"Visible by default : {visible}",
        f"Why                : " + (
            "requires an action or decision for this work" if visible
            else f"{klass.lower().replace('_', ' ')}; surfaces if it becomes "
                 f"{', '.join(SURFACING_CONDITIONS)}"),
        f"Mandatory          : {record['mandatory_or_conditional']}  "
        f"(exception: {record['exception_policy']})",
        f"Failure surfaces as: {', '.join(record.get('failure_outcomes') or [])}",
        f"Evidence           : {', '.join(record.get('required_evidence') or [])}",
    ])


# --------------------------------------------------------------------------------------------- #
# Deployment action grouping — several controls may support ONE genuine actor action
# --------------------------------------------------------------------------------------------- #

DEPLOYMENT_GROUPS: dict[str, tuple[str, ...]] = {
    # The universal per-work set every Task also carries. Grouping it separately keeps the
    # deployment-specific actions legible instead of burying them among ordinary discipline.
    "STANDARD WORK DISCIPLINE": ("PBG-WORK-001", "PBG-SOD-003", "PBG-CONT-005",
                                 "PBG-EVID-001", "PBG-EVID-002"),
    "AUTHORITY AND TARGET": ("PBG-WORK-003", "PBG-AUTH-001", "PBG-AUTH-003", "PBG-GIT-004"),
    "BUILD AND ARTEFACT IDENTITY": ("PBG-CI-001", "PBG-CI-003", "PBG-CI-004", "PBG-DEPLOY-001",
                                    "PBG-DEPLOY-007"),
    "CONFIGURATION AND SECRETS": ("PBG-SEC-001", "PBG-SEC-002", "PBG-EVID-003", "PBG-EVID-004"),
    "DATA AND MIGRATION SAFETY": ("PBG-DATA-002", "PBG-DATA-003"),
    "RUNTIME READINESS": ("PBG-RT-011", "PBG-RT-012", "PBG-RT-013", "PBG-OBS-001", "PBG-OBS-002",
                          "PBG-OBS-003", "PBG-SEC-003"),
    "DEPLOYMENT EXECUTION": ("PBG-RT-001", "PBG-RT-004", "PBG-RT-005", "PBG-RT-006",
                             "PBG-DEPLOY-005", "PBG-WORK-004"),
    "POST-DEPLOYMENT VERIFICATION": ("PBG-DEPLOY-002", "PBG-DEPLOY-003", "PBG-DEPLOY-004",
                                     "PBG-DEPLOY-006", "PBG-DEPLOY-008", "PBG-CI-005"),
    "ROLLBACK AND INCIDENT READINESS": ("PBG-INC-003", "PBG-RT-002", "PBG-RT-003"),
}


def grouped_deployment_actions(root: Path, scenario: Scenario) -> dict:
    """Group a deployment's action-required controls into coherent operational actions.

    Grouping never hides an individual failed control — it presents one operational action with
    its supporting controls named, so the actor performs eight things rather than twenty-six.
    """
    report = analyse(root, scenario)
    remaining = set(report.burdensome_ids)
    groups = {}
    for name, members in DEPLOYMENT_GROUPS.items():
        hit = sorted(set(members) & remaining)
        if hit:
            groups[name] = hit
            remaining -= set(hit)
    return {
        "control_actions": report.agent_action_required,
        "grouped_actions": len(groups),
        "groups": groups,
        "ungrouped": sorted(remaining),
    }


# --------------------------------------------------------------------------------------------- #
# Axis 5 — remaining actor burden, computed from observation
#
# The governing invariant, and the whole point of the migration:
#
#     A declaration never reduces burden. Only an observed result does.
#
# The old model let `enforcement_expectation: ENFORCED` discharge 49 controls to zero actor cost on
# the strength of a word, and a regex over `verification_expectation` credit 59 as mechanically
# verified when 9 had anything that executed. Nothing below reads prose, and no branch reaches
# NO_ACTION from a declared mechanism alone.
# --------------------------------------------------------------------------------------------- #

def remaining_burden(record: dict, observed: str, applicable: bool,
                     baseline_validated: bool = False) -> str:
    """What the actor still owes for this control, given what was actually observed."""
    from . import checks as checks_mod

    if record.get("schema_version") != 2:
        # A v1 record cannot be reasoned about on these axes. It never passes.
        return BLOCKED_UNRESOLVED
    if not applicable:
        return NO_ACTION

    if observed == checks_mod.PASS:
        return NO_ACTION
    if observed == checks_mod.FAIL:
        return REPAIR_REQUIRED
    if observed in (checks_mod.ERROR, checks_mod.STALE, checks_mod.UNVERIFIABLE):
        return BLOCKED_UNRESOLVED

    discharge = record.get("discharge_mechanism")
    if discharge == "INDEPENDENT_ASSURANCE":
        return ASSURANCE_REQUIRED
    if discharge == "HUMAN_DECISION":
        return DECISION_REQUIRED
    if discharge == "EVIDENCE_SUBMISSION":
        return EVIDENCE_REQUIRED
    if discharge == "INHERITED_BASELINE":
        # Only an explicitly VALIDATED baseline discharges. A declared one does not.
        return NO_ACTION if baseline_validated else ACTION_REQUIRED
    if discharge in ("DEFINED_PROCEDURE", "EXTERNAL_MECHANICAL_CHECK", "NO_MECHANISM",
                     "EXECUTING_CHECK"):
        return ACTION_REQUIRED
    return BLOCKED_UNRESOLVED


def observe_control(root, control_id: str, record: dict, applicable: bool) -> str:
    """Axis 4. Computed by executing something, or by honestly reporting that nothing ran."""
    from . import checks as checks_mod

    if record.get("schema_version") != 2:
        return checks_mod.NOT_EVALUATED
    if not applicable:
        return checks_mod.NOT_APPLICABLE
    if record.get("verification_mechanism") != "CHECK_REF":
        # No local verifier exists. NOT a pass, and not NOT_APPLICABLE either.
        return checks_mod.NOT_YET_RUN
    ref = record.get("verification_ref")
    if not ref:
        return checks_mod.ERROR
    return checks_mod.execute(control_id, ref, root).state


def burden_partition(root, scenario: "Scenario", baseline_validated: set | None = None) -> dict:
    """Every control, exactly once, across both computed axes. Sums are asserted by test."""
    baseline_validated = baseline_validated or set()
    flat = controls_mod.all_controls(root)
    traits = active_traits(scenario.as_work())

    observed_counts = collections.Counter()
    burden_counts = collections.Counter()
    per_control = {}

    for cid, record in flat.items():
        ok, _why = applies(record, scenario.work_type, traits)
        observed = observe_control(root, cid, record, ok)
        burden = remaining_burden(record, observed, ok, cid in baseline_validated)
        observed_counts[observed] += 1
        burden_counts[burden] += 1
        per_control[cid] = {"applicable": ok, "observed": observed, "burden": burden,
                            "discharge": record.get("discharge_mechanism"),
                            "verification": record.get("verification_mechanism")}

    total = len(flat)
    assert sum(observed_counts.values()) == total, "observed partition is not exhaustive"
    assert sum(burden_counts.values()) == total, "burden partition is not exhaustive"
    return {
        "total": total,
        "observed": dict(observed_counts),
        "burden": dict(burden_counts),
        "actor_actions": sorted(c for c, v in per_control.items()
                                if v["burden"] not in BURDEN_FREE),
        "per_control": per_control,
    }


# --------------------------------------------------------------------------------------------- #
# Burden decomposition (Product Authority ruling 2026-08-01)
#
# The 92 was accurate and mis-labelled. It counted every unresolved obligation and called the total
# "small-task burden", which multiplied standing project debt into every typo fix as though each
# task had created the gap. Debt and task burden are different dimensions.
#
# The rule that keeps this honest rather than cosmetic:
#
#     not every unresolved standing control is a per-task action
#     but every unresolved standing control must propagate to the actions that depend on it
#
# Nothing below special-cases a work type. Divergence comes from triggers and dependencies or it
# does not come at all.
# --------------------------------------------------------------------------------------------- #

# Standing control state, DERIVED from project evidence. Never authored in a control record.
NOT_ESTABLISHED = "NOT_ESTABLISHED"
VALID = "VALID"
STALE = "STALE"
FAILED = "FAILED"
UNVERIFIABLE = "UNVERIFIABLE"
STANDING_NOT_APPLICABLE = "NOT_APPLICABLE"

STANDING_STATES = (NOT_ESTABLISHED, VALID, STALE, FAILED, UNVERIFIABLE, STANDING_NOT_APPLICABLE)

#: What a standing gap blocks. Explicit, narrow, and justified per entry -- a missing deployment
#: baseline must not block a documentation typo, and a missing continuity baseline must block
#: everything that mutates.
BASELINE_DEPENDENCIES = {
    "PBG-CONT-001": {"blocks": ("TASK", "CHANGE", "CONTROLLED_ACTION", "INCIDENT"),
                     "why": "no canonical Build Log or Active Work: nothing durable records the work"},
    "PBG-FWK-013": {"blocks": ("TASK", "CHANGE", "CONTROLLED_ACTION", "INCIDENT"),
                    "why": "the pinned snapshot is unverified: what is loaded is not known to be what was pinned"},
    "PBG-SOV-001": {"blocks": ("CHANGE", "CONTROLLED_ACTION"),
                    "why": "project boundaries undeclared: writes cannot be shown to stay inside them"},
    "PBG-BOOT-006": {"blocks": ("CHANGE", "CONTROLLED_ACTION"),
                     "why": "standards baseline not acknowledged"},
    "PBG-RT-010": {"blocks": ("CONTROLLED_ACTION",),
                   "why": "container readiness unestablished: relevant to deployment, not to a typo"},
    "PBG-RT-013": {"blocks": ("CONTROLLED_ACTION",),
                   "why": "storage classes undeclared: a deployment concern"},
    "PBG-SEC-001": {"blocks": ("CONTROLLED_ACTION",),
                    "why": "configuration boundary unestablished"},
    "PBG-SEC-003": {"blocks": ("CONTROLLED_ACTION",),
                    "why": "interface boundaries unestablished"},
}


def standing_state(root, control_id: str, record: dict, observed: str,
                   baseline_evidence: dict | None = None) -> str:
    """Derive a standing control's state from project evidence, not from its own declaration."""
    from . import checks as checks_mod

    baseline_evidence = baseline_evidence or {}
    if (record.get("applicability") or {}).get("mode") != "STANDING":
        return STANDING_NOT_APPLICABLE
    if observed == checks_mod.PASS:
        return VALID
    if observed == checks_mod.FAIL:
        return FAILED
    if observed in (checks_mod.ERROR, checks_mod.UNVERIFIABLE):
        return UNVERIFIABLE
    if observed == checks_mod.STALE:
        return STALE

    entry = baseline_evidence.get(control_id)
    if entry is None:
        # No project has recorded establishing this. Debt, not a per-task action.
        return NOT_ESTABLISHED
    if entry.get("stale"):
        return STALE
    return VALID if entry.get("established") else NOT_ESTABLISHED


def read_baseline_evidence(root) -> dict:
    """Project-recorded evidence that a standing control was established, and when.

    Absent means NOT_ESTABLISHED. It never means satisfied.
    """
    import yaml
    path = Path(root) / "governance" / "baseline-evidence.yaml"
    if not path.is_file():
        return {}
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return doc.get("controls") or {}


def decompose(root, scenario: "Scenario", baseline_evidence: dict | None = None) -> dict:
    """The actor view, with debt and task burden kept apart. All 127 accounted for."""
    from . import checks as checks_mod

    evidence = baseline_evidence if baseline_evidence is not None else read_baseline_evidence(root)
    flat = controls_mod.all_controls(root)
    traits = active_traits(scenario.as_work())

    out = {k: [] for k in (
        "current_work_actions", "current_work_evidence_requirements", "current_work_decisions",
        "current_work_assurance_requirements", "project_baseline_gaps", "standing_validations_due",
        "blockers", "inherited_valid_baselines", "no_action_controls", "unclassified_controls")}
    total_unresolved = []

    for cid, record in flat.items():
        ok, why = applies(record, scenario.work_type, traits)
        observed = observe_control(root, cid, record, ok)
        burden = remaining_burden(record, observed, ok)
        mode = (record.get("applicability") or {}).get("mode")

        if burden not in BURDEN_FREE:
            total_unresolved.append(cid)

        if not ok:
            out["no_action_controls"].append(cid)
            continue

        if mode == "STANDING":
            state = standing_state(root, cid, record, observed, evidence)
            if state == VALID:
                out["inherited_valid_baselines"].append(cid)
            elif state == STALE:
                out["standing_validations_due"].append(cid)
            elif state in (FAILED, UNVERIFIABLE):
                out["blockers"].append(cid)
            else:                       # NOT_ESTABLISHED
                out["project_baseline_gaps"].append(cid)
                # Propagation: a gap still blocks the work that depends on it.
                dep = BASELINE_DEPENDENCIES.get(cid)
                if dep and scenario.work_type in dep["blocks"]:
                    out["blockers"].append(cid)
            continue

        # Everything else is current work, bucketed by what the actor actually owes.
        if burden == NO_ACTION:
            out["no_action_controls"].append(cid)
        elif burden == EVIDENCE_REQUIRED:
            out["current_work_evidence_requirements"].append(cid)
        elif burden == DECISION_REQUIRED:
            out["current_work_decisions"].append(cid)
        elif burden == ASSURANCE_REQUIRED:
            out["current_work_assurance_requirements"].append(cid)
        elif burden in (ACTION_REQUIRED, REPAIR_REQUIRED):
            out["current_work_actions"].append(cid)
        elif burden == BLOCKED_UNRESOLVED:
            out["blockers"].append(cid)
        else:                                                # pragma: no cover - guarded by test
            out["unclassified_controls"].append(cid)

    for v in out.values():
        v.sort()

    # Exhaustive accounting: every control lands exactly once, blockers excluded because a
    # blocker is a CROSS-REFERENCE to a control already counted in its own bucket.
    counted = sum(len(v) for k, v in out.items() if k != "blockers")
    result = {
        "scenario": scenario.name,
        "work_type": scenario.work_type,
        "applicable_controls_total": sum(
            len(out[k]) for k in out if k not in ("blockers", "no_action_controls")) +
            len([c for c in out["no_action_controls"]
                 if applies(flat[c], scenario.work_type, traits)[0]]),
        **{k: v for k, v in out.items()},
        "counts": {k: len(v) for k, v in out.items()},
        "total_unresolved_obligations": len(total_unresolved),
        "accounting_total": counted,
        "corpus_total": len(flat),
    }
    assert counted == len(flat), f"accounting is not exhaustive: {counted} of {len(flat)}"
    assert not out["unclassified_controls"], out["unclassified_controls"]
    return result
