#!/usr/bin/env python3
"""CD-RT-002-CONSTRUCTORS-ESTABLISH-FROM-THE-DECLARED-FIELD-LIST.

    python3 -B tools/register/check_constructor_field_establishment.py --root <subject tree>

CRITERION: CD-AC-002 and CD-AC-005. BP-AMENDMENT-0001 §D.1, in force, applied one level down
by the Product Owner's ruling at PO-DECISIONS-0007 ruling 1 (CD-D-105, answer (A)):

    "The principle that decides it is §D.1's own: establishment derived from the declaration,
     never written into an editable body. `__post_init__` IS A BODY."

and RE-BASED at PO-DECISIONS-0008 ruling 2 (CD-D-114) from a list of four types to A CLASS:

    "increment 5's scope is THE CLASS — every public type in the frozen subject on a
     judgement path whose field establishment is body-borne — ENUMERATED BY AN INSTRUMENT at
     increment-5 start, with its command and count recorded (CD-RULE-009). The four named
     types plus `AttemptRecord` are the FLOOR, NOT THE POPULATION."

WHAT THIS FILE IS, AND THE ORDER IN WHICH IT WAS BUILT
------------------------------------------------------
**THIS INSTRUMENT WAS WRITTEN AND RUN BEFORE THE MECHANISM IT NOW CHECKS FOR EXISTED**, on
the Project Lead's instruction and the Product Owner's reasoning: *"if you build the
mechanism first, your instrument will enumerate what your mechanism already covers — a
photograph of your own diff."* The population and count it printed at increment-5 start, on
a tree where **ZERO** classes carried ``@establishes``, are recorded in the Build Log entry
and in the commit that landed this file, with the command beside them (CD-RULE-009).

**IT IS AN ENUMERATOR FIRST AND AN ASSERTER SECOND, AND THE ENUMERATION IS THE PART THAT
MATTERS.** It parses; it does not import the product, so an auditor who trusts nothing in
the implementation can run it against a tree they extracted themselves. That also means it
proves NOTHING about runtime behaviour. The runtime claim is made by
``tests/test_field_establishment.py`` and by the plants, never here.

**EVERY CANDIDATE IT EXAMINED IS PRINTED WITH ITS VERDICT AND ITS REASON.** A member
excluded silently is the defect this instrument exists to prevent, so nothing is excluded
silently: ``--why`` prints the full ledger, and the counts are printed unconditionally.

====================================================================================
THE DEFINITION. IT IS PRINTED AT EVERY RUN SO A READER CAN DISAGREE WITH IT WITHOUT
READING THIS SOURCE.
====================================================================================

A class is **IN** the body-borne field-establishment class when ALL FOUR hold:

 (1) **PUBLIC** — its name does not begin with ``_``.
 (2) **FROZEN SUBJECT** — it is declared ``@dataclass(frozen=True, ...)``.
 (3) **ON A JUDGEMENT PATH** — reached by ANY of three unioned rules, all derived from the
     tree and none trusted alone:

       * **RULE A — JUDGEMENT-PATH PACKAGES.** It is defined in a module under
         ``src/crash_detector/engine/``, ``.../serving/`` or ``.../collectors/``. This is
         the same package set ``check_judgement_path_doors.py`` uses for its RULE 1, and it
         carries the same limit: **the package list is a VOCABULARY** (DECLARED LIMIT 2).
       * **RULE B — DOOR REACH, derived from the artefact.** Its name appears in the
         ``@admits(...)`` DECLARATION, a parameter annotation, or the return annotation of
         any callable in the tree that carries ``@admits(...)``. The doors are the subject
         of §D.1's own closure; the types those doors require or return are the types that
         cross a judgement-path boundary. **No list of judgement types is written into this
         file** — the set is read out of the decorations.
       * **RULE C — FIELD REACH, TRANSITIVE.** It is NAMED in the declared field annotation
         of a type already reached. A type the judgement path CARRIES INSIDE a type it
         already carries is on the judgement path: ``ConfigSnapshot`` declares a
         ``SourceRegistry`` field, so a ``SourceRegistry`` is something the judgement path
         holds. Run to a FIXPOINT, so the reach is a closure and not a hop.

     **RULES B AND C BOTH RESOLVE MODULE-LEVEL NAMES TO A FIXPOINT**, because both
     declarations and annotations reach types through a name rather than by spelling them:
     ``@admits(reading=one_of(*READING_CONSTRUCTORS))`` names no constructor, and
     ``outcome: 'FetchOutcome'`` names no outcome. **THE FIRST DRAFT OF THIS INSTRUMENT DID
     NOT RESOLVE THEM AND MEASURED THE POPULATION AT 18; RESOLVING THEM MEASURED IT AT 32.**
     That defect is recorded rather than quietly fixed: an instrument that stops at the
     spelling measures a VOCABULARY, which is the error this whole increment is about, and
     it found it in this file first.

 (4) **BODY-BORNE** — it defines ``__post_init__`` or ``__init__`` **in its own class
     body**, and that body EITHER

       * names at least one DECLARED FIELD of the class — ``self.<field>``, or the string
         ``'<field>'`` anywhere in the body — **OR**
       * reaches the field list REFLECTIVELY (``dataclasses.fields``, ``__dataclass_fields__``,
         ``self.__dict__``, ``vars(self)``), which establishes fields without naming them.

**(4) IS A HEURISTIC AND IS DECLARED AS ONE. ITS ERROR DIRECTION IS STATED.** No static
reader can tell *establishment* from *derivation*: a ``__post_init__`` that merely reads a
field to compute a message is counted IN by this test exactly as one that refuses a bad
value is. **The heuristic therefore OVER-INCLUDES, which is the safe direction** — it
enlarges the class the closure must cover and can never shrink it. The second clause exists
to close the under-including direction, which is the dangerous one: a body that establishes
fields by walking ``dataclasses.fields(self)`` names none of them.

**WHAT IS DELIBERATELY NOT A NARROWING.** The definition does not ask *what the body does
with the field*. Asking that is how a definition gets tuned until the population is the size
the author wanted, which is the defect PO-DECISIONS-0008 ruling 2 ruled on, and this
instrument's own enumeration is on the fourth Assurance seat's named-target list
(CD-D-119) precisely so that this file is read for that.

====================================================================================
WHAT IT ASSERTS ABOUT EACH MEMBER — THREE THINGS
====================================================================================
 1. the class carries ``@establishes(...)``;
 2. the field names ``establishes`` was told about are EXACTLY the class's declared field
    list — in BOTH directions. **This is P7 at the constructor level, caught statically: a
    NEW FIELD added to a governed type arrives REFUSED, never unguarded**;
 3. ``@establishes`` is applied OUTSIDE ``@dataclass``. Inside it, the field list does not
    exist yet and the mechanism cannot derive anything from it.

====================================================================================
DECLARED LIMIT (CD-RULE-004) — in this header, in ``required-tests.yaml`` and in
``contracts/execution/CD-RT-002-CONSTRUCTORS-ESTABLISH-FROM-THE-DECLARED-FIELD-LIST.md``,
each with an executable example. CD-RULE-006: each hand-off names a layer MEASURED to carry
it, or says NOT PROVED TO BE CARRIED ANYWHERE.
====================================================================================

 1  **THE ADJACENT SET: A FROZEN PUBLIC JUDGEMENT-PATH TYPE WITH NO ESTABLISHING BODY IS
    NOT IN THIS CLASS, AND IT IS COUNTED AND NAMED RATHER THAN DROPPED.** The class the
    Product Owner ruled is *body-borne* establishment. A type whose fields are established
    NOWHERE fails clause (4) — its establishment is ABSENT, not body-borne — so this check
    does not require ``@establishes`` of it. **THIS IS A REAL HOLE AND THIS SEAT IS NOT
    HIDING IT:** a NEW frozen judgement-path type written with no ``__post_init__`` at all
    is outside the ruled class and this check will report it as ADJACENT rather than fail.
    Every member of the adjacent set is printed with its file and line at every run.
    Executable example: add ``@dataclass(frozen=True)\\nclass Verdict: score: float`` to
    ``src/crash_detector/engine/`` with no ``__post_init__`` — this check exits 0 and names
    it in the ADJACENT SET.
    **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** No other layer requires establishment of
    a type that never establishes anything. RAISED AS A FINDING (CD-ENG-WO2R3-F17) and
    referred to the Project Lead and the Product Owner, because widening the ruled class is
    a scope decision and not this seat's to take (the dispatch's objective says "AND NOTHING
    ELSE").

 2  **RULE A's PACKAGE LIST IS A VOCABULARY.** ``engine``, ``serving`` and ``collectors``
    are spelled in this file. A frozen judgement-path type written under a package name this
    file has never heard of is reached only by RULE B, and only if some ``@admits`` door
    names it. This is the SAME limit ``check_judgement_path_doors.py`` declares as its
    DECLARED LIMIT 2, reached from the type side instead of the callable side. Executable
    example: ``variants/WO-2R3/V16-new-package-undecorated-door.patch`` adds
    ``src/crash_detector/judging/``; a frozen type placed there and named by no door is
    reached by neither rule.
    **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.**

 3  **``establishes`` AND ``admits`` ARE RECOGNISED BY THEIR NAMES IN THE SOURCE.** This
    check reads TEXT; it cannot know that the ``establishes`` a module imported is
    ``crash_detector.establishment.establishes``. This is the same limit
    ``check_judgement_path_doors.py`` declares as its DECLARED LIMIT 4 and it is inherited
    rather than newly incurred. Executable example: the counterfeit pattern of
    ``variants/WO-2R3/V18-counterfeit-admits.patch``, applied to ``establishes``.
    **CARRIER MEASURED: THE RUNTIME.** ``tests/test_field_establishment.py`` imports the
    product and constructs the real types; a counterfeit decorator leaves those tests
    failing. A static reader alone cannot carry this and does not claim to.

 4  **THIS CHECK ESTABLISHES THAT A DECLARATION EXISTS AND MATCHES THE FIELD LIST. IT DOES
    NOT ADJUDICATE WHAT WAS DECLARED.** ``@establishes(payload=ESTABLISHED_HERE("..."))``
    satisfies every assertion here. Every ``ESTABLISHED_HERE`` use is therefore PRINTED with
    its class, field and line at every run, exactly as the sibling check does for doors, so
    an exemption that starts absorbing the population is visible in the output rather than
    discovered later.
    **CARRIER MEASURED:** ``tests/test_field_establishment.py::
    test_the_established_here_field_exemptions_are_exactly_this_set`` pins the exact set —
    class, field and reason — so a new exemption is a test failure and not a quiet widening.
"""

