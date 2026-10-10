"""UTC is the only timestamp (BLUEPRINT §4, Standards Baseline §9).

Every timestamp this application emits, stores, compares or renders is timezone-aware
UTC, ISO-8601 with an explicit ``Z``. Local time exists only in a display layer, and this
project has no display layer.

There is no bare ``now()`` in the dial path: :func:`crash_detector.engine.evaluate` takes
``now_utc`` as a parameter, so that every historical reading is reproducible from its
stored inputs (BLUEPRINT §7).

A naive datetime is **refused**, never assumed to be UTC. Assuming is how cross-boundary
time corruption becomes silent, and silent is the one failure mode this product exists to
prevent.

===========================================================================================
DECLARED LIMIT (CD-RULE-004, CD-RULE-006) — **THE TWO ``isinstance`` TESTS IN THIS MODULE
ARE KEPT, AND THE REASON IS RE-MEASURED AND NOT INHERITED.** WO-2R3 increment 10, ITEM_1,
the F01 exact-type sweep under ``PO-DECISIONS-0018`` ruling 2.
===========================================================================================
``ensure_utc``'s ``isinstance(value, datetime)`` is the site the original finding was about
and it is STILL an ``isinstance``. **THAT IS THE PRODUCT'S CHOICE:** a ``pandas.Timestamp``
IS a ``datetime`` subclass and MUST be readable, and the whole design of this door is that
it admits a SHAPE TO BE READ rather than an object to be consulted. What is returned is
rebuilt by :func:`crash_detector.own_terms.own_instant` from the supplied object's own
C-struct fields, and **nothing after that line calls a method of ``type(value)``.**

``parse_utc``'s ``isinstance(text, str)`` is the same shape one type across. The line
immediately below it is ``candidate = own_str(text)``, and every subsequent operation —
``endswith``, the slice, ``datetime.fromisoformat`` — is on the rebuilt exact ``str``.
MEASURED at ``686a374``: a ``str`` subclass whose ``endswith`` answers ``False`` for every
argument still parses ``'2026-01-01T00:00:00Z'`` to ``2026-01-01 00:00:00+00:00``, identical
to the exact-``str`` control, **because its ``endswith`` is never the one consulted.**

**AND THE ``__class__`` ROUTE IS CARRIED, MEASURED, BY THE C LAYER.** ``isinstance`` also
consults ``__class__``, so an object of an unrelated type WEARING ``datetime`` or ``str``
satisfies these tests where a subclass is not even needed. It does not survive the next
line. MEASURED, with ``class Forged: __class__ = property(lambda s: datetime)``::

    ensure_utc(<forged datetime>)  TypeError: descriptor 'utcoffset' for
                                   'datetime.datetime' objects doesn't apply to a 'Forged'
    parse_utc(<forged str>)        TypeError: descriptor '__str__' requires a 'str' object
                                   but received a 'Forged'

**THE CARRIER IS CPYTHON'S DESCRIPTOR PROTOCOL, NAMED FROM ITS OWN FAILURE TEXT.** See
:mod:`crash_detector.own_terms` DECLARED LIMIT 5, which is the same sentence at the module
that owns the descriptors.
"""

from __future__ import annotations

from datetime import datetime, timezone

from crash_detector.own_terms import own_instant, own_str, own_utc_offset

__all__ = [
    "NaiveTimestampRejected",
    "ensure_utc",
    "parse_utc",
    "format_utc",
    "now_utc",
    "age_seconds",
]

_UTC_DESIGNATOR = "Z"
_ZERO_OFFSET = "+00:00"


class NaiveTimestampRejected(ValueError):
    """A timezone-naive datetime or timestamp string reached a UTC boundary."""


