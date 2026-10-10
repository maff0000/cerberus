"""THE CARRIER FOR `F-06-K` — MODULE SCOPE IS NOT `tree.body`, AND THE DIFFERENCE IS AN ESCAPE.

WO-2R3 increment 8, item 5. The sixth Assurance seat measured that increment 7 closed one
``for node in tree.body`` residual and **added three**, leaving a net **+2** across the two
governing instruments, and that the escape it opens *"is uncarried anywhere"*.

**THIS FILE IS THAT CARRIER, AND EVERY TEST IN IT FAILED BEFORE THE FIX.** Measured at
``4410275f3fd3fc6cb419265a8d782edb3301ddcf`` on pristine ``git archive`` extractions before
a line was changed — the numbers are in ``BL-...-0061`` and every one of them came out of a
run and not out of a document (CD-RULE-009).

WHY A `tree.body` READING IS NOT "MODULE LEVEL"
------------------------------------------------
``for node in tree.body`` enumerates statements that are module-level **and not indented**.
Python does not agree that those are the same set: a name bound inside a module-level
``if TYPE_CHECKING:``, ``try:``/``except ImportError:``, ``with``, ``for`` or ``while``
is bound in the module namespace exactly as a top-level one is, and is importable,
callable and reachable identically. **The instruments could not see any of it.**

THE FOUR SITES, AND WHAT EACH ONE'S BLINDNESS COSTS
-----------------------------------------------------
=========================================================  =====================================
site                                                        what the blindness does
=========================================================  =====================================
``check_constructor_field_establishment.py``                drops types out of the GOVERNED
  ``_module_level_names``                                   CLASS — **converts a real FAIL
                                                            into a PASS**
``check_judgement_path_doors.py`` ``_module_bindings``      the reachability clause calls a
                                                            REACHABLE callable unreachable —
                                                            **converts the RIGHT violation
                                                            into the WRONG one. NOT into a
                                                            pass: measured, and see the
                                                            second doors test for why I
                                                            could not build that arm**
``check_judgement_path_doors.py`` NET resolution            a resolvable post-condition is
``check_judgement_path_doors.py`` NET fetch                  reported UNRESOLVABLE — a FALSE
                                                            VIOLATION, the safe direction, and
                                                            still wrong
=========================================================  =====================================

**THE MIDDLE ROW IS THE CONVERGENCE WITH GROUND 1** and it is why this item had to be taken
BEFORE the CD-ASR-F03 criterion redesign: ``_module_bindings`` is the function the
reachability criterion reasons over, so *"real public binding"* computed by it was already
wrong before the redesign asked it a question.

**THE `CD-ENG-WO2R3-F12` STANDARD IS APPLIED THROUGHOUT.** Two arms exiting 1 for different
reasons look identical in a summary table and prove nothing, so every assertion below is on
the VIOLATION CODE and not on the exit code alone — except where the contrast genuinely is
``EXIT 0 -> EXIT 1``, and that one is marked.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _throwaway_tree() -> pathlib.Path:
    """A copy carrying ``src/`` and ``tools/``. Not a fixture on purpose: each arm mutates
    its own copy and runs THAT TREE'S OWN COPY of the instrument, so no two arms can share
    a tree and quietly measure the same thing twice (CD-PL-F98)."""
    destination = pathlib.Path(tempfile.mkdtemp(prefix="cd-modscope-"))
    for part in ("src", "tools"):
        shutil.copytree(_REPO_ROOT / part, destination / part)
    return destination


def _run(tree: pathlib.Path, check: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(tree / "tools" / "register" / check), "--root", str(tree)],
        capture_output=True,
        text=True,
    )


_OBSERVATIONS = pathlib.Path("src") / "crash_detector" / "observations.py"
_EVALUATE = pathlib.Path("src") / "crash_detector" / "engine" / "evaluate.py"

_ESTABLISHES_ON_FETCHFAILED = """@establishes(
    error_class=str,
    http_status=one_of(int, None),
)
@dataclass(frozen=True, slots=True)
class FetchFailed:"""

#: WHAT THE CONTROL ARM LEAVES BEHIND. It strips ``@establishes`` and NOTHING ELSE — the
#: ``slots=True`` stays, because the axis of this contrast is the ``if True:`` and an arm
#: that also unsealed the type would be two changes wearing one name (``CD-ENG-WO2R3-F12``).
_FETCHFAILED_WITHOUT_ESTABLISHES = "@dataclass(frozen=True, slots=True)\nclass FetchFailed:"

_FETCH_OUTCOME_UNION = "FetchOutcome = Union[OK, FetchFailed, Malformed, Empty]"


# ===================================================================================== #
# SITE 1 — `check_constructor_field_establishment.py:_module_level_names`.
#          THE ONE THAT CONVERTS A REAL FAIL INTO A PASS.
# ===================================================================================== #


def test_a_union_hidden_in_a_module_level_block_cannot_shrink_the_governed_class():
    """**THREE ARMS ON ONE AXIS, AND THE AXIS IS THE `if True:`.**

    * CLEAN — the tree as it stands.
    * CONTROL (CD-D-079) — ``@establishes`` stripped from ``FetchFailed``, which is a
      REAL violation of the rule this check exists to enforce. It must FAIL.
    * ESCAPE — **the same real violation**, plus ``FetchOutcome = Union[...]`` wrapped in
      ``if True:``. Nothing about the violation changed. If the check now passes, the
      escape is a way to take any class out of the governed population by indenting one
      line, and the check's own PASS means nothing.

    **MEASURED AT THE BASE SHA, ALL THREE ARMS: clean PASS/101/pop 33 EXIT 0 · control
    FAIL/1 violation/pop 33 EXIT 1 · escape PASS/91 assertions/pop 30 EXIT 0.** The escape
    arm is the failure this test exists to prevent, and it is the reason ``if True:`` and
    not a contrived construct: the population line moves 33 -> 30 and the verdict moves
    FAIL -> PASS with the defect untouched.
    """
    tree = _throwaway_tree()
    try:
        observations = tree / _OBSERVATIONS
        source = observations.read_text()
        assert _ESTABLISHES_ON_FETCHFAILED in source, "the subject of this test moved; fix the test"
        assert _FETCH_OUTCOME_UNION in source, "the subject of this test moved; fix the test"

        clean = _run(tree, "check_constructor_field_establishment.py")
        assert clean.returncode == 0, clean.stdout + clean.stderr

        violated = source.replace(
            _ESTABLISHES_ON_FETCHFAILED, _FETCHFAILED_WITHOUT_ESTABLISHES, 1
        )
        observations.write_text(violated)
        control = _run(tree, "check_constructor_field_establishment.py")
        assert control.returncode == 1, (
            "THE CONTROL ARM DID NOT FAIL. Stripping `@establishes` from a fielded member "
            "of the governed class must be a violation, and if it is not then this whole "
            "test is measuring nothing (CD-D-079).\n" + control.stdout
        )

        observations.write_text(
            violated.replace(
                _FETCH_OUTCOME_UNION, "if True:\n    " + _FETCH_OUTCOME_UNION, 1
            )
        )
        escape = _run(tree, "check_constructor_field_establishment.py")
        assert escape.returncode == 1, (
            "**INDENTING ONE LINE TOOK THREE TYPES OUT OF THE GOVERNED CLASS AND TURNED A "
            "REAL FAIL INTO A PASS.** `FetchOutcome = Union[...]` moved inside a "
            "module-level `if` block, so `_module_level_names` — which reads `tree.body` — "
            "stopped resolving it, and `FetchFailed`, `Malformed` and `Empty` left the "
            "population with the violation still in the file. A guard that can be removed "
            "by indentation is not a guard.\n" + escape.stdout
        )
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_the_population_is_the_same_whether_the_union_is_indented_or_not():
    """The same fact stated as an INVARIANT rather than as a verdict, because a verdict can
    be right for the wrong reason. The governed population must not depend on whether a
    module-level binding happens to be indented."""
    tree = _throwaway_tree()
    try:
        observations = tree / _OBSERVATIONS
        source = observations.read_text()
        flat = _run(tree, "check_constructor_field_establishment.py")
        observations.write_text(
            source.replace(_FETCH_OUTCOME_UNION, "if True:\n    " + _FETCH_OUTCOME_UNION, 1)
        )
        indented = _run(tree, "check_constructor_field_establishment.py")

        def population(result):
            return result.stdout.split("measures the population at")[1].split(".")[0].strip()

        assert flat.returncode == 0 and indented.returncode == 0, (
            flat.stdout + indented.stdout
        )
        assert population(flat) == population(indented), (
            f"THE GOVERNED POPULATION MOVED ON AN INDENT: {population(flat)} -> "
            f"{population(indented)}. Membership is being decided by source layout."
        )
    finally:
        shutil.rmtree(tree, ignore_errors=True)


# ===================================================================================== #
# SITE 2 — `check_judgement_path_doors.py:_module_bindings`.
#          THE ONE THE REACHABILITY CRITERION REASONS OVER (GROUND 1's convergence).
# ===================================================================================== #

#: A private factory returning a function-local callable, and a PUBLIC module-level name
#: holding the factory's return value — bound INSIDE a module-level block. The object is
#: reachable as `module.public_evaluator` by anyone who can import the module.
_FACTORY_BEHIND_A_BLOCK = '''

def _install_evaluator():
    def decide(spec, usable, now_utc):
        return Unknown(reason="planted", since_utc=now_utc, missing_inputs=())

    return decide


if True:
    public_evaluator = _install_evaluator()
'''


def test_a_public_module_level_binding_written_inside_a_block_is_a_real_binding():
    """**GROUND 1's CRITERION IS ONLY AS GOOD AS THE BINDINGS IT CAN SEE.**

    ``_reachable_public_binding`` asks ``_module_bindings`` where a function-local
    callable's escape route LANDS. Until this increment that map was built from
    ``tree.body``, so a public module-level name bound inside ``if``/``try``/``with``/
    ``for``/``while`` did not exist as far as the criterion was concerned — and the
    criterion answered UNREACHABLE about an object any importer can obtain and call.

    **BOTH ARMS EXIT 1, WHICH IS EXACTLY WHY THIS ASSERTS THE VIOLATION CODE AND NOT THE
    EXIT CODE** (``CD-ENG-WO2R3-F12``). On a RULE 1 judgement path the NETS population
    denies by default, so at the base SHA the plant failed as ``UNCLASSIFIED_INTERCEPTOR``
    — the check refusing an object it believed unreachable — while the truth is
    ``UNDECORATED_JUDGEMENT_PATH_DOOR``. Same exit code, opposite diagnosis.
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / _EVALUATE
        clean = _run(tree, "check_judgement_path_doors.py")
        assert clean.returncode == 0, clean.stdout + clean.stderr

        evaluate_py.write_text(evaluate_py.read_text() + _FACTORY_BEHIND_A_BLOCK)
        planted = _run(tree, "check_judgement_path_doors.py")

        assert planted.returncode == 1, planted.stdout + planted.stderr
        assert "UNDECORATED_JUDGEMENT_PATH_DOOR" in planted.stdout, (
            "THE REACHABILITY CLAUSE DID NOT SEE A PUBLIC MODULE-LEVEL BINDING BECAUSE IT "
            "WAS WRITTEN INSIDE A BLOCK. `public_evaluator = _install_evaluator()` binds a "
            "name every importer can reach; the clause answered UNREACHABLE and the "
            "callable was refused as an undeclared NET instead of named as the "
            "undecorated DOOR it is.\n" + planted.stdout
        )
        assert "_install_evaluator.decide" in planted.stdout, planted.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