from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import (  # noqa: E402
    Check,
    parse_root,
    read_text,
    resolve_root,
)

CHECK_ID = "CD-RT-002-CONSTRUCTORS-ESTABLISH-FROM-THE-DECLARED-FIELD-LIST"

#: RULE A. The same package set `check_judgement_path_doors.py` uses for its RULE 1. See
#: DECLARED LIMIT 2: this tuple is a vocabulary and says so.
JUDGEMENT_PATH_PACKAGES = ("engine", "serving", "collectors")

#: The decorator that makes a callable a judgement-path door. RULE B reads the types out of
#: these decorations rather than out of a list written here. See DECLARED LIMIT 3.
ADMITS = "admits"

#: The decorator that derives a type's field establishment from its DECLARED FIELD LIST.
ESTABLISHES = "establishes"

#: The exemption inside `establishes`. Every use is PRINTED with its location.
ESTABLISHED_HERE = "ESTABLISHED_HERE"

#: The bodies that can carry field establishment. `__post_init__` is the one the Product
#: Owner's ruling names; `__init__` is included because a hand-written `__init__` on a frozen
#: dataclass is the same body one step earlier.
ESTABLISHING_BODIES = ("__post_init__", "__init__")

#: Reflective reaches into the field list. A body using one of these establishes fields
#: WITHOUT NAMING THEM, which is clause (4)'s under-including direction.
REFLECTIVE_REACHES = ("fields", "__dataclass_fields__", "__dict__", "vars")