def ensure_utc(value: datetime) -> datetime:
    """Return an exact-type UTC ``datetime`` THIS SYSTEM BUILT from ``value``, or refuse.

    A naive datetime is refused rather than localised by assumption. A datetime carrying
    a non-UTC offset is converted — the instant is unambiguous, so there is nothing to
    guess.

    **IT RE-CONSTRUCTS; IT DOES NOT ADMIT (CD-AC-005, CD-ASR-WO2R-F02).** This function
    used to end ``return value.astimezone(timezone.utc)``, having admitted ``value`` by
    ``isinstance``. Both halves of that were the caller's to define: ``astimezone`` is a
    method, and so is the ``__rsub__`` that ``age_seconds`` would later reach for. A
    ``datetime`` subclass overriding the pair made a row dated 2016 render ``WITNESS
    AGREES`` in 2026 with every constructor on the path having run (variant ASR2-005-A).

    What is returned now is built by :func:`crash_detector.own_terms.own_instant` from the
    seven integers stored in ``value``'s own C struct, read through ``datetime``'s own
    descriptors, and is of exact type ``datetime``. The supplied object is still accepted
    and still believed about its DATA — a ``pandas.Timestamp`` reads correctly and is
    meant to — it is simply no longer consulted about its BEHAVIOUR. Read
    :mod:`crash_detector.own_terms` for the doctrine and for the declared limit.

    This is the ONE door: every constructor in this package that stores a timestamp calls
    it, and :func:`age_seconds` calls it on BOTH of its operands. So no comparison site
    has to remember anything — by the time an age is computed, neither operand is an
    object a caller supplied.
    """
    if not isinstance(value, datetime):
        raise TypeError(f"expected datetime, got {type(value).__name__}")
    offset = own_utc_offset(value)
    if offset is None:
        raise NaiveTimestampRejected(
            "timezone-naive datetime refused; supply an aware UTC datetime"
        )
    return own_instant(value, offset=offset)


def parse_utc(text: str) -> datetime:
    """Parse an ISO-8601 timestamp that carries an explicit UTC designator.

    An offset must be present. A string with no offset is not a UTC timestamp, it is a
    timestamp of unknown origin, and it is refused.
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    # RE-ESTABLISHED BEFORE IT IS PARSED (CD-AC-005, Class 2). `candidate.endswith(...)`
    # decides whether the UTC designator is present and therefore what instant this text
    # denotes, and `endswith` is the supplied object's to define.
    candidate = own_str(text)
    if candidate.endswith(_UTC_DESIGNATOR):
        candidate = candidate[: -len(_UTC_DESIGNATOR)] + _ZERO_OFFSET
    parsed = datetime.fromisoformat(candidate)
    if own_utc_offset(parsed) is None:
        raise NaiveTimestampRejected(
            f"timestamp {text!r} carries no UTC designator; refused"
        )
    # Through the same door as everything else, so there is one place a UTC instant comes
    # into existence in this package rather than two that must be kept in step.
    return ensure_utc(parsed)


def format_utc(value: datetime) -> str:
    """Render a UTC-aware datetime as ISO-8601 with an explicit ``Z``.

    Built on :meth:`datetime.isoformat` rather than ``strftime``, whose behaviour for
    years below 1000 is platform-dependent.
    """
    rendered = ensure_utc(value).isoformat()
    if not rendered.endswith(_ZERO_OFFSET):
        # ensure_utc guarantees the UTC offset, so this cannot be reached by ordinary
        # input. It is raised rather than patched over, because a timestamp that does not
        # render as UTC after being normalised to UTC is a defect, not a formatting case.
        raise ValueError(f"expected a +00:00 offset after normalisation, got {rendered!r}")
    return rendered[: -len(_ZERO_OFFSET)] + _UTC_DESIGNATOR


def now_utc() -> datetime:
    """The current instant, UTC-aware.

    Deliberately NOT called from the dial evaluation core: ``evaluate`` takes ``now_utc``
    as an argument so that it is a pure function of its arguments (BLUEPRINT §7).
    """
    return datetime.now(timezone.utc)


def age_seconds(*, as_of_utc: datetime, now_utc: datetime) -> float:
    """Age of an observation in seconds.

    **Negative if the observation claims to be from the future**, and returned negative
    rather than clamped to zero. A source claiming a future timestamp is a fact the caller
    must decide about, not one to be smoothed away — and clamping it is precisely how a
    future-dated row would become permanently fresh. Callers on the freshness path must
    reject a negative age; see :func:`crash_detector.engine.evaluate.evaluate` and
    :func:`crash_detector.serving.witness_resolver.resolve_panel`.

    **THE SUBTRACTION IS THIS SYSTEM'S OWN (CD-AC-005, CD-ASR-WO2R-F02).** Both operands
    go through :func:`ensure_utc` first, which does not admit them — it REBUILDS them as
    exact-type ``datetime`` values from their own primitive fields. So the ``-`` below is
    CPython's ``datetime.__sub__`` between two objects this package constructed, and an
    ``__rsub__`` defined on a supplied subclass is not bypassed by a guard here: it is
    never reached, because by this line neither operand is that object. The returned
    ``float`` is likewise ``timedelta.total_seconds`` on an exact ``timedelta``, which is
    what lets :meth:`crash_detector.staleness.StalenessWindow.covers` insist on a plain
    ``float`` without that insistence being a burden on any caller.
    """
    return (ensure_utc(now_utc) - ensure_utc(as_of_utc)).total_seconds()
