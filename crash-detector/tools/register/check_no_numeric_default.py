#!/usr/bin/env python3
"""CD-RT-001-AST-NO-NUMERIC-DEFAULT — no route from absence to a number on the dial path.

    python3 tools/register/check_no_numeric_default.py --root <subject tree>

CRITERION: CD-AC-001, "missing or stale input never renders as calm" (PID §6, BLUEPRINT
§13). PID doctrine §3.2 is constitutional: missing data must never render as calm. The dial
types make the calm rendering of absence *inexpressible*; this check makes sure nobody
quietly re-expresses it.

WHAT IT BANS, AND WHY EACH IS THE SAME DEFECT
----------------------------------------------
Each of the following turns "we do not know" into a number, silently, at a point where a
reader sees arithmetic rather than a decision:

  A  NULLABLE-NUMBER ANNOTATION   ``float | None``, ``Optional[float]``, ``Union[float,
     None]``, ``None | int`` and their string forms. A nullable number is a type whose
     absence case is a value slot, and every consumer of it must remember to branch. The
     dial path uses a sum type instead, where absence has a constructor and no value field.

  B  NUMERIC FALLBACK IN A LOOKUP  ``mapping.get(k, 0)``, ``getattr(o, n, 0.0)``,
     ``d.setdefault(k, 0)``, ``d.pop(k, 0)``, ``next(it, 0)``. The lookup that fails is
     absence; the second argument is the number it becomes.

  C  ``or <number>``              ``value or 0``. Also fires on ``0`` reached through a
     module constant, and on ``x or 0.0`` where ``x`` is legitimately zero — which is the
     second bug in the idiom and the reason it is banned as a class.

  D  NUMERIC DEFAULT OUT OF AN EXCEPT  a handler that returns, yields or assigns a number.
     "It threw, so call it zero" is the same substitution with a traceback thrown away.

  E  CONDITIONAL NUMERIC DEFAULT  ``x if x is not None else 0``, ``0 if x is None else x``,
     and the statement form ``if x is None: x = 0``. This is B and C written longhand, and
     a check that missed it would guard the idiom rather than the proposition.

BUILT FOR THE CLASS, NOT THE INSTANCE. The number may arrive as a literal, as a negated
literal, or through a module-level constant bound to a literal (``_ZERO = 0.0``); all three
are resolved. Annotations are read whether written as syntax or as a string.

WHAT IT DELIBERATELY DOES NOT FLAG, stated so the boundary is visible rather than
discovered: an ordinary numeric parameter default such as ``grace_seconds: float = 15.0``.
That is configuration with a declared value, not absence becoming a value. Where such a
default were ever to stand in for a missing dial input, class B, C, D or E is what carries
it into the computation, and that is where this check bites.

SCANNED SET, IN TWO TIERS, declared below as data and not discovered. If a declared path is
missing the check REFUSES (non-zero, stated reason) rather than scanning less — otherwise
deleting a module would shrink the guard silently.

  DIAL PATH — ``src/crash_detector/dials/`` and ``src/crash_detector/engine/``. This is not
  a choice this check made: both packages declare themselves the dial path in their own
  ``__init__`` docstrings, BLUEPRINT §7 scopes the ``float | None`` ban to it, and
  BLUEPRINT §13 words the criterion as "AST check bans ``float | None``, ``or 0``,
  ``.get(k, 0)`` **in the dial path**". Here ALL FIVE classes are violations.

  ADJACENT PATH — ``src/crash_detector/serving/`` and ``src/crash_detector/observations.py``.
  The serving layer carries CD-AC-001's rendering half ("absent or stale envelope renders
  UNKNOWN at the serving layer"), and ``observations`` carries the outcome sum type that
  keeps the three absences separate. Here classes B, C, D and E are violations — a number
  substituted for a failed lookup is wrong anywhere in this product, and the criterion is
  about the substitution, not about the directory. Class A is REPORTED AS A NOTE with its
  file and line, because the type-level ban on nullable numbers is scoped by the Blueprint
  to the dial path and this check does not get to widen a ratified scope on its own
  initiative. Two such annotations exist today and both are deliberate; see CD-ENG-F26 in
  the Build Log for the reasoning, which is disclosed rather than silently tolerated.

EXIT: 0 clean · 1 violation, each with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import (  # noqa: E402
    EXIT_USAGE,
    Check,
    parse_root,
    python_files,
    read_text,
    resolve_root,
)

CHECK_ID = "CD-RT-001-AST-NO-NUMERIC-DEFAULT"

#: THE DIAL PATH. Declared, not discovered. All five classes are violations here.
DIAL_PATH_DIRS = ("src/crash_detector/dials", "src/crash_detector/engine")
DIAL_PATH_FILES = ()

#: THE ADJACENT PATH. Classes B, C, D and E are violations; class A is a reported note.
ADJACENT_PATH_DIRS = ("src/crash_detector/serving",)
ADJACENT_PATH_FILES = ("src/crash_detector/observations.py",)

#: Names that mean "a number" in an annotation.
NUMERIC_TYPE_NAMES = frozenset(
    {
        "float",
        "int",
        "complex",
        "Decimal",
        "Fraction",
        "Number",
        "Real",
        "Integral",
        "Complex",
        "SupportsFloat",
        "SupportsInt",
        "SupportsIndex",
    }
)

#: Lookup calls whose SECOND positional argument is the value that absence becomes.
FALLBACK_CALLS = {
    "get": 2,
    "getattr": 3,
    "setdefault": 2,
    "pop": 2,
    "next": 2,
    "getint": 2,
    "getfloat": 2,
}


def _is_numeric_constant(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float, complex)) and not isinstance(
            node.value, bool
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return _is_numeric_constant(node.operand)
    return False


class NumericDefaultScanner(ast.NodeVisitor):
    """One module. Reports every route from absence to a number that it can see."""

    def __init__(
        self, check: Check, path: pathlib.Path, tree: ast.AST, *, tier: str
    ) -> None:
        self.check = check
        self.path = path
        #: "DIAL" — every class is a violation. "ADJACENT" — class A is a reported note.
        self.tier = tier
        self.numeric_constants = self._module_numeric_constants(tree)

    # -- module-level constants bound to numbers ------------------------------------- #
    @staticmethod
    def _module_numeric_constants(tree: ast.AST) -> set:
        """``_ZERO = 0.0`` at module level makes ``or _ZERO`` the same defect as ``or 0``."""
        names: set = set()
        for node in getattr(tree, "body", []):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = [node.target]
                value = node.value
            else:
                continue
            if not _is_numeric_constant(value):
                continue
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        return names

    def _is_number(self, node: ast.AST) -> bool:
        if _is_numeric_constant(node):
            return True
        if isinstance(node, ast.Name) and node.id in self.numeric_constants:
            return True
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return self._is_number(node.operand)
        return False

    def report(self, node: ast.AST, rule: str, what: str) -> None:
        self.check.violation(self.path, getattr(node, "lineno", 0), rule, what)

    # -- A: nullable-number annotations ------------------------------------------------ #
    def _annotation_names(self, node: ast.AST, depth: int = 0) -> tuple[set, bool]:
        """(numeric type names mentioned, whether None is one of the members)."""
        numeric: set = set()
        has_none = False
        if node is None or depth > 12:
            return numeric, has_none
        if isinstance(node, ast.Constant):
            if node.value is None:
                return numeric, True
            if isinstance(node.value, str):
                try:
                    inner = ast.parse(node.value, mode="eval").body
                except SyntaxError:
                    return numeric, has_none
                return self._annotation_names(inner, depth + 1)
            return numeric, has_none
        if isinstance(node, ast.Name):
            if node.id in NUMERIC_TYPE_NAMES:
                numeric.add(node.id)
            if node.id == "None":
                has_none = True
            return numeric, has_none
        if isinstance(node, ast.Attribute):
            if node.attr in NUMERIC_TYPE_NAMES:
                numeric.add(node.attr)
            return numeric, has_none
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            for side in (node.left, node.right):
                sub_numeric, sub_none = self._annotation_names(side, depth + 1)
                numeric |= sub_numeric
                has_none = has_none or sub_none
            return numeric, has_none
        if isinstance(node, ast.Subscript):
            base = node.value
            base_name = (
                base.id
                if isinstance(base, ast.Name)
                else base.attr if isinstance(base, ast.Attribute) else ""
            )
            slice_node = node.slice
            members = (
                list(slice_node.elts)
                if isinstance(slice_node, ast.Tuple)
                else [slice_node]
            )
            if base_name == "Optional":
                has_none = True
            for member in members:
                sub_numeric, sub_none = self._annotation_names(member, depth + 1)
                numeric |= sub_numeric
                has_none = has_none or sub_none
            return numeric, has_none
        return numeric, has_none

    def check_annotation(self, node: ast.AST, annotation: ast.AST, where: str) -> None:
        if annotation is None:
            return
        self.check.asserted()
        numeric, has_none = self._annotation_names(annotation)
        if not (numeric and has_none):
            return
        detail = (
            f"{where} is annotated as a number that may be None "
            f"({', '.join(sorted(numeric))} | None). Absence has a constructor here "
            "(Unknown), not a null value slot: a nullable number obliges every consumer "
            "to remember, and one that forgets renders absence as a number."
        )
        if self.tier == "DIAL":
            self.report(annotation, "A: nullable-number annotation", detail)
            return
        line = getattr(annotation, "lineno", 0)
        relative = self.path
        try:
            relative = self.path.relative_to(self.check.root)
        except ValueError:
            pass
        self.check.note(
            f"class A on the ADJACENT path at {relative}:{line} — {detail} REPORTED, NOT "
            "FAILED: BLUEPRINT §7 and §13 scope the nullable-number ban to the dial path, "
            "and this check does not widen a ratified scope on its own initiative. It is "
            "printed on every run so it is disclosed rather than tolerated in silence."
        )

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target = (
            node.target.id
            if isinstance(node.target, ast.Name)
            else ast.unparse(node.target)
        )
        self.check_annotation(node, node.annotation, f"`{target}`")
        self.generic_visit(node)

    def _visit_function(self, node) -> None:
        args = node.args
        every = (
            list(args.posonlyargs)
            + list(args.args)
            + list(args.kwonlyargs)
            + ([args.vararg] if args.vararg else [])
            + ([args.kwarg] if args.kwarg else [])
        )
        for argument in every:
            self.check_annotation(
                node, argument.annotation, f"parameter `{argument.arg}` of `{node.name}`"
            )
        self.check_annotation(node, node.returns, f"the return of `{node.name}`")
        self.generic_visit(node)

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function

    # -- B: numeric fallback in a lookup ----------------------------------------------- #
    def visit_Call(self, node: ast.Call) -> None:
        name = (
            node.func.attr
            if isinstance(node.func, ast.Attribute)
            else node.func.id if isinstance(node.func, ast.Name) else ""
        )
        arity = FALLBACK_CALLS.get(name)
        if arity is not None:
            self.check.asserted()
            if len(node.args) >= arity and self._is_number(node.args[arity - 1]):
                self.report(
                    node,
                    "B: numeric fallback in a lookup",
                    f"`{ast.unparse(node)[:120]}` supplies a NUMBER as the value a failed "
                    "lookup becomes. The lookup failing is absence; this makes absence a "
                    "number. Return the absence and let the caller name it.",
                )
        for keyword in node.keywords:
            if keyword.arg in {"default", "fallback"} and self._is_number(keyword.value):
                self.check.asserted()
                self.report(
                    node,
                    "B: numeric fallback in a lookup",
                    f"`{ast.unparse(node)[:120]}` passes a NUMBER as `{keyword.arg}=`. "
                    "Same substitution, spelled as a keyword.",
                )
        self.generic_visit(node)

    # -- C: `or <number>` --------------------------------------------------------------- #
    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        if isinstance(node.op, ast.Or):
            self.check.asserted()
            for operand in node.values[1:]:
                if self._is_number(operand):
                    self.report(
                        node,
                        "C: `or <number>`",
                        f"`{ast.unparse(node)[:120]}` substitutes a number when the left "
                        "side is falsey. Two defects in one idiom: absence becomes a "
                        "number, and a legitimate 0, 0.0 or empty value is replaced by "
                        "the default as well.",
                    )
        self.generic_visit(node)

    # -- D: a numeric default out of an except ------------------------------------------ #
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.check.asserted()
        for inner in ast.walk(node):
            produced = None
            if isinstance(inner, ast.Return) and inner.value is not None:
                produced = inner.value
            elif isinstance(inner, (ast.Assign, ast.AnnAssign)) and inner.value is not None:
                produced = inner.value
            elif isinstance(inner, ast.Expr) and isinstance(inner.value, ast.Yield):
                produced = inner.value.value
            if produced is not None and self._contains_number(produced):
                kind = (
                    "a bare `except:`"
                    if node.type is None
                    else f"`except {ast.unparse(node.type)}`"
                )
                self.report(
                    inner,
                    "D: numeric default out of an except handler",
                    f"{kind} produces the number `{ast.unparse(produced)[:80]}`. "
                    "'It threw, so call it zero' is absence rendering as calm with the "
                    "traceback thrown away. Let the exception travel, or return a named "
                    "absence.",
                )
        self.generic_visit(node)

    def _contains_number(self, node: ast.AST) -> bool:
        if self._is_number(node):
            return True
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return any(self._is_number(element) for element in node.elts)
        if isinstance(node, ast.Dict):
            return any(
                value is not None and self._is_number(value) for value in node.values
            )
        if isinstance(node, ast.Call):
            return any(self._is_number(argument) for argument in node.args)
        return False

    # -- E: conditional numeric default -------------------------------------------------- #
    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.check.asserted()
        if self._tests_for_absence(node.test):
            for branch, label in ((node.body, "then"), (node.orelse, "else")):
                if self._is_number(branch):
                    self.report(
                        node,
                        "E: conditional numeric default",
                        f"`{ast.unparse(node)[:120]}` yields a number on the {label} "
                        "branch of an absence test. This is `or 0` and `.get(k, 0)` "
                        "written longhand, and it is the same substitution.",
                    )
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.check.asserted()
        if self._tests_for_absence(node.test):
            for statement in node.body:
                if isinstance(statement, (ast.Assign, ast.AnnAssign)) and (
                    statement.value is not None and self._is_number(statement.value)
                ):
                    self.report(
                        statement,
                        "E: conditional numeric default",
                        f"`{ast.unparse(statement)[:120]}` assigns a number inside a "
                        "branch taken because something was absent. The statement form of "
                        "the same substitution.",
                    )
                if isinstance(statement, ast.Return) and statement.value is not None:
                    if self._is_number(statement.value):
                        self.report(
                            statement,
                            "E: conditional numeric default",
                            f"`{ast.unparse(statement)[:120]}` returns a number from a "
                            "branch taken because something was absent.",
                        )
        self.generic_visit(node)

    @staticmethod
    def _tests_for_absence(test: ast.AST) -> bool:
        """True for ``x is None``, ``x is not None``, ``not x``, ``x`` and their ands/ors."""
        if isinstance(test, ast.Compare):
            return any(
                isinstance(op, (ast.Is, ast.IsNot))
                and isinstance(comparator, ast.Constant)
                and comparator.value is None
                for op, comparator in zip(test.ops, test.comparators)
            )
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            return True
        if isinstance(test, ast.BoolOp):
            return any(
                NumericDefaultScanner._tests_for_absence(value) for value in test.values
            )
        return False


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    missing = [
        relative
        for relative in DIAL_PATH_DIRS + ADJACENT_PATH_DIRS
        if not (root / relative).is_dir()
    ] + [
        relative
        for relative in DIAL_PATH_FILES + ADJACENT_PATH_FILES
        if not (root / relative).is_file()
    ]
    if missing:
        return check.refuse(
            "the declared scanned set is incomplete in this subject tree — missing: "
            + ", ".join(missing)
            + ". The scanned set is declared, not discovered, so a deleted module shrinks "
            "the guard visibly instead of silently."
        )

    dial_files = python_files(root, DIAL_PATH_DIRS, DIAL_PATH_FILES)
    adjacent_files = python_files(root, ADJACENT_PATH_DIRS, ADJACENT_PATH_FILES)
    if not dial_files:
        return check.refuse(
            "the declared dial path contains no Python files. Nothing was scanned."
        )

    for tier, files in (("DIAL", dial_files), ("ADJACENT", adjacent_files)):
        for path in files:
            source = read_text(check, path)
            if source is None:
                continue
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError as exc:
                check.violation(
                    path,
                    exc.lineno or 0,
                    "UNPARSEABLE",
                    f"this file in the {tier} scanned set could not be parsed "
                    f"({exc.msg}). A file the check cannot read is a file the check "
                    "cannot guard, which is a failure and never a pass.",
                )
                continue
            NumericDefaultScanner(check, path, tree, tier=tier).visit(tree)

    return check.done(
        f"{len(dial_files)} Python files on the declared dial path "
        f"({', '.join(DIAL_PATH_DIRS)}) and {len(adjacent_files)} on the adjacent path "
        f"({', '.join(ADJACENT_PATH_DIRS + ADJACENT_PATH_FILES)})"
    )


if __name__ == "__main__":
    raise SystemExit(main())
