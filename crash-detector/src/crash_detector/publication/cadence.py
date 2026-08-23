"""Cadence on the publication layer (CD-AC-008, BLUEPRINT §8, §10).

    budget  = CadenceBudget(publication_interval_seconds=30.0, missed_cycles_allowed=1)
    verdict = evaluate_cadence(heartbeats_utc, now_utc=..., budget=budget)
    verdict.breached      # True iff some INTERVAL BETWEEN HEARTBEATS exceeded the budget

===========================================================================================
*** A CADENCE BREACH IS AN EXCESSIVE INTERVAL BETWEEN HEARTBEATS. IT IS NOT THE AGE OF A
    NUMBER. ***
===========================================================================================
BLUEPRINT §8 says it in those words, and the two come apart **exactly when it matters**:

* **a detector republishing a STALE number ON TIME** has a healthy cadence and stale data.
  Cadence says nothing is wrong, and cadence is right — the publisher is publishing. What is
  wrong is upstream, and it is :mod:`crash_detector.staleness`'s to say;
* **a detector publishing FRESH data LATE** has fresh data and a broken cadence. Freshness
  says nothing is wrong, and freshness is right — the number is current. What is wrong is
  that the pipeline stopped for a while, and **only cadence can see it**.

An instrument that conflated them would report exactly one of these two failures and would
report the other one wrongly.

**SO THIS MODULE IS BUILT SO THAT IT CANNOT SEE THE AGE OF A NUMBER.**
:func:`evaluate_cadence` takes heartbeat instants and ``now_utc``. It takes no reading, no
envelope, no ``as_of_utc`` and no dial. **There is no parameter through which the age of a
number could reach it**, so the conflation is not prevented by a rule that a future edit
could relax — it is unrepresentable in the signature. A test asserts the signature by
introspection, so widening it is a failing test rather than a discovery.

===========================================================================================
*** THE OPEN INTERVAL IS THE WHOLE POINT, AND IT IS THE EASY THING TO LEAVE OUT ***
===========================================================================================
The obvious implementation walks consecutive heartbeats and takes the largest gap. **IT
CANNOT DETECT THE FAILURE THE CRITERION IS ABOUT.** A publisher that has STOPPED writes no
further heartbeat, so it creates no further gap: the largest closed interval stays whatever
it was while the system was healthy, forever, and the check reports health about a dead
detector with total confidence.

The register's own scenario is *"publication halted while ingestion continues"* — the halted
case. So the interval that matters most is the **OPEN** one, from the LAST heartbeat to
``now_utc``, and it is the one that grows without bound when publication stops. Both are
measured here; the open one is why this module is not a one-line ``max(diff)``.

The same argument is why the store keeps ``publication.heartbeat`` as its own table rather
than reading ``public_envelope.published_utc``, and migration 5 says so: *"an envelope that
was never written leaves no timestamp to be old, and the absence of a heartbeat is what must
be detected."*

===========================================================================================
THE BUDGET IS DERIVED FROM TWO RATIFIED CLAUSES AND ONE DECLARED CONFIGURATION VALUE
===========================================================================================
**A NUMBER THAT CARRIES PRODUCT MEANING IS DERIVED WITH ITS CLAUSE CITED, OR THE SEAT FAILS
CLOSED** (``CD-RULE-003``). Three inputs, and not one of them is chosen here:

1. **THE PUBLICATION INTERVAL IS ALREADY DECLARED AND ALREADY HAS NO DEFAULT.**
   ``deploy/entrypoints/_service.py`` makes ``CD_TICK_INTERVAL_SECONDS`` **REQUIRED with no
   in-code default**, and states why in terms of this criterion: *"A tick interval nobody
   chose is a cadence nobody chose, and cadence is what CD-AC-008 alerts on: a default here
   would mean an alert threshold derived from a number no human picked."* That seat left the
   hole open on purpose. This module does not fill it: the interval is an argument.

2. **THE CEILING IS PID §5, THE SAME CLAUSE** :mod:`crash_detector.staleness` **DERIVES
   FROM.** *"pipeline/publication failure independently detectable ≤ 15 minutes."* A breach
   threshold WIDER than the detectability budget means a stopped publisher goes unreported
   for longer than the product permits a failure to go undetected. So the threshold is
   bounded from above at :data:`~crash_detector.staleness.STALENESS_WINDOW_CEILING_SECONDS`
   — 900 s — **and that constant is imported rather than retyped**, so the two derivations
   from one clause cannot drift apart.

3. **THE FLOOR IS A COHERENCE FACT, NOT A JUDGEMENT.** ``missed_cycles_allowed`` must be at
   least 1. At 0 the threshold equals the publication interval, and **a perfectly punctual
   publisher breaches on every single cycle** — an alarm that fires on correct behaviour is
   an alarm nobody reads, and the first response to it is to disable the alarm.

**NO TOLERANCE, GRACE OR FUDGE FACTOR IS INVENTED.** The threshold is exactly
``interval × (1 + missed_cycles_allowed)`` — an integer number of whole publication cycles,
so an operator reading it can say "we alert after N missed publishes" and be exactly right.

===========================================================================================
DECLARED LIMIT (CD-RULE-004). Stated identically here, in ``required-tests.yaml`` and in
``contracts/execution/CD-RT-008-CADENCE-BREACH-ALERTS.md``.
===========================================================================================
 1  **THIS MODULE JUDGES CADENCE AND CLAIMS NOTHING ABOUT DATA.** A detector republishing a
    decade-old number every 30 s is reported HEALTHY here, correctly and deliberately. The
    age of the number is ``CD-AC-009``'s and :mod:`crash_detector.staleness`'s.
    MEASURED, both directions, in ``tests/test_cadence_breach.py``. **Carried by
    :class:`~crash_detector.staleness.FreshnessEvidence`, which is a different instrument on
    a different input** — and a deployment that runs this one and not that one has a cadence
    monitor and no freshness monitor.

 2  **DETECTION IS NOT NOTIFICATION.** This module computes a verdict. Whether anything
    reaches a human is ``Q26``, and its ruling is: durable ``alert.event`` row first, surfaced
    on the publication surface and a machine-readable state endpoint, **NO EXTERNAL PUSH
    CHANNEL**. **NOT PROVED TO BE CARRIED ANYWHERE** — no channel exists, by ruling, and
    nothing here is measured reaching a person.

 3  **A CHECK THAT DOES NOT RUN DETECTS NOTHING.** "Alerts within one publication cycle" is a
    property of how often the evaluation is invoked, which is the caller's. This module is a
    pure function of its arguments; it schedules nothing and wakes nothing up.
    **NOT PROVED TO BE CARRIED ANYWHERE** in the container set, which is not built
    (``CONTAINER_READY_DESIGN``). What IS carried is that the same halt is visible from
    OUTSIDE the container set by ``tools/probe/external_probe.py``, which needs no process
    inside the system to be running in order to report that nothing is running.

 4  **CLOCK TRUST IS NOT ESTABLISHED**, exactly as :mod:`crash_detector.staleness` boundary 2
    states. ``now_utc`` is an argument so a historical evaluation replays exactly; a caller
    passing a false instant gets a verdict about the world it described.
    **NOT PROVED TO BE CARRIED ANYWHERE.** Pre-existing and project-wide.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence, Tuple

from crash_detector.staleness import STALENESS_WINDOW_CEILING_SECONDS
from crash_detector.time_utc import age_seconds, ensure_utc

__all__ = [
    "CADENCE_THRESHOLD_CEILING_SECONDS",
    "CADENCE_THRESHOLD_CEILING_SOURCE",
    "CadenceBudgetIncoherent",
    "CadenceBudget",
    "CadenceVerdict",
    "evaluate_cadence",
]

#: The HARD UPPER BOUND on a cadence breach threshold. **IMPORTED, NOT RETYPED**, from
#: :mod:`crash_detector.staleness`, because both are derived from the SAME ratified clause —
#: PID §5's 15-minute detectability budget — and two independently written copies of one
#: derived number are two copies that can drift.
CADENCE_THRESHOLD_CEILING_SECONDS: float = STALENESS_WINDOW_CEILING_SECONDS

CADENCE_THRESHOLD_CEILING_SOURCE = (
    "PID.md §5, assurance latency budget, RATIFIED 2026-08-18 (CD-D-003 resolved): "
    "pipeline/publication failure independently detectable <= 15 minutes, and a cadence "
    "breach alerts within one publication cycle. A breach threshold wider than the "
    "detectability budget lets a STOPPED publisher go unreported for longer than the "
    "product permits a failure to go undetected. It is a CEILING and not a setting: the "
    "operating threshold is the deployment's declared publication interval times one plus "
    "the whole number of missed cycles it declares it will tolerate."
)


class CadenceBudgetIncoherent(ValueError):
    """A declared cadence budget cannot mean what it claims.

    A ``ValueError`` to sit beside
    :exc:`~crash_detector.staleness.StalenessWindowOutOfRange`, which refuses the same class
    of thing about a window.
    """


@dataclass(frozen=True)
class CadenceBudget:
    """The declared publication interval and how many missed cycles are tolerated.

    Constructing one IS the admission of the threshold, and it is the only route to one: a
    bare number of seconds cannot be passed to :func:`evaluate_cadence`, so there is no
    second place a threshold can come into existence. That is
    :class:`~crash_detector.staleness.StalenessWindow`'s argument, applied to cadence.

    **REFUSED, each for its own reason:**

    * an interval that is not a plain finite positive number — a subclass of ``float`` may
      redefine comparison, and the comparison is the whole of the verdict;
    * ``missed_cycles_allowed`` that is not a plain ``int``, or is below 1 — at 0 a
      punctual publisher breaches every cycle;
    * a resulting threshold above :data:`CADENCE_THRESHOLD_CEILING_SECONDS` — **REFUSED, not
      clamped.** A clamped threshold is a wrong threshold that looks like a right one: the
      operator believes they configured a 30-minute tolerance, the system applies 15
      minutes, and the two disagree forever with nothing in the record saying so. That is
      :mod:`crash_detector.staleness`'s argument verbatim, and
      :class:`~crash_detector.dials.scores.ScoreOutOfRange`'s before it.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2) — see :class:`~crash_detector.staleness.StalenessWindow`.
    __slots__ = ("publication_interval_seconds", "missed_cycles_allowed")

    publication_interval_seconds: float
    missed_cycles_allowed: int

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            f"{cls.__name__} may not subclass CadenceBudget: a subclass could redefine the "
            "admission that gives a threshold its meaning while remaining acceptable to "
            "every isinstance check downstream. The budget is CLOSED."
        )

    def __post_init__(self) -> None:
        interval = self.publication_interval_seconds
        # EXACT type, not isinstance. bool is an int in Python and a boolean interval is a
        # type error wearing a value; a float subclass may redefine comparison.
        if type(interval) is not float and type(interval) is not int:
            raise CadenceBudgetIncoherent(
                "the publication interval must be a plain int or float number of seconds, "
                f"got {type(interval).__name__}. A subclass of a number is not a number: it "
                "may redefine what comparison means."
            )
        interval = float(interval)
        if not math.isfinite(interval) or interval <= 0.0:
            raise CadenceBudgetIncoherent(
                f"the publication interval must be finite and positive, got {interval!r}. "
                "A publisher with no interval has no cadence to breach."
            )

        missed = self.missed_cycles_allowed
        if type(missed) is not int:
            raise CadenceBudgetIncoherent(
                "missed_cycles_allowed must be a plain int — a WHOLE NUMBER OF PUBLICATION "
                f"CYCLES — got {type(missed).__name__}. It is expressed in cycles rather "
                "than seconds so an operator reads the threshold as 'we alert after N "
                "missed publishes' and is exactly right."
            )
        if missed < 1:
            raise CadenceBudgetIncoherent(
                f"missed_cycles_allowed is {missed} and must be at least 1. At 0 the "
                "threshold equals the publication interval itself, so a PERFECTLY PUNCTUAL "
                "publisher breaches on every single cycle — an alarm that fires on correct "
                "behaviour is an alarm nobody reads, and the first response to it is to "
                "switch the alarm off."
            )

        threshold = interval * (1 + missed)
        if threshold > CADENCE_THRESHOLD_CEILING_SECONDS:
            raise CadenceBudgetIncoherent(
                f"a publication interval of {interval!r} s tolerating {missed} missed "
                f"cycle(s) gives a breach threshold of {threshold!r} s, which exceeds the "
                f"ceiling of {CADENCE_THRESHOLD_CEILING_SECONDS} s and is REFUSED, not "
                f"clamped. {CADENCE_THRESHOLD_CEILING_SOURCE}"
            )

        object.__setattr__(self, "publication_interval_seconds", interval)
        object.__setattr__(self, "missed_cycles_allowed", missed)

    @property
    def breach_threshold_seconds(self) -> float:
        """The interval above which a gap between heartbeats is a breach. Derived, never
        stored, so it cannot be overwritten independently of what it is derived from."""
        return self.publication_interval_seconds * (1 + self.missed_cycles_allowed)


