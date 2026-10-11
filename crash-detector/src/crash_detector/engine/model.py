"""MODELS ARE DATA — named specs the engine resolves, never objects a caller supplies.

BP-AMENDMENT-0001 §C, in force. This module replaces the one that shipped at
``f30e63c``, and the replacement is a DELETION and not a repair.

====================================================================================
WHAT WAS HERE, AND WHY IT IS GONE
====================================================================================

Until this commit this module declared::

    class ContributionModel(Protocol):
        def compute(self, payloads) -> ScoreComputation: ...

    CONTRIBUTION_MODELS: Mapping[str, ContributionModel] = {}

and :class:`~crash_detector.engine.config.DialSpec` carried a field holding one of
those objects. ``evaluate`` then called ``spec.contribution_model.compute(payloads)``
and stamped whatever came back with the dial's own provenance.

That is the route ``ASR3-F02`` published a laundered number through: ONE stateful object
placed in BOTH ``DialSpec``s saw the equity dial's payloads on the first call and the
monetary dial's on the second, blended them in its own memory, and returned a number that
every downstream layer stamped with honest single-dial provenance. **Every field of the
claim was true except the number.** A ``Protocol`` annotation asserts nothing at runtime,
so there was no check to strengthen — there was a door that should not have existed.

**THIS IS THIS CODEBASE'S OWN STRONGEST EXISTING CLOSURE, APPLIED ONE LEVEL UP.**
:func:`~crash_detector.dials.magnitude.combine_within_one_dial` lived exactly this history
one increment earlier: its ``using`` argument received released floats and returned one,
which made it the public proxy through which ``ASR2-002-A`` published an equity 0.5 out of
an equity 0.9 and a monetary 0.1 with every static layer green. The repair was not a
stronger check on the callable. It was **deleting the callable argument** and replacing it
with a NAME from a closed set, executed by the module that owns the numbers
(:class:`~crash_detector.dials.provenance.SameDialReduction`). ``ASR3-F02`` is the identical
defect wearing a ``Protocol`` instead of a ``lambda``, arriving through ``DialSpec`` instead
of through a keyword argument, and it gets the identical repair.

====================================================================================
THE RULE (§C.1)
====================================================================================

    A computational mapping enters this system as a NAME resolved against a registry,
    never as an object supplied by a caller. The engine resolves the name, the engine
    executes the mapping over values the engine released, and no argument exists through
    which a caller's number or a caller's code can reach a dial.

The difference from what stood before is not the strength of a check. **There is nothing
to check, because there is no parameter through which the thing could arrive.**

====================================================================================
NO FIELD ON THIS PATH ACCEPTS A CALLABLE, AND THAT IS A PROPERTY OF THE TYPES
====================================================================================

Every field of :class:`ModelSpec` refuses a callable, and none of them refuses it by
looking for one:

============================  ==========================================================
Field                         Why a callable cannot be stored there
============================  ==========================================================
``model_id``                  :func:`own_model_id` — ``own_str`` rebuilds an exact ``str``
                              from the value's own code points. A callable is not a
                              ``str``; a ``str`` SUBCLASS that is callable is rebuilt as
                              an exact ``str``, which has no ``__call__``
``dial_id``                   the same door, plus membership of ``DIAL_IDS``
``required_input_ids``        every element through ``own_str``
``contributing_input_ids``    every element through ``own_str``
``mapping``                   ``type(x) is not MappingKind`` — an ``Enum`` with members is
                              closed against subclassing BY THE INTERPRETER and members
                              cannot be added after class creation
``parameters``                ``type(x) is not DeclaredParameter``, elementwise
``provenance``                ``type(x) is not ModelProvenance``
============================  ==========================================================

**NONE OF THESE REFUSALS DEPENDS ON A NAME.** Rename every identifier in this module and
every one of them still refuses, because each is a property of the structure — an exact
type comparison, an enum's closed membership, or a value rebuilt from primitives. That is
the test ``CD-PL-F74`` requires be applied to a refusal before it is relied on, and it is
applied here rather than to the auditor's report.

**AND THERE IS NO FIELD LEFT TO PUT AN OBJECT IN.**
``DialSpec.contribution_model`` does not exist. It was not emptied, deprecated or
type-narrowed: the attribute is gone, so ``DialSpec(..., contribution_model=x)`` is a
``TypeError`` from the dataclass constructor itself, and ``spec.contribution_model`` is an
``AttributeError``. Nothing in this package re-exports either deleted name.

====================================================================================
WO-2 REGISTERS ZERO MODELS, AND THAT IS THE DELIVERABLE
====================================================================================

CD-D-005 — which inputs feed a dial, what each stands for, and how they weigh — is the
Product Owner's decision and is owed before WO-3 (BLUEPRINT §16). PID doctrine §3.6 forbids
unexplained mappings. So :data:`EMPTY_MODEL_REGISTRY` ships with zero rows, joining
:data:`~crash_detector.source_registry.EMPTY_SOURCE_REGISTRY`, and both dials read
``Unknown``. That empty state is not an inconvenience: it is what keeps CD-D-005 visibly
owed in code, and it is what makes every planted violation demonstrable without a single
product number existing anywhere.

Registering a row here is a PRODUCT decision (``PBG-AUTH-005``, CD-RULE-003). This module
registers none.

====================================================================================
DECLARED LIMIT (CD-RULE-004). Each hand-off names a layer MEASURED to hold it, or says
NOT PROVED TO BE CARRIED ANYWHERE (CD-RULE-006).
====================================================================================
 1  **``object.__setattr__`` STILL WALKS PAST FROZEN**, here as on every frozen value in
    this repository and in Python. A ``ModelSpec`` validated at construction can have its
    ``mapping``, ``dial_id`` or input tuples overwritten afterwards by code that has already
    chosen to write past the language's own frozen guarantee. This is the same boundary
    :mod:`crash_detector.own_terms` declares as its boundary 4 and
    :mod:`crash_detector.staleness` as its boundary 3, unchanged by this module.

    PARTIALLY CARRIED, AND THE CARRIER IS MEASURED: the dial binding and the declared-input
    invariants are enforced by :func:`establish_model_for_dial`, which is called BOTH at
    ``ConfigSnapshot`` construction AND again at every resolution, so a slot rewritten
    between the two is refused at the second. It is one function called twice, not two
    checks that can come apart. MEASURED — ``tests/test_engine_model_registry.py``
    ``::test_a_dial_id_rewritten_after_snapshot_construction_is_refused_at_resolution``.

    NOT carried for ``ModelSpec.mapping`` rewritten to a NON-member after construction: the
    executor refuses that with a ``TypeError`` at :func:`crash_detector.engine.mapping.compute`
    (MEASURED — ``::test_the_executor_refuses_a_spec_whose_mapping_slot_was_rewritten``), but
    rewritten to ANOTHER member of the enum there is nothing to refuse, because the enum has
    exactly one member and it is the one that refuses. Should a computing member ever be
    added, that route is **NOT PROVED TO BE CARRIED ANYWHERE**.

 2  **THIS MODULE ESTABLISHES A SPEC; IT DOES NOT ESTABLISH THAT THE SPEC IS TRUE.** A
    registry row whose ``ModelProvenance`` misdescribes what its mapping measures gets a
    faithfully validated misdescription. Doctrine §3.6's "no unexplained mappings" is
    served by REQUIRING an account, not by adjudicating one. The adjudication is CD-D-005
    and is the Product Owner's. **NOT PROVED TO BE CARRIED ANYWHERE.**

 3  **A MAPPING MEMBER'S IMPLEMENTATION IS CODE, AND CODE CAN BE WRONG.** This design does
    not make a mapping correct; it makes it **have source** for static analysis to read,
    which is a strictly weaker claim than "cannot happen" and is stated as one in
    BP-AMENDMENT-0001 §E and in BLUEPRINT §17 as CD-BP-002. WO-2 ships no computing member
    at all, so there is no implementation to be wrong yet. **NOT PROVED TO BE CARRIED
    ANYWHERE**, and it is the risk the amendment declines to call a win.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Union

from crash_detector.admission import ESTABLISHED_HERE, admits, one_of
from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.dials.scores import Contribution
from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_float, own_str
from crash_detector.establishment import each_of, establishes

__all__ = [
    "ScoreComputation",
    "ModelId",
    "own_model_id",
    "MappingKind",
    "MAPPING_KIND_NAMES",
    "DeclaredParameter",
    "ModelProvenance",
    "ModelSpec",
    "ModelRegistry",
    "EMPTY_MODEL_REGISTRY",
    "ModelNotRegistered",
    "ModelBoundToAnotherDial",
    "ModelReadsUndeclaredInput",
    "establish_model_for_dial",
]


@establishes(
    magnitude=float,
    contributions=each_of(Contribution, within=(tuple,)),
)
@dataclass(frozen=True)
class ScoreComputation:
    """A magnitude and the named contributions that produced it.

    SURVIVES THIS AMENDMENT UNCHANGED. The contributions are not decoration: BLUEPRINT §7
    requires that every reading be explicable from its stored inputs a year later, without
    archaeology, and that requirement is untouched by who computes the magnitude.

    What changed is only WHO CONSTRUCTS ONE. Before, a caller-supplied object returned it.
    Now the only thing in this package that may return one is
    :func:`crash_detector.engine.mapping.compute`, which is engine-owned and takes no
    caller code.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `ScoreComputation.__new__(ScoreComputation)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("magnitude", "contributions")

    magnitude: float
    contributions: tuple[Contribution, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "contributions", tuple(self.contributions))


#: A model's name.
#:
#: A ``str``, deliberately, and established the way every other id in this codebase is
#: established — through :func:`~crash_detector.own_terms.own_str`, which rebuilds an exact
#: ``str`` from the supplied value's own code points. ``SourceRecord.source_id`` and
#: ``DialSpec.dial_id`` are the same thing and are re-established the same way.
#:
#: **THE ALIAS IS DOCUMENTATION; THE ESTABLISHMENT IS THE REFUSAL.** An annotation asserts
#: nothing at runtime — that is the whole of ``ASR3-F02`` — so nothing here relies on this
#: name. What refuses an object offered as a model reference is :func:`own_model_id`, run
#: inside ``DialSpec.__post_init__``, ``ModelSpec.__post_init__`` and
#: ``ModelRegistry.get``.
ModelId = str


@admits(
    value=ESTABLISHED_HERE(
        "this callable IS the establishment door for a model reference: its contract is to "
        "accept ANY object and refuse it here, naming what was offered. Requiring an exact "
        "str at the door would make it unable to do the one job it exists for, and would "
        "also refuse a str SUBCLASS rather than REBUILDING it, which is the behaviour "
        "crash_detector.own_terms argues for at length and which this function documents. "
        "CARRIER MEASURED, by name: tests/test_engine_model_registry.py::test_p1_the_plant"
        "_adapted_to_the_new_field_is_refused_because_an_object_is_not_a_name and "
        "::test_p1_a_callable_str_subclass_is_rebuilt_as_a_str_that_cannot_be_called."
    )
)
def own_model_id(value: str) -> "ModelId":
    """A model name established on this system's own terms, or a refusal.

    ``own_str`` is the door. It is invoked here rather than open-coded so that a model
    reference is established in exactly one place and so the refusal carries a message
    naming what was actually offered — an object with a ``compute`` method offered as a
    ``model_ref`` is the ``ASR3-F02`` plant arriving one field across, and it should say so
    when it dies.

    A ``str`` SUBCLASS is not refused; it is REBUILT as an exact ``str``, exactly as
    :mod:`crash_detector.own_terms` argues at length. That matters here because the returned
    value is compared for equality against registry rows, and ``__eq__`` on a supplied
    subclass is the subclass's code deciding which model a dial resolved to.
    """
    try:
        established = own_str(value)
    except NotEstablishedOnOwnTerms:
        raise NotEstablishedOnOwnTerms(
            f"a model reference is a NAME, and {type(value).__name__} is not a name. "
            "Models are DATA resolved against the model registry, never objects supplied "
            "by a caller (BP-AMENDMENT-0001 §C.1): there is no field anywhere on the dial "
            "path that holds a model object or a callable."
        ) from None
    if not established:
        raise ValueError(
            "a model reference must be a non-empty name; an empty name resolves to "
            "nothing and would make the registry lookup a formality"
        )
    return established


class MappingKind(Enum):
    """THE CLOSED SET OF WAYS THIS ENGINE MAY TURN A DIAL'S INPUTS INTO ITS MAGNITUDE.

    The :class:`~crash_detector.dials.provenance.SameDialReduction` pattern at the model
    boundary, and for the same structural reason: an :class:`enum.Enum` with members is
    closed against subclassing by the interpreter, and members cannot be added after class
    creation. The set is therefore closed BY THE LANGUAGE rather than by a check that could
    be rewritten, and a value that is not a member cannot be smuggled in as one.

    A caller of :func:`crash_detector.engine.mapping.compute` NAMES a mapping; it does not
    supply one. There is no argument through which a caller's code can arrive, so there is
    nothing for a door to fail to validate.

    **IT SHIPS WITH EXACTLY ONE MEMBER, AND THAT MEMBER COMPUTES NOTHING.**
    Ruled by the Product Owner at PO-DECISIONS-0005 ruling 2, against the PO's own first
    lean — which was an EMPTY enum, the stronger statement — because the full read refuted
    it: the planted violations against ``ConfigSnapshot``'s invariants must CONSTRUCT a
    ``ModelSpec``, and over an empty enum they would die at ``ModelSpec`` construction for a
    reason that is not under test. *A criterion that cannot be demonstrated is a rumour.*

    **A SECOND MEMBER IS A PRODUCT DECISION AND NOT AN IMPLEMENTATION ONE.** The first
    COMPUTING member arrives only with the CD-D-005 register, by amendment to BLUEPRINT
    §16's owed list (PO-DECISIONS-0005 ruling 2, in terms). A seat adding one without that
    register is inventing product meaning (``PBG-AUTH-005``, CD-RULE-003), and CD-HOLD-004
    is held by the Product Authority. Adding one here without also giving it a branch in
    :mod:`crash_detector.engine.mapping` makes that module refuse to import at all — see
    the set-equality assertion there, which is the
    :data:`~crash_detector.dials.provenance.SAME_DIAL_REDUCTIONS` precedent.
    """

    UNSPECIFIED = "unspecified"
    """The ABSENCE of a declared mapping, named.

    It is not a mapping, it is not a default, and it is not a placeholder for one that is
    coming. Its executor branch RAISES
    :exc:`~crash_detector.engine.mapping.UnspecifiedMapping` and returns nothing — no zero,
    no ``None``, no ``Unknown`` manufactured inside the executor. CD-AC-001's failure mode
    is exactly a number standing in for an absence, and an executor answering ``0.0`` here
    would reintroduce it at the one place this amendment concentrates all computation.
    """

    BANDED_WEIGHTED_MEAN = "banded_weighted_mean"
    """THE FIRST COMPUTING MEMBER (WO-1.3, Owner direction 2026-10-11).

    Each input's released ``value`` is scaled onto [0, 1] by a linear band declared as DATA
    (parameters ``calm::<source_id>`` -> 0.0 and ``stress::<source_id>`` -> 1.0, clamped; the
    ORDER of the two encodes the indicator's polarity, so there is no separate sign to
    forget), and the dial magnitude is the weighted mean of those stresses over the inputs
    present (parameters ``weight::<source_id>``). Every contribution is returned by name.

    **EVERY BAND AND WEIGHT IS PROVISIONAL.** Nothing is calibrated; no backtest has been
    run (PO-DECISIONS-0025 r3). The values are carried in ``deploy/indicator-scaling.json``
    with their rationale and travel in the snapshot so a reading can be explained later.
    A mean over the inputs PRESENT is only ever returned as ``Value``/``Degraded`` by
    ``evaluate``, which states the missing inputs; absence is never averaged in as zero.
    """


#: The persisted discriminator values for a model registry row's ``mapping`` column, when
#: deliverable A5's schema reaches it. Derived from the enum rather than restated, so the
#: two cannot disagree.
MAPPING_KIND_NAMES: tuple[str, ...] = tuple(member.value for member in MappingKind)


class ModelNotRegistered(LookupError):
    """A model was named that the registry does not carry.

    Raised rather than answered with a default spec, for the reason
    :exc:`~crash_detector.source_registry.SourceNotRegistered` gives one level down: a
    configuration naming a model nobody registered is a configuration whose dial binding
    and input declarations cannot be checked at all, and answering would hide it.

    **THIS IS THE REFUSAL THAT MAKES THE SHIPPED CONFIGURATION SAFE ON ITS OWN.** With
    :data:`EMPTY_MODEL_REGISTRY` no name resolves, so no ``ModelSpec`` reaches the executor
    by any route whatever, whatever else is true of the ``DialSpec``.
    """


class ModelBoundToAnotherDial(ValueError):
    """A dial named a model that declares it serves the other dial.

    ``ModelSpec.dial_id`` is not decoration: it is the specific structural answer to
    ``ASR3-F02``, whose mechanism was one object placed in BOTH ``DialSpec``s. A registry
    row declares the ONE dial it serves, so there is no row two dials can share, and there
    is no object to place in both because there is no object.
    """


class ModelReadsUndeclaredInput(ValueError):
    """A model declared an input the dial naming it did not declare.

    The same evasion :class:`~crash_detector.source_registry.SourceRegistry`'s first
    invariant closes, one level up: without this, a model reads whatever it likes and the
    dial's declared input set — the set the absence post-condition re-derives its answer
    from — stops describing what the dial actually consumed.
    """


@establishes(
    name=str,
    value=float,
)
@dataclass(frozen=True)
class DeclaredParameter:
    """One configured number a mapping is parameterised by, with the name it is known as.

    **NOT a magnitude and not a dial quantity.** It is deliberately NOT
    :class:`~crash_detector.dials.provenance.DeclaredQuantity`, which is a number that has
    already entered a dial and carries the provenance of the dial it belongs to. This is
    configuration — a threshold, a window, a coefficient — external to the logic
    (``PBG-SEC-001``) and carried in the run-level snapshot so a reading can be explained a
    year later (Standards Baseline §10). The names are close enough to be worth separating
    in writing, which is why this paragraph exists.

    **WO-2 SHIPS NONE.** Every parameter carries product meaning — the relative worth of one
    observation against another, the point at which something counts as a crash — and
    CD-D-005 is owed. A seat writing a value here is inventing a product quantity
    (CD-RULE-003, ``PBG-AUTH-005``). The SHAPE is construction; the CONTENTS are the
    Product Owner's.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `DeclaredParameter.__new__(DeclaredParameter)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("name", "value")

    name: str
    value: float

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "name", own_str(self.name))
        except NotEstablishedOnOwnTerms:
            raise NotEstablishedOnOwnTerms(
                f"DeclaredParameter.name must be a name, got "
                f"{type(self.name).__name__}"
            ) from None
        if not self.name:
            raise ValueError("DeclaredParameter requires a non-empty name")
        try:
            established = own_float(self.value)
        except NotEstablishedOnOwnTerms:
            raise NotEstablishedOnOwnTerms(
                f"DeclaredParameter.value must be a float, got "
                f"{type(self.value).__name__}. It is refused rather than coerced: "
                "float('0') and float(0) both succeed and both would produce a "
                "parameter of zero (Standards Baseline §4)."
            ) from None
        if not math.isfinite(established):
            # NOT a range and NOT a ceiling — no product quantity is chosen here
            # (CD-RULE-003). A NaN parameter compares false against everything including
            # itself and an infinite one abolishes whatever it bounds; neither is a
            # configured number, and refusing them invents nothing.
            raise ValueError(
                f"DeclaredParameter.value must be finite, got {established!r}. A NaN "
                "compares false against everything including itself and an infinity "
                "abolishes whatever it bounds; neither is a configured quantity."
            )
        object.__setattr__(self, "value", established)


