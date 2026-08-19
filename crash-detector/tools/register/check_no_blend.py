#!/usr/bin/env python3
"""CD-RT-002-AST-NO-BLEND — the two dials are never combined into one number.

    python3 tools/register/check_no_blend.py --root <subject tree>

CRITERION: CD-AC-002. PID §3.1 is CONSTITUTIONAL: "Two dials, never blended. Equity crash
and monetary/debasement fail in opposite directions; averaging cancels the signal."

This is the second of CD-AC-002's three independent refusals. The first is the type system
— neither score type defines an arithmetic dunder, so ``equity + monetary`` is a TypeError.
The third is the closed public envelope schema. None is load-bearing alone (BLUEPRINT §13,
§17 risk CD-BP-001), and this one exists precisely to catch the blend that reaches for the
``.score`` floats and so never asks the type system anything.

TWO RULES, DELIBERATELY DIFFERENT IN REACH
-------------------------------------------
  RULE 1  ARITHMETIC.  No expression anywhere in the application source may combine an
          equity-flavoured value and a monetary-flavoured value under an arithmetic or
          bitwise operator, a comparison, an augmented assignment, or a numeric aggregate
          (``sum``, ``min``, ``max``, ``mean``, ``statistics.*`` …). **There is no
          allowlist for this rule, not even the container and the serving layer.** Holding
          the two dials side by side never requires arithmetic between them.

  RULE 2  CO-OCCURRENCE.  No single expression may consume both dial types at all —
          outside the allowlisted container and serving layer, which are the two places
          BLUEPRINT §13 says composition legitimately happens. The container constructs a
          ``DialSet`` from both; the serving layer renders both side by side; the engine's
          ``evaluate`` builds the container. Everywhere else, an expression that has hold
          of both is one edit away from a headline number.

BUILT FOR THE CLASS, NOT THE INSTANCE
--------------------------------------
The obvious plant is ``combined = (dials.equity.score + dials.monetary.score) / 2`` — one
expression, both markers, caught by inspecting that expression alone. The obvious ESCAPE is
to spell it over three statements:

    e = dials.equity.value.score
    m = dials.monetary.value.score
    combined = (e + m) / 2

By the time the addition happens, no dial marker is in the expression. A check that only
looked at single expressions would report the tree clean while the blend sat in it. So this
check carries a small intra-procedural FLAVOUR PROPAGATION: within each function (and at
module level) a local name assigned from an equity-flavoured expression becomes
equity-flavoured itself, through plain assignment, annotated assignment, augmented
assignment, tuple unpacking, walrus, ``for`` targets, ``with ... as`` and comprehension
targets. Parameters annotated with a score type are flavoured from their annotation. The
rules are then applied to the propagated flavours, so the three-statement spelling is
caught in the same breath as the one-liner.

FLAVOUR MARKERS: the score type names; the ``.equity`` / ``.monetary`` dial slots; the
``EQUITY_DIAL_ID`` / ``MONETARY_DIAL_ID`` constants; the dial-id string literals
``'equity_crash'`` / ``'monetary_debasement'``; and identifiers whose tokens name a dial.

SCANNED SET: the application source — ``src/crash_detector/`` and
``deploy/entrypoints/``. ``tests/`` is deliberately NOT scanned: the tests for CD-AC-002
must write ``operator.add(equity, monetary)`` in order to assert that it raises, and a
check that failed the test proving the property would be nonsense. ``import`` statements
are not expressions and are not markers — importing both types is how a module gets them.

EXIT: 0 clean · 1 violation, each with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, python_files, read_text, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-002-AST-NO-BLEND"

SCAN_DIRS = ("src/crash_detector", "deploy/entrypoints")

#: Where consuming both dials in one expression is legitimate (RULE 2 only — RULE 1 has no
#: allowlist). Each is named with the reason it is here, so widening the list is a
#: deliberate act with a stated justification rather than a quiet append.
CO_OCCURRENCE_ALLOWLIST = {
    "src/crash_detector/dials/dialset.py": (
        "THE CONTAINER. DialSet holds the two readings side by side and exposes no scalar; "
        "constructing it necessarily names both slots (BLUEPRINT §7, §13)."
    ),
    "src/crash_detector/dials/scores.py": (
        "THE MODULE THAT DEFINES BOTH TYPES. `SCORE_TYPES = (EquityCrashScore, "
        "MonetaryDebasementScore)` enumerates them as data so the guards that assert their "
        "unrelatedness can iterate, which is the opposite of blending them. RULE 1 applies "
        "here in full and without allowlist, and the type-level refusal "
        "(CD-RT-002-TYPE-NO-ARITHMETIC) is a second independent instrument over this file."
    ),
    "src/crash_detector/dials/__init__.py": (
        "the package's re-export surface: __all__ and the import block name both types."
    ),
    "src/crash_detector/engine/evaluate.py": (
        "evaluate() BUILDS the container: `DialSet(equity=..., monetary=...)` is one "
        "expression naming both, and the dial/score type map is one dict naming both. "
        "RULE 1 still applies here in full, which is what actually guards this module."
    ),
    "src/crash_detector/engine/__init__.py": (
        "the package's re-export surface."
    ),
    "src/crash_detector/serving": (
        "THE SERVING LAYER. BLUEPRINT §13: 'composition happens only at the serving "
        "layer'. It renders both dials side by side; RULE 1 still forbids arithmetic "
        "between them here."
    ),
}

EQUITY = "EQUITY"
MONETARY = "MONETARY"

EQUITY_NAMES = frozenset({"EquityCrashScore", "EQUITY_DIAL_ID", "equity"})
MONETARY_NAMES = frozenset({"MonetaryDebasementScore", "MONETARY_DIAL_ID", "monetary"})
EQUITY_STRINGS = frozenset({"equity_crash"})
MONETARY_STRINGS = frozenset({"monetary_debasement"})
EQUITY_TOKENS = frozenset({"equity"})
MONETARY_TOKENS = frozenset({"monetary", "debasement"})

#: Calls that reduce several numbers to one. A blend does not need an operator.
AGGREGATE_CALLS = frozenset(
    {
        "sum", "min", "max", "abs", "round", "pow", "divmod",
        "mean", "fmean", "median", "average", "geometric_mean", "harmonic_mean",
        "stdev", "pstdev", "variance", "pvariance", "quantiles",
        "hypot", "prod", "fsum", "dist", "norm", "sqrt", "log",
        "blend", "combine", "combined", "overall", "aggregate", "composite",
    }
)


def _tokens(identifier: str) -> set:
    """Split ``equityScore``/``equity_score``/``EQUITY_DIAL_ID`` into lowercase tokens."""
    out: list[str] = []
    current: list[str] = []
    for char in identifier:
        if char == "_":
            if current:
                out.append("".join(current))
                current = []
            continue
        if char.isupper() and current and not current[-1].isupper():
            out.append("".join(current))
            current = [char]
            continue
        current.append(char)
    if current:
        out.append("".join(current))
    return {token.lower() for token in out if token}


class Flavours:
    """The set of dial flavours an expression is built from, with taint propagation."""

    def __init__(self) -> None:
        self.env: dict[str, set] = {}

    # -- reading an expression --------------------------------------------------------- #
    def of(self, node) -> set:
        found: set = set()
        if node is None:
            return found
        for inner in ast.walk(node):
            if isinstance(inner, ast.Name):
                found |= self._of_identifier(inner.id)
            elif isinstance(inner, ast.Attribute):
                found |= self._of_identifier(inner.attr)
            elif isinstance(inner, ast.arg):
                found |= self._of_identifier(inner.arg)
            elif isinstance(inner, ast.keyword) and inner.arg:
                found |= self._of_identifier(inner.arg)
            elif isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                if inner.value in EQUITY_STRINGS:
                    found.add(EQUITY)
                if inner.value in MONETARY_STRINGS:
                    found.add(MONETARY)
        return found

    def _of_identifier(self, identifier: str) -> set:
        found: set = set(self.env.get(identifier, ()))
        if identifier in EQUITY_NAMES:
            found.add(EQUITY)
        if identifier in MONETARY_NAMES:
            found.add(MONETARY)
        tokens = _tokens(identifier)
        if tokens & EQUITY_TOKENS:
            found.add(EQUITY)
        if tokens & MONETARY_TOKENS:
            found.add(MONETARY)
        return found

    # -- propagation -------------------------------------------------------------------- #
    def bind(self, target, flavours: set) -> None:
        if not flavours:
            return
        for inner in ast.walk(target):
            if isinstance(inner, ast.Name):
                self.env.setdefault(inner.id, set()).update(flavours)

    def child(self) -> "Flavours":
        """A nested scope that inherits what the enclosing scope has established."""
        nested = Flavours()
        nested.env = {name: set(value) for name, value in self.env.items()}
        return nested


class BlendScanner:
    def __init__(self, check: Check, path: pathlib.Path, allow_co_occurrence: bool) -> None:
        self.check = check
        self.path = path
        self.allow_co_occurrence = allow_co_occurrence

    def report(self, node, rule: str, what: str) -> None:
        self.check.violation(self.path, getattr(node, "lineno", 0), rule, what)

    # -- driving ------------------------------------------------------------------------ #
    def scan_module(self, tree: ast.Module) -> None:
        self.scan_body(tree.body, Flavours())

    def scan_body(self, body, flavours: Flavours) -> None:
        for statement in body:
            self.scan_statement(statement, flavours)

    def scan_statement(self, node, flavours: Flavours) -> None:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Importing both types is how a module obtains them. Not an expression.
            return

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nested = flavours.child()
            arguments = node.args
            every = (
                list(arguments.posonlyargs)
                + list(arguments.args)
                + list(arguments.kwonlyargs)
                + ([arguments.vararg] if arguments.vararg else [])
                + ([arguments.kwarg] if arguments.kwarg else [])
            )
            for argument in every:
                marks = nested.of(argument.annotation) | nested._of_identifier(argument.arg)
                if marks:
                    nested.env.setdefault(argument.arg, set()).update(marks)
            for decorator in node.decorator_list:
                self.scan_expression(decorator, nested)
            for default in list(arguments.defaults) + [
                d for d in arguments.kw_defaults if d is not None
            ]:
                self.scan_expression(default, nested)
            self.scan_body(node.body, nested)
            return

        if isinstance(node, ast.ClassDef):
            nested = flavours.child()
            for decorator in node.decorator_list:
                self.scan_expression(decorator, nested)
            self.scan_body(node.body, nested)
            return

        if isinstance(node, ast.Assign):
            # `__all__ = [...]` is a re-export surface, not a computation.
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                return
            self.scan_expression(node.value, flavours)
            marks = flavours.of(node.value)
            for target in node.targets:
                if isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
                    for slot, value in zip(target.elts, node.value.elts):
                        flavours.bind(slot, flavours.of(value))
                else:
                    flavours.bind(target, marks)
            return

        if isinstance(node, ast.AnnAssign):
            if node.value is not None:
                self.scan_expression(node.value, flavours)
            marks = flavours.of(node.value) | flavours.of(node.annotation)
            flavours.bind(node.target, marks)
            return

        if isinstance(node, ast.AugAssign):
            left = flavours.of(node.target)
            right = flavours.of(node.value)
            self._judge_combination(node, left, right, f"`{ast.unparse(node)[:120]}`")
            self.scan_expression(node.value, flavours)
            flavours.bind(node.target, left | right)
            return

        if isinstance(node, (ast.For, ast.AsyncFor)):
            self.scan_expression(node.iter, flavours)
            flavours.bind(node.target, flavours.of(node.iter))
            self.scan_body(node.body, flavours)
            self.scan_body(node.orelse, flavours)
            return

        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                self.scan_expression(item.context_expr, flavours)
                if item.optional_vars is not None:
                    flavours.bind(item.optional_vars, flavours.of(item.context_expr))
            self.scan_body(node.body, flavours)
            return

        for field_name, value in ast.iter_fields(node):
            if isinstance(value, list):
                statements = [item for item in value if isinstance(item, ast.stmt)]
                expressions = [item for item in value if isinstance(item, ast.expr)]
                self.scan_body(statements, flavours)
                for expression in expressions:
                    self.scan_expression(expression, flavours)
            elif isinstance(value, ast.stmt):
                self.scan_statement(value, flavours)
            elif isinstance(value, ast.expr):
                self.scan_expression(value, flavours)
            elif isinstance(value, list) is False and isinstance(value, ast.AST):
                for sub in ast.iter_child_nodes(value):
                    if isinstance(sub, ast.stmt):
                        self.scan_statement(sub, flavours)
                    elif isinstance(sub, ast.expr):
                        self.scan_expression(sub, flavours)

    # -- expressions --------------------------------------------------------------------- #
    def scan_expression(self, node, flavours: Flavours) -> None:
        if node is None:
            return
        for inner in ast.walk(node):
            if isinstance(inner, ast.NamedExpr):
                flavours.bind(inner.target, flavours.of(inner.value))
            if isinstance(inner, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                for generator in inner.generators:
                    flavours.bind(generator.target, flavours.of(generator.iter))

        self.check.asserted()

        for inner in ast.walk(node):
            if isinstance(inner, ast.BinOp):
                self._judge_combination(
                    inner,
                    flavours.of(inner.left),
                    flavours.of(inner.right),
                    f"`{ast.unparse(inner)[:120]}`",
                )
            elif isinstance(inner, ast.Compare):
                left = flavours.of(inner.left)
                for comparator in inner.comparators:
                    self._judge_combination(
                        inner,
                        left,
                        flavours.of(comparator),
                        f"`{ast.unparse(inner)[:120]}`",
                    )
            elif isinstance(inner, ast.BoolOp):
                seen: set = set()
                for value in inner.values:
                    marks = flavours.of(value)
                    self._judge_combination(
                        inner, seen, marks, f"`{ast.unparse(inner)[:120]}`"
                    )
                    seen |= marks
            elif isinstance(inner, ast.Call):
                name = (
                    inner.func.attr
                    if isinstance(inner.func, ast.Attribute)
                    else inner.func.id if isinstance(inner.func, ast.Name) else ""
                )
                is_aggregate = name in AGGREGATE_CALLS or bool(
                    _tokens(name) & {"blend", "combine", "combined", "aggregate", "mean", "average"}
                )
                if is_aggregate:
                    marks: set = set()
                    for argument in list(inner.args) + [k.value for k in inner.keywords]:
                        marks |= flavours.of(argument)
                    if EQUITY in marks and MONETARY in marks:
                        self.report(
                            inner,
                            "RULE 1: arithmetic across the two dials",
                            f"`{ast.unparse(inner)[:120]}` passes BOTH dials to the "
                            f"numeric aggregate `{name}`. A blend does not need an "
                            "operator: reducing the two dials to one number is the thing "
                            "PID §3.1 forbids, however it is spelled.",
                        )

        if not self.allow_co_occurrence:
            marks = flavours.of(node)
            if EQUITY in marks and MONETARY in marks:
                self.report(
                    node,
                    "RULE 2: one expression consumes both dials",
                    f"`{ast.unparse(node)[:120]}` consumes BOTH dial types in a single "
                    "expression, outside the container and the serving layer. BLUEPRINT "
                    "§13: composition happens only at the serving layer. An expression "
                    "holding both is one edit away from a headline number.",
                )

    def _judge_combination(self, node, left: set, right: set, rendered: str) -> None:
        if (EQUITY in left and MONETARY in right) or (
            MONETARY in left and EQUITY in right
        ):
            self.report(
                node,
                "RULE 1: arithmetic across the two dials",
                f"{rendered} combines an equity-flavoured value with a "
                "monetary-flavoured value. PID §3.1 is constitutional: the two dials fail "
                "in opposite directions and averaging cancels the signal. There is no "
                "allowlist for this rule, in any module.",
            )


def _allow_co_occurrence(root: pathlib.Path, path: pathlib.Path) -> bool:
    relative = path.relative_to(root).as_posix()
    for allowed in CO_OCCURRENCE_ALLOWLIST:
        if relative == allowed or relative.startswith(allowed.rstrip("/") + "/"):
            return True
    return False


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    if not (root / "src/crash_detector").is_dir():
        return check.refuse(
            "src/crash_detector/ does not exist in this subject tree, so there is no "
            "application source to scan."
        )

    files = python_files(root, SCAN_DIRS)
    if not files:
        return check.refuse("no Python files found in the application source.")

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
                f"this application module could not be parsed ({exc.msg}). A file the "
                "check cannot read is a file the check cannot guard, which is a failure "
                "and never a pass.",
            )
            continue
        BlendScanner(check, path, _allow_co_occurrence(root, path)).scan_module(tree)

    return check.done(
        f"{len(files)} application Python files under {', '.join(SCAN_DIRS)}; "
        f"{len(CO_OCCURRENCE_ALLOWLIST)} paths allowlisted for RULE 2 only"
    )


if __name__ == "__main__":
    raise SystemExit(main())
