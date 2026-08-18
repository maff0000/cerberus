"""Canonical resolved-state model.

ONE resolver. Every command consumes this, so five commands cannot produce five interpretations
of the same project — which is how PBGv1's tooling diverged.

Two rules run through it:

  1. A value read from Git, a value declared in YAML and a value inferred from a filename do not
     have equal authority. Every fact carries where it came from.

  2. Precedence establishes authority. It does NOT erase a contradiction. A lower-precedence
     source disagreeing is reported, never silently discarded.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --------------------------------------------------------------------------------------------- #
# Source types, ordered by default authority
# --------------------------------------------------------------------------------------------- #

PRODUCT_AUTHORITY_DECISION = "PRODUCT_AUTHORITY_DECISION"
PID_CONSTITUTIONAL = "PID_CONSTITUTIONAL"
AUTHORITY_RECORD = "AUTHORITY_RECORD"
GIT_OBSERVATION = "GIT_OBSERVATION"
RUNTIME_OBSERVATION = "RUNTIME_OBSERVATION"
BLUEPRINT = "BLUEPRINT"
PROJECT_MANIFEST = "PROJECT_MANIFEST"
ACTIVE_WORK = "ACTIVE_WORK"
BUILD_LOG = "BUILD_LOG"
TOOL_OBSERVATION = "TOOL_OBSERVATION"
DERIVED_INFERENCE = "DERIVED_INFERENCE"
GENERATED_PROJECTION = "GENERATED_PROJECTION"
AGENT_MEMORY = "AGENT_MEMORY"

#: Default order, weakest last. Deliberately NOT universal — see PRECEDENCE_BY_CLASS.
DEFAULT_PRECEDENCE = (
    PRODUCT_AUTHORITY_DECISION,
    PID_CONSTITUTIONAL,
    AUTHORITY_RECORD,
    GIT_OBSERVATION,
    RUNTIME_OBSERVATION,
    BLUEPRINT,
    PROJECT_MANIFEST,
    ACTIVE_WORK,
    BUILD_LOG,
    TOOL_OBSERVATION,
    DERIVED_INFERENCE,
    GENERATED_PROJECTION,
    AGENT_MEMORY,
)

#: Precedence is per FACT CLASS, because it genuinely differs. Product intent is documentary and
#: the PID outranks the code; implementation identity is observational and Git outranks any
#: document that describes it. A single global ladder would get one of those backwards.
PRECEDENCE_BY_CLASS: dict[str, tuple[str, ...]] = {
    # What the product is for — documentation outranks inference from the code.
    "product_purpose": (PRODUCT_AUTHORITY_DECISION, PID_CONSTITUTIONAL, BLUEPRINT, DERIVED_INFERENCE),
    "product_scope": (PRODUCT_AUTHORITY_DECISION, PID_CONSTITUTIONAL, AUTHORITY_RECORD, DERIVED_INFERENCE),

    # What the code IS — observation outranks every record that describes it.
    "current_sha": (GIT_OBSERVATION, ACTIVE_WORK, BUILD_LOG, GENERATED_PROJECTION, AGENT_MEMORY),
    "branch": (GIT_OBSERVATION, ACTIVE_WORK, BUILD_LOG, AGENT_MEMORY),
    "working_tree_state": (GIT_OBSERVATION, ACTIVE_WORK, AGENT_MEMORY),

    # What is RUNNING — the runtime outranks what a deployment intended.
    "runtime_image": (RUNTIME_OBSERVATION, TOOL_OBSERVATION, AUTHORITY_RECORD, BLUEPRINT, DERIVED_INFERENCE),
    "runtime_sha": (RUNTIME_OBSERVATION, TOOL_OBSERVATION, AUTHORITY_RECORD, DERIVED_INFERENCE),

    # Who may act — the authority record outranks a role file every time.
    "role_assignment": (AUTHORITY_RECORD, PRODUCT_AUTHORITY_DECISION, PROJECT_MANIFEST, AGENT_MEMORY),
    "authority_state": (AUTHORITY_RECORD, PID_CONSTITUTIONAL, PROJECT_MANIFEST),

    # What a host CAN do — observed capability only. A document cannot grant capability.
    "capability_state": (TOOL_OBSERVATION, RUNTIME_OBSERVATION),

    # Framework identity — the external anchor outranks the snapshot's own claim about itself.
    "framework_authenticity_level": (PROJECT_MANIFEST, PRODUCT_AUTHORITY_DECISION, TOOL_OBSERVATION),
    "framework_integrity_level": (TOOL_OBSERVATION,),

    # Where the work has got to — reconciled records outrank conversation, always.
    "work_progress": (GIT_OBSERVATION, ACTIVE_WORK, BUILD_LOG, AGENT_MEMORY),
}

# --------------------------------------------------------------------------------------------- #
# Conflict states
# --------------------------------------------------------------------------------------------- #

MATCH = "MATCH"
STALE_DECLARATION = "STALE_DECLARATION"
DRIFT = "DRIFT"
CONTRADICTION = "CONTRADICTION"
MISSING = "MISSING"
UNVERIFIABLE = "UNVERIFIABLE"

CONFLICT_MEANING = {
    MATCH: "All sources agree.",
    STALE_DECLARATION: "A lower-precedence source carries a superseded value.",
    DRIFT: "Recorded and observed values differ where they are expected to track each other.",
    CONTRADICTION: "Sources assert mutually incompatible facts.",
    MISSING: "No source supplied this fact.",
    UNVERIFIABLE: "A claim exists but no independent evidence supports it.",
}

#: States that must surface rather than resolve quietly. Precedence picks a value; these say the
#: disagreement still happened.
REPORTABLE = {STALE_DECLARATION, DRIFT, CONTRADICTION, UNVERIFIABLE}


class StateModelError(ValueError):
    """A resolution request that cannot be honoured coherently."""


@dataclass(frozen=True)
class Observation:
    """One source's claim about one fact."""

    value: object
    source_type: str
    source_ref: str = ""
    observed_utc: str | None = None
    authentic_or_derived: str = "AUTHENTIC"   # AUTHENTIC | DERIVED
    derivation_rule: str = ""
    independent_source: bool | None = None
    trust_anchor: str | None = None

    def __post_init__(self) -> None:
        if self.authentic_or_derived == "DERIVED" and not self.derivation_rule.strip():
            raise StateModelError(
                f"a DERIVED observation from {self.source_type} must name its derivation rule"
            )