@establishes(
    stands_for=str,
    account=str,
    decided_by=str,
)
@dataclass(frozen=True)
class ModelProvenance:
    """WHERE CD-D-005 ATTACHES TO A REGISTRY ROW (§C.6).

    **THE SHAPE IS CONSTRUCTION AND IS THE PROJECT LEAD'S; THE CONTENTS ARE THE PRODUCT
    OWNER'S REGISTER AND ARE NOT INVENTED HERE** (``PBG-AUTH-005``, and §C.6 in terms).
    WO-2 ships zero rows, so zero instances of this type exist in the product.

    Three fields, and the reasoning for each is written out rather than left to be inferred,
    because a provenance shape nobody can populate is as useless as one that asks for
    nothing:

    ``stands_for``
        what this mapping's OUTPUT stands for. The source-level equivalent is
        ``SourceRecord.stands_for``, and this is the same obligation for the thing the
        mapping produces rather than for the things it consumes.

    ``account``
        the account of the mapping that PID doctrine §3.6 requires — *"No unexplained
        mappings. We do not copy a score-to-probability curve we cannot account for."*
        A row that cannot say why these inputs map to this magnitude in this way is exactly
        the thing doctrine §3.6 forbids, and this field is where it must say it.

    ``decided_by``
        the product-authority record that registered the row. Every governed claim on this
        project cites its authority, and a model row is a product decision.

    **WHAT IS DELIBERATELY NOT HERE.** The per-source facts — which source, what IT stands
    for, at what criticality — are NOT copied onto this type. They live in
    :class:`~crash_detector.source_registry.SourceRegistry`, the model names its inputs by
    id, and ``ConfigSnapshot``'s third invariant forces the two to agree. Duplicating them
    here would create two records of one fact that drift apart quietly, which is the defect
    this project has now paid for three times in other forms.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `ModelProvenance.__new__(ModelProvenance)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("stands_for", "account", "decided_by")

    stands_for: str
    account: str
    decided_by: str

    def __post_init__(self) -> None:
        for field_name in ("stands_for", "account", "decided_by"):
            try:
                object.__setattr__(
                    self, field_name, own_str(getattr(self, field_name))
                )
            except NotEstablishedOnOwnTerms:
                raise NotEstablishedOnOwnTerms(
                    f"ModelProvenance.{field_name} must be text, got "
                    f"{type(getattr(self, field_name)).__name__}"
                ) from None
            if not getattr(self, field_name):
                raise ValueError(
                    f"ModelProvenance requires a non-empty {field_name}; an unexplained "
                    "mapping is what PID doctrine §3.6 forbids, and an empty explanation "
                    "is an unexplained mapping with a field for it"
                )


@establishes(
    model_id=str,
    dial_id=str,
    required_input_ids=each_of(str, within=(tuple,)),
    contributing_input_ids=each_of(str, within=(tuple,)),
    mapping=MappingKind,
    parameters=each_of(DeclaredParameter, within=(tuple,)),
    provenance=ModelProvenance,
)
@dataclass(frozen=True)
class ModelSpec:
    """One registered model — one row of the model registry. FROZEN DATA, NO CALLABLES.

    There is no method on this type that computes anything, and there is no field on it
    that can hold code. What it declares is: which dial it serves, which inputs it reads,
    which NAMED mapping the engine is to execute, the configured numbers that mapping is
    parameterised by, and the account of itself that doctrine §3.6 requires.

    **``dial_id`` BINDS THE ROW TO ONE DIAL** (§C.4). This is the structural answer to
    ``ASR3-F02``: a row serves one dial, so no row can be shared by two, and the executor is
    handed one dial's spec and one dial's payloads and holds no state between them. Two rows
    naming the same mapping compute two independent results — there is nothing to blend
    with, because neither has a reference to the other's payloads to close over.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `ModelSpec.__new__(ModelSpec)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("model_id", "dial_id", "required_input_ids", "contributing_input_ids", "mapping", "parameters", "provenance")

    model_id: ModelId
    dial_id: str
    required_input_ids: tuple[str, ...]
    contributing_input_ids: tuple[str, ...]
    mapping: MappingKind
    parameters: tuple[DeclaredParameter, ...]
    provenance: ModelProvenance

    def __post_init__(self) -> None:
        object.__setattr__(self, "model_id", own_model_id(self.model_id))

        # EVERY ID RE-ESTABLISHED BEFORE ANY OF THEM DECIDES ANYTHING (CD-AC-005, Class 2),
        # exactly as `DialSpec` and `SourceRecord` do it. `dial_id` selects the dial this
        # row may serve and is compared against the naming DialSpec's own id; the input ids
        # are compared as SETS against the dial's declared inputs and looked up in the
        # source registry. All of those are the supplied strings' `__eq__` and `__hash__`
        # to answer unless the strings are rebuilt here first.
        try:
            object.__setattr__(self, "dial_id", own_str(self.dial_id))
        except NotEstablishedOnOwnTerms:
            raise ValueError(
                f"unknown dial_id {self.dial_id!r}; the dials are {DIAL_IDS}. A model "
                "serves exactly one dial (BP-AMENDMENT-0001 §C.4)."
            ) from None
        if self.dial_id not in DIAL_IDS:
            raise ValueError(
                f"unknown dial_id {self.dial_id!r}; the dials are {DIAL_IDS}. A model "
                "serves exactly one dial (BP-AMENDMENT-0001 §C.4)."
            )

        for field_name in ("required_input_ids", "contributing_input_ids"):
            try:
                established = tuple(
                    own_str(source_id) for source_id in getattr(self, field_name)
                )
            except NotEstablishedOnOwnTerms:
                raise ValueError(
                    f"ModelSpec.{field_name} must be non-empty source names"
                ) from None
            except TypeError:
                raise TypeError(
                    f"ModelSpec.{field_name} must be a sequence of source names, got "
                    f"{type(getattr(self, field_name)).__name__}"
                ) from None
            object.__setattr__(self, field_name, established)

        for field_name in ("required_input_ids", "contributing_input_ids"):
            ids = getattr(self, field_name)
            if any(not source_id for source_id in ids):
                raise ValueError(f"ModelSpec.{field_name} must be non-empty source names")
            if len(set(ids)) != len(ids):
                raise ValueError(f"ModelSpec.{field_name} contains duplicates")
        overlap = set(self.required_input_ids) & set(self.contributing_input_ids)
        if overlap:
            raise ValueError(
                f"model {self.model_id!r} declares sources as both required and "
                f"contributing: {sorted(overlap)}. A source has one criticality "
                "(BLUEPRINT §5)."
            )

        # THE FIELD THAT WOULD HAVE HELD THE CALLABLE, IF THIS DESIGN HAD ONE.
        # EXACT TYPE, not isinstance: `type(member) is MappingKind` is true of every enum
        # member and false of everything else, including a look-alike carrying a `value`
        # attribute and a `__call__`. An Enum with members cannot be subclassed by the
        # interpreter, so there is no subclass whose membership this could admit.
        if type(self.mapping) is not MappingKind:
            raise TypeError(
                f"ModelSpec.mapping must be a MappingKind member, got "
                f"{type(self.mapping).__name__}. A mapping is a NAME from a closed set "
                "executed by the engine, never a function, a callable or an object "
                "supplied by a caller (BP-AMENDMENT-0001 §C.1). There is no field on this "
                "type that holds code."
            )

        try:
            parameters = tuple(self.parameters)
        except TypeError:
            raise TypeError(
                f"ModelSpec.parameters must be a sequence of DeclaredParameter, got "
                f"{type(self.parameters).__name__}"
            ) from None
        seen_parameters: set[str] = set()
        for parameter in parameters:
            # EXACT TYPE (CD-AC-005, Class 2). A DeclaredParameter subclass may shadow
            # `value` with a property, and a property is the subclass's code running where
            # a configured number is read.
            if type(parameter) is not DeclaredParameter:
                raise TypeError(
                    f"ModelSpec.parameters holds DeclaredParameter, got "
                    f"{type(parameter).__name__}"
                )
            if parameter.name in seen_parameters:
                raise ValueError(
                    f"duplicate parameter {parameter.name!r} on model "
                    f"{self.model_id!r}: two values for one name is two configurations "
                    "for one model"
                )
            seen_parameters.add(parameter.name)
        object.__setattr__(self, "parameters", parameters)

        # EXACT TYPE, for the same reason: a ModelProvenance subclass may shadow `account`
        # with a property, and the account is the whole of what doctrine §3.6 requires a row
        # to carry.
        if type(self.provenance) is not ModelProvenance:
            raise TypeError(
                f"ModelSpec.provenance must be a ModelProvenance, got "
                f"{type(self.provenance).__name__}. Doctrine §3.6 forbids unexplained "
                "mappings, and an account this system did not establish is not an account."
            )


