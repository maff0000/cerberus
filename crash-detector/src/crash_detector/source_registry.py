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

import json
import os
from enum import Enum
from pathlib import Path
from typing import Iterable, Union

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from crash_detector.establishment import each_of, establishes, one_of
from crash_detector.staleness import (
    STALENESS_WINDOW_CEILING_SECONDS,
    STALENESS_WINDOW_CEILING_SOURCE,
    RelevanceWindow,
    StalenessWindow,
    StalenessWindowOutOfRange,
)

__all__ = [
    "Criticality",
    "CRITICALITY_NAMES",
    "SourceRecord",
    "SourceRegistry",
    "EMPTY_SOURCE_REGISTRY",
    "SourceNotRegistered",
    "CriticalityContractViolated",
    "DisposableSourceIsLoadBearing",
    # --- THE INDICATOR->DIAL MAPPING (WO-3 increment 16A, PO-DECISIONS-0025 r1/r2/r6) --- #
    "Polarity",
    "POLARITY_NAMES",
    "ProvisionalTier",
    "PROVISIONAL_TIER_NAMES",
    "WiringState",
    "WIRING_STATE_NAMES",
    "MappingRefused",
    "DialBoundTwice",
    "PendingSourceMayNotRenderAsValue",
    "StalenessWindowTooWideForTheCeiling",
    "DialBinding",
    "MappingProvenance",
    "IndicatorMapping",
    "IndicatorMappingRegistry",
    "EMPTY_INDICATOR_MAPPING_REGISTRY",
    "INDICATOR_MAPPING_PATH_ENV_VAR",
    "SYNTHETIC_ID_MARKER",
    "admit_staleness_window",
    "admit_relevance_window",
    "indicator_mapping_path",
    "load_indicator_mapping_registry",
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


@establishes(
    source_id=str,
    adapter_id=str,
    cadence_seconds=int,
    criticality=Criticality,
    stands_for=str,
)
@dataclass(frozen=True)
class SourceRecord:
    """One registered ingredient source — one row of ``raw.source_registry``."""

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `SourceRecord.__new__(SourceRecord)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("source_id", "adapter_id", "cadence_seconds", "criticality", "stands_for")

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
        # EXACT TYPE, NOT `isinstance` (WO-2R3 increment 10, ITEM_1, the F01 sweep).
        #
        # **THE DECLARED REASON FOR THE `isinstance` HERE WAS FALSIFIED BY MEASUREMENT.**
        # The register said: *"Criticality is an enum.Enum with members, which CPython
        # refuses to subclass, so isinstance and exact type coincide here and no supplied
        # implementation exists to reach."* **SUBCLASSING IS NOT THE ONLY ROUTE TO
        # `isinstance`.** CPython's `object_isinstance` falls back to the instance's
        # `__class__` attribute, and `__class__` is an ordinary property a caller can
        # define. MEASURED at `686a374`, against this very class:
        #
        #     class EvilCrit(Criticality)          -> TypeError: cannot extend
        #     class Forged:
        #         @property
        #         def __class__(self): return Criticality
        #     isinstance(Forged(), Criticality)    -> True
        #     type(Forged()) is Criticality        -> False        <- the asymmetry
        #
        # THIS door was already carried — `@establishes(criticality=Criticality)` refused
        # the forgery with `FieldNotEstablished` — but the sibling test in
        # `SourceRegistry.ids_with` was NOT, and ADMITTED it. Both are exact-typed now, so
        # the claim and the code agree at both.
        if type(self.criticality) is not Criticality:
            raise TypeError(
                "SourceRecord.criticality must be a Criticality member, got "
                f"{type(self.criticality).__name__}. A string is not a criticality: it "
                "is a criticality that has not been checked. Exact type and never "
                "isinstance: an enum CPython refuses to SUBCLASS can still be WORN, "
                "because isinstance also consults __class__."
            )
        # EXACT TYPE on the `int` limb; the `bool` limb stays `isinstance`, which is the
        # STRICTER of the two operators at a REFUSAL predicate. `cadence_seconds <= 0`
        # immediately below is an int subclass's `__le__` to answer — which is exactly what
        # the `DELEGATED` disposition said and left open. It is closed here.
        if isinstance(self.cadence_seconds, bool) or type(self.cadence_seconds) is not int:
            raise TypeError(
                "SourceRecord.cadence_seconds must be an int, got "
                f"{type(self.cadence_seconds).__name__}"
            )
        if self.cadence_seconds <= 0:
            raise ValueError(
                "SourceRecord.cadence_seconds must be positive; a zero or negative "
                "cadence is not a schedule"
            )


@establishes(
    sources=each_of(SourceRecord, within=(tuple,)),
)
@dataclass(frozen=True)
class SourceRegistry:
    """The registered ingredient sources. Frozen — a change is a new snapshot.

    Frozen because the registry is carried inside
    :class:`~crash_detector.engine.config.ConfigSnapshot`, and a snapshot that can be
    mutated after an evaluation cannot explain that evaluation a year later.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `SourceRegistry.__new__(SourceRegistry)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("sources",)

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
        """Every registered source at ``criticality``.

        **EXACT TYPE, AND THIS SITE WAS A LIVE ADMISSION OF A FORGED CRITICALITY**
        (WO-2R3 increment 10, ITEM_1). MEASURED at ``686a374``, before the change::

            class Forged:
                @property
                def __class__(self): return Criticality

            registry.ids_with(Forged())   -> ADMITTED, returned ()      <- no refusal
            registry.ids_with("REQUIRED") -> TypeError                  <- the control

        An object that is not a criticality was admitted and answered *"no sources at this
        criticality"*, because ``source.criticality is criticality`` is identity and no
        member is identical to the forgery. **A CALLER ASKING WHICH SOURCES ARE REQUIRED IS
        TOLD "NONE", AND A REQUIRED-INPUTS CHECK OVER AN EMPTY TUPLE PASSES VACUOUSLY.** The
        declared disposition for this site was ``EXACT`` on the ground that ``Criticality``
        cannot be subclassed; it cannot, and it did not need to be.
        """
        if type(criticality) is not Criticality:
            raise TypeError(
                "ids_with expects a Criticality member, got "
                f"{type(criticality).__name__}. Exact type and never isinstance: isinstance "
                "consults __class__, so an unrelated object WEARING Criticality was "
                "admitted here and answered that no source carries it."
            )
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


# ========================================================================================= #
# ========================================================================================= #
#
#   THE INDICATOR -> DIAL MAPPING, AS REGISTRY DATA
#   WO-3 INCREMENT 16A · PO-DECISIONS-0025 r1/r2/r6 · CD-ENG-WO3-03
#
# ========================================================================================= #
#
# *** WHY THIS LIVES IN source_registry.py AND NOT IN A COMPANION MODULE BESIDE IT. ***
#
# The dispatch offered both and left the choice to the Engineer (PBG-AUTH-005). A companion
# module `crash_detector/indicator_mapping.py` WAS WRITTEN FIRST and was then MOVED HERE, for
# a reason that was MEASURED and not anticipated:
#
#     tools/sweep/delegated_judgement_sweep.py --root .
#       baseline (116c01f)              PASS — 548 sites over 19 modules
#       with the companion module       FAIL — 610 sites, 1 violation
#                                       UNDECLARED MODULE: crash_detector.indicator_mapping
#
# A module entering the judgement closure is DECLARED either by a
# `DECLARED_MODULE_DISPOSITIONS` entry or by declaring every one of its tier-2 sites — and
# BOTH live in `tools/sweep/declared_dispositions.py`, which is (a) outside this seat's
# writable scope and (b) HELD by PO-DECISIONS-0018 ruling 3. **SO ANY NEW MODULE UNDER
# src/crash_detector/ TURNS A PASSING CONTROL RED, AND THE ONLY REMEDY IS A FILE NO ENGINEER
# SEAT MAY WRITE.** Weakening the sweep, or editing the register to make it green, would be
# the bypass PBG-FWK-013 and CD-D-130 exist to prevent.
#
# `crash_detector.source_registry` already carries an ESTABLISHED module disposition covering
# tier 2 module-wide, so the carrier lands here with ZERO new tier-1 admissions and the sweep
# returns to PASS. THE CONSTRAINT IS REAL AND IT IS REPORTED RATHER THAN ROUTED AROUND: this
# project cannot presently add a module under src/ without a Project-Lead act in the same
# increment. Raised as a finding in this increment's Build Log.
#
# THE COST IS DECLARED TOO, BECAUSE IT IS NOT ZERO: this file now answers TWO questions
# instead of one — how much of a dial's honesty depends on a source (the criticality
# contract, above) and which dial an indicator moves and how (the mapping, below). They are
# separate contracts with separate refusals and separate tests; they share a file, not a
# constructor.
#
#
# ========================================================================================= #
# *** THE MAPPING'S OWN DECLARED LIMITS (CD-RULE-004). THEY ARE NOT THE REGISTRY'S. ***
# ========================================================================================= #
#
#  1  ZERO ROWS ARE REGISTERED, SO EVERY REFUSAL BELOW IS UNEXERCISED BY REAL DATA. It is
#     exercised by tests using OBVIOUSLY-SYNTHETIC identifiers (PLANT_SYNTH_*), and
#     tests/test_indicator_mapping.py asserts that no synthetic identifier can appear in the
#     shipped data file. NOTHING HERE HAS MET A REAL INDICATOR.
#
#     And the ZERO is the deliverable, for a DIFFERENT reason from the empty source registry
#     above. WO-2 registered nothing because CD-D-005 HAD NOT BEEN DECIDED. This ships empty
#     because CD-D-005 HAS been decided — PO-DECISIONS-0025 ruling 1 ratifies
#     `trinity:pbgv2:crash_detector:indicator_dial_mapping:v1`, ~24 indicators, each with a
#     dial binding, a tier weight and a polarity — AND THAT ARTEFACT RESOLVES NOWHERE
#     REACHABLE FROM THIS REPOSITORY. Measured and raised as Q30. The rows are 16B. A
#     placeholder row would be inventing the product meaning the ruling exists to supply.
#
#  2  *** THE POLARITY VOCABULARY IS THIS SEAT'S DERIVATION AND NOT A RATIFIED LIST. ***
#     Ruling 1 says every indicator carries "polarity" and DOES NOT SAY what the admissible
#     values are; the artefact that would is Q30. `Polarity` declares the two values a SIGN
#     can take, on the reasoning that a polarity IS the sign of a monotone mapping and a sign
#     is exhaustively two-valued — a structural derivation, not a product choice. IF THE
#     RATIFIED MAPPING USES A RICHER VOCABULARY — a non-monotone or U-shaped relationship,
#     where BOTH extremes are risk — THEN THIS ENUM IS WRONG AND 16B FINDS IT AT THE FIRST
#     SUCH ROW. That is a real possibility for macro indicators and it is raised, not assumed
#     away.
#
#  3  *** THE STALENESS WINDOW CANNOT EXPRESS WHAT RULING 6 REQUIRES, AND THIS SEAT DID NOT
#     WIDEN THE BOUND TO MAKE IT. *** See `admit_staleness_window` below — it carries the
#     measurement. THIS IS THE MOST IMPORTANT LIMIT HERE AND IT BLOCKS 16B.
#
#  4  NOTHING HERE IS PERSISTED. There is no `raw.indicator_mapping` table and no migration.
#     The mapping travels as a FILE inside the image and inside the ConfigSnapshot; the
#     database half is not built and is not claimed.
#
#  5  TWO DIALS ARE NEVER BLENDED, AND IT IS ENFORCED BY SHAPE RATHER THAN BY VIGILANCE
#     (PO-DECISIONS-0025 r7). A `BOTH` indicator is TWO `DialBinding` entries with TWO
#     polarities. `DialBinding` carries exactly ONE dial_id and ONE Polarity: THERE IS NO
#     FIELD FOR A SECOND DIAL, so there is no expression a caller can write that puts two
#     dials in one binding. `provisional_tier` is an enum member and NOT a float, so there is
#     nothing here that can be summed across two dials.
#
#  6  THE NEW ENUMS ARE NEW DOORS OF A KIND THIS PROJECT HAS ALREADY BEEN FORGED THROUGH.
#     Lines 174-200 above record it: an enum CPython refuses to SUBCLASS can still be WORN,
#     because isinstance consults __class__ — and that forgery was LIVE AND ADMITTED at
#     `ids_with` until increment 10. `Polarity`, `ProvisionalTier` and `WiringState` are
#     compared by EXACT TYPE and never isinstance, and tests/test_indicator_mapping.py plants
#     the __class__ forgery against EVERY ONE of them and shows it REFUSED.
#
# ========================================================================================= #


class Polarity(Enum):
    """Which DIRECTION of an indicator's movement means MORE risk on the dial it binds.

    **TWO MEMBERS, AND THE TWO ARE THE SIGN OF A MONOTONE MAPPING.** See declared limit 2 in
    the module docstring: this vocabulary is DERIVED by this seat from the structure of the
    word, because the ratified list is ``Q30``. A third member is not an edit here — it is a
    statement that the relationship is not monotone, which is a product question.

    A polarity is REQUIRED on every binding. There is no ``UNKNOWN`` and no ``NEUTRAL``
    member: an indicator whose direction nobody has decided is an indicator that cannot be
    scored, and giving it a member here would let it register and read as though it could.
    """

    RISING_MEANS_MORE_RISK = "RISING_MEANS_MORE_RISK"
    RISING_MEANS_LESS_RISK = "RISING_MEANS_LESS_RISK"


POLARITY_NAMES: tuple[str, ...] = tuple(member.value for member in Polarity)


class ProvisionalTier(Enum):
    """The starting weight tier — ``x3 | x2 | x1`` (``PO-DECISIONS-0025`` r1).

    *** **THE TYPE CARRIES THE WORD "PROVISIONAL" BECAUSE THE NUMBERS ARE PROVISIONAL, AND
    THE NAME IS THE ONLY PART OF A TYPE THAT TRAVELS INTO EVERY CALL SITE.** *** Ruling 3:

        *"THE TIER WEIGHTS ARE STARTING VALUES. They are calibrated by backtest against
        historical crash + debasement episodes… **No weight is trusted on assertion.**"*

    A bare ``float`` field named ``weight`` would launder a provisional starting value into
    an authoritative one the moment somebody multiplied by it, and nothing at the call site
    would say otherwise. **A MEMBER OF THIS ENUM CANNOT BE MULTIPLIED BY ANYTHING**: it is
    not a number and defines no arithmetic dunder, so the backtest that ruling 3 requires has
    to happen before any weight can be applied — enforced by the type rather than remembered.

    That is also the second guard on ``CD-AC-002``: three enum members cannot be summed
    across two dials, so there is nothing here from which a combined headline could be built.
    """

    X3 = "x3"
    X2 = "x2"
    X1 = "x1"


PROVISIONAL_TIER_NAMES: tuple[str, ...] = tuple(member.value for member in ProvisionalTier)


class WiringState(Enum):
    """Whether this indicator's feed is actually connected in THIS container.

    ``PO-DECISIONS-0025`` r4, on SLOOS: *"until registered in this container it shows
    PENDING, **never a false green**."* The NDFI leg is manual-quarterly and will be
    ``PENDING`` for real, for a long time, and that is not a defect.

    *** ``PENDING`` NEVER RENDERS AS A VALUE, AND THAT IS A REFUSAL AND NOT A CONVENTION. ***
    See :meth:`IndicatorMapping.assert_may_render_as_value`.
    """

    WIRED = "WIRED"
    PENDING = "PENDING"


WIRING_STATE_NAMES: tuple[str, ...] = tuple(member.value for member in WiringState)

#: Every test fixture in this project uses an identifier carrying this marker, and
#: ``tests/test_indicator_mapping.py`` asserts the shipped data file contains none of them.
#: ``CD-PL-F154`` is what a fixture escaping onto a real branch costs. A fixture id of
#: ``CREDIT_HY_OAS`` would be exactly that defect, so the fixtures are unmistakable instead.
SYNTHETIC_ID_MARKER = "PLANT_SYNTH_"

#: Where the registry data file lives. Configuration from the environment (Standards
#: Baseline §12, ``PO-DECISIONS-0025`` r2: ALL config via env), so a container that mounts
#: the mapping elsewhere needs no code change and no host path appears in this source.
INDICATOR_MAPPING_PATH_ENV_VAR = "CD_INDICATOR_MAPPING_PATH"

_DEFAULT_MAPPING_PATH = Path(__file__).resolve().parents[2] / "deploy" / "indicator-mapping.json"


class MappingRefused(ValueError):
    """A row cannot be admitted to the indicator mapping.

    A base class so a guard can catch the CLASS of refusal rather than the one member
    somebody planted — the same reason :exc:`CriticalityContractViolated` has subclasses.
    """


class DialBoundTwice(MappingRefused):
    """One indicator declared two bindings for the SAME dial.

    Two directions for one dial is the blend wearing a different hat: whatever consumed both
    would have to reconcile them, and reconciling two polarities into one answer is a
    function taking two readings of the same dial and returning one — the ``CD-AC-002`` shape
    reached from the inside rather than across.
    """


class PendingSourceMayNotRenderAsValue(MappingRefused):
    """A ``PENDING`` row was asked to render as a value.

    ``PO-DECISIONS-0025`` r4: *"until registered in this container it shows PENDING, never a
    false green."* PID §3.2 is the constitutional half: *"Missing data must never render as
    calm."* A row whose feed is not wired has no observation, and an unwired feed rendering
    green is precisely a false green.
    """


class StalenessWindowTooWideForTheCeiling(MappingRefused):
    """The declared window is wider than :data:`STALENESS_WINDOW_CEILING_SECONDS`.

    *** **THIS IS NOT A ROUTINE REFUSAL. IT IS A COLLISION BETWEEN TWO RATIFIED CLAUSES, AND
    IT BLOCKS 16B.** *** See :func:`admit_staleness_window`, which carries the measurement.
    """


def admit_staleness_window(seconds: object) -> StalenessWindow:
    """Admit a per-indicator staleness window through the project's ONE window door.

    ``PO-PRODUCT-0001`` R2: the window is declared **per indicator, never global**. This
    reuses :class:`~crash_detector.staleness.StalenessWindow` rather than building a second
    mechanism beside it, because two guarded comparison sites are an enumeration and
    enumerations come apart.

    ===========================================================================================
    *** AND REUSING IT SURFACES A REAL COLLISION, MEASURED AND NOT INFERRED. ***
    ===========================================================================================
    ``PO-DECISIONS-0025`` ruling 6 requires *"private credit stress with a **WIDE** staleness
    window (its latency IS the point — absence reads Unknown, never calm)"*, and ruling 4
    registers SLOOS's NDFI leg as **manual-quarterly**.

    :data:`STALENESS_WINDOW_CEILING_SECONDS` is **900.0 — fifteen minutes**. MEASURED at this
    increment against the real constructor, not read off the constant::

        StalenessWindow(seconds=91*86400)  quarterly   -> REFUSED StalenessWindowOutOfRange
        StalenessWindow(seconds=30*86400)  one month   -> REFUSED
        StalenessWindow(seconds=86400)     one day     -> REFUSED
        StalenessWindow(seconds=3600)      one hour    -> REFUSED
        StalenessWindow(seconds=960)       16 minutes  -> REFUSED
        StalenessWindow(seconds=900)       15 minutes  -> ADMITTED

    **SO THE CARRIER CANNOT TODAY HOLD THE WINDOWS THE RULING REQUIRES, AND NOT ONLY THE
    QUARTERLY ONES — NOTHING SLOWER THAN INTRADAY FITS.**

    **THE BOUND IS NOT WIDENED HERE, AND THAT IS DELIBERATE.** The ceiling is DERIVED from
    ``PID.md`` §5's ratified assurance latency budget, with its clause cited
    (``CD-RULE-003``); moving it to make a row fit would be reversing the derivation to suit
    the data, which is the definition of the invention the rule forbids. It is also outside
    this dispatch.

    **WHAT THE COLLISION LOOKS LIKE ON INSPECTION, OFFERED AS ANALYSIS AND NOT AS A RULING**
    (``PBG-AUTH-005`` — product meaning is not this seat's): the ceiling's own derivation
    reasons about **FEED LIVENESS** — *"a window wider than the detectability budget renders
    a dead feed as fresh for longer than the product permits a failure to go undetected"*.
    A per-indicator window under ``PO-PRODUCT-0001`` R2 reasons about **DATA CADENCE** — how
    old an observation of a quarterly survey may legitimately be while still being the
    current observation. A three-month-old SLOOS reading is not a dead feed; it is a healthy
    feed of a quarterly series. **THOSE ARE TWO DIFFERENT QUANTITIES THAT HAPPEN TO SHARE A
    UNIT, AND ONE CONSTANT IS CURRENTLY SERVING BOTH.** Whether they should be separated is a
    Product Owner question. **RAISED, NOT RESOLVED, AND NOT ROUTED AROUND.**
    """
    try:
        return StalenessWindow(seconds=seconds)
    except StalenessWindowOutOfRange as refusal:
        window = None
        try:
            window = float(seconds)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise
        if window > STALENESS_WINDOW_CEILING_SECONDS:
            raise StalenessWindowTooWideForTheCeiling(
                f"a per-indicator staleness window of {window!r} seconds exceeds the "
                f"ceiling of {STALENESS_WINDOW_CEILING_SECONDS} seconds "
                f"({STALENESS_WINDOW_CEILING_SECONDS / 60:.0f} minutes) and is REFUSED, not "
                "clamped. *** THIS IS A KNOWN COLLISION AND NOT A CONFIGURATION MISTAKE: "
                "PO-DECISIONS-0025 ruling 6 requires a WIDE window for private credit "
                "stress and ruling 4 registers SLOOS's NDFI leg as manual-QUARTERLY, and "
                "NOTHING SLOWER THAN 15 MINUTES FITS THROUGH THIS DOOR. *** The ceiling is "
                "DERIVED and was not chosen, so it is not this code's to widen "
                f"(CD-RULE-003). {STALENESS_WINDOW_CEILING_SOURCE}"
            ) from refusal
        raise


def admit_relevance_window(seconds: object) -> RelevanceWindow:
    """Admit a per-indicator RELEVANCE window (data cadence), the door ``_admit_row`` uses.

    WO-1.3 (Owner direction, 2026-10-11): separate from :func:`admit_staleness_window`, which
    keeps the 900 s FEED-LIVENESS ceiling and is unchanged. See
    :class:`~crash_detector.staleness.RelevanceWindow`.
    """
    return RelevanceWindow(seconds=seconds)


@establishes(dial_id=str, polarity=Polarity)
@dataclass(frozen=True)
class DialBinding:
    """ONE dial, and the direction that means more risk on it.

    *** **THERE IS NO FIELD HERE FOR A SECOND DIAL.** *** A ``BOTH`` indicator is two of
    these, with two polarities. That is not a convention to follow; it is the only shape the
    class can hold, which is the structural answer ``CD-AC-002`` asks for.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `DialBinding.__new__(DialBinding)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having executed
    #: NO package code. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("dial_id", "polarity")

    dial_id: str
    polarity: Polarity

    def __post_init__(self) -> None:
        # RE-ESTABLISHED BEFORE IT IS COMPARED OR HASHED (CD-AC-005, Class 2). `dial_id` is
        # tested for DIAL_IDS membership and put in a set to detect a dial bound twice —
        # both the supplied string's `__eq__`/`__hash__` to answer, and `isinstance(x, str)`
        # admitted a subclass that could answer them differently on the second call.
        try:
            object.__setattr__(self, "dial_id", own_str(self.dial_id))
        except NotEstablishedOnOwnTerms:
            raise MappingRefused(
                f"a dial binding requires a non-empty dial_id; the dials are {DIAL_IDS}"
            ) from None
        if self.dial_id not in DIAL_IDS:
            raise MappingRefused(
                f"unknown dial_id {self.dial_id!r}; the dials are {DIAL_IDS}. A binding "
                "names ONE dial. A token meaning 'both' is not a dial: an indicator that "
                "moves both dials is TWO bindings with TWO polarities "
                "(PO-DECISIONS-0025 r7 — two dials NEVER blended). A third dial is a PID "
                "amendment, not a mapping edit."
            )
        # EXACT TYPE, NOT `isinstance`. An enum CPython refuses to SUBCLASS can still be
        # WORN, because isinstance consults __class__ — measured against Criticality at
        # 686a374 and live at `ids_with` until increment 10. This is a new door of that kind.
        if type(self.polarity) is not Polarity:
            raise MappingRefused(
                "a bound dial must declare a Polarity member, got "
                f"{type(self.polarity).__name__}. A bound dial with no polarity is a dial "
                "nobody can score: the mapping would know the indicator matters and not "
                "which way. Exact type and never isinstance: an enum CPython refuses to "
                "SUBCLASS can still be WORN, because isinstance also consults __class__."
            )


@establishes(
    ruling_ref=str,
    mapping_artefact=str,
    mapping_version=str,
    stands_for=str,
)
@dataclass(frozen=True)
class MappingProvenance:
    """The ``CD-D-005`` authority trail: WHO admitted this row, and FROM WHAT.

    PID doctrine §3.6 forbids unexplained mappings, and ``stands_for`` is *"the admission
    ticket, not documentation"*. **AN UNEXPLAINED MAPPING CANNOT BE ADMITTED**, so every
    field here is required and non-empty — there is no ``None``, no default and no
    ``"TBD"``-shaped escape, because a row that cannot say who admitted it is a row nobody
    can defend a year later.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason given on DialBinding.
    __slots__ = ("ruling_ref", "mapping_artefact", "mapping_version", "stands_for")

    #: The decision record that admitted the row, e.g. a PO-DECISIONS reference.
    ruling_ref: str
    #: The mapping artefact the row was read from, by its full identifier.
    mapping_artefact: str
    #: That artefact's version. A mapping without a version cannot be re-derived.
    mapping_version: str
    #: What this indicator STANDS FOR on the dial it binds — the admission ticket.
    stands_for: str

    def __post_init__(self) -> None:
        # EACH FIELD NAMED EXPLICITLY, NOT REACHED THROUGH `getattr(self, name)`.
        # A `getattr` loop over field names is a DUCK admission — a TIER 1 site under
        # `tools/sweep/delegated_judgement_sweep.py`, carrying an obligation to write a
        # disposition in a register no Engineer seat owns (PO-DECISIONS-0018 r3). Writing
        # the four out costs four lines and creates no debt. It is also the more honest
        # code: the fields are a fixed, declared four, and a loop implied they were not.
        object.__setattr__(self, "ruling_ref", self._established("ruling_ref", self.ruling_ref))
        object.__setattr__(
            self,
            "mapping_artefact",
            self._established("mapping_artefact", self.mapping_artefact),
        )
        object.__setattr__(
            self,
            "mapping_version",
            self._established("mapping_version", self.mapping_version),
        )
        object.__setattr__(self, "stands_for", self._established("stands_for", self.stands_for))

    @staticmethod
    def _established(name: str, value: object) -> str:
        """Re-establish ONE provenance field on this system's own terms, or refuse.

        One function, four call sites — never four independently written checks, because
        four checks are an enumeration and enumerations come apart.
        """
        try:
            established = own_str(value)
        except NotEstablishedOnOwnTerms:
            raise MappingRefused(
                f"provenance requires a non-empty {name}. An unexplained mapping cannot be "
                "admitted (PID doctrine §3.6); stands_for is the admission ticket, not "
                "documentation."
            ) from None
        if not established.strip():
            raise MappingRefused(
                f"provenance requires a non-empty {name}, and whitespace is not content. "
                "An unexplained mapping cannot be admitted (PID §3.6)."
            )
        return established


@establishes(
    source_id=str,
    dial_bindings=each_of(DialBinding, within=(tuple,)),
    provisional_tier=ProvisionalTier,
    staleness_window=one_of(StalenessWindow, RelevanceWindow),
    provenance=MappingProvenance,
    wiring_state=WiringState,
)
@dataclass(frozen=True)
class IndicatorMapping:
    """ONE registered indicator's mapping — one row of the registry data file.

    Everything ``PO-DECISIONS-0025`` r6 requires a row to carry, and nothing it does not.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason given on DialBinding.
    __slots__ = (
        "source_id",
        "dial_bindings",
        "provisional_tier",
        "staleness_window",
        "provenance",
        "wiring_state",
    )

    source_id: str
    dial_bindings: tuple[DialBinding, ...]
    provisional_tier: ProvisionalTier
    staleness_window: Union[StalenessWindow, RelevanceWindow]
    provenance: MappingProvenance
    wiring_state: WiringState

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "source_id", own_str(self.source_id))
        except NotEstablishedOnOwnTerms:
            raise MappingRefused("an indicator mapping requires a non-empty source_id") from None

        object.__setattr__(self, "dial_bindings", tuple(self.dial_bindings))

        # EXACT TYPE on every element: a DialBinding subclass may shadow `dial_id` or
        # `polarity` with a property, and a property is the caller's code running inside the
        # duplicate-dial test below — deciding, at the moment it is asked, which dial it is.
        if any(type(binding) is not DialBinding for binding in self.dial_bindings):
            raise MappingRefused(
                "IndicatorMapping.dial_bindings must all be DialBinding, got "
                f"{[type(b).__name__ for b in self.dial_bindings]}"
            )
        if not self.dial_bindings:
            raise MappingRefused(
                f"indicator {self.source_id!r} binds no dial. A mapping row exists to say "
                "which dial an indicator moves; a row that binds nothing is a source "
                "registration wearing a mapping's name."
            )
        bound: set[str] = set()
        for binding in self.dial_bindings:
            if binding.dial_id in bound:
                raise DialBoundTwice(
                    f"indicator {self.source_id!r} binds {binding.dial_id!r} twice. Two "
                    "polarities for one dial cannot both be applied, so something "
                    "downstream would have to reconcile them into one answer — which is a "
                    "function taking two readings of one dial and returning one, the "
                    "CD-AC-002 shape reached from the inside. An indicator that moves BOTH "
                    "dials is one binding per dial (PO-DECISIONS-0025 r7)."
                )
            bound.add(binding.dial_id)

        # EXACT TYPE on both new enum limbs, for the __class__-forgery reason recorded in
        # the module docstring and measured in source_registry.py:174-200.
        if type(self.provisional_tier) is not ProvisionalTier:
            raise MappingRefused(
                "IndicatorMapping.provisional_tier must be a ProvisionalTier member, got "
                f"{type(self.provisional_tier).__name__}. The vocabulary is "
                f"{list(PROVISIONAL_TIER_NAMES)} (PO-DECISIONS-0025 r1). A bare number is "
                "not a tier: it is a weight that has skipped the backtest ruling 3 "
                "requires. Exact type and never isinstance."
            )
        if type(self.wiring_state) is not WiringState:
            raise MappingRefused(
                "IndicatorMapping.wiring_state must be a WiringState member, got "
                f"{type(self.wiring_state).__name__}. The vocabulary is "
                f"{list(WIRING_STATE_NAMES)}. Exact type and never isinstance."
            )
        # EXACT TYPE: a StalenessWindow subclass may redefine `covers`, and `covers` IS the
        # freshness answer — the thing that decides whether an observation is current.
        if type(self.staleness_window) not in (StalenessWindow, RelevanceWindow):
            raise MappingRefused(
                "IndicatorMapping.staleness_window must be a StalenessWindow, got "
                f"{type(self.staleness_window).__name__}. A bare number of seconds has not "
                "passed the one admission door (PO-PRODUCT-0001 R2: declared PER INDICATOR, "
                "never global); build it through admit_staleness_window."
            )
        if type(self.provenance) is not MappingProvenance:
            raise MappingRefused(
                "IndicatorMapping.provenance must be a MappingProvenance, got "
                f"{type(self.provenance).__name__}. An unexplained mapping cannot be "
                "admitted (PID doctrine §3.6, CD-D-005)."
            )

    @property
    def bound_dial_ids(self) -> tuple[str, ...]:
        """The dials this indicator moves, in declaration order. Never a combined token."""
        return tuple(binding.dial_id for binding in self.dial_bindings)

    def polarity_for(self, dial_id: str) -> Polarity:
        """This indicator's polarity ON ONE DIAL.

        Takes ONE dial and returns ONE polarity. **There is deliberately no variant that
        returns both**, and no ``polarities`` property that hands out a pair for something
        else to reconcile: the pair is where a blend gets assembled.
        """
        for binding in self.dial_bindings:
            if binding.dial_id == dial_id:
                return binding.polarity
        raise MappingRefused(
            f"indicator {self.source_id!r} declares no binding for dial {dial_id!r}; it "
            f"binds {list(self.bound_dial_ids)}. Answered with a refusal rather than a "
            "default polarity: a default direction is a direction nobody decided."
        )

    def assert_may_render_as_value(self) -> None:
        """*** REFUSE unless this row's feed is actually WIRED. ***

        ``PO-DECISIONS-0025`` r4: *"until registered in this container it shows PENDING,
        **never a false green**."*

        **A REFUSAL AND NOT A CONVENTION.** A convention is a thing every renderer must
        remember; this raises, so a surface that forgot to branch on ``wiring_state`` fails
        loudly at the point of the mistake instead of quietly publishing a green dial for a
        feed that has never been connected.
        """
        if self.wiring_state is not WiringState.WIRED:
            raise PendingSourceMayNotRenderAsValue(
                f"indicator {self.source_id!r} is {self.wiring_state.value} and may not "
                "render as a value. PO-DECISIONS-0025 ruling 4: 'until registered in this "
                "container it shows PENDING, never a false green.' PID §3.2 is "
                "constitutional on the same point: 'Missing data must never render as "
                "calm.' An unwired feed has no observation, and an unwired feed rendering "
                "green IS the false green."
            )


@establishes(mappings=each_of(IndicatorMapping, within=(tuple,)))
@dataclass(frozen=True)
class IndicatorMappingRegistry:
    """The registered indicator mappings. Frozen — a change is a new snapshot.

    Frozen for the reason :class:`~crash_detector.source_registry.SourceRegistry` is: it is
    carried inside :class:`~crash_detector.engine.config.ConfigSnapshot`, and a snapshot that
    can be mutated after an evaluation cannot explain that evaluation a year later.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason given on DialBinding.
    __slots__ = ("mappings",)

    mappings: tuple[IndicatorMapping, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "mappings", tuple(self.mappings))
        seen: set[str] = set()
        for mapping in self.mappings:
            # EXACT TYPE: an IndicatorMapping subclass may shadow `source_id` or
            # `wiring_state` with a property, and `wiring_state` IS the false-green refusal.
            if type(mapping) is not IndicatorMapping:
                raise MappingRefused(
                    "IndicatorMappingRegistry holds IndicatorMapping, got "
                    f"{type(mapping).__name__}"
                )
            if mapping.source_id in seen:
                raise MappingRefused(
                    f"duplicate source_id in the indicator mapping: {mapping.source_id!r}. "
                    "Two rows for one indicator is two dial bindings for one indicator "
                    "arriving by the back door."
                )
            seen.add(mapping.source_id)

    @property
    def is_empty(self) -> bool:
        """True when no indicator is mapped — **the WO-3 increment 16A shipped state.**"""
        return not self.mappings

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(mapping.source_id for mapping in self.mappings)

    def get(self, source_id: str) -> IndicatorMapping:
        """The mapping for ``source_id``, or :exc:`MappingRefused`.

        Deliberately no ``default``: a caller asking about an indicator nobody mapped has a
        defect, and answering would hide it.
        """
        for mapping in self.mappings:
            if mapping.source_id == source_id:
                return mapping
        raise MappingRefused(f"indicator not mapped: {source_id!r}")

    def mappings_for_dial(self, dial_id: str) -> tuple[IndicatorMapping, ...]:
        """Every mapping bound to ``dial_id``. **ONE dial in, and never both.**"""
        if dial_id not in DIAL_IDS:
            raise MappingRefused(
                f"unknown dial_id {dial_id!r}; the dials are {DIAL_IDS}. This method takes "
                "ONE dial and there is no variant that takes both."
            )
        return tuple(m for m in self.mappings if dial_id in m.bound_dial_ids)

    def pending_source_ids(self) -> tuple[str, ...]:
        """Every indicator whose feed is not wired in this container.

        Exposed so an operator can SEE the pending set rather than discovering it as a dial
        that never moves (``PO-DECISIONS-0025`` r4).
        """
        return tuple(
            m.source_id for m in self.mappings if m.wiring_state is WiringState.PENDING
        )


#: *** THE MAPPING WO-3 INCREMENT 16A SHIPS: ZERO ROWS, AND THAT IS THE DELIVERABLE. ***
#: The ratified artefact's CONTENT cannot be read from this project (``Q30``), and a
#: placeholder row would be invented product meaning (``PBG-AUTH-005``). The rows are 16B.
EMPTY_INDICATOR_MAPPING_REGISTRY = IndicatorMappingRegistry(mappings=())


def indicator_mapping_path() -> Path:
    """Where the registry data file lives — from the environment, with a declared default.

    Unlike the detail-policy thresholds, a DEFAULT is correct here and the difference is
    worth stating: a threshold default would invent a dial SCALE (product meaning), whereas
    this default names a FILE INSIDE THIS REPOSITORY that ships with the code. Getting it
    wrong is a missing-file error, not a silently-wrong number.
    """
    override = os.environ.get(INDICATOR_MAPPING_PATH_ENV_VAR)
    return Path(override) if override else _DEFAULT_MAPPING_PATH


def _admit_binding(raw: object, *, source_id: str) -> DialBinding:
    if type(raw) is not dict:
        raise MappingRefused(
            f"{source_id}: a dial binding must be a plain JSON object, got "
            f"{type(raw).__name__}. Exact type and never isinstance: a dict subclass may "
            "redefine __contains__ or keys, and the key-set equality below IS the judgement."
        )
    declared = set(raw)
    if declared != {"dial_id", "polarity"}:
        raise MappingRefused(
            f"{source_id}: a dial binding declares exactly 'dial_id' and 'polarity', got "
            f"{sorted(declared)}. The key set is asserted by EQUALITY, so a key nobody has "
            "thought of — a second dial, a combined weight — fails the same clause."
        )
    try:
        polarity = Polarity(raw["polarity"])
    except ValueError:
        raise MappingRefused(
            f"{source_id}: {raw['polarity']!r} is not a declared polarity; the vocabulary "
            f"is {list(POLARITY_NAMES)}"
        ) from None
    return DialBinding(dial_id=raw["dial_id"], polarity=polarity)


def _admit_row(raw: object) -> IndicatorMapping:
    if type(raw) is not dict:
        raise MappingRefused(
            "each entry under 'indicators' must be a plain JSON object, got "
            f"{type(raw).__name__}. Exact type and never isinstance, for the reason given "
            "in _admit_binding: the key-set equality below is the judgement itself."
        )
    declared = set(raw)
    expected = {
        "source_id",
        "dial_bindings",
        "provisional_tier",
        "staleness_window_seconds",
        "provenance",
        "wiring_state",
    }
    if declared != expected:
        raise MappingRefused(
            f"an indicator declares exactly {sorted(expected)}, got {sorted(declared)}. "
            "Asserted by EQUALITY: a missing provenance and an invented 'weight' both fail "
            "here, and neither can be added by writing a key nobody has read."
        )
    source_id = raw["source_id"]
    provenance_raw = raw["provenance"]
    if type(provenance_raw) is not dict:
        raise MappingRefused(
            f"{source_id}: provenance must be a plain JSON object, got "
            f"{type(provenance_raw).__name__}. It is splatted into MappingProvenance(**...) "
            "immediately below, so a subclass controlling `keys` chooses which fields the "
            "constructor even sees — including whether provenance is there at all."
        )
    try:
        tier = ProvisionalTier(raw["provisional_tier"])
    except ValueError:
        raise MappingRefused(
            f"{source_id}: {raw['provisional_tier']!r} is not a declared tier; the "
            f"vocabulary is {list(PROVISIONAL_TIER_NAMES)} (PO-DECISIONS-0025 r1)"
        ) from None
    try:
        wiring = WiringState(raw["wiring_state"])
    except ValueError:
        raise MappingRefused(
            f"{source_id}: {raw['wiring_state']!r} is not a declared wiring state; the "
            f"vocabulary is {list(WIRING_STATE_NAMES)}"
        ) from None
    return IndicatorMapping(
        source_id=source_id,
        dial_bindings=tuple(
            _admit_binding(b, source_id=source_id) for b in raw["dial_bindings"]
        ),
        provisional_tier=tier,
        staleness_window=admit_relevance_window(raw["staleness_window_seconds"]),
        provenance=MappingProvenance(**provenance_raw),
        wiring_state=wiring,
    )


def load_indicator_mapping_registry(path: "Path | None" = None) -> IndicatorMappingRegistry:
    """Read the registry data file and admit every row through the constructors above.

    **THE LOADER PERFORMS NO VALIDATION OF ITS OWN BEYOND SHAPE.** Every judgement about
    whether a row MEANS anything — the dial vocabulary, the polarity, the tier, the window
    ceiling, the provenance — is made by the same constructors a hand-built row goes
    through. A loader with its own copy of the rules is a second place the rules live, and
    the two come apart in exactly the direction nobody is testing.

    JSON and not YAML, deliberately: ``src/`` imports no YAML parser today and PyYAML is not
    among this project's declared dependencies, so a YAML mapping file would either add a
    runtime dependency for one file or need a hand-written parser inside ``src/``. The
    registry travels as JSON, which the standard library reads.
    """
    target = indicator_mapping_path() if path is None else Path(path)
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise MappingRefused(
            f"the indicator mapping data file does not exist at {target}. It is REQUIRED "
            "and there is no empty default: a mapping that arrived by omission is not "
            f"evidence of anything. Set {INDICATOR_MAPPING_PATH_ENV_VAR} or ship the file."
        ) from None
    except json.JSONDecodeError as exc:
        raise MappingRefused(f"the indicator mapping at {target} is not valid JSON: {exc}") from None

    if type(document) is not dict:
        raise MappingRefused(
            f"the indicator mapping at {target} is not a plain JSON object, got "
            f"{type(document).__name__}. Exact type and never isinstance: the top-level "
            "key-set equality below is the judgement."
        )
    expected_top = {"$comment", "mapping_artefact", "mapping_version", "indicators"}
    if set(document) != expected_top:
        raise MappingRefused(
            f"the indicator mapping at {target} declares {sorted(document)}; the key set is "
            f"asserted by EQUALITY and must be {sorted(expected_top)}. An ABSENT "
            "'indicators' key is a file nobody finished (an EMPTY list is the shipped state "
            "and is legal), and an EXTRA top-level key is a place to smuggle a global "
            "default — a global staleness window, a default polarity, a fallback tier — "
            "past the per-indicator declaration PO-PRODUCT-0001 R2 requires."
        )
    rows = document["indicators"]
    if type(rows) is not list:
        raise MappingRefused(
            f"'indicators' must be a plain JSON list, got {type(rows).__name__}. A list "
            "subclass may redefine __iter__ and hand the loop below different rows than the "
            "ones the file holds."
        )
    return IndicatorMappingRegistry(mappings=tuple(_admit_row(row) for row in rows))