@dataclass
class Fact:
    """A resolved fact, with the disagreement it resolved over still attached."""

    name: str
    fact_class: str
    value: object
    authoritative_source: str
    conflict_state: str
    observations: list[Observation] = field(default_factory=list)
    dissenting: list[Observation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def is_reportable(self) -> bool:
        return self.conflict_state in REPORTABLE

    @property
    def independently_verified(self) -> bool:
        """Did an independent source support this, rather than the claimant alone?"""
        return any(o.independent_source for o in self.observations)

    def render(self) -> str:
        lines = [f"{self.name}: {self.value!r}  [{self.conflict_state}]"]
        lines.append(f"  claim source      : {self.authoritative_source}")
        anchors = [o.trust_anchor for o in self.observations if o.trust_anchor]
        lines.append(f"  trust anchor      : {anchors[0] if anchors else 'none declared'}")
        lines.append(f"  independent source: {self.independently_verified}")
        for d in self.dissenting:
            lines.append(f"  DISAGREES         : {d.source_type} says {d.value!r} ({d.source_ref})")
        for n in self.notes:
            lines.append(f"  note              : {n}")
        return "\n".join(lines)


def _rank(source_type: str, order: tuple[str, ...]) -> int:
    try:
        return order.index(source_type)
    except ValueError:
        return len(order) + DEFAULT_PRECEDENCE.index(source_type) if source_type in DEFAULT_PRECEDENCE else 10_000


def resolve(
    name: str,
    fact_class: str,
    observations: list[Observation],
    expected_to_track: bool = False,
    requires_independent_evidence: bool = False,
) -> Fact:
    """Resolve one fact.

    `expected_to_track` marks facts where sources SHOULD hold the same value — a recorded SHA and
    an observed SHA, for instance. Disagreement there is DRIFT, not an ordinary difference of
    opinion, and it is the single most useful signal after an interruption.

    `requires_independent_evidence` marks claims that need a source other than the claimant. A
    Build Log entry saying the tests passed is not the test evidence.
    """
    if not observations:
        return Fact(name, fact_class, None, "none", MISSING,
                    notes=["no source supplied this fact"])

    order = PRECEDENCE_BY_CLASS.get(fact_class, DEFAULT_PRECEDENCE)
    ranked = sorted(observations, key=lambda o: _rank(o.source_type, order))
    winner = ranked[0]
    dissenting = [o for o in ranked[1:] if o.value != winner.value]

    if not dissenting:
        conflict = MATCH
    elif expected_to_track:
        # These sources are supposed to hold the same value. They do not.
        conflict = DRIFT
    else:
        higher = _rank(winner.source_type, order)
        # A weak, derived or projected source lagging is staleness. A peer-authority source
        # asserting something incompatible is a contradiction, and the difference matters:
        # one needs regeneration, the other needs a decision.
        if all(
            d.source_type in (GENERATED_PROJECTION, DERIVED_INFERENCE, AGENT_MEMORY, BUILD_LOG)
            or _rank(d.source_type, order) > higher + 1
            for d in dissenting
        ):
            conflict = STALE_DECLARATION
        else:
            conflict = CONTRADICTION

    fact = Fact(
        name=name,
        fact_class=fact_class,
        value=winner.value,
        authoritative_source=winner.source_type,
        conflict_state=conflict,
        observations=list(observations),
        dissenting=dissenting,
    )

    if requires_independent_evidence and not fact.independently_verified:
        # Precedence chose a value; nothing independent supports the claim.
        fact.conflict_state = UNVERIFIABLE
        fact.notes.append(
            "claim requires independent evidence; no independent source supplied it"
        )

    if conflict is CONTRADICTION:
        fact.notes.append("precedence selected a value; the contradiction is NOT resolved")

    return fact


@dataclass
class ResolvedState:
    """Everything a command needs, resolved once."""

    facts: dict[str, Fact] = field(default_factory=dict)

    def add(self, fact: Fact) -> None:
        self.facts[fact.name] = fact

    def get(self, name: str) -> Fact | None:
        return self.facts.get(name)

    def value(self, name: str, default=None):
        fact = self.facts.get(name)
        return default if fact is None else fact.value

    @property
    def reportable(self) -> list[Fact]:
        """Everything that disagreed. Boot, status, checkpoint and close all surface this."""
        return [f for f in self.facts.values() if f.is_reportable]

    @property
    def contradictions(self) -> list[Fact]:
        return [f for f in self.facts.values() if f.conflict_state == CONTRADICTION]

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for fact in self.facts.values():
            counts[fact.conflict_state] = counts.get(fact.conflict_state, 0) + 1
        return {
            "facts": len(self.facts),
            "by_conflict_state": counts,
            "reportable": [f.name for f in self.reportable],
            "contradictions": [f.name for f in self.contradictions],
        }


# --------------------------------------------------------------------------------------------- #
# Capability and authority stay separate — PBG-GIT-004
# --------------------------------------------------------------------------------------------- #

AVAILABLE = "AVAILABLE"
UNAVAILABLE = "UNAVAILABLE"
AUTHORISED = "AUTHORISED"
NOT_AUTHORISED = "NOT_AUTHORISED"

ACTION_PERMITTED = "PERMITTED"
ACTION_PROHIBITED = "PROHIBITED"
ACTION_CAPABILITY_GAP = "AMBER_RUNTIME_CAPABILITY_GAP"


def action_result(capability: str, authority: str) -> str:
    """Combine capability and authority without letting either become the other.

    Authority does not create capability, and capability does not create authority. The asymmetry
    matters: an unauthorised action is PROHIBITED whether or not the host could perform it, so
    losing a capability never launders a permission question into a technical one.
    """
    if authority != AUTHORISED:
        return ACTION_PROHIBITED          # decided first, and regardless of capability
    if capability != AVAILABLE:
        return ACTION_CAPABILITY_GAP
    return ACTION_PERMITTED


# --------------------------------------------------------------------------------------------- #
# Continuation policy — what is TRUE and what is SAFE are separate calculations
# --------------------------------------------------------------------------------------------- #
#
# Selecting an authoritative value answers "what value should be used for interpretation?".
# It does NOT answer "is it safe to proceed?". A resolver that returns a clean value and buries
# the disagreement in metadata has laundered the contradiction.

CONTINUE_UNAFFECTED_WORK = "CONTINUE_UNAFFECTED_WORK"
CONTINUE_READ_ONLY_ONLY = "CONTINUE_READ_ONLY_ONLY"
CONTINUE_WITH_AMBER = "CONTINUE_WITH_AMBER"
BLOCK_AFFECTED_ACTION = "BLOCK_AFFECTED_ACTION"
BLOCK_ALL_MUTATION = "BLOCK_ALL_MUTATION"
BLOCK_CLOSE = "BLOCK_CLOSE"
BLOCK_DEPLOYMENT = "BLOCK_DEPLOYMENT"
ESCALATE_PRODUCT_AUTHORITY = "ESCALATE_PRODUCT_AUTHORITY"

# Proposed actions the resolver can be asked about.
READ_SOURCE = "READ_SOURCE"
WRITE_SOURCE = "WRITE_SOURCE"
DISPATCH_ENGINEER = "DISPATCH_ENGINEER"
RUN_TESTS = "RUN_TESTS"
QUERY_RUNTIME = "QUERY_RUNTIME"
MUTATE_RUNTIME = "MUTATE_RUNTIME"
MIGRATE_DATABASE = "MIGRATE_DATABASE"
MERGE = "MERGE"
DEPLOY = "DEPLOY"
CLOSE = "CLOSE"
INCIDENT_DIAGNOSIS = "INCIDENT_DIAGNOSIS"

#: Actions that change governed state. Judged by effect, per PBG-RT-001.
MUTATING_ACTIONS = frozenset({
    WRITE_SOURCE, MUTATE_RUNTIME, MIGRATE_DATABASE, MERGE, DEPLOY, DISPATCH_ENGINEER,
})

#: Which actions each policy forbids. Deliberately narrow: over-blocking makes a framework that
#: gets switched off, and a stop-everything response to a stale projection teaches agents to
#: ignore the whole mechanism.
_POLICY_BLOCKS: dict[str, frozenset[str]] = {
    CONTINUE_UNAFFECTED_WORK: frozenset(),
    CONTINUE_WITH_AMBER: frozenset(),
    CONTINUE_READ_ONLY_ONLY: MUTATING_ACTIONS,
    BLOCK_ALL_MUTATION: MUTATING_ACTIONS | {CLOSE},
    BLOCK_AFFECTED_ACTION: frozenset({WRITE_SOURCE, MERGE, DEPLOY, CLOSE, DISPATCH_ENGINEER}),
    BLOCK_CLOSE: frozenset({CLOSE}),
    BLOCK_DEPLOYMENT: frozenset({DEPLOY}),
    ESCALATE_PRODUCT_AUTHORITY: MUTATING_ACTIONS | {CLOSE},
}

#: (fact_class, resolution_state) -> continuation policies.
#: The same resolution state means different things about different facts, which is the whole
#: reason this is a table rather than a rule about severity.
_CONTINUATION: dict[tuple[str, str], tuple[str, ...]] = {
    ("product_purpose", CONTRADICTION): (ESCALATE_PRODUCT_AUTHORITY,),
    ("product_scope", CONTRADICTION): (ESCALATE_PRODUCT_AUTHORITY,),
    ("authority_state", CONTRADICTION): (BLOCK_ALL_MUTATION,),
    ("role_assignment", CONTRADICTION): (BLOCK_ALL_MUTATION,),
    ("current_sha", DRIFT): (BLOCK_AFFECTED_ACTION,),
    ("branch", DRIFT): (BLOCK_AFFECTED_ACTION,),
    ("working_tree_state", DRIFT): (CONTINUE_WITH_AMBER,),
    # Diagnosis may continue read-only while deployment and close are shut.
    ("runtime_sha", DRIFT): (BLOCK_DEPLOYMENT, BLOCK_CLOSE),
    ("runtime_image", DRIFT): (BLOCK_DEPLOYMENT, BLOCK_CLOSE),
    ("work_progress", UNVERIFIABLE): (BLOCK_CLOSE,),
    ("framework_authenticity_level", CONTRADICTION): (BLOCK_ALL_MUTATION,),
    ("framework_integrity_level", CONTRADICTION): (BLOCK_ALL_MUTATION,),
}

#: Fallbacks when a class has no specific entry.
_CONTINUATION_DEFAULT: dict[str, tuple[str, ...]] = {
    MATCH: (CONTINUE_UNAFFECTED_WORK,),
    STALE_DECLARATION: (CONTINUE_UNAFFECTED_WORK,),   # regenerate; do not halt the project
    DRIFT: (CONTINUE_READ_ONLY_ONLY,),
    CONTRADICTION: (BLOCK_AFFECTED_ACTION,),
    MISSING: (CONTINUE_WITH_AMBER,),
    UNVERIFIABLE: (BLOCK_CLOSE,),
}


def continuation_policy(fact: Fact) -> tuple[str, ...]:
    """What may still proceed, given this fact's unresolved difference."""
    key = (fact.fact_class, fact.conflict_state)
    if key in _CONTINUATION:
        return _CONTINUATION[key]
    return _CONTINUATION_DEFAULT.get(fact.conflict_state, (CONTINUE_WITH_AMBER,))


def blocks_action(policies: tuple[str, ...], action: str) -> bool:
    return any(action in _POLICY_BLOCKS.get(p, frozenset()) for p in policies)


@dataclass
class ActionVerdict:
    action: str
    permitted: bool
    blocking: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)
    advisory: list[str] = field(default_factory=list)

    def render(self) -> str:
        head = f"{self.action}: {'PERMITTED' if self.permitted else 'BLOCKED'}"
        lines = [head]
        for name, policies in self.blocking:
            lines.append(f"  blocked by {name} -> {', '.join(policies)}")
        for note in self.advisory:
            lines.append(f"  advisory: {note}")
        return "\n".join(lines)


