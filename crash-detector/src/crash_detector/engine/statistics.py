"""THE SECOND AND THIRD STATISTICS — ``acute`` and ``count``, BESIDE ``breadth``, NEVER INSIDE IT.

WO-1.3a round 2, built to ``governance/WO-1.3a-engine-spec.md`` §6 and to the §5 addendum
that ruled this module's shape.

====================================================================================
WHY THIS MODULE EXISTS AT ALL, AND WHY IT IS NOT A ``MappingKind`` MEMBER
====================================================================================

DECISION-RULE.md §6 asks each dial for THREE numbers, not one: ``breadth`` (how widely
stress is spread), ``acute`` (whether any ONE named composite is extreme) and ``count`` (how
many indicators are at their stress band). ``breadth`` already exists and is NOT touched
here: it is :func:`crash_detector.engine.mapping._banded_weighted_mean`, the executor branch
of ``MappingKind.BANDED_WEIGHTED_MEAN``, and it stays byte-identical to what it is today.

The obvious-looking move was a second ``MappingKind`` member computing all three. It was
investigated and REFUSED by the Product Owner (spec §5): ``MappingKind``/``ScoreComputation``
are sealed around ONE MAGNITUDE PER DIAL, which is ``ASR3-F02``'s repair, and a
three-statistic member would need either several ``ModelSpec`` rows for one dial (refused at
:func:`~crash_detector.engine.model.establish_model_for_dial`) or a widening of the sealed
type. The precedent taken instead is :mod:`crash_detector.engine.derivations`, which added
its own closed ``DerivationKind`` for a genuinely different kind of computation without
touching the model boundary. This module is that, for the masters.

====================================================================================
THE THREE PROPERTIES, RE-ESTABLISHED HERE AND NOT INHERITED
====================================================================================

:mod:`crash_detector.engine.mapping` holds three structural properties. **THEY ARE
PROPERTIES OF THAT MODULE AND NOT OF THE ENGINE**, so nothing about them carries across a
module boundary by itself. They are re-established here, by construction, and each one is
measured by ``tests/test_engine_masters.py``.

**1. IT TAKES NO CODE.** Every public function below takes exactly one argument, a ``tuple``
of :class:`~crash_detector.dials.scores.Contribution` — a frozen, slotted, exact-typed value
with no callable field — admitted by ``@admits(contributions=each_of(Contribution,
within=(tuple,)))``. The masters are DATA in this module, not objects a caller supplies, and
the way each master's components are reduced is a NAME from a closed enum executed by
:func:`_combined` below. There is no parameter through which a caller's function can arrive
and no field on :class:`Master` that could hold one.

**2. IT HOLDS NO STATE, BETWEEN DIALS OR BETWEEN RUNS.** Every function here is a
module-level function of its arguments. The only module-level bindings are the two frozen
masters tables, the provisional thresholds and the enums — no mutable binding of any kind,
so there is nowhere to put the first dial's figures while the second is computed. That was
``ASR3-F02``'s actual mechanism and it is the reason this is stated rather than assumed.

**3. IT CANNOT SPAN TWO DIALS, AND HERE IS HOW THAT IS PROVED.** The dial is in the
FUNCTION'S IDENTITY, never in a parameter: :func:`equity_crash_acute` reads
:data:`EQUITY_CRASH_MASTERS` and nothing else, :func:`monetary_debasement_acute` reads
:data:`MONETARY_DEBASEMENT_MASTERS` and nothing else. **There is no ``dial_id`` argument
anywhere in this module's public surface**, so there is no call through which one dial's
table could be pointed at the other dial's reading, and no shared "scaled score for
indicator X" helper for the two to meet in. Two separate tables, ruled by the Product Owner
(spec §5) over a single table keyed by dial, for a concrete reason: ``real_rate_10y_tips``
is bound to BOTH dials with OPPOSITE polarity and scores 1.0 on one and 0.0 on the other
FROM THE SAME UNDERLYING VALUE. A shared lookup would be exactly the cross-dial function
``tools/register/check_no_blend.py`` exists to catch, and this module is deliberately NOT in
that check's co-occurrence allowlist — the hazard is removed rather than the lint silenced.

The import-time assertions below state the same property as a property of the ARTEFACT: each
table's rows all name ONE dial, so a row filed under the wrong table stops this module
importing rather than quietly scoring an indicator against the other dial's masters.

====================================================================================
EVERY NUMBER IN THIS MODULE IS PROVISIONAL. NOT ONE OF THEM IS CALIBRATED.
====================================================================================

PO-DECISIONS-0025 r3 discipline, the same disclosure ``deploy/indicator-scaling.json`` and
``engine/derivations.py`` already carry: **no backtest has been run and no distribution
study has been done.** :data:`PROVISIONAL_WARNING`, :data:`PROVISIONAL_STRESS`,
:data:`PROVISIONAL_EXIT` and :data:`COUNT_THRESHOLD` are placeholders the Product Owner
placed in the spec so the state machine can be built and exercised at all (spec §2, §3).
They are stated here, in STATUS.md and in the spec as PROVISIONAL; they must be replaced by
WO-1.3b's calibration pass before any reading is relied on, and nothing in this module may
be read as a tuned threshold.

**A KNOWN DEFECT IN ``count`` AS SPECIFIED, CARRIED INTO WO-1.3b RATHER THAN FIXED HERE**
(spec §5): a scaled score is CLAMPED to 1.0 by the banded mean, so three indicators
(``michigan_sentiment``, ``real_rate_10y_tips``, ``shiller_cape``) sit at exactly 1.0 on
today's provisional bands and are counted as acute when what they are is SATURATED. ``count``
therefore measures band-narrowness as much as market stress — the same root cause as
``MATH.md`` R-6. Counting unclamped distance-to-stress instead is R2D2's open question for
WO-1.3b. It is written here so a reader of the code meets the limit where the number is
computed, not only in a governance file.

====================================================================================
WHAT THIS MODULE DOES NOT DO YET (spec §6, and it is the deliverable rather than a gap)
====================================================================================

NO PERSISTENCE COUNTING, NO SECOND-LEG RULE, NO PREVIOUS STATE AND NO OUTPUT CONTRACT.

Round 4 added ONE HALF of spec §3's state machine: :func:`candidate_state_for_one_reading`,
which answers *"ignoring how long anything has held, what state does THIS SINGLE READING's
data call for?"* — rules 1-6 read as a precedence over one reading's numbers. It has no
memory by construction. It never reads ``MachineStateHistoryStore``, it does not know what
the dial's previous official state was, and it does not count consecutive readings.

The OTHER half — spec §3's ``persistence`` counting (spec §7: the current evaluation plus the
immediately preceding rows, however many ``evaluator.resolve.PROVISIONAL_PERSISTENCE`` asks
for; it reads 5 since WO-1.3e and is PROVISIONAL there, so no number is quoted here where
nothing could enforce it), the second-leg rule, and rule 5's "the PREVIOUS state was
``ALARM``" condition — is the next round's wrapper around this function, and rule 5's
declared limit on that boundary is written out on the function itself. Read it before reading
a ``RECOVERY`` out of this module as a verdict; it is a candidate.

What round 2 left here is what both halves stand on, including the ability to say
``UNKNOWN``: see :class:`AcuteUnknown`, which exists NOW rather than being bolted on later,
because a statistic that cannot express "I do not know" has already turned an absence into a
number — and it is what makes rule 1 a type check rather than a sentinel comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from crash_detector.admission import admits, one_of
from crash_detector.dials.provenance import require_finite_float
from crash_detector.dials.scores import EQUITY_DIAL_ID, MONETARY_DIAL_ID, Contribution
from crash_detector.establishment import each_of, establishes
from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str

__all__ = [
    "State",
    "MasterCombine",
    "COMBINES_WITH_AN_EXECUTOR_BRANCH",
    "Master",
    "MasterScore",
    "MasterUnknown",
    "MASTER_RESULTS",
    "Acute",
    "AcuteUnknown",
    "ACUTE_RESULTS",
    "Count",
    "PROVISIONAL_WARNING",
    "PROVISIONAL_STRESS",
    "PROVISIONAL_EXIT",
    "COUNT_THRESHOLD",
    "PROVISIONAL_BREADTH_MID",
    "PROVISIONAL_BREADTH_HIGH",
    "PROVISIONAL_BREADTH_RISE_DEADBAND",
    "PROVISIONAL_COUNT_K",
    "EQUITY_CRASH_MASTERS",
    "MONETARY_DEBASEMENT_MASTERS",
    "equity_crash_masters",
    "equity_crash_acute",
    "monetary_debasement_masters",
    "monetary_debasement_acute",
    "count_for_one_dial",
    "candidate_state_for_one_reading",
]


class State(Enum):
    """THE CLOSED SET OF STATES ONE DIAL MAY BE IN (DECISION-RULE.md §6, spec §3).

    An :class:`enum.Enum` with members, for the reason
    :class:`~crash_detector.engine.model.MappingKind` and
    :class:`~crash_detector.engine.derivations.DerivationKind` are: the set is closed BY THE
    LANGUAGE — members cannot be added after class creation and the class cannot be
    subclassed — rather than by a check somebody could rewrite.

    **NO ORDERING IS DECLARED AND NONE MAY BE ASSUMED.** It is not an ``IntEnum`` and the
    members carry no severity rank, because the state machine spec §3 describes is a
    PRECEDENCE OF RULES, not a comparison of states: ``UNKNOWN`` wins over ``ALARM`` by rule
    1 while ``ALARM`` wins over ``WATCH`` by rules 2-4, and no single ``<`` relation
    expresses both. An ordering added for convenience here would be read as product meaning
    nobody ruled (``PBG-AUTH-005``). If round 3's machine genuinely needs one, it declares
    it there, as data, with its own reason.
    """

    #: EVERY MEMBER'S VALUE IS NAMESPACED ``state.*``, AND THAT IS NOT COSMETIC. PID §4's
    #: detail levels are the strings ``"calm"``, ``"elevated"`` and ``"acute"``, and
    #: :mod:`crash_detector.publication.detail_level` is the ONE module permitted to decide
    #: one — a rule ``test_detail_level.test_only_one_module_decides_a_detail_level``
    #: enforces by walking the package for those literals. A bare ``CALM = "calm"`` here
    #: produced exactly that literal in the engine, and the collision is not merely a lint:
    #: the two vocabularies answer different questions (how much to RENDER vs what the dial
    #: IS), they will never share a member list, and a stored ``"calm"`` whose vocabulary is
    #: ambiguous is a reading nobody can interpret a year later. The prefix is carried on
    #: ALL FIVE members rather than only the colliding one, so no later edit reads an odd
    #: member out as a typo and tidies the hazard back in.
    CALM = "state.calm"
    """No rule above CALM fired for this reading. It is the LAST branch of spec §3, never a
    default: a dial that could not be resolved is ``UNKNOWN``, and the two are different."""

    WATCH = "state.watch"
    """A master at or beyond its WARNING threshold, or breadth rising into mid-band."""

    ALARM = "state.alarm"
    """An ``alarm_eligible`` master at or beyond its STRESS threshold, or breadth at or
    beyond its high band. A firing eligible master fires ALARM on its own and no amount of
    calm elsewhere outvotes it; a WATCH-only master (``alarm_eligible=False``) never reaches
    this state by rule 2 at any score. Rule 3's breadth limb carried a ``count`` conjunct
    until WO-1.3e dropped it; breadth now fires this state alone."""

    RECOVERY = "state.recovery"
    """Late by design: every master back under its EXIT threshold for ``persistence``
    consecutive readings AND a trend confirmation. Both conditions, never either."""

    UNKNOWN = "state.unknown"
    """THE ABSENCE OF A RESOLVABLE STATE, NAMED. A required component was missing or stale,
    so this dial has no state for this reading — it does not have ``CALM``. CD-AC-001 is
    exactly this distinction and it is why this member is not optional."""


class MasterCombine(Enum):
    """THE CLOSED SET OF WAYS A MASTER'S COMPONENTS MAY BE REDUCED TO THE MASTER'S SCORE.

    The :data:`~crash_detector.dials.provenance.SAME_DIAL_REDUCTIONS` /
    :class:`~crash_detector.engine.model.MappingKind` pattern, one storey down. A master
    NAMES its combine rule in the table below; it does not carry one, so there is no field
    on :class:`Master` through which a caller's callable could arrive at the reduction.

    **TWO MEMBERS, BOTH COMPUTING, AND BOTH ARE THE PRODUCT OWNER'S (spec §2).** Masters v1
    is deliberately level-only: every master is the ``max`` of one or more EXISTING
    indicators' already-scaled scores, and a one-component master is ``IDENTITY`` rather
    than a ``max`` of one, because "the maximum of a single number" says less than the
    artefact knows. A third member is a product decision and not an implementation one.
    """

    IDENTITY = "identity"
    """Exactly one component, and the master's score IS that component's scaled score.
    Refuses — never averages, never picks — if handed anything but one component."""

    MAX = "max"
    """The largest of the components' scaled scores. This is the whole point of a master
    (DECISION-RULE.md §6): the average is ``breadth``'s job, and a master asks whether any
    ONE of its named components is extreme regardless of the average."""


#: Every :class:`MasterCombine` member that has a branch in :func:`_combined`, asserted by
#: set EQUALITY against the enum at import, in both directions.
#:
#: **THIS IS** :data:`crash_detector.engine.mapping.MAPPINGS_WITH_AN_EXECUTOR_BRANCH`
#: **RE-ESTABLISHED FOR THIS MODULE'S OWN ENUM, AND IT IS WHAT MAKES "NO FALLTHROUGH" A
#: PROPERTY OF THE MODULE RATHER THAN OF THIS SEAT'S CARE.** A member added to the enum
#: without a branch makes this module refuse to IMPORT — so the engine does not start,
#: rather than starting and reaching the end of :func:`_combined` with nothing to do. A
#: branch naming a member the enum does not declare is the same failure from the other side.
#:
#: A ``frozenset`` and not a list: membership is what is asserted, and order is not a
#: property of an enum's branches.
COMBINES_WITH_AN_EXECUTOR_BRANCH = frozenset({MasterCombine.IDENTITY, MasterCombine.MAX})

if COMBINES_WITH_AN_EXECUTOR_BRANCH != frozenset(MasterCombine):
    raise AssertionError(
        "COMBINES_WITH_AN_EXECUTOR_BRANCH and MasterCombine disagree about which combine "
        "rules this module can execute. The two are asserted by set equality because a "
        "declared member with no branch would fall out of the bottom of _combined() at the "
        "worst possible moment, and a branch with no member would be a reduction nobody "
        f"declared. Declared: {sorted(c.value for c in MasterCombine)}; branched: "
        f"{sorted(c.value for c in COMBINES_WITH_AN_EXECUTOR_BRANCH)}."
    )


#: PROVISIONAL (spec §2). The scaled score at or beyond which a master is WARNING.
#: Not calibrated, not backtested, placed by the Product Owner so the machine can be built.
PROVISIONAL_WARNING = 0.6

#: PROVISIONAL (spec §2). The scaled score at or beyond which a master is STRESSED — the
#: level that fires ALARM on its own under spec §3 rule 2, FOR AN ``alarm_eligible`` MASTER
#: (WO-1.3e). A WATCH-only row reaching this score does not fire rule 2 at all; see
#: :attr:`Master.alarm_eligible`. Not calibrated, not backtested.
PROVISIONAL_STRESS = 0.85

#: PROVISIONAL (spec §2). The scaled score a master must fall back UNDER before recovery can
#: even be considered. Strictly below :data:`PROVISIONAL_WARNING` on purpose: that gap is
#: the hysteresis DECISION-RULE.md §6 asks for, so a master hovering at its warning level
#: cannot flap. The gap is deliberate; its WIDTH is a placeholder like everything else here.
PROVISIONAL_EXIT = 0.5

#: PROVISIONAL (spec §1). The scaled score at or beyond which an indicator is counted by
#: :func:`count_for_one_dial`. 0.9 means "essentially at its stress band".
#:
#: **READ THE MODULE DOCSTRING'S NOTE ON ``count`` BEFORE USING THIS NUMBER.** A clamped
#: score of exactly 1.0 is counted here and clamping is saturation, not necessarily stress;
#: that is a known, disclosed defect carried into WO-1.3b, not a property of the market.
COUNT_THRESHOLD = 0.9

#: PROVISIONAL (spec §3, ``B_mid``). The breadth at or beyond which breadth ALONE — when it
#: is ALSO rising over the 20-reading lookback, by more than
#: :data:`PROVISIONAL_BREADTH_RISE_DEADBAND` — is enough for ``WATCH`` under rule 4. Not
#: calibrated, not backtested; one of spec §10's own "unset — calibration" rows.
PROVISIONAL_BREADTH_MID = 0.35

#: PROVISIONAL (spec §3, ``B_high``). The breadth which fires ``ALARM`` under rule 3 — ON ITS
#: OWN since WO-1.3e. Spec §3 pairs it with ``count`` at or beyond
#: :data:`PROVISIONAL_COUNT_K`; that conjunct was dropped on R2D2's interim recommendation
#: (finding B3), so this band is now the WHOLE of rule 3 and the only number standing
#: between a high breadth reading and ``ALARM``. Not calibrated.
#:
#: Strictly ABOVE :data:`PROVISIONAL_BREADTH_MID`, asserted at import below for the reason
#: :class:`Master` asserts ``exit < warning < stress`` about its own three: a high band at or
#: under the mid band would have rules 3 and 4 disagree about which reading is the more
#: serious, and the numbers being provisional is no licence for them to be incoherent.
PROVISIONAL_BREADTH_HIGH = 0.55

#: PROVISIONAL (R2D2's WO-1.3b finding B1, remediated in WO-1.3e). HOW MUCH BREADTH MUST
#: ACTUALLY HAVE RISEN over the lookback before rule 4's breadth limb will call it "rising".
#:
#: **THE DEFECT THIS CLOSES WAS LIVE.** Rule 4's limb compared ``here > earlier`` — a bare
#: ``>`` — so with breadth sitting at or just past :data:`PROVISIONAL_BREADTH_MID` an uptick
#: of 0.0001 between one reading and the reading 20 back was enough to turn ``CALM`` into a
#: ``WATCH`` candidate, and the next 0.0001 downtick enough to turn it back. R2D2 observed
#: exactly that flapping on the live dials. Breadth is a BANDED WEIGHTED MEAN of scaled
#: scores, so its last decimals are the scaling bands' arithmetic and not a market signal;
#: a rule that reads them is reading noise. The deadband says how big a move has to be
#: before the number is allowed to mean something.
#:
#: Not calibrated, not backtested: 0.02 is R2D2's suggested placeholder, two breadth points
#: on a 0-1 scale, and it is a placeholder in exactly the sense every other number here is.
#: It is a ONE-SIDED band and deliberately so — it raises the bar for claiming a rise, and
#: nothing anywhere reads "breadth fell", so there is no falling limb to widen symmetrically.
PROVISIONAL_BREADTH_RISE_DEADBAND = 0.02

#: PROVISIONAL (spec §3, ``k``). How many of a dial's contributing indicators must be at or
#: beyond :data:`COUNT_THRESHOLD` for rule 3's breadth-and-count ``ALARM``. An ``int``,
#: because it is compared against :attr:`Count.count`, which is a LENGTH and not a
#: measurement — there is no finite-float establishment to do on a count of names.
#:
#: **CURRENTLY UNUSED BY THE STATE MACHINE (WO-1.3e).** Rule 3 of
#: :func:`candidate_state_for_one_reading` reads BREADTH ALONE since R2D2's WO-1.3b finding
#: B3 — the count conjunct was dropped on R2D2's interim recommendation — so nothing in this
#: package compares anything against this number today. **Do not read a state machine
#: behaviour off it.**
#:
#: It is KEPT rather than deleted for two reasons. ``count`` itself is still fully computed
#: by :func:`count_for_one_dial` and still PUBLISHED on the contract and in the state
#: history, so the quantity this threshold is about remains a live reading. And the drop is
#: INTERIM: a future redesign of rule 3 may reintroduce a gate over the count, for which the
#: number spec §3 wrote down is the obvious starting point, where a deleted constant would
#: have to be re-derived from nothing.
#:
#: **READ THE MODULE DOCSTRING'S NOTE ON ``count``.** Three indicators sit CLAMPED at exactly
#: 1.0 on today's provisional bands, so this threshold is reachable by SATURATION alone. That
#: is recorded here because it bears on any attempt to reintroduce the gate; it is NOT stated
#: as R2D2's reason for the drop — the recommendation is theirs and this seat did not invent
#: a rationale for it.
PROVISIONAL_COUNT_K = 3

if not PROVISIONAL_BREADTH_MID < PROVISIONAL_BREADTH_HIGH:
    raise AssertionError(
        f"the provisional breadth bands read mid={PROVISIONAL_BREADTH_MID}, "
        f"high={PROVISIONAL_BREADTH_HIGH}. The two must read mid < high: spec §3 rule 3 "
        "treats the high band as MORE serious than rule 4's mid band, and bands that "
        "invert or coincide make the two rules describe the same reading differently."
    )

if not 0.0 < PROVISIONAL_BREADTH_RISE_DEADBAND < (
    PROVISIONAL_BREADTH_HIGH - PROVISIONAL_BREADTH_MID
):
    raise AssertionError(
        f"the breadth rise deadband reads {PROVISIONAL_BREADTH_RISE_DEADBAND} against a "
        f"mid-to-high band of {PROVISIONAL_BREADTH_HIGH - PROVISIONAL_BREADTH_MID}. It must "
        "be strictly positive, because a deadband of 0 IS the bare `>` comparison this "
        "constant exists to replace and a negative one would let a FALL read as a rise; and "
        "it must be strictly narrower than the gap between rule 4's mid band and rule 3's "
        "high band, because a deadband at least that wide would make a rise harder to "
        "evidence than the whole distance from WATCH's threshold to ALARM's — rule 4's limb "
        "would then be unreachable for any reading rule 3 does not already answer."
    )


@establishes(
    master_id=str,
    dial_id=str,
    component_ids=each_of(str, within=(tuple,)),
    combine=MasterCombine,
    warning_threshold=float,
    stress_threshold=float,
    exit_threshold=float,
    alarm_eligible=bool,
)
@dataclass(frozen=True)
class Master:
    """ONE MASTER: a named composite of existing indicators, with its own thresholds.

    FROZEN DATA AND NOTHING ELSE. There is no field here that holds code — the reduction is
    a :class:`MasterCombine` NAME executed by this module — and no field that holds a
    number this module computed: ``component_ids`` names indicators the dial already scores,
    and the three thresholds are the Product Owner's provisional placeholders.

    ====================================================================================
    ``alarm_eligible``: MAY THIS MASTER FIRE ``ALARM`` ON ITS OWN? (WO-1.3e)
    ====================================================================================

    Spec §3 rule 2 reads *"any master at or beyond its stress threshold → ALARM"*, and
    R2D2's WO-1.3b audit found two rows for which that sentence is not supportable by the
    backtest. ``alarm_eligible=False`` says this master is **WATCH-ONLY**: it is excluded
    from rule 2 and from NOTHING ELSE. It still scores, it still contributes to
    :class:`Acute`'s maximum and to :attr:`Acute.from_master_id`, it still fires rule 4's
    ``WATCH`` at its warning threshold, and rule 5 still requires it back under its exit
    threshold before a ``RECOVERY`` candidate. The demotion removes ONE privilege and
    leaves the master fully wired, which is what R2D2 asked for — capped below ALARM, not
    deleted from the dial.

    **IT IS A FIELD ON THE ROW AND NOT A NAME THE RULE LOGIC KNOWS, AND THAT IS THE WHOLE
    CHOICE.** The alternative — ``if master.master_id == "curve_master"`` somewhere inside
    :func:`candidate_state_for_one_reading` — would put a policy decision in a place no
    reader of the masters table could see it, would need a second edit in a second file the
    day the Owner confirms or reverses the demotion, and would be unfindable from the row it
    is about. Here the table states it, every row states it (there is no default, so a new
    master cannot arrive silently armed), and the state machine reads a fact the data
    carries rather than a list of names the code remembers.

    **WHY NOT JUST PARK THE STRESS THRESHOLD ABOVE 1.0?** Because that is a lie told in
    numbers. ``stress_threshold`` would then no longer describe where this master is
    stressed, the ``exit < warning < stress`` coherence this type enforces would be
    asserting an ordering over a sentinel, and the import-time uniformity assertion further
    down — the one that stops this module importing the day a master is genuinely
    recalibrated — would have been spent on a row nobody recalibrated. Eligibility and
    calibration are different facts and they get different fields.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `Master.__new__(Master)` followed by `__dict__.update(...)` yields an
    #: object of exactly this type carrying forged field values, having executed NO package
    #: code: the establishment boundary is not consulted, it is walked around. Declared here
    #: rather than via @dataclass(slots=True), which also installs a stdlib __setstate__
    #: that re-opens the same route by its sibling.
    __slots__ = (
        "master_id",
        "dial_id",
        "component_ids",
        "combine",
        "warning_threshold",
        "stress_threshold",
        "exit_threshold",
        "alarm_eligible",
    )

    master_id: str
    dial_id: str
    component_ids: tuple
    combine: MasterCombine
    warning_threshold: float
    stress_threshold: float
    exit_threshold: float
    alarm_eligible: bool

    def __post_init__(self) -> None:
        # RE-ESTABLISHED BEFORE THEY ARE JUDGED OR STORED (CD-AC-005, Class 2), exactly as
        # Contribution and ModelSpec re-establish theirs. The ids go through own_str, which
        # REBUILDS a str from the supplied value's own code points rather than approving the
        # object, so no supplied __eq__ or __hash__ decides a later lookup; the numbers go
        # through require_finite_float, which returns the established float.
        for field_name in ("master_id", "dial_id"):
            try:
                object.__setattr__(self, field_name, own_str(getattr(self, field_name)))
            except NotEstablishedOnOwnTerms as refusal:
                raise TypeError(f"Master.{field_name} must be a str: {refusal}") from None
        if not self.master_id:
            raise ValueError("Master requires a master_id")
        if not self.dial_id:
            raise ValueError("Master requires a dial_id")
        try:
            components = tuple(own_str(component) for component in self.component_ids)
        except NotEstablishedOnOwnTerms as refusal:
            raise TypeError(
                f"Master.component_ids must each be an indicator id: {refusal}"
            ) from None
        if not components:
            raise ValueError(
                f"master {self.master_id!r} declares no components. A master over nothing "
                "has no score, and an empty master would reduce to whatever the combine "
                "rule does with nothing — which is how an absence becomes a number."
            )
        if len(frozenset(components)) != len(components):
            raise ValueError(
                f"master {self.master_id!r} names the same component twice: {components}"
            )
        object.__setattr__(self, "component_ids", components)
        if type(self.combine) is not MasterCombine:
            raise TypeError(
                f"master {self.master_id!r} carries {type(self.combine).__name__} where a "
                "MasterCombine member belongs. A combine rule is a NAME from a closed set "
                "executed by this module, and nothing here dispatches on anything else."
            )
        if self.combine is MasterCombine.IDENTITY and len(components) != 1:
            raise ValueError(
                f"master {self.master_id!r} declares IDENTITY over {len(components)} "
                "components. IDENTITY means the master IS its single component; over "
                "several it would have to pick one, and picking silently is a guess."
            )
        for field_name in ("warning_threshold", "stress_threshold", "exit_threshold"):
            object.__setattr__(
                self,
                field_name,
                require_finite_float("Master", field_name, getattr(self, field_name)),
            )
        # THE HYSTERESIS, AS A PROPERTY OF THE ROW (DECISION-RULE.md §6, spec §2). Exit
        # BELOW warning below stress, or the row is refused: a table whose exit sits at or
        # above its entry is a table that flaps, and the numbers being provisional is not a
        # licence for them to be incoherent.
        if not self.exit_threshold < self.warning_threshold < self.stress_threshold:
            raise ValueError(
                f"master {self.master_id!r} declares exit={self.exit_threshold}, "
                f"warning={self.warning_threshold}, stress={self.stress_threshold}. The "
                "three must read exit < warning < stress: exit at or above entry is no "
                "hysteresis at all."
            )
        # EXACT TYPE AND NEVER TRUTHINESS. ``bool`` cannot be subclassed, so
        # ``type(value) is bool`` admits exactly ``True`` and ``False`` — there is nothing
        # to re-establish through an own_terms door the way ``master_id`` is, because the
        # two values ARE this system's own. What the check keeps out is ``1``, ``"yes"`` and
        # anything else that merely EVALUATES to armed: whether a master may fire rule 2 is
        # a stated fact about the row, and a value that happens to be truthy is a guess.
        # The @establishes boundary makes the same check one level out; it is repeated here
        # so the field is judged in the same place as every sibling rather than reading as
        # though it arrived unestablished.
        if type(self.alarm_eligible) is not bool:
            raise TypeError(
                f"master {self.master_id!r} carries "
                f"{type(self.alarm_eligible).__name__} where alarm_eligible's True or "
                "False belongs. A master is eligible to fire spec §3 rule 2 or it is "
                "WATCH-only, and the row says which."
            )


