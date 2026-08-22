"""WAITING IS A NAMED KIND, NOT A CALLABLE (BP-AMENDMENT-0001 §D.3 part 1, in force).

    apply_delay(DelayKind.WALL_CLOCK, seconds)     # the caller NAMES; this module ACTS

===========================================================================================
THE PRECEDENT, AND IT IS THIS CODEBASE'S OWN STRONGEST EXISTING CLOSURE
===========================================================================================

Until WO-2R increment 1, ``combine_within_one_dial(magnitudes, using)`` took ``using`` as a
CALLABLE. It received a tuple of released floats, returned one, and that return went
straight into the derivation door — which made it the public proxy through which
``ASR2-002-A`` published an equity 0.5 out of an equity 0.9 and a monetary 0.1 with every
static layer green.

**The repair was not a stronger check on the callable. It was DELETING the callable
argument** and replacing it with a NAME from a closed set, executed by the module that owns
the numbers.

``collect(sleep=...)`` was the same shape one component across: a caller-supplied
``Callable[[float], None]``, admitted by ``callable(sleep)``, which establishes that the
object can be CALLED and nothing whatever about what happens when it is. The bound the
:class:`~crash_detector.collectors.runner.RetryPolicy` states — *at most this many attempts,
at most this long between them* — was therefore enforced by code the caller wrote. A
``sleep`` that returns immediately makes ``backoff_seconds`` a number in a record and
nothing in the world; a ``sleep`` that blocks makes the policy's ``worst_case_seconds`` a
fiction in the other direction. Neither is a check this module could add to the callable:
the defect is that there is a parameter through which code arrives at all.

So the parameter is DELETED and replaced by :class:`DelayKind`. A caller names a kind of
waiting; THIS module decides what that kind means and performs it. There is no expression a
caller can write that puts code on the retry path.

===========================================================================================
ONE MEMBER, AND WHY THAT IS THE HONEST NUMBER
===========================================================================================

:class:`DelayKind` ships with exactly one member, :data:`DelayKind.WALL_CLOCK`, because
there is exactly one kind of waiting this product has ever needed: wait the configured
backoff, on the wall clock, before the next attempt.

**A ``NONE``/``NO_DELAY`` member was considered and deliberately NOT added**, and the reason
is recorded rather than left to be guessed at: it would exist only to let the test suite run
without waiting, and a member that exists for the tests is an option a production caller can
also choose — a way to set ``backoff_seconds`` to a real number and then not honour it,
selected from outside the module that owns the policy. The tests instead configure a real,
tiny backoff and really wait for it (a fraction of a millisecond), which measures the delay
that ships rather than a substitute for it.

A second member is therefore a deliberate future act with a reason, not a convenience.

**THE MEMBER SET IS CLOSED BY THE INTERPRETER AND NOT BY A CONVENTION.** ``Enum`` refuses to
be subclassed once it has members — ``class Sneaky(DelayKind): EXTRA = "x"`` raises
``TypeError: <enum 'DelayKind'> cannot be extended`` at class-creation time, before any
instance exists. And :func:`apply_delay` is decorated ``@admits(kind=DelayKind, ...)``, so a
look-alike object carrying ``.name``/``.value`` is refused by exact type at the door. Both
halves are measured in ``tests/test_collector_delay.py``.

===========================================================================================
WHY THE ELAPSED MEASUREMENT LIVES HERE TOO
===========================================================================================

The runner's timeout-budget refusal — *a response that arrived after its budget is recorded
as a failure even when the payload is perfect* — is a JUDGEMENT the collector makes about an
adapter. Until this module existed it was computed by subtracting two values obtained from
``clock()``, **a callable the caller supplied**: a clock that never advances makes every
adapter punctual, and the one guarantee the runner offers about an adapter that ignores its
budget evaporates without a single line of the runner changing.

:func:`monotonic_reading` and :func:`seconds_since` are that measurement, owned here. They
read ``time.monotonic``, which is monotonic non-decreasing by definition, so an elapsed span
computed from them cannot be negative and cannot be influenced from outside this process.
There is no parameter through which a caller supplies either.

**WHAT THIS DOES NOT ESTABLISH, SAID HERE RATHER THAN FOUND LATER:** a caller still supplies
the run's starting INSTANT to ``collect`` (``started_utc``), because a collection run's
nominal instant is data about the run and not a behaviour. Its TYPE is established at the
door and it is rebuilt by ``ensure_utc`` from its own primitive fields, so no method of the
supplied object is ever consulted; its TRUTH is not established, and nothing here claims it
is. A caller that passes an instant from last year gets attempt rows dated last year. That
residue is carried in ``collect``'s own DECLARED LIMIT block.
"""

