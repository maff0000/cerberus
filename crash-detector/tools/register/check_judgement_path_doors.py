#!/usr/bin/env python3
"""CD-RT-002-DOORS-REQUIRE-THEIR-TYPES — every judgement-path door is an ``admits`` door.

    python3 -B tools/register/check_judgement_path_doors.py --root <subject tree>

CRITERION: CD-AC-002 and CD-AC-005. BP-AMENDMENT-0001 §D.1, in force:

    "Every public entry point on a judgement path establishes each of its arguments by
     EXACT TYPE at the door, and the establishment is derived from the signature rather
     than written into the body."

§D.1 names the acceptance test for that rule in the same paragraph, and this is it: *"a
static check that enumerates the judgement paths and fails on any public entry point that
is not decorated — not a list of three fixes."*

WHAT THIS CHECK IS, AND WHAT IT IS NOT
----------------------------------------
**IT IS AN ENUMERATOR, AND ITS VALUE IS THE DENOMINATOR IT PRINTS.** It parses; it does not
import the product and it does not execute it, so an auditor who trusts nothing in the
implementation can run it against a tree they extracted themselves. That also means it
proves NOTHING about runtime behaviour: every escape on this project's record passed a
static checker. The runtime claim is made by the plants (P5, P6, P7) and by
``tests/test_admission.py``, not here.

**IT DERIVES ITS SUBJECT FROM THE ARTEFACT AND NEVER FROM A LIST OF DOORS** (CD-D-098). The
amendment's §B measured 44 public callables with an unestablished parameter at ``f30e63c``.
That number is a floor on where to look and it is already STALE: WO-2R3 increment 1 created
``engine/mapping.py`` and with it ``compute(spec, payloads)`` — the one place in the product
a dial magnitude is computed — which post-dates the inventory entirely. A check enumerating
44 names would not have looked at it. This one walks the tree, so ``engine.mapping.compute``
is a subject because it EXISTS, and so is whatever the next increment writes.

**IT PRINTS ITS SUBJECT COUNT**, so a vacuous pass is visible. A run that found no subjects
refuses (``PBG-CI-002`` via ``Check.done``): `exit 0` must never be able to mean "I looked
at nothing".

HOW A SUBJECT IS DERIVED — TWO INDEPENDENT RULES, UNIONED
-----------------------------------------------------------
A callable is a SUBJECT if EITHER rule reaches it. They are unioned rather than intersected
because each covers the other's blind spot, and neither is trusted alone.

**RULE 1 — JUDGEMENT-PATH PACKAGES, DENY-BY-DEFAULT WITHIN THEM.** Every ``*.py`` under
``src/crash_detector/engine/`` and ``src/crash_detector/serving/`` is read, and every public
module-level ``def`` and every public method of a public class in it is a subject. Nothing
inside those packages is opted out by name: a NEW MODULE is a subject with no edit to this
file, which is the CD-D-098 property above.

**RULE 2 — RETURN-TYPE REACH, ANYWHERE UNDER ``src/``.** Any public callable whose return
annotation names one of the JUDGEMENT VALUE TYPES — the types that ARE a dial's answer or a
witness's answer — is a subject wherever it lives, including in a package rule 1 has never
heard of. A judgement-path door added under a new package name is caught by this rule if it
declares what it returns.

EXEMPTIONS, EACH DERIVED FROM THE ARTEFACT AND EACH COUNTED IN THE OUTPUT
--------------------------------------------------------------------------
* names beginning ``_`` — not public entry points;
* ``@property`` accessors — a property getter takes only its receiver, and no argument can
  be added to one, so there is nothing for ``admits`` to be told about and nothing that can
  arrive later unguarded;
* methods of a class whose bases include ``Protocol`` — these are stubs describing a
  boundary to a foreign system, they have no body to guard, and BP-AMENDMENT-0001 §D.3
  (increment 3) is where that boundary is closed, by a different mechanism.

Each exemption's COUNT is printed. An exemption that starts absorbing the subject set is
therefore visible in the output rather than discovered later.

WHAT IT ASSERTS ABOUT EACH SUBJECT — TWO THINGS
-------------------------------------------------
1. it carries ``@admits(...)``;
2. the parameter names ``admits`` was told about are EXACTLY the parameter names in the
   signature, minus the method receiver. This is planted violation **P7** caught statically
   as well as at runtime: a new parameter added to a decorated door fails HERE too, and it
   fails without the module being imported.

====================================================================================
DECLARED LIMIT (CD-RULE-004) — in this header, in required-tests.yaml and in
contracts/execution/CD-RT-002-DOORS-REQUIRE-THEIR-TYPES.md, each with an executable
example. CD-RULE-006: each hand-off names a layer MEASURED to carry it, or says NOT PROVED
TO BE CARRIED ANYWHERE.

**THIS ROW HAS SIX DECLARED LIMITS AND ONLY FOUR OF THEM ARE BELOW.** The four here are
THE STATIC CHECK'S. Limits **5** (§D.1's rule is NOT held at the three §B.3 doors, whose
type establishment is body-borne) and **6** (the interpreter reach — ``__closure__``,
``__wrapped__``, and rebinding the establishing function in its own module namespace) are
THE MECHANISM'S, they live in the header of ``src/crash_detector/admission.py``, and they
are reproduced in full in the register entry and the execution contract. Numbering runs
1..6 across the two headers on purpose: they are one row's limits, not two lists.
An auditor who reads only this file has read FOUR SIXTHS of what this row declares open.
(CD-PL-F81, ruled CD-D-111 — until WO-2R3 increment 4 the register carried four of six and
``grep -c "__closure__" required-tests.yaml`` returned 0.)
====================================================================================

 1  **CONSTRUCTORS ARE STILL NOT SUBJECTS *OF THIS CHECK*, AND SINCE WO-2R3 INCREMENT 5
    THAT IS NO LONGER AN UNCARRIED GAP. NARROWED TO ITS MEASURED REACH; THE SUPERSEDED
    WORDING IS QUOTED RATHER THAN DELETED.**

    It read: *"CONSTRUCTORS ARE NOT SUBJECTS OF THIS CHECK, AND THAT IS A REAL GAP IN §D AS
    SCOPED. ... §D.2 lists no constructor and this check does not invent that scope. ... As
    a residue of §D.1's own rule: NOT PROVED TO BE CARRIED ANYWHERE."* The Product Owner
    ruled on exactly that declaration at PO-DECISIONS-0007 ruling 1 — ``__post_init__`` IS A
    BODY — and re-based it at PO-DECISIONS-0008 ruling 2 from four named types to THE CLASS.

    **STILL TRUE:** this check reads CALLABLES, and a constructor is not one of its
    subjects. Executable example, re-measured at increment 5 on a pristine extraction:
    ``variants/WO-2R3/V17-constructor-body-escape.patch`` deletes the
    ``type(spec) is not DialSpec`` loop from ``ConfigSnapshot.__post_init__`` and **this
    check still exits 0 with 54 assertions**. No reader should infer anything about
    constructors from a clean run of THIS check.

    **NO LONGER TRUE — THE HAND-OFF, AND THE CARRIER IS MEASURED (CD-RULE-006):** the
    structure is ``crash_detector.establishment.establishes``; the enumeration is
    ``python3 -B tools/register/check_constructor_field_establishment.py --root .``, which
    **ENUMERATES that class and asserts every fielded member carries its declaration —
    RUN IT AND READ ITS POPULATION LINE; NO COUNT IS TRANSCRIBED HERE** (CD-RULE-009, and
    see the note below on CD-PL-F91); and
    the measurement is V17 itself, RUN — with V17 applied and the mechanism present a duck
    ``DialSpec`` into ``ConfigSnapshot`` is REFUSED with
    ``establishment.FieldNotEstablished``, and with the mechanism removed
    (``V40-v17-violated-arm-establishes-removed.patch``) the same construction ESCAPES.

    **STILL NOT CARRIED, so this correction does not overstate itself:** the new mechanism
    establishes a field's TYPE and never a RELATION BETWEEN TWO FIELDS. §C.5's invariants 2
    and 3 and ``ConfigSnapshot``'s one-spec-per-dial REMAIN BODY-BORNE —
    ``variants/WO-2R3/V36-cross-field-invariant-body-rewrite.patch``, measured, ACCEPTED —
    and for that residue: **NOT PROVED TO BE CARRIED ANYWHERE.** It lives as residue (ii) of
    the constructor check's DECLARED LIMIT 1.

    **AND THIS NOTE ONCE CARRIED A COPY OF THE SIBLING'S CLASS DEFINITION AND COUNT, WHICH
    NO RULE POINTED AT (CD-PL-F91, raised by the Project Lead against this project's rules
    and not against a seat).** It read *"...which measures the body-borne field-establishment
    class at 32 members"*. That sentence carried BOTH the sibling's old class wording and a
    count, in a FOURTH place — CD-RULE-004's "all three places" are a LIMIT'S OWN three, and
    a copy living in a DIFFERENT instrument was outside every rule that keeps the three in
    step. PO-DECISIONS-0010 ruling 1 widened that class to **BODY-BORNE OR ABSENT** and
    moved the count, so the copy went stale exactly as an unpointed-at copy does. **THE
    REPAIR IS THAT THIS NOTE NOW CARRIES NEITHER** — no definition of the sibling's class
    and no count of it. It names the sibling's command instead, so a reader who wants either
    gets it from a measurement.

 2  **RULE 1's PACKAGE LIST IS A VOCABULARY.** ``engine`` and ``serving`` are spelled here.
    A judgement-path door written under a package name this file has never heard of is
    reached only by rule 2, and only if it annotates its return type. Executable example:
    ``variants/WO-2R3/V16-new-package-undecorated-door.patch`` adds
    ``src/crash_detector/judging/decide.py`` with a public, undecorated, unannotated
    ``decide(reading)`` — and this check still exits 0.
    **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** No other layer enumerates judgement-path
    packages. It is stated here so the fourth Assurance seat can hit it without having to
    find it first.

 3  **``collectors/`` IS NOW A JUDGEMENT-PATH PACKAGE, AND WHAT REMAINS OPEN THERE IS
    NAMED CD-BP-003.** The limit this slot held at WO-2R3 increment 2 — *"``collectors/`` is
    not yet a judgement-path package here, by scope and not by oversight"* — WAS DISCHARGED
    AT INCREMENT 3 AND IS NOT RESTATED. ``collectors`` is in ``JUDGEMENT_PATH_PACKAGES``
    above, deny-by-default within, so every public callable in it is a subject and a new
    module there is a subject the day it is written.

    **THE SIZE OF THAT DISCHARGE, RE-MEASURED AT INCREMENT 4 AND STATED LIKE-FOR-LIKE**
    (CD-PL-F82, ruled CD-D-120). It was recorded as *"subjects 19 -> 24"*, which compared a
    TOTAL against a SUBSET: this check reaches subjects by two unioned rules, and at both
    SHAs rule 2 reaches 3 doors rule 1 does not, so 24 was the rule-1 part of a total of 27.
    Both figures below are re-derived by RUNNING THIS FILE, not transcribed::

        git archive 995ec3e | tar -x -C /tmp/cd-995   # increment-2 head, the base
        cd /tmp/cd-995 && python3 -B tools/register/check_judgement_path_doors.py --root .
            -> SUBJECTS ENUMERATED: 19. DECORATED: 19.   by rule 2 only: 3
            -> PASS — 38 assertions, 0 violations

        git archive 04cdd34 | tar -x -C /tmp/cd-clean # increment-3 head, this lane
        cd /tmp/cd-clean && python3 -B tools/register/check_judgement_path_doors.py --root .
            -> SUBJECTS ENUMERATED: 27. DECORATED: 27.   by rule 2 only: 3
            -> PASS — 54 assertions, 0 violations

    **TOTAL: 19 -> 27. RULE-1 SUBSET: 16 -> 24. ASSERTIONS: 38 -> 54.** The two subset
    figures are the printed total minus the printed rule-2-only count, arithmetic on this
    check's own output. Never pair 19 with 24: they are different measurements. The
    correction makes the coverage WIDER than it was claimed to be, not narrower — 27 of 27
    subjects are decorated. Nothing was unguarded because of the error, and nothing here
    changes what the check does: ``tests/test_judgement_path_doors.py`` still asserts
    ``subjects >= 24``, A FLOOR, which is why the discrepancy was never caught. **Raising
    that floor to an equality is NOT ruled and is NOT done here** (CD-D-120); it is a code
    change answering a documentary finding, and it is left alone deliberately.

    **WHAT IS OPEN IS NARROWER, AND IT IS THE SOFTEST SURFACE IN THE PRODUCT**
    (BLUEPRINT §17, CD-BP-003; the Product Owner named it the fourth Assurance seat's first
    target). ``collect``'s ``adapter``, ``sink``, ``ledger`` and ``validator`` are
    ``Protocol`` boundaries to genuinely foreign things — a market data source, the store —
    so exact-typing them against a concrete class is not available and BP-AMENDMENT-0001
    §D.3 part 2 says it would be wrong. They are declared ``ESTABLISHED_HERE`` and **this
    check prints all four, with file, line and parameter, at every run**, derived from the
    ARTEFACT and not from a list written here. **IT IS A DOOR THAT ADMITS, NOT AN ABSENCE OF
    A DOOR.**

    What IS closed at that door, and is not a limit: ``policy`` exact ``RetryPolicy``
    (``isinstance`` admitted a subclass shadowing ``max_attempts`` with a property until
    increment 3), ``started_utc`` exact ``datetime`` then rebuilt by ``ensure_utc``,
    ``delay`` exact ``DelayKind``, and every value the four Protocols RETURN exact-typed at
    its point of return.

    What is NOT closed, executable example — and it is a POSITIVE example, an object that is
    ADMITTED::

        class ConformingButFictional:            # supplies all five protocol members
            source_id = "src.does.not.exist"     # returns an exact FetchedResponse
            adapter_id = "fiction.v0"            # carrying a schema-conforming payload
            response_schema = {...}              # that it invented
            def fetch(self, *, timeout_seconds): return FetchedResponse(...)
            def is_empty(self, payload): return False

    ``variants/WO-2R3/V26-conforming-hostile-adapter.patch`` is that object and it is
    ADMITTED, measured at
    ``tests/test_collector_admission.py::test_cd_bp_003_a_structurally_conforming_adapter_is_admitted_whatever_it_says``.
    **CARRIER, PARTIAL AND MEASURED:** it cannot compute a dial value — nothing under
    ``collectors/`` may import ``crash_detector.dials`` or ``crash_detector.engine``,
    asserted over the whole package by
    ``tests/test_collector_boundaries.py::test_no_collector_module_imports_the_dial_types_or_the_engine``
    — and its observation still faces the staleness window and the required-input rules in
    ``engine.evaluate``. **CARRIER FOR WHETHER A CONFORMING ADAPTER IS TELLING THE TRUTH:
    NOT PROVED TO BE CARRIED ANYWHERE.** Source trust is CD-D-005 and BLUEPRINT §5 and it is
    OWED, not held. No guard was built over it.
    **THE PROTOCOL CONFORMANCE CHECK ITSELF FAILS THE RENAME TEST** (CD-PL-F74):
    ``missing_adapter_members`` asks ``hasattr`` for five SPELLED names, so it measures a
    VOCABULARY and not a class. That is unavoidable at a boundary to a foreign system —
    structural conformance IS nominal — and it is recorded rather than presented as a
    closure.
    **CARRIER MEASURED for the extent of the limit itself:**
    ``tests/test_admission.py::test_cd_bp_003_is_exactly_four_parameters_and_every_one_names_its_residue``
    pins CD-BP-003 at FOUR parameters of ONE door and requires each to name the risk and to
    write CD-RULE-006's words; a fifth is a test failure, not a quiet widening.

 4  **A DECORATOR NAMED ``admits`` IS RECOGNISED BY ITS NAME IN THE SOURCE.** This check
    reads TEXT; it cannot know that the ``admits`` a module imported is
    ``crash_detector.admission.admits``. Executable example:
    ``variants/WO-2R3/V18-counterfeit-admits.patch`` defines a do-nothing ``admits`` in
    ``crash_detector/own_terms.py`` — a module this check does not scan for doors — and
    imports it into ``serving/witness_resolver.py``. MEASURED, RE-TAKEN AT INCREMENT 4 BY
    RUNNING IT (it read ``38 assertions`` here, which was the increment-2 figure and had
    not moved with the artefact — CD-ENG-WO2R3-F14): this check exits 0 with **54
    assertions** and PASS, and ``ASR3-F04``'s duck row then renders ``WITNESS AGREES``.
    (The counterfeit must be planted OUTSIDE a judgement-path package to work. Defined
    inside ``serving/witness_resolver.py`` it is itself a public undecorated callable in a
    judgement-path package and this check reports it — measured, and disclosed here rather
    than claimed as design.)
    **CARRIER MEASURED: THE RUNTIME.** The same patched tree runs 3 FAILED under
    ``PYTHONPATH=src python3 -B -m pytest tests -q``, because the plants call the real doors
    and observe the real refusals. A static reader alone cannot carry this and does not
    claim to. CD-RULE-006 exists because two declarations once each assumed the other
    covered the route.

 7  **THE TRAVERSAL'S RESIDUAL REACH. NEW AT WO-2R3 INCREMENT 6, AND IT REPLACES A LIMIT THAT
    WAS NEVER DECLARED AT ALL.** (Numbered 7 because 1..4 are this file's and 5..6 are the
    mechanism's, and this row's limits run as ONE sequence across the two headers.)

    **THE UNDECLARED LIMIT THAT WAS HERE UNTIL THIS INCREMENT.** ``_callables`` read
    ``tree.body`` — top-level ``def``s plus the DIRECT members of top-level public classes —
    and its sibling ``check_constructor_field_establishment.py`` did the same for classes.
    **BOTH GOVERNING INSTRUMENTS SHARED THIS BLIND SPOT AND NEITHER DECLARED IT.**
    ``CD-ASR-WO2R3-01``'s four arms against ONE undecorated public door in
    ``collectors/runner.py``: module-level ``def`` **exit 1**; method of a top-level class
    **exit 1**; method nested ONE level **exit 0**; function-local ``def`` bound in a module
    dict **exit 0** — and live, ``POLICY["decide"]`` accepted unestablished arguments.
    ``_callables`` now descends to ANY DEPTH. **Both zeros are ones.**

    **WHAT IS NOW CLOSED, MEASURED** by ``variants/WO-2R3/P-B-how-deep-can-a-type-hide.py``,
    which plants one public undecorated callable at nine placements: nested ONE class level ·
    nested TWO class levels · inside a PUBLIC function body · inside a PRIVATE function body ·
    conditionally defined under ``if True:``. All are now NAMED by this check.

    **THE RESIDUAL REACH LIMITS ARE EXACTLY TWO, and they are the same two the sibling
    instrument declares as its DECLARED LIMIT 5, because they are properties of reading source
    rather than of either check:**

    (i) **A CALLABLE WITH NO ``FunctionDef`` NODE IS INVISIBLE.** A ``lambda`` bound to a name,
        or a function built by ``exec``/``type``, leaves nothing to walk. Executable example —
        the probe's ``built by type(...) AT RUNTIME`` placement writes
        ``hidden_decide = lambda reading: reading`` into ``engine/config.py``; MEASURED at both
        SHAs, this check **does not name it**. **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.**

    (ii) **A MODULE OUTSIDE ``src/crash_detector/`` IS NEVER PARSED.** Measured: the probe's
        ``in a module OUTSIDE the scanned root`` placement is not named at either SHA.
        **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.**

    **AND A LIMIT THAT TURNED OUT NOT TO BE ONE:** a module that does not parse is an
    ``UNPARSEABLE`` violation, not a silence. Measured, and therefore NOT declared as a limit.

    **WHAT THE WIDENING FOUND IN EXISTING CODE, WHICH IS A FINDING AND NOT A LIMIT.**
    ``engine/evaluate.py``'s ``guarded`` — the closure inside the private decorator
    ``_absence_is_never_a_number`` that carries the CD-ASR-F03 post-condition — is a
    PUBLIC-NAMED callable in a RULE 1 package with ``*extra, **extra_by_name`` and no
    ``@admits``. **THIS CHECK NOW EXITS 1 ON IT.** It is NOT exempted here and it is NOT fixed:
    ``engine/evaluate.py`` is outside WO-2R3 increment 6's writable scope, adding an exemption
    for it would be the quiet widening this project keeps finding, and deciding whether it
    should be decorated, renamed ``_guarded`` or declared exempt is a DESIGN QUESTION FOR THE
    PROJECT OWNER. Raised as ``CD-ENG-WO2R3-02-F06``. Note also that ``functools.wraps`` gives
    it the runtime ``__name__`` ``_evaluate_dial``, so the static reading and the runtime name
    DISAGREE about whether it is public at all — which is part of what makes it a question
    rather than an oversight.
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
    read_text,
    resolve_root,
)

CHECK_ID = "CD-RT-002-DOORS-REQUIRE-THEIR-TYPES"

#: RULE 1. Packages every one of whose public callables is a door. DENY-BY-DEFAULT WITHIN:
#: no module inside these is opted out, so a new module is a subject the day it is written.
#: See DECLARED LIMIT 2 — this tuple itself is a vocabulary.
JUDGEMENT_PATH_PACKAGES = ("engine", "serving", "collectors")

#: DECLARED LIMIT 3. `collectors` JOINED RULE 1 AT WO-2R3 INCREMENT 3 (BP-AMENDMENT-0001
#: §D.3, A6). What remains open there is not a package gap: it is CD-BP-003, the four
#: `Protocol` parameters of `collect`, and it is DERIVED FROM THE ARTEFACT below rather than
#: listed here — this check reports the ESTABLISHED_HERE uses it actually finds under this
#: package, so the limit's extent cannot drift away from the code that carries it.
CD_BP_003_PACKAGE = "collectors"

#: The door BP-AMENDMENT-0001 §D.2 lists as A6. Named so CD-BP-003 is reported at exactly
#: its own extent — the four Protocol parameters of this door — and not widened to every
#: ESTABLISHED_HERE that happens to share the package.
A6_DOOR = "collect"

#: RULE 2. The types that ARE a dial's answer, a witness's answer, or the material one is
#: computed from. A public callable that says it returns one of these is a judgement-path
#: door wherever it is written.
JUDGEMENT_VALUE_TYPES = frozenset(
    {
        "DialSet",
        "Reading",
        "Value",
        "Degraded",
        "Unknown",
        "WitnessPanel",
        "Agrees",
        "Diverges",
        "Unavailable",
        "Shown",
        "NotShown",
        "DialPresentation",
        "ScoreComputation",
        "DialMagnitude",
        "DeclaredQuantity",
        "ConfigSnapshot",
        "DialSpec",
        "ModelSpec",
    }
)

#: The decorator that makes a callable a door. See DECLARED LIMIT 4.
ADMITS = "admits"

#: The exemption inside `admits` itself. Every use is PRINTED with its location.
ESTABLISHED_HERE = "ESTABLISHED_HERE"

_RECEIVER_NAMES = ("self", "cls")


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _decorator_names(node) -> list:
    """Every decorator on ``node``, as the bare name at its head."""
    names = []
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        names.append(getattr(target, "id", None) or getattr(target, "attr", None) or "")
    return names


def _admits_call(node):
    """The ``admits(...)`` call decorating ``node``, or ``None``."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            target = decorator.func
            if (getattr(target, "id", None) or getattr(target, "attr", None)) == ADMITS:
                return decorator
        elif (getattr(decorator, "id", None) or getattr(decorator, "attr", None)) == ADMITS:
            # `@admits` without a call is not a declaration at all.
            return decorator
    return None


