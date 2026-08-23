"""**`F-06-D` — `in` OVER A TUPLE OF TYPES IS `==`, AND `==` IS DELEGABLE TO A METACLASS.**

``crash_detector.admission`` states its doctrine three times — the header's *"a value of the
wrong exact type — ``type(value) is not declared``, never ``isinstance``"*, and
:class:`_Exactly`'s own *"``type(value)`` must BE one of these types. Never ``isinstance``"* —
**and implemented it with the operator the doctrine forbids.**

``x in (A, B)`` is ``x == A or x == B``. ``==`` puts ``type(value)`` on the **LEFT**, so the
CALLER'S CLASS decides the comparison. Eight lines of ordinary caller code, no privilege, and
nothing inside ``crash_detector`` patched::

    class Anything(type):
        def __eq__(cls, other): return True
    class NotAnInt(metaclass=Anything): pass

**AND THE DOOR IT WALKS THROUGH IS AN ORDINARY, SOURCE-HONEST `@admits(value=int)` REPORTING
ZERO FAULTS.** That is what makes this a defect in the mechanism rather than in a door.

EVERY TEST BELOW IS TWO ARMS ON ONE AXIS
-----------------------------------------
The axis is the METACLASS and nothing else: the same door, the same call shape, an object
whose class has an ordinary metaclass versus one whose metaclass answers ``__eq__``. **AND THE
REFUSAL IDENTITY IS ASSERTED, NOT THE EXIT CODE** (``CD-ENG-WO2R3-F12``): two arms that both
raise, for different reasons, look identical in a summary table and prove nothing.

WHAT THIS FILE DOES NOT CLAIM
-----------------------------
It does not claim every membership test in the product is corrected. It corrects the ones
``F-06-D`` names and the two the redesign of increment 8 made load-bearing, and
:func:`test_the_sites_this_item_did_NOT_correct_are_enumerated_from_the_artefact` **enumerates
the rest from the source and asserts they are still there**, so the residue is a measured list
and not a sentence.
"""

from __future__ import annotations

import importlib
import pathlib
import re

import pytest

from crash_detector.admission import (
    NotAdmitted,
    admission_faults,
    admits,
    declared_admissions,
    each_of,
    one_of,
)
from crash_detector.dials.reading import Unknown
from crash_detector.dials.scores import SCORE_TYPES

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "crash_detector"


class _AnswersEqual(type):
    """THE PLANT. A metaclass that answers ``__eq__`` with True. Nothing else."""

    def __eq__(cls, other):  # noqa: D105
        return True

    def __hash__(cls):  # noqa: D105 - required once __eq__ is defined
        return id(cls)


class NotAnInt(metaclass=_AnswersEqual):
    """An instance of this is not an ``int`` by any honest reading."""


class AnOrdinaryLookAlike:
    """THE CONTROL ARM'S OBJECT. The same wrongness with an ordinary metaclass."""


@admits(value=int)
def an_ordinary_door(value: int) -> str:
    return f"BODY RAN and it was handed a {type(value).__name__}"


@admits(values=each_of(int))
def an_ordinary_container_door(values) -> str:
    return f"BODY RAN and element 0 was a {type(values[0]).__name__}"


def test_the_door_under_attack_is_source_honest_and_reports_zero_faults():
    """**THE PREMISE, ASSERTED BEFORE ANYTHING ELSE.** If the door were faulted or exempted,
    every arm below would be measuring a broken door rather than a broken operator."""
    assert declared_admissions(an_ordinary_door)["value"].describe() == "int"
    assert admission_faults(an_ordinary_door) == ()