THE_DEFINITION = (
    "BODY-BORNE FIELD ESTABLISHMENT — a class is IN when ALL FOUR hold: "
    "(1) PUBLIC: its name does not begin with '_'. "
    "(2) FROZEN SUBJECT: declared @dataclass(frozen=True, ...). "
    "(3) ON A JUDGEMENT PATH, by any of three unioned rules derived from the tree — "
    "RULE A: defined under src/crash_detector/{engine,serving,collectors}/; "
    "RULE B: its name appears in the @admits(...) declaration, a parameter annotation or "
    "the return annotation of any callable carrying @admits(...); "
    "RULE C: it is named in the declared field annotation of a type already reached, run "
    "to a FIXPOINT. RULES B AND C RESOLVE MODULE-LEVEL NAMES TO A FIXPOINT, because both "
    "reach types through a name — one_of(*READING_CONSTRUCTORS) spells no constructor and "
    "outcome: 'FetchOutcome' spells no outcome. "
    "(4) BODY-BORNE: it defines __post_init__ or __init__ IN ITS OWN CLASS BODY, and that "
    "body either names at least one DECLARED FIELD of the class, or reaches the field list "
    "reflectively (dataclasses.fields / __dataclass_fields__ / __dict__ / vars). "
    "CLAUSE (4) IS A HEURISTIC AND OVER-INCLUDES BY DESIGN: no static reader can tell "
    "ESTABLISHMENT from DERIVATION, so a body that merely reads a field is counted IN. The "
    "error direction is toward a LARGER class, never a smaller one."
)


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _decorator_call(node, name: str):
    """The ``name(...)`` decorator on ``node``, its bare form, or ``None``."""
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if (getattr(target, "id", None) or getattr(target, "attr", None)) == name:
            return decorator
    return None