@establishes(
    models=each_of(ModelSpec, within=(tuple,)),
)
@dataclass(frozen=True)
class ModelRegistry:
    """The registered models. Frozen — a change is a new snapshot.

    **A TUPLE OF EXACT-TYPED ROWS, NOT A CALLER-SUPPLIED MAPPING**, and the choice is
    structural rather than stylistic. Holding a ``Mapping`` supplied by a caller would mean
    resolution runs that object's ``__getitem__`` — the caller's code deciding which spec a
    dial resolved to, which is this whole amendment's defect one storey down. It is the same
    reasoning that put :data:`~crash_detector.dials.provenance.SAME_DIAL_REDUCTIONS` behind
    a ``MappingProxyType`` over a dict with no other reference: a door that refuses a
    caller's callable is worth nothing if the caller can write into the table the door
    trusts.

    Frozen for the reason :class:`~crash_detector.source_registry.SourceRegistry` is: the
    registry is carried inside :class:`~crash_detector.engine.config.ConfigSnapshot`, and a
    snapshot that can be mutated after an evaluation cannot explain that evaluation a year
    later.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `ModelRegistry.__new__(ModelRegistry)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("models",)

    models: tuple[ModelSpec, ...]

    def __post_init__(self) -> None:
        try:
            models = tuple(self.models)
        except TypeError:
            raise TypeError(
                f"ModelRegistry.models must be a sequence of ModelSpec, got "
                f"{type(self.models).__name__}"
            ) from None
        object.__setattr__(self, "models", models)
        seen: set[str] = set()
        for model in models:
            # EXACT TYPE, not isinstance (CD-AC-005, Class 2). A ModelSpec subclass may
            # shadow `dial_id`, `mapping` or the input tuples with properties, and every one
            # of those is read inside an invariant that decides what a dial may compute.
            if type(model) is not ModelSpec:
                raise TypeError(
                    f"ModelRegistry holds ModelSpec, got {type(model).__name__}"
                )
            if model.model_id in seen:
                raise ValueError(
                    f"duplicate model_id in registry: {model.model_id!r}. Two rows for "
                    "one name is two mappings for one name, and which one a dial resolved "
                    "to would depend on iteration order."
                )
            seen.add(model.model_id)

    @property
    def is_empty(self) -> bool:
        """True when no model is registered — the WO-2 shipped state."""
        return not self.models

    @property
    def model_ids(self) -> tuple[str, ...]:
        return tuple(model.model_id for model in self.models)

    @admits(
        model_id=ESTABLISHED_HERE(
            "own_model_id below IS the establishment door for this parameter and it "
            "REBUILDS a str subclass rather than refusing it, deliberately, so that which "
            "row a lookup matches is decided by str.__eq__ between two exact strings. "
            "Requiring an exact str here would refuse what this registry is designed to "
            "re-establish, and would move the refusal off own_model_id, which is where "
            "every model reference in the product is established. CARRIER MEASURED, by "
            "name: tests/test_engine_model_registry.py::test_p1_a_callable_str_subclass_is"
            "_rebuilt_as_a_str_that_cannot_be_called and "
            "::test_the_model_registry_refuses_a_row_that_is_not_exactly_a_modelspec."
        )
    )
    def get(self, model_id: str) -> ModelSpec:
        """The spec for ``model_id``, or :exc:`ModelNotRegistered`.

        Deliberately no ``default`` parameter and no ``default`` behaviour, for the reason
        :meth:`~crash_detector.source_registry.SourceRegistry.get` gives: a caller asking
        about a model nobody registered has a defect, and answering would hide it.

        The name is re-established before it is compared, so which row a lookup matches is
        decided by ``str.__eq__`` between two exact strings and never by a supplied
        subclass's ``__eq__``.
        """
        wanted = own_model_id(model_id)
        for model in self.models:
            if model.model_id == wanted:
                return model
        raise ModelNotRegistered(
            f"model not registered: {wanted!r}. Registered models are "
            f"{list(self.model_ids)} — WO-2 ships EMPTY_MODEL_REGISTRY, zero rows, "
            "because CD-D-005 is owed by the Product Owner (BLUEPRINT §16)."
        )


#: The registry WO-2 ships. Zero rows, joining
#: :data:`~crash_detector.source_registry.EMPTY_SOURCE_REGISTRY`.
#:
#: CD-D-005 is owed by the Product Owner before WO-3; until then a populated registry would
#: be invented product meaning (``PBG-AUTH-005``, CD-RULE-003). With no model registered no
#: ``model_ref`` resolves, so no ``ModelSpec`` reaches the executor at all — the shipped
#: configuration is safe by having nothing in it, and every planted violation below is
#: demonstrated against exactly this registry.
EMPTY_MODEL_REGISTRY = ModelRegistry(models=())


@admits(
    model_registry=ModelRegistry,
    dial_id=str,
    model_ref=one_of(str, None),
    required_input_ids=tuple,
    contributing_input_ids=tuple,
)
def establish_model_for_dial(
    model_registry: "ModelRegistry",
    *,
    dial_id: str,
    model_ref: "Union[ModelId, None]",
    required_input_ids: tuple[str, ...],
    contributing_input_ids: tuple[str, ...],
) -> "Union[ModelSpec, None]":
    """Resolve ``model_ref`` and hold §C.5's three invariants over the result.

    **ONE FUNCTION, CALLED FROM TWO PLACES, AND THAT IS THE POINT.**
    :meth:`~crash_detector.engine.config.ConfigSnapshot.__post_init__` calls it so an
    incoherent configuration is refused before any evaluation runs, and
    :meth:`~crash_detector.engine.config.ConfigSnapshot.model_for` calls it again at every
    resolution so a slot rewritten past ``frozen`` after construction is refused at the
    second reading. Two independently written checks would be an enumeration, and
    enumerations come apart — that is the reasoning
    :class:`~crash_detector.staleness.StalenessWindow` already applies to the two staleness
    comparison sites, read here.

    The three invariants (§C.5), in the order the interpreter reaches them:

    1. **every ``model_ref`` a dial names must RESOLVE** in the registry. Under
       :data:`EMPTY_MODEL_REGISTRY` nothing resolves, which is why the shipped
       configuration cannot reach the executor by any route;
    2. **a resolved spec's ``dial_id`` must EQUAL the dial naming it.** This is §C.4 —
       one model serves one dial — and it is the refusal ``ASR3-F02``'s cross-dial
       mechanism now meets;
    3. **a resolved spec's input ids must be a SUBSET of the naming dial's declared
       inputs**, per set, so a model may not read an input its dial did not declare, and may
       not silently promote a contributing input to required. The registry criticality
       agreement is asserted by the caller against the same ids, using
       :class:`~crash_detector.source_registry.SourceRegistry`'s own contract rather than a
       second copy of it.

    Returns ``None`` when the dial names no model, which is the WO-2 shipped state of both
    dials and is not an error.
    """
    if type(model_registry) is not ModelRegistry:
        raise TypeError(
            "the model registry must be a ModelRegistry, got "
            f"{type(model_registry).__name__}. Pass EMPTY_MODEL_REGISTRY explicitly for "
            "the WO-2 state; there is no default, because a registry nobody chose is not "
            "evidence of anything."
        )
    if model_ref is None:
        return None

    # INVARIANT 1 — it must resolve. `get` re-establishes the name before comparing.
    model = model_registry.get(model_ref)

    # INVARIANT 2 — the row declares the one dial it serves.
    if model.dial_id != own_str(dial_id):
        raise ModelBoundToAnotherDial(
            f"dial {dial_id!r} names model {model.model_id!r}, which declares it serves "
            f"dial {model.dial_id!r}. A model serves EXACTLY ONE dial "
            "(BP-AMENDMENT-0001 §C.4): the cross-dial route ASR3-F02 used was one stateful "
            "object placed in BOTH dial specs, and after this amendment there is no object "
            "to place and no row two dials may share."
        )

    # INVARIANT 3 — subset, per set, so criticality cannot be laundered by moving an id.
    undeclared_required = set(model.required_input_ids) - set(required_input_ids)
    undeclared_contributing = set(model.contributing_input_ids) - set(
        contributing_input_ids
    )
    if undeclared_required or undeclared_contributing:
        raise ModelReadsUndeclaredInput(
            f"model {model.model_id!r} reads inputs dial {dial_id!r} did not declare: "
            f"required {sorted(undeclared_required)}, contributing "
            f"{sorted(undeclared_contributing)}. The dial declares required "
            f"{list(required_input_ids)} and contributing {list(contributing_input_ids)}. "
            "A model may not read an input its dial did not declare, and may not name as "
            "required an input the dial declared as contributing: the dial's declared set "
            "is what the absence post-condition re-derives its answer from, so a model "
            "reading outside it would make that answer describe something other than what "
            "the dial consumed."
        )
    return model
