#!/usr/bin/env python3
"""CD-RT-002-AST-NO-BLEND — the two dials are never combined into one number.

    python3 tools/register/check_no_blend.py --root <subject tree>

CRITERION: CD-AC-002. PID §3.1 is CONSTITUTIONAL: "Two dials, never blended. Equity crash
and monetary/debasement fail in opposite directions; averaging cancels the signal."

WHAT THIS CHECK IS, AFTER CD-ASR-F01 (HIGH)
--------------------------------------------
**THIS CHECK IS A LOCATOR. IT IS NOT THE CLOSURE, AND IT CANNOT BE.** Read the DECLARED
LIMIT at the bottom of this header before reading a clean run as evidence of anything.

It used to be described as one of three independent refusals, and the register said "a
blend that slips past any one layer must still fail the other two". An independent auditor
REFUTED that claim BY EXECUTION: two working blends passed all three layers simultaneously
and each returned 0.5 from equity 0.9 and monetary 0.1 (`CD-ASR-F01`, escaped variants
`E01` and `E02`). Both walked past THIS check, for a reason that is structural and
permanent — flavour propagation here is INTRA-PROCEDURAL and purely STATIC, so moving the
arithmetic one call away, or reaching the attribute through ``getattr`` with a non-marker
string literal, erases the flavour entirely.

The class is now closed where it can be closed:

* AT THE TYPE — ``crash_detector.dials.magnitude.DialMagnitude``. A dial magnitude is a
  nominal, per-dial, NON-COERCIBLE value carrying its provenance as data. It defines no
  arithmetic dunder and no numeric coercion, so ``left + right``, ``sum([...])``,
  ``functools.reduce``, ``statistics.mean`` and every other reduction raise ``TypeError``
  from the interpreter regardless of how the two values were reached. Both `E01` and `E02`
  now raise when EXECUTED.
* AT THE POINT OF COMBINATION — ``combine_within_one_dial`` compares the provenance the
  magnitudes CARRY and refuses anything but a single dial, so the refusal does not depend
  on anybody having read the code.
* AT THE PUBLICATION BOUNDARY — ``crash_detector.publication.dial_scalar`` releases a
  number into a dial slot only from a magnitude whose provenance is exactly that slot's
  dial, and the closed public envelope schema has no third key for a combined figure.

What THIS check still earns its keep for: it LOCATES a blend in the source, with a file and
a line, in the one place a reviewer can act on it cheaply; and it catches the three-line
spelling that no runtime layer would see until the branch executed. It is a locator with a
declared limit, and the register entry now says exactly that and no more.

THREE RULES, DELIBERATELY DIFFERENT IN REACH
---------------------------------------------
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

  RULE 3  REACHING PAST THE DECLARED RELEASE.  No expression anywhere in the application
          source may name the private slot in which a ``DialMagnitude`` holds its number
          (``_DialMagnitude__quantity``), by attribute or as a string handed to
          ``getattr``. **There is no allowlist for this rule either**, save the one module
          that DEFINES the slot. The declared way to obtain the number is
          ``magnitude.quantity_for(<dial id>)``, which names one dial and refuses a
          mismatch; reaching around it is a deliberate act to obtain a number without
          saying which dial it belongs to, which is the first half of a blend. This rule
          is not aimed at a variant somebody wrote. It exists because the closure created
          exactly one private name, and a guard over exactly one name is the narrowest
          kind of guard there is.

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

DECLARED LIMIT — WHAT THIS CHECK DOES NOT CATCH, AND WHICH LAYER DOES
---------------------------------------------------------------------
Required by CD-RULE-004 and by the WO-2R dispatch, drawn in the pattern of
CD-RT-012-NO-EXECUTION-INTERFACE, whose declaration an independent auditor examined and
judged HONESTLY DRAWN AND DRAWN CONSERVATIVELY. That same auditor's caveat is why this
block exists: "CD-AC-002's AST guard has comparable limitations (intra-procedural, static)
and NO comparable written declaration, which is why CD-ASR-F01 is reported at HIGH."

It is written as fact, not as apology, and every boundary carries an example an auditor can
execute. **DO NOT READ A CLEAN RUN OF THIS CHECK AS PROOF THAT NO CODE PATH COMBINES THE
TWO DIALS.** It was clean for both blends that produced CD-ASR-F01. The register entry for
CD-RT-002-AST-NO-BLEND and this check's execution contract carry the same list.

THIS CHECK IS A STATIC READ OF SOURCE TEXT AT ONE COMMIT, AND ITS FLAVOUR PROPAGATION IS
INTRA-PROCEDURAL. Both limitations are permanent. They are not defects to be repaired in a
later work order; they are what a static intra-procedural checker IS.

  1  INTER-PROCEDURAL FLOW. A value carried into a function is not followed. Flavour is
     established per scope, from annotations and from assignments within that scope; a
     parameter annotated ``float`` carries no dial flavour whatever the caller passed.
     MEASURED EXAMPLE, which exits 0 here — this is `E01` verbatim:
         def _fold(left: float, right: float) -> float:
             return (left + right) / 2.0
         def banner_figure(dials):
             return _fold(dials.equity.value.score, dials.monetary.value.score)
     The call expression holds both dial markers but contains no arithmetic, so RULE 1
     does not fire; the arithmetic is one call away where there is no flavour to see.
     THE TYPE LAYER CARRIES THIS: executed, ``_fold`` raises
     ``TypeError: unsupported operand type(s) for +: 'DialMagnitude' and 'DialMagnitude'``.

  2  DYNAMIC ATTRIBUTE ACCESS ERASES FLAVOUR ENTIRELY. A dial reached through ``getattr``
     with a plain string is not a dial as far as this check is concerned. MEASURED
     EXAMPLE, which exits 0 here — this is `E02` verbatim:
         _SLOTS = ("equity", "monetary")
         magnitudes = [getattr(dials, slot).value.score for slot in _SLOTS]
         return sum(magnitudes) / len(magnitudes)
     No dial marker appears in any expression, so nothing is ever flavoured and no rule
     fires. This is the STRONGER of the two escapes because it needs no allowlisted path.
     THE TYPE LAYER CARRIES THIS: executed, ``sum`` raises
     ``TypeError: unsupported operand type(s) for +: 'int' and 'DialMagnitude'``.

  3  THE RULE 2 ALLOWLIST IS A REAL HOLE IN RULE 2, BY DESIGN. Six paths may consume both
     dials in one expression, and `E01` was planted in one of them
     (``src/crash_detector/serving``). RULE 1 has no allowlist and applies there in full,
     but RULE 1 only sees arithmetic it can attribute to both dials in one scope.
     MEASURED EXAMPLE: any inter-procedural fold placed under ``src/crash_detector/
     serving/`` is invisible to both rules. THE TYPE LAYER CARRIES THIS.

  4  THE SCANNED SET. Only ``src/crash_detector/`` and ``deploy/entrypoints/`` are read.
     ``tests/`` is deliberately excluded — the tests for CD-AC-002 must write
     ``operator.add(equity, monetary)`` in order to assert that it raises. MEASURED
     EXAMPLE: a blend placed in ``tests/`` or in ``db/`` exits 0 here. It also cannot
     reach a shipped image: all six application Dockerfiles COPY exactly ``src/`` and
     ``deploy/entrypoints/``.

  5  IT READS SOURCE, NOT BEHAVIOUR. A blend assembled at runtime — from a configuration
     value, from a plugin, from ``eval``, or from a module written at import time — is
     outside a static check entirely. MEASURED EXAMPLE: ``exec(open(cfg).read())`` is one
     expression naming no dial. THE TYPE LAYER CARRIES THIS, because the refusal is a
     property of the objects rather than of the text.

  6  A NUMBER ALREADY RELEASED IS AN ORDINARY FLOAT. ``quantity_for(<dial id>)`` yields a
     bare ``float`` to a caller that names its one dial, and two such floats can be added
     by ordinary Python. MEASURED EXAMPLE, which RULE 1 DOES catch when spelled with the
     dial ids and does NOT catch when the ids are reached dynamically:
         e = dials.equity.value.score.quantity_for(EQUITY_DIAL_ID)
         m = dials.monetary.value.score.quantity_for(MONETARY_DIAL_ID)
         blended = (e + m) / 2.0
     THE PUBLICATION BOUNDARY CARRIES THIS: ``number_for_dial_slot`` accepts only a
     ``DialMagnitude`` whose provenance is exactly the slot's dial, so ``blended`` cannot
     be offered for publication; and the closed envelope schema has no third key for it.
     This is the residue that is DECLARED rather than closed, and it is declared in
     ``src/crash_detector/dials/magnitude.py`` (boundary A), in the register entry, and in
     the execution contract, in the same words.

FOR THE AUDITOR. A CD-AC-002 variant that lands beyond a boundary above is a finding
against THIS DECLARATION — was the limit honestly drawn? — and not an automatic RED
against the guard. A variant that reaches the violation through a route a boundary above
says is COVERED by the type layer or the publication boundary, and is nevertheless not
refused when EXECUTED, is a defect in the closure and should be reported as one.

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

#: The private slot in which a ``DialMagnitude`` holds its number, in both the spelling a
#: reader would type and the mangled spelling CPython actually installs. RULE 3 refuses
#: either, as an attribute and as a string constant (so ``getattr(m, "_DialMagnitude__
#: quantity")`` is refused with the attribute form). Declared as data because the closure
#: created exactly ONE private name and this rule guards exactly that name.
SEALED_MAGNITUDE_SLOTS = frozenset({"_DialMagnitude__quantity", "__quantity"})

#: The one module RULE 3 does not apply to: the module that DECLARES the slot, and which
#: must therefore name it in order to read it out inside ``quantity_for``. This is not an
#: allowlist in the RULE 2 sense — it is the definition site, and a rule that fired on the
#: definition would forbid the structure it exists to protect.
MAGNITUDE_MODULE = "src/crash_detector/dials/magnitude.py"

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
    def __init__(
        self,
        check: Check,
        path: pathlib.Path,
        allow_co_occurrence: bool,
        declares_the_slot: bool = False,
    ) -> None:
        self.check = check
        self.path = path
        self.allow_co_occurrence = allow_co_occurrence
        self.declares_the_slot = declares_the_slot

    def report(self, node, rule: str, what: str) -> None:
        self.check.violation(self.path, getattr(node, "lineno", 0), rule, what)

    # -- driving ------------------------------------------------------------------------ #
    def scan_module(self, tree: ast.Module) -> None:
        self.scan_sealed_slot_reach(tree)
        self.scan_body(tree.body, Flavours())

    def scan_sealed_slot_reach(self, tree: ast.Module) -> None:
        """RULE 3 over the whole module, in one pass and with no allowlist.

        Walked over the module rather than threaded through the expression scanner
        because it is not a question about flavour or about scope: naming the private
        slot is a violation wherever it appears, in an expression, in a default, in a
        decorator, in an annotation or in a string.
        """
        if self.declares_the_slot:
            return
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Attribute, ast.Constant)):
                continue
            # One assertion per node that COULD name the slot — every attribute access and
            # every constant in the module. Counting every AST node would inflate the
            # number without widening the guard, and an assertion count is evidence.
            self.check.asserted()
            reached = ""
            if isinstance(node, ast.Attribute) and node.attr in SEALED_MAGNITUDE_SLOTS:
                reached = node.attr
            elif isinstance(node, ast.Constant) and node.value in SEALED_MAGNITUDE_SLOTS:
                reached = str(node.value)
            if not reached:
                continue
            self.report(
                node,
                "RULE 3: reaching past the declared magnitude release",
                f"`{reached}` is the PRIVATE slot in which a DialMagnitude holds its "
                "number. Reaching it obtains a bare float without naming which dial it "
                "belongs to, which is the first half of a blend and the reason the slot "
                "is private. The declared release is "
                "`magnitude.quantity_for(<dial id>)`, which names one dial and refuses a "
                "mismatch by comparing provenance (CD-AC-002, CD-ASR-F01). There is no "
                "allowlist for this rule.",
            )

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

    if not (root / MAGNITUDE_MODULE).is_file():
        return check.refuse(
            f"{MAGNITUDE_MODULE} does not exist in this subject tree. That module is the "
            "type-level closure of CD-AC-002 after CD-ASR-F01 — the nominal, per-dial, "
            "non-coercible magnitude — and this check is only a LOCATOR over it. A tree "
            "without it has lost the layer that actually carries the criterion, so this "
            "check refuses rather than reporting a clean scan of the layer that does not."
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
        BlendScanner(
            check,
            path,
            _allow_co_occurrence(root, path),
            declares_the_slot=path.relative_to(root).as_posix() == MAGNITUDE_MODULE,
        ).scan_module(tree)

    return check.done(
        f"{len(files)} application Python files under {', '.join(SCAN_DIRS)}; "
        f"{len(CO_OCCURRENCE_ALLOWLIST)} paths allowlisted for RULE 2 only; RULE 1 and "
        f"RULE 3 have no allowlist (RULE 3 exempts only {MAGNITUDE_MODULE}, which "
        "declares the slot)"
    )


if __name__ == "__main__":
    raise SystemExit(main())