@establishes(master_id=str, dial_id=str, score=float, alarm_eligible=bool)
@dataclass(frozen=True)
class MasterScore:
    """ONE MASTER'S OWN SCORE for one reading, with the master and dial it belongs to.

    It is NOT a dial magnitude and carries no provenance: a magnitude is
    :class:`~crash_detector.dials.magnitude.DialMagnitude`, built at the one admission site
    in :mod:`crash_detector.engine.evaluate`, and nothing here goes near it.

    ====================================================================================
    WHY ``alarm_eligible`` RIDES ON THE SCORE WHEN THE THRESHOLDS DELIBERATELY DO NOT
    ====================================================================================

    :class:`Master` is where ``alarm_eligible`` is DECLARED; this type is where the state
    machine READS it, because :attr:`Acute.masters` is a tuple of these and
    :func:`candidate_state_for_one_reading` receives nothing else. The field is copied from
    the row by :func:`_master_result` and by no other code path.

    That is NOT the shortcut the thresholds were refused (see the import-time uniformity
    assertion further down), and the difference is the reason both decisions are right.
    The thresholds are UNIFORM across every row today, so the state machine can read
    module-level constants and an assertion stops it the day they stop being uniform.
    ``alarm_eligible`` is the opposite: it is NON-UNIFORM BY DESIGN — telling two rows apart
    is the entire point of it — so there is no constant it could ever be read from, and the
    only alternatives are carrying it here or looking the row up by ``master_id`` in a table
    selected by ``dial_id``. That lookup is the dial-keyed dispatch PROPERTY 3 of the module
    docstring says does not exist in this module, and it is not being introduced for this.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason given on :class:`Master`.
    __slots__ = ("master_id", "dial_id", "score", "alarm_eligible")

    master_id: str
    dial_id: str
    score: float
    alarm_eligible: bool

    def __post_init__(self) -> None:
        for field_name in ("master_id", "dial_id"):
            try:
                object.__setattr__(self, field_name, own_str(getattr(self, field_name)))
            except NotEstablishedOnOwnTerms as refusal:
                raise TypeError(
                    f"MasterScore.{field_name} must be a str: {refusal}"
                ) from None
        object.__setattr__(
            self, "score", require_finite_float("MasterScore", "score", self.score)
        )
        # Exact type and never truthiness, for the reason :class:`Master` records. There is
        # NO DEFAULT on this field and there must not be one: a default of ``True`` would
        # mean that a construction site which forgot to carry the row's eligibility through
        # silently RE-ARMS a master the Owner demoted, which is the one failure this field
        # exists to prevent.
        if type(self.alarm_eligible) is not bool:
            raise TypeError(
                f"MasterScore.alarm_eligible must be True or False, got "
                f"{type(self.alarm_eligible).__name__}. It is copied from the master row "
                "and says whether this score may fire spec §3 rule 2."
            )


@establishes(
    master_id=str,
    dial_id=str,
    missing_component_ids=each_of(str, within=(tuple,)),
)
@dataclass(frozen=True)
class MasterUnknown:
    """A MASTER THAT CANNOT BE SCORED FOR THIS READING, AND IT CARRIES NO NUMBER.

    **THERE IS NO ``score`` FIELD ON THIS TYPE AND THAT IS THE WHOLE POINT.** A required
    component was not in this dial's contributions — the indicator is MISSING or its feed is
    failing, so the banded mean never produced a scaled score for it — and spec §2 is
    explicit that such a master reads ``UNKNOWN`` and NOT 0.0. CD-AC-001's failure mode is a
    number standing in for an absence; a nullable score would be that failure with a
    ``None`` in front of it, which is why this is a separate type rather than an optional
    field (and why ``tools/register/check_no_numeric_default.py`` bans the alternative on
    this path by class).

    What it carries instead is WHICH components were missing, so the absence can be
    explained from the reading a year later without archaeology (BLUEPRINT §7).

    **IT CARRIES NO ``alarm_eligible`` EITHER, AND FOR THE SAME REASON IT CARRIES NO
    SCORE.** Eligibility answers "may this master's score fire rule 2?" and there is no
    score here to ask it of; spec §3 rule 1 has already returned ``UNKNOWN`` for the whole
    dial before any rule could consult it. A field nothing reads is a field that drifts.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason given on :class:`Master`.
    __slots__ = ("master_id", "dial_id", "missing_component_ids")

    master_id: str
    dial_id: str
    missing_component_ids: tuple

    def __post_init__(self) -> None:
        for field_name in ("master_id", "dial_id"):
            try:
                object.__setattr__(self, field_name, own_str(getattr(self, field_name)))
            except NotEstablishedOnOwnTerms as refusal:
                raise TypeError(
                    f"MasterUnknown.{field_name} must be a str: {refusal}"
                ) from None
        try:
            missing = tuple(own_str(name) for name in self.missing_component_ids)
        except NotEstablishedOnOwnTerms as refusal:
            raise TypeError(
                f"MasterUnknown.missing_component_ids must each be a str: {refusal}"
            ) from None
        if not missing:
            raise ValueError(
                f"master {self.master_id!r} is UNKNOWN for no stated missing component. An "
                "unexplained absence is not an explanation, and this type exists to carry "
                "the reason."
            )
        object.__setattr__(self, "missing_component_ids", missing)


