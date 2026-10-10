"""The observation record and its fetch outcome — the collector/engine contract.

BLUEPRINT §5. **Every fetch attempt produces a record, including the failures**, and the
outcome of a fetch is a sum type with four constructors:

    outcome := OK(payload, source_as_of_utc)
             | FetchFailed(error_class, http_status?)   # we could not ask
             | Malformed(schema_error_class)            # we asked, the answer did not conform
             | Empty(source_as_of_utc?)                 # we asked, the source has nothing

A failed fetch that records nothing is indistinguishable from a fetch that was never
scheduled, and both are indistinguishable from a source that had nothing to report —
three states that demand different responses, collapsed into one absence. Standards
Baseline §8: *cannot determine* is not *determined to be absent*.

The engine reads outcomes, not values, and **the only outcome that can produce a dial
contribution is** :class:`OK`. The other three produce ``Unknown`` or ``Degraded`` — never
zero, never the previous value, never a default (BLUEPRINT §7).

----

SCOPE NOTE, disclosed rather than quietly taken (WO-2, increment 1 of 7).

This module exists in increment 1 because deliverable A2's own signature —
``evaluate(observations, config_snapshot, now_utc)`` — cannot be typed without it, and
because "only ``OK`` contributes" is an A2 property that has to be testable now. It is
therefore the minimum of the observation contract, and no more:

  * DELIVERED HERE: the four-constructor outcome sum type, and the observation record.
  * NOT DELIVERED HERE, and owed to deliverable A4: the adapter protocol, boundary schema
    validation, the collector runner and its bounded timeouts and retries, idempotency on
    ``(source_id, source_as_of_utc)``, the source registry with its
    ``REQUIRED | CONTRIBUTING | DISPOSABLE`` criticality, the persistence path that makes
    "every attempt writes a row" true of the store rather than only of the type, and the
    in-memory fake adapter used by tests.

It lives at the package root rather than under ``collectors/`` on purpose. It is the
*contract between* the collector layer and the engine, not a component of either, and
putting it under ``collectors/`` would make :mod:`crash_detector.engine` import the
collector package — an import-graph edge that CD-AC-003's checks should not have to
reason about.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Union

from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from crash_detector.time_utc import ensure_utc
from crash_detector.establishment import establishes, one_of

__all__ = [
    "OK",
    "FetchFailed",
    "Malformed",
    "Empty",
    "FetchOutcome",
    "ObservationRecord",
    "OUTCOME_CLASSES",
    "MAX_INSTANCE_PATH_LENGTH",
    "outcome_class",
]

#: Ceiling on :attr:`Malformed.instance_path`. Declared HERE, on the type that stores it,
#: so the producer in :mod:`crash_detector.collectors.validation` imports the same number
#: the constructor enforces. Two constants that must agree is one constant with a bug
#: scheduled for whenever somebody edits the wrong copy.
MAX_INSTANCE_PATH_LENGTH = 200


@establishes(
    payload=dict,
    source_as_of_utc=datetime,
)
@dataclass(frozen=True)
class OK:
    """We asked, the source answered, and the answer conformed to its declared schema.

    The only outcome that can produce a dial contribution.

    ``payload`` is the validated response. ``source_as_of_utc`` is the instant the SOURCE
    says its data is for — not the instant we fetched it. Freshness is a property of the
    data, not of our diligence in asking for it.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `OK.__new__(OK)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("payload", "source_as_of_utc")

    payload: Mapping[str, object]
    source_as_of_utc: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))
        object.__setattr__(self, "source_as_of_utc", ensure_utc(self.source_as_of_utc))


@establishes(
    error_class=str,
    http_status=one_of(int, None),
)
@dataclass(frozen=True, slots=True)
class FetchFailed:
    """We could not ask. Network, timeout, transport, refusal, non-2xx.

    Carries no payload and no ``source_as_of_utc``, because there is no observation here
    — only a record that we tried.
    """

    error_class: str
    http_status: Union[int, None] = None

    def __post_init__(self) -> None:
        if not self.error_class:
            raise ValueError("FetchFailed requires a stated error_class")
        status = self.http_status
        # EXACT TYPE ON THE `int` LIMB (WO-2R3 increment 10, ITEM_1, the F01 sweep).
        # `isinstance(status, int)` admitted an int SUBCLASS here, and the register recorded
        # the residue as **NOT PROVED TO BE CARRIED ANYWHERE**. RE-MEASURED at `686a374`, and
        # the record was wrong in the GOOD direction — it IS carried:
        # `FetchFailed(error_class="x", http_status=EvilInt(404))` raises
        # `FieldNotEstablished: FetchFailed.http_status=EvilInt is not admitted`, from this
        # type's own `@establishes(http_status=one_of(int, None))`, which runs AFTER
        # `__post_init__`. The refusal is moved to the FIRST gate anyway, so a wrong type is
        # refused where it is named rather than one layer downstream by a check aimed at
        # something else — the "wrong reason again" this project has been caught by.
        #
        # The `bool` limb stays `isinstance` DELIBERATELY: it is a REFUSAL predicate, where
        # `isinstance` is the STRICTER of the two operators. `bool` cannot be subclassed
        # (MEASURED: `class B(bool)` -> `TypeError: type 'bool' is not an acceptable base
        # type`), but `isinstance` also consults `__class__`, so an object WEARING `bool`
        # is refused here and would be admitted by `type(status) is bool`. Narrowing a
        # refusal predicate to exact type is a WEAKENING and it is not taken.
        if status is not None and (isinstance(status, bool) or type(status) is not int):
            raise TypeError(
                "FetchFailed.http_status must be an int or absent, got "
                f"{type(status).__name__}. Exact type and never isinstance: an int subclass "
                "may redefine every comparison this status is later read by."
            )

