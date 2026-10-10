"""**THE ATTACK ITSELF** — the carrier for `PO-DECISIONS-0015` ruling 1's three acceptance
properties for the redesigned `CD-ASR-F03` control.

    (a) no undecorated evaluator object exists at runtime
    (b) the door's establishment is DERIVED FROM THE SIGNATURE
    (c) the CD-ASR-F03 post-condition is retained inside the same mechanism

**WHY THIS FILE EXISTS AND WHY IT IS NOT `tests/test_evaluate.py`.** The dispatch that
commissioned the redesign says in terms: *"YOUR CARRIER MUST BE THE ATTACK ITSELF: a test
that walks ``__closure__`` (and ``__wrapped__``, and ``__globals__``, and the module
namespace) and asserts that what it finds cannot be called to reach the judgement without
establishment. A CARRIER THAT ONLY CHECKS THE DECORATOR IS PRESENT TESTS THE WRAPPER, NOT THE
PROPERTY."* Every test below is that attack, run against the shipped object, obtained the way
the attack that felled `PO-DECISIONS-0012` ruling 1 obtained it — **from ``sys.modules``**,
importing nothing by name from the module under attack.

**EVERY PROPERTY HERE HAS TWO ARMS ON ONE AXIS (CD-D-079).** The control arm is a decorator
built THE OLD WAY — ``functools.wraps`` over a closure cell holding the naked function — so
each assertion is shown to move on exactly the structure it credits and on nothing else. An
attack that only ran against the fixed tree would prove that the attack does not work, which
is not the same claim as the fix working.

**AND THE RESIDUE IS CARRIED HERE TOO, NOT ONLY DECLARED.**
:func:`test_the_reconstitution_residue_is_real_and_is_declared_limit_10` PERFORMS the
reconstitution the declared limit names and asserts that it SUCCEEDS. A test suite that
asserted only the good news would let DECLARED LIMIT 10 go stale the day somebody believed it
closed.
"""

from __future__ import annotations

import functools
import inspect
import sys
import types
from datetime import datetime, timezone

import pytest

from crash_detector.admission import (
    AdmissionFault,
    NotAdmitted,
    declared_admissions,
    is_admitting_door,
)
from crash_detector.dials.dialset import EQUITY_DIAL_ID
from crash_detector.dials.reading import (
    AbsenceYieldedAValue,
    Reading,
    Unknown,
    Value,
)
from crash_detector.engine.config import DialSpec

from test_evaluate import DECLARES_A_MODEL, _spec, _value_reading

NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)

#: THE MODULE UNDER ATTACK, OBTAINED THE WAY THE ATTACK OBTAINS IT. `sys.modules` is the
#: route a conforming foreign `SourceAdapter` used on the second collection cycle to reach
#: the undecorated evaluator — no import statement naming it, no cast, no privilege.
_MODULE_PATH = "crash_detector.engine.evaluate"


def _module_from_sys_modules():
    __import__(_MODULE_PATH)
    return sys.modules[_MODULE_PATH]


def _starved() -> DialSpec:
    """A dial that DECLARES a required input and a model and did not get the input.

    Any reading carrying a value from this spec is CD-ASR-F03's own shape.
    """
    return _spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL)


# ==================================================================================== #
# THE WALK. One function, used by every arm, so the ATTACKED and the CONTROL arm are
# attacked by the identical code and can differ only in their subject.
# ==================================================================================== #