def _signature_names(node, in_class_body: bool) -> "tuple[list, list]":
    """The parameter names to establish, and any variadic parameters.

    The receiver rule is READ FROM THE SAME PLACE the runtime reads it: the first parameter
    is dropped only when the callable is written inside a class body AND it is named
    ``self`` or ``cls``. A module-level function whose parameter is named ``cls`` keeps it.
    """
    args = node.args
    ordered = list(args.posonlyargs) + list(args.args)
    if in_class_body and ordered and ordered[0].arg in _RECEIVER_NAMES:
        ordered = ordered[1:]
    names = [a.arg for a in ordered] + [a.arg for a in args.kwonlyargs]
    variadic = []
    if args.vararg:
        variadic.append("*" + args.vararg.arg)
    if args.kwarg:
        variadic.append("**" + args.kwarg.arg)
    return names, variadic


def _returns_a_judgement_value(node) -> bool:
    """Does the return annotation NAME one of the judgement value types?

    Read as source text, because ``from __future__ import annotations`` makes every
    annotation in this codebase a string and half of them are written as strings anyway.
    """
    if node.returns is None:
        return False
    rendered = ast.unparse(node.returns)
    return any(
        name in _identifiers(rendered) for name in JUDGEMENT_VALUE_TYPES
    )


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