@dataclass(frozen=True)
class CadenceVerdict:
    """What the heartbeat intervals were, and whether any exceeded the budget.

    Carries the measured intervals so a reader of an alert can see WHY it fired, and carries
    no envelope, no dial and no reading, because this verdict is not about data.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2).
    __slots__ = (
        "breached",
        "worst_interval_seconds",
        "open_interval_seconds",
        "closed_intervals_seconds",
        "heartbeat_count",
        "budget",
    )

    breached: bool
    #: The largest interval measured, closed or open. ``None`` only when nothing could be
    #: measured at all.
    worst_interval_seconds: "float | None"
    #: Last heartbeat -> ``now_utc``. **The one that grows without bound when publication
    #: stops**, and therefore the one that detects a halt.
    open_interval_seconds: "float | None"
    #: Between consecutive heartbeats, oldest pair first.
    closed_intervals_seconds: Tuple[float, ...]
    heartbeat_count: int
    budget: CadenceBudget

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(f"{cls.__name__} may not subclass CadenceVerdict.")


def evaluate_cadence(
    heartbeats_utc: Sequence[datetime],
    *,
    now_utc: datetime,
    budget: CadenceBudget,
) -> CadenceVerdict:
    """Was any INTERVAL BETWEEN HEARTBEATS longer than the budget allows?

    ``heartbeats_utc`` are the instants ``publication.heartbeat`` rows were written, in any
    order; they are sorted here so a caller's ``ORDER BY`` cannot change the verdict.

    *** THERE IS NO PARAMETER HERE FOR THE AGE OF A NUMBER, AND THAT IS THE DESIGN. *** No
    reading, no envelope, no ``as_of_utc``, no dial. This function cannot conflate cadence
    with staleness because it is never given the thing it would conflate it with.

    **NO HEARTBEATS AT ALL IS A BREACH, NOT AN UNKNOWN.** A publisher that has never written
    a heartbeat has never published. Returning "no data, cannot say" would be the silent
    failure the whole product exists to avoid — most confidently wrong exactly when the
    system is most broken (``PBG-CI-002``: where a check cannot reach its target it must
    fail, never wave through).
    """
    if type(budget) is not CadenceBudget:
        raise TypeError(
            "cadence must be judged against a CadenceBudget, got "
            f"{type(budget).__name__}. A bare number is not a budget: it has not passed the "
            "admission that gives a threshold its meaning."
        )

    observed = ensure_utc(now_utc)
    instants = sorted(ensure_utc(value) for value in heartbeats_utc)
    threshold = budget.breach_threshold_seconds

    if not instants:
        # Nothing has ever been published. Breached, and the open interval is unmeasurable
        # rather than zero — reporting 0.0 would read as "published just now".
        return CadenceVerdict(
            breached=True,
            worst_interval_seconds=None,
            open_interval_seconds=None,
            closed_intervals_seconds=(),
            heartbeat_count=0,
            budget=budget,
        )

    closed = tuple(
        age_seconds(as_of_utc=earlier, now_utc=later)
        for earlier, later in zip(instants[:-1], instants[1:])
    )

    # *** THE OPEN INTERVAL. Without this line a stopped publisher is never detected. ***
    open_interval = age_seconds(as_of_utc=instants[-1], now_utc=observed)

    measured = closed + (open_interval,)
    worst = max(measured)

    return CadenceVerdict(
        breached=worst > threshold,
        worst_interval_seconds=worst,
        open_interval_seconds=open_interval,
        closed_intervals_seconds=closed,
        heartbeat_count=len(instants),
        budget=budget,
    )