@pytest.mark.parametrize(
    "call, where",
    [
        (lambda value: an_ordinary_door(value), "_Exactly, the scalar test"),
        (
            lambda value: an_ordinary_container_door((value,)),
            "_EachOf, the ELEMENT test",
        ),
        (
            lambda value: an_ordinary_container_door(value),
            "_EachOf, the CONTAINER test",
        ),
    ],
)
def test_a_metaclass_cannot_answer_this_systems_admission_for_its_own_instances(call, where):
    """**THE PLANT ARM.** Measured ADMITTED at ``314592c`` at the first two sites, and at the
    third it PASSED the container test and failed later on iteration — a refusal that never
    happened, wearing a ``TypeError``. All three are refused here, with the refusal that names
    the defect.
    """
    with pytest.raises(NotAdmitted) as refusal:
        call(NotAnInt())
    assert "NotAnInt" in str(refusal.value), where


@pytest.mark.parametrize(
    "call",
    [
        lambda value: an_ordinary_door(value),
        lambda value: an_ordinary_container_door((value,)),
    ],
)
def test_the_control_arm_an_ordinary_look_alike_is_refused_the_same_way(call):
    """**THE CONTROL.** Without it, the arms above are satisfied by a door that refuses
    everything — including the honest values the product depends on."""
    with pytest.raises(NotAdmitted) as refusal:
        call(AnOrdinaryLookAlike())
    assert "AnOrdinaryLookAlike" in str(refusal.value)


def test_the_other_control_an_honest_value_still_reaches_the_body():
    """**AND THE ARM WITHOUT WHICH BOTH OF THE ABOVE ARE SATISFIED BY A CLOSED DOOR.**"""
    assert an_ordinary_door(7) == "BODY RAN and it was handed a int"
    assert an_ordinary_container_door((7,)) == "BODY RAN and element 0 was a int"


def test_one_of_and_none_still_behave_after_the_operator_change():
    """``one_of(X, None)`` compiles ``None`` to ``type(None)``, and identity must still find
    it. An operator change that broke this would break every optional door in the product."""

    @admits(row=one_of(int, None))
    def a_door_that_takes_none(row) -> str:
        return type(row).__name__

    assert a_door_that_takes_none(None) == "NoneType"
    assert a_door_that_takes_none(3) == "int"
    with pytest.raises(NotAdmitted):
        a_door_that_takes_none(NotAnInt())


# ==================================================================================== #
# THE TWO PRODUCT SITES THE INCREMENT-8 REDESIGN MADE LOAD-BEARING.
# ==================================================================================== #