def _decorator_order(node) -> list:
    out = []
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        out.append(getattr(target, "id", None) or getattr(target, "attr", None) or "")
    return out


def _is_frozen_dataclass(node) -> bool:
    call = _decorator_call(node, "dataclass")
    if call is None or not isinstance(call, ast.Call):
        return False
    for keyword in call.keywords:
        if keyword.arg == "frozen" and isinstance(keyword.value, ast.Constant):
            return bool(keyword.value.value)
    return False


def _declared_fields(node) -> list:
    """The class's DECLARED FIELD LIST, read from its own body. ClassVar is not a field."""
    names = []
    for member in node.body:
        if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
            rendered = ast.unparse(member.annotation)
            if "ClassVar" in _identifiers(rendered):
                continue
            names.append(member.target.id)
    return names


def _identifiers(rendered: str) -> set:
    out: set = set()
    token = ""
    for character in rendered:
        if character.isalnum() or character == "_":
            token += character
        else:
            if token:
                out.add(token)
            token = ""
    if token:
        out.add(token)
    return out


def _establishing_body(node):
    """The ``__post_init__``/``__init__`` written in this class's own body, or ``None``."""
    for member in node.body:
        if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if member.name in ESTABLISHING_BODIES:
                return member
    return None


def _body_borne_evidence(body, fields: list) -> str:
    """Why clause (4) holds, or ``''`` if it does not."""
    named = []
    reflective = []
    for inner in ast.walk(body):
        if isinstance(inner, ast.Attribute) and inner.attr in fields:
            named.append(inner.attr)
        elif isinstance(inner, ast.Constant) and isinstance(inner.value, str):
            if inner.value in fields:
                named.append(inner.value)
        elif isinstance(inner, ast.Attribute) and inner.attr in REFLECTIVE_REACHES:
            reflective.append(inner.attr)
        elif isinstance(inner, ast.Name) and inner.id in REFLECTIVE_REACHES:
            reflective.append(inner.id)
    if named:
        return f"{body.name} names declared field(s) {sorted(set(named))}"
    if reflective:
        return f"{body.name} reaches the field list reflectively via {sorted(set(reflective))}"
    return ""


def _module_level_names(parsed) -> dict:
    """Every module-level ``NAME = <expression>``, as NAME -> identifiers in <expression>.

    This is what makes RULES B and C reach through a NAME. ``READING_CONSTRUCTORS``,
    ``PRESENTATION_CONSTRUCTORS``, ``Reading = Union[Value[T], Degraded[T], Unknown]`` and
    ``FetchOutcome = Union[OK, FetchFailed, Malformed, Empty]`` are all of them, and a rule
    that stopped at the spelling would reach none of the eight types they name.

    The namespace is FLAT ACROSS MODULES — a name defined anywhere resolves everywhere.
    That is deliberately WIDE: it can only enlarge the class, never shrink it, which is the
    safe direction for an instrument whose whole risk is being tuned small.
    """
    names: dict = {}
    for _path, tree in parsed:
        for node in tree.body:
            targets = []
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                value = node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target.id]
                value = node.value
            else:
                continue
            if value is None:
                continue
            found = _identifiers(ast.unparse(value))
            for target in targets:
                names.setdefault(target, set()).update(found)
    return names


def _resolved(identifiers: set, module_level: dict) -> set:
    """``identifiers`` plus everything the module-level names in it resolve to, to a fixpoint."""
    out = set(identifiers)
    pending = list(identifiers)
    while pending:
        name = pending.pop()
        for reached in module_level.get(name, ()):
            if reached not in out:
                out.add(reached)
                pending.append(reached)
    return out


