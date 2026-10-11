"""THE EXECUTOR — the one place in this product where a dial magnitude is computed.

BP-AMENDMENT-0001 §C.2, in force::

    compute(spec: ModelSpec, payloads) -> ScoreComputation

It dispatches on ``spec.mapping`` — a member of a closed enum, a NAME — over payload values
the engine released, and returns a magnitude the engine then stamps with the dial's
provenance at the existing single admission site in
:mod:`crash_detector.engine.evaluate`.

====================================================================================
WHY THIS MODULE EXISTS AT ALL
====================================================================================

Before this amendment the equivalent line was ``spec.contribution_model.compute(payloads)``:
a call on an object the CALLER put in the ``DialSpec``. The number it returned was a number
this system did not compute, and no layer downstream could tell such a number from a
measurement — which is precisely how ``ASR3-F02`` published an equity 0.5 out of an equity
0.9 and a monetary 0.1 with every static layer green.

The repair is this codebase's own, taken from
:func:`~crash_detector.dials.magnitude.combine_within_one_dial`: **delete the callable and
replace it with a name from a closed set, executed by the module that owns the numbers.**
This module is that module for the model boundary.

====================================================================================
THREE PROPERTIES THIS FUNCTION HOLDS, AND EACH IS STRUCTURAL
====================================================================================

**1. IT TAKES NO CODE.** ``spec`` is exact-typed
:class:`~crash_detector.engine.model.ModelSpec` — frozen data with no callable-typed field —
and ``payloads`` is rebuilt here as a plain ``dict`` of plain ``dict``s keyed by names this
module established. There is no parameter through which a caller's function can arrive, so
there is nothing for a door to fail to validate.

**2. IT HOLDS NO STATE, BETWEEN DIALS OR BETWEEN RUNS.** It is a module-level function of
its arguments with no module-level mutable binding of any kind. ``ASR3-F02``'s mechanism was
one *stateful* object seeing both dials in turn; this function has no memory to put the
first dial's figures in, and no reference to the other dial's payloads to close over.

**3. IT CANNOT SPAN TWO DIALS.** Its arguments are ONE dial's spec and ONE dial's payloads.
:attr:`~crash_detector.engine.model.ModelSpec.dial_id` binds the row to one dial and
:func:`~crash_detector.engine.model.establish_model_for_dial` refuses a row named by the
other one, at snapshot construction and again at resolution. Two rows naming the same
mapping compute two independent results — there is nothing to blend with.

====================================================================================
THE ONE MEMBER, AND WHY IT REFUSES
====================================================================================

:class:`~crash_detector.engine.model.MappingKind` ships with exactly one member,
``UNSPECIFIED``, which names the ABSENCE of a declared mapping. Its branch below **RAISES
:exc:`UnspecifiedMapping` AND RETURNS NOTHING** — no zero, no ``None``, no ``Unknown``
manufactured inside the executor, no ``else`` and no fallthrough. Ruled by the Product Owner
at PO-DECISIONS-0005 ruling 2, and the reason is CD-AC-001 itself: a number standing in for
an absence is the failure mode this whole product exists to refuse, and an executor
answering ``0.0`` here would reintroduce it at the one place this amendment concentrates all
computation.

**THE FIRST COMPUTING MEMBER ARRIVES ONLY WITH THE CD-D-005 REGISTER**, by amendment to
BLUEPRINT §16's owed list. Until then this function computes nothing, and that is the
deliverable rather than a gap.

====================================================================================
DECLARED LIMIT (CD-RULE-004). Each hand-off names a layer MEASURED to hold it, or says
NOT PROVED TO BE CARRIED ANYWHERE (CD-RULE-006).
====================================================================================
 1  **THIS FUNCTION ESTABLISHES THE SHAPE OF A PAYLOAD, NOT THE TRUTH OF ITS CONTENTS.**
    Payload keys are rebuilt through :func:`~crash_detector.own_terms.own_str` and the
    mappings are copied into ``dict``s this module built, so no supplied object's
    ``__getitem__``, ``__eq__``, ``__hash__`` or ``keys`` runs while a mapping is executed.
    The VALUES inside a payload are external observation data, believed as data exactly as
    :mod:`crash_detector.own_terms` boundary 3 describes. Source trust is a different
    problem with a different instrument (BLUEPRINT §5, CD-D-005). **NOT PROVED TO BE CARRIED
    ANYWHERE.**

 2  **A MAPPING MEMBER'S IMPLEMENTATION IS CODE, AND CODE CAN BE WRONG.** A ``MEAN`` that is
    not a mean is a defect this architecture does not prevent — it makes it *have source*
    for static analysis to read, which is strictly weaker than "cannot happen". Stated as a
    risk and not as a win, per BP-AMENDMENT-0001 §E and BLUEPRINT §17's **CD-BP-002**: this
    function is now the single highest-value target in the product, and that concentration
    is deliberate — one place with source beats seven doors without. WO-2 ships no computing
    member at all, so there is no implementation to be wrong yet. **NOT PROVED TO BE CARRIED
    ANYWHERE.**

 3  **SUPERSEDED AT WO-2R3 INCREMENT 2 — THE CARRIER IS NOW BUILT AND IS NOW MEASURED.**
    This limit read, at increment 1: *"THIS DOOR IS EXACT-TYPED IN ITS BODY, NOT YET DERIVED
    FROM ITS SIGNATURE … THE CARRIER IS NOT YET BUILT AND IS NOT CLAIMED: NOT PROVED TO BE
    CARRIED ANYWHERE."* It is corrected here rather than deleted, because a declaration that
    was true and has been made false by a later closure is part of the record
    (CD-RULE-004, and corrections supersede rather than edit).

    :func:`compute` now carries ``@admits(spec=ModelSpec, payloads=dict)``, applied at the
    boundary and derived from its own signature by :mod:`crash_detector.admission`, so the
    establishment no longer depends on this body. The body's own exact-type refusals are
    KEPT — deleting a guard to make a closure look tidier is exactly the move this project
    forbids — and they are now the second of two independent refusals rather than the only
    one. **CARRIER MEASURED:** ``tools/register/check_judgement_path_doors.py`` enumerates
    the judgement-path doors FROM THE ARTEFACT and fails if this one is not decorated;
    ``tests/test_judgement_path_doors.py`` runs both its arms. THIS FUNCTION IS THE REASON
    THE CHECK DERIVES ITS SUBJECT FROM THE ARTEFACT AND NOT FROM A LIST (CD-D-098): it was
    created by increment 1 and therefore post-dates §B's measured inventory of 44 doors, so
    a check enumerating that list would not have looked at it.

    WHAT IS STILL NOT CARRIED, stated so the correction does not read as a clean sweep: the
    ``admits`` door establishes that ``spec`` is exactly a ``ModelSpec``. It does not
    establish that ``spec.mapping`` still holds a ``MappingKind`` member at the moment it
    selects a branch — ``object.__setattr__`` walks past ``frozen`` on every frozen value in
    Python — and THAT refusal is the body's, below, and remains the body's. **NOT PROVED TO
    BE CARRIED ANYWHERE.**

    What depends on neither, and is the §C claim: there is no field on ``ModelSpec`` or
    ``DialSpec`` that holds code, so even with every line below deleted and the decorator
    removed, ``compute`` has no caller-supplied callable to execute. The refusals bound what
    a MALFORMED spec can do here; they are not what stops a model object arriving.
"""