def _established_here_parameters(call) -> list:
    """Which parameters of an ``admits(...)`` call declare ``ESTABLISHED_HERE``."""
    found = []
    for keyword in call.keywords:
        if keyword.arg is None:
            continue
        for inner in ast.walk(keyword.value):
            head = inner.func if isinstance(inner, ast.Call) else inner
            if (getattr(head, "id", None) or getattr(head, "attr", None)) == ESTABLISHED_HERE:
                found.append(keyword.arg)
                break
    return found


def main() -> int:
    arguments = parse_root(
        CHECK_ID,
        "Every public entry point on a judgement path is an `admits` door, and its "
        "declaration matches its signature exactly (BP-AMENDMENT-0001 §D.1).",
    )
    root, code = resolve_root(CHECK_ID, arguments.root)
    if root is None:
        return code
    check = Check(check_id=CHECK_ID, root=root)

    package_root = root / "src" / "crash_detector"
    if not package_root.is_dir():
        return check.refuse(
            f"{package_root} is not a directory. --root must be the repository root of "
            "the tree under audit, not the package directory."
        )

    files = sorted(
        path
        for path in package_root.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    if not files:
        return check.refuse(f"no *.py found under {package_root}.")

    modules_by_rule_1 = 0
    subjects = 0
    decorated = 0
    exempt_private = 0
    exempt_property = 0
    exempt_protocol = 0
    static_or_class_methods = 0
    established_here: list = []
    reached_only_by_rule_2: list = []

    for path in files:
        source = read_text(check, path)
        if source is None:
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            check.violation(
                path,
                getattr(exc, "lineno", 0) or 0,
                "UNPARSEABLE",
                f"this file could not be parsed ({exc}). A file inside the scanned set that "
                "the check cannot read is a failure, not a file to pass over.",
            )
            continue

        relative = path.relative_to(package_root)
        in_judgement_package = (
            len(relative.parts) > 1 and relative.parts[0] in JUDGEMENT_PATH_PACKAGES
        )
        if in_judgement_package:
            modules_by_rule_1 += 1

        for node, in_class_body, class_node in _callables(tree):
            if not _is_public(node.name):
                exempt_private += 1
                continue
            decorators = _decorator_names(node)
            if "property" in decorators or any(d == "setter" for d in decorators):
                exempt_property += 1
                continue
            if in_class_body and _is_protocol(class_node):
                exempt_protocol += 1
                continue
            if "staticmethod" in decorators or "classmethod" in decorators:
                static_or_class_methods += 1

            by_rule_1 = in_judgement_package
            by_rule_2 = _returns_a_judgement_value(node)
            if not (by_rule_1 or by_rule_2):
                continue

            subjects += 1
            where = _where(class_node, node)
            if by_rule_2 and not by_rule_1:
                reached_only_by_rule_2.append(f"{relative}:{node.lineno} {where}")

            call = _admits_call(node)
            if call is None:
                check.asserted()
                check.violation(
                    path,
                    node.lineno,
                    "UNDECORATED_JUDGEMENT_PATH_DOOR",
                    f"{where} is a public entry point on a judgement path and it carries no "
                    f"@{ADMITS}(...). BP-AMENDMENT-0001 §D.1: every such door establishes "
                    "each of its arguments by exact type AT THE DOOR, derived from the "
                    "signature and not written into the body. A door whose establishment "
                    "lives in its body stops establishing the moment the body is rewritten, "
                    "which is CD-ASR-F03's shape exactly.",
                )
                continue
            if not isinstance(call, ast.Call):
                check.asserted()
                check.violation(
                    path,
                    node.lineno,
                    "ADMITS_NOT_CALLED",
                    f"{where} is decorated with a bare @{ADMITS} rather than "
                    f"@{ADMITS}(...). A decorator that declares nothing declares nothing.",
                )
                continue

            decorated += 1
            established_here.extend(
                f"{relative}:{node.lineno} {where}({parameter})"
                for parameter in _established_here_parameters(call)
            )

            names, variadic = _signature_names(node, in_class_body)
            check.asserted()
            if variadic:
                check.violation(
                    path,
                    node.lineno,
                    "OPEN_CHANNEL",
                    f"{where} declares {', '.join(variadic)}. A variadic parameter is the "
                    "general case of a parameter the declaration was not told about: "
                    "values arrive through it with no name to declare and no type to "
                    "require. The runtime refuses every call to such a door; it is a "
                    "violation here too so it is visible without running anything.",
                )
            if any(keyword.arg is None for keyword in call.keywords):
                check.violation(
                    path,
                    node.lineno,
                    "DECLARATION_UNREADABLE",
                    f"{where}'s @{ADMITS}(**...) is built from an expression this check "
                    "cannot read. A declaration a static reader cannot enumerate cannot be "
                    "checked against the signature, and an unreadable declaration is not a "
                    "declaration.",
                )
                continue

            declared = [keyword.arg for keyword in call.keywords]
            check.asserted()
            undeclared = [name for name in names if name not in declared]
            adrift = [name for name in declared if name not in names]
            if undeclared:
                check.violation(
                    path,
                    node.lineno,
                    "PARAMETER_NOT_DECLARED_TO_ADMITS",
                    f"{where} has parameter(s) {undeclared} in its signature that "
                    f"@{ADMITS}() was not told about. A new argument on a judgement-path "
                    "door arrives REFUSED, never unguarded (planted violation P7). The "
                    "runtime refuses every call to this door; this is the same fact read "
                    "without importing anything.",
                )
            if adrift:
                check.violation(
                    path,
                    node.lineno,
                    "DECLARATION_ADRIFT_FROM_SIGNATURE",
                    f"{where}'s @{ADMITS}() was told about {adrift}, which are not "
                    "parameters of it. A declaration that has come adrift from its "
                    "signature is guarding a door that is not there.",
                )

    check.note(
        f"RULE 1 (judgement-path packages, deny-by-default within): "
        f"{'/'.join(JUDGEMENT_PATH_PACKAGES)} — {modules_by_rule_1} module(s) read."
    )
    check.note(
        f"RULE 2 (return-type reach, anywhere under src/): reached "
        f"{len(reached_only_by_rule_2)} door(s) rule 1 did not."
    )
    for row in reached_only_by_rule_2:
        check.note(f"  by rule 2 only: {row}")
    check.note(f"SUBJECTS ENUMERATED: {subjects}. DECORATED: {decorated}.")
    check.note(
        f"EXEMPT: {exempt_private} non-public, {exempt_property} @property accessor(s), "
        f"{exempt_protocol} Protocol stub(s)."
    )
    check.note(
        f"staticmethod/classmethod in the subject set: {static_or_class_methods} "
        "(DECLARED LIMIT 2 in src/crash_detector/admission.py assumes this is 0)."
    )
    check.note(f"ESTABLISHED_HERE uses: {len(established_here)}.")
    for row in established_here:
        check.note(f"  ESTABLISHED_HERE: {row}")
    in_the_collectors = [
        row for row in established_here if row.startswith(f"{CD_BP_003_PACKAGE}/")
    ]
    # CD-BP-003 IS THE PROTOCOL BOUNDARY OF A6 AND NOTHING ELSE. The four parameters of
    # `collect` are separated from the establishment doors that share the package, because
    # a declared limit reported wider than it is, is as useless as one reported narrower:
    # a reader who cannot tell which of eight rows is the risk has not been told the risk.
    cd_bp_003 = [row for row in in_the_collectors if f" {A6_DOOR}(" in row]
    establishment_doors = [row for row in in_the_collectors if row not in cd_bp_003]
    check.note(
        f"DECLARED LIMIT 3 — CD-BP-003, THE PROTOCOL BOUNDARY THAT ADMITS: "
        f"{len(cd_bp_003)} parameter(s) of {A6_DOOR}() under {CD_BP_003_PACKAGE}/. "
        "BP-AMENDMENT-0001 §D.3 part 2: adapter, sink, ledger and validator keep their "
        "Protocols because the thing on the other side is genuinely foreign; every value "
        "they RETURN is established at the point of return. THIS IS A DOOR THAT ADMITS, NOT "
        "AN ABSENCE OF A DOOR, and it is BLUEPRINT §17's softest remaining surface — the "
        "Product Owner named it the fourth Assurance seat's first target. See the header "
        "for the executable example, which is an object that IS ADMITTED, and for what is "
        "NOT PROVED TO BE CARRIED ANYWHERE."
    )
    for row in cd_bp_003:
        check.note(f"  CD-BP-003 ADMITS: {row}")
    check.note(
        f"  (also under {CD_BP_003_PACKAGE}/, and NOT CD-BP-003: {len(establishment_doors)} "
        "ESTABLISHMENT DOOR parameter(s) — callables whose whole contract is to accept any "
        "object and establish or describe it, the same kind of use as own_model_id(value). "
        "Listed above with the rest; separated here so the risk is not reported wider than "
        "it is.)"
    )
    check.note(
        f"{CD_BP_003_PACKAGE}/ IS a judgement-path package under RULE 1 as of WO-2R3 "
        "increment 3. The increment-2 declaration that it was deferred BY SCOPE is "
        "DISCHARGED and is not restated."
    )
    check.note(
        "DECLARED LIMIT 1 — CONSTRUCTORS ARE STILL NOT SUBJECTS *OF THIS CHECK*, AND SINCE "
        "WO-2R3 INCREMENT 5 THAT IS NO LONGER AN UNCARRIED GAP. This check reads CALLABLES; "
        "a constructor is not one of its subjects, and V17 still leaves it exiting 0. THE "
        "CARRIER IS NAMED AND MEASURED (CD-RULE-006): "
        "crash_detector.establishment.establishes, enumerated and asserted by "
        "tools/register/check_constructor_field_establishment.py — RUN IT AND READ ITS OWN "
        "POPULATION LINE. THIS NOTE CITES NEITHER THAT CLASS'S DEFINITION NOR ITS COUNT, "
        "AND UNTIL PO-DECISIONS-0010 RULING 1 IT CITED BOTH: it read '...which measures the "
        "body-borne field-establishment class at 32 members'. That was a FOURTH place "
        "holding a copy of a sibling limit's definition and count with no rule pointing at "
        "it (CD-PL-F91) — CD-RULE-004's three places are each limit's OWN — and the ruling "
        "widened that class to BODY-BORNE OR ABSENT and moved the count, so the copy went "
        "stale exactly as an unpointed-at copy does. A COUNT READ FROM A SIBLING'S RUN IS A "
        "MEASUREMENT; A COUNT COPIED HERE IS A TRANSCRIPTION (CD-RULE-009). WHAT IS STILL "
        "NOT CARRIED is a CROSS-FIELD invariant, which no declared field list can state — "
        "that is residue (ii) of the constructor check's own DECLARED LIMIT 1, and the "
        "widening did not touch it. The superseded wording of this note is quoted in full "
        "in this file's header rather than deleted."
    )

    return check.done(
        f"{len(files)} file(s) under {package_root.relative_to(root)}; "
        f"{subjects} judgement-path door(s)"
    )


def _callables(tree):
    """Every function definition **AT ANY NESTING DEPTH**, with its enclosing class if any.

    **THIS IS WO-2R3 INCREMENT 6'S STRUCTURAL CHANGE TO THIS INSTRUMENT** (item B1,
    PO-DECISIONS-0011 ruling 2). It used to read ``tree.body`` — TOP LEVEL ONLY — plus the
    direct members of top-level public classes, and it did not declare that. Its sibling
    ``check_constructor_field_establishment.py`` had the same blind spot. **BOTH GOVERNING
    INSTRUMENTS SHARED IT AND NEITHER DECLARED IT.**

    ``CD-ASR-WO2R3-01`` measured the four arms against the same undecorated public door:

    ======================================  ==========
    where the door was defined              doors check
    ======================================  ==========
    module-level ``def``                    exit 1
    method of a TOP-LEVEL class             exit 1
    method nested one level (Outer.Inner)   **exit 0**
    function-local ``def``                  **exit 0** — and live, ``POLICY["decide"]``
                                            accepted unestablished arguments
    ======================================  ==========

    Both zeros are now ones.

    **THE ENCLOSING-CLASS RULE IS UNCHANGED IN SUBSTANCE AND WIDER IN REACH.** The old code
    skipped the members of a NON-PUBLIC top-level class. That is preserved, and it is now
    applied to the whole chain: a callable is skipped if ANY enclosing class is non-public,
    which is the same judgement — "nothing outside can name this" — asked of every level
    rather than only the first. **NO NEW EXEMPTION IS INTRODUCED HERE.** The three the check
    declares (non-public name, ``@property``, ``Protocol`` stub) are untouched and are still
    the only ones, and each is still counted in the output.

    ``in_class_body`` is TRUE only when the callable's IMMEDIATE parent is a class, because
    that is what it is used for — deciding whether a receiver parameter is skipped — and a
    function defined inside a METHOD has no receiver of its own.
    """
    def descend(node, class_chain, immediate_class):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if all(_is_public(name) for name in class_chain):
                    yield child, immediate_class is not None, immediate_class
                yield from descend(child, class_chain, None)
            elif isinstance(child, ast.ClassDef):
                yield from descend(child, class_chain + [child.name], child)
            else:
                yield from descend(child, class_chain, immediate_class)

    yield from descend(tree, [], None)


def _is_protocol(class_node) -> bool:
    if class_node is None:
        return False
    for base in class_node.bases:
        if (getattr(base, "id", None) or getattr(base, "attr", None)) == "Protocol":
            return True
    return False


def _where(class_node, node) -> str:
    return f"{class_node.name}.{node.name}" if class_node is not None else node.name


if __name__ == "__main__":
    raise SystemExit(main())
