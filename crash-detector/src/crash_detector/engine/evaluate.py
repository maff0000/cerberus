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

====================================================================================
THE ABSENCE POST-CONDITION — added closing CD-ASR-F03 (MEDIUM)
====================================================================================

The four rules above were written down, implemented, and defeated. An independent auditor
replaced the ``missing_required`` branch of :func:`_evaluate_dial` with
``Value(value=<ScoreType>(score=QUIET_MAGNITUDE, ...))`` where ``QUIET_MAGNITUDE = 0.0``
was a module-level constant (`CD-ASR-F03`, escaped variant `E04`). The AST guard enumerated
four spellings of a numeric default and this was a fifth, so it saw nothing.

The lesson is that the rules were a property of *how this function happened to be written*,
and a rule that lives in a function body is rewritten by editing the function body. So the
rules are now enforced from **outside** the body, as a post-condition:
:func:`refuse_a_number_without_its_inputs` re-derives from ``(spec, usable)`` — the
function's own arguments, not its internal state — whether this dial actually got its
required inputs, and refuses the returned reading if it carries a value when it did not.

That is what makes the closure a CLASS closure rather than a fifth spelling caught. The
post-condition never asks where the number came from, so it does not care: a literal, a
module constant, a configuration default, a previous value carried across a gap, a random
number, a value read from the database — all of them raise
:exc:`~crash_detector.dials.reading.AbsenceYieldedAValue`, because what is refused is the
*claim* rather than the *arithmetic*. A reading that carries a value is a claim that inputs
were present; the post-condition checks the claim against the inputs.

It is deliberately one-directional. A body that returns ``Unknown`` when the inputs WERE
present is not refused: that is the safe direction, and a guard that compelled a number
would be pushing the wrong way.

====================================================================================
THE POST-CONDITION IS ALSO A DOOR NOW (PO-DECISIONS-0015 RULING 1, in force)
====================================================================================

``PO-DECISIONS-0012`` ruling 1 held that :func:`_evaluate_dial` was *"reachable only through
doors that already establish"* and made that the reason the guard was a NET rather than a
DOOR. **THE LOAD-BEARING HALF WAS FALSIFIED BY MEASUREMENT TWICE INDEPENDENTLY** — a
conforming, declared-foreign ``SourceAdapter`` obtains this module from ``sys.modules`` on the
second collection cycle and reaches the UNDECORATED evaluator through ``__closure__``, passing
no door. The ruling fell on its own pre-committed terms.

So ``guarded`` is a DOOR: it establishes every argument by exact type, DERIVED FROM
:func:`_evaluate_dial`'s own signature, before the body binds — and it is still the
CD-ASR-F03 net, in the same wrapper and the same closure, because *"the guard and the guarded
are inseparable"* is a statement about object identity. The body is carried as a ``code``
object, so nothing callable survives for the attack to find.

====================================================================================
DECLARED LIMIT (CD-RULE-004), in this header, in required-tests.yaml and in
contracts/execution/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.md, each with an executable example.
CD-RULE-006: each hand-off names a layer MEASURED to carry it, or says NOT PROVED TO BE
CARRIED ANYWHERE.

**THE NUMBERING RUNS AS ONE SEQUENCE ACROSS THREE HEADERS AND NOT THREE LISTS.** Limits 1-4
and 7-9 are the static check's and live in ``tools/register/check_judgement_path_doors.py``;
5-6 are ``admits``'s and live in ``src/crash_detector/admission.py``; **10 and 11 are THIS
MECHANISM'S and are new at WO-2R3 increment 8.** An auditor who reads only one header has
read part of what this row declares open — which is CD-PL-F81's finding, ruled CD-D-111, and
this header is the third place it now applies to.
====================================================================================

10  **THE BODY CAN BE RECONSTITUTED FROM ITS CODE OBJECT, AND THAT IS A REACH THIS DESIGN
    RAISES THE COST OF RATHER THAN CLOSES.**

    Property (a) of ``PO-DECISIONS-0015`` ruling 1 is met AS THE RULING STATES IT: after
    :func:`_absence_is_never_a_number` returns, **no undecorated evaluator OBJECT exists** —
    every cell of ``_evaluate_dial.__closure__`` holds data, ``__wrapped__`` is never created,
    ``__globals__`` and the module namespace hold no second form of the evaluator, and the
    walk that finds them finds nothing callable. **THAT IS NOT THE SAME CLAIM AS "THE
    ``__closure__`` REACH IS CLOSED", AND THIS LIMIT EXISTS SO NOBODY READS IT AS ONE.**

    Anything that can read the cells can also write::

        cells   = [c.cell_contents for c in evaluate._evaluate_dial.__closure__]
        code    = next(c for c in cells if isinstance(c, types.CodeType))
        globals_ = next(c for c in cells if isinstance(c, dict) and "Value" in c)
        body    = types.FunctionType(code, globals_)     # a callable body again
        body(starved_spec, {}, now, None)                # no door, no post-condition

    **MEASURED, AND ASSERTED TRUE RATHER THAN DESCRIBED**:
    ``tests/test_the_absence_door.py::test_the_reconstitution_residue_is_real_and_is_declared_limit_10``
    performs exactly that and requires it to SUCCEED, so this paragraph cannot go stale in
    the reassuring direction — the day the reconstitution stops working, that test goes red
    and this limit is corrected in all three places rather than quietly enjoyed. It is the
    same discipline the superseded closure assertion in ``tests/test_evaluate.py`` carried,
    and that assertion is why anyone could tell the closure route had closed.

    **WHAT ACTUALLY CHANGED, STATED WITHOUT DECORATION.** Before: the cell HELD the callable
    and one attribute access reached it. Now: the cell holds materials and an attacker must
    CONSTRUCT a callable from them. The reach is the same reach; the cost is one line of
    interpreter-internals work instead of none, and the property the ruling names — that no
    such object EXISTS — is what holds. **CARRIER for preventing the reconstitution itself:
    NOT PROVED TO BE CARRIED ANYWHERE**, and CPython offers no way to prevent it, exactly as
    ``admission.py``'s DECLARED LIMIT 6 (a) says of the closure reach generally.

