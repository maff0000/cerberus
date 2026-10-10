"""THE RUNTIME CARRIER FOR THE SEAL — WO-2R3 INCREMENT 9, `PO-DECISIONS-0016` ruling 2.

**A SEAL THAT IS NEVER TESTED IS A ``__slots__`` LINE.** The register check
``tools/register/check_sealed_against_forged_establishment.py`` ENUMERATES and REPORTS; this
file is what FAILS. Both exist because a check that both measures a property and is the only
thing that would notice its removal is one instrument wearing two hats.

**"UNCONSTRUCTIBLE", "SEALED" AND "CANNOT BE FORGED" ARE RUNTIME CLAIMS, AND EVERY ESCAPE ON
THIS PROJECT'S RECORD PASSED A STATIC CHECKER.** So every assertion below CONSTRUCTS the
thing, reads the EXCEPTION TYPE and the MESSAGE, and names the layer that refused **from the
failure text and never from the exit code** (the ``CD-ENG-WO2R3-F12`` standard). Two arms
that both fail for different reasons look identical in a summary table and prove nothing.

WHAT EACH TEST HERE IS FOR
--------------------------
1. the route the record names is REFUSED, and the refusal is read from its text;
2. the ``__setstate__`` SIBLING is refused too, in BOTH of its state shapes;
3. **THE COUNTERFACTUAL (CD-D-079)** — with the seal removed from one class in a throwaway
   tree, the SAME route SUCCEEDS and yields an object of exactly that type carrying a value
   the front door refuses. Without this, every assertion above is consistent with the route
   never having worked;
4. **THE INSTRUMENT'S OWN CONTRAST** — the check exits 0 on the tree and exits 1 naming
   ``OPEN TO FORGED STATE`` on the same tree with one seal removed;
5. **THE VACUITY GUARD ON THE EXCLUSION CLAUSE** — an exclusion that excluded everything
   would pass every run. The check must still FAIL when a class the seal IS available to is
   opened;
6. **THE DERIVATION DIFF IS NOT DECORATION** — a class built by ``type(...)`` at module level
   is live and invisible to the source reading, and the check must say so;
7. **THE FALSE-GREEN PROOF (`CD-ENG-WO2R3-07-F01`)** — ``@dataclass(frozen=True, slots=True)``
   ALONE does not close the property, because CPython installs a stdlib ``__setstate__`` that
   writes whatever it is handed with no package code at all. This is the finding that decided
   the mechanism this increment applied, and it is carried here so that a future seat which
   "simplifies" the seal to that decorator fails a test instead of shipping a false green.
"""

from __future__ import annotations

import dataclasses
import pathlib
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import pytest

from crash_detector.witness.panel import Agrees

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_CHECK = "check_sealed_against_forged_establishment.py"
_PANEL = pathlib.Path("src") / "crash_detector" / "witness" / "panel.py"

#: The exact bytes the counterfactual removes. If this literal stops matching, the subject
#: MOVED and the test says so rather than passing vacuously.
_AGREES_SLOTS = '    __slots__ = ("divergence_measure", "as_of_utc", "freshness")'

_FORGED = "not a datetime"


def _throwaway_tree() -> pathlib.Path:
    """A copy carrying ``src/`` and ``tools/``.

    Not a fixture, on purpose: each arm mutates its own copy and runs THAT TREE'S OWN COPY of
    the instrument, so no two arms can share a tree and quietly measure the same thing twice
    (``CD-PL-F98``).
    """
    destination = pathlib.Path(tempfile.mkdtemp(prefix="cd-seal-"))
    for part in ("src", "tools"):
        shutil.copytree(_REPO_ROOT / part, destination / part)
    return destination


def _run_check(tree: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(tree / "tools" / "register" / _CHECK), "--root", str(tree)],
        capture_output=True,
        text=True,
    )


def _package_lines(work) -> "tuple[object, BaseException | None, int]":
    """Run ``work`` and COUNT the lines executed under ``crash_detector``.

    The property is *"executes no package code"*, and a property about execution is measured
    by tracing execution. This is the same instrument ``P-E23`` arm 1 used.
    """
    executed = 0

    def trace(frame, event, _arg):
        nonlocal executed
        name = frame.f_globals.get("__name__", "")
        if event == "line" and (name == "crash_detector" or name.startswith("crash_detector.")):
            executed += 1
        return trace

    previous = sys.gettrace()
    sys.settrace(trace)
    try:
        result, error = None, None
        try:
            result = work()
        except BaseException as exc:  # noqa: BLE001 — the refusal is the measurement
            error = exc
    finally:
        sys.settrace(previous)
    return result, error, executed