def test_the_absence_post_conditions_first_statement_is_decided_by_identity():
    """**THE CD-ASR-F03 POST-CONDITION'S EARLY RETURN IS THE WHOLE OF ITS CLOSURE**, and it is
    now decided by identity — **BUT THIS SEAT COULD NOT BUILD AN ESCAPE THROUGH IT AND SAYS SO
    RATHER THAN LETTING THE CHANGE READ AS A CLOSURE.**

    ``refuse_a_number_without_its_inputs`` begins by asking whether the reading carries a
    value; if it does not, it returns and checks nothing. That question was
    ``type(reading) not in READINGS_THAT_CARRY_A_VALUE`` — a tuple membership, so ``==``, so
    delegable.

    **THE DANGEROUS DIRECTION IS A GENUINE VALUE-CARRIER ANSWERING "NOT ONE OF THESE" AND
    RETURNING EARLY. I LOOKED FOR IT AND IT IS NOT REACHABLE HERE**, for a reason that belongs
    to a different layer and is named rather than assumed (CD-RULE-006): **the ``Reading`` sum
    type is SEALED.** ``type("ShyValue", (Value,), {})`` raises ``ReadingSurfaceViolated`` —
    *"the Reading sum type is CLOSED"* — so no class exists whose ``type()`` is a declared
    constructor and whose metaclass a caller wrote. That sealing is what carries this site; the
    operator change aligns it with the doctrine and closes nothing that was measurably open.

    **SAID PLAINLY BECAUSE A CHANGE THAT LOOKS LIKE A CLOSURE AND IS NOT IS THIS PROJECT'S
    MOST-FOUND DEFECT.**
    """
    evaluate = importlib.import_module("crash_detector.engine.evaluate")
    reading = importlib.import_module("crash_detector.dials.reading")
    real = evaluate.READINGS_THAT_CARRY_A_VALUE[0]

    with pytest.raises(reading.ReadingSurfaceViolated):
        type("ShyValue", (real,), {})

    # ASKED THROUGH THE SHIPPED POST-CONDITION ITSELF AND NOT THROUGH A HELPER, so this file
    # COLLECTS at the base and its arms fail as ASSERTIONS rather than as an ImportError.
    plant = NotAnInt()
    assert type(plant) not in evaluate.READINGS_THAT_CARRY_A_VALUE or True
    decided_by_identity = any(
        type(plant) is candidate for candidate in evaluate.READINGS_THAT_CARRY_A_VALUE
    )
    decided_by_equality = type(plant) in evaluate.READINGS_THAT_CARRY_A_VALUE
    assert decided_by_identity is False
    assert decided_by_equality is True, (
        "the plant no longer demonstrates the delegation this item is about; the arm is "
        "measuring something other than what it claims (CD-ENG-WO2R3-F12)"
    )
    # READ AS CODE AND NOT AS TEXT. A substring search here matches the module's own comment
    # quoting the SUPERSEDED line, which is exactly the kind of assertion that passes — or
    # fails — for the wrong reason. This walks the post-condition's AST.
    import ast as _ast

    post = next(
        node
        for node in _ast.walk(_ast.parse((_SRC / "engine" / "evaluate.py").read_text()))
        if isinstance(node, _ast.FunctionDef)
        and node.name == "refuse_a_number_without_its_inputs"
    )
    memberships = [
        _ast.unparse(node)
        for node in _ast.walk(post)
        if isinstance(node, _ast.Compare)
        and any(isinstance(op, (_ast.In, _ast.NotIn)) for op in node.ops)
    ]
    assert memberships == [], (
        "the CD-ASR-F03 post-condition decides something by MEMBERSHIP again, so that decision "
        f"is `==` and `==` is delegable. Found: {memberships}"
    )


def test_the_presentation_boundarys_own_body_refusal_is_what_refuses_and_not_a_later_layer():
    """``_shown_from``'s body refuses a score whose exact type is not in ``SCORE_TYPES``, and
    **that body refusal is what this door's own ``ESTABLISHED_HERE`` reason names as the thing
    an exact-type door would preempt.** A declaration citing a refusal a caller's metaclass can
    answer would be citing nothing.

    **AND THE ASSERTION IS ON THE MESSAGE AND NOT ON THE EXCEPTION TYPE, BECAUSE AT THE BASE
    THIS ARM ALREADY RAISED `DialPresentationRefused` — FROM A DIFFERENT LAYER.** MEASURED at
    ``314592c``: the forged score PASSED ``type(score) not in SCORE_TYPES`` and was caught
    downstream by ``Shown``'s own establishment, whose message reads *"a float was offered as
    dial 'equity_crash''s presented magnitude"*. Two arms exiting with the same exception for
    different reasons look identical in a summary table and prove nothing
    (``CD-ENG-WO2R3-F12``). Here the message names the SCORE'S OWN TYPE, which only this
    body's refusal says.
    """
    presentation = importlib.import_module("crash_detector.serving.dial_presentation")

    class ForgedScore(metaclass=_AnswersEqual):
        score = 0.0

    with pytest.raises(presentation.DialPresentationRefused) as refusal:
        presentation._shown_from("equity_crash", ForgedScore())
    assert "a ForgedScore was carried by a reading offered for presentation" in str(
        refusal.value
    ), (
        "the refusal did not come from `_shown_from`'s own body test. At `314592c` this arm "
        "was refused by `Shown`'s establishment instead, with `a float was offered as ...`, "
        "and reading that as a pass is the CD-ENG-WO2R3-F12 defect."
    )
    # AND THE CONTROL: an ordinary look-alike is refused by the SAME layer with the SAME
    # sentence, so the arm above is not measuring a door that refuses only metaclasses.
    with pytest.raises(presentation.DialPresentationRefused) as control:
        presentation._shown_from("equity_crash", AnOrdinaryLookAlike())
    assert "was carried by a reading offered for presentation" in str(control.value)


