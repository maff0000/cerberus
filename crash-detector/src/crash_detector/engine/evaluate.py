"""``evaluate`` — the pure computation core (BLUEPRINT §7).

    evaluate(observations, config_snapshot, now_utc) -> DialSet

**No I/O of any kind inside it.** I/O happens at the edges — read observations, call
``evaluate``, write the result. That is not tidiness. It is what makes CD-AC-003's
"byte-identical with witnesses unreachable" a cheap repeatable check rather than an
environment exercise, and it makes every historical reading reproducible from its stored
inputs.

This module imports nothing from :mod:`crash_detector.witness`, and nothing reachable from
here does either. That is CD-AC-003 held structurally in the import graph, and held again
independently in the store, where ``cd_engine`` has no privilege of any kind on schema
``witness`` — not even ``USAGE``.

The absence rules, in one place, because scattering them is how one of them goes missing:

* a dial whose spec declares **no required inputs** is ``Unknown``. Zero satisfied
  requirements is not "all requirements satisfied" — that reading is exactly how an empty
  registry would come to publish a calm number, and it is refused here explicitly.
* a **required** input that is missing, stale, future-dated, or whose latest outcome is
  not ``OK`` forces ``Unknown``.
* a **contributing** input in the same condition forces ``Degraded``.
* nothing anywhere substitutes a zero, a previous value or a default.

====================================================================================
THE ABSENCE POST-CONDITION — added closing CD-ASR-F03 (MEDIUM)
====================================================================================

The four rules above were written down, implemented, and defeated. An independent auditor
replaced the ``missing_required`` branch of :func:`_evaluate_dial` with
``Value(value=<ScoreType>(score=QUIET_MAGNITUDE, ...))`` where ``QUIET_MAGNITUDE = 0.0``
was a module-level constant (`CD-ASR-F03`, escaped variant `E04`). The AST guard enumerated
four spellings of a numeric default and this was a fifth, so it saw nothing.

The lesson is that the rules were a property of *how this function happened to be written*,
and a rule that lives in a function body is rewritten by editing the function body. So the
rules are now enforced from **outside** the body, as a post-condition:
:func:`refuse_a_number_without_its_inputs` re-derives from ``(spec, usable)`` — the
function's own arguments, not its internal state — whether this dial actually got its
required inputs, and refuses the returned reading if it carries a value when it did not.

That is what makes the closure a CLASS closure rather than a fifth spelling caught. The
post-condition never asks where the number came from, so it does not care: a literal, a
module constant, a configuration default, a previous value carried across a gap, a random
number, a value read from the database — all of them raise
:exc:`~crash_detector.dials.reading.AbsenceYieldedAValue`, because what is refused is the
*claim* rather than the *arithmetic*. A reading that carries a value is a claim that inputs
were present; the post-condition checks the claim against the inputs.

It is deliberately one-directional. A body that returns ``Unknown`` when the inputs WERE
present is not refused: that is the safe direction, and a guard that compelled a number
would be pushing the wrong way.

====================================================================================
THE MODEL DOOR IS GONE (BP-AMENDMENT-0001 §C, in force)
====================================================================================

Until this commit the line below the payload assembly read::

    computation = spec.contribution_model.compute(payloads)

— a call on an object the CALLER had put in the ``DialSpec``. That is the line ``ASR3-F02``
published a laundered number through, and it **does not exist any more**. Not because it was
deleted: because there is no attribute on ``DialSpec`` holding an object, so there is no
expression that could be written there.

What stands in its place calls one engine-owned function,
:func:`crash_detector.engine.mapping.compute`, over a spec the engine RESOLVED from a name
and payloads the engine RELEASED. The consequence for this module's own headline claim is
that ``evaluate``'s purity got STRONGER, and the old caveat is withdrawn rather than
softened: there is no longer any object a caller can supply whose ``compute`` could perform
I/O, read a clock or hold state between the two dials, because there is no such parameter
and no such field.
"""

