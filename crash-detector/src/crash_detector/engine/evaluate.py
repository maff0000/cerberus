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
"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Sequence

from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID, DialSet
from crash_detector.dials.reading import Degraded, Reading, Unknown, Value
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
]

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


def _evaluate_dial(
    spec: DialSpec,
    usable: Mapping[str, OK],
    now_utc: datetime,
) -> "Reading":
    """One dial's reading, or the named reason there is not one."""
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
    score = DIAL_SCORE_TYPES[spec.dial_id](
        score=computation.magnitude, contributions=computation.contributions
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