def _admits_reach(parsed, module_level: dict) -> set:
    """RULE B, derived: every type name an ``@admits`` door requires or returns."""
    reached: set = set()
    for _path, tree in parsed:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            call = _decorator_call(node, ADMITS)
            if call is None:
                continue
            if isinstance(call, ast.Call):
                for keyword in call.keywords:
                    reached |= _identifiers(ast.unparse(keyword.value))
            for argument in (
                list(node.args.posonlyargs)
                + list(node.args.args)
                + list(node.args.kwonlyargs)
            ):
                if argument.annotation is not None:
                    reached |= _identifiers(ast.unparse(argument.annotation))
            if node.returns is not None:
                reached |= _identifiers(ast.unparse(node.returns))
    return _resolved(reached, module_level)


def _field_reach(seed: set, frozen_by_name: dict, module_level: dict) -> set:
    """RULE C, derived and run to a FIXPOINT: types named in the fields of reached types."""
    reached = set(seed)
    changed = True
    while changed:
        changed = False
        for name in list(reached):
            node = frozen_by_name.get(name)
            if node is None:
                continue
            named: set = set()
            for member in node.body:
                if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
                    named |= _identifiers(ast.unparse(member.annotation))
            for candidate in _resolved(named, module_level):
                if candidate in frozen_by_name and candidate not in reached:
                    reached.add(candidate)
                    changed = True
    return reached


def _established_here_fields(call) -> list:
    found = []
    if not isinstance(call, ast.Call):
        return found
    for keyword in call.keywords:
        if keyword.arg is None:
            continue
        for inner in ast.walk(keyword.value):
            head = inner.func if isinstance(inner, ast.Call) else inner
            if (getattr(head, "id", None) or getattr(head, "attr", None)) == ESTABLISHED_HERE:
                found.append(keyword.arg)
                break
    return found


def _extra(parser) -> None:
    parser.add_argument(
        "--why",
        action="store_true",
        help=(
            "print the verdict and the reason for EVERY class examined, including the ones "
            "ruled OUT. The counts are printed either way; this prints the ledger behind "
            "them."
        ),
    )


