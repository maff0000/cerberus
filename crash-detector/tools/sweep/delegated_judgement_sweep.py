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

**AND SINCE WO-2R3 INCREMENT 7, THREE MORE — DRAFTED BY THE PROJECT LEAD, NOT YET RATIFIED**
(``PO-DECISIONS-0013`` ruling 3). The fifth Assurance seat's T8 measured the eleven undeclared
sites as THREE CATEGORIES where this form assumed one, and *"writing eleven dispositions into
a form that does not fit them would be the hand-maintained-summary defect with a signature"*.
**AN ENTRY USING ONE OF THESE IS ``(word, EVIDENCE MAPPING)`` AND NOT ``(word, note)``:**

    DEFECT_OPEN            a caller-influenceable route EXISTS and has been MEASURED. The
                           site is a real defect, recorded OPEN. **IT BUYS NOTHING** — not a
                           pass, not an exemption, and it does not make this sweep green.
                           REQUIRES: ``finding``, ``measured_reach``, ``counterfactual``.
    CARRIER_ONLY           reached by NO module under ``src/``; its only callers are carriers,
                           so the consequence of a false answer is CARRIER CREDIBILITY and not
                           product judgement. REQUIRES: ``callable``,
                           ``why_it_is_not_product_judgement``. **``callable`` IS
                           MACHINE-CHECKED — this word is an ENUMERATION, NOT A CLAIM, and it
                           fails the day a product module calls the thing.**
    UPSTREAM_OF_THE_PATH   not itself a judgement path, and in the closure anyway, because
                           what it decides is whether judgement-path doors establish their
                           arguments at all. **THE OPPOSITE OF AN EXCUSE.**
                           REQUIRES: ``decides``, ``route``.

**THE WORDS ARE A CONTRACT, NOT A LABEL SET.** An unrecognised word, a malformed entry, or an
extended word missing any mandatory evidence field is a VIOLATION — ``UNKNOWN_DISPOSITION``,
``MALFORMED_DISPOSITION``, ``DISPOSITION_EVIDENCE_MISSING``, ``CARRIER_ONLY_HAS_A_PRODUCT_CALLER``.

**A DEFECT THAT WAS ALREADY HERE AND IS CLOSED BY THE SAME CHANGE:** until increment 7 the
``DISPOSITIONS`` tuple was consulted **only to print the summary table**. A register entry
carrying a word that was not in it was silently accepted, counted into nothing, and never
shown — so the one thing the vocabulary existed to constrain, it did not constrain. That now
fails, for the original five exactly as hard as for the new three.

**THE ELEVEN DISPOSITIONS ARE NOT WRITTEN AND ARE NOT THIS CONTRACT'S AUTHOR'S** (CD-D-130).
This increment lands the FORM; the Product Owner ratifies the words; the Project Lead then
writes the contents. Every extended count below reads **0** at this SHA and that is correct.

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

#: THE FIVE ORIGINAL WORDS. A register entry using one of these is ``(word, note)`` where
#: ``note`` is prose, and that shape is UNCHANGED by this increment.
DISPOSITIONS = ("ESTABLISHED", "EXACT", "OWN", "DELEGATED", "OUT_OF_BOUND")

# ======================================================================================= #
# THE EXTENDED DISPOSITION VOCABULARY — **THE REGISTER CONTRACT.**
# WO-2R3 increment 7, PO-DECISIONS-0013 ruling 3:
#
#   *"The disposition vocabulary is EXTENDED FIRST. T8 measured three categories where the
#    form assumed one; writing eleven dispositions into a form that does not fit them would
#    be the hand-maintained-summary defect with a signature. The Project Lead drafts the
#    extended vocabulary (register-contract change, PO ratifies in-increment); THEN the
#    eleven are written."*
#
# **THE SPLIT IS SHARP AND THIS FILE IS ON ONE SIDE OF IT.** The Project Lead DRAFTED these
# three words. This file IMPLEMENTS THE CONTRACT THAT ACCEPTS THEM. The Product Owner
# RATIFIES. The Project Lead then writes the eleven dispositions in
# ``tools/sweep/declared_dispositions.py`` — **WHICH IS NOT THIS SEAT'S FILE AND CONTAINS NOT
# ONE WORD OF THIS SEAT'S** (CD-D-130).
#
# **THE WORDS ARE NOT RATIFIED.** This contract accepts them so the Product Owner can rule on
# something that EXISTS rather than on a proposal. If the ruling changes a word or drops one,
# this table is where that lands, and the eleven have not yet been written against it. That
# ordering is the whole of ruling 3.
#
# THE BINDING CONSTRAINT, VERBATIM FROM THE DISPATCH:
#   **"NO NEW WORD MAY BE A SYNONYM FOR 'NOT LOOKED AT'. The instrument must REJECT a
#   disposition whose mandatory evidence fields are absent — the words are a contract, not a
#   label set, and a vocabulary that can be satisfied with prose is the hand-maintained-
#   summary defect that ruling 3 exists to prevent."**
#
# **AND THE DEFECT THAT WAS ALREADY HERE, FOUND WHILE BUILDING THIS AND CLOSED BY IT.** Until
# this increment ``DISPOSITIONS`` WAS USED ONLY FOR PRINTING. A register entry carrying a
# word that is not in it was silently accepted, counted into nothing, and never printed — so
# the one thing the tuple existed to constrain, it did not constrain. ``UNKNOWN_DISPOSITION``
# below is that hole closed, and it binds the original five exactly as hard as the new three.
# ======================================================================================= #