from __future__ import annotations

import functools
from datetime import datetime
from typing import Mapping, Sequence, Union

from crash_detector.admission import admits, each_of, one_of
from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID, DialSet
from crash_detector.dials.reading import (
    READING_CONSTRUCTORS,
    AbsenceYieldedAValue,
    Degraded,
    Reading,
    Unknown,
    Value,
)
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.provenance import observed_for_dial
from crash_detector.dials.scores import EquityCrashScore, MonetaryDebasementScore
from crash_detector.engine.config import ConfigSnapshot, DialSpec
from crash_detector.engine.mapping import compute
from crash_detector.engine.model import ModelSpec
from crash_detector.observations import OK, ObservationRecord
from crash_detector.staleness import StalenessWindow
from crash_detector.time_utc import age_seconds, ensure_utc

__all__ = [
    "evaluate",
    "DIAL_SCORE_TYPES",
    "REASON_NO_REQUIRED_INPUTS",
    "REASON_REQUIRED_INPUTS_UNAVAILABLE",
    "REASON_CONTRIBUTING_INPUTS_UNAVAILABLE",
    "REASON_NO_MODEL_DECLARED",
    "READINGS_THAT_CARRY_A_VALUE",
    "required_inputs_are_all_present",
    "refuse_a_number_without_its_inputs",
]

#: The two Reading constructors that carry a value, named as data. A reading of one of
#: these types is a CLAIM that this dial's inputs were present; the post-condition below
#: checks that claim against the inputs the dial was actually given.
READINGS_THAT_CARRY_A_VALUE: tuple[type, ...] = (Value, Degraded)

#: Which score type each dial carries. Two dials, two unrelated types (CD-AC-002).
DIAL_SCORE_TYPES: Mapping[str, type] = {
    EQUITY_DIAL_ID: EquityCrashScore,
    MONETARY_DIAL_ID: MonetaryDebasementScore,
}

# Stable reason classes. Recorded on the reading and carried into the envelope, so a
# consumer sees *why* a dial is not a number rather than only that it is not.
REASON_NO_REQUIRED_INPUTS = "NO_REQUIRED_INPUTS_DECLARED"
REASON_REQUIRED_INPUTS_UNAVAILABLE = "REQUIRED_INPUTS_UNAVAILABLE"
REASON_CONTRIBUTING_INPUTS_UNAVAILABLE = "CONTRIBUTING_INPUTS_UNAVAILABLE"
#: RENAMED at BP-AMENDMENT-0001 §C from ``REASON_NO_CONTRIBUTION_MODEL``
#: (``"NO_CONTRIBUTION_MODEL_DECLARED"``), because the type it named is deleted. The
#: PROPOSITION is unchanged — a dial that names no mapping is Unknown for that stated
#: reason. Nothing outside this module read either the constant or its value: it is absent
#: from both envelope schemas and from every test, which is why the rename is safe and why
#: keeping a name that points at a deleted type would have been the worse choice.
REASON_NO_MODEL_DECLARED = "NO_MODEL_DECLARED"