#: SEALED (PO-DECISIONS-0016 ruling 2). This type carries a FIELD DEFAULT, and a
#: manual __slots__ beside a class-level default is a ValueError at class creation
#: ('conflicts with class variable'), so the slots come from @dataclass(slots=True).
#: THAT DECORATOR ALSO INSTALLS dataclasses._dataclass_setstate — A STDLIB FUNCTION
#: THAT WRITES EVERY KEY IT IS GIVEN THROUGH object.__setattr__ WITH NO VALIDATION
#: AND NO PACKAGE CODE — which re-opens by the __setstate__ sibling exactly the route
#: the slots closed. MEASURED, not reasoned: without this removal,
#: `FetchFailed.__new__(FetchFailed).__setstate__({...})` returns an object of exactly
#: this type carrying forged field values. It is removed rather than overridden
#: because @dataclass(slots=True) installs it AFTER the class body has been read.
#: The cost is measured and declared: this type is no longer picklable or
#: deep-copyable, which is the state every already-sealed governed type (Value,
#: Degraded, Unknown, Shown, NotShown, DialMagnitude) has always been in.
del FetchFailed.__setstate__


@establishes(
    schema_error_class=str,
    instance_path=str,
)
@dataclass(frozen=True, slots=True)
class Malformed:
    """We asked, and the answer did not conform to the schema the adapter declares.

    Stored with its error class and **never coerced** (Standards Baseline §4). External
    input is hostile, including from a source that has been reliable for a year.

    ``instance_path`` is an RFC 6901 JSON Pointer naming WHERE the response failed —
    property names and array indices only. It is built by
    :mod:`crash_detector.collectors.validation`, which is also where the reasoning lives
    for why nothing value-bearing may travel on this type: ``jsonschema``'s own messages
    embed the offending instance value, and a hostile response's values may include a
    secret the source echoed back (``PBG-SEC-002``, non-waivable).

    The empty string is the pointer to the document ROOT, exactly as RFC 6901 defines it
    — "the whole response was the wrong shape". It is a real location, not a placeholder
    for "we do not know", which is why this field can carry it as a default without
    becoming one of those sometimes-present fields where a reader learns to guess.

    (Field added in WO-2 increment 2 for deliverable A4 — extending increment 1's type in
    place, as CD-D-008 permits, rather than duplicating the sum type under ``collectors/``.)
    """

    schema_error_class: str
    instance_path: str = ""

    def __post_init__(self) -> None:
        if not self.schema_error_class:
            raise ValueError("Malformed requires a stated schema_error_class")
        # EXACT TYPE (WO-2R3 increment 10, ITEM_1, the F01 sweep). The register recorded
        # this site as `OUT_OF_BOUND` with **NOT PROVED TO BE CARRIED ANYWHERE**.
        # RE-MEASURED at `686a374`: it IS carried — `Malformed(schema_error_class="x",
        # instance_path=EvilStr("bad"))` raises `FieldNotEstablished:
        # Malformed.instance_path=EvilStr is not admitted`, from this type's own
        # `@establishes(instance_path=str)`. **BUT THE CARRIER FIRES ONE LAYER TOO LATE:**
        # `@establishes` runs after `__post_init__`, so the subclass's own `startswith` and
        # `__len__` answered the RFC 6901 shape check and the length ceiling first. Exact
        # type here refuses it BEFORE either is asked, which is the point of the door.
        if type(self.instance_path) is not str:
            raise TypeError(
                "Malformed.instance_path must be a str, got "
                f"{type(self.instance_path).__name__}. Exact type and never isinstance: the "
                "two checks below are `startswith` and `len`, and both are the supplied "
                "object's to define."
            )
        if self.instance_path and not self.instance_path.startswith("/"):
            raise ValueError(
                "Malformed.instance_path must be an RFC 6901 JSON Pointer: the empty "
                "string for the document root, or a '/'-prefixed path. Got "
                f"{self.instance_path!r}"
            )
        if len(self.instance_path) > MAX_INSTANCE_PATH_LENGTH:
            raise ValueError(
                "Malformed.instance_path exceeds "
                f"{MAX_INSTANCE_PATH_LENGTH} characters. It is built from external "
                "property names, and unbounded external input on a path to an "
                "append-only store is an unbounded row."
            )