#: The two things one master's result may be, as a closed tuple of type identities for
#: exact-identity dispatch. Membership here is IDENTITY: a look-alike and a subclass are
#: both absent from it. Used by callers (and by round 3's state machine) to branch on the
#: result without reaching for ``hasattr``, which is how an absence gets read as a number.
MASTER_RESULTS = (MasterScore, MasterUnknown)


@establishes(
    dial_id=str,
    score=float,
    from_master_id=str,
    masters=each_of(MasterScore, within=(tuple,)),
)
@dataclass(frozen=True)
class Acute:
    """ONE DIAL'S ACUTE STATISTIC: the largest of its masters' scores, and which one it was.

    ``score`` is ``max`` over this dial's masters (spec §2) and ``from_master_id`` names the
    master it came from, so a reading states WHICH signal is extreme rather than only that
    one is. ``masters`` carries every master's own score for the same reading — the
    explainability requirement of BLUEPRINT §7, and what spec §3's rules 2, 4 and 5 will
    read per master rather than off the maximum.

    A tie is resolved by the table's declared order, which is stable because the tables are
    frozen data; nothing here depends on which of two equal signals is named.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason given on :class:`Master`.
    __slots__ = ("dial_id", "score", "from_master_id", "masters")

    dial_id: str
    score: float
    from_master_id: str
    masters: tuple

    def __post_init__(self) -> None:
        for field_name in ("dial_id", "from_master_id"):
            try:
                object.__setattr__(self, field_name, own_str(getattr(self, field_name)))
            except NotEstablishedOnOwnTerms as refusal:
                raise TypeError(f"Acute.{field_name} must be a str: {refusal}") from None
        object.__setattr__(
            self, "score", require_finite_float("Acute", "score", self.score)
        )
        object.__setattr__(self, "masters", tuple(self.masters))
        if not self.masters:
            raise ValueError(
                "an Acute over no masters is not a statistic; a dial with no masters has "
                "no acute reading and must not be given one"
            )


@establishes(
    dial_id=str,
    unknown_master_ids=each_of(str, within=(tuple,)),
    missing_component_ids=each_of(str, within=(tuple,)),
)
@dataclass(frozen=True)
class AcuteUnknown:
    """THIS DIAL HAS NO ACUTE READING, AND IT CARRIES NO NUMBER.

    **THE PROPAGATION, BUILT NOW RATHER THAN BOLTED ON IN ROUND 3** (spec §2 and §3 rule 1):
    if ANY of a dial's masters is :class:`MasterUnknown`, the dial's acute statistic is
    UNKNOWN — not "the max of the ones we could compute", which would be a maximum over a
    silently thinned set and would read CALMER the more data is missing. That is CD-AC-001's
    failure mode stated in the one place it would be most tempting.

    Like :class:`MasterUnknown` it has no ``score`` field at all, and it carries which
    masters could not be scored and which components they were waiting on.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason given on :class:`Master`.
    __slots__ = ("dial_id", "unknown_master_ids", "missing_component_ids")

    dial_id: str
    unknown_master_ids: tuple
    missing_component_ids: tuple

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "dial_id", own_str(self.dial_id))
        except NotEstablishedOnOwnTerms as refusal:
            raise TypeError(f"AcuteUnknown.dial_id must be a str: {refusal}") from None
        for field_name in ("unknown_master_ids", "missing_component_ids"):
            try:
                established = tuple(
                    own_str(name) for name in getattr(self, field_name)
                )
            except NotEstablishedOnOwnTerms as refusal:
                raise TypeError(
                    f"AcuteUnknown.{field_name} must each be a str: {refusal}"
                ) from None
            if not established:
                raise ValueError(
                    f"AcuteUnknown requires {field_name}: an unexplained absence is not an "
                    "explanation"
                )
            object.__setattr__(self, field_name, established)


