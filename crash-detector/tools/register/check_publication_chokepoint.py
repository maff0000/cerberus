#!/usr/bin/env python3
"""CD-RT-001-PUBLICATION-CHOKEPOINT — there is ONE door to publication and it is not bypassable.

    python3 tools/register/check_publication_chokepoint.py --root <subject tree>

CRITERION: `CD-AC-001` — *"Missing **or stale** input never renders as calm."* — and `PID §3.2`,
which is CONSTITUTIONAL in the same words. Authority: `PO-DECISIONS-0031` **ruling 1(ii)**:

    "(ii) No bypass PATH to publication exists. The five-line early return is a code path that
     skips the gate. There is exactly ONE publication chokepoint and no route reaches
     publication without passing the freshness stage — enforced structurally, so an early
     return around it cannot exist (the 'no undecorated evaluator exists' principle, applied to
     the publication path)."

===========================================================================================
**WHY THIS INSTRUMENT EXISTS, AND WHY IT IS STRUCTURAL WHEN ITS SIBLING IS DELIBERATELY NOT.**

`CD-RT-001-STALE-DATA-NEVER-CALM` is BEHAVIOURAL on purpose, and its header says a structural
read is *"precisely what let this class of defect through repeatedly on this project"*. **THAT
REMAINS TRUE AND THAT ROW STAYS BEHAVIOURAL. THIS ROW IS NOT A LICENCE TO MAKE IT STRUCTURAL.**

This row's subject is different IN KIND. It is a claim about **WHICH CODE ROUTES EXIST**, and
**NO BEHAVIOURAL PROBE CAN ENUMERATE ROUTES THAT NOBODY CALLS.** A second function that writes
`publication.public_envelope` without passing the gate is invisible to every probe that drives
the gate, because the probe drives the gate — that is what makes it a *bypass*. A claim of the
form *"there is no other door"* is a claim about the source text and can only be read there.

So: the behavioural row proves WHAT THE GATE DOES with a document. This row proves THAT THE GATE
IS THE ONLY WAY IN, and that no path through it reaches a write without the freshness stage
having run. Neither is sufficient. `A312-F1` and `A313-F1` are both the shape *"the guarantee is
true and nothing watches the thing that could remove it"*, one layer apart.
===========================================================================================

WHAT IS ASSERTED — AND EVERY ONE OF THEM HAS AN ADMITTING DIRECTION
===========================================================================================

*** A STRUCTURAL CONTROL THAT ASSERTS "EXACTLY ONE CALLER" IS SATISFIED BY A TREE IN WHICH
NOTHING CALLS ANYTHING. *** That is this row's own vacuity direction, it is the direction this
project's history says gets missed, and it was recorded as the NAMED RISK of this increment by
the Project Lead before a line of this file was written. Every assertion below therefore fails
on the EMPTY tree as loudly as on the BYPASSED one, and `CD-CHOKE-000` exists to say so.

 CD-CHOKE-000  **THE SUBJECT SET IS NON-EMPTY.** At least one publication-surface write
               statement exists, at least one function executes one, the publication gate
               exists, and the gate reaches a freshness stage. **A tree with no writes, no
               gate or no stage FAILS THIS ROW.** It does not pass by having nothing to say.

 CD-CHOKE-001  **EXACTLY ONE FUNCTION IN `src/` EXECUTES A PUBLICATION-SURFACE WRITE.** Two is
               a second door; zero is `CD-CHOKE-000`.

 CD-CHOKE-002  **THE CHOKEPOINT JUDGES BEFORE IT WRITES, ONCE PER SURFACE, UNCONDITIONALLY.**
               Every publication write in the chokepoint is preceded, at the function's own top
               level and with no `if`/`for`/`while`/conditional-expression between it and the
               function body, by as many calls to the gate as `EnvelopeSurface` declares
               members. **A gate call moved inside a conditional is not a gate.**

 CD-CHOKE-003  **A REFUSAL RAISED BY THE GATE MAY NOT BE SWALLOWED ON THE WAY TO THE WRITE.**
               Where the chokepoint wraps its gate calls in `try:`, **AND WHERE THE GATE WRAPS
               ITS OWN STAGE CALLS IN `try:`**, every `except` handler must END IN A `raise`. A
               handler that logs and continues turns a refusal into a publication, which is the
               whole failure the gate exists to prevent, arriving through the error path
               instead of the happy path.

               *** ITS IMPLEMENTED SCOPE WAS NARROWER THAN ITS STATED SCOPE UNTIL `16G`.
               WIDENED, NOT REWRITTEN, AND THE GAP IS STATED AND NOT ERASED (`CD-RULE-004`,
               `PBG-CONT-003`). ***

               > **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"Where the
               > chokepoint wraps its gate calls in `try:`, every `except` handler must END IN
               > A `raise`."*

               **THAT SENTENCE NAMED THE CHOKEPOINT AND THE MESSAGE IT PRINTED SAID "ON THE
               JUDGING PATH", AND THOSE ARE NOT THE SAME SET.** The judging path continues into
               `refuse_unless_publishable`, which is where the stages actually raise. Arm `Z5`
               — `CD-ASR-F14-03`, raised by `CD-ASR-WO3-14` — wraps the freshness stage INSIDE
               THE GATE and re-raises only when a root property is not `"BYPASS"`. MEASURED at
               `c475b8e` by `CD-ENG-WO3-15` before this widening was written: the live gate
               ADMITTED a 1970-stamped calm dial on BOTH surfaces (`STALE-CALM ADMISSIONS = 2`,
               `MUST-ADMIT ROWS REFUSED = 0`) while this row returned `PASS — 11 assertions, 0
               violations`. **A SWALLOW ONE FRAME IN IS THE SAME PUBLICATION AS A SWALLOW ONE
               FRAME OUT.** EXECUTABLE:
               `plants/WO3-INC16G/Z5-THE-GATE-SWALLOWS-ITS-OWN-FRESHNESS-REFUSAL.patch`, and
               its control `Z5CTRL...` — the SAME `try` shape whose handler DOES re-raise —
               **which must stay `PASS`.**

 CD-CHOKE-004  **THE GATE REACHES THE FRESHNESS STAGE, UNCONDITIONALLY, AND NO `return`
               PRECEDES IT.** The freshness stage is identified BY THE REFUSAL TOKEN IT RAISES
               — the check reads the token's VALUE from the running application and then finds
               which module-level NAME carries it, so renaming the constant does not blind this
               check and does not silently narrow it. `plants/WO3-INC16D/D1` (the whole stage
               unreachable from the gate) is exactly this assertion's arm.

 CD-CHOKE-005  **NO PATH THROUGH THE FRESHNESS STAGE REACHES ITS END WITHOUT ENUMERATING THE
               CALM-BEARING NODES.** Two structural facts, both of which the two MEASURED fifth
               weakenings break:
                 (a) the stage's FIRST executable statement binds a name from an expression
                     that calls the SHARED DOCUMENT WALK — the walk another of the gate's own
                     stages already trusts — so the enumeration happens before anything else
                     can decide not to;
                 (b) EVERY `return` in the stage sits inside an `if` whose test asserts that
                     binding is EMPTY, so the only way out of the stage without judging is
                     *"there was nothing claiming calm"* — not its size, not anything else;
                 (c) the stage contains NO `continue` AND NO `break` AT ALL. **`return`,
                     `continue` and `break` are the three ways to leave a calm-bearing node
                     unjudged and this assertion covers all three.** (b) alone covered one of
                     them when this file was first frozen, and this seat's own post-freeze arm
                     `N8` walked through the gap — `CD-ENG-F16F-01`.
               **`W5G` (`if len(candidate["inputs_used"]) > 1: return`) AND `W5B2`
               (`if candidate["regime"] == calm: return`) BOTH INSERT A `return` GUARDED BY
               SOMETHING THAT IS NOT THAT BINDING, AND BOTH INSERT IT BEFORE (a).**

===========================================================================================
*** THE DECLARED SCOPE OF THIS GUARD — READ THIS BEFORE READING A CLEAN RUN ***
Said identically here, in `contracts/execution/CD-RT-001-PUBLICATION-CHOKEPOINT.md` and in
`required-tests.yaml` (`CD-RULE-004`, three places).
===========================================================================================

**THIS ROW IS ABOUT ROUTES IN `src/`, AND A ROUTE IS A THING THIS CHECK CAN SEE IN THE SOURCE.**
It reads Python. It does not run the publisher, it does not watch a database, and it cannot see
a write performed by a process this repository does not contain. What it proves is that **within
the application's own source tree** there is one function that writes a publication surface and
that function cannot reach its write without the gate and the freshness stage having run.

===========================================================================================
DECLARED LIMITS — THIS ROW'S OWN SEQUENCE, 1 TO 8
===========================================================================================
**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** These eight are
`CD-RT-001-PUBLICATION-CHOKEPOINT`'s and they are said identically in this header, in
`contracts/execution/CD-RT-001-PUBLICATION-CHOKEPOINT.md` and in `required-tests.yaml`.
**Quote the row id with the number.**

*** THIS HEADING READ `1 TO 7` / `These seven are` UNTIL `16G`, WHICH ADDED `DECLARED LIMIT 8`.
THE PRIOR WORDING IS QUOTED HERE RATHER THAN SIMPLY OVERWRITTEN. *** An index that moves because
the list grew is not the same act as a claim that was weakened — but `CD-ASR-F14-04` is in this
very increment BECAUSE a heading word was changed with no quote of what it had said, and this
seat is not going to commit that act while repairing it (`PBG-CONT-003`, non-waivable).

  1. **A PUBLICATION WRITE IS RECOGNISED AS AN SQL STATEMENT AGAINST THE `publication` SCHEMA,
     AND NOTHING ELSE.** A string containing `INSERT INTO publication.`, `UPDATE publication.`
     or `DELETE FROM publication.`, executed through a `.execute(...)` call. **A ROUTE THAT
     PUBLISHED BY WRITING A FILE, POSTING TO AN HTTP ENDPOINT, OR CALLING AN ORM THAT BUILDS
     ITS OWN SQL WOULD NOT BE SEEN BY THIS CHECK.** That is a real gap and it is stated rather
     than implied: today the application has no such route (MEASURED — `publication/publish.py`
     is the only writer and it executes literal SQL constants), and the day one is added this
     limit must be re-read before this row is quoted.

  2. **IT IS A STRUCTURAL READ AND IT IS NAME-COUPLED IN TWO PLACES**, deliberately and with
     the same trade `DECLARED LIMIT 3` of the behavioural sibling row prices: the gate is found
     by the name `refuse_unless_publishable` (which is EXPORTED — it is in that module's
     `__all__`), and `EnvelopeSurface` is imported to count the surfaces. **RENAMING EITHER
     MAKES THIS CHECK EXIT `3`, DELIBERATELY** — a check that cannot find its authentic target
     must fail and never wave through (`PBG-CI-002`). The freshness stage is NOT name-coupled:
     it is found by the refusal token's VALUE.

  3. **"UNCONDITIONAL" IS A LEXICAL PROPERTY, NOT A DATA-FLOW ONE.** A call is unconditional
     here when no `if`, `for`, `while`, conditional expression or boolean short-circuit stands
     between it and its function's body. **THIS IS A SOUND UNDER-APPROXIMATION IN THE
     DIRECTION THAT MATTERS** — it can only ever call a real gate call conditional and go RED,
     never call a conditional one unconditional and go green — but it means a legitimate
     refactor that puts the gate call inside a loop over surfaces WOULD FAIL THIS ROW and would
     need this limit re-read and this check deliberately rewritten. That cost is accepted: the
     alternative is a control that a `if not skip_validation:` defeats.

  4. **IT PROVES NOTHING ABOUT WHAT THE GATE DECIDES.** That is the behavioural sibling row
     `CD-RT-001-STALE-DATA-NEVER-CALM`, and this row would be perfectly satisfied by a
     chokepoint that calls a freshness stage whose body is `pass`. **THE TWO ROWS ARE A PAIR
     AND NEITHER IS A SOLE GUARD.** Quoting this one alone is half a report.

  5. **THE STAGE'S SHAPE IS ASSERTED, NOT ITS SEMANTICS.** `CD-CHOKE-005` requires the first
     statement to enumerate through the shared document walk and every `return` to be guarded
     by that enumeration. A stage that did that and then judged wrongly is this row's blind
     spot and the sibling row's subject.

  6. **IT READS THE TREE UNDER `--root` AND ONLY `src/`.** A publication route in `tools/`, in
     `tests/`, or in a script outside this repository is outside this check. `tests/` is
     excluded deliberately: a test that writes a publication row through a recording double is
     not a production route, and including it would make this row RED for the wrong reason.

  7. **IT IS A CLAIM AT A COMMIT, LIKE EVERY STRUCTURAL CLAIM.** `DECLARED LIMIT 6` of the
     sibling row said the only callers of the gate were `publication/publish.py` lines 276-277
     **as a measurement at a commit, which is a sentence that goes stale silently.** THIS ROW
     IS THAT SENTENCE TURNED INTO A CONTROL, so it cannot go stale without going RED — but the
     control itself is only as current as the last time the register ran.

  8. **`CD-CHOKE-003` NOW READS TWO FRAMES AND NOT ONE, AND BOTH READS ARE LEXICAL AND
     SILENT WHERE THERE IS NO `try`. NEW AT `16G`.** The gate half asserts over every `try`
     that lexically encloses one of `refuse_unless_publishable`'s calls to its OWN module's
     functions. Three things follow and all three are costs, stated rather than implied:
     **(a) IT IS VACUOUS BY CONSTRUCTION ON A GATE THAT WRAPS NOTHING** — at this tip the gate
     contains no `try` at all, so this pass contributes ZERO assertions to a clean run, and it
     therefore prints a NOTE carrying the count (including `0`) so a reader can see it ran.
     **A CONDITIONAL-SHAPE ASSERTION CANNOT BITE ON A TREE THAT DOES NOT HAVE THE SHAPE, AND
     THAT IS NOT THE SAME AS BEING A CONTROL.** (b) It is an OVER-approximation in the safe
     direction: a `try` around a gate call to a helper that never raises a refusal would be
     required to re-raise anyway, so a legitimate refactor that swallowed, say, a logging
     error inside the gate WOULD FAIL THIS ROW and would need this limit re-read and the check
     deliberately rewritten. That cost is accepted for the same reason `DECLARED LIMIT 3`
     accepts its own. **(c) IT IS A HANDLER-SHAPE READ AND NOT A CONTROL-FLOW PROOF.** It asks
     whether the handler's last statement is a `raise`; a handler that re-raises on one branch
     of an `if` and falls through on the other is caught (its last statement is the `if`), but
     a handler ending in a `raise` reached only conditionally at runtime is not something a
     lexical read can decide. **THE SWALLOW CLASS IS NARROWED, NOT CLOSED**, and the residual
     belongs where `PO-DECISIONS-0032` ruling 3 put it: a code-structure invariant is a
     heavier mechanism than a document instrument.

===========================================================================================
FOR THE AUDITOR
===========================================================================================
Do not read a clean run of this check as proof that nothing stale can be published. It proves
that, **in this tree's `src/`**, exactly one function executes a publication-surface write; that
it judges both surfaces through the gate, unconditionally, before it writes anything; that no
`except` handler on that path — **IN THE CHOKEPOINT AND, SINCE `16G`, IN THE GATE ITSELF; THE
GATE FRAME WAS UNREAD BEFORE THAT AND ARM `Z5` WALKED THROUGH IT** — can swallow a refusal; that
the gate reaches a freshness stage
with no `return` in front of it; and that the stage cannot reach its end without first
enumerating the calm-bearing nodes. **It says nothing whatever about whether the stage's verdict
is correct** — that is `CD-RT-001-STALE-DATA-NEVER-CALM`, and `DECLARED LIMIT 4` says so.

*** AND DO NOT READ IT AS PROOF THAT NO `return`-SHAPED BYPASS EXISTS ON THE PUBLICATION PATH.
`CD-CHOKE-005` WALKS THE FRESHNESS STAGE AND NOT THE FUNCTIONS THE STAGE DEPENDS ON.*** Arm `Z7`
puts a `return` at the top of the SHARED DOCUMENT WALK `_iter_nodes` — a `return`, on the
publication path, that this row does not see, MEASURED at `c475b8e` by `CD-ENG-WO3-15`. The
sibling row's `DECLARED LIMIT 9` used to say this row caught that class; **it does not, and that
sentence is superseded there.** EXECUTABLE:
`plants/WO3-INC16G/Z7-THE-SHARED-WALK-DECLINES-TO-YIELD-ONE-NODE.patch`.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, python_files, read_text, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-001-PUBLICATION-CHOKEPOINT"

#: The gate. **NAME-COUPLED, DECLARED LIMIT 2.** It is the module's exported entry point and the
#: only thing the application calls before it writes; a rename makes this check exit `3`.
GATE_FUNCTION = "refuse_unless_publishable"

#: The surface enumeration, imported so the number of judgements the chokepoint owes is DERIVED
#: from the application rather than typed as `2`.
SURFACE_ENUM = "EnvelopeSurface"

#: A statement that writes a publication surface. `DECLARED LIMIT 1`: SQL against the
#: `publication` schema, and nothing else. Case-insensitive because SQL is.
PUBLICATION_WRITE_RE = re.compile(
    r"\b(?:insert\s+into|update|delete\s+from)\s+publication\s*\.", re.IGNORECASE | re.DOTALL
)

#: The nodes that make a statement CONDITIONAL when one of them stands between it and the
#: function body. `DECLARED LIMIT 3` prices the under-approximation.
CONDITIONAL_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.BoolOp,
                     ast.comprehension, ast.ListComp, ast.SetComp, ast.DictComp,
                     ast.GeneratorExp)


def _functions(tree):
    """Every function definition in a module, with its qualified-enough name."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append(node)
    return found


