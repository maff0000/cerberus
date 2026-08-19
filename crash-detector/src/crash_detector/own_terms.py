"""JUDGE VALUES, NEVER TYPES — establishing a supplied value on this system's own terms.

    own_utc_offset(value)  the UTC offset a datetime DECLARES, as a timedelta this module built
    own_instant(value)     an exact-type ``datetime`` this module built from that datetime's
                           own primitive fields, normalised to UTC
    own_float(value)       an exact-type ``float`` this module built from that float's own
                           IEEE-754 double
    own_str(value)         an exact-type ``str`` this module built from that string's own
                           code points

===========================================================================================
THE CLASS THIS MODULE EXISTS TO CLOSE. CD-AC-005, finding CD-ASR-WO2R-F02 (HIGH), variant
ASR2-005-A, and the ``_finite_measure`` sibling the auditor named in the same breath.
===========================================================================================
The class is NOT "datetime subclasses". It is:

    ANY JUDGEMENT THIS SYSTEM MAKES THAT DELEGATES ITS DECIDING OPERATION TO AN OBJECT THE
    SYSTEM DID NOT CONSTRUCT.

The subtraction, the comparison, the equality, the ordering, the truthiness, the hashing,
the formatting — each of those is a METHOD, and a method on a supplied object is that
object's to define. When the answer to "is this observation stale?" is computed by calling
``__rsub__`` on something a collector handed us, the collector decides staleness and this
system only reports what it was told.

:class:`~crash_detector.staleness.StalenessWindow` already knew this and said so in terms:

    "a subclass of a number is not a number: it may redefine what comparison means, and a
     window whose comparisons it controls is not a window at all."

**THE DOCTRINE WAS APPLIED TO ONE OPERAND AND NOT THE OTHER. A COMPARISON HAS TWO.** The
window was admitted on exact type four modules away while the timestamp on the other side
of the very same subtraction was admitted by ``isinstance`` — so ASR2-005-A defines

    class FeedInstant(datetime):
        def __rsub__(self, other):      return timedelta(0)
        def astimezone(self, tz=None):  return self

hands it to the resolver, and a row dated **2016** renders ``WITNESS AGREES`` in 2026 with
a 600-second window. Every constructor on the path ran. Every field of the resulting
``Agrees`` is internally coherent. The only variable is the concrete type of the timestamp.

===========================================================================================
WHY THIS IS RE-CONSTRUCTION AND NOT A BAN, AND WHY THE DIFFERENCE IS THE WHOLE POINT
===========================================================================================
The obvious closure — refuse anything whose ``type`` is not exactly ``datetime`` — is
**not available here and taking it would trade a defect for a defect.** ``pandas.Timestamp``
IS a ``datetime`` subclass. So are ``freezegun``'s, and several time libraries'. A collector
handing the resolver one is not an attack, it is Tuesday. A system that cannot read an
ordinary library timestamp is not a safer system, it is a broken one, and the seat that
shipped it would owe the same disclosure as the seat that shipped the hole.

So the move is not to refuse the object. It is to **stop asking the object anything that
matters**:

  1. READ ITS PRIMITIVES THROUGH THE BASE TYPE'S OWN ACCESSORS. ``datetime.year`` is a
     ``getset_descriptor`` that reads the C struct. ``datetime.year.__get__(value)`` returns
     the ``int`` that is actually stored, and a ``year`` property defined by a subclass never
     runs. ``float.__float__(value)`` returns a new exact ``float`` built from the stored
     IEEE-754 double, and a ``__float__`` defined by a subclass never runs.
  2. BUILD A NEW VALUE OF THE EXACT BASE TYPE FROM THOSE PRIMITIVES, in this module.
  3. LET EVERY SUBSEQUENT JUDGEMENT RUN ON THAT VALUE. The subtraction, the comparison and
     the equality are then CPython's implementations for the exact base type, because both
     operands are objects this system constructed.

The supplied object is still accepted, still read, and still believed about its DATA. It is
simply no longer consulted about its BEHAVIOUR. That is the difference between "we do not
accept your type" and "we do not run your code", and only the second one is compatible with
reading a ``pandas.Timestamp``.

**Measured, not asserted.** ``tests/test_own_terms.py`` is the DECLARED evidence and it
imports nothing outside the standard library, deliberately: ``pandas``, ``numpy`` and
``pytz`` are not declared dependencies of this project (they are absent from
``requirements.txt`` and ``requirements.lock``), and a test that needs an undeclared import
is a test that can skip, which is not evidence. What the declared tests use are stdlib
stand-ins that are *exactly what those library types are* — a ``datetime`` subclass and a
``float`` subclass.

The real libraries WERE measured, as implementation evidence rather than as a declared
test, and the numbers are recorded in the Build Log entry for this increment with their
versions: ``pandas`` 2.1.4 ``Timestamp``, ``numpy`` 1.26.4 ``float64`` and ``pytz`` 2025.2
``Europe/London`` all pass through these functions and resolve to ``Agrees``, with the
stored measurement coming out as an exact ``float``.

===========================================================================================
WHERE THIS MODULE IS THE DOOR
===========================================================================================
Nothing here is a second check bolted beside an existing one. Each function replaces the
DECIDING step of an admission that already existed, at the one place that admission happens:

* :func:`crash_detector.time_utc.ensure_utc` — the ONE door every timestamp in this package
  comes through. Every constructor that stores a timestamp calls it (``PanelRow``, ``OK``,
  ``ObservationRecord``, ``Agrees``, ``Diverges``, ``Unavailable``, ``FreshnessEvidence``,
  ``Value``, ``Degraded``, ``Unknown``, ``AttemptRecord``, ``SourceObservation``), and
  :func:`crash_detector.time_utc.age_seconds` calls it on BOTH of its operands. So the age
  arithmetic is between two objects this system built, at every site, without any site
  having to remember.
* :func:`crash_detector.serving.witness_resolver._finite_measure` and
  :func:`crash_detector.witness.panel._require_finite_float` — the two doors a divergence
  measurement comes through.
* ``PanelRow.__post_init__`` and ``Unavailable.__post_init__`` — the two doors a
  discriminator label comes through, where ``row.state == "AGREES"`` and
  ``reason not in UNAVAILABLE_REASONS`` are decided.

===========================================================================================
DECLARED LIMIT (CD-RULE-004). Each hand-off names a layer that was MEASURED or says NOT
PROVED TO BE CARRIED ANYWHERE (CD-RULE-006).
===========================================================================================
 1  **A ``tzinfo`` THAT LIES ABOUT ITS OFFSET SHIFTS THE INSTANT, AND THE SHIFT IS BOUNDED
    BY THE INTERPRETER TO STRICTLY LESS THAN ONE DAY.** :func:`own_utc_offset` calls
    ``datetime.utcoffset(value)`` — the base implementation, so a subclass override never
    runs — but that implementation asks ``value.tzinfo.utcoffset(value)``, and a ``tzinfo``
    is itself a supplied object. It cannot be refused without refusing ``zoneinfo``,
    ``pytz`` and ``pandas``, all of which supply their own.

    What it CANNOT do is unbounded: CPython's ``call_utcoffset`` refuses any return that is
    not a ``timedelta`` and refuses any magnitude of one day or more, so the worst a lying
    ``tzinfo`` can achieve is to move the instant by up to 24 hours.
    MEASURED — ``tests/test_own_terms.py::test_a_lying_tzinfo_is_bounded_to_under_a_day``:
    a ``tzinfo`` returning ``timedelta(hours=-23)`` moves the computed instant by 23 hours
    and a ``tzinfo`` returning ``timedelta(days=1)`` raises ``ValueError`` from CPython.
    THE CARRIER IS THE CPYTHON INTERPRETER, and it carries the BOUND, not the truth: a row
    up to 24 hours old can be made to look current to a 900-second window by this route.
    Beyond that bound, NOT PROVED TO BE CARRIED ANYWHERE.

    This is the same fact as boundary 2 of :mod:`crash_detector.staleness` — clock trust is
    not established and is not claimed — reached through the offset rather than through
    ``now_utc``. It is a statement about the DATA the caller supplied, which this system
    believes by design, and not about code the caller supplied, which it no longer runs.

 2  **PRECISION FINER THAN A MICROSECOND IS DISCARDED.** ``datetime`` stores microseconds
    and this module rebuilds from ``datetime``'s own fields, so a ``pandas.Timestamp``
    carrying nanoseconds loses them.
    MEASURED — ``tests/test_own_terms.py::test_sub_microsecond_precision_is_dropped_and_never_rounded_up``,
    and with the real library as implementation evidence:
    ``pandas.Timestamp("2026-08-19T12:00:00.123456789Z")`` becomes
    ``2026-08-19 12:00:00.123456+00:00``. It is a TRUNCATION and never a rounding, so a
    reading is never made to look FRESHER than it is by this module. NOT PROVED TO BE
    CARRIED ANYWHERE, and deliberately so: sub-microsecond freshness is not a quantity this
    product has ratified anywhere and inventing a policy for it here would be CD-RULE-003's
    invented product quantity.

 3  **THIS MODULE ESTABLISHES A VALUE; IT DOES NOT ESTABLISH THAT THE VALUE IS TRUE.** A
    collector that reports a fabricated instant, or a fabricated measurement, gets a
    faithful canonicalisation of its fabrication. Source trust is a different problem with a
    different instrument (BLUEPRINT §5, and the ingredient register CD-D-005 owed by the
    Product Owner). NOT PROVED TO BE CARRIED ANYWHERE.

 4  **``object.__setattr__`` STILL WALKS PAST FROZEN**, here as on every frozen value in
    Python and in this repository. A value canonicalised by this module at construction can
    be overwritten with a non-canonical one afterwards by code that has already chosen to
    write past the language's own frozen guarantee. That is boundary 3 of
    :mod:`crash_detector.staleness`, unchanged by this module and not claimed to be closed
    by it. NOT PROVED TO BE CARRIED ANYWHERE.

Do not read this module as a promise that every judgement in this package is made on the
system's own terms. Read it as the door through which timestamps, measurements and
discriminator labels are re-established, and read
``tools/sweep/delegated_judgement_sweep.py`` for the enumeration of what came through it,
what did not, and what remains outside.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

__all__ = [
    "NotEstablishedOnOwnTerms",
    "DATETIME_FIELDS",
    "own_utc_offset",
    "own_instant",
    "own_float",
    "own_str",
]


class NotEstablishedOnOwnTerms(TypeError):
    """A supplied object could not be re-established as a value of this system's own.

    A ``TypeError`` because what is wrong is the *kind of thing* offered, not the quantity
    it carries. Raised rather than coerced, and raised rather than defaulted: a judgement
    this system cannot make on its own terms is a judgement it declines to make (Standards
    Baseline §4 — reject, do not coerce).
    """


#: The complete set of primitive fields a ``datetime`` stores, in constructor order. Written
#: out rather than discovered, because a set derived from ``dir(value)`` would enumerate
#: whatever the supplied object chose to expose.
DATETIME_FIELDS: tuple[str, ...] = (
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "microsecond",
)

#: The base type's own descriptors for those fields, bound once at import. Each is a
#: ``getset_descriptor`` that reads the C struct of the instance, so a ``property`` of the
#: same name defined by a subclass is never consulted. Resolving them here rather than at
#: each call also means the descriptor set cannot be swapped between the check and the read.
_DATETIME_FIELD_DESCRIPTORS: tuple = tuple(
    getattr(datetime, _name) for _name in DATETIME_FIELDS
)

#: The same, for the three primitive fields a ``timedelta`` stores.
_TIMEDELTA_FIELD_DESCRIPTORS: tuple = (
    timedelta.days,
    timedelta.seconds,
    timedelta.microseconds,
)


def own_utc_offset(value: datetime) -> "timedelta | None":
    """The UTC offset ``value`` declares, as a ``timedelta`` this module built.

    ``None`` when the datetime is naive — mirroring ``datetime.utcoffset`` itself, whose
    contract this deliberately matches so the caller's naive-timestamp refusal keeps the
    exception type it already had.

    ``datetime.utcoffset(value)`` is the BASE implementation invoked explicitly, so a
    ``utcoffset`` override defined by a subclass never runs. What it consults is
    ``value.tzinfo``, which is a supplied object and is boundary 1 of this module's declared
    limit; CPython bounds what that object can return to a ``timedelta`` of magnitude
    strictly less than one day.
    """
    if not isinstance(value, datetime):
        raise NotEstablishedOnOwnTerms(
            f"expected datetime, got {type(value).__name__}"
        )
    declared = datetime.utcoffset(value)
    if declared is None:
        return None
    if not isinstance(declared, timedelta):
        # Unreachable through CPython's own ``call_utcoffset``, which already refuses this.
        # Kept as a named refusal rather than an assumption: "the interpreter checks it" is
        # a claim about this interpreter, and this is the freshness path.
        raise NotEstablishedOnOwnTerms(
            f"a tzinfo offered {type(declared).__name__} as a UTC offset; an offset is a "
            "timedelta and nothing else"
        )
    days, seconds, microseconds = (
        descriptor.__get__(declared) for descriptor in _TIMEDELTA_FIELD_DESCRIPTORS
    )
    return timedelta(days=days, seconds=seconds, microseconds=microseconds)


def own_instant(value: datetime, *, offset: timedelta) -> datetime:
    """An exact-type UTC ``datetime`` rebuilt from ``value``'s own primitive fields.

    The returned object is constructed HERE, from seven integers read out of ``value``'s C
    struct through the base type's descriptors, minus an offset built by
    :func:`own_utc_offset`. Nothing defined by ``type(value)`` runs, and the subtraction is
    CPython's ``datetime.__sub__`` between two objects this module built.

    That is what makes the age arithmetic downstream unforgeable: ``age_seconds`` puts both
    of its operands through this function first, so ``__rsub__`` on a supplied subclass is
    never reached — not because the subtraction site guards against it, but because by the
    time the subtraction happens neither operand is a supplied object.
    """
    if not isinstance(value, datetime):
        raise NotEstablishedOnOwnTerms(
            f"expected datetime, got {type(value).__name__}"
        )
    if type(offset) is not timedelta:
        raise NotEstablishedOnOwnTerms(
            f"the UTC offset must be a plain timedelta, got {type(offset).__name__}. A "
            "subclass of a timedelta may redefine what subtraction means, and the "
            "subtraction is the whole of this answer."
        )
    fields = tuple(
        descriptor.__get__(value) for descriptor in _DATETIME_FIELD_DESCRIPTORS
    )
    try:
        # An exact ``datetime``, built here. ``fold`` is deliberately not carried across:
        # it disambiguates a repeated LOCAL wall-clock hour, and the offset above has
        # already resolved which of the two this instant is.
        local = datetime(*fields)
        return (local - offset).replace(tzinfo=timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise NotEstablishedOnOwnTerms(
            f"the instant {fields!r} with offset {offset!r} does not exist as a UTC "
            f"datetime: {exc}. It is refused rather than clamped to the nearest "
            "representable instant, because a clamped instant is a wrong instant that "
            "looks like a right one."
        ) from None


def own_float(value: float) -> float:
    """An exact-type ``float`` built from ``value``'s own stored IEEE-754 double.

    ``float.__float__`` is the BASE implementation invoked explicitly. For an exact ``float``
    it returns the object itself; for a subclass it reads the ``ob_fval`` field of the C
    struct and returns a NEW exact ``float``. A ``__float__`` defined by the subclass never
    runs, and neither does its ``__lt__``, ``__eq__``, ``__bool__`` or ``__format__``,
    because what leaves this function is not that object.

    This is the SAME doctrine :class:`~crash_detector.staleness.StalenessWindow` applies to a
    window and a DIFFERENT remedy, and the difference is argued rather than left to be
    noticed. A window is a CONFIGURED quantity: refusing a ``numpy.float64`` there costs a
    deployment one ``float()`` call in its own configuration code and closes the route
    outright, so ``StalenessWindow`` refuses on exact type and is not relaxed by this module.
    A measurement is SUPPLIED data arriving from a collector, where ``numpy.float64`` — which
    IS a ``float`` subclass — is ordinary, so the same refusal would make ordinary numeric
    libraries unusable on the one path that actually reads external data. Both establish the
    value on this system's own terms. Only one of them can afford to do it by refusal.

    ``bool`` is refused ahead of everything, as it is at every other numeric door in this
    package: ``isinstance(True, int)`` is true in Python and a boolean measurement is a type
    error wearing a value.
    """
    if isinstance(value, bool):
        raise NotEstablishedOnOwnTerms(
            "a bool was offered as a measurement; True is not 1.0 and False is not 0.0, "
            "and a False that became a zero divergence measure would read as perfect "
            "agreement manufactured from a type error"
        )
    if not isinstance(value, float):
        raise NotEstablishedOnOwnTerms(
            f"expected float, got {type(value).__name__}. It is refused rather than "
            "coerced: float('0.0') and float(0) both succeed and both would produce a "
            "measurement of zero (Standards Baseline §4)."
        )
    return float.__float__(value)


def own_str(value: str) -> str:
    """An exact-type ``str`` built from ``value``'s own code points.

    ``str.__str__`` is the BASE implementation invoked explicitly. For an exact ``str`` it
    returns the object itself; for a subclass it copies the underlying code points into a
    NEW exact ``str``. A ``__str__``, ``__eq__`` or ``__hash__`` defined by the subclass
    never runs.

    That matters because this package decides two things by comparing labels —
    ``row.state == "AGREES"`` selects the panel constructor, and
    ``reason not in UNAVAILABLE_REASONS`` admits an unavailability reason — and both of
    those operators are the LEFT operand's to define. A ``str`` subclass whose ``__eq__``
    answers ``True`` for ``"AGREES"`` makes a row that says ``UNAVAILABLE`` render as
    agreement, which is CD-AC-005's exact forbidden sentence reached without any timestamp
    being involved at all.
    """
    if not isinstance(value, str):
        raise NotEstablishedOnOwnTerms(
            f"expected str, got {type(value).__name__}"
        )
    return str.__str__(value)