from __future__ import annotations

import enum
import math
import time

from crash_detector.admission import admits

__all__ = [
    "DelayKind",
    "UnknownDelayKind",
    "DelayRefused",
    "MAX_DELAY_SECONDS_CEILING",
    "apply_delay",
    "monotonic_reading",
    "seconds_since",
]

#: The hard ceiling on any single wait this module will perform. A delay nobody bounded is
#: an outage generator (Standards Baseline §11), and this function is public: bounding it
#: only where ``RetryPolicy`` happens to call it would leave the bound somewhere else's
#: property. ``RetryPolicy.MAX_BACKOFF_SECONDS_CEILING`` is THIS constant, imported, so the
#: two cannot drift apart into a pair of numbers that disagree.
MAX_DELAY_SECONDS_CEILING = 30.0


class UnknownDelayKind(Exception):
    """A :class:`DelayKind` member reached :func:`apply_delay` with no branch to execute it.

    Named, and raised rather than fallen through. The parallel is
    :exc:`~crash_detector.engine.mapping.UnspecifiedMapping`: a member with no executor is a
    defect in this module, and the honest answer is to say so loudly rather than to wait for
    an unspecified duration or for none.
    """


class DelayRefused(ValueError):
    """The requested wait is not a duration this module will perform.

    Negative, non-finite, or beyond :data:`MAX_DELAY_SECONDS_CEILING`. An infinite backoff
    is not a lenient backoff; it is a hang.
    """


class DelayKind(enum.Enum):
    """The closed set of ways this system waits between attempts.

    A NAME, resolved and executed by this module. Not a callable, not a strategy object, and
    not a duration — the duration is a separate, bounded argument, so a kind cannot smuggle
    one.
    """

    #: Wait on the wall clock for the configured number of seconds, then continue. The only
    #: kind of waiting WO-2 performs. See the module docstring for why there is no second
    #: member and what adding one would mean.
    WALL_CLOCK = "WALL_CLOCK"


@admits(kind=DelayKind, seconds=float)
def apply_delay(kind: DelayKind, seconds: float) -> float:
    """Perform one bounded wait of the named kind. Returns the seconds waited.

    The return value is what the RUNNER records as having happened, so a caller reads the
    delays a collection actually performed off
    :class:`~crash_detector.collectors.runner.CollectionResult` rather than off a test
    double's bookkeeping.

    :raises DelayRefused: the duration is negative, non-finite or above the ceiling.
    :raises UnknownDelayKind: the member has no executor branch here. There is no ``else``
        and no fallthrough: this function either performs a wait it recognises or it raises.
    """
    if isinstance(seconds, bool) or not math.isfinite(seconds):
        raise DelayRefused(f"a delay of {seconds!r} is not a duration")
    if seconds < 0.0 or seconds > MAX_DELAY_SECONDS_CEILING:
        raise DelayRefused(
            f"a delay must lie in [0.0, {MAX_DELAY_SECONDS_CEILING}], got {seconds!r}"
        )
    if kind is DelayKind.WALL_CLOCK:
        if seconds > 0.0:
            time.sleep(seconds)
        return seconds
    raise UnknownDelayKind(
        f"{kind!r} has no executor in this module. A delay kind that reaches this line is a "
        "defect here, and it is raised rather than silently treated as no wait at all."
    )


@admits()
def monotonic_reading() -> float:
    """A reading of this process's monotonic clock. Engine-owned; nothing supplies it.

    ``time.monotonic`` cannot go backwards and is unaffected by system clock adjustments, so
    a span computed from two readings is a fact about how long something took rather than a
    fact about what a clock object chose to say.
    """
    return time.monotonic()


@admits(reading=float)
def seconds_since(reading: float) -> float:
    """How long, in seconds, since :func:`monotonic_reading` produced ``reading``.

    Never negative: the underlying clock is monotonic non-decreasing. That is why an attempt
    row derived from it can never claim to have finished before it started.
    """
    return time.monotonic() - reading