#: SEALED (PO-DECISIONS-0016 ruling 2). This type carries a FIELD DEFAULT, and a
#: manual __slots__ beside a class-level default is a ValueError at class creation
#: ('conflicts with class variable'), so the slots come from @dataclass(slots=True).
#: THAT DECORATOR ALSO INSTALLS dataclasses._dataclass_setstate — A STDLIB FUNCTION
#: THAT WRITES EVERY KEY IT IS GIVEN THROUGH object.__setattr__ WITH NO VALIDATION
#: AND NO PACKAGE CODE — which re-opens by the __setstate__ sibling exactly the route
#: the slots closed. MEASURED, not reasoned: without this removal,
#: `Malformed.__new__(Malformed).__setstate__({...})` returns an object of exactly
#: this type carrying forged field values. It is removed rather than overridden
#: because @dataclass(slots=True) installs it AFTER the class body has been read.
#: The cost is measured and declared: this type is no longer picklable or
#: deep-copyable, which is the state every already-sealed governed type (Value,
#: Degraded, Unknown, Shown, NotShown, DialMagnitude) has always been in.
del Malformed.__setstate__


@establishes()
@dataclass(frozen=True)
class Empty:
    """We asked, the source conformed, and it has nothing to report for the period.

    Distinct from :class:`FetchFailed`: this is *determined to be absent*, which is a
    different fact from *cannot determine*, and it is not a value either.

    Nullary on purpose. It carries no ``source_as_of_utc``, because there is no
    observation to be as-of; the attempt's own time is on the
    :class:`ObservationRecord`. An optional timestamp here would be a field that is
    sometimes present, and "sometimes present" is where a reader learns to guess.

    **``@establishes()`` WITH NO DECLARATIONS, AND THAT IS THE POINT AND NOT AN OVERSIGHT.**
    :func:`~crash_detector.establishment.establishes`'s own docstring prescribes exactly
    this — *"``@establishes()`` with no declarations is a meaningful and deliberate
    statement, not a no-op: it says this type declares no fields and I was told about none,
    and adding one later refuses every construction"* — and until WO-2R3 increment 6 it had
    not been applied here.

    **WHY IT WAS OWED.** `Empty` is the ONE member PO-DECISIONS-0010 ruling 1 added to the
    constructor check's population, and the ruling's phrase for a fielded public frozen
    judgement-path type with no establishment is **"FAILS ON ARRIVAL"** — which in this
    module's vocabulary means RAISES ON EVERY CONSTRUCTION. `CD-ASR-WO2R3-01`'s F-A1
    measured that for `Empty` it was **A STATIC CHECK LINE ONLY**: adding a field made the
    instrument exit 1 with a VIOLATION — that claim was true — while at runtime
    `Empty(confidence=object())` was ***ACCEPTED*** and `is_establishing_type(Empty)`
    answered `False`. **NOTHING REFUSED IT.**

    **WHAT THIS DOES NOT DO, AND IT MATTERS MORE HERE THAN ON ANY OTHER MEMBER BECAUSE THIS
    TYPE IS NULLARY BY DESIGN.** It does not make the type fielded, does not let it accept a
    field, and moves no construction that succeeds today: `Empty()` is unchanged, and
    `Empty(confidence=...)` is still a plain `TypeError` from the generated `__init__`
    because no such parameter exists. What changes is the day someone ADDS a field — from
    that moment every construction, including the ones that work now, raises
    :exc:`~crash_detector.establishment.UndeclaredField`. Measured at both SHAs by
    ``variants/WO-2R3/P-D-empty-is-runtime-unguarded.py``.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `Empty.__new__(Empty)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ()


#: The fetch outcome sum type. Closed: an unrecognised member is a defect, not a case to
#: be defaulted. There is deliberately no common base class — a base class is somewhere a
#: ``.value`` or ``.payload`` accessor could later be added that all four constructors
#: would inherit, which is exactly the route from a failure to a number that this type
#: exists to close.
FetchOutcome = Union[OK, FetchFailed, Malformed, Empty]

#: The persisted discriminator values for ``raw.observation.outcome``.
OUTCOME_CLASSES: tuple[str, ...] = ("OK", "FETCH_FAILED", "MALFORMED", "EMPTY")

_CLASS_BY_TYPE = {
    OK: "OK",
    FetchFailed: "FETCH_FAILED",
    Malformed: "MALFORMED",
    Empty: "EMPTY",
}


def outcome_class(outcome: "FetchOutcome") -> str:
    """The persisted discriminator for an outcome value.

    An unrecognised member raises. It is not defaulted, and in particular it is never
    defaulted to ``OK``.
    """
    try:
        return _CLASS_BY_TYPE[type(outcome)]
    except KeyError:
        raise TypeError(
            f"not a FetchOutcome: {type(outcome).__name__}. The sum type is closed; "
            "there is no fall-through, least of all to OK."
        ) from None


@establishes(
    source_id=str,
    observed_utc=datetime,
    outcome=one_of(OK, FetchFailed, Malformed, Empty),
)
@dataclass(frozen=True)
class ObservationRecord:
    """One row of ``raw.observation`` — one fetch attempt, whatever came of it.

    ``observed_utc`` is when WE performed the attempt; the source's own timestamp, where
    one exists, lives on the outcome. Keeping the two apart is what stops "we asked
    recently" from being mistaken for "the data is recent".
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `ObservationRecord.__new__(ObservationRecord)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("source_id", "observed_utc", "outcome")

    source_id: str
    observed_utc: datetime
    outcome: "FetchOutcome"

    def __post_init__(self) -> None:
        # RE-ESTABLISHED BEFORE IT IS USED AS A KEY (CD-AC-005, Class 2). `source_id` had no
        # type check at all, so `not self.source_id` was decided by the supplied object's
        # own __bool__/__len__; and the engine uses this value as a dict key and tests
        # `source_id in usable`, both of which are decided by its __hash__ and __eq__. A
        # `str` subclass could therefore answer to a source id it is not.
        try:
            object.__setattr__(self, "source_id", own_str(self.source_id))
        except NotEstablishedOnOwnTerms as refusal:
            raise TypeError(
                f"ObservationRecord.source_id must be a str: {refusal}"
            ) from None
        if not self.source_id:
            raise ValueError("ObservationRecord requires a source_id")
        object.__setattr__(self, "observed_utc", ensure_utc(self.observed_utc))
        # Validates membership of the closed sum type, and raises if it is not a member.
        outcome_class(self.outcome)