def _module_string_constants(tree) -> dict:
    """Module-level ``NAME = "..."`` bindings, including tuple-built SQL joined by adjacency."""
    bindings = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        text = None
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            text = value.value
        elif isinstance(value, ast.JoinedStr):
            text = "".join(
                part.value for part in value.values
                if isinstance(part, ast.Constant) and isinstance(part.value, str)
            )
        if text is None:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                bindings[target.id] = text
    return bindings


def _adjacent_string(node) -> "str | None":
    """The text of a string constant, following implicit adjacency inside parentheses."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _top_level_index(function, target) -> "int | None":
    """Which statement of ``function.body`` contains ``target``. ``None`` if it does not."""
    for index, statement in enumerate(function.body):
        for node in ast.walk(statement):
            if node is target:
                return index
    return None


def _is_unconditional(function, target) -> bool:
    """Is ``target`` reached on every path into its enclosing top-level statement?

    ``DECLARED LIMIT 3``: lexical, and an UNDER-approximation. A ``try:`` body is
    unconditional — an exception propagates rather than skipping ahead — and that is why
    ``CD-CHOKE-003`` separately requires every handler on the path to re-raise.
    """
    parents = {}
    for node in ast.walk(function):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    cursor = target
    while cursor in parents:
        cursor = parents[cursor]
        if cursor is function:
            return True
        if isinstance(cursor, CONDITIONAL_NODES):
            return False
        if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return False
    return True


def _called_names(node) -> list:
    """Every callee NAME reachable inside ``node``: ``f(...)`` and ``a.f(...)`` alike."""
    names = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name):
            names.append(func.id)
        elif isinstance(func, ast.Attribute):
            names.append(func.attr)
    return names


def _calls(node) -> list:
    return [child for child in ast.walk(node) if isinstance(child, ast.Call)]


def _raised_token_names(function) -> set:
    """The NAMES passed as the first positional argument of every ``raise Something(NAME, ...)``."""
    names = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        exc = node.exc
        if isinstance(exc, ast.Call) and exc.args:
            first = exc.args[0]
            if isinstance(first, ast.Name):
                names.add(first.id)
            elif isinstance(first, ast.Constant) and isinstance(first.value, str):
                names.add(first.value)
    return names


def _is_emptiness_test(test, bound: set) -> bool:
    """Is ``test`` the test *"the enumeration produced nothing"* over one of ``bound``?

    ``not N`` · ``len(N) == 0`` · ``N == []`` · ``len(N) < 1`` and their spellings. **NOTHING
    ELSE**, and the narrowness is the point: the ONLY early exit a freshness stage is allowed is
    *"no node in this document claims calm"*. A `return` guarded by ``len(calm_nodes) > 1`` is
    guarded by the enumeration and is still a bypass — MEASURED as arm `N7`.
    """
    def names(node) -> set:
        return {sub.id for sub in ast.walk(node) if isinstance(sub, ast.Name)}

    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return bool(names(test.operand) & bound)
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        left, op, right = test.left, test.ops[0], test.comparators[0]
        if not (names(left) & bound):
            return False
        if isinstance(op, ast.Eq):
            return (isinstance(right, ast.Constant) and right.value == 0) or (
                isinstance(right, (ast.List, ast.Tuple, ast.Set)) and not right.elts)
        if isinstance(op, ast.Lt):
            return isinstance(right, ast.Constant) and right.value == 1
        if isinstance(op, ast.LtE):
            return isinstance(right, ast.Constant) and right.value == 0
    return False


def _handler_ends_in_raise(handler) -> bool:
    """Does this ``except`` handler end in a ``raise`` on the path that falls out of it?"""
    body = list(handler.body)
    while body:
        last = body[-1]
        if isinstance(last, ast.Raise):
            return True
        if isinstance(last, ast.Try):
            # A nested try whose own body ends in a raise, or whose handlers all do.
            if _handler_ends_in_raise(ast.ExceptHandler(body=last.body, type=None, name=None)):
                return True
            body = list(last.body)
            continue
        return False
    return False


def main(argv=None) -> int:
    parse_root  # referenced so a reader sees the shared command line is used below
    args = parse_root(CHECK_ID, __doc__.splitlines()[0])
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code
    check = Check(CHECK_ID, root)

    src = root / "src"
    if not (src / "crash_detector" / "__init__.py").is_file():
        return check.refuse(
            f"{src}/crash_detector/__init__.py does not exist, so there is no application in "
            "which to look for a publication route. This check will not report on a tree it "
            "could not find."
        )

    # ---- THE REFUSAL TOKEN, READ FROM THE RUNNING APPLICATION ------------------------ #
    # The freshness stage is identified BY THE TOKEN IT RAISES and never by its own name, so a
    # rename of the stage does not blind this check (DECLARED LIMIT 2). The token's VALUE comes
    # from the application; the NAME that carries it is then found in the source.
    sys.path.insert(0, str(src))
    for name in [
        module for module in sys.modules
        if module == "crash_detector" or module.startswith("crash_detector.")
    ]:
        del sys.modules[name]
    try:
        import crash_detector  # noqa: F401
        from crash_detector.publication.envelope_contract import (
            REFUSAL_STALE_CALM,
            EnvelopeSurface,
        )
    except Exception as exc:
        return check.refuse(
            f"the subject tree at {src} did not import: {type(exc).__name__}: {exc}. This "
            "check reads the freshness refusal token's VALUE from the application so it can "
            "find the stage without being coupled to the stage's name."
        )
    package_dir = pathlib.Path(crash_detector.__file__).resolve().parent
    check.note(f"imported crash_detector from: {package_dir / '__init__.py'}")
    check.note(f"python: {sys.version.split()[0]}")
    check.note(f"the freshness refusal token, read from the application: {REFUSAL_STALE_CALM!r}")
    surface_count = len(list(EnvelopeSurface))
    check.note(f"{SURFACE_ENUM} declares {surface_count} surface(s), so the chokepoint owes "
               f"{surface_count} judgement(s) before it writes")

    paths = python_files(root, ("src",))
    if not paths:
        return check.refuse(f"no Python files under {src}, so there is nothing to read.")

    trees = {}
    for path in paths:
        text = read_text(check, path)
        if text is None:
            continue
        try:
            trees[path] = ast.parse(text)
        except SyntaxError as exc:
            return check.refuse(
                f"{path} does not parse ({exc}). A tree this check cannot read is a tree it "
                "will not report clean on (PBG-CI-002)."
            )

    # ---- THE PUBLICATION WRITE SITES ------------------------------------------------- #
    write_statements = []      # (path, name-or-literal, text)
    write_calls = []           # (path, function, call)
    for path, tree in sorted(trees.items()):
        bindings = _module_string_constants(tree)
        for name, text in sorted(bindings.items()):
            if PUBLICATION_WRITE_RE.search(text):
                write_statements.append((path, name, text))
        for function in _functions(tree):
            for call in _calls(function):
                func = call.func
                if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
                    continue
                if not call.args:
                    continue
                first = call.args[0]
                text = _adjacent_string(first)
                if text is None and isinstance(first, ast.Name):
                    text = bindings.get(first.id)
                if text is None or not PUBLICATION_WRITE_RE.search(text):
                    continue
                write_calls.append((path, function, call))

    here = pathlib.Path(__file__)

    # ---- CD-CHOKE-000 — THE SUBJECT SET IS NON-EMPTY --------------------------------- #
    # *** THE ADMITTING ARM. A CONTROL THAT ASSERTS "EXACTLY ONE CALLER" IS SATISFIED BY A TREE
    # IN WHICH NOTHING CALLS ANYTHING, AND THIS IS WHERE THAT IS REFUSED. ***
    check.asserted()
    if not write_statements:
        check.violation(
            here, 0, "CD-CHOKE-000",
            "*** NO PUBLICATION-SURFACE WRITE STATEMENT EXISTS ANYWHERE IN src/. *** This row "
            "asserts that there is EXACTLY ONE door to publication, and a tree with NO door "
            "satisfies 'no bypass' vacuously while the product can no longer publish at all. "
            "That is the vacuity direction of a structural control and it is equally a "
            "violation of this row. If the publication layer has genuinely moved out of this "
            "repository, DECLARED LIMIT 1 must be rewritten before this row can be quoted.",
        )
    else:
        check.note(
            "publication-surface write statements found: "
            f"{[(str(p.relative_to(root)), n) for p, n, _t in write_statements]!r}"
        )
    check.asserted()
    if not write_calls:
        check.violation(
            here, 0, "CD-CHOKE-000",
            "*** NOTHING IN src/ EXECUTES A PUBLICATION-SURFACE WRITE. *** The statements may "
            "exist as constants, but no `.execute(...)` call carries one, so there is no route "
            "to publication for this row to guard and 'exactly one chokepoint' would be "
            "satisfied by a tree that publishes nothing.",
        )

    # ---- CD-CHOKE-001 — EXACTLY ONE CHOKEPOINT --------------------------------------- #
    writers = {}
    for path, function, call in write_calls:
        writers.setdefault((path, function.name, function), []).append(call)
    check.asserted()
    if len(writers) > 1:
        check.violation(
            here, 0, "CD-CHOKE-001",
            "*** MORE THAN ONE FUNCTION IN src/ EXECUTES A PUBLICATION-SURFACE WRITE: "
            f"{sorted((str(p.relative_to(root)), n) for p, n, _f in writers)!r}. *** There is "
            "exactly ONE publication chokepoint by design, and a second writer is a second "
            "door — it does not have to skip the gate deliberately to be a bypass, it only "
            "has to be somewhere the gate was not put. Every write to a publication surface "
            "goes through the one function that judges both envelopes first.",
        )
    elif len(writers) == 1:
        (chokepoint_path, chokepoint_name, chokepoint), chokepoint_calls = next(
            iter(writers.items())
        )
        check.note(
            f"the publication chokepoint: {chokepoint_path.relative_to(root)}::"
            f"{chokepoint_name} with {len(chokepoint_calls)} publication write(s)"
        )
    else:
        chokepoint = None
        chokepoint_path = None
        chokepoint_name = None
        chokepoint_calls = []

    # ---- CD-CHOKE-002 — JUDGE BEFORE YOU WRITE, ONCE PER SURFACE, UNCONDITIONALLY ---- #
    if len(writers) == 1:
        gate_calls = [
            call for call in _calls(chokepoint)
            if isinstance(call.func, ast.Name) and call.func.id == GATE_FUNCTION
        ]
        unconditional_gate_calls = [
            call for call in gate_calls if _is_unconditional(chokepoint, call)
        ]
        first_write_index = min(
            index for index in (
                _top_level_index(chokepoint, call) for call in chokepoint_calls
            ) if index is not None
        )
        judged_before = [
            call for call in unconditional_gate_calls
            if (_top_level_index(chokepoint, call) or -1) < first_write_index
        ]
        check.asserted()
        if len(judged_before) < surface_count:
            check.violation(
                here, 0, "CD-CHOKE-002",
                f"*** THE CHOKEPOINT {chokepoint_name} REACHES ITS FIRST PUBLICATION WRITE "
                f"AFTER ONLY {len(judged_before)} UNCONDITIONAL CALL(S) TO {GATE_FUNCTION}, "
                f"AND {SURFACE_ENUM} DECLARES {surface_count} SURFACE(S). *** It found "
                f"{len(gate_calls)} gate call(s) in total, of which "
                f"{len(unconditional_gate_calls)} are unconditional. A gate call that was "
                "removed, moved after the write, or wrapped in a condition is a write that can "
                "happen without a judgement — and BOTH validations must happen before EITHER "
                "write, which is the publication layer's own stated design.",
            )
        else:
            check.note(
                f"{chokepoint_name}: {len(judged_before)} unconditional {GATE_FUNCTION} "
                f"call(s) precede the first publication write at top-level statement "
                f"{first_write_index}"
            )

        # ---- CD-CHOKE-003 — A REFUSAL MAY NOT BE SWALLOWED --------------------------- #
        parents = {}
        for node in ast.walk(chokepoint):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        guarding_tries = []
        for call in judged_before:
            cursor = call
            while cursor in parents:
                cursor = parents[cursor]
                if isinstance(cursor, ast.Try) and cursor not in guarding_tries:
                    guarding_tries.append(cursor)
                if cursor is chokepoint:
                    break
        for guard in guarding_tries:
            for handler in guard.handlers:
                check.asserted()
                if _handler_ends_in_raise(handler):
                    continue
                check.violation(
                    here, 0, "CD-CHOKE-003",
                    f"*** AN `except` HANDLER ON THE CHOKEPOINT'S JUDGING PATH DOES NOT END IN "
                    f"A `raise` (line {handler.lineno} of "
                    f"{chokepoint_path.relative_to(root)}). *** A handler that catches the "
                    "gate's refusal and then falls through lets execution continue to the "
                    "write, so the refusal becomes a publication by way of the error path. "
                    "Publication REFUSES, it does not filter, and it does not log-and-carry-on.",
                )
        if guarding_tries:
            check.note(
                f"{chokepoint_name}: {sum(len(g.handlers) for g in guarding_tries)} except "
                "handler(s) on the judging path, each ending in a raise"
            )

    # ---- THE GATE ITSELF -------------------------------------------------------------- #
    gate_definitions = [
        (path, function)
        for path, tree in sorted(trees.items())
        for function in _functions(tree)
        if function.name == GATE_FUNCTION
    ]
    if len(gate_definitions) != 1:
        return check.refuse(
            f"src/ declares {len(gate_definitions)} function(s) named {GATE_FUNCTION!r} and "
            "this check needs exactly one to read. DECLARED LIMIT 2: the gate is name-coupled "
            "and a rename makes this check exit 3 rather than quietly measure nothing "
            "(PBG-CI-002)."
        )
    gate_path, gate = gate_definitions[0]

    # The NAME the module binds the freshness refusal token to, derived from its VALUE.
    gate_tree = trees[gate_path]
    token_names = {
        target.id
        for node in gate_tree.body if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        and isinstance(node.value, ast.Constant)
        and node.value.value == REFUSAL_STALE_CALM
    }
    if not token_names:
        return check.refuse(
            f"no module-level constant in {gate_path.relative_to(root)} carries the freshness "
            f"refusal token {REFUSAL_STALE_CALM!r}, so this check cannot identify the "
            "freshness stage without being coupled to its name. It exits 3 rather than fall "
            "back to a name (PBG-CI-002)."
        )
    check.note(f"the freshness refusal token is carried by module name(s) {sorted(token_names)!r}")

    module_functions = {function.name: function for function in _functions(gate_tree)}
    stage_calls = [
        call for call in _calls(gate)
        if isinstance(call.func, ast.Name) and call.func.id in module_functions
    ]
    freshness_stages = [
        call for call in stage_calls
        if _raised_token_names(module_functions[call.func.id]) & token_names
    ]

    # ---- CD-CHOKE-003 (continued) — THE GATE'S OWN HANDLERS ------------------------- #
    # *** THIS PASS EXISTS BECAUSE THIS ASSERTION'S STATED SCOPE WAS WIDER THAN ITS
    # IMPLEMENTED SCOPE, AND AN ARM WALKED THROUGH THE GAP. *** `CD-CHOKE-003` says "no
    # `except` handler ON THE JUDGING PATH may swallow the refusal". Until `16G` it read
    # ONLY the chokepoint's handlers. **THE JUDGING PATH DOES NOT END AT THE CHOKEPOINT —
    # IT CONTINUES INTO THE GATE, WHICH IS WHERE THE STAGES ACTUALLY RAISE.** Arm `Z5`
    # (`CD-ASR-F14-03`, `CD-ASR-WO3-14`) wraps the freshness stage IN THE GATE and re-raises
    # only when a root property is not `"BYPASS"`: MEASURED at `c475b8e`, the live gate
    # ADMITS a 1970-stamped calm dial on BOTH surfaces while this row returned
    # `PASS — 11 assertions, 0 violations`. A swallow one frame in is the same publication
    # as a swallow one frame out, and it was invisible to the row that names it.
    #
    # It reads the `try` statements that lexically enclose the gate's OWN calls to its OWN
    # module's functions — the four `_refuse_*` stages, derived and never named. It is the
    # same rule as the chokepoint half, applied to the other half of the same path.
    gate_parents = {}
    for node in ast.walk(gate):
        for child in ast.iter_child_nodes(node):
            gate_parents[child] = node
    gate_guarding_tries = []
    for call in stage_calls:
        cursor = call
        while cursor in gate_parents:
            cursor = gate_parents[cursor]
            if isinstance(cursor, ast.Try) and cursor not in gate_guarding_tries:
                gate_guarding_tries.append(cursor)
            if cursor is gate:
                break
    for guard in gate_guarding_tries:
        for handler in guard.handlers:
            check.asserted()
            if _handler_ends_in_raise(handler):
                continue
            check.violation(
                here, 0, "CD-CHOKE-003",
                f"*** AN `except` HANDLER INSIDE {GATE_FUNCTION} ITSELF DOES NOT END IN A "
                f"`raise` (line {handler.lineno} of {gate_path.relative_to(root)}). *** The "
                "gate's stages REFUSE BY RAISING and the gate means ADMITTED by returning "
                "None, so a handler here that catches a refusal and falls through converts "
                "that refusal into an admission WITHOUT the chokepoint ever seeing an "
                "exception. Every assertion this row makes about the chokepoint's own "
                "handlers is true and irrelevant on such a tree: the refusal died one frame "
                "in. This is arm `Z5`. A handler on the judging path re-raises, or the path "
                "is not a judging path.",
            )
    # *** PRINTED EVEN WHEN IT IS ZERO. *** On the clean tree the gate wraps nothing, so this
    # pass adds NO assertions, and a reader of a clean run would otherwise have no way to tell
    # whether it ran at all — the `CD-ENG-F16F-03` complaint, answered in advance rather than
    # left to be found.
    check.note(
        f"{GATE_FUNCTION}: {len(gate_guarding_tries)} `try` statement(s) enclose its "
        f"{len(stage_calls)} stage call(s), carrying "
        f"{sum(len(g.handlers) for g in gate_guarding_tries)} except handler(s) — "
        "CD-CHOKE-003 read the GATE'S OWN handlers, not only the chokepoint's"
    )

    # ---- CD-CHOKE-000 (continued) + CD-CHOKE-004 ------------------------------------- #
    check.asserted()
    if not freshness_stages:
        check.violation(
            here, 0, "CD-CHOKE-000",
            f"*** {GATE_FUNCTION} CALLS NOTHING THAT RAISES {REFUSAL_STALE_CALM!r}. *** The "
            "gate no longer reaches a freshness stage at all, so there is no stage for this "
            "row to prove is unbypassable and the behavioural sibling row's whole subject has "
            "left the publication path. This is `plants/WO3-INC16D/D1`'s exact shape.",
        )
    else:
        unconditional_stages = [
            call for call in freshness_stages if _is_unconditional(gate, call)
        ]
        check.asserted()
        if not unconditional_stages:
            check.violation(
                here, 0, "CD-CHOKE-004",
                f"*** EVERY CALL FROM {GATE_FUNCTION} TO THE FRESHNESS STAGE IS CONDITIONAL. "
                "*** A stage that runs only when some other condition holds is a stage that "
                "does not run, on the documents where the condition does not hold — and those "
                "are exactly the documents a weakening would choose.",
            )
        else:
            stage_index = min(
                index for index in (
                    _top_level_index(gate, call) for call in unconditional_stages
                ) if index is not None
            )
            early_returns = [
                node for node in ast.walk(gate)
                if isinstance(node, ast.Return)
                and (_top_level_index(gate, node) or 0) < stage_index
            ]
            check.asserted()
            if early_returns:
                check.violation(
                    here, 0, "CD-CHOKE-004",
                    f"*** {GATE_FUNCTION} CONTAINS {len(early_returns)} `return` STATEMENT(S) "
                    f"BEFORE IT CALLS THE FRESHNESS STAGE (lines "
                    f"{sorted(node.lineno for node in early_returns)}). *** The gate returns "
                    "`None` to mean ADMITTED, so a `return` in front of the freshness stage is "
                    "an admission that skipped it. The gate reaches its end by falling off it "
                    "or by raising, and never by returning early.",
                )
            else:
                check.note(
                    f"{GATE_FUNCTION}: the freshness stage is called unconditionally at "
                    f"top-level statement {stage_index} with no `return` before it"
                )

            # ---- CD-CHOKE-005 — NO PATH REACHES THE STAGE'S END UNJUDGED ------------- #
            for call in unconditional_stages:
                stage = module_functions[call.func.id]
                body = [
                    node for node in stage.body
                    if not (isinstance(node, ast.Expr)
                            and isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str))
                ]
                check.asserted()
                if not body:
                    check.violation(
                        here, 0, "CD-CHOKE-005",
                        f"the freshness stage {stage.name} has an EMPTY body. A stage that "
                        "does nothing satisfies every structural assertion about being called.",
                    )
                    continue

                # The SHARED DOCUMENT WALK: a function of this module that at least two of the
                # gate's own stages call. Derived, never named.
                walk_counts = {}
                for other in stage_calls:
                    other_function = module_functions[other.func.id]
                    for name in set(_called_names(other_function)):
                        if name in module_functions:
                            walk_counts[name] = walk_counts.get(name, 0) + 1
                shared_walks = {name for name, count in walk_counts.items() if count >= 2}

                first = body[0]
                first_calls = set(_called_names(first))
                bound = {
                    target.id for target in getattr(first, "targets", [])
                    if isinstance(target, ast.Name)
                }
                check.asserted()
                if not (isinstance(first, ast.Assign) and bound
                        and (first_calls & shared_walks)):
                    check.violation(
                        here, 0, "CD-CHOKE-005",
                        f"*** THE FIRST EXECUTABLE STATEMENT OF THE FRESHNESS STAGE "
                        f"{stage.name} (line {first.lineno}) DOES NOT ENUMERATE THE DOCUMENT "
                        f"THROUGH THE SHARED WALK. *** It calls {sorted(first_calls)!r}; the "
                        f"walk(s) shared by two or more of the gate's stages are "
                        f"{sorted(shared_walks)!r}. **THIS IS THE ASSERTION THE TWO MEASURED "
                        "FIFTH WEAKENINGS BREAK:** both `W5G` and `W5B2` insert a five-line "
                        "early return AT THE TOP OF THIS FUNCTION, in front of the "
                        "enumeration, and both leave the live gate admitting a 1970-stamped "
                        "calm dial on both surfaces. The enumeration of the calm-bearing nodes "
                        "happens FIRST, so nothing can decide not to do it.",
                    )
                    continue
                check.note(
                    f"{stage.name}: enumerates the document at line {first.lineno} through "
                    f"{sorted(first_calls & shared_walks)!r}, binding {sorted(bound)!r}"
                )

                parents = {}
                for parent in ast.walk(stage):
                    for child in ast.iter_child_nodes(parent):
                        parents[child] = parent

                # *** THE THREE WAYS TO LEAVE A CALM-BEARING NODE UNJUDGED ARE `return`,
                # `continue` AND `break`, AND THIS ASSERTION COVERS ALL THREE. ***
                # It covered only `return` when this file was first frozen (`6491b64`), and
                # this seat's own post-freeze arm `N8` — a `continue` keyed on a root string
                # OUTSIDE the behavioural row's vocabulary — ESCAPED BOTH ROWS AND PUBLISHED A
                # 1970-STAMPED CALM DIAL ON BOTH SURFACES. Raised against this seat's own work
                # as `CD-ENG-F16F-01` and recorded rather than quietly corrected.
                for node in ast.walk(stage):
                    if not isinstance(node, (ast.Return, ast.Continue, ast.Break)):
                        continue
                    check.asserted()
                    guards = []
                    cursor = node
                    while cursor in parents:
                        cursor = parents[cursor]
                        if isinstance(cursor, ast.If):
                            guards.append(cursor.test)
                        if cursor is stage:
                            break
                    if isinstance(node, ast.Return) and any(
                        _is_emptiness_test(test, bound) for test in guards
                    ):
                        continue
                    rendered = sorted(
                        {sub.id for test in guards for sub in ast.walk(test)
                         if isinstance(sub, ast.Name)}
                    )
                    kind = type(node).__name__.lower()
                    check.violation(
                        here, 0, "CD-CHOKE-005",
                        f"*** THE FRESHNESS STAGE {stage.name} CAN `{kind}` AT LINE "
                        f"{node.lineno} AND LEAVE A CALM-BEARING NODE UNJUDGED. *** The `if`s "
                        f"guarding it name {rendered!r}, and the enumeration this stage begins "
                        f"with binds {sorted(bound)!r}. **THE ONLY EARLY EXIT THIS STAGE MAY "
                        "HAVE IS A `return` GUARDED BY THE ENUMERATION BEING EMPTY — 'nothing "
                        "in this document claims calm'.** A `return` guarded by anything else, "
                        "or by the enumeration's SIZE rather than its emptiness, and ANY "
                        "`continue` or `break` at all, is a skip: the node it skips is a node "
                        "that claimed calm and was never asked to prove it. The number of "
                        "inputs the envelope used, the regime it declares, a configuration id, "
                        "the node's own state or its contributions — a five-line bypass keyed "
                        "on any of them leaves every other register line diff-identical. That "
                        "is `A313-F1`, MEASURED, twice, and `CD-ENG-F16F-01`, measured once "
                        "more against this very check.",
                    )

    return check.done(
        f"{len(paths)} Python file(s) under src/, {len(write_statements)} publication-surface "
        f"write statement(s), {len(write_calls)} execution site(s) in {len(writers)} "
        f"function(s), the gate {GATE_FUNCTION} and the freshness stage it reaches, identified "
        f"by the refusal token {REFUSAL_STALE_CALM!r} read from the running application"
    )


if __name__ == "__main__":
    raise SystemExit(main())