def _every_callable_reachable_from(door, module) -> dict:
    """Every CALLABLE the four named routes reach from ``door``, by route.

    The four routes are the ones the dispatch names, and they are walked in full rather than
    sampled: ``__closure__`` cells, ``__wrapped__``, ``__globals__``, and the module
    namespace. ``__globals__`` and the module namespace are the SAME dict for a function
    defined in that module and are walked separately anyway, because that identity is a fact
    about today's implementation and not a property anyone promised.
    """
    found: dict = {}

    found["__closure__"] = [
        cell.cell_contents
        for cell in (door.__closure__ or ())
        if callable(getattr(cell, "cell_contents", None))
    ]

    unwrapped = getattr(door, "__wrapped__", None)
    found["__wrapped__"] = [unwrapped] if callable(unwrapped) else []

    # `__globals__` and the module namespace are searched for CALLABLES THAT ARE NOT THE DOOR
    # ITSELF and that are defined in this module — a caller reaching `compute` or `Unknown`
    # through them has reached a name it could have imported, which is not a bypass of
    # anything. What would be a bypass is an undecorated form of the evaluator.
    for route, namespace in (
        ("__globals__", getattr(door, "__globals__", {}) or {}),
        ("module namespace", vars(module)),
    ):
        found[route] = [
            value
            for name, value in namespace.items()
            if callable(value)
            and value is not door
            and getattr(value, "__module__", None) == _MODULE_PATH
            and getattr(value, "__qualname__", "") in (
                door.__qualname__,
                f"{door.__qualname__}",
            )
        ]

    # AND THE ONE THAT IS NOT A NAMED ROUTE BUT IS THE OBVIOUS NEXT THING TO TRY: any
    # callable hanging off the door's own attribute dictionary.
    found["door.__dict__"] = [
        value for value in vars(door).values() if callable(value)
    ]
    return found


def _reaches_the_judgement_without_establishment(candidate) -> bool:
    """Does calling ``candidate`` produce a value-bearing reading from a starved dial?

    **THIS IS THE ATTACK'S PAYLOAD AND NOT A PROXY FOR IT.** The question the ruling asks is
    not "is there an object" but "can what is there be called to reach the judgement without
    establishment", so the candidate is CALLED and its answer is read.
    """
    try:
        answer = candidate(_starved(), {}, NOW)
    except Exception:
        return False
    return isinstance(answer, Value)


# ==================================================================================== #
# (a) NO UNDECORATED EVALUATOR OBJECT EXISTS AT RUNTIME.
# ==================================================================================== #


def _the_old_shape(evaluate_one_dial):
    """**THE CONTROL ARM.** The mechanism as it stood before WO-2R3 increment 8.

    Reconstructed here rather than referenced, because the shipped one is gone and a control
    arm that cannot be run is a sentence. It is the shape `PO-DECISIONS-0015` ruling 1 calls
    *"the defect class, not an implementation choice"*: a wrapper that keeps the naked
    callable alive in a closure cell.
    """

    @functools.wraps(evaluate_one_dial)
    def guarded(spec, usable, now_utc, *extra, **extra_by_name):
        reading = evaluate_one_dial(spec, usable, now_utc, *extra, **extra_by_name)
        from crash_detector.engine.evaluate import refuse_a_number_without_its_inputs

        refuse_a_number_without_its_inputs(spec, usable, reading)
        return reading

    return guarded


def _a_body_that_pays_a_number_for_nothing(
    spec: DialSpec, usable: dict, now_utc: datetime
) -> "Reading":
    """CD-ASR-F03's own shape: a value-bearing reading from a dial that got no inputs."""
    return _value_reading()


