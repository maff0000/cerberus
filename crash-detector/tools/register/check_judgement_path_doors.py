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
====================================================================================

 1  **CONSTRUCTORS ARE NOT SUBJECTS OF THIS CHECK, AND THAT IS A REAL GAP IN §D AS SCOPED.**
    ``ConfigSnapshot(...)``, ``DialSpec(...)``, ``ModelSpec(...)`` and ``PanelRow(...)`` are
    public entry points on the judgement path and they establish their fields IN
    ``__post_init__`` — that is, in a body. §D.1's own reasoning ("a rule that lives in a
    function body is rewritten by editing the function body") applies to them, and §D.2's
    table lists no constructor, so nothing in the amendment closes them. This check does not
    invent that scope. Executable example: extract the tree, delete the
    ``type(spec) is not DialSpec`` loop from ``ConfigSnapshot.__post_init__``, and this
    check still exits 0 — the demonstration is
    ``variants/WO-2R3/V17-constructor-body-escape.patch``.
    **CARRIER MEASURED, IN PART:** the frozen dataclasses re-establish every field, and the
    existing suite refuses a look-alike at each of them (``test_config_source_registry.py``,
    ``test_engine_model_registry.py``, ``test_witness_resolver.py``). That is a body-level
    guard measured to work TODAY, not a structure that survives an edit to the body. As a
    residue of §D.1's own rule: **NOT PROVED TO BE CARRIED ANYWHERE.** RAISED AS A FINDING
    to the Project Lead rather than closed here.

 2  **RULE 1's PACKAGE LIST IS A VOCABULARY.** ``engine`` and ``serving`` are spelled here.
    A judgement-path door written under a package name this file has never heard of is
    reached only by rule 2, and only if it annotates its return type. Executable example:
    ``variants/WO-2R3/V16-new-package-undecorated-door.patch`` adds
    ``src/crash_detector/judging/decide.py`` with a public, undecorated, unannotated
    ``decide(reading)`` — and this check still exits 0.
    **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** No other layer enumerates judgement-path
    packages. It is stated here so the fourth Assurance seat can hit it without having to
    find it first.

 3  **``collectors/`` IS NOT YET A JUDGEMENT-PATH PACKAGE HERE, BY SCOPE AND NOT BY
    OVERSIGHT.** A6 — ``collect(adapter, policy, sink, ledger, collector_run_id, clock,
    sleep, validator)`` — is BP-AMENDMENT-0001 §D.3 and WO-2R3 increment 3, and §D.3's
    closure is a different mechanism (``clock`` and ``sleep`` stop being caller callables;
    the protocol returns are established at the point of return). Adding ``collectors`` to
    rule 1 today would make this check fail on work that has not been dispatched yet. The
    check PRINTS the gap as a note at every run, so it cannot be forgotten silently.
    **CARRIER MEASURED:** the gap is asserted, not merely noted, by
    ``tests/test_judgement_path_doors.py::test_the_collector_gap_is_declared_and_still_open``,
    which fails the day ``collectors`` becomes a judgement-path package without this header
    and the execution contract being corrected with it.

 4  **A DECORATOR NAMED ``admits`` IS RECOGNISED BY ITS NAME IN THE SOURCE.** This check
    reads TEXT; it cannot know that the ``admits`` a module imported is
    ``crash_detector.admission.admits``. Executable example:
    ``variants/WO-2R3/V18-counterfeit-admits.patch`` defines a do-nothing ``admits`` in
    ``crash_detector/own_terms.py`` — a module this check does not scan for doors — and
    imports it into ``serving/witness_resolver.py``. MEASURED: this check exits 0 with 38
    assertions and PASS, and ``ASR3-F04``'s duck row then renders ``WITNESS AGREES``.
    (The counterfeit must be planted OUTSIDE a judgement-path package to work. Defined
    inside ``serving/witness_resolver.py`` it is itself a public undecorated callable in a
    judgement-path package and this check reports it — measured, and disclosed here rather
    than claimed as design.)
    **CARRIER MEASURED: THE RUNTIME.** The same patched tree runs 3 FAILED under
    ``PYTHONPATH=src python3 -B -m pytest tests -q``, because the plants call the real doors
    and observe the real refusals. A static reader alone cannot carry this and does not
    claim to. CD-RULE-006 exists because two declarations once each assumed the other
    covered the route.
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
JUDGEMENT_PATH_PACKAGES = ("engine", "serving")

#: DECLARED LIMIT 3. Named so the gap is printed at every run rather than inferred from an
#: absence, and asserted by a test so it cannot close silently.
DEFERRED_PACKAGES = {
    "collectors": (
        "A6, the collector boundary — BP-AMENDMENT-0001 §D.3 and WO-2R3 increment 3. Its "
        "closure is a different mechanism from admits and it has not been dispatched yet."
    ),
}

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
    for package, why in sorted(DEFERRED_PACKAGES.items()):
        check.note(f"DECLARED LIMIT 3 — {package}/ is NOT a judgement-path package here: {why}")
    check.note(
        "DECLARED LIMIT 1 — CONSTRUCTORS ARE NOT SUBJECTS. ConfigSnapshot(...), "
        "DialSpec(...), ModelSpec(...) and PanelRow(...) establish their fields in "
        "__post_init__, which is a BODY. §D.2 lists no constructor and this check does not "
        "invent that scope. See the header; raised as a finding, not closed."
    )

    return check.done(
        f"{len(files)} file(s) under {package_root.relative_to(root)}; "
        f"{subjects} judgement-path door(s)"
    )


def _callables(tree):
    """Every function definition, with whether it sits in a class body and which class."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node, False, None
        elif isinstance(node, ast.ClassDef):
            if not _is_public(node.name):
                continue
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield member, True, node


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