from __future__ import annotations

import math

from crash_detector.admission import admits
from crash_detector.dials.scores import Contribution
from crash_detector.engine.model import (
    MappingKind,
    ModelSpec,
    ScoreComputation,
)
from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str

__all__ = ["UnspecifiedMapping", "MAPPINGS_WITH_AN_EXECUTOR_BRANCH", "compute"]


class UnspecifiedMapping(Exception):
    """A model whose mapping names the ABSENCE of a mapping reached the executor.

    A NAMED error, per PO-DECISIONS-0005 ruling 2, and it carries NO magnitude — there is no
    attribute on it holding a number and no code path below returns one. A caller catching
    it has caught a refusal, not a result.

    It is deliberately not a ``ValueError`` or a ``LookupError``. The spec is well-formed and
    the model is registered; what is absent is a mapping to run, and collapsing that into an
    existing exception class would let a caller's ``except ValueError`` swallow it beside a
    genuinely bad value. *Cannot determine* and *determined to be absent* lead to different
    actions and collapsing them is how a check comes to report success it never established
    (Standards Baseline §8).
    """


#: Every :class:`~crash_detector.engine.model.MappingKind` member that has a branch in
#: :func:`compute`, asserted by set EQUALITY against the enum at import, in both directions.
#:
#: **THIS IS THE** :data:`~crash_detector.dials.provenance.SAME_DIAL_REDUCTIONS` **PRECEDENT,
#: AND IT IS WHAT MAKES "NO FALLTHROUGH" A PROPERTY OF THE MODULE RATHER THAN OF THIS
#: SEAT'S CARE.** A member added to the enum without a branch here makes this module refuse
#: to IMPORT — so the engine does not start, rather than starting and reaching the end of
#: :func:`compute` with nothing to do. A branch here naming a member the enum does not
#: declare is the same failure read from the other side.
#:
#: A ``frozenset`` and not a list: membership is what is asserted, and order is not a
#: property of an enum's branches.
MAPPINGS_WITH_AN_EXECUTOR_BRANCH = frozenset(
    {MappingKind.UNSPECIFIED, MappingKind.BANDED_WEIGHTED_MEAN}
)