# ===================================================================================== #
# 1 and 2 — THE ROUTES, REFUSED, WITH THE LAYER READ FROM THE FAILURE TEXT.
# ===================================================================================== #


def test_the_new_plus_dict_update_route_is_refused_and_the_refusal_is_the_missing___dict__():
    """``Agrees.__new__(Agrees)`` then ``__dict__.update`` — the route the record names.

    Before this increment this route returned an object of exactly type ``Agrees`` carrying
    ``as_of_utc == 'not a datetime'`` having executed **ZERO** lines of package code
    (``P-E23`` arm 1). The refusal asserted here is the INTERPRETER's, not a guard's, and
    that is the strongest form available: there is no ``__dict__`` to write into.
    """
    subject = Agrees.__new__(Agrees)
    with pytest.raises(AttributeError) as raised:
        subject.__dict__.update({"as_of_utc": _FORGED})
    assert "__dict__" in str(raised.value), str(raised.value)
    assert "Agrees" in str(raised.value), str(raised.value)
    assert Agrees.__dictoffset__ == 0, (
        f"Agrees.__dictoffset__ is {Agrees.__dictoffset__}. __slots__ alone closes nothing "
        "if any base carries a __dict__; the seal is slots PLUS an empty __dictoffset__."
    )


def test_the_front_door_refuses_the_same_values_and_it_is_PACKAGE_CODE_that_refuses():
    """The CONTROL half of the contrast, and the half that names the layer.

    A refusal is only evidence of a boundary if the boundary ran. The forged route refuses
    with **0** package lines (the interpreter); the front door refuses with **many** (this
    package's establishment boundary). Both numbers are asserted, because either alone can be
    read the wrong way.
    """
    _result, error, executed = _package_lines(
        lambda: Agrees(divergence_measure=0.0, as_of_utc=_FORGED, freshness=None)
    )
    assert error is not None, "the front door ACCEPTED a string where a datetime is declared"
    assert type(error).__name__ in {"FieldNotEstablished", "TypeError", "UndeclaredField"}, (
        f"the front door refused with {type(error).__name__}: {error} — which is a refusal, "
        "but not one this test recognises. Read the text before adjusting the assertion."
    )
    assert executed > 0, (
        "the front door refused having executed ZERO lines of package code, which would mean "
        "the refusal came from the interpreter and not from this package's boundary."
    )

    _forged, forged_error, forged_executed = _package_lines(
        lambda: Agrees.__new__(Agrees).__dict__.update({"as_of_utc": _FORGED})
    )
    assert isinstance(forged_error, AttributeError), forged_error
    assert forged_executed == 0, (
        f"the forged route executed {forged_executed} lines of package code. That is not a "
        "failure of the seal, but it means this contrast is not measuring what it says."
    )


@pytest.mark.parametrize(
    "state",
    [
        pytest.param({"divergence_measure": 0.0, "as_of_utc": _FORGED, "freshness": None},
                     id="MAPPING-state"),
        pytest.param([0.0, _FORGED, None], id="SEQUENCE-state"),
    ],
)
def test_the_setstate_sibling_is_refused_in_BOTH_of_its_state_shapes(state):
    """``__setstate__`` — the sibling the ruling names — in both shapes that exist here.

    **BOTH SHAPES, BECAUSE ONE SHAPE ALONE MEASURED THIS PROJECT'S OWN TREE WRONG.** CPython's
    ``dataclasses._dataclass_setstate`` ZIPS ``fields(self)`` against the state, so handed a
    MAPPING it iterates the keys and writes field names as values — an object that is forged
    and does not carry the marker a naive check reads back. ``DialMagnitude.__setstate__`` and
    ``DeclaredQuantity.__setstate__`` INDEX BY NAME and need the mapping. A route that fails
    for the wrong reason scores a class closed.
    """
    subject = Agrees.__new__(Agrees)
    assert not hasattr(subject, "__setstate__"), (
        "Agrees carries a __setstate__. If it was installed by @dataclass(slots=True) it is "
        "dataclasses._dataclass_setstate, which writes any state it is handed through "
        "object.__setattr__ with NO validation and NO package code — the seal is open by its "
        "sibling. If this package DEFINED it, it must revive through the same validation the "
        "constructor uses, as DialMagnitude and DeclaredQuantity do."
    )
    with pytest.raises(AttributeError) as raised:
        subject.__setstate__(state)
    assert "__setstate__" in str(raised.value), str(raised.value)


