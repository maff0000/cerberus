"""The source registry — data, not code (BLUEPRINT §5).

``raw.source_registry`` names each source, its adapter, its cadence, and its
**criticality**, and the criticality is a statement about the ENGINE's behaviour:

===============  ===========================================  ===========================
Criticality      Meaning                                      Engine consequence
===============  ===========================================  ===========================
``REQUIRED``     the dial cannot be computed honestly          its absence forces
                 without it                                    ``Unknown``
``CONTRIBUTING`` improves the reading                          its absence forces
                                                                ``Degraded``
``DISPOSABLE``   useful, never load-bearing                    its absence changes
                                                                nothing
===============  ===========================================  ===========================

**WO-2 REGISTERS ZERO SOURCES, and that is the deliverable, not a gap.** CD-D-005 — which
inputs feed each dial and what each stands for — is the Product Owner's decision and is
owed before WO-3 (BLUEPRINT §16, ``governance/decisions/PO-ACCEPT-BLUEPRINT-0001.md``).
Choosing ingredients is choosing what a dial *means*, and PID doctrine §3.6 forbids
unexplained mappings. With no sources registered every dial correctly reads ``Unknown`` —
the doctrinally right empty state, and the thing that makes CD-AC-001's first plant
demonstrable. See :data:`EMPTY_SOURCE_REGISTRY`.

----

WHY THIS MODULE IS AT THE PACKAGE ROOT AND NOT UNDER ``collectors/``.

The same reason :mod:`crash_detector.observations` is (CD-D-008, ruled KEEP by the Project
Lead). The registry is the *contract between* the collector layer and the engine, not a
component of either: :class:`~crash_detector.engine.config.ConfigSnapshot` must carry it,
because which sources exist and how critical each one is are configuration that affects a
result (Standards Baseline §10). Putting it under ``collectors/`` would make
:mod:`crash_detector.engine` import the collector package and invert the §5/§7 boundary,
which is precisely the import-graph edge CD-AC-003's checks should not have to reason
about.

----

THE CRITICALITY CONTRACT, AND WHY IT IS TOTAL RATHER THAN A SINGLE PROHIBITION.

The dispatch requires, at the type and config level, that a ``DISPOSABLE`` source can
**never** be named in a dial's required-input set. That rule is enforced here by
:exc:`DisposableSourceIsLoadBearing`, and the equivalent database constraint is owed to
deliverable A5.

The rule implemented here is deliberately the whole table above rather than that one row,
because the table is a *total function* from criticality to engine consequence, and any
disagreement between a source's declared criticality and the set it is named in is an
incoherent configuration:

  * a ``REQUIRED`` source in ``contributing_input_ids`` would have its absence produce
    ``Degraded`` when the registry says it must produce ``Unknown``;
  * a ``CONTRIBUTING`` source in ``required_input_ids`` would have its absence produce
    ``Unknown`` when the registry says ``Degraded``;
  * a ``DISPOSABLE`` source in either set would have its absence change something when the
    registry says it changes nothing.

Refusing all three is enforcing the Blueprint's own declared table, not inventing product
meaning: the *content* of the registry — which sources, at what criticality — remains
entirely the Product Owner's, and this module registers none of it.
"""

from __future__ import annotations

from dataclasses import dataclass

from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from enum import Enum
from typing import Iterable

__all__ = [
    "Criticality",
    "CRITICALITY_NAMES",
    "SourceRecord",
    "SourceRegistry",
    "EMPTY_SOURCE_REGISTRY",
    "SourceNotRegistered",
    "CriticalityContractViolated",
    "DisposableSourceIsLoadBearing",
]


class Criticality(Enum):
    """How much of a dial's honesty depends on a source.

    Three members. A fourth is a Blueprint amendment, not an edit here, because each
    member carries a declared engine consequence and a member without one would be a
    criticality nobody can act on.
    """

    REQUIRED = "REQUIRED"
    CONTRIBUTING = "CONTRIBUTING"
    DISPOSABLE = "DISPOSABLE"