def test_the_attack_that_felled_the_ruling_finds_no_callable_at_all():
    """**PROPERTY (a), AND IT IS THE ATTACK ITSELF.**

    `PO-DECISIONS-0012` ruling 1 fell because a conforming foreign adapter obtained
    ``sys.modules[m]._evaluate_dial.__closure__[i].cell_contents`` and CALLED it, reaching the
    judgement with no door passed. This walks all four routes the dispatch names against the
    SHIPPED object obtained the same way, and asserts that **nothing any of them finds is a
    callable at all** — so there is nothing to call, let alone anything that reaches the
    judgement.

    **THE COUNTERFACTUAL ARM IS IN THE SAME TEST ON PURPOSE.** The identical walk against a
    decorator built the old way FINDS the naked callable AND reaches the judgement through
    it. One axis: whether the mechanism carries the body as a ``code`` object or as a function
    object. Nothing else differs between the two subjects.
    """
    module = _module_from_sys_modules()
    door = module._evaluate_dial

    # ---- ARM 1: THE SHIPPED DOOR. Every route, and the payload attempted on every hit.
    attacked = _every_callable_reachable_from(door, module)
    assert attacked["__closure__"] == [], (
        "A CALLABLE IS REACHABLE THROUGH THE GUARD'S OWN CLOSURE. `PO-DECISIONS-0015` "
        "ruling 1 (a) calls a wrapper that keeps the naked callable alive in a cell THE "
        "DEFECT CLASS, not an implementation choice. Found: "
        + repr([getattr(c, "__qualname__", c) for c in attacked["__closure__"]])
    )
    assert attacked["__wrapped__"] == [], (
        "the shipped evaluator publishes `__wrapped__`, which `inspect.unwrap` follows and "
        "editors offer — a bypass writable in ordinary-looking code (PO-DECISIONS-0013 "
        "ruling 2)"
    )
    assert attacked["__globals__"] == [], attacked["__globals__"]
    assert attacked["module namespace"] == [], attacked["module namespace"]
    assert attacked["door.__dict__"] == [], attacked["door.__dict__"]
    for route, candidates in attacked.items():
        for candidate in candidates:  # pragma: no cover - the lists above are empty
            assert not _reaches_the_judgement_without_establishment(candidate), (
                f"{route} reached {candidate!r} and calling it produced a value-bearing "
                "reading from a dial that got no inputs"
            )

    # ---- ARM 2: THE CONTROL. The same walk, the same payload, the OLD shape.
    control = _the_old_shape(_a_body_that_pays_a_number_for_nothing)
    old = _every_callable_reachable_from(control, module)
    assert old["__closure__"], (
        "THE CONTROL ARM FOUND NOTHING EITHER, so this test proves nothing about the fix. "
        "The old shape MUST expose the naked callable in a cell; if it does not, this "
        "control has stopped being a control and the whole assertion above is vacuous."
    )
    assert any(
        _reaches_the_judgement_without_establishment(candidate)
        for candidate in old["__closure__"]
    ), (
        "the control arm's closure cell did not reach the judgement, so the axis this test "
        "varies is not the axis that decides the outcome (CD-ENG-WO2R3-F12)"
    )
    assert old["__wrapped__"], "the control arm did not even set `__wrapped__`"


def test_the_shipped_mechanism_uses_no_functools_wraps_so_wrapped_is_never_created():
    """`PO-DECISIONS-0013` ruling 2, MET MORE STRONGLY THAN BY THE `delattr` IT REPLACES.

    *Superseded implementation (PBG-CONT-003): the mechanism called ``functools.wraps`` and
    then ``delattr(guarded, "__wrapped__")``* — it created the bypass and withdrew it inside
    one function, which leaves a window and leaves something for a future edit to reinstate by
    putting the decorator back. The attribute is now NEVER CREATED.

    **READ AS CODE AND NOT AS TEXT.** A ``grep`` here would match this file's own prose about
    the superseded implementation, which is exactly the kind of assertion that passes for the
    wrong reason.
    """
    import ast
    import pathlib

    source = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src" / "crash_detector" / "engine" / "evaluate.py"
    ).read_text()
    mechanism = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef)
        and node.name == "_absence_is_never_a_number"
    )
    decorators = {
        ast.unparse(d.func if isinstance(d, ast.Call) else d)
        for inner in ast.walk(mechanism)
        if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef))
        for d in inner.decorator_list
    }
    assert "functools.wraps" not in decorators, (
        "the CD-ASR-F03 mechanism has gone back to `functools.wraps`, which SETS "
        f"`__wrapped__`. PO-DECISIONS-0013 ruling 2 called that a PRODUCT DEFECT. {decorators}"
    )
    assert not any(
        isinstance(inner, ast.Constant) and inner.value == "__wrapped__"
        for inner in ast.walk(mechanism)
    ), (
        "the mechanism names `__wrapped__` in code again. It should have no reason to: the "
        "attribute is not created, so there is nothing to delete."
    )
    assert not hasattr(_module_from_sys_modules()._evaluate_dial, "__wrapped__")


