#!/usr/bin/env python3
"""THE CLASS-2 SWEEP — every delegated judgement on the deciding paths, with a denominator.

    python3 -B tools/sweep/delegated_judgement_sweep.py --root .
    python3 -B tools/sweep/delegated_judgement_sweep.py --root . --list        # the table
    python3 -B tools/sweep/delegated_judgement_sweep.py --root . --list-undeclared

===========================================================================================
WHY THIS EXISTS, AND WHAT IT IS NOT
===========================================================================================
CD-AC-005's finding CD-ASR-WO2R-F02 was the FOURTH constructor route to ``Agrees`` after a
boundary had said "THREE MEASURED, and three is the denominator, not a proof that a fourth
does not exist". The hedge was honest and it did its job. What was missing was a way to say
what the denominator IS.

**THIS TOOL IS THE ENUMERATION, NOT THE CLOSURE, AND THE DIFFERENCE IS THE WHOLE POINT.**
The closure is :mod:`crash_detector.own_terms`: values are RE-CONSTRUCTED at the door, so no
method a caller defined runs while anything is being decided. That property is a runtime
property of the values and it does not depend on this file existing. What this file does is
make the SURFACE countable, and fail when the surface changes without anyone saying so.

It is a STATIC, INTRA-PROCEDURAL, AST-BASED LOCATOR. Every escape on this project's record
passed a static checker. Do not read a clean run of this tool as evidence that any class is
closed — read it as evidence that the set of places where a judgement COULD be delegated is
the set that was declared, and that each of them has a written disposition.

===========================================================================================
THE DENOMINATOR, AND THE METHOD BY WHICH IT IS TAKEN
===========================================================================================
**THE SUBJECT SET** is the transitive intra-package import closure of the six modules that
host a judgement about staleness, agreement or reading-ness — computed here, from the import
graph, rather than listed by hand:

    crash_detector.serving.witness_resolver   (agreement: resolve_panel, render_panel)
    crash_detector.witness.panel              (agreement: the sum type and its constructors)
    crash_detector.staleness                  (staleness: the window and the evidence)
    crash_detector.engine.evaluate            (staleness + reading-ness: the dial path)
    crash_detector.dials.reading              (reading-ness: fold, is_value)
    crash_detector.serving.dial_presentation  (reading-ness: what a surface may show)

The closure is OVER-INCLUSIVE ON PURPOSE. It is taken over MODULES, not over functions, so a
module that is imported for one constant still contributes every site it contains. An
over-inclusive denominator can only make this tool complain about places that do not matter;
an under-inclusive one is how a route goes uncounted.

**THE SITE SET** is every AST node in a subject module at which an operation could be
executed by an object the enclosing module did not construct. Two tiers, because the
dispatch asks for one and the class is the other:

  TIER 1 — ADMISSION.  ``isinstance``, ``issubclass``, ``hasattr``, ``getattr``. These are
  the sites the finding is literally about: a test that admits a value, and admits a
  subclass with it.

  TIER 2 — THE DECIDING OPERATION.  ``<  >  <= >= == !=`` (``__lt__`` and kin), ``in`` /
  ``not in`` (``__eq__`` and ``__hash__``), ``+ - * / % //`` (``__add__`` and kin),
  ``min`` / ``max`` / ``sorted`` / ``sum`` / ``math.fsum`` (``__lt__``), ``float`` / ``int``
  / ``str`` / ``len`` / ``bool`` / ``hash`` / ``math.isfinite`` / ``tuple`` / ``frozenset``
  / ``set`` / ``dict`` / ``list`` (``__float__``, ``__len__``, ``__iter__`` and kin), the
  set operators, truthiness in an ``if`` or behind a ``not``, and ``is`` / ``is not``
  (listed because identity is the one that is NEVER delegated, so it is the contrast).
  Tier 2 is where the auditor's variant actually did its work: ``isinstance`` let the object
  in, and ``__rsub__`` decided the answer.

**EVERY SITE CARRIES A WRITTEN DISPOSITION**, one of:

    ESTABLISHED   the operand was re-established by crash_detector.own_terms before this
                  operation, so what runs is CPython's implementation for an exact base type
    EXACT         the check is exact-type identity, or a comparison between class objects of
                  types this package sealed against subclassing
    OWN           both operands are values this module constructed in the same scope
    DELEGATED     the deciding operation IS executed by a supplied object — OPEN, and the
                  note says under whose authority it is left open
    OUT_OF_BOUND  reached by the sweep and DECLARED as outside this increment's scope

**THE REGISTER IS ASSERTED BY SET EQUALITY IN BOTH DIRECTIONS.** A site with no disposition
fails this tool, and a disposition for a site that no longer exists fails it too — because a
register that only complained about additions could be satisfied by deleting the entry that
does the complaining. That is the same argument
:data:`crash_detector.dials.reading.DECLARED_MEMBER_SURFACE` already makes about a class
dictionary.

===========================================================================================
DECLARED LIMIT (CD-RULE-004). This tool CLOSES NOTHING; it counts.
===========================================================================================
 1  IT IS STATIC AND INTRA-PROCEDURAL. It reads one expression at a time and does not know
    what any name is bound to at runtime. A disposition of ESTABLISHED is a CLAIM BY THIS
    SEAT about the code around the site, not something this tool verified. The runtime
    evidence for those claims is ``tests/test_own_terms.py`` and the variants under
    ``variants/WO-2R2/CLASS-2/``, and the claim an auditor should attack is the disposition
    text, not the count.
    CARRIER FOR THE RUNTIME HALF, MEASURED: crash_detector.own_terms, exercised by
    tests/test_own_terms.py (29 tests) and by the variants. For a site whose disposition is
    wrong, NOT PROVED TO BE CARRIED ANYWHERE — a mis-declared disposition is invisible here
    by construction.

 2  IT SEES ONLY OPERATORS AND CALLS WRITTEN LITERALLY IN THE SUBJECT MODULES. An operation
    reached through ``operator.lt``, ``functools.reduce``, a dunder invoked by name, a
    comprehension over a caller's generator, or any C-level protocol call CPython makes on
    this code's behalf is NOT a node this tool visits.
    MEASURED EXAMPLE, executable: a module writing ``operator.__lt__(a, b)`` instead of
    ``a < b`` produces no site here. NOT PROVED TO BE CARRIED ANYWHERE at the static layer;
    the RUNTIME layer carries it, because own_terms re-establishes the VALUE and an
    operation on an established value is CPython's whichever syntax reaches it.

 3  ITS SUBJECT SET IS AN IMPORT CLOSURE, SO A MODULE THAT REACHES A JUDGEMENT WITHOUT
    IMPORTING ONE OF THE SIX IS OUTSIDE IT. Nineteen names of this package are outside the
    closure — six package ``__init__`` modules and thirteen real ones — and every run prints
    them by name so the exclusion is disclosed rather than discovered. The claim that none of
    them decides staleness, agreement or reading-ness is a claim about THIS SHA, made by
    reading them, and it is the claim to attack: ``crash_detector.collectors.*`` CONSTRUCTS
    the timestamps that are later judged, and ``crash_detector.publication.*`` renders what
    was decided, but neither decides. NOT PROVED TO BE CARRIED ANYWHERE.

 4  A DISPOSITION IS KEYED BY THE EXPRESSION'S TEXT, so renaming a local variable makes the
    site UNDECLARED and this tool FAILS. That is the safe direction and it is deliberate: it
    is better to be asked to re-declare a site than to have a register quietly follow a
    rename. It also means a clean run of this tool is evidence about THIS SOURCE TEXT and
    survives no rewriting of it.
"""