#: The persisted discriminator values for ``raw.source_registry.criticality``. Deliverable
#: A5's ``CHECK`` constraint must admit exactly these and nothing else.
CRITICALITY_NAMES: tuple[str, ...] = tuple(member.value for member in Criticality)


class SourceNotRegistered(LookupError):
    """A source was named that the registry does not carry.

    Raised rather than answered with a default record. A configuration naming a source
    nobody registered is a configuration whose criticality contract cannot be checked, and
    an unregistered source is the cheapest way to make the ``DISPOSABLE`` prohibition
    vacuous — you simply do not register the source you are about to make load-bearing.
    """


class CriticalityContractViolated(ValueError):
    """A source was named in a set that contradicts its declared criticality.

    The base class exists so a guard can catch the CLASS of violation rather than the one
    member somebody planted.
    """


class DisposableSourceIsLoadBearing(CriticalityContractViolated):
    """A ``DISPOSABLE`` source was named in a dial's input set.

    Refused here in code, and refused again by a database constraint (deliverable A5).
    Two independent refusals, because "useful, never load-bearing" is exactly the property
    that decays quietly under six months of edits (BLUEPRINT §5; PID §7 names Quantical's
    undocumented ``price_history`` endpoint as the case in point).
    """


@dataclass(frozen=True)
class SourceRecord:
    """One registered ingredient source — one row of ``raw.source_registry``."""

    source_id: str
    adapter_id: str
    cadence_seconds: int
    criticality: Criticality
    stands_for: str

    def __post_init__(self) -> None:
        # RE-ESTABLISHED BEFORE ANY OF THEM IS COMPARED OR HASHED (CD-AC-005, Class 2).
        # `source_id` is put in a set to detect duplicates, is looked up by
        # `SourceRegistry.get`, and is what `source_id in usable` in the engine tests to
        # decide whether a required input was present — which decides whether a dial is a
        # number at all. All of those are the supplied string's `__eq__`/`__hash__` to
        # answer, and `isinstance(observed, str)` admitted a subclass that could answer them.
        for name in ("source_id", "adapter_id", "stands_for"):
            try:
                object.__setattr__(self, name, own_str(getattr(self, name)))
            except NotEstablishedOnOwnTerms:
                raise ValueError(
                    f"SourceRecord requires a non-empty {name}"
                ) from None
            if not getattr(self, name):
                raise ValueError(f"SourceRecord requires a non-empty {name}")
        if not isinstance(self.criticality, Criticality):
            raise TypeError(
                "SourceRecord.criticality must be a Criticality member, got "
                f"{type(self.criticality).__name__}. A string is not a criticality: it "
                "is a criticality that has not been checked."
            )
        if isinstance(self.cadence_seconds, bool) or not isinstance(
            self.cadence_seconds, int
        ):
            raise TypeError("SourceRecord.cadence_seconds must be an int")
        if self.cadence_seconds <= 0:
            raise ValueError(
                "SourceRecord.cadence_seconds must be positive; a zero or negative "
                "cadence is not a schedule"
            )