@admits(
    observations=each_of(ObservationRecord),
    config_snapshot=ConfigSnapshot,
    now_utc=datetime,
)
def evaluate(
    observations: Sequence[ObservationRecord],
    config_snapshot: ConfigSnapshot,
    now_utc: datetime,
) -> DialSet:
    """Compute both dials.

    **A2 AND A3 OF BP-AMENDMENT-0001 §D.2, ESTABLISHED AT THE DOOR AND DERIVED FROM THIS
    SIGNATURE.** ``config_snapshot`` must be exactly a
    :class:`~crash_detector.engine.config.ConfigSnapshot` — ``ASR3-F05`` supplied a duck
    object answering ``window()`` and ``spec_for()`` and it decided the window and both
    dials' specs, therefore both dials. ``observations`` must be a ``tuple`` or ``list``
    whose EVERY element is exactly an
    :class:`~crash_detector.observations.ObservationRecord` — the RECORD and not only its
    ``outcome``, which is already exact-typed one level in by ``_latest_usable_ok``: a
    look-alike record carrying an honest ``OK`` still decides its own ``source_id``, and
    which source an observation belongs to decides whether a required input was present.

    Neither requirement is written in this body. Both are read from the signature above by
    :func:`~crash_detector.admission.admits`, so an edit to this body cannot remove them and
    an argument added to this signature arrives REFUSED rather than unguarded.

    Pure: the same arguments produce the same result, and nothing outside the arguments is
    read or written. No clock is consulted — ``now_utc`` is an argument precisely so that
    a historical evaluation can be replayed exactly.

    **THE PURITY IS NOW STRUCTURAL AND THE OLD CAVEAT IS WITHDRAWN.** It used to read: *"the
    one way a caller can break that purity is by injecting a ContributionModel that performs
    I/O"*, and it pointed at a docstring contract for the remedy. A contract stated on a
    ``Protocol`` is not a runtime property, which is the whole of ``ASR3-F02``. After
    BP-AMENDMENT-0001 §C there is no field through which such an object can arrive, so
    ``evaluate`` is pure because the executor is pure and takes no caller code — a stronger
    purity than the one the injection argument bought.

    The model is RESOLVED here, per dial, through
    :meth:`~crash_detector.engine.config.ConfigSnapshot.model_for` — the one resolution
    door, which re-asserts every §C.5 invariant at the moment of resolution. Under the
    shipped :data:`~crash_detector.engine.model.EMPTY_MODEL_REGISTRY` both dials name no
    model, both resolutions answer ``None``, and both dials read ``Unknown``.
    """
    instant = ensure_utc(now_utc)
    usable = _latest_usable_ok(
        observations,
        now_utc=instant,
        window=config_snapshot.window(),
    )
    return DialSet(
        equity=_evaluate_dial(
            config_snapshot.spec_for(EQUITY_DIAL_ID),
            usable,
            instant,
            config_snapshot.model_for(EQUITY_DIAL_ID),
        ),
        monetary=_evaluate_dial(
            config_snapshot.spec_for(MONETARY_DIAL_ID),
            usable,
            instant,
            config_snapshot.model_for(MONETARY_DIAL_ID),
        ),
    )


def _latest_usable_ok(
    observations: Sequence[ObservationRecord],
    *,
    now_utc: datetime,
    window: StalenessWindow,
) -> Mapping[str, OK]:
    """The most recent usable ``OK`` observation per source.

    Only :class:`~crash_detector.observations.OK` is considered. ``FetchFailed``,
    ``Malformed`` and ``Empty`` are answers about the fetch, and none of them is a value —
    carrying any of them forward as one is the collapse BLUEPRINT §5 exists to prevent.

    An observation is **not usable** if:

    * it is older than the staleness window — it is treated as absent, not as a value
      with a caveat; or
    * it claims a ``source_as_of_utc`` **in the future**. A future-dated observation would
      otherwise never age out of the window, which is a stale reading that renders as
      current forever — CD-AC-001's failure mode reached by the back door. Source
      timestamps are external input and external input is hostile (Baseline §4). If a
      clock-skew allowance is ever wanted it is configuration with a declared value, not
      a tolerance quietly assumed here.

    **``window`` is a :class:`~crash_detector.staleness.StalenessWindow`, not a float, and
    that is the closure of CD-ASR-F06 on this path.** A bare number could be anything —
    ``1e18`` is a bare number, and it abolishes staleness on this path exactly as it did on
    the serving path. This private helper therefore cannot be called with an unadmitted
    quantity at all: the only way to obtain the argument is to construct one, and
    constructing one is the admission.
    """
    latest: dict[str, OK] = {}
    for record in observations:
        outcome = record.outcome
        # EXACT TYPE, not isinstance (CD-AC-005, Class 2). An `OK` subclass may shadow
        # `source_as_of_utc` with a property, and a property is the subclass's code running
        # inside this system's freshness decision. Skipping it is the fail-closed
        # direction: an outcome this function cannot recognise contributes nothing, exactly
        # as `FetchFailed`, `Malformed` and `Empty` contribute nothing. `outcome_class`,
        # which `ObservationRecord.__post_init__` calls, already admits by exact type, so
        # this is the same rule read at the second of the two sites rather than a new one.
        if type(outcome) is not OK:
            continue
        age = age_seconds(as_of_utc=outcome.source_as_of_utc, now_utc=now_utc)
        if not window.covers(age):
            continue
        incumbent = latest.get(record.source_id)
        # WHICH OBSERVATION IS THE LATEST IS DECIDED BY THIS SYSTEM. `>` between two stored
        # timestamps is the left operand's `__gt__` to define, so the comparison is made on
        # instants re-established here rather than on whatever the operands are. Both sides
        # are already canonical if they came through `OK.__post_init__`; putting them
        # through the door again costs nothing and removes the dependence on that being so.
        if incumbent is None or ensure_utc(outcome.source_as_of_utc) > ensure_utc(
            incumbent.source_as_of_utc
        ):
            latest[record.source_id] = outcome
    return latest