def main() -> int:
    arguments = parse_root(
        CHECK_ID,
        "Every public type in the frozen subject, on a judgement path, whose field "
        "establishment is BODY-BORNE, derives that establishment from its DECLARED FIELD "
        "LIST at the boundary (BP-AMENDMENT-0001 §D.1 one level down; PO-DECISIONS-0007 "
        "ruling 1; PO-DECISIONS-0008 ruling 2).",
        extra=_extra,
    )
    root, code = resolve_root(CHECK_ID, arguments.root)
    if root is None:
        return code
    check = Check(check_id=CHECK_ID, root=root)

    package_root = root / "src" / "crash_detector"
    if not package_root.is_dir():
        return check.refuse(
            f"{package_root} is not a directory. --root must be the repository root of the "
            "tree under audit, not the package directory."
        )

    files = sorted(
        path for path in package_root.rglob("*.py") if "__pycache__" not in path.parts
    )
    if not files:
        return check.refuse(f"no *.py found under {package_root}.")

    parsed = []
    for path in files:
        source = read_text(check, path)
        if source is None:
            continue
        try:
            parsed.append((path, ast.parse(source, filename=str(path))))
        except SyntaxError as exc:
            check.violation(
                path,
                getattr(exc, "lineno", 0) or 0,
                "UNPARSEABLE",
                f"this file could not be parsed ({exc}). A file inside the scanned set the "
                "check cannot read is a failure, not a file to pass over.",
            )

    module_level = _module_level_names(parsed)

    #: Every PUBLIC FROZEN DATACLASS in the tree, by name. RULE C walks this graph.
    frozen_by_name: dict = {}
    for path, tree in parsed:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and _is_public(node.name):
                if _is_frozen_dataclass(node):
                    frozen_by_name[node.name] = node

    reached_by_admits = _admits_reach(parsed, module_level)
    seed_a: set = set()
    for path, tree in parsed:
        relative = path.relative_to(package_root)
        if len(relative.parts) > 1 and relative.parts[0] in JUDGEMENT_PATH_PACKAGES:
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name in frozen_by_name:
                    seed_a.add(node.name)
    seed_b = {name for name in frozen_by_name if name in reached_by_admits}
    reached_by_field = _field_reach(seed_a | seed_b, frozen_by_name, module_level)

    population: list = []          # IN — the class
    adjacent_no_body: list = []    # frozen + public + judgement path, NO establishing body
    ledger: list = []              # every class examined, with its verdict and reason
    established_here: list = []
    classes_seen = 0
    by_rule_a = 0
    by_rule_b_only = 0
    by_rule_c_only = 0

    for path, tree in parsed:
        relative = path.relative_to(package_root)
        in_judgement_package = (
            len(relative.parts) > 1 and relative.parts[0] in JUDGEMENT_PATH_PACKAGES
        )
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            classes_seen += 1
            where = f"{relative}:{node.lineno} {node.name}"

            if not _is_public(node.name):
                ledger.append(f"OUT  {where} — clause (1): not public.")
                continue
            if not _is_frozen_dataclass(node):
                ledger.append(
                    f"OUT  {where} — clause (2): not declared @dataclass(frozen=True)."
                )
                continue
            rule_a = in_judgement_package
            rule_b = node.name in seed_b
            rule_c = node.name in reached_by_field
            if not (rule_a or rule_b or rule_c):
                ledger.append(
                    f"OUT  {where} — clause (3): reached by RULE A (package "
                    f"{'/'.join(JUDGEMENT_PATH_PACKAGES)}) — no; RULE B (named by an "
                    "@admits door, names resolved) — no; RULE C (named in the fields of a "
                    "reached type, to a fixpoint) — no."
                )
                continue
            if rule_a:
                reach = "RULE A"
                by_rule_a += 1
            elif rule_b:
                reach = "RULE B"
                by_rule_b_only += 1
            else:
                reach = "RULE C"
                by_rule_c_only += 1

            fields = _declared_fields(node)
            body = _establishing_body(node)
            if body is None:
                adjacent_no_body.append(f"{where} [{reach}] fields={fields}")
                ledger.append(
                    f"ADJ  {where} — clauses (1)(2)(3) hold by {reach}; clause (4) FAILS: "
                    "no __post_init__ or __init__ in its own class body. Its establishment "
                    "is ABSENT, not body-borne. See DECLARED LIMIT 1."
                )
                continue
            evidence = _body_borne_evidence(body, fields)
            if not evidence:
                adjacent_no_body.append(
                    f"{where} [{reach}] fields={fields} (body present, names no field)"
                )
                ledger.append(
                    f"ADJ  {where} — clauses (1)(2)(3) hold by {reach}; clause (4) FAILS: "
                    f"{body.name} exists but names no declared field and makes no reflective "
                    "reach. See DECLARED LIMIT 1."
                )
                continue

            population.append((path, node, relative, reach, fields, evidence))
            ledger.append(f"IN   {where} — [{reach}] clause (4): {evidence}.")

    # ---- THE ASSERTIONS. Three per member of the population. ---------------------------- #
    decorated = 0
    for path, node, relative, _reach, fields, _evidence in population:
        where = f"{relative}:{node.lineno} {node.name}"
        call = _decorator_call(node, ESTABLISHES)
        check.asserted()
        if call is None:
            check.violation(
                path,
                node.lineno,
                "FIELD_ESTABLISHMENT_NOT_DERIVED_FROM_THE_DECLARED_FIELD_LIST",
                f"{node.name} is a public frozen type on a judgement path whose field "
                f"establishment is BODY-BORNE, and it carries no @{ESTABLISHES}(...). "
                "PO-DECISIONS-0007 ruling 1: `__post_init__` IS A BODY, and a rule that "
                "lives in a body is removed by editing the body. The establishment must be "
                "derived from the DECLARED FIELD LIST and applied at the boundary, where a "
                "body rewrite cannot reach it.",
            )
            continue
        if not isinstance(call, ast.Call):
            check.violation(
                path,
                node.lineno,
                "ESTABLISHES_NOT_CALLED",
                f"{node.name} is decorated with a bare @{ESTABLISHES} rather than "
                f"@{ESTABLISHES}(...). A decorator that declares nothing declares nothing.",
            )
            continue
        decorated += 1
        established_here.extend(
            f"{relative}:{node.lineno} {node.name}.{field}"
            for field in _established_here_fields(call)
        )

        check.asserted()
        if any(keyword.arg is None for keyword in call.keywords):
            check.violation(
                path,
                node.lineno,
                "DECLARATION_UNREADABLE",
                f"{node.name}'s @{ESTABLISHES}(**...) is built from an expression this "
                "check cannot read. A declaration a static reader cannot enumerate cannot "
                "be checked against the field list.",
            )
        else:
            declared = [keyword.arg for keyword in call.keywords]
            undeclared = [name for name in fields if name not in declared]
            adrift = [name for name in declared if name not in fields]
            if undeclared:
                check.violation(
                    path,
                    node.lineno,
                    "FIELD_NOT_DECLARED_TO_ESTABLISHES",
                    f"{node.name} declares field(s) {undeclared} that @{ESTABLISHES}() was "
                    "not told about. A NEW FIELD on a judgement-path type arrives REFUSED, "
                    "never unguarded — P7 at the constructor level. The runtime refuses "
                    "every construction of this type; this is the same fact read without "
                    "importing anything.",
                )
            if adrift:
                check.violation(
                    path,
                    node.lineno,
                    "DECLARATION_ADRIFT_FROM_THE_FIELD_LIST",
                    f"{node.name}'s @{ESTABLISHES}() was told about {adrift}, which are not "
                    "declared fields of it. A declaration that has come adrift from its "
                    "field list is establishing a field that is not there.",
                )

        check.asserted()
        order = _decorator_order(node)
        if ESTABLISHES in order and "dataclass" in order:
            if order.index(ESTABLISHES) > order.index("dataclass"):
                check.violation(
                    path,
                    node.lineno,
                    "ESTABLISHES_APPLIED_INSIDE_DATACLASS",
                    f"{node.name} applies @{ESTABLISHES} BELOW @dataclass, so it runs "
                    "before the dataclass machinery has built the field list and there is "
                    "nothing to derive establishment FROM. It must be the outer decorator.",
                )

    # ---- THE OUTPUT. The enumeration is the part that matters. -------------------------- #
    check.note(f"THE DEFINITION — {THE_DEFINITION}")
    check.note(
        f"CLASSES EXAMINED: {classes_seen} across {len(parsed)} module(s) under "
        f"{package_root.relative_to(root)}."
    )
    check.note(
        f"POPULATION — THE BODY-BORNE FIELD-ESTABLISHMENT CLASS: {len(population)}. "
        f"DECLARED TO @{ESTABLISHES}: {decorated}."
    )
    check.note(
        f"  reached by RULE A (judgement-path package): {by_rule_a}; "
        f"by RULE B ONLY (named by an @{ADMITS} door, names resolved): {by_rule_b_only}; "
        f"by RULE C ONLY (named in the fields of a reached type, to a fixpoint): "
        f"{by_rule_c_only}."
    )
    for _path, node, relative, reach, fields, evidence in population:
        check.note(
            f"  IN [{reach}]: {relative}:{node.lineno} {node.name} — "
            f"{len(fields)} declared field(s) {fields} — {evidence}"
        )
    check.note(
        "THE FLOOR THE PRODUCT OWNER NAMED (PO-DECISIONS-0008 ruling 2) is ConfigSnapshot, "
        "DialSpec, ModelSpec, PanelRow, AttemptRecord — FIVE. THE FLOOR IS NOT THE "
        f"POPULATION and this run measures the population at {len(population)}."
    )
    check.note(
        f"ADJACENT SET — DECLARED LIMIT 1, frozen public judgement-path types whose "
        f"establishment is ABSENT rather than body-borne, and which this check therefore "
        f"does NOT require to be declared: {len(adjacent_no_body)}."
    )
    for row in adjacent_no_body:
        check.note(f"  ADJACENT (not required, and this is a real hole): {row}")
    check.note(f"ESTABLISHED_HERE field exemptions: {len(established_here)}.")
    for row in established_here:
        check.note(f"  ESTABLISHED_HERE: {row}")
    if arguments.why:
        check.note("THE FULL LEDGER — every class examined, with its verdict:")
        for row in ledger:
            check.note(f"  {row}")
    else:
        check.note(
            "Re-run with --why for the verdict and reason on every one of the "
            f"{classes_seen} classes examined, including the ones ruled OUT."
        )

    return check.done(
        f"{len(parsed)} module(s) under {package_root.relative_to(root)}; "
        f"{classes_seen} class(es) examined; {len(population)} in the class"
    )


if __name__ == "__main__":
    raise SystemExit(main())