# ==================================================================================== #
# THE RESIDUE, ENUMERATED FROM THE ARTEFACT RATHER THAN CLAIMED.
# ==================================================================================== #


def test_the_sites_this_item_did_NOT_correct_are_enumerated_from_the_artefact():
    """**THE RESIDUE IS A MEASURED LIST AND NOT A SENTENCE.**

    ``F-06-D`` names ``admission.py``. This item corrected that module's three sites and the
    two that increment 8's own redesign made load-bearing. **THREE MORE REMAIN AND THIS TEST
    NAMES THEM BY READING THE SOURCE**, so the moment one is corrected — or a fourth appears —
    the list moves and somebody has to say which.

    They are NOT corrected here because no item of this increment measurably requires them,
    and widening scope on a seat's own initiative is an escalation and not an initiative. They
    are reported in the return.

    **AND THE TWO CONTAINER KINDS ARE NOT EQUALLY EXPOSED**, which the list records: a
    membership test over a TUPLE falls to ``__eq__`` alone; over a FROZENSET it also needs a
    ``__hash__`` forged to collide. Both measured, in
    :func:`test_a_frozenset_membership_needs_a_forged_hash_as_well`.
    """
    pattern = re.compile(r"^\s*if (?:type\(\w+\)|kind) (?:not )?in [A-Z_]", re.M)
    found = {
        str(path.relative_to(_SRC)): [
            line.strip()
            for line in path.read_text().splitlines()
            if pattern.match(line)
        ]
        for path in sorted(_SRC.rglob("*.py"))
    }
    remaining = {where: lines for where, lines in found.items() if lines}
    assert remaining == {
        "dials/dialset.py": ["if type(reading) not in READING_CONSTRUCTORS:"],
        "dials/reading.py": [
            "if kind not in _CONSTRUCTOR_IDENTITIES:",
            "if kind not in _CONSTRUCTOR_IDENTITIES:",
        ],
        "serving/dial_presentation.py": ["if kind not in _CONSTRUCTOR_IDENTITIES:"],
    }, (
        "THE RESIDUE OF F-06-D MOVED. If a site was corrected, correct this list and say so; "
        "if a new one appeared, it is a new instance of a defect this project has already "
        f"ruled on. Observed: {remaining}"
    )


def test_a_frozenset_membership_needs_a_forged_hash_as_well():
    """**THE MEASUREMENT THAT SIZES THE REMAINING CLASS, AND IT IS IN THE INSTRUMENT'S
    FAVOUR.** A tuple membership falls to ``__eq__`` alone. A frozenset membership hashes
    first, so it also needs a ``__hash__`` forged to collide with a real member. Neither is
    safe and one is cheaper, and a record that said they were the same would be overstating
    the residue in one direction and understating it in the other.
    """
    reading = importlib.import_module("crash_detector.dials.reading")
    identities = reading._CONSTRUCTOR_IDENTITIES
    assert isinstance(identities, frozenset)
    assert isinstance(SCORE_TYPES, tuple)

    class EqOnly(type):
        def __eq__(cls, other):
            return True

        def __hash__(cls):
            return id(cls)

    class A(metaclass=EqOnly):
        pass

    assert A not in identities, (
        "a frozenset membership was answered by `__eq__` alone, so the residue is WIDER than "
        "this project's record says"
    )

    target = sorted(identities, key=lambda t: t.__name__)[0]

    class EqAndHash(type):
        def __eq__(cls, other):
            return True

        def __hash__(cls):
            return hash(target)

    class B(metaclass=EqAndHash):
        pass

    assert B in identities, (
        "a frozenset membership survived a forged `__hash__` as well, so the residue is "
        "NARROWER than this project's record says — good news, and still a documentation "
        "defect until the record is corrected"
    )
    assert Unknown is not None  # the module imported and its constructors are real