@admits(spec=DialSpec, usable=dict)
def required_inputs_are_all_present(
    spec: DialSpec, usable: Mapping[str, OK]
) -> bool:
    """Did this dial get everything it needs to produce a magnitude at all?

    THREE ways the answer is no, and each of them is a way a dial can fail to be a number
    without anything having gone wrong in the arithmetic:

    * the spec declares no required inputs — zero requirements satisfied is not "all
      requirements satisfied", and with the WO-2 empty source registry this is the shipped
      state of both dials;
    * the spec names no model, so there is no declared mapping from inputs to a magnitude
      (doctrine §3.6) and any number produced would be unexplainable. It reads the NAME and
      not a resolved spec, deliberately: the post-condition must re-derive its answer from
      the function's own arguments, and the resolved model is not one of them;
    * a declared required input is not in the usable set — absent, stale, future-dated, or
      its latest outcome was not ``OK``.

    These are the same three conditions the three ``Unknown`` branches of
    :func:`_evaluate_dial` test, restated here as ONE predicate over the arguments so that
    :func:`refuse_a_number_without_its_inputs` can recompute the answer without trusting
    anything the body decided. The duplication is the point and is disclosed rather than
    factored away: if the body and this predicate ever disagree, the post-condition raises
    and the disagreement is loud. What must not happen is the post-condition asking the body
    what it concluded, because the body is what a plant edits.
    """
    if not spec.required_input_ids:
        return False
    if spec.model_ref is None:
        return False
    return all(source_id in usable for source_id in spec.required_input_ids)


@admits(spec=DialSpec, usable=dict, reading=one_of(*READING_CONSTRUCTORS))
def refuse_a_number_without_its_inputs(
    spec: DialSpec, usable: Mapping[str, OK], reading: "Reading"
) -> None:
    """Refuse a value-bearing reading from a dial that did not get its inputs.

    The whole of CD-ASR-F03's runtime closure, and the reason it closes a CLASS: it never
    asks where the number came from. A literal, a module-level constant, a configuration
    default, a previous magnitude carried across an outage, a value read from the store —
    every one of them fails here, because what is refused is the *claim* that inputs were
    present and not any particular way of spelling a zero.

    One-directional on purpose: ``Unknown`` where a number was available is not refused.
    That is the safe direction, and a guard that compelled a number would be pushing
    against PID §3.2 rather than for it.
    """
    if type(reading) not in READINGS_THAT_CARRY_A_VALUE:
        return
    if required_inputs_are_all_present(spec, usable):
        return
    raise AbsenceYieldedAValue(
        f"dial {spec.dial_id!r} produced {type(reading).__name__}, which carries a value, "
        f"but its required inputs were not all present: it declares "
        f"{list(spec.required_input_ids)}, "
        f"{'it names model ' + repr(spec.model_ref) if spec.model_ref is not None else 'it NAMES NO MODEL'}"
        f", and the usable inputs are {sorted(usable)}. A reading that carries a value is "
        "a claim that its inputs were present; a dial that did not get them must be "
        "Unknown, whatever the number is and wherever it came from (PID §3.2, CD-AC-001, "
        "CD-ASR-F03)."
    )