if MAPPINGS_WITH_AN_EXECUTOR_BRANCH != frozenset(MappingKind):
    raise AssertionError(
        "MAPPINGS_WITH_AN_EXECUTOR_BRANCH and MappingKind disagree about which mappings "
        "this engine can execute. The two are asserted by set equality because a declared "
        "member with no branch would fall out of the bottom of compute() at the worst "
        f"possible moment, and a branch with no member would be a mapping nobody declared. "
        f"Declared: {sorted(m.value for m in MappingKind)}; branched: "
        f"{sorted(m.value for m in MAPPINGS_WITH_AN_EXECUTOR_BRANCH)}."
    )


def _payloads_the_engine_released(payloads: object) -> dict:
    """The payloads, rebuilt as plain ``dict``s keyed by names this module established.

    ``evaluate`` builds the argument from ``OK.payload`` values it selected, so in the
    product this is a copy of something already ours. It is rebuilt anyway, and the reason
    is the one :mod:`crash_detector.own_terms` gives at length: the moment a judgement is
    made by calling a method on a supplied object, the supplier makes the judgement. Here
    the judgements are which source ids are present and which payload a source id maps to,
    and both are the supplied mapping's ``__getitem__``, ``keys`` and ``__eq__`` to answer
    unless the mapping is rebuilt first.

    Exact ``dict`` rather than ``Mapping``, at both levels, for the same reason
    :class:`~crash_detector.staleness.StalenessWindow` refuses a ``float`` subclass: this is
    an internal hand-off between two engine modules, so refusing outright costs the product
    nothing and closes the route completely.
    """
    if type(payloads) is not dict:
        raise TypeError(
            f"compute() takes payloads as a dict keyed by source id, got "
            f"{type(payloads).__name__}. A supplied mapping decides its own lookups, and "
            "which payload a source id maps to is not a supplied object's judgement to "
            "make."
        )
    established: dict = {}
    for source_id, payload in payloads.items():
        try:
            name = own_str(source_id)
        except NotEstablishedOnOwnTerms:
            raise NotEstablishedOnOwnTerms(
                f"a payload key must be a source id, got {type(source_id).__name__}"
            ) from None
        if type(payload) is not dict:
            raise TypeError(
                f"the payload for source {name!r} must be a dict, got "
                f"{type(payload).__name__}"
            )
        established[name] = dict(payload)
    return established


def _finite_number(owner: str, value: object) -> float:
    if type(value) is bool or type(value) not in (int, float):
        raise TypeError(
            f"{owner} must be a plain number, got {type(value).__name__}. A token, a string "
            "or a missing value is not a measurement and is never coerced into one."
        )
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{owner} must be finite, got {number!r}")
    return number