def evaluate_action(state: ResolvedState, action: str) -> ActionVerdict:
    """Is this specific action safe given every unresolved difference?

    Action-aware on purpose. The same runtime-identity drift that must block DEPLOY and CLOSE
    should still permit QUERY_RUNTIME and INCIDENT_DIAGNOSIS — otherwise the framework becomes
    stop-everything at exactly the moment someone needs to investigate.
    """
    blocking: list[tuple[str, tuple[str, ...]]] = []
    advisory: list[str] = []

    for fact in state.facts.values():
        policies = continuation_policy(fact)
        if blocks_action(policies, action):
            blocking.append((fact.name, policies))
        elif fact.is_reportable:
            advisory.append(f"{fact.name} is {fact.conflict_state} but does not block {action}")

    return ActionVerdict(action=action, permitted=not blocking, blocking=blocking, advisory=advisory)


def resolution_trace(fact: Fact) -> str:
    """Concise trace for a material fact. Detailed mode for assurance and diagnosis."""
    policies = continuation_policy(fact)
    lines = [
        f"Fact: {fact.name}",
        f"Selected value: {fact.value!r}",
        f"Source: {fact.authoritative_source}",
    ]
    for d in fact.dissenting:
        lines.append(f"Dissent: {d.source_type} records {d.value!r}"
                     + (f" ({d.source_ref})" if d.source_ref else ""))
    lines.append(f"State: {fact.conflict_state}")
    lines.append(f"Continuation: {', '.join(policies)}")
    if fact.is_reportable:
        lines.append("Required resolution: reconcile before the blocked actions may proceed")
    return "\n".join(lines)