#: The same plant, in a module OUTSIDE the RULE 1 judgement-path packages, reached by
#: RULE 2 — the return annotation.
_OFF_PATH_MODULE = '''"""A probe module outside engine/serving/collectors. RULE 1 does not
reach it; RULE 2 does, through the return annotation."""

from crash_detector.dials.reading import Unknown


def _install_evaluator():
    def decide(spec, usable, now_utc) -> "Unknown":
        return Unknown(reason="planted", since_utc=now_utc, missing_inputs=())

    return decide


if True:
    public_evaluator = _install_evaluator()
'''


def test_outside_the_rule_1_packages_the_diagnosis_was_wrong_in_the_same_way():
    """**THE SECOND SITE, IN A MODULE RULE 1 NEVER READS — AND THE HONEST RESULT.**

    **THIS TEST WAS WRITTEN TO BE AN `EXIT 0` -> `EXIT 1` ARM AND MEASUREMENT SAID IT IS
    NOT ONE. THE MEASUREMENT WINS AND THE TEST IS THE THING THAT CHANGED.** The intent was
    a plant with no NETS backstop, on the reasoning that a module outside
    ``engine``/``serving``/``collectors`` is off the judgement path. **IT IS NOT:** RULE 2
    reaches any callable whose return annotation names a judgement value type, wherever it
    lives, and being reached by RULE 2 *is* being on a judgement path for the NETS
    population's purposes. Measured at the base SHA this arm is
    ``UNCLASSIFIED_INTERCEPTOR``, **EXIT 1** — not EXIT 0.

    **AND THE ONLY WAY TO REMOVE THE BACKSTOP IS TO REMOVE THE SUBJECT.** Drop the return
    annotation and neither rule reaches the callable at all, so there is nothing to exit 0
    *about*. I therefore state it plainly rather than leaving it to be found:
    **AT THIS SITE I COULD NOT BUILD AN ARM WHERE `_module_bindings`'s BLINDNESS CONVERTS
    A FAIL INTO A PASS, AND I LOOKED.** What it converts is a RIGHT violation into a WRONG
    one — the check refuses, and refuses for a reason that is false. The NETS
    deny-by-default population is what holds the exit code, exactly as DECLARED LIMIT 9
    says it does, and that is a measured result in the instrument's favour.

    **THE FAIL-INTO-PASS CONVERSION IS REAL AT THE OTHER SITE** — the constructor check —
    and it is measured in the first test in this file. The two sites are not equally
    dangerous and this file does not pretend they are.
    """
    tree = _throwaway_tree()
    try:
        probe = tree / "src" / "crash_detector" / "module_scope_probe.py"
        probe.write_text(_OFF_PATH_MODULE)
        planted = _run(tree, "check_judgement_path_doors.py")
        assert planted.returncode == 1, planted.stdout + planted.stderr
        assert "UNDECORATED_JUDGEMENT_PATH_DOOR" in planted.stdout, (
            "THE CHECK NAMED THE WRONG DEFECT. `public_evaluator = _install_evaluator()` "
            "binds a public module-level name every importer can reach; it is written "
            "inside a block, `_module_bindings` could not read it, and the reachability "
            "clause therefore reported this callable UNREACHABLE and refused it as an "
            "undeclared NET. It is a DOOR. An instrument whose stated reason is false is "
            "an instrument an auditor cannot use, even when its exit code is "
            "right.\n" + planted.stdout
        )
        assert "_install_evaluator.decide" in planted.stdout, planted.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