def test_the_reconstitution_residue_is_real_and_is_declared_limit_10():
    """**THE RESIDUE, CARRIED RATHER THAN CLAIMED CLOSED.**

    Property (a) is met as the ruling states it — no undecorated evaluator OBJECT EXISTS. It
    is NOT a closure of the ``__closure__`` REACH, and this project's most-found defect is a
    declaration that is wrong in the reassuring direction. So the residue is asserted TRUE:
    ``types.FunctionType(code, globals)`` over the materials in the cells RECONSTITUTES a
    callable body, and calling it reaches the judgement.

    **IF THIS TEST EVER FAILS, DECLARED LIMIT 10 HAS BECOME OVERSTATED AND MUST BE CORRECTED
    IN ALL THREE CD-RULE-004 PLACES RATHER THAN QUIETLY ENJOYED** — which is the exact
    sentence the assertion this file replaces carried, and it is why anyone could tell that
    the closure route had closed.
    """
    module = _module_from_sys_modules()
    door = module._evaluate_dial
    cells = [cell.cell_contents for cell in (door.__closure__ or ())]

    codes = [value for value in cells if isinstance(value, types.CodeType)]
    assert len(codes) == 1, (
        "the mechanism no longer carries exactly one code object in its cells; DECLARED "
        f"LIMIT 10 describes a shape that is not there. Found {len(codes)}."
    )
    globals_dicts = [
        value for value in cells if isinstance(value, dict) and "Value" in value
    ]
    assert globals_dicts, "the body's globals are not in the cells; DECLARED LIMIT 10 moved"

    rebuilt = types.FunctionType(codes[0], globals_dicts[0])
    assert callable(rebuilt)
    # `model` is passed explicitly because the reconstitution above does not carry the
    # defaults — an attacker who wants them takes the `__defaults__` tuple out of the cells
    # too, which is one more line and no more privilege. Recorded rather than smoothed over.
    answer = rebuilt(_starved(), {}, NOW, None)
    assert isinstance(answer, Unknown), (
        "the reconstituted body did not behave like the evaluator, so this arm is measuring "
        "something other than the residue it claims to measure"
    )
    # AND THE HALF THAT MAKES IT A RESIDUE RATHER THAN A CURIOSITY: the reconstituted body
    # runs WITHOUT THE DOOR AND WITHOUT THE NET. Neither establishment nor the post-condition
    # is applied to it, because both live in the wrapper it is not.
    assert not is_admitting_door(rebuilt)


# ==================================================================================== #
# (b) THE ESTABLISHMENT IS DERIVED FROM THE SIGNATURE.
# ==================================================================================== #