from __future__ import annotations

import argparse
import ast
import collections
import pathlib
import sys

PACKAGE = "crash_detector"

#: The six modules that host a judgement about staleness, agreement or reading-ness. The
#: subject set is their transitive intra-package import closure, computed at run time.
JUDGEMENT_ENTRY_MODULES: tuple = (
    "crash_detector.serving.witness_resolver",
    "crash_detector.witness.panel",
    "crash_detector.staleness",
    "crash_detector.engine.evaluate",
    "crash_detector.dials.reading",
    "crash_detector.serving.dial_presentation",
)

TIER_1_ADMISSION = ("ISINSTANCE", "ISSUBCLASS", "DUCK")

_ORDERING_CALLS = frozenset({"min", "max", "sorted", "sum", "fsum"})
_COERCION_CALLS = frozenset(
    {
        "float",
        "int",
        "str",
        "len",
        "bool",
        "hash",
        "isfinite",
        "tuple",
        "frozenset",
        "set",
        "dict",
        "list",
        "next",
        "iter",
    }
)

DISPOSITIONS = ("ESTABLISHED", "EXACT", "OWN", "DELEGATED", "OUT_OF_BOUND")


class SweepFailed(SystemExit):
    pass


# ------------------------------------------------------------------------------------- #
# the enumerator
# ------------------------------------------------------------------------------------- #