# ===================================================================================== #
# 3 — THE COUNTERFACTUAL. CD-D-079.
# ===================================================================================== #


def test_COUNTERFACTUAL_with_the_seal_removed_the_same_route_forges_an_exact_Agrees():
    """**WITHOUT THIS TEST EVERY ASSERTION ABOVE IS CONSISTENT WITH A ROUTE THAT NEVER WORKED.**

    A throwaway tree with ``Agrees.__slots__`` deleted and nothing else changed. The same
    route, run against THAT tree's own package in a subprocess, returns an object of exactly
    type ``Agrees`` carrying ``'not a datetime'`` — and reports the package lines it executed
    to get there, which must be **0**.
    """
    tree = _throwaway_tree()
    try:
        panel = tree / _PANEL
        source = panel.read_text()
        assert _AGREES_SLOTS in source, "the subject of this test moved; fix the test"
        panel.write_text(source.replace(_AGREES_SLOTS + "\n", "", 1))

        program = (
            "import sys\n"
            "executed = 0\n"
            "def trace(frame, event, arg):\n"
            "    global executed\n"
            "    n = frame.f_globals.get('__name__', '')\n"
            "    if event == 'line' and (n == 'crash_detector' or n.startswith('crash_detector.')):\n"
            "        executed += 1\n"
            "    return trace\n"
            "from crash_detector.witness.panel import Agrees\n"
            "sys.settrace(trace)\n"
            "smuggled = Agrees.__new__(Agrees)\n"
            "smuggled.__dict__.update({'as_of_utc': 'not a datetime'})\n"
            "sys.settrace(None)\n"
            "print('EXACT', type(smuggled) is Agrees)\n"
            "print('VALUE', repr(smuggled.as_of_utc))\n"
            "print('PACKAGE_LINES', executed)\n"
            "print('TREE', Agrees.__module__, sys.modules['crash_detector'].__file__)\n"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", program],
            capture_output=True, text=True, cwd=str(tree),
            env={"PYTHONPATH": str(tree / "src"), "PATH": "/usr/bin:/bin"},
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "EXACT True" in result.stdout, result.stdout
        assert "VALUE 'not a datetime'" in result.stdout, result.stdout
        assert "PACKAGE_LINES 0" in result.stdout, result.stdout
        # CD-PL-F98: prove the arm read the THROWAWAY tree and not this one.
        assert str(tree) in result.stdout, result.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


# ===================================================================================== #
# 4, 5 — THE INSTRUMENT'S OWN CONTRAST, AND THE VACUITY GUARD ON THE EXCLUSION CLAUSE.
# ===================================================================================== #


def test_the_check_is_clean_on_this_tree_and_says_what_it_measured():
    """CLEAN ARM. A run that asserts nothing is not a clean run — the count is asserted."""
    tree = _throwaway_tree()
    try:
        result = _run_check(tree)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OPEN AND REQUIRED" in result.stdout, result.stdout
        assert "0 OPEN AND REQUIRED" in result.stdout, result.stdout
        assert "EXCLUDED BY MEASUREMENT" in result.stdout, result.stdout
        assert "0 UNMEASURABLE" in result.stdout, (
            "the check reported classes whose seal availability it could not measure. An "
            "unmeasured exclusion is not an exclusion." + result.stdout
        )
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_VIOLATED_ARM_removing_one_seal_fails_the_check_AT_THE_LAYER_ITS_PROPOSITION_NAMES():
    """VIOLATED ARM — and the assertion is on the VIOLATION TEXT, never on the exit code.

    This is simultaneously the VACUITY GUARD on the exclusion clause (test 5). An exclusion
    clause that excluded everything would pass this arm; ``Agrees`` has no base imposing a
    ``__dict__``, so the seal IS available to it and the clause must NOT excuse it.
    """
    tree = _throwaway_tree()
    try:
        panel = tree / _PANEL
        source = panel.read_text()
        assert _AGREES_SLOTS in source, "the subject of this test moved; fix the test"
        panel.write_text(source.replace(_AGREES_SLOTS + "\n", "", 1))

        result = _run_check(tree)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "OPEN TO FORGED STATE" in result.stdout, result.stdout
        assert "Agrees" in result.stdout, result.stdout
        assert "1 OPEN AND REQUIRED" in result.stdout, (
            "exactly one class should have become open. A different number means this arm "
            "changed more than it says it did." + result.stdout
        )
        assert "R1 cls.__new__(cls) + __dict__.update" in result.stdout, result.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


# ===================================================================================== #
# 6 — THE TWO DERIVATIONS DISAGREEING IS A VIOLATION AND NOT A RECONCILIATION.
# ===================================================================================== #


def test_a_class_built_by_type_at_module_level_makes_the_two_enumerations_disagree():
    """The derivation diff is not decoration, and here is the arm that proves it.

    A class built by ``type(...)`` is LIVE and invisible to any source reading. The check must
    REPORT the difference rather than adopt either side, take the union or take the
    intersection.
    """
    tree = _throwaway_tree()
    try:
        panel = tree / _PANEL
        panel.write_text(
            panel.read_text()
            + '\n\nSmuggled = type("Smuggled", (object,), {"as_of_utc": None})\n'
        )
        result = _run_check(tree)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "ENUMERATIONS DISAGREE" in result.stdout, result.stdout
        assert "Smuggled" in result.stdout, result.stdout
        assert "LIVE AND NOT IN THE SOURCE: 1" in result.stdout, result.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


# ===================================================================================== #
# 7 — THE FALSE-GREEN PROOF. CD-ENG-WO2R3-07-F01.
# ===================================================================================== #


def test_dataclass_slots_ALONE_does_not_close_the_property_and_this_is_why_it_was_not_used():
    """**THE FINDING THAT DECIDED THIS INCREMENT'S MECHANISM, CARRIED SO IT CANNOT REGRESS.**

    ``@dataclass(frozen=True, slots=True)`` is the obvious remedy and the dispatch named it.
    CPython's ``dataclasses._add_slots`` ends with two UNCONDITIONAL lines that install
    ``_dataclass_getstate``/``_dataclass_setstate``, and the setter writes every value it is
    handed through ``object.__setattr__`` with no validation and **no package code**. So the
    class passes ``"__slots__" in vars(cls) and not cls.__dictoffset__`` — the exact test both
    readings handed to this seat used — **and is still forgeable by the sibling route the
    ruling itself names.**

    A future seat that "simplifies" the seal to that decorator alone fails HERE, in a test,
    instead of shipping a green board over an open class.
    """

    @dataclasses.dataclass(frozen=True, slots=True)
    class LooksSealed:
        as_of_utc: datetime

    assert "__slots__" in vars(LooksSealed)
    assert LooksSealed.__dictoffset__ == 0
    assert hasattr(LooksSealed, "__setstate__"), (
        "CPython no longer installs a stdlib __setstate__ for a frozen slotted dataclass. "
        "That would make @dataclass(frozen=True, slots=True) sufficient on its own and this "
        "test would be describing history — re-measure before deleting it."
    )
    assert LooksSealed.__setstate__.__module__ == "dataclasses", (
        f"__setstate__ came from {LooksSealed.__setstate__.__module__}, not the stdlib."
    )

    smuggled = LooksSealed.__new__(LooksSealed)
    _r, error, executed = _package_lines(lambda: smuggled.__setstate__([_FORGED]))
    assert error is None, f"the sibling route was refused: {error!r}"
    assert type(smuggled) is LooksSealed
    assert smuggled.as_of_utc == _FORGED, (
        "the state did not land. _dataclass_setstate ZIPS fields against the state, so a "
        "MAPPING writes field NAMES as values; this arm passes a SEQUENCE on purpose."
    )
    assert executed == 0, (
        f"{executed} lines of package code ran. The point of this test is that ZERO do."
    )

    # And the shape this project actually applies: manual __slots__, no __setstate__ at all.
    assert not hasattr(Agrees, "__setstate__"), (
        "Agrees has acquired a __setstate__. If it is the stdlib one, the seal on the whole "
        "governed class has quietly regressed to the false-green form this test exists for."
    )