def test_adding_a_parameter_is_established_without_anyone_editing_the_guard():
    """**PROPERTY (b), AND THE DISPATCH CALLS THIS CONTRAST "THE WHOLE OF (b)".**

    *"ADD A PARAMETER AND SHOW THE GUARD STILL COVERS IT, WITHOUT ANYONE EDITING THE GUARD."*

    The evaluator below has a FOURTH parameter that no line of
    ``_absence_is_never_a_number`` mentions, and the mechanism applied to it is the shipped
    one, unedited and imported rather than copied. The new parameter is established BY EXACT
    TYPE on the first run, because the annotation IS the declaration.

    **THE COUNTERFACTUAL ARM (CD-D-079) IS THE OLD NET'S OWN SHAPE**, whose ``*extra`` existed
    for precisely this case and BOUND NOTHING — which is the finding `PO-DECISIONS-0015`
    ruling 1 records. Same body, same argument, opposite outcome, and the only difference is
    whether the wrapper derives or gapes.
    """
    module = _module_from_sys_modules()

    def a_body_with_a_fourth_parameter(
        spec: DialSpec, usable: dict, now_utc: datetime, weighting: float
    ) -> "Reading":
        return Unknown(reason="planted", since_utc=now_utc, missing_inputs=())

    door = module._absence_is_never_a_number(a_body_with_a_fourth_parameter)

    # THE GUARD KNOWS ABOUT THE NEW PARAMETER, AND NOBODY TOLD IT.
    assert is_admitting_door(door)
    assert sorted(declared_admissions(door)) == [
        "now_utc", "spec", "usable", "weighting",
    ]
    assert declared_admissions(door)["weighting"].describe() == "float"

    # AND IT REFUSES A VALUE OF THE WRONG EXACT TYPE THROUGH IT.
    assert isinstance(door(_spec(EQUITY_DIAL_ID), {}, NOW, 1.0), Unknown)
    with pytest.raises(NotAdmitted) as refused:
        door(_spec(EQUITY_DIAL_ID), {}, NOW, "1.0")
    assert "weighting" in str(refused.value)

    # ---- THE COUNTERFACTUAL: the old net's shape, same body, same argument.
    def the_old_net(evaluate_one_dial):
        @functools.wraps(evaluate_one_dial)
        def guarded(spec, usable, now_utc, *extra, **extra_by_name):
            return evaluate_one_dial(spec, usable, now_utc, *extra, **extra_by_name)

        return guarded

    gaping = the_old_net(a_body_with_a_fourth_parameter)
    assert isinstance(gaping(_spec(EQUITY_DIAL_ID), {}, NOW, "1.0"), Unknown), (
        "the control arm refused too, so the axis this test varies is not the axis that "
        "decides the outcome (CD-ENG-WO2R3-F12)"
    )
    assert not is_admitting_door(gaping)


def test_a_parameter_with_no_annotation_faults_the_door_at_import_time():
    """Deny by default. The annotation IS the declaration, so a parameter without one is a
    parameter with no declaration, and the mechanism REFUSES rather than admitting it.

    The refusal is at DECORATION, which for a module-level ``def`` is at import: the module
    does not load rather than loading with an unguarded door.
    """
    module = _module_from_sys_modules()

    def unannotated(spec: DialSpec, usable: dict, now_utc: datetime, weighting) -> "Reading":
        return Unknown(reason="planted", since_utc=now_utc, missing_inputs=())

    with pytest.raises(AdmissionFault) as fault:
        module._absence_is_never_a_number(unannotated)
    assert "weighting" in str(fault.value)
    assert "NO ANNOTATION" in str(fault.value)


@pytest.mark.parametrize(
    "channel", ["*extra", "**extra_by_name"], ids=["var-positional", "var-keyword"]
)
def test_an_open_channel_on_this_guard_faults_the_door(channel):
    """**THE OLD NET HAD BOTH OF THESE AND THAT IS WHAT RULING 1 FOUND.**

    An open channel cannot be derived from, because there is no name in the signature to
    derive from. The mechanism refuses at decoration rather than admitting values with no
    name to declare and no type to require — which is the same refusal ``admits`` makes for
    the general case, in the same words.
    """
    module = _module_from_sys_modules()
    namespace: dict = {
        "DialSpec": DialSpec,
        "datetime": datetime,
        "Unknown": Unknown,
        "Reading": Reading,
    }
    exec(  # noqa: S102 - the parameter list is the subject of this test
        "def body(spec: DialSpec, usable: dict, now_utc: datetime, "
        f"{channel}: object) -> 'Reading':\n"
        "    return Unknown(reason='planted', since_utc=now_utc, missing_inputs=())\n",
        namespace,
    )
    with pytest.raises(AdmissionFault) as fault:
        module._absence_is_never_a_number(namespace["body"])
    assert "OPEN CHANNEL" in str(fault.value)