#: The two things one dial's acute statistic may be, as a closed tuple of type identities.
#: The same closed-set dispatch as :data:`MASTER_RESULTS`, one storey up.
ACUTE_RESULTS = (Acute, AcuteUnknown)


@establishes(
    at_or_beyond=each_of(str, within=(tuple,)),
    considered=each_of(str, within=(tuple,)),
)
@dataclass(frozen=True)
class Count:
    """THE THIRD STATISTIC: WHICH indicators are at or beyond :data:`COUNT_THRESHOLD`.

    ``count`` itself is :attr:`count`, derived from ``at_or_beyond`` rather than stored
    beside it, so there is no second number to drift out of agreement with the list that
    explains it.

    **IT COUNTS WHAT THE READING CARRIED AND IT SAYS SO.** ``considered`` is every
    contributing indicator present in the contributions it was given — the SAME set
    ``breadth`` is averaged over, by construction, because both read the one tuple
    ``_banded_weighted_mean`` returned. A Degraded dial's count is therefore a count over a
    thinned set exactly as its breadth is a mean over one, which is why
    :class:`~crash_detector.dials.reading.Degraded` states its missing inputs and why
    nothing here invents a count for an indicator that was absent.

    It carries NO dial id, and that is deliberate: there is no per-dial table in this
    computation, so a dial label here would be a caller's claim this module cannot check —
    exactly the kind of parameter property 3 in the module docstring exists to keep out.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason given on :class:`Master`.
    __slots__ = ("at_or_beyond", "considered")

    at_or_beyond: tuple
    considered: tuple

    def __post_init__(self) -> None:
        for field_name in ("at_or_beyond", "considered"):
            try:
                established = tuple(own_str(name) for name in getattr(self, field_name))
            except NotEstablishedOnOwnTerms as refusal:
                raise TypeError(
                    f"Count.{field_name} must each be an indicator id: {refusal}"
                ) from None
            object.__setattr__(self, field_name, established)
        if not frozenset(self.at_or_beyond) <= frozenset(self.considered):
            raise ValueError(
                "Count.at_or_beyond names an indicator that was not considered: "
                f"{sorted(frozenset(self.at_or_beyond) - frozenset(self.considered))}"
            )

    @property
    def count(self) -> int:
        """How many contributing indicators are at or beyond :data:`COUNT_THRESHOLD`."""
        return len(self.at_or_beyond)


#: THE EQUITY DIAL'S MASTERS (spec §2, Trinity, PO-authored). Frozen data, in the order the
#: spec's table declares them. Components are indicator ids the equity dial already scores,
#: and the scores read here are the ones THIS DIAL's bands produced — see the module
#: docstring on why there is no shared per-indicator lookup.
#:
#: EVERY THRESHOLD ON EVERY ROW IS PROVISIONAL AND UNCALIBRATED (PO-DECISIONS-0025 r3).
EQUITY_CRASH_MASTERS = (
    Master(
        master_id="credit_master",
        dial_id=EQUITY_DIAL_ID,
        component_ids=("hy_oas",),
        combine=MasterCombine.IDENTITY,
        warning_threshold=PROVISIONAL_WARNING,
        stress_threshold=PROVISIONAL_STRESS,
        exit_threshold=PROVISIONAL_EXIT,
        alarm_eligible=True,
    ),
    # WATCH-ONLY (WO-1.3e; R2D2's WO-1.3b audit of this row, verdict RED). An inverted curve
    # is a LEAD indicator measured in quarters, and rule 2 reads every master as though it
    # were a coincident one. R2D2 measured what that costs: curve-only readings were 39% of
    # all ALARM-day readings, and ONE curve-driven ALARM ran from 2022-11-04 to 2024-10-22 —
    # just under two years — while the S&P rose 55%. Capping this master below the level
    # that fires ALARM alone took ALARM-days from 19.9% to 11.9% of the backtest and raised
    # day-level precision from 0.16 to 0.26 with recall essentially unchanged (0.37 to
    # 0.36): the ALARMs it removes are very largely the wrong ones.
    #
    # IT IS DEMOTED AND NOT REMOVED. The curve still scores, still sets ``acute`` when it is
    # the extreme master, and still says WATCH at its warning threshold — which is what a
    # lead indicator is FOR. What it may no longer do is declare a crash on its own.
    Master(
        master_id="curve_master",
        dial_id=EQUITY_DIAL_ID,
        component_ids=("yield_curve_10y3m", "yield_curve_10y2y"),
        combine=MasterCombine.MAX,
        warning_threshold=PROVISIONAL_WARNING,
        stress_threshold=PROVISIONAL_STRESS,
        exit_threshold=PROVISIONAL_EXIT,
        alarm_eligible=False,
    ),
    Master(
        master_id="volatility_master",
        dial_id=EQUITY_DIAL_ID,
        component_ids=("vix_level", "vix_term_structure"),
        combine=MasterCombine.MAX,
        warning_threshold=PROVISIONAL_WARNING,
        stress_threshold=PROVISIONAL_STRESS,
        exit_threshold=PROVISIONAL_EXIT,
        alarm_eligible=True,
    ),
    Master(
        master_id="financial_conditions_master",
        dial_id=EQUITY_DIAL_ID,
        component_ids=("chicago_fed_nfci",),
        combine=MasterCombine.IDENTITY,
        warning_threshold=PROVISIONAL_WARNING,
        stress_threshold=PROVISIONAL_STRESS,
        exit_threshold=PROVISIONAL_EXIT,
        alarm_eligible=True,
    ),
)

#: THE MONETARY/DEBASEMENT DIAL'S MASTERS (spec §2, Trinity, PO-authored). A SEPARATE table
#: from the equity one, never a shared dict keyed by dial: ``real_rate_10y_tips`` appears
#: here AND on the equity dial with opposite polarity, scoring 0.0 here and 1.0 there from
#: one underlying value, and a shared lookup is precisely the cross-dial function this
#: project's no-blend rule exists to catch (spec §5).
#:
#: EVERY THRESHOLD ON EVERY ROW IS PROVISIONAL AND UNCALIBRATED (PO-DECISIONS-0025 r3).
MONETARY_DEBASEMENT_MASTERS = (
    # WATCH-ONLY (WO-1.3e; R2D2's WO-1.3b audit of the monetary masters, verdict RED). This
    # master is IDENTITY over ``fiscal_dominance``, which is a 0/1 FLAG — it has two values,
    # so it is either silent or pinned at the top of the scale, and there is no reading of
    # it that sits between. R2D2 measured a 0% hit rate for it across the whole backtest,
    # and the indicator itself is an Owner-UNCONFIRMED substitute for what the spec asked
    # for. A binary, unconfirmed, never-right input holding its own ALARM trigger is a
    # single flip away from declaring a crash.
    #
    # THE DEMOTION IS UNTIL OWNER-CONFIRMED, NOT FOREVER: when the Owner rules on what
    # ``fiscal_dominance`` is to be and it is calibrated against something, this row is the
    # one place the decision is written and the one line that has to change.
    Master(
        master_id="fiscal_master",
        dial_id=MONETARY_DIAL_ID,
        component_ids=("fiscal_dominance",),
        combine=MasterCombine.IDENTITY,
        warning_threshold=PROVISIONAL_WARNING,
        stress_threshold=PROVISIONAL_STRESS,
        exit_threshold=PROVISIONAL_EXIT,
        alarm_eligible=False,
    ),
    Master(
        master_id="real_rate_master",
        dial_id=MONETARY_DIAL_ID,
        component_ids=("real_rate_10y_tips",),
        combine=MasterCombine.IDENTITY,
        warning_threshold=PROVISIONAL_WARNING,
        stress_threshold=PROVISIONAL_STRESS,
        exit_threshold=PROVISIONAL_EXIT,
        alarm_eligible=True,
    ),
    Master(
        master_id="currency_master",
        dial_id=MONETARY_DIAL_ID,
        component_ids=("broad_dollar",),
        combine=MasterCombine.IDENTITY,
        warning_threshold=PROVISIONAL_WARNING,
        stress_threshold=PROVISIONAL_STRESS,
        exit_threshold=PROVISIONAL_EXIT,
        alarm_eligible=True,
    ),
)


def _one_dial_only(masters: tuple, declared: str) -> str:
    """The one dial every row in ``masters`` names, or a refusal naming what it found.

    PROPERTY 3 OF THE MODULE DOCSTRING, AS A PROPERTY OF THE ARTEFACT. It is asserted at
    import over each table below and again on every call, because a table is a module-level
    tuple and ``object.__setattr__`` walks past ``frozen`` on every frozen value in Python:
    the rows are read as they stand NOW, at the moment they are used to score a reading,
    rather than as they stood when the module was imported.
    """
    if not masters:
        raise ValueError("a masters table with no rows scores nothing and is refused")
    named = frozenset(master.dial_id for master in masters)
    if named != frozenset({declared}):
        raise ValueError(
            f"a masters table declared for dial {declared!r} holds rows naming "
            f"{sorted(named)}. One table is ONE dial's masters: a table that spans two is "
            "the cross-dial structure two separate tables exist to make impossible."
        )
    return declared


if _one_dial_only(EQUITY_CRASH_MASTERS, EQUITY_DIAL_ID) != EQUITY_DIAL_ID:
    raise AssertionError("the equity masters table does not name the equity dial")

if _one_dial_only(MONETARY_DEBASEMENT_MASTERS, MONETARY_DIAL_ID) != MONETARY_DIAL_ID:
    raise AssertionError("the monetary masters table does not name the monetary dial")


# **WHY :func:`candidate_state_for_one_reading` MAY READ THE MODULE-LEVEL THRESHOLDS, AND
# WHAT STOPS THAT BEING A LIE THE DAY THE TABLES CHANGE.**
#
# Spec §3 rules 2, 4 and 5 say "its stress threshold", "its warning threshold", "its exit
# threshold" — PER MASTER. :class:`Master` carries exactly those three fields per row, and it
# is :class:`MasterScore`, with no thresholds on it, that the state machine actually receives
# inside :attr:`Acute.masters`. Resolving a score's own row would mean a ``master_id`` lookup
# into the dial's table SELECTED BY :attr:`Acute.dial_id` — a dial-keyed dispatch, which is
# precisely the structure PROPERTY 3 of the module docstring says does not exist here and
# which spec §5 refused.
#
# So the state machine compares against the module-level constants, which is CORRECT ONLY
# BECAUSE EVERY ROW OF BOTH TABLES CARRIES EXACTLY THOSE CONSTANTS — and that is asserted
# here, at import, rather than left as a thing a reader would have to go and check. The day a
# master is given its own calibrated numbers (WO-1.3b's whole purpose), THIS MODULE STOPS
# IMPORTING and the next seat has to thread per-master thresholds through the state machine
# properly. It does not quietly judge a recalibrated master against the old shared number.
if any(
    (row.warning_threshold, row.stress_threshold, row.exit_threshold)
    != (PROVISIONAL_WARNING, PROVISIONAL_STRESS, PROVISIONAL_EXIT)
    for table in (EQUITY_CRASH_MASTERS, MONETARY_DEBASEMENT_MASTERS)
    for row in table
):
    raise AssertionError(
        "a master row carries thresholds of its own, and candidate_state_for_one_reading "
        "compares every master's score against the module-level PROVISIONAL_WARNING / "
        "PROVISIONAL_STRESS / PROVISIONAL_EXIT. That shortcut was sound only while the "
        "tables were uniform. Thread each master's OWN warning/stress/exit through the "
        "state machine now — do not relax this assertion, and do not judge a recalibrated "
        "master against a threshold it no longer declares (spec §3 rules 2, 4 and 5 each "
        "say *its* threshold)."
    )


def _combined(combine: MasterCombine, scores: tuple) -> float:
    """Execute ``combine``'s NAMED reduction over one master's component scores.

    Raises (never returns a number) when handed no scores at all, or an ``IDENTITY`` master
    with more than one. An empty reduction is not a score.
    """
    if type(combine) is not MasterCombine:
        raise TypeError(
            f"a combine rule is a MasterCombine member, got {type(combine).__name__}. This "
            "executor dispatches on a NAME from a closed set and on nothing else."
        )
    if not scores:
        raise ValueError(
            "a master was handed no component scores. Nothing is returned here: a "
            "reduction over nothing is an absence, and an absence is never a number."
        )

    if combine is MasterCombine.IDENTITY:
        if len(scores) != 1:
            raise ValueError(
                f"IDENTITY was handed {len(scores)} component scores. It means the master "
                "IS its single component; over several it would have to pick one."
            )
        return scores[0]

    if combine is MasterCombine.MAX:
        return max(scores)

    # NO `else`, NO FALLTHROUGH, AND NO RETURN. Reaching this line would require a
    # MasterCombine member with no branch above, and COMBINES_WITH_AN_EXECUTOR_BRANCH is
    # asserted equal to the enum at import — so a member added without a branch stops this
    # module importing rather than arriving here. There is deliberately no `raise` here
    # either: a catch-all at the bottom would be a place for a future edit to put a return.


def _scaled_scores(contributions: tuple) -> dict:
    """One dial's contributions, rebuilt as a plain ``dict`` of indicator id -> scaled score.

    The scores are ``_banded_weighted_mean``'s own, already scaled onto [0, 1] by THIS
    dial's bands. Nothing is re-scaled here and no band is read here — this module computes
    no scaling at all, which is what keeps the two dials' opposite polarities where they
    belong, in the one model spec that declared them.

    Rebuilt rather than consulted, for the reason :mod:`crash_detector.own_terms` gives at
    length: the judgement being made is WHICH indicator a score belongs to, and that is the
    supplied objects' ``__eq__`` and ``__hash__`` to answer unless the keys are re-established
    first. A duplicate id is REFUSED rather than last-wins: two scores for one indicator is
    not a reading this module can resolve, and silently keeping one of them is a guess.
    """
    established: dict = {}
    for contribution in contributions:
        if type(contribution) is not Contribution:
            raise TypeError(
                "a dial's contributions are exactly Contribution values, got "
                f"{type(contribution).__name__}. A look-alike decides its own attribute "
                "lookups, and which indicator a score belongs to is not a supplied "
                "object's judgement to make."
            )
        try:
            name = own_str(contribution.source_id)
        except NotEstablishedOnOwnTerms:
            raise NotEstablishedOnOwnTerms(
                "a contribution's source_id must be an indicator id, got "
                f"{type(contribution.source_id).__name__}"
            ) from None
        if name in established:
            raise ValueError(
                f"indicator {name!r} appears twice in one dial's contributions. Two scores "
                "for one indicator is not a reading, and keeping either one would be a "
                "choice this module has no grounds to make."
            )
        established[name] = require_finite_float(
            "Contribution", "contribution", contribution.contribution
        )
    return established


def _master_result(master: Master, scaled: dict):
    """One master's result over one dial's scaled scores: a score, or a stated UNKNOWN.

    THE MISSING-COMPONENT RULE (spec §2), and it is the whole reason this returns a sum type
    rather than a float: a component that is not in ``scaled`` was MISSING or FEED_FAILING
    for this reading, so the master has no score. It does not have 0.0, which on these bands
    would read as perfectly calm — the loudest possible way to get CD-AC-001 wrong.
    """
    if type(master) is not Master:
        raise TypeError(
            f"a master is exactly a Master row, got {type(master).__name__}. The masters "
            "are DATA in this module and are never accepted from a caller."
        )
    missing = tuple(
        component for component in master.component_ids if component not in scaled
    )
    if missing:
        return MasterUnknown(
            master_id=master.master_id,
            dial_id=master.dial_id,
            missing_component_ids=missing,
        )
    # ``alarm_eligible`` IS COPIED FROM THE ROW HERE AND NOWHERE ELSE (WO-1.3e). This is
    # the one site where a Master becomes a MasterScore, so it is the one site where the
    # row's WATCH-only demotion can be lost; the field has no default on either type, so
    # removing this line does not quietly re-arm the master — it raises.
    return MasterScore(
        master_id=master.master_id,
        dial_id=master.dial_id,
        score=_combined(
            master.combine,
            tuple(scaled[component] for component in master.component_ids),
        ),
        alarm_eligible=master.alarm_eligible,
    )


def _masters_over(masters: tuple, declared: str, contributions: tuple) -> tuple:
    """Every row of ONE table against ONE dial's contributions, in the table's own order."""
    _one_dial_only(masters, declared)
    scaled = _scaled_scores(contributions)
    return tuple(_master_result(master, scaled) for master in masters)


def _acute_over(masters: tuple, declared: str, contributions: tuple):
    """ONE dial's acute statistic: ``max`` over its masters, or UNKNOWN if any is UNKNOWN.

    The propagation is first and unconditional, per spec §3 rule 1: the maximum is taken
    only when EVERY master has a score. A max over the masters that happened to be
    computable would fall as data goes missing, and a statistic that gets calmer the less it
    knows is the defect this product exists to refuse.
    """
    results = _masters_over(masters, declared, contributions)
    unresolved = tuple(result for result in results if type(result) is MasterUnknown)
    if unresolved:
        waiting_on: list = []
        for result in unresolved:
            for component in result.missing_component_ids:
                if component not in waiting_on:
                    waiting_on.append(component)
        return AcuteUnknown(
            dial_id=declared,
            unknown_master_ids=tuple(result.master_id for result in unresolved),
            missing_component_ids=tuple(waiting_on),
        )
    highest = results[0]
    for result in results[1:]:
        if result.score > highest.score:
            highest = result
    return Acute(
        dial_id=declared,
        score=highest.score,
        from_master_id=highest.master_id,
        masters=results,
    )


@admits(contributions=each_of(Contribution, within=(tuple,)))
def equity_crash_masters(contributions: tuple) -> tuple:
    """Each EQUITY master's own result for this reading, in :data:`EQUITY_CRASH_MASTERS` order.

    One dial's contributions in, one dial's answers out. The table is this module's, not a
    parameter: there is no call through which the other dial's masters could arrive.
    """
    return _masters_over(EQUITY_CRASH_MASTERS, EQUITY_DIAL_ID, contributions)


@admits(contributions=each_of(Contribution, within=(tuple,)))
def equity_crash_acute(contributions: tuple):
    """The EQUITY dial's acute statistic: an :class:`Acute`, or an :class:`AcuteUnknown`."""
    return _acute_over(EQUITY_CRASH_MASTERS, EQUITY_DIAL_ID, contributions)