#: word -> the evidence fields a register entry using it MUST carry, each present and
#: NON-EMPTY. An entry using one of these words is ``(word, evidence_mapping)`` and **not**
#: ``(word, note)``: the whole point is that prose is not enough for these three.
EXTENDED_DISPOSITIONS = {
    # A caller-influenceable route to this deciding operand EXISTS and has been MEASURED.
    # The site is a real defect, recorded OPEN, remediation owed and not yet done.
    # **IT BUYS NOTHING** — not a pass, not an exemption, and it does not make the sweep
    # green. A register full of DEFECT_OPEN is a register honestly describing a broken
    # system, and that is the word's entire purpose.
    "DEFECT_OPEN": ("finding", "measured_reach", "counterfactual"),
    # This site is reached by NO module under `src/`. Its only callers are carriers — tests
    # and instruments — so the consequence of a false answer is CARRIER CREDIBILITY, not
    # product judgement. **`callable` IS MACHINE-CHECKED**: see `_carrier_only_violations`.
    # This word is an ENUMERATION, NOT A CLAIM, and it breaks the build the day somebody
    # adds an import.
    "CARRIER_ONLY": ("callable", "why_it_is_not_product_judgement"),
    # This module is not itself a judgement path AND belongs in the closure anyway, because
    # what it decides is whether judgement-path doors establish their arguments at all.
    # **IT IS THE OPPOSITE OF AN EXCUSE.**
    "UPSTREAM_OF_THE_PATH": ("decides", "route"),
}

#: Every word the register may use. Anything else is `UNKNOWN_DISPOSITION`.
ALL_DISPOSITIONS = tuple(DISPOSITIONS) + tuple(EXTENDED_DISPOSITIONS)


def _disposition_contract_violations(declared_admissions, declared_modules):
    """Every register entry whose WORD or EVIDENCE does not satisfy the contract.

    **THIS IS THE HALF OF RULING 3 THAT IS NOT A VOCABULARY.** A word list is a label set;
    what makes it a CONTRACT is that an entry which does not carry the word's mandatory
    evidence is REFUSED. Returns a list of ``(rule, where, detail)``.
    """
    found = []
    for register, kind in (
        (declared_admissions, "ADMISSION"),
        (declared_modules, "MODULE"),
    ):
        for key, value in register.items():
            where = f"{key[0]}::{key[1]} {key[2]}: {key[3]}" if isinstance(key, tuple) else str(key)
            if not isinstance(value, tuple) or len(value) < 2:
                found.append((
                    "MALFORMED_DISPOSITION", where,
                    f"a {kind} entry must be (word, note-or-evidence); found {value!r}",
                ))
                continue
            word, evidence = value[0], value[1]
            if word not in ALL_DISPOSITIONS:
                found.append((
                    "UNKNOWN_DISPOSITION", where,
                    f"{word!r} is not a disposition. The vocabulary is "
                    f"{list(ALL_DISPOSITIONS)}. **UNTIL WO-2R3 INCREMENT 7 AN UNRECOGNISED "
                    "WORD WAS SILENTLY ACCEPTED AND SILENTLY UNPRINTED** — the one thing "
                    "the vocabulary existed to constrain, it did not constrain.",
                ))
                continue
            if word not in EXTENDED_DISPOSITIONS:
                continue
            required = EXTENDED_DISPOSITIONS[word]
            if not isinstance(evidence, dict):
                found.append((
                    "DISPOSITION_EVIDENCE_MISSING", where,
                    f"{word} requires an EVIDENCE MAPPING carrying {list(required)}, not "
                    f"prose. Found {type(evidence).__name__}. **A VOCABULARY THAT CAN BE "
                    "SATISFIED WITH PROSE IS THE HAND-MAINTAINED-SUMMARY DEFECT RULING 3 "
                    "EXISTS TO PREVENT.**",
                ))
                continue
            for field in required:
                if not str(evidence.get(field, "")).strip():
                    found.append((
                        "DISPOSITION_EVIDENCE_MISSING", where,
                        f"{word} requires {field!r} and it is absent or empty. "
                        "**NO NEW WORD MAY BE A SYNONYM FOR 'NOT LOOKED AT'.**",
                    ))
    return found