def test_the_declaration_is_compiled_by_the_projects_ONE_vocabulary():
    """The establishment is compiled through :func:`crash_detector.admission.declaration` —
    the same function ``admits`` and ``establishes`` use — and not by a second vocabulary
    grown here.

    ``admission.py`` says why in terms: *"Two declaration vocabularies that drift apart is how
    a reader comes to believe a field is established as strictly as a parameter when it is
    not; there is one, and it is here."* The assertion is that the objects this door publishes
    are the SAME CLASS the one vocabulary produces, read from the runtime and not from source.
    """
    from crash_detector.admission import declaration

    door = _module_from_sys_modules()._evaluate_dial
    published = declared_admissions(door)
    assert published, "the door publishes no declaration at all"
    for name, admission in published.items():
        assert type(admission) in {
            type(declaration("x", DialSpec)),
            type(declaration("x", (DialSpec, type(None)))),
        }, (name, type(admission))
    # AND THE UNION SPELLING IS UNWRAPPED RATHER THAN PASSED THROUGH WHOLE.
    assert published["model"].describe() == "ModelSpec or None"
    # AND THE SUBSCRIPT IS DROPPED TO ITS ORIGIN, WHICH IS DECLARED LIMIT 11.
    assert published["usable"].describe() == "dict"


# ==================================================================================== #
# (c) THE POST-CONDITION IS RETAINED INSIDE THE SAME MECHANISM.
# ==================================================================================== #


def test_the_post_condition_still_refuses_a_number_a_rewritten_body_paid_for():
    """**PROPERTY (c).** The door and the net are one object, so the redesign that added the
    establishment must not have cost the post-condition.

    CD-ASR-F03's own shape: the mechanism is applied to a body that returns a value-bearing
    reading having received no inputs at all. The counterfactual arm is the identical body
    with no mechanism applied, which does not refuse.
    """
    module = _module_from_sys_modules()
    door = module._absence_is_never_a_number(_a_body_that_pays_a_number_for_nothing)
    with pytest.raises(AbsenceYieldedAValue):
        door(_starved(), {}, NOW)
    assert isinstance(
        _a_body_that_pays_a_number_for_nothing(_starved(), {}, NOW), Value
    ), "the counterfactual arm refused too, so the mechanism is not what refuses"


def test_the_post_condition_arguments_are_derived_from_its_own_signature():
    """(c)'s other half: WHICH arguments the post-condition receives is derived too, so the
    post-condition can grow a parameter without anyone editing the wrapper — and a
    post-condition asking for something the door does not have is refused AT IMPORT rather
    than at a gate.
    """
    module = _module_from_sys_modules()
    signature = inspect.signature(module._evaluate_dial, follow_wrapped=False)

    def asks_for_nothing_the_door_has(alpha, beta):
        return None

    with pytest.raises(AdmissionFault) as fault:
        module._post_condition_order(signature, asks_for_nothing_the_door_has)
    assert "EXACTLY ONE MUST BE OUTSTANDING" in str(fault.value)

    # THE SHIPPED PAIRING, DERIVED: two names matched to the door's own bound arguments and
    # exactly one outstanding slot for what the body returned.
    order = module._post_condition_order(
        signature, module.refuse_a_number_without_its_inputs
    )
    assert order == ("spec", "usable", None)


def test_the_guard_and_the_guarded_are_the_same_object():
    """*"The guard and the guarded are inseparable"* is a statement about OBJECT IDENTITY.

    There is exactly one object at ``crash_detector.engine.evaluate._evaluate_dial``; it is
    the wrapper; it carries the establishment AND the post-condition; and there is no second
    object anywhere that is the body on its own. The last clause is what
    :func:`test_the_attack_that_felled_the_ruling_finds_no_callable_at_all` measures; this one
    asserts the first three, which is what makes "the same mechanism" checkable.
    """
    module = _module_from_sys_modules()
    door = module._evaluate_dial
    assert is_admitting_door(door)
    assert getattr(door, "__admission_faults__") == ()
    assert door.__qualname__ == "_evaluate_dial"
    assert list(inspect.signature(door).parameters) == [
        "spec", "usable", "now_utc", "model",
    ]
    with pytest.raises(NotAdmitted):
        door(object(), {}, NOW)
    with pytest.raises(AbsenceYieldedAValue):
        module._absence_is_never_a_number(_a_body_that_pays_a_number_for_nothing)(
            _starved(), {}, NOW
        )