@admits(spec=ModelSpec, released=dict)
def _banded_weighted_mean(spec: ModelSpec, released: dict) -> ScoreComputation:
    """The ``BANDED_WEIGHTED_MEAN`` executor. See :class:`MappingKind` for the definition.

    Raises (never returns a number) when an input has no declared band/weight, a band has no
    span, a weight is not positive, or a payload's ``value`` is not a finite plain number.
    With no inputs at all it raises rather than answering 0.0: ``evaluate`` never calls it
    without at least the dial's required inputs, and an empty mean is not a score.
    """
    parameters = {parameter.name: parameter.value for parameter in spec.parameters}
    if not released:
        raise ValueError(f"model {spec.model_id!r} was handed no inputs; an empty mean is not a score")
    total_weight = 0.0
    weighted = 0.0
    contributions = []
    for source_id in sorted(released):
        try:
            calm = parameters[f"calm::{source_id}"]
            stress = parameters[f"stress::{source_id}"]
            weight = parameters[f"weight::{source_id}"]
        except KeyError as missing:
            raise ValueError(
                f"model {spec.model_id!r} has no declared parameter {missing.args[0]!r} for "
                f"input {source_id!r}: an input without a band is not scored, it is refused"
            ) from None
        if stress == calm:
            raise ValueError(f"input {source_id!r} declares a band with no span")
        if weight <= 0.0:
            raise ValueError(f"input {source_id!r} declares a non-positive weight")
        value = _finite_number(f"payload value of {source_id!r}", released[source_id].get("value"))
        scaled = (value - calm) / (stress - calm)
        scaled = 0.0 if scaled < 0.0 else 1.0 if scaled > 1.0 else scaled
        total_weight += weight
        weighted += weight * scaled
        contributions.append(
            Contribution(source_id=source_id, category="banded_indicator", weight=weight, contribution=scaled)
        )
    return ScoreComputation(magnitude=weighted / total_weight, contributions=tuple(contributions))


@admits(spec=ModelSpec, payloads=dict)
def compute(spec: ModelSpec, payloads: dict) -> ScoreComputation:
    """Execute ``spec``'s NAMED mapping over ``payloads`` and return the computation.

    One dial's spec, one dial's payloads. No state is held between calls, between dials or
    between runs.

    :raises TypeError: if ``spec`` is not exactly a
        :class:`~crash_detector.engine.model.ModelSpec`, if its ``mapping`` slot does not
        hold a :class:`~crash_detector.engine.model.MappingKind` member, or if the payloads
        are not a ``dict`` of ``dict``s keyed by source names.
    :raises UnspecifiedMapping: if the spec's mapping names the absence of a mapping. **No
        magnitude is returned on that path, and there is no branch below it.**
    """
    # EXACT TYPE, not isinstance (CD-AC-005, Class 2). A ModelSpec subclass may shadow
    # `mapping` with a property, and a property is the subclass's code choosing which branch
    # of this executor runs — which is a caller supplying code to the one place in the
    # product that computes a dial magnitude, reached without any field ever having held it.
    if type(spec) is not ModelSpec:
        raise TypeError(
            f"compute() takes a ModelSpec, got {type(spec).__name__}. Models are DATA "
            "resolved by the engine against the registry, never objects accepted from "
            "callers (BP-AMENDMENT-0001 §C.1)."
        )
    # The slot, not the constructor. `ModelSpec.__post_init__` already established this, and
    # `object.__setattr__` walks past `frozen` on this type as on every frozen value in
    # Python — so the value is read as it stands NOW, at the moment it selects a branch,
    # rather than as it stood when the row was built.
    if type(spec.mapping) is not MappingKind:
        raise TypeError(
            f"model {spec.model_id!r} carries {type(spec.mapping).__name__} where a "
            "MappingKind member belongs. A mapping is a NAME from a closed set executed by "
            "this module, and this executor dispatches on nothing else."
        )

    released = _payloads_the_engine_released(payloads)

    if spec.mapping is MappingKind.UNSPECIFIED:
        raise UnspecifiedMapping(
            f"model {spec.model_id!r} for dial {spec.dial_id!r} declares "
            f"MappingKind.UNSPECIFIED over inputs {sorted(released)}, which NAMES THE "
            "ABSENCE of a declared mapping. There is nothing to execute and NOTHING IS "
            "RETURNED: not a zero, not a None and not an Unknown manufactured here. A "
            "number standing in for an absence is CD-AC-001's failure mode, and this is "
            "the one place in the product a dial magnitude is computed. The first "
            "COMPUTING mapping arrives only with the CD-D-005 register (BLUEPRINT §16, "
            "PO-DECISIONS-0005 ruling 2)."
        )

    if spec.mapping is MappingKind.BANDED_WEIGHTED_MEAN:
        return _banded_weighted_mean(spec, released)

    # NO `else`, NO FALLTHROUGH, AND NO RETURN. Reaching this line would require a
    # MappingKind member with no branch above, and MAPPINGS_WITH_AN_EXECUTOR_BRANCH is
    # asserted equal to the enum at import — so a member added without a branch stops this
    # module importing rather than arriving here. There is deliberately no `raise` here
    # either: a catch-all at the bottom would be a place for a future edit to put a return.