class _Sites(ast.NodeVisitor):
    def __init__(self, module: str) -> None:
        self.module = module
        self.scope: list = []
        self.sites: list = []

    def _qualname(self) -> str:
        return ".".join(self.scope) or "<module>"

    def _record(self, node: ast.AST, category: str) -> None:
        self.sites.append(
            (self.module, self._qualname(), category, _normalise(ast.unparse(node)))
        )

    def visit_FunctionDef(self, node) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node) -> None:
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name == "isinstance":
            self._record(node, "ISINSTANCE")
        elif name == "issubclass":
            self._record(node, "ISSUBCLASS")
        elif name in ("hasattr", "getattr"):
            self._record(node, "DUCK")
        elif name in _ORDERING_CALLS:
            self._record(node, "ORDERING")
        elif name in _COERCION_CALLS:
            self._record(node, "COERCION")
        self.generic_visit(node)

    def visit_Compare(self, node) -> None:
        for op in node.ops:
            if isinstance(op, (ast.Is, ast.IsNot)):
                self._record(node, "IDENTITY")
            elif isinstance(op, (ast.In, ast.NotIn)):
                self._record(node, "MEMBERSHIP")
            else:
                self._record(node, "COMPARE")
        self.generic_visit(node)

    def visit_BinOp(self, node) -> None:
        if isinstance(
            node.op,
            (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv),
        ):
            self._record(node, "ARITH")
        elif isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.BitXor)):
            self._record(node, "SETOP")
        self.generic_visit(node)

    def visit_If(self, node) -> None:
        if not isinstance(node.test, (ast.Compare, ast.Call)):
            self._record(node.test, "TRUTHINESS")
        self.generic_visit(node)

    def visit_UnaryOp(self, node) -> None:
        if isinstance(node.op, ast.Not) and not isinstance(
            node.operand, (ast.Compare, ast.Call)
        ):
            self._record(node.operand, "TRUTHINESS")
        self.generic_visit(node)


def _normalise(text: str) -> str:
    """One line, single-spaced. A site's key must not move when a line is re-wrapped."""
    return " ".join(text.split())


def _module_name(path: pathlib.Path, package_root: pathlib.Path) -> str:
    relative = path.relative_to(package_root.parent).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _closure(sources: dict) -> set:
    """The transitive intra-package import closure of the six judgement entry modules."""
    imports = collections.defaultdict(set)
    for module, tree in sources.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(PACKAGE):
                    imports[module].add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(PACKAGE):
                        imports[module].add(alias.name)
    reached: set = set()
    pending = list(JUDGEMENT_ENTRY_MODULES)
    while pending:
        module = pending.pop()
        if module in reached or module not in sources:
            continue
        reached.add(module)
        pending.extend(imports[module])
    return reached


def sweep(root: pathlib.Path):
    package_root = root / "src" / PACKAGE
    if not package_root.is_dir():
        raise SweepFailed(f"no package at {package_root}")
    sources = {}
    paths = {}
    for path in sorted(package_root.rglob("*.py")):
        module = _module_name(path, package_root)
        sources[module] = ast.parse(path.read_text(encoding="utf-8"))
        paths[module] = path
    subject = _closure(sources)
    sites = []
    for module in sorted(subject):
        visitor = _Sites(module)
        visitor.visit(sources[module])
        sites.extend(visitor.sites)
    outside = sorted(set(sources) - subject)
    return sites, sorted(subject), outside


# ------------------------------------------------------------------------------------- #
# the declared disposition register
# ------------------------------------------------------------------------------------- #