def _absence_is_never_a_number(evaluate_one_dial):
    """Wrap a per-dial evaluator in the CD-ASR-F03 post-condition.

    The guard is applied HERE, at the boundary of the function, rather than written into
    its body, because the escape that produced CD-ASR-F03 was an edit to the body. A
    post-condition derived from the arguments survives any rewriting of what is between
    them and the return statement.
    """

    @functools.wraps(evaluate_one_dial)
    def guarded(
        spec: DialSpec,
        usable: Mapping[str, OK],
        now_utc: datetime,
        *extra: object,
        **extra_by_name: object,
    ) -> "Reading":
        # ``*extra`` is not laziness. The post-condition needs only the spec and the usable
        # inputs, and a wrapper that fixed the arity would stop guarding the moment anybody
        # gave the evaluator a fourth argument — which is exactly the kind of edit that
        # arrives with a new feature and takes a guard off with it.
        reading = evaluate_one_dial(spec, usable, now_utc, *extra, **extra_by_name)
        refuse_a_number_without_its_inputs(spec, usable, reading)
        return reading

    return guarded


@_absence_is_never_a_number
def _evaluate_dial(
    spec: DialSpec,
    usable: Mapping[str, OK],
    now_utc: datetime,
    model: "Union[ModelSpec, None]" = None,
) -> "Reading":
    """One dial's reading, or the named reason there is not one.

    Every ``return`` below is checked against
    :func:`refuse_a_number_without_its_inputs` by the decorator, so a branch that did not
    get its inputs cannot return a reading carrying a value however it is rewritten.

    ``model`` is the spec ``evaluate`` RESOLVED through
    :meth:`~crash_detector.engine.config.ConfigSnapshot.model_for`. It arrives through the
    ``*extra`` the post-condition wrapper already carries, which is what that wrapper was
    written with in the first place — *"a wrapper that fixed the arity would stop guarding
    the moment anybody gave the evaluator a fourth argument"*. This is that fourth argument,
    and the guard did not come off with it.
    """
    if not spec.required_input_ids:
        # The WO-2 state: no ingredient sources declared (CD-D-005 owed, BLUEPRINT §16).
        # Zero requirements satisfied is NOT "all requirements satisfied".
        return Unknown(
            reason=REASON_NO_REQUIRED_INPUTS,
            since_utc=now_utc,
            missing_inputs=(),
        )

    if spec.model_ref is None:
        # DialSpec already refuses required inputs without a model, so this is currently
        # unreachable. It is kept as a named refusal rather than an assumption, because
        # "unreachable" is a claim about today's constructor and this is the dial path.
        return Unknown(
            reason=REASON_NO_MODEL_DECLARED,
            since_utc=now_utc,
            missing_inputs=tuple(spec.required_input_ids),
        )

    missing_required = tuple(
        source_id
        for source_id in spec.required_input_ids
        if source_id not in usable
    )
    if missing_required:
        return Unknown(
            reason=REASON_REQUIRED_INPUTS_UNAVAILABLE,
            since_utc=now_utc,
            missing_inputs=missing_required,
        )

    missing_contributing = tuple(
        source_id
        for source_id in spec.contributing_input_ids
        if source_id not in usable
    )
    used_ids = tuple(spec.required_input_ids) + tuple(
        source_id
        for source_id in spec.contributing_input_ids
        if source_id in usable
    )
    payloads = {source_id: usable[source_id].payload for source_id in used_ids}

    # THE ENGINE EXECUTES THE MAPPING. THE CALLER SUPPLIED NEITHER THE CODE NOR THE NUMBER.
    #
    # This line used to read `spec.contribution_model.compute(payloads)` — a call on an
    # object the caller had put in the DialSpec — and it is the line ASR3-F02 published a
    # laundered number through. It cannot be written any more: DialSpec has no field holding
    # an object, so there is no expression that names one.
    #
    # `model` is a ModelSpec the engine RESOLVED from a name (ConfigSnapshot.model_for, the
    # one resolution door), `payloads` are values the engine RELEASED from OK observations
    # it selected, and `compute` is engine-owned, holds no state, and takes one dial's spec
    # and one dial's payloads. There is nothing here for a caller to close over.
    #
    # The refusal travels. It is not caught and turned into a number, and it is not caught
    # and turned into Unknown either: an executor that cannot compute honestly is a defect,
    # and swallowing it would publish "we have no data" when the truth is "our code is
    # broken". Under the shipped registry this line is unreachable — nothing resolves — and
    # under any registry WO-2 could carry it raises UnspecifiedMapping and returns nothing.
    computation = compute(model, payloads)
    # THE ONE ADMISSION SITE IN THE PRODUCT (CD-PL-F54, and see RULE 4 of
    # tools/register/check_no_blend.py, which admits a reference to `observed_for_dial`
    # from here and from nowhere else on the scanned path).
    #
    # This is where a number enters a dial from outside the system, and it is the only
    # place in src/ that may say so. The claim it makes is not decorative: `used_ids` is
    # the set of sources this dial's declared spec actually got, computed above from the
    # usable observations, and the enclosing function is wrapped by
    # `_absence_is_never_a_number`, which re-derives from (spec, usable) whether those
    # inputs were present at all and refuses the reading if they were not. So the
    # admission's citation and the post-condition's premise are the same evidence, read
    # twice, and a branch that did not get its inputs cannot reach this line and keep the
    # value it produced.
    #
    # The magnitude is wrapped in this dial's provenance AT THE POINT IT IS COMPUTED and
    # never travels as a bare float (CD-ASR-F01). `spec.dial_id` is the same key that
    # selected the score type below, and it is stated twice on purpose — once to the
    # admission door and once to the magnitude — because the magnitude compares the two by
    # SET EQUALITY rather than inferring either from the other.
    score = DIAL_SCORE_TYPES[spec.dial_id](
        score=DialMagnitude(
            dial_id=spec.dial_id,
            quantity=observed_for_dial(
                dial_id=spec.dial_id,
                quantity=computation.magnitude,
                inputs_used=used_ids,
            ),
        ),
        contributions=computation.contributions,
    )
    as_of = _oldest_as_of(usable, used_ids)

    if missing_contributing:
        return Degraded(
            value=score,
            as_of_utc=as_of,
            missing_inputs=missing_contributing,
            reason=REASON_CONTRIBUTING_INPUTS_UNAVAILABLE,
        )
    return Value(value=score, as_of_utc=as_of, inputs_used=used_ids)


def _oldest_as_of(usable: Mapping[str, OK], used_ids: Sequence[str]) -> datetime:
    """The reading is only as fresh as its oldest input.

    Taking the newest would make a reading look fresher than the data behind it, which is
    the stale-reads-as-calm failure with an extra step.
    """
    # `min` is decided by the elements' own `__lt__`, so the elements are re-established
    # first (CD-AC-005, Class 2): the reading's `as_of_utc` is what every later freshness
    # judgement about this reading is made against, and taking the newest rather than the
    # oldest would make a reading look fresher than the data behind it.
    return min(
        ensure_utc(usable[source_id].source_as_of_utc) for source_id in used_ids
    )