@admits(contributions=each_of(Contribution, within=(tuple,)))
def monetary_debasement_masters(contributions: tuple) -> tuple:
    """Each MONETARY master's own result, in :data:`MONETARY_DEBASEMENT_MASTERS` order.

    One dial's contributions in, one dial's answers out. The table is this module's, not a
    parameter: there is no call through which the other dial's masters could arrive.
    """
    return _masters_over(MONETARY_DEBASEMENT_MASTERS, MONETARY_DIAL_ID, contributions)


@admits(contributions=each_of(Contribution, within=(tuple,)))
def monetary_debasement_acute(contributions: tuple):
    """The MONETARY dial's acute statistic: an :class:`Acute`, or an :class:`AcuteUnknown`."""
    return _acute_over(MONETARY_DEBASEMENT_MASTERS, MONETARY_DIAL_ID, contributions)


@admits(contributions=each_of(Contribution, within=(tuple,)))
def count_for_one_dial(contributions: tuple) -> Count:
    """How many of ONE dial's contributing indicators are at or beyond :data:`COUNT_THRESHOLD`.

    ONE dial's contributions in, one dial's :class:`Count` out, and NO dial parameter: this
    statistic consults no per-dial table, so naming a dial here would be a label this module
    could not check rather than a structure it enforces (see :class:`Count`).

    The comparison is ``>=`` because :data:`COUNT_THRESHOLD` is spec §1's "at/beyond its
    stress band", and a clamped 1.0 therefore counts — read the module docstring's note on
    what that measures before reading the number as market stress.
    """
    scaled = _scaled_scores(contributions)
    considered = tuple(sorted(scaled))
    at_or_beyond = tuple(
        indicator for indicator in considered if scaled[indicator] >= COUNT_THRESHOLD
    )
    return Count(at_or_beyond=at_or_beyond, considered=considered)