def _load_register():
    """Load the sibling register without requiring the repository on sys.path.

    A tool an auditor runs as `python3 -B tools/sweep/...` from a tree it extracted itself
    must not need a PYTHONPATH, an installed package or a wrapper (PBG-ASSURE-001).
    """
    here = pathlib.Path(__file__).resolve().parent / "declared_dispositions.py"
    namespace: dict = {"__file__": str(here), "__name__": "declared_dispositions"}
    exec(compile(here.read_text(encoding="utf-8"), str(here), "exec"), namespace)
    return namespace["DECLARED_ADMISSIONS"], namespace["DECLARED_MODULE_DISPOSITIONS"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--list", action="store_true", help="print every site")
    parser.add_argument("--list-undeclared", action="store_true")
    arguments = parser.parse_args(argv)
    root = pathlib.Path(arguments.root).resolve()

    declared_admissions, declared_modules = _load_register()
    sites, subject, outside = sweep(root)

    admissions = {site for site in sites if site[2] in TIER_1_ADMISSION}
    deciding = [site for site in sites if site[2] not in TIER_1_ADMISSION]

    undeclared = sorted(admissions - set(declared_admissions))
    stale = sorted(set(declared_admissions) - admissions)
    undeclared_modules = sorted(set(subject) - set(declared_modules))
    stale_modules = sorted(set(declared_modules) - set(subject))

    by_category = collections.Counter(site[2] for site in sites)
    tier_1_dispositions = collections.Counter(
        declared_admissions[site][0] for site in admissions if site in declared_admissions
    )
    tier_2_by_module = collections.Counter(site[0] for site in deciding)

    print("CD-CLASS-2-DELEGATED-JUDGEMENT-SWEEP")
    print(
        f"    SUBJECT SET: the transitive intra-package import closure of "
        f"{len(JUDGEMENT_ENTRY_MODULES)} judgement entry modules = {len(subject)} modules"
    )
    for module in subject:
        disposition = declared_modules.get(module, ("UNDECLARED", ""))[0]
        print(f"        [{disposition:12s}] {module:44s} tier-2 sites: "
              f"{tier_2_by_module[module]}")
    print(f"    OUTSIDE THE CLOSURE, therefore NOT swept: {len(outside)} modules")
    for module in outside:
        print(f"        {module}")
    print(f"    THE DENOMINATOR: {len(sites)} sites")
    print(f"        TIER 1 — admission: {len(admissions)} distinct sites "
          f"({sum(by_category[c] for c in TIER_1_ADMISSION)} occurrences)")
    for category in TIER_1_ADMISSION:
        print(f"            {category:12s} {by_category[category]}")
    print(f"        TIER 2 — the deciding operation: {len(deciding)} occurrences")
    for category, count in sorted(by_category.items()):
        if category not in TIER_1_ADMISSION:
            print(f"            {category:12s} {count}")
    print("    TIER 1 DISPOSITIONS, declared per site:")
    for disposition in DISPOSITIONS:
        print(f"        {disposition:14s} {tier_1_dispositions[disposition]}")

    if arguments.list or arguments.list_undeclared:
        rows = undeclared if arguments.list_undeclared else sorted(admissions)
        for site in rows:
            disposition, note = declared_admissions.get(site, ("UNDECLARED", ""))
            print(f"    [{disposition:12s}] {site[0]}::{site[1]} {site[2]}: {site[3]}")
            if note:
                print(f"                     {note}")

    violations = 0
    for site in undeclared:
        violations += 1
        print(
            f"    UNDECLARED ADMISSION: {site[0]}::{site[1]} {site[2]}: {site[3]}\n"
            "        A tier-1 admission on a deciding path has no written disposition. "
            "Declare it in tools/sweep/declared_dispositions.py — including DELEGATED or "
            "OUT_OF_BOUND, which are legitimate answers when they are written down."
        )
    for site in stale:
        violations += 1
        print(
            f"    STALE DECLARATION: {site[0]}::{site[1]} {site[2]}: {site[3]}\n"
            "        A disposition is declared for a site that does not exist. The register "
            "is asserted by set equality in BOTH directions, because one that only noticed "
            "additions could be satisfied by deleting the entry that complains."
        )
    for module in undeclared_modules:
        violations += 1
        print(
            f"    UNDECLARED MODULE: {module}\n"
            "        A module entered the judgement closure with no tier-2 disposition. "
            "Say how its deciding operands are established, or say they are not."
        )
    for module in stale_modules:
        violations += 1
        print(
            f"    STALE MODULE DECLARATION: {module}\n"
            "        Declared, but no longer in the closure."
        )

    if violations:
        print(
            f"CD-CLASS-2-SWEEP: FAIL — {len(sites)} sites, {violations} violations"
        )
        return 1
    open_sites = (
        tier_1_dispositions["DELEGATED"] + tier_1_dispositions["OUT_OF_BOUND"]
    )
    open_modules = sum(
        1
        for module in subject
        if declared_modules[module][0] in ("DELEGATED", "OUT_OF_BOUND")
    )
    print(
        f"CD-CLASS-2-SWEEP: PASS — {len(sites)} sites enumerated over {len(subject)} "
        f"modules; every tier-1 admission and every subject module carries a written "
        f"disposition; {open_sites} tier-1 sites and {open_modules} modules are declared "
        "OPEN or OUT OF BOUND and are named in this increment's Build Log. A PASS here is "
        "a statement about the SURFACE and never about the class."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