11  **THE DERIVATION DROPS A GENERIC'S SUBSCRIPT, SO A CONTAINER'S ELEMENTS ARE NOT
    ESTABLISHED AT THIS DOOR.**

    ``usable: dict[str, OK]`` is derived to ``_Exactly((dict,))``: the argument must be
    EXACTLY a ``dict`` and this door says nothing about its keys or its values. Executable
    example — ``_evaluate_dial(spec, {"src.a": object()}, now)`` passes this door, and what
    refuses it, if anything does, is somewhere else.

    **CARRIER MEASURED, and it is one level up:** :func:`_latest_usable_ok` builds the only
    ``usable`` any product caller supplies, and it admits an outcome only when
    ``type(outcome) is OK``. On the product path the elements are therefore established at
    construction. **FOR A DIRECT CALLER SUPPLYING ITS OWN ``dict``: NOT PROVED TO BE CARRIED
    ANYWHERE** — the post-condition re-derives from ``spec`` and from the KEYS of ``usable``
    only, so a dict whose values are not ``OK`` reaches the body. This is
    ``crash_detector.admission``'s DECLARED LIMIT 4 (*a container's elements are established
    when the door is called, not afterwards*) met from the other side: here they are not
    established at the door at all.

    **AND THE ANNOTATION CHANGE THIS LIMIT SITS ON IS DECLARED RATHER THAN INHERITED**
    (``CD-PL-F109``). :func:`_evaluate_dial`'s ``usable`` moved ``Mapping[str, OK]`` ->
    ``dict[str, OK]`` because the establishment is now derived from that annotation and an
    abstract ``Mapping`` has no exact type to derive. **IT IS NOT A NARROWING OF WHAT THE
    PRODUCT ACCEPTS, AND THAT IS MEASURED AND NOT ARGUED**: at the base commit a
    ``collections.abc.Mapping`` that is not a ``dict`` was ALREADY refused with
    ``NotAdmitted`` — by :func:`refuse_a_number_without_its_inputs`, whose ``@admits``
    declared ``usable=dict`` and fired on every call — and it is refused with ``NotAdmitted``
    here too. **THE ACCEPTED SET IS IDENTICAL; ONLY THE POINT OF REFUSAL MOVES**, from after
    the body has run to before it binds. Two arms, one axis, both trees, in the Build Log
    entry for this increment.

====================================================================================
THE MODEL DOOR IS GONE (BP-AMENDMENT-0001 §C, in force)
====================================================================================

Until this commit the line below the payload assembly read::

    computation = spec.contribution_model.compute(payloads)

— a call on an object the CALLER had put in the ``DialSpec``. That is the line ``ASR3-F02``
published a laundered number through, and it **does not exist any more**. Not because it was
deleted: because there is no attribute on ``DialSpec`` holding an object, so there is no
expression that could be written there.