@admits(
    breadth=float,
    acute=one_of(*ACUTE_RESULTS),
    count=Count,
    breadth_20_rows_ago=one_of(float, None),
    trend_confirmed=bool,
)
def candidate_state_for_one_reading(
    breadth: float,
    acute,
    count: Count,
    breadth_20_rows_ago: float | None,
    trend_confirmed: bool,
) -> State:
    """WHAT THIS ONE READING'S DATA CALLS FOR, IGNORING HOW LONG ANYTHING HAS HELD.

    Rules 1-6 of spec §3 as a PRECEDENCE over one reading's numbers, and nothing else. This
    is deliberately the smaller half of the state machine, and the split is the point:

    * **THIS function** asks *"on this reading's numbers alone, which rule fires?"* It has no
      memory. It does not know the dial's previous official state, it does not count
      consecutive readings, and it never reads ``MachineStateHistoryStore``.
    * **The next round's wrapper** decides whether that answer BECOMES the dial's state:
      spec §3's ``persistence`` counting (spec §7's reading of it — the current evaluation
      plus the immediately preceding rows for this dial, ``PROVISIONAL_PERSISTENCE`` of them
      in total, 5 since WO-1.3e), the second-leg rule,
      and the previous-state condition rule 5 carries.

    Persistence is a property of a SEQUENCE of readings; rules 1-6 are properties of ONE. A
    single function doing both would have to consult the history to answer "which rule
    fires", and every test of the rules would then be a test of the store as well.

    ====================================================================================
    **RULE 5'S DECLARED LIMIT — A ``RECOVERY`` FROM HERE IS A CANDIDATE, NOT A VERDICT.**
    ====================================================================================

    Spec §3 rule 5 reads *"Else if the dial's PREVIOUS state was ``ALARM`` AND (every
    master's acute ≤ its exit threshold for ``persistence`` consecutive readings) AND
    (trend-confirmed)"*. TWO of those three conditions are outside what one reading can
    answer — the previous state, and "for ``persistence`` consecutive readings" — and this
    function is built not to know either. What it computes is the REST of rule 5: every
    master back under its exit threshold ON THIS READING, and ``trend_confirmed``.

    So ``State.RECOVERY`` returned from here means *"this reading satisfies everything about
    rule 5 that a single reading can satisfy"*. **THE CALLER MUST DECIDE WHAT THAT IS WORTH.**
    When the previous state was not ``ALARM``, spec §3's own "Else" chain falls through to
    rule 6 and the state is ``CALM``; making that call needs the previous state, which is the
    wrapper's input and not this function's. **THIS IS A SCOPE BOUNDARY AND NOT A BUG** — it
    is written here, on the function, so that no caller can reach a ``RECOVERY`` out of this
    module without meeting the sentence that says it is not yet one.

    ``trend_confirmed`` is a PARAMETER THE CALLER SUPPLIES and is not computed from any wired
    indicator (spec §7's explicit scope cut): ``spx_vs_200dma`` exists in the mapping as a
    SCALED SCORE, not as a raw "above a flattening 200-day mean" boolean, and fabricating a
    trend signal to make ``RECOVERY`` work end to end was refused rather than overlooked.

    ====================================================================================
    THE PARAMETERS, AND THE ONE THING THIS FUNCTION CANNOT CHECK ABOUT THEM
    ====================================================================================

    ``breadth`` is :func:`crash_detector.engine.mapping._banded_weighted_mean`'s number for
    THIS reading, unchanged. ``breadth_20_rows_ago`` is the ONE earlier number rule 4's
    lookback needs — spec §7's provisional reading of "breadth rising over the last 20
    readings" is a simple lookback comparison and not a monotonicity requirement, so one
    number is the whole of it, and it is read through
    :data:`PROVISIONAL_BREADTH_RISE_DEADBAND`: breadth must be above it by MORE than the
    deadband for the limb to call that a rise (WO-1.3e, R2D2's finding B1). **``None`` MEANS
    "FEWER THAN 20 ROWS OF HISTORY EXIST", WHICH
    IS "CANNOT CONFIRM RISING" AND NEVER "DID NOT RISE"** — and the consequence is that
    rule 4's breadth limb cannot fire, while its per-master limb is unaffected. A young
    history therefore cannot be read as a calm one, which is the same sentence
    :class:`AcuteUnknown` exists for one storey down. Fetching that number is the caller's
    job; this function performs no query.

    ``count`` IS STILL A REQUIRED PARAMETER AND IS NO LONGER READ BY ANY RULE (WO-1.3e).
    Rule 3 dropped its count conjunct on R2D2's interim recommendation (finding B3), so this
    function computes nothing from ``count`` today. The parameter is KEPT, and the door still
    admits it as a :class:`Count`, because the caller's pairing of the three statistics for
    one dial is what the contract and the state history publish, and because the drop is
    interim: removing it from the signature would make reintroducing a count gate a change to
    every caller rather than a change to one rule. A reader who finds no use of it in the
    body has found the right thing — see :data:`PROVISIONAL_COUNT_K`.

    **DECLARED LIMIT: NOTHING HERE PROVES ``breadth``, ``count`` AND ``acute`` CAME FROM THE
    SAME DIAL.** ``acute`` carries a ``dial_id``; ``breadth`` is a bare ``float`` and
    :class:`Count` carries no dial at all. Adding a ``dial_id`` parameter to compare against
    would be a CALLER'S CLAIM this function could not check — the exact reasoning
    :class:`Count` already records for having no dial field — and a dial-keyed dispatch is
    the structure PROPERTY 3 of the module docstring says is absent here. The three
    statistics are PAIRED at the site that computes them for one dial from one evaluation,
    and that site is the next round's wrapper, not this function.

    Returns one :class:`State` member. It never returns ``None`` and there is no branch that
    falls out of the bottom: rule 6 is an answer, and :data:`State.CALM`'s own docstring says
    it is the last branch rather than a default.
    """
    # ESTABLISHED BEFORE ANY RULE IS JUDGED, AND BEFORE RULE 1'S EARLY RETURN. A NaN breadth
    # is refused on an UNKNOWN reading too: `NaN >= PROVISIONAL_BREADTH_HIGH` is False and
    # `NaN > earlier` is False, so an unestablished number would not raise here — it would
    # quietly make every breadth limb fail and read as the calm answer. The door's
    # `breadth=float` admits the TYPE; finiteness is this line's job.
    here = require_finite_float("candidate_state_for_one_reading", "breadth", breadth)
    earlier = (
        None
        if breadth_20_rows_ago is None
        else require_finite_float(
            "candidate_state_for_one_reading",
            "breadth_20_rows_ago",
            breadth_20_rows_ago,
        )
    )

    # RULE 1. FIRST, UNCONDITIONAL, AND A TYPE IDENTITY RATHER THAN A SENTINEL. "Stop; no
    # other rule overrides this" is the spec's own sentence, and `AcuteUnknown` has no
    # `score` field at all, so there is no number here to compare against a threshold even
    # by accident. Rules 2-6 below may therefore read `acute.masters` unguarded: past this
    # line `acute` is exactly an `Acute`, whose `masters` is non-empty by construction.
    if type(acute) is AcuteUnknown:
        return State.UNKNOWN

    # RULE 2. ANY ``alarm_eligible`` master at or beyond its stress threshold, read PER
    # MASTER and not off `acute.score`'s maximum. The spec says "any master", so the code
    # says it too — and SINCE WO-1.3e THE TWO NO LONGER AGREE: `acute.score` can be the
    # maximum of a WATCH-ONLY master's score, so reading the maximum here would fire ALARM
    # for exactly the rows R2D2's WO-1.3b finding B3 demoted (`curve_master`,
    # `fiscal_master`; the reasoning is on `Master.alarm_eligible` and on each row).
    #
    # AN INELIGIBLE MASTER AT 1.0 DOES NOT FIRE THIS RULE AT ANY BREADTH OR COUNT. The
    # eligibility term is FIRST in the conjunction so that the demotion is what the reader
    # meets before the threshold, and it is `master.alarm_eligible` and never a master id:
    # the policy lives on the row, which is the whole point of the field.
    #
    # Among the ELIGIBLE masters the rule is unchanged and unsoftened: no amount of calm
    # elsewhere in the reading outvotes a firing one (spec §3's parenthesis on this rule).
    if any(
        master.alarm_eligible and master.score >= PROVISIONAL_STRESS
        for master in acute.masters
    ):
        return State.ALARM

    # RULE 3. BREADTH ALONE SINCE WO-1.3e. Spec §3 writes this rule as breadth AND count
    # together and the code read
    # `here >= PROVISIONAL_BREADTH_HIGH and count.count >= PROVISIONAL_COUNT_K`; R2D2's
    # WO-1.3b finding B3 recommends dropping the count conjunct as an INTERIM measure, and
    # this is that drop. A reading at or beyond the high breadth band now fires ALARM with
    # NOTHING counted at all.
    #
    # `PROVISIONAL_COUNT_K` IS THEREFORE CURRENTLY UNUSED BY THIS STATE MACHINE, and the
    # constant is kept anyway — its docstring says why. `count` itself is untouched:
    # `count_for_one_dial` still computes it, and the contract and the state history still
    # publish it, because it is a reading operators read and the evidence any future
    # recalibration of a count gate would need. ONLY THIS GATE CHANGED.
    if here >= PROVISIONAL_BREADTH_HIGH:
        return State.ALARM

    # RULE 4. EITHER limb is enough, and they are independent: a master at warning fires
    # WATCH with breadth flat or falling, and breadth rising past the mid band fires WATCH
    # with every master quiet. `earlier is not None` is the first term because an absent
    # lookback means the comparison cannot be made at all.
    #
    # `> earlier + PROVISIONAL_BREADTH_RISE_DEADBAND` AND NOT `> earlier` (R2D2's WO-1.3b
    # finding B1, remediated in WO-1.3e; the constant carries the reasoning). A rise has to
    # be bigger than the deadband to count as one: with the bare `>`, breadth parked at the
    # mid band flapped WATCH/CALM on the last decimals of a weighted mean. "Rising" stays a
    # STRICT claim — a move of exactly the deadband is not a rise either, for the same
    # reason an unchanged number never was.
    rising_into_the_mid_band = (
        earlier is not None
        and here > earlier + PROVISIONAL_BREADTH_RISE_DEADBAND
        and here >= PROVISIONAL_BREADTH_MID
    )
    if (
        any(master.score >= PROVISIONAL_WARNING for master in acute.masters)
        or rising_into_the_mid_band
    ):
        return State.WATCH

    # RULE 5. EVERY master under exit AND the trend confirmed — both, never either (spec §3,
    # DECISION-RULE.md §6: late by design). Read the DECLARED LIMIT above: this is a
    # candidate, because the previous state and the consecutive-readings requirement are
    # the wrapper's to check.
    if (
        all(master.score <= PROVISIONAL_EXIT for master in acute.masters)
        and trend_confirmed
    ):
        return State.RECOVERY

    # RULE 6. The last branch of the precedence, and an answer in its own right.
    return State.CALM