# ===================================================================================== #
# SITES 3 AND 4 — the NET post-condition resolution and fetch.
#                 A FALSE VIOLATION: the safe direction, and still wrong.
# ===================================================================================== #


def test_a_post_condition_defined_inside_a_module_level_block_still_resolves():
    """The NET register names its post-condition as DATA and the instrument resolves that
    name against the module. Both the resolution and the fetch read ``tree.body``, so a
    post-condition defined inside a module-level block resolved to nothing and the check
    reported ``NET_POST_CONDITION_UNRESOLVABLE`` about a function that is right there and
    is called on every evaluation.

    The error direction is a FALSE VIOLATION rather than a silence, which is the safe one —
    and a shipped declaration wrong in a stated direction is this project's most-found
    defect, so it is corrected rather than tolerated. **CONTRAST: at the base SHA this arm
    was `FAIL — NET_POST_CONDITION_UNRESOLVABLE`, EXIT 1, with the code unchanged in every
    way that matters to the runtime.**
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / _EVALUATE
        source = evaluate_py.read_text()
        marker = "@admits(spec=DialSpec, usable=dict, reading=one_of(*READING_CONSTRUCTORS))\ndef refuse_a_number_without_its_inputs("
        assert marker in source, "the subject of this test moved; fix the test"

        head, _, tail = source.partition(marker)
        body, _, rest = tail.partition("\n\n\ndef _absence_is_never_a_number")
        indented = "\n".join(
            ("    " + line) if line.strip() else line
            for line in (marker + body).splitlines()
        )
        evaluate_py.write_text(
            head + "if True:\n" + indented + "\n\n\ndef _absence_is_never_a_number" + rest
        )

        result = _run(tree, "check_judgement_path_doors.py")
        assert "NET_POST_CONDITION_UNRESOLVABLE" not in result.stdout, (
            "THE POST-CONDITION WAS REPORTED UNRESOLVABLE WHILE BEING DEFINED IN THE FILE "
            "AND CALLED BY THE NET. The NET resolution reads `tree.body`, so indenting a "
            "module-level `def` made it invisible to the instrument and visible to nobody "
            "else.\n" + result.stdout
        )
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        shutil.rmtree(tree, ignore_errors=True)


# ===================================================================================== #
# THE PROPERTY ITSELF, ASSERTED DIRECTLY ON THE HELPER.
# ===================================================================================== #


def test_module_level_statements_prunes_at_scope_and_enumerates_no_block_types():
    """**THE REPAIR MUST NOT BE A VOCABULARY, WHICH IS WHAT MADE IT WORTH DOING.**

    A repair that enumerated ``if``/``try``/``with``/``for``/``while`` would be a list of
    spellings — the exact defect class ``PO-DECISIONS-0012`` ruling 2 removed from the
    membership clause. The helper instead prunes at the three node types that END module
    scope and descends through everything else, so a statement type nobody has written yet
    is handled with no edit.

    Asserted on constructs the fix was NOT written against: ``match``, and a name bound
    inside a nested block. And asserted in the other direction too — a ``def`` inside a
    ``class`` body and a name bound inside a function body must NOT be reported as module
    scope, because widening past the scope rule would be its own defect.
    """
    sys.path.insert(0, str(_REPO_ROOT / "tools" / "register"))
    try:
        import ast

        from _support import module_level_statements
    finally:
        sys.path.pop(0)

    tree = ast.parse(
        "import os\n"
        "if os.name:\n"
        "    SEEN_IN_IF = 1\n"
        "    try:\n"
        "        SEEN_NESTED = 2\n"
        "    except Exception:\n"
        "        SEEN_IN_HANDLER = 3\n"
        "match os.name:\n"
        "    case _:\n"
        "        SEEN_IN_MATCH = 4\n"
        "for _x in ():\n"
        "    def seen_def_in_for():\n"
        "        NOT_SEEN_IN_FUNCTION = 5\n"
        "class Holder:\n"
        "    def not_seen_method(self):\n"
        "        pass\n"
        "    NOT_SEEN_CLASS_ATTR = 6\n"
    )
    bound = set()
    defs = set()
    for node in module_level_statements(tree):
        if isinstance(node, ast.Assign):
            bound.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.add(node.name)

    assert bound == {"SEEN_IN_IF", "SEEN_NESTED", "SEEN_IN_HANDLER", "SEEN_IN_MATCH"}, bound
    assert defs == {"seen_def_in_for", "Holder"}, defs
    assert "NOT_SEEN_IN_FUNCTION" not in bound, (
        "the helper descended INTO a function body. Module scope ends at `def`, and a "
        "reader that walks past it is reporting locals as module-level names."
    )
    assert "NOT_SEEN_CLASS_ATTR" not in bound, "the helper descended INTO a class body"
    assert "not_seen_method" not in defs, "the helper descended INTO a class body"
