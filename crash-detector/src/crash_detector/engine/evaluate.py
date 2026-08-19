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
"""

from __future__ import annotations

import functools
from datetime import datetime
from typing import Mapping, Sequence

from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID, DialSet
from crash_detector.dials.reading import (
    AbsenceYieldedAValue,
    Degraded,
    Reading,
    Unknown,
    Value,
)
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.scores import EquityCrashScore, MonetaryDebasementScore
from crash_detector.engine.config import ConfigSnapshot, DialSpec
from crash_detector.observations import OK, ObservationRecord
from crash_detector.time_utc import age_seconds, ensure_utc

__all__ = [
    "evaluate",
    "DIAL_SCORE_TYPES",
    "REASON_NO_REQUIRED_INPUTS",
    "REASON_REQUIRED_INPUTS_UNAVAILABLE",
    "REASON_CONTRIBUTING_INPUTS_UNAVAILABLE",
    "REASON_NO_CONTRIBUTION_MODEL",
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
REASON_NO_CONTRIBUTION_MODEL = "NO_CONTRIBUTION_MODEL_DECLARED"


def evaluate(
    observations: Sequence[ObservationRecord],
    config_snapshot: ConfigSnapshot,
    now_utc: datetime,
) -> DialSet:
    """Compute both dials.

    Pure: the same arguments produce the same result, and nothing outside the arguments is
    read or written. No clock is consulted — ``now_utc`` is an argument precisely so that
    a historical evaluation can be replayed exactly.

    (The one way a caller can break that purity is by injecting a ``ContributionModel``
    that performs I/O. The contract forbidding it is stated on
    :class:`~crash_detector.engine.model.ContributionModel`, where an implementer reads
    it. In WO-2 no model is registered at all, so no model runs.)
    """
    instant = ensure_utc(now_utc)
    usable = _latest_usable_ok(
        observations,
        now_utc=instant,
        staleness_window_seconds=config_snapshot.staleness_window_seconds,
    )
    return DialSet(
        equity=_evaluate_dial(
            config_snapshot.spec_for(EQUITY_DIAL_ID), usable, instant
        ),
        monetary=_evaluate_dial(
            config_snapshot.spec_for(MONETARY_DIAL_ID), usable, instant
        ),
    )


def _latest_usable_ok(
    observations: Sequence[ObservationRecord],
    *,
    now_utc: datetime,
    staleness_window_seconds: float,
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
    """
    latest: dict[str, OK] = {}
    for record in observations:
        outcome = record.outcome
        if not isinstance(outcome, OK):
            continue
        age = age_seconds(as_of_utc=outcome.source_as_of_utc, now_utc=now_utc)
        if age < 0.0:
            continue
        if age > staleness_window_seconds:
            continue
        incumbent = latest.get(record.source_id)
        if incumbent is None or outcome.source_as_of_utc > incumbent.source_as_of_utc:
            latest[record.source_id] = outcome
    return latest


def required_inputs_are_all_present(
    spec: DialSpec, usable: Mapping[str, OK]
) -> bool:
    """Did this dial get everything it needs to produce a magnitude at all?

    THREE ways the answer is no, and each of them is a way a dial can fail to be a number
    without anything having gone wrong in the arithmetic:

    * the spec declares no required inputs — zero requirements satisfied is not "all
      requirements satisfied", and with the WO-2 empty source registry this is the shipped
      state of both dials;
    * the spec declares no contribution model, so there is no declared mapping from inputs
      to a magnitude (doctrine §3.6) and any number produced would be unexplainable;
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
    if spec.contribution_model is None:
        return False
    return all(source_id in usable for source_id in spec.required_input_ids)


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
        f"{'a contribution model is declared' if spec.contribution_model is not None else 'NO contribution model is declared'}"
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
) -> "Reading":
    """One dial's reading, or the named reason there is not one.

    Every ``return`` below is checked against
    :func:`refuse_a_number_without_its_inputs` by the decorator, so a branch that did not
    get its inputs cannot return a reading carrying a value however it is rewritten.
    """
    if not spec.required_input_ids:
        # The WO-2 state: no ingredient sources declared (CD-D-005 owed, BLUEPRINT §16).
        # Zero requirements satisfied is NOT "all requirements satisfied".
        return Unknown(
            reason=REASON_NO_REQUIRED_INPUTS,
            since_utc=now_utc,
            missing_inputs=(),
        )

    if spec.contribution_model is None:
        # DialSpec already refuses required inputs without a model, so this is currently
        # unreachable. It is kept as a named refusal rather than an assumption, because
        # "unreachable" is a claim about today's constructor and this is the dial path.
        return Unknown(
            reason=REASON_NO_CONTRIBUTION_MODEL,
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

    # A model that cannot compute honestly raises, and the exception travels. It is not
    # caught here and turned into a number, and it is not caught here and turned into
    # Unknown either: a model blowing up is a defect in the model, and swallowing it would
    # publish "we have no data" when the truth is "our code is broken".
    computation = spec.contribution_model.compute(payloads)
    # The magnitude is wrapped in this dial's provenance AT THE POINT IT IS COMPUTED, and
    # never travels as a bare float (CD-ASR-F01). `spec.dial_id` is the same key that
    # selected the score type on the line below, so the provenance and the type cannot
    # disagree: if they ever did, the score type's own constructor refuses.
    score = DIAL_SCORE_TYPES[spec.dial_id](
        score=DialMagnitude(dial_id=spec.dial_id, quantity=computation.magnitude),
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
    return min(usable[source_id].source_as_of_utc for source_id in used_ids)