What stands in its place calls one engine-owned function,
:func:`crash_detector.engine.mapping.compute`, over a spec the engine RESOLVED from a name
and payloads the engine RELEASED. The consequence for this module's own headline claim is
that ``evaluate``'s purity got STRONGER, and the old caveat is withdrawn rather than
softened: there is no longer any object a caller can supply whose ``compute`` could perform
I/O, read a clock or hold state between the two dials, because there is no such parameter
and no such field.
"""

from __future__ import annotations

import inspect
import types
import typing
from datetime import datetime
from typing import Mapping, Sequence, Union

from crash_detector.admission import (
    ADMITS_ATTRIBUTE,
    FAULTS_ATTRIBUTE,
    AdmissionFault,
    NotAdmitted,
    admits,
    declaration,
    is_exactly,
    each_of,
    one_of,
)
from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID, DialSet
from crash_detector.dials.reading import (
    READING_CONSTRUCTORS,
    AbsenceYieldedAValue,
    Degraded,
    Reading,
    Unknown,
    Value,
)
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.provenance import observed_for_dial
from crash_detector.dials.scores import EquityCrashScore, MonetaryDebasementScore
from crash_detector.engine.config import ConfigSnapshot, DialSpec
from crash_detector.engine.mapping import compute
from crash_detector.engine.model import ModelSpec
from crash_detector.observations import OK, ObservationRecord
from crash_detector.staleness import StalenessWindow
from crash_detector.time_utc import age_seconds, ensure_utc

__all__ = [
    "evaluate",
    "DIAL_SCORE_TYPES",
    "REASON_NO_REQUIRED_INPUTS",
    "REASON_REQUIRED_INPUTS_UNAVAILABLE",
    "REASON_CONTRIBUTING_INPUTS_UNAVAILABLE",
    "REASON_NO_MODEL_DECLARED",
    "READINGS_THAT_CARRY_A_VALUE",
    "required_inputs_are_all_present",
    "refuse_a_number_without_its_inputs",
]

#: The two Reading constructors that carry a value, named as data. A reading of one of
#: these types is a CLAIM that this dial's inputs were present; the post-condition below
#: checks that claim against the inputs the dial was actually given.
READINGS_THAT_CARRY_A_VALUE: tuple[type, ...] = (Value, Degraded)

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
#: RENAMED at BP-AMENDMENT-0001 §C from ``REASON_NO_CONTRIBUTION_MODEL``
#: (``"NO_CONTRIBUTION_MODEL_DECLARED"``), because the type it named is deleted. The
#: PROPOSITION is unchanged — a dial that names no mapping is Unknown for that stated
#: reason. Nothing outside this module read either the constant or its value: it is absent
#: from both envelope schemas and from every test, which is why the rename is safe and why
#: keeping a name that points at a deleted type would have been the worse choice.
REASON_NO_MODEL_DECLARED = "NO_MODEL_DECLARED"


@admits(
    observations=each_of(ObservationRecord),
    config_snapshot=ConfigSnapshot,
    now_utc=datetime,
)
def evaluate(
    observations: Sequence[ObservationRecord],
    config_snapshot: ConfigSnapshot,
    now_utc: datetime,
) -> DialSet:
    """Compute both dials.

    **A2 AND A3 OF BP-AMENDMENT-0001 §D.2, ESTABLISHED AT THE DOOR AND DERIVED FROM THIS
    SIGNATURE.** ``config_snapshot`` must be exactly a
    :class:`~crash_detector.engine.config.ConfigSnapshot` — ``ASR3-F05`` supplied a duck
    object answering ``window()`` and ``spec_for()`` and it decided the window and both
    dials' specs, therefore both dials. ``observations`` must be a ``tuple`` or ``list``
    whose EVERY element is exactly an
    :class:`~crash_detector.observations.ObservationRecord` — the RECORD and not only its
    ``outcome``, which is already exact-typed one level in by ``_latest_usable_ok``: a
    look-alike record carrying an honest ``OK`` still decides its own ``source_id``, and
    which source an observation belongs to decides whether a required input was present.

    Neither requirement is written in this body. Both are read from the signature above by
    :func:`~crash_detector.admission.admits`, so an edit to this body cannot remove them and
    an argument added to this signature arrives REFUSED rather than unguarded.

    Pure: the same arguments produce the same result, and nothing outside the arguments is
    read or written. No clock is consulted — ``now_utc`` is an argument precisely so that
    a historical evaluation can be replayed exactly.

    **THE PURITY IS NOW STRUCTURAL AND THE OLD CAVEAT IS WITHDRAWN.** It used to read: *"the
    one way a caller can break that purity is by injecting a ContributionModel that performs
    I/O"*, and it pointed at a docstring contract for the remedy. A contract stated on a
    ``Protocol`` is not a runtime property, which is the whole of ``ASR3-F02``. After
    BP-AMENDMENT-0001 §C there is no field through which such an object can arrive, so
    ``evaluate`` is pure because the executor is pure and takes no caller code — a stronger
    purity than the one the injection argument bought.

    The model is RESOLVED here, per dial, through
    :meth:`~crash_detector.engine.config.ConfigSnapshot.model_for` — the one resolution
    door, which re-asserts every §C.5 invariant at the moment of resolution. Under the
    shipped :data:`~crash_detector.engine.model.EMPTY_MODEL_REGISTRY` both dials name no
    model, both resolutions answer ``None``, and both dials read ``Unknown``.
    """
    instant = ensure_utc(now_utc)
    usable = _latest_usable_ok(
        observations,
        now_utc=instant,
        window=config_snapshot.window(),
    )
    return DialSet(
        equity=_evaluate_dial(
            config_snapshot.spec_for(EQUITY_DIAL_ID),
            usable,
            instant,
            config_snapshot.model_for(EQUITY_DIAL_ID),
        ),
        monetary=_evaluate_dial(
            config_snapshot.spec_for(MONETARY_DIAL_ID),
            usable,
            instant,
            config_snapshot.model_for(MONETARY_DIAL_ID),
        ),
    )


def _latest_usable_ok(
    observations: Sequence[ObservationRecord],
    *,
    now_utc: datetime,
    window: StalenessWindow,
) -> dict[str, OK]:
    """The most recent usable ``OK`` observation per source.

    **THE RETURN ANNOTATION SAYS ``dict`` AND NOT ``Mapping`` SINCE WO-2R3 INCREMENT 8, AND
    IT IS A CORRECTION RATHER THAN A NARROWING.** *Superseded wording, quoted rather than
    deleted (CD-RULE-004, PBG-CONT-003): ``-> Mapping[str, OK]``.* The body has always built
    and returned the ``dict`` literal below; the two doors that consume this value —
    :func:`required_inputs_are_all_present` and :func:`refuse_a_number_without_its_inputs` —
    have always declared ``usable=dict`` and have always refused anything else on every call.
    The annotation was the only thing in the path saying otherwise, and since
    :func:`_evaluate_dial`'s establishment is now DERIVED FROM ITS ANNOTATION an annotation
    that is wider than the truth would be an establishment wider than the truth.

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

    **``window`` is a :class:`~crash_detector.staleness.StalenessWindow`, not a float, and
    that is the closure of CD-ASR-F06 on this path.** A bare number could be anything —
    ``1e18`` is a bare number, and it abolishes staleness on this path exactly as it did on
    the serving path. This private helper therefore cannot be called with an unadmitted
    quantity at all: the only way to obtain the argument is to construct one, and
    constructing one is the admission.
    """
    latest: dict[str, OK] = {}
    for record in observations:
        outcome = record.outcome
        # EXACT TYPE, not isinstance (CD-AC-005, Class 2). An `OK` subclass may shadow
        # `source_as_of_utc` with a property, and a property is the subclass's code running
        # inside this system's freshness decision. Skipping it is the fail-closed
        # direction: an outcome this function cannot recognise contributes nothing, exactly
        # as `FetchFailed`, `Malformed` and `Empty` contribute nothing. `outcome_class`,
        # which `ObservationRecord.__post_init__` calls, already admits by exact type, so
        # this is the same rule read at the second of the two sites rather than a new one.
        if type(outcome) is not OK:
            continue
        age = age_seconds(as_of_utc=outcome.source_as_of_utc, now_utc=now_utc)
        if not window.covers(age):
            continue
        incumbent = latest.get(record.source_id)
        # WHICH OBSERVATION IS THE LATEST IS DECIDED BY THIS SYSTEM. `>` between two stored
        # timestamps is the left operand's `__gt__` to define, so the comparison is made on
        # instants re-established here rather than on whatever the operands are. Both sides
        # are already canonical if they came through `OK.__post_init__`; putting them
        # through the door again costs nothing and removes the dependence on that being so.
        if incumbent is None or ensure_utc(outcome.source_as_of_utc) > ensure_utc(
            incumbent.source_as_of_utc
        ):
            latest[record.source_id] = outcome
    return latest


@admits(spec=DialSpec, usable=dict)
def required_inputs_are_all_present(
    spec: DialSpec, usable: Mapping[str, OK]
) -> bool:
    """Did this dial get everything it needs to produce a magnitude at all?

    THREE ways the answer is no, and each of them is a way a dial can fail to be a number
    without anything having gone wrong in the arithmetic:

    * the spec declares no required inputs — zero requirements satisfied is not "all
      requirements satisfied", and with the WO-2 empty source registry this is the shipped
      state of both dials;
    * the spec names no model, so there is no declared mapping from inputs to a magnitude
      (doctrine §3.6) and any number produced would be unexplainable. It reads the NAME and
      not a resolved spec, deliberately: the post-condition must re-derive its answer from
      the function's own arguments, and the resolved model is not one of them;
    * a declared required input is not in the usable set — absent, stale, future-dated, or
      its latest outcome was not ``OK``.

    These are the same three conditions the three ``Unknown`` branches of
    :func:`_evaluate_dial` test, restated here as ONE predicate over the arguments so that
    :func:`refuse_a_number_without_its_inputs` can recompute the answer without trusting
    anything the body decided. The duplication is the point and is disclosed rather than
    factored away: if the body and this predicate ever disagree, the post-condition raises
    and the disagreement is loud. What must not happen is the post-condition asking the body
    what it concluded, because the body is what a plant edits.
    """
    if not spec.required_input_ids:
        return False
    if spec.model_ref is None:
        return False
    return all(source_id in usable for source_id in spec.required_input_ids)


@admits(spec=DialSpec, usable=dict, reading=one_of(*READING_CONSTRUCTORS))
def refuse_a_number_without_its_inputs(
    spec: DialSpec, usable: Mapping[str, OK], reading: "Reading"
) -> None:
    """Refuse a value-bearing reading from a dial that did not get its inputs.

    The whole of CD-ASR-F03's runtime closure, and the reason it closes a CLASS: it never
    asks where the number came from. A literal, a module-level constant, a configuration
    default, a previous magnitude carried across an outage, a value read from the store —
    every one of them fails here, because what is refused is the *claim* that inputs were
    present and not any particular way of spelling a zero.

    One-directional on purpose: ``Unknown`` where a number was available is not refused.
    That is the safe direction, and a guard that compelled a number would be pushing
    against PID §3.2 rather than for it.
    """
    # `is_exactly` AND NOT `type(reading) not in READINGS_THAT_CARRY_A_VALUE`
    # (`F-06-D`, WO-2R3 increment 8). **THIS IS THE POST-CONDITION'S FIRST STATEMENT AND
    # ITS EARLY RETURN IS THE WHOLE OF CD-ASR-F03's CLOSURE.** `in` over a tuple is `==`,
    # `==` puts `type(reading)` on the LEFT, and a metaclass answering `__eq__` inverted
    # nothing here — it made `not in` FALSE, so a value-bearing reading DID reach the
    # check. What it could do is the other direction: a reading whose metaclass answers
    # `__eq__` False for every member returns EARLY and the claim is never checked.
    # `is` between two type objects has nothing to delegate.
    if not is_exactly(reading, READINGS_THAT_CARRY_A_VALUE):
        return
    if required_inputs_are_all_present(spec, usable):
        return
    raise AbsenceYieldedAValue(
        f"dial {spec.dial_id!r} produced {type(reading).__name__}, which carries a value, "
        f"but its required inputs were not all present: it declares "
        f"{list(spec.required_input_ids)}, "
        f"{'it names model ' + repr(spec.model_ref) if spec.model_ref is not None else 'it NAMES NO MODEL'}"
        f", and the usable inputs are {sorted(usable)}. A reading that carries a value is "
        "a claim that its inputs were present; a dial that did not get them must be "
        "Unknown, whatever the number is and wherever it came from (PID §3.2, CD-AC-001, "
        "CD-ASR-F03)."
    )


# ==================================================================================== #
# THE CD-ASR-F03 MECHANISM, REDESIGNED — `PO-DECISIONS-0015` RULING 1.
#
# `PO-DECISIONS-0012` ruling 1 held that this evaluator was *"reachable only through doors
# that already establish"*. **THAT HALF WAS FALSIFIED BY MEASUREMENT TWICE INDEPENDENTLY**:
# a conforming, declared-foreign `SourceAdapter` obtains the module from `sys.modules` on the
# SECOND collection cycle and reaches the UNDECORATED evaluator through `__closure__`,
# passing no door. The ruling fell on its own pre-committed terms and the consequence was
# taken in full: **`guarded` becomes a DOOR, and this control is REDESIGNED, not repaired.**
#
# THE THREE ACCEPTANCE PROPERTIES, AND WHERE EACH ONE LIVES IN THE CODE BELOW:
#
#   (a) **NO UNDECORATED EVALUATOR OBJECT EXISTS AT RUNTIME.** `_body_materials` takes the
#       evaluator's CODE OBJECT and lets the function object go. After the decorator returns,
#       nothing in `guarded.__closure__`, nothing under `__wrapped__` (never set), nothing in
#       `__globals__` and nothing in the module namespace is a CALLABLE that reaches the
#       judgement without establishment. What the cell holds instead is a `code` object,
#       which cannot be called — the same line this codebase already draws for
#       `__signature__`: *"a Signature is a description; it is not a callable and it is not a
#       way through."*
#       **AND THE RESIDUE IS DECLARED, NOT CLAIMED CLOSED: `types.FunctionType(code,
#       globals)` RECONSTITUTES A CALLABLE BODY, AND THE MATERIALS FOR IT ARE IN THE CELLS.
#       MEASURED. See DECLARED LIMIT 10 in this module's header.**
#
#   (b) **THE ESTABLISHMENT IS DERIVED FROM THE SIGNATURE.** `_establishment_derived_from`
#       reads the evaluator's own RESOLVED ANNOTATIONS and compiles one admission per
#       parameter through `crash_detector.admission.declaration` — the same vocabulary every
#       other door uses, never a second one. **NOBODY WRITES A PARAMETER LIST HERE.** The old
#       net had `*extra, **extra_by_name` — open arity — precisely so that a fourth argument
#       would not take the guard off with it; that openness was a GAP THAT BOUND NOTHING, and
#       PO-DECISIONS-0015 ruling 1 is the finding that says so. This derives instead, so a new
#       parameter is ESTABLISHED BY EXACT TYPE on the run it is added, with no edit to this
#       function. A parameter whose annotation this mechanism cannot turn into a type set,
#       or which carries no annotation at all, FAULTS THE DOOR AT IMPORT — fail-closed,
#       never open.
#
#   (c) **THE POST-CONDITION IS RETAINED INSIDE THE SAME MECHANISM.** One wrapper, one
#       closure: the door and the net are the same object, which is what makes them
#       inseparable. `refuse_a_number_without_its_inputs` is called by that literal name so
#       `tools/register/declared_nets.py`'s "the body actually CALLS it" assertion is checked
#       against this code and not against prose. **WHICH ARGUMENTS IT RECEIVES IS ALSO
#       DERIVED** — from the post-condition's OWN signature, matched by name against the
#       evaluator's bound arguments — so the post-condition can grow a parameter too, and
#       neither signature can drift past the other silently.
# ==================================================================================== #


def _one_exact_type(annotation):
    """A single resolved annotation -> the type a value of it will actually BE at runtime.

    ``dict[str, OK]`` -> ``dict``. ``DialSpec`` -> ``DialSpec``. ``None`` -> ``None``, which
    :func:`~crash_detector.admission.declaration` reads as ``type(None)``.

    **THE SUBSCRIPT IS DROPPED AND THAT IS DECLARED RATHER THAN QUIET** (DECLARED LIMIT 11):
    ``dict[str, OK]`` establishes that the argument is exactly a ``dict`` and says nothing
    about its keys or its values. The element establishment on this path is
    ``_latest_usable_ok``'s ``type(outcome) is not OK``, one level up, and the post-condition
    re-derives from ``spec`` and from the KEYS of ``usable`` only.
    """
    origin = typing.get_origin(annotation)
    return annotation if origin is None else origin


def _exact_types_of(annotation):
    """One resolved annotation -> the type, or the tuple of types, it stands for.

    Whatever this returns is handed to :func:`~crash_detector.admission.declaration`, which
    is what decides whether it is a legal declaration. **This function does not validate and
    does not guess** — it unwraps a union and a generic subscript and hands the result to the
    one vocabulary, so there is no second opinion anywhere about what a declaration means.

    Both union spellings are unwrapped: ``typing.Union[X, None]`` and PEP 604's ``X | None``,
    whose ``get_origin`` is ``types.UnionType`` rather than ``typing.Union``. Neither is
    preferred and neither is assumed absent. ``types.UnionType`` is named DIRECTLY and not
    through ``getattr(types, "UnionType", ...)``: this project is pinned to ``3.11.*``
    (``pyproject.toml``), where the attribute always exists, and a ``getattr`` with a default
    is a DUCK admission — a tier-1 site of the Class-2 sweep — which would need a written
    disposition in a register this module has no business enlarging.
    """
    origin = typing.get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        return tuple(_one_exact_type(member) for member in typing.get_args(annotation))
    return _one_exact_type(annotation)


def _establishment_derived_from(evaluate_one_dial, signature) -> dict:
    """One admission per parameter, DERIVED FROM THE ANNOTATION and from nothing else.

    **THIS IS PROPERTY (b), AND THE WHOLE OF IT.** ``@admits(spec=DialSpec, usable=dict,
    now_utc=datetime)`` is a HAND-WRITTEN parameter list, and a hand-written parameter list is
    a silent hole on the day somebody adds an argument — which is the failure the old net's
    open arity was written to survive, met from the other side. Here the annotation IS the
    declaration, so nobody has to remember to add anything.

    **THE DERIVATION IS CLOSED AND DENY-BY-DEFAULT:**

    * a plain class annotation becomes that exact type;
    * ``X | None`` / ``Union[X, Y]`` becomes ``one_of(X, Y)`` — via ``typing.get_args``, not
      by reading source text;
    * a subscripted generic becomes its ORIGIN — ``dict[str, OK]`` is exactly ``dict``, which
      is what the runtime type of that argument actually is. The subscript stays in the
      signature for a reader and decides nothing here (DECLARED LIMIT 11);
    * **ANYTHING ELSE RAISES AT IMPORT.** :func:`~crash_detector.admission.declaration`
      refuses any declaration it does not recognise and that refusal is NOT caught. A door
      this mechanism cannot derive must stop the module importing rather than exist
      unguarded — the same choice ``admits`` makes, made by the same code.

    Annotations are resolved with ``typing.get_type_hints`` because this module carries
    ``from __future__ import annotations``, so ``__annotations__`` holds STRINGS. Reading the
    strings would be reading source text; resolving them reads the objects the interpreter
    will actually compare against.
    """
    # THE OPEN-CHANNEL REFUSAL IS ASKED FIRST, BEFORE THE ANNOTATIONS ARE EVEN RESOLVED, AND
    # THAT ORDER IS THE POINT. An open channel is refused whatever its annotation says and
    # whether or not the annotation resolves at all: a signature this mechanism cannot derive
    # from must be refused by the refusal that names the real defect, not by whichever error
    # the resolver happens to raise first.
    for name, parameter in signature.parameters.items():
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            # AN OPEN CHANNEL ON THE ONE GUARD THAT EXISTS BECAUSE OF AN ESCAPE. `admits`
            # refuses these for the general case in the same words. The old net HAD them,
            # and PO-DECISIONS-0015 ruling 1 is the finding that they bound nothing.
            raise AdmissionFault(
                f"{evaluate_one_dial.__qualname__} declares {name!r} as an OPEN CHANNEL "
                "(*args / **kwargs). Values arrive through it with no name to declare and "
                "no type to require. The establishment here is DERIVED FROM THE SIGNATURE "
                "(PO-DECISIONS-0015 ruling 1 (b)), and a channel with no name in the "
                "signature cannot be derived from it."
            )
    resolved = typing.get_type_hints(evaluate_one_dial)
    derived: dict = {}
    for name, parameter in signature.parameters.items():
        if name not in resolved:
            raise AdmissionFault(
                f"{evaluate_one_dial.__qualname__} parameter {name!r} carries NO "
                "ANNOTATION, and the annotation is what this door's establishment is "
                "derived from. A parameter added without one arrives REFUSED — at import, "
                "loudly — rather than unguarded (BP-AMENDMENT-0001 §D.1, planted violation "
                "P7)."
            )
        derived[name] = declaration(name, _exact_types_of(resolved[name]))
    if not derived:
        raise AdmissionFault(
            f"{evaluate_one_dial.__qualname__} has no parameters, so this mechanism would "
            "establish nothing and the post-condition would have nothing to re-derive from. "
            "A guard with an empty subject is REFUSED rather than counted."
        )
    return derived


def _post_condition_order(signature, post_condition) -> tuple:
    """WHICH of the door's arguments the post-condition gets, DERIVED FROM ITS SIGNATURE.

    Returns one entry per post-condition parameter, in the post-condition's own order: the
    parameter's NAME where it is also a parameter of the evaluator, and ``None`` for the
    single remaining parameter, which receives what the body returned.

    **THERE MUST BE EXACTLY ONE REMAINING PARAMETER AND THIS REFUSES OTHERWISE.** A
    post-condition asking for something the door does not have is a post-condition checking a
    claim against evidence nobody supplied, and it fails at import instead of at a gate.
    """
    parameters = list(
        inspect.signature(post_condition, follow_wrapped=False).parameters
    )
    outstanding = [name for name in parameters if name not in signature.parameters]
    if len(outstanding) != 1:
        raise AdmissionFault(
            f"{post_condition.__qualname__} takes {parameters}, of which {outstanding} are "
            "not arguments of the evaluator. **EXACTLY ONE MUST BE OUTSTANDING** — the one "
            "that receives what the body returned. The rest are matched to the door's own "
            "bound arguments BY NAME so that neither signature can grow past the other "
            "silently."
        )
    return tuple(None if name in outstanding else name for name in parameters)


def _body_materials(evaluate_one_dial) -> tuple:
    """**PROPERTY (a).** The evaluator's body, as MATERIALS rather than as a callable.

    Returns ``(code, globals, name, defaults, kwdefaults)``. The FUNCTION OBJECT is not among
    them and is not retained anywhere: once :func:`_absence_is_never_a_number` returns, the
    only reference to the undecorated evaluator that ever existed has gone, and what stands
    in the closure is a ``code`` object.

    **A ``code`` OBJECT CANNOT BE CALLED.** That is the difference between this and the shape
    `PO-DECISIONS-0015` ruling 1 condemns as *"the defect class, not an implementation
    choice"*, and it is why the attack that felled the ruling —
    ``sys.modules[m]._evaluate_dial.__closure__[i].cell_contents(spec, usable, now)`` — no
    longer reaches anything: every cell it finds is data. **IT IS NOT A CLOSURE OF THE REACH
    AND IS NOT OFFERED AS ONE; see DECLARED LIMIT 10.**

    **FAIL CLOSED ON A BODY THIS CANNOT REBUILD.** A body with free variables would need its
    CELLS carried too, and carrying a cell is carrying whatever is in it — which is exactly
    the thing the ruling names as the defect class. Rather than handle a case that does not
    exist here, this refuses it at import.
    """
    if evaluate_one_dial.__closure__ is not None or evaluate_one_dial.__code__.co_freevars:
        raise AdmissionFault(
            f"{evaluate_one_dial.__qualname__} closes over "
            f"{list(evaluate_one_dial.__code__.co_freevars)}. This mechanism carries the "
            "body as a CODE OBJECT so that no callable form of it survives "
            "(PO-DECISIONS-0015 ruling 1 (a)); a body with free variables would require its "
            "CELLS to be carried too, and a cell is exactly the thing that ruling names as "
            "the defect class. REFUSED AT IMPORT rather than handled by carrying them."
        )
    return (
        evaluate_one_dial.__code__,
        evaluate_one_dial.__globals__,
        evaluate_one_dial.__name__,
        evaluate_one_dial.__defaults__,
        evaluate_one_dial.__kwdefaults__,
    )


def _absence_is_never_a_number(evaluate_one_dial):
    """Make a per-dial evaluator a DOOR that is also the CD-ASR-F03 net, INSEPARABLY.

    The guard is applied HERE, at the boundary of the function, rather than written into its
    body, because the escape that produced CD-ASR-F03 was an edit to the body. A
    post-condition derived from the arguments survives any rewriting of what is between them
    and the return statement.

    **AND SINCE `PO-DECISIONS-0015` RULING 1 IT IS ALSO A DOOR**: the arguments are
    established by EXACT TYPE before the body runs, DERIVED FROM THE EVALUATOR'S OWN
    SIGNATURE. The two are one wrapper and one closure on purpose — *"the guard and the
    guarded are inseparable"* is a statement about object identity, not about intent.
    """
    signature = inspect.signature(evaluate_one_dial, follow_wrapped=False)
    establishment = _establishment_derived_from(evaluate_one_dial, signature)
    post_condition_order = _post_condition_order(
        signature, refuse_a_number_without_its_inputs
    )
    code, body_globals, body_name, body_defaults, body_kwdefaults = _body_materials(
        evaluate_one_dial
    )
    # `evaluate_one_dial` is deliberately NOT READ AGAIN below this line. Nothing in the
    # closure of `guarded` is the undecorated evaluator, and nothing rebuilds it except the
    # one expression inside `guarded` itself, per call, from data.

    def guarded(*arguments, **by_name):
        # THE DOOR. Derived from the signature, refused before the body binds.
        #
        # `*arguments, **by_name` IS AN ARITY THAT PASSES THROUGH, NOT A CHANNEL. It is
        # erased at the first statement by `signature.bind`, against THE EVALUATOR'S OWN REAL
        # SIGNATURE, so nothing can arrive here that that signature would not hold and
        # nothing that arrives is unestablished. This is the same structure and the same
        # reasoning as `admits`'s own `door(*args, **kwargs)`, whose ten measured arms are
        # DECLARED LIMIT 7 in `crash_detector.admission`. It is NOT the old net's shape: the
        # old net forwarded `*extra` to a callee whose signature it never bound against, and
        # that gap is what PO-DECISIONS-0015 ruling 1 found.
        bound = signature.bind(*arguments, **by_name)
        bound.apply_defaults()
        for parameter, admission in establishment.items():
            refusal = admission.refusal(parameter, bound.arguments[parameter])
            if refusal is not None:
                raise NotAdmitted(
                    f"{body_name}: {refusal} (BP-AMENDMENT-0001 §D.1 — every entry point on "
                    "a judgement path establishes each of its arguments by exact type at "
                    "the door, DERIVED FROM THE SIGNATURE; PO-DECISIONS-0015 ruling 1.)"
                )
        # THE BODY. Rebuilt from its code FOR THIS CALL and dropped again — there is no
        # persistent callable form of it for anything to reach.
        body = types.FunctionType(code, body_globals, body_name, body_defaults)
        body.__kwdefaults__ = body_kwdefaults
        reading = body(*bound.args, **bound.kwargs)
        # THE NET. Named literally so `tools/register/declared_nets.py`'s third assertion is
        # checked against this line and not against a sentence about it; its arguments are
        # derived from ITS OWN signature.
        refuse_a_number_without_its_inputs(
            *[
                reading if name is None else bound.arguments[name]
                for name in post_condition_order
            ]
        )
        return reading

    # THE GUARD DOES NOT PUBLISH A WAY ROUND ITSELF, AND NOW IT NEVER HAD ONE TO DELETE.
    #
    # *Superseded implementation, described rather than deleted (CD-RULE-004, PBG-CONT-003):
    # until this increment this mechanism used `functools.wraps` and then `delattr`'d the
    # `__wrapped__` it had just created* — a bypass introduced and withdrawn inside one
    # function. **`functools.wraps` IS NOT USED HERE AT ALL.** The four attributes that make
    # the door readable are copied by name; `__wrapped__` is NEVER SET, so there is no window
    # between creating it and removing it, and a future edit that puts the decorator back
    # cannot silently reinstate it. That is a strictly stronger answer to `PO-DECISIONS-0013`
    # ruling 2 than the `delattr` it replaces.
    guarded.__name__ = body_name
    guarded.__qualname__ = evaluate_one_dial.__qualname__
    guarded.__doc__ = evaluate_one_dial.__doc__
    guarded.__module__ = evaluate_one_dial.__module__
    # The real signature is kept as DATA, so `inspect.signature(_evaluate_dial)` still reports
    # what the evaluator takes. A `Signature` is a description; it is not a callable and it is
    # not a way through. This mirrors `admits` and `establishes` exactly.
    guarded.__signature__ = signature
    # AND IT ANSWERS THE PROJECT'S OWN RUNTIME QUESTION `is_admitting_door(...)` WITH TRUE,
    # which is what "`guarded` becomes a DOOR" has to mean if it is to mean anything a test
    # can read. The declaration it publishes is the DERIVED one, so `declared_admissions()`
    # reports what a caller must actually satisfy rather than what somebody typed.
    setattr(guarded, ADMITS_ATTRIBUTE, dict(establishment))
    setattr(guarded, FAULTS_ATTRIBUTE, ())
    return guarded


@_absence_is_never_a_number
def _evaluate_dial(
    spec: DialSpec,
    usable: dict[str, OK],
    now_utc: datetime,
    model: "Union[ModelSpec, None]" = None,
) -> "Reading":
    """One dial's reading, or the named reason there is not one.

    Every ``return`` below is checked against
    :func:`refuse_a_number_without_its_inputs` by the decorator, so a branch that did not
    get its inputs cannot return a reading carrying a value however it is rewritten.

    ``model`` is the spec ``evaluate`` RESOLVED through
    :meth:`~crash_detector.engine.config.ConfigSnapshot.model_for`. It arrives through the
    ``*extra`` the post-condition wrapper already carries, which is what that wrapper was
    written with in the first place — *"a wrapper that fixed the arity would stop guarding
    the moment anybody gave the evaluator a fourth argument"*. This is that fourth argument,
    and the guard did not come off with it.
    """
    if not spec.required_input_ids:
        # The WO-2 state: no ingredient sources declared (CD-D-005 owed, BLUEPRINT §16).
        # Zero requirements satisfied is NOT "all requirements satisfied".
        return Unknown(
            reason=REASON_NO_REQUIRED_INPUTS,
            since_utc=now_utc,
            missing_inputs=(),
        )

    if spec.model_ref is None:
        # DialSpec already refuses required inputs without a model, so this is currently
        # unreachable. It is kept as a named refusal rather than an assumption, because
        # "unreachable" is a claim about today's constructor and this is the dial path.
        return Unknown(
            reason=REASON_NO_MODEL_DECLARED,
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

    # THE ENGINE EXECUTES THE MAPPING. THE CALLER SUPPLIED NEITHER THE CODE NOR THE NUMBER.
    #
    # This line used to read `spec.contribution_model.compute(payloads)` — a call on an
    # object the caller had put in the DialSpec — and it is the line ASR3-F02 published a
    # laundered number through. It cannot be written any more: DialSpec has no field holding
    # an object, so there is no expression that names one.
    #
    # `model` is a ModelSpec the engine RESOLVED from a name (ConfigSnapshot.model_for, the
    # one resolution door), `payloads` are values the engine RELEASED from OK observations
    # it selected, and `compute` is engine-owned, holds no state, and takes one dial's spec
    # and one dial's payloads. There is nothing here for a caller to close over.
    #
    # The refusal travels. It is not caught and turned into a number, and it is not caught
    # and turned into Unknown either: an executor that cannot compute honestly is a defect,
    # and swallowing it would publish "we have no data" when the truth is "our code is
    # broken". Under the shipped registry this line is unreachable — nothing resolves — and
    # under any registry WO-2 could carry it raises UnspecifiedMapping and returns nothing.
    computation = compute(model, payloads)
    # THE ONE ADMISSION SITE IN THE PRODUCT (CD-PL-F54, and see RULE 4 of
    # tools/register/check_no_blend.py, which admits a reference to `observed_for_dial`
    # from here and from nowhere else on the scanned path).
    #
    # This is where a number enters a dial from outside the system, and it is the only
    # place in src/ that may say so. The claim it makes is not decorative: `used_ids` is
    # the set of sources this dial's declared spec actually got, computed above from the
    # usable observations, and the enclosing function is wrapped by
    # `_absence_is_never_a_number`, which re-derives from (spec, usable) whether those
    # inputs were present at all and refuses the reading if they were not. So the
    # admission's citation and the post-condition's premise are the same evidence, read
    # twice, and a branch that did not get its inputs cannot reach this line and keep the
    # value it produced.
    #
    # The magnitude is wrapped in this dial's provenance AT THE POINT IT IS COMPUTED and
    # never travels as a bare float (CD-ASR-F01). `spec.dial_id` is the same key that
    # selected the score type below, and it is stated twice on purpose — once to the
    # admission door and once to the magnitude — because the magnitude compares the two by
    # SET EQUALITY rather than inferring either from the other.
    score = DIAL_SCORE_TYPES[spec.dial_id](
        score=DialMagnitude(
            dial_id=spec.dial_id,
            quantity=observed_for_dial(
                dial_id=spec.dial_id,
                quantity=computation.magnitude,
                inputs_used=used_ids,
            ),
        ),
        contributions=computation.contributions,
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
    # `min` is decided by the elements' own `__lt__`, so the elements are re-established
    # first (CD-AC-005, Class 2): the reading's `as_of_utc` is what every later freshness
    # judgement about this reading is made against, and taking the newest rather than the
    # oldest would make a reading look fresher than the data behind it.
    return min(
        ensure_utc(usable[source_id].source_as_of_utc) for source_id in used_ids
    )