@dataclass(frozen=True)
class SourceRegistry:
    """The registered ingredient sources. Frozen — a change is a new snapshot.

    Frozen because the registry is carried inside
    :class:`~crash_detector.engine.config.ConfigSnapshot`, and a snapshot that can be
    mutated after an evaluation cannot explain that evaluation a year later.
    """

    sources: tuple[SourceRecord, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", tuple(self.sources))
        seen: set[str] = set()
        for source in self.sources:
            # EXACT TYPE, not isinstance (CD-AC-005, Class 2). A SourceRecord subclass may
            # shadow `source_id` or `criticality` with a property, and a property is the
            # subclass's code running inside the criticality contract that decides which
            # sources a dial may declare as required.
            if type(source) is not SourceRecord:
                raise TypeError(
                    f"SourceRegistry holds SourceRecord, got {type(source).__name__}"
                )
            if source.source_id in seen:
                raise ValueError(
                    f"duplicate source_id in registry: {source.source_id!r}. Two rows "
                    "for one source is two criticalities for one source."
                )
            seen.add(source.source_id)

    @property
    def is_empty(self) -> bool:
        """True when no source is registered — the WO-2 shipped state."""
        return not self.sources

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(source.source_id for source in self.sources)

    def get(self, source_id: str) -> SourceRecord:
        """The record for ``source_id``, or :exc:`SourceNotRegistered`.

        Deliberately no ``default`` parameter and no ``default`` behaviour. A caller
        asking about a source nobody registered has a defect, and answering would hide it.
        """
        for source in self.sources:
            if source.source_id == source_id:
                return source
        raise SourceNotRegistered(f"source not registered: {source_id!r}")

    def criticality_of(self, source_id: str) -> Criticality:
        """The declared criticality of ``source_id``, or :exc:`SourceNotRegistered`."""
        return self.get(source_id).criticality

    def ids_with(self, criticality: Criticality) -> tuple[str, ...]:
        """Every registered source at ``criticality``."""
        if not isinstance(criticality, Criticality):
            raise TypeError("ids_with expects a Criticality member")
        return tuple(
            source.source_id
            for source in self.sources
            if source.criticality is criticality
        )

    def assert_registered(self, source_ids: Iterable[str]) -> None:
        """Refuse unless every named source is registered."""
        for source_id in source_ids:
            self.get(source_id)

    def assert_may_be_required(self, source_ids: Iterable[str]) -> None:
        """Refuse unless every named source is declared ``REQUIRED``.

        A ``DISPOSABLE`` source here raises :exc:`DisposableSourceIsLoadBearing` — the
        rule the dispatch names explicitly and the one the A5 database constraint must
        mirror. A ``CONTRIBUTING`` source here raises the base
        :exc:`CriticalityContractViolated`, because promoting a contributing source to
        load-bearing without changing its registry row is the same defect wearing a
        milder name.
        """
        for source_id in source_ids:
            record = self.get(source_id)
            if record.criticality is Criticality.DISPOSABLE:
                raise DisposableSourceIsLoadBearing(
                    f"source {source_id!r} is registered DISPOSABLE and may never be "
                    "named in a dial's required-input set (BLUEPRINT §5): a disposable "
                    "source's absence must change nothing, and a required input's "
                    "absence forces Unknown."
                )
            if record.criticality is not Criticality.REQUIRED:
                raise CriticalityContractViolated(
                    f"source {source_id!r} is registered "
                    f"{record.criticality.value} but is named in a required-input set. "
                    "Its declared engine consequence and the one this set gives it "
                    "disagree; change the registry row deliberately or change the set."
                )

    def assert_may_be_contributing(self, source_ids: Iterable[str]) -> None:
        """Refuse unless every named source is declared ``CONTRIBUTING``.

        A ``DISPOSABLE`` source here raises :exc:`DisposableSourceIsLoadBearing` too: the
        contributing set forces ``Degraded`` on absence, and "its absence changes
        nothing" and "its absence forces Degraded" cannot both be true of one source.
        """
        for source_id in source_ids:
            record = self.get(source_id)
            if record.criticality is Criticality.DISPOSABLE:
                raise DisposableSourceIsLoadBearing(
                    f"source {source_id!r} is registered DISPOSABLE and may never be "
                    "named in a dial's contributing-input set (BLUEPRINT §5): a "
                    "disposable source's absence must change nothing, and a "
                    "contributing input's absence forces Degraded."
                )
            if record.criticality is not Criticality.CONTRIBUTING:
                raise CriticalityContractViolated(
                    f"source {source_id!r} is registered "
                    f"{record.criticality.value} but is named in a contributing-input "
                    "set. Its declared engine consequence and the one this set gives it "
                    "disagree; change the registry row deliberately or change the set."
                )


#: The registry WO-2 ships. CD-D-005 is owed by the Product Owner before WO-3; until then
#: a populated registry would be invented product meaning (``PBG-AUTH-005``).
EMPTY_SOURCE_REGISTRY = SourceRegistry(sources=())