def _carrier_only_violations(declared_admissions, sources, subject):
    """**`CARRIER_ONLY` IS AN ENUMERATION, NOT A CLAIM, AND THIS IS WHERE THAT IS TRUE.**

    The word asserts *"this site is reached by NO module under ``src/``"*. The draft says the
    register *"must be able to show that no caller exists under ``src/``, by instrument, and
    FAIL when one appears. A ``CARRIER_ONLY`` that becomes false when somebody adds an import
    must break the build the day they add it."*

    So the declared ``callable`` is looked for as a CALL in every module of the swept subject
    other than the one that defines it. Any hit is a violation.

    **WHAT THIS CHECK DOES NOT SEE, DECLARED HERE RATHER THAN LEFT TO BE FOUND:** a call
    reached through an alias (``f = admission_faults; f(x)``), through ``getattr`` on a
    module, or through a container. It reads CALL EXPRESSIONS BY NAME. That is the same
    class of limit the doors instrument declares for ``ESTABLISHED_HERE``, and it means this
    check is a FLOOR on the caller set and not a proof of its emptiness.
    """
    found = []
    for key, value in declared_admissions.items():
        if not (isinstance(value, tuple) and len(value) >= 2):
            continue
        word, evidence = value[0], value[1]
        if word != "CARRIER_ONLY" or not isinstance(evidence, dict):
            continue
        name = str(evidence.get("callable", "")).strip()
        if not name:
            continue
        defining_module = key[0] if isinstance(key, tuple) else None
        for module in subject:
            if module == defining_module:
                continue
            tree = sources.get(module)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                target = node.func
                called = getattr(target, "id", None) or getattr(target, "attr", None)
                if called == name:
                    found.append((
                        "CARRIER_ONLY_HAS_A_PRODUCT_CALLER",
                        f"{key[0]}::{key[1]}" if isinstance(key, tuple) else str(key),
                        f"{name!r} is declared CARRIER_ONLY — 'reached by NO module under "
                        f"src/' — and {module} calls it at line {node.lineno}. **THE WORD "
                        "ASSERTS AN ENUMERATION AND THE ENUMERATION IS NOW FALSE.** Either "
                        "the caller is wrong or the disposition is.",
                    ))
    return found


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
    # `sources` is returned as well since WO-2R3 increment 7: `CARRIER_ONLY` is an
    # ENUMERATION over the swept modules, so the contract check needs the same parse the
    # sweep used. Re-parsing would be a second reading of one input and they come apart.
    return sites, sorted(subject), outside, sources


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
    sites, subject, outside, sources = sweep(root)

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
    for disposition in ALL_DISPOSITIONS:
        marker = "  (EXTENDED, PO RATIFICATION PENDING)" if disposition in EXTENDED_DISPOSITIONS else ""
        print(f"        {disposition:22s} {tier_1_dispositions[disposition]}{marker}")
    # **A WORD THE VOCABULARY DOES NOT KNOW USED TO VANISH HERE.** The loop printed the five
    # and a register entry carrying anything else was counted into nothing and never shown.
    # It is now a violation (UNKNOWN_DISPOSITION); this line is the visible half of that.
    unknown_words = sorted(
        {word for word, _ in tier_1_dispositions.items() if word not in ALL_DISPOSITIONS}
    )
    print(f"        words used that are NOT in the vocabulary: {len(unknown_words)} {unknown_words or ''}")

    if arguments.list or arguments.list_undeclared:
        rows = undeclared if arguments.list_undeclared else sorted(admissions)
        for site in rows:
            disposition, note = declared_admissions.get(site, ("UNDECLARED", ""))
            print(f"    [{disposition:12s}] {site[0]}::{site[1]} {site[2]}: {site[3]}")
            if note:
                print(f"                     {note}")

    # ------------------------------------------------------------------------------- #
    # THE DISPOSITION CONTRACT (WO-2R3 increment 7, PO-DECISIONS-0013 ruling 3).
    # **THE WORDS ARE A CONTRACT, NOT A LABEL SET**, and this is where that is true: an
    # unrecognised word, a malformed entry, or an extended word without its mandatory
    # evidence is a VIOLATION rather than a row nobody reads.
    # ------------------------------------------------------------------------------- #
    contract_failures = _disposition_contract_violations(
        declared_admissions, declared_modules
    ) + _carrier_only_violations(declared_admissions, sources, subject)

    violations = 0
    for rule, where, detail in contract_failures:
        violations += 1
        print(f"    {rule}: {where}\n        {detail}")
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
