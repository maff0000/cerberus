#!/usr/bin/env python3
"""CD-RT-012-NO-EXECUTION-INTERFACE — the codebase contains no way to place a trade.

    python3 tools/register/check_no_execution_interface.py --root <subject tree>

CRITERION: CD-AC-012, "no execution pathway exists — a test asserts the codebase contains
no broker/order/execution interface; advisory-only is STRUCTURAL, not policy" (PID §6).
PID §2 is the reason: this product tells Matt what is happening; it never acts. A policy
that says "we do not trade" is a sentence somebody can change in an afternoon. A codebase
with no order interface in it is a different kind of promise.

WHAT IT SCANS
--------------
Every Python module and every SQL migration in the application tree — ``src/``, ``db/``,
``deploy/``, ``tests/`` and ``tools/`` — and inside each, THREE INDEPENDENT LAYERS. Any one
of them failing is a violation; none of them is load-bearing alone.

  L1  NAMES. Functions, classes, parameters, variables, attributes, keyword arguments,
      imports, SQL identifiers, and string literals shaped like an endpoint. Judged by
      composition, never by a bare word — see ``_broker_vocabulary.judge_identifier``.

  L2  SIGNATURE SHAPE (added closing CD-PL-F32). The FIELD SET of every callable and every
      class, judged as an order ticket: an instrument together with a quantity and a side,
      a price or order type, or a destination that is a venue, broker or exchange. This
      layer never reads the callable's name for its two main rules, so renaming
      ``place_order`` to ``f`` does not evade it.

  L3  PROSE (added closing CD-PL-F32). Docstrings, comments, string literals and SQL
      comments, read for a direct-object construction — a verb of transmission applied to
      a noun naming a tradeable instruction. A thing whose own documentation says it
      routes orders to a broker is an execution interface by the product's definition,
      whatever it is called.

WHY L2 AND L3 EXIST. The first cut of this check had L1 only, and
``submit_instruction(symbol, qty, side)`` passed it — identically with and without the
docstring "Route an order to the broker for execution", because prose was not read at all
(CD-PL-F32, raised by the Project Lead's independent probe). The instance was not the
finding; the finding was that ONE question was being asked of every construct, and an
order-entry path is a shape rather than a word. The escape is now caught twice over, by L2
with its docstring deleted and by L3 with every identifier renamed.

L3's original exclusion is preserved as a CONSTRAINT rather than discarded. A docstring
saying "this system places no orders" is not an order interface, and a check whose output
is mostly the project's own charter is a check nobody reads. So L3 is a tight direct-object
pattern, and any sentence carrying a negation ("no", "never", "refuses", "forbidden") or a
hypothetical framing ("if", "would", "planted", "variant", "guard") is suppressed. That
suppression is a deliberate false-negative trade: prose is the third net, not the only one.

TWO PATHS ARE EXCLUDED, each with its reason:
  * ``tools/register/_broker_vocabulary.py`` and this script — the GUARD must name what it
    forbids in order to forbid it. Excluding the guard's own vocabulary is not a hole: the
    vocabulary is data, not an interface, and every other file in ``tools/`` IS scanned.
  * nothing else.

HOW IT JUDGES — BUILT FOR THE CLASS. See ``_broker_vocabulary.py``. Identifiers are
tokenised (``placeOrder``, ``place_order`` and ``PLACE_ORDER`` all reduce to
``{place, order}``) and judged by COMPOSITION — an execution verb applied to an execution
object, an execution object wearing an interface suffix, an execution object carrying an
order's data model, or a standalone brokerage noun. That is what makes ``submitTrade``,
``OrderGateway``, ``close_position`` and ``order_id`` all fail alongside the ``place_order``
somebody plants, while ``test_callbacks_run_in_registration_order`` and
``the_filename_pattern_orders_lexically`` — which are English — do not.

Imports are additionally matched against the broker-SDK module denylist, so
``import ib_insync`` fails even though its name contains no execution word at all.

DECLARED LIMIT — WHAT THIS CHECK DOES NOT CATCH
------------------------------------------------
Required by CD-D-014 and bounded by CD-D-015. This is the guard stating its own scope. It
is written as fact, not as apology: everything below is a boundary that was measured, and
a reader who takes a clean run here as proof that no execution pathway exists has misread
the check. The boundary is stated HERE, in the check itself and in its register entry, so
that an auditor sees it without having to discover it.

WHAT IT DOES CATCH, by CLASS and not by instance: an order-entry callable or class under
ANY name, recognised by its field set (L2, which never reads the name); a transmission
verb applied to a tradeable noun in any spelling, casing or word order (L1); an execution
object wearing an interface suffix or carrying an order's data model; a standalone
brokerage noun; a broker-SDK import; an execution endpoint string literal; an execution
identifier in a SQL migration; and plain-English documentation, in five grammars —
direct object, passive, nominalised, trade-lifecycle act with a party, and intransitive
motion toward a destination — saying the code sends instructions to something that trades.

WHAT IT DOES NOT CATCH. Six boundaries, each with the reason it exists:

  1  DELIBERATE EUPHEMISM. A static reader of natural language cannot have a terminating
     condition against an author choosing words to avoid it, and this check does not
     pretend to one. An act named in vocabulary this project's word lists do not hold — an
     invented internal codename, another market's term of art, a spelling nobody
     anticipated — passes L1 and L3. This is not speculative: two rounds of independent
     probing each found a fresh escape of exactly this kind (CD-PL-F32, CD-PL-F35, and
     the residual CD-PL-F38). Each was closed. The fact that each round found ANOTHER is
     the evidence for this limit, and CD-D-015 ends the chase here rather than pretending
     the next round would be the last.

  2  CODE NAMED TO HIDE BEHIND THE ``work_order`` SEQUENCE-SENSE SUPPRESSION. So the check
     does not fail on this project's own daily vocabulary, L1 suppresses the token
     ``order`` in its SEQUENCE sense — when the word in front of it is one of the
     thirty-one sequence modifiers in ``ORDER_SEQUENCE_MODIFIERS`` (``work_order``,
     ``sort_order``, ``registration_order``, ``in order to``). An execution pathway named
     ``work_order_router`` or ``sort_order_gateway`` PRECISELY to sit inside that
     suppression is therefore invisible to L1. It is not invisible to L2, which reads no
     names at all — ``def work_order(symbol, qty, side)`` still fails on its field set —
     so what genuinely escapes is a pathway BOTH named to exploit the suppression AND
     shaped to avoid looking like an order ticket. That residue is accepted deliberately:
     the alternative was a guard that cries wolf on ``apply_work_order``, and a guard that
     cries wolf is a guard somebody eventually weakens to obtain a pass.

  3  ANY SENTENCE L3 SUPPRESSES — AND THE SUPPRESSION LIST IS WIDE. L3 does not read a
     sentence at all if it carries any of 46 negation words or any of 25 hypothetical
     words. Those lists are broader than the obvious cases and this matters: besides
     ``no``, ``never``, ``forbidden``, ``if`` and ``would``, they include ``must``,
     ``free``, ``advisory``, ``absence``, ``zero``, ``say``, ``check``, ``example``,
     ``criterion`` and ``were``. MEASURED CONSEQUENCE: the docstring "The engine must send
     each instruction to the broker" is NOT read by L3, because of ``must`` alone. A
     sentence needs no cunning to be suppressed, only an ordinary modal verb. The trade was
     taken because this project's own charter says repeatedly that it places no orders, and
     a check whose output is mostly its own charter is a check nobody reads. It is
     affordable only because L1 and L2 never read prose: the interface in that example is
     still caught if its name or its field set gives it away, and prose is the third net.

  4  A MOTION CHAIN LONGER THAN EIGHT WORDS. L3's intransitive-motion grammar scans at most
     eight consecutive particles, articles and adjectives between the verb of motion and
     the destination noun (CD-PL-F38 widened this from four; CD-D-015 permits no further
     widening). Prose stacking more than eight escapes that grammar. Declared, not fixed.

  5  ANYTHING THAT IS NOT PYTHON OR SQL UNDER THE FIVE SCANNED ROOTS. The scan reads only
     files with a ``.py`` or ``.sql`` suffix under ``src/``, ``db/``, ``deploy/``,
     ``tests/`` and ``tools/``. It does not read YAML, JSON, TOML, shell, Markdown,
     notebooks, templates, compiled artefacts, vendored or installed dependencies,
     container images, or ANY file outside those five directories. An order interface
     delivered as a shell script, a compose command, a CI job or a dependency's own code is
     outside this check entirely.

  6  RUNTIME. This is a static read of source text at one commit. It says nothing about
     what the process does when it runs, nor about code generated, configured or fetched at
     run time.

WHY THAT IS ACCEPTABLE, AND WHAT CARRIES THE REST. CD-BP-001 — risk-accepted by the Product
Owner at Blueprint acceptance — records that the AST register checks are NEVER A SOLE
GUARD. This check is ONE OF THREE refusals on CD-AC-012, standing behind a structural
fourth:

  * this check, the source scan — names, shapes and documented intent;
  * CD-RT-012-LOCKFILE-DENYLIST — a broker SDK in any dependency manifest, which no
    euphemism in OUR source can evade, because the SDK is named by its publisher and not
    by us;
  * CD-RT-012-EGRESS-NO-BROKER — a broker host in any egress allowlist, and ANY egress at
    all granted to cd-engine, cd-public, cd-private or cd-store;
  * and the network posture itself (BLUEPRINT §2, §13): the engine and both surfaces sit on
    internal networks with nowhere to send an order. A perfectly euphemised execution
    pathway inside cd-engine still has no route to a venue.

WHAT A READER SHOULD DO INSTEAD OF TRUSTING THIS ALONE. Read a clean run here as evidence
about NAMES, SHAPES and DOCUMENTED INTENT at one commit — not as proof of the proposition.
For the proposition itself, weigh the egress posture first: of the four, it is the only one
that constrains what the software CAN DO rather than what it says or how it is written. An
auditor planting a CD-AC-012 variant that lands beyond this boundary should raise a finding
against THIS DECLARATION — was the limit honestly drawn? — rather than an automatic RED
against the guard (CD-D-014). That is a fair test of a guard that says what it is, and it
is available only because the limit was written down first.

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import ast
import io
import pathlib
import re
import sys
import tokenize

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _broker_vocabulary import (  # noqa: E402
    BROKER_SDK_MODULES,
    PROSE_HYPOTHETICALS,
    PROSE_NEGATIONS,
    STRONG_NOUNS,
    TRADEABLE_NOUNS,
    judge_identifier,
    judge_prose,
    judge_signature,
    tokens,
)
from _support import Check, parse_root, read_text, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-012-NO-EXECUTION-INTERFACE"

SCAN_DIRS = ("src", "db", "deploy", "tests", "tools")

EXCLUDED = (
    "tools/register/_broker_vocabulary.py",
    "tools/register/check_no_execution_interface.py",
    "tools/register/check_lockfile_denylist.py",
    "tools/register/check_egress_no_broker.py",
)

#: A string literal that looks like an endpoint rather than a sentence.
ENDPOINT = re.compile(r"^(?:[a-z]+://|/)|/[A-Za-z0-9_.\-]+/")

SQL_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SQL_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)
SQL_STRING = re.compile(r"'(?:[^']|'')*'", re.DOTALL)
SQL_DOLLAR = re.compile(r"\$\$.*?\$\$", re.DOTALL)


def _excluded(relative: str) -> bool:
    return relative in EXCLUDED


def _parameters(node) -> list:
    """Every parameter name of a callable, in declaration order."""
    args = node.args
    names = [arg.arg for arg in list(getattr(args, "posonlyargs", [])) + list(args.args)]
    if args.vararg:
        names.append(args.vararg.arg)
    names.extend(arg.arg for arg in args.kwonlyargs)
    if args.kwarg:
        names.append(args.kwarg.arg)
    return names


def _class_fields(node: ast.ClassDef) -> list:
    """The attribute names a class declares in its own body — its data model."""
    names: list = []
    for statement in node.body:
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            names.append(statement.target.id)
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
    return names


def _prose(check: Check, path: pathlib.Path, line: int, where: str, text: str) -> None:
    """L3. Read a piece of English for a statement that this code routes orders."""
    if not text or len(text) > 20000:
        return
    check.asserted()
    verdict = judge_prose(text)
    if verdict is None:
        return
    reason, sentence = verdict
    check.violation(
        path,
        line,
        f"execution interface declared in prose ({where})",
        f'"{sentence}" — {reason}',
    )


def _scan_comments(check: Check, path: pathlib.Path, source: str) -> None:
    """L3 over Python COMMENTS, which the AST discards entirely."""
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                _prose(check, path, token.start[0], "comment", token.string.lstrip("# "))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        check.violation(
            path,
            0,
            "UNTOKENISABLE",
            f"the comments of this module could not be read ({type(exc).__name__}: "
            f"{exc}), so its prose is unknown. Unknown is a failure, never a pass.",
        )


def _scan_python(check: Check, path: pathlib.Path, source: str) -> None:
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        check.violation(
            path,
            exc.lineno or 0,
            "UNPARSEABLE",
            f"this module could not be parsed ({exc.msg}), so its interfaces are unknown. "
            "Unknown is a failure, never a pass.",
        )
        return

    _scan_comments(check, path, source)

    for node in ast.walk(tree):
        candidates: list = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            candidates.append((node.name, "definition"))
            # L2 — SIGNATURE SHAPE. Judged from the FIELD SET, not from the name.
            check.asserted()
            if isinstance(node, ast.ClassDef):
                reason = judge_signature(node.name, _class_fields(node), "class")
            else:
                reason = judge_signature(node.name, _parameters(node), "function")
            if reason:
                check.violation(
                    path,
                    node.lineno,
                    "execution interface (signature shape)",
                    f"{reason} CD-AC-012: no execution pathway exists, and a pathway is "
                    "recognised by what it carries, not by what it is called.",
                )
        elif isinstance(node, ast.Name):
            candidates.append((node.id, "name"))
        elif isinstance(node, ast.Attribute):
            candidates.append((node.attr, "attribute"))
        elif isinstance(node, ast.arg):
            candidates.append((node.arg, "parameter"))
        elif isinstance(node, ast.keyword) and node.arg:
            candidates.append((node.arg, "keyword argument"))
        elif isinstance(node, ast.alias):
            module_tail = node.name.split(".")[-1]
            check.asserted()
            for part in node.name.split("."):
                if part in BROKER_SDK_MODULES:
                    check.violation(
                        path,
                        getattr(node, "lineno", 0),
                        "broker SDK import",
                        f"`import {node.name}` brings in `{part}`, a known broker, "
                        "exchange or order-routing SDK. It carries no execution word in "
                        "its name, which is why the denylist exists alongside the token "
                        "rules.",
                    )
            candidates.append((module_tail, "import"))
            if node.asname:
                candidates.append((node.asname, "import alias"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.strip()
            # L3 — every string literal, docstrings included. A docstring IS a Constant,
            # so this one branch covers module, class and function documentation as well
            # as ordinary message strings.
            _prose(check, path, node.lineno, "docstring or string literal", text)
            if ENDPOINT.search(text) and len(text) < 400:
                check.asserted()
                segments = [
                    segment for segment in re.split(r"[/?&#]", text) if segment
                ]
                for segment in segments:
                    # A PATH SEGMENT IS A RESOURCE, NOT ENGLISH. In prose `orders` may be
                    # a verb about filenames; in `/v2/orders/new` it is the thing the
                    # endpoint acts on, and no partner token is needed to know that. So a
                    # bare execution object condemns a segment here, where in an
                    # identifier it would not — the composite rules exist to avoid firing
                    # on English, and a URL path is not English. Variant EX-V6 escaped the
                    # first cut of this check for exactly this reason (CD-ENG-F28).
                    bare = sorted(tokens(segment) & (TRADEABLE_NOUNS | STRONG_NOUNS))
                    reason = judge_identifier(segment)
                    if bare and not reason:
                        reason = (
                            f"the path segment `{segment}` names `{bare[0]}` — in an "
                            "endpoint that is the resource being acted on."
                        )
                    if reason:
                        check.violation(
                            path,
                            node.lineno,
                            "execution endpoint in a string literal",
                            f'the endpoint "{text[:100]}" has a path segment that is an '
                            f"order pathway: {reason}",
                        )
                        break
            continue

        for identifier, kind in candidates:
            check.asserted()
            reason = judge_identifier(identifier)
            if reason:
                check.violation(
                    path,
                    getattr(node, "lineno", 0),
                    f"execution interface ({kind})",
                    f"{reason} CD-AC-012: no execution pathway exists, and advisory-only "
                    "is structural rather than a policy anybody has to keep.",
                )


def _scan_sql(check: Check, path: pathlib.Path, source: str) -> None:
    """L1 over SQL identifiers, L3 over the comments and literals blanked out of L1.

    The blanking is why L1 does not cry wolf on a migration comment; reading the blanked
    text separately, under the prose rule, is how CD-PL-F32's second gap is closed here
    too. A migration whose comment says it routes orders to the broker is as much a
    declaration as one whose table is called ``order_ticket``.
    """
    for pattern, where in (
        (SQL_DOLLAR, "SQL dollar-quoted body"),
        (SQL_COMMENT, "SQL comment"),
        (SQL_STRING, "SQL string literal"),
    ):
        for match in pattern.finditer(source):
            _prose(
                check,
                path,
                source.count("\n", 0, match.start()) + 1,
                where,
                match.group(0).strip("-/*$' \t"),
            )

    blanked = SQL_DOLLAR.sub(lambda m: " " * len(m.group(0)), source)
    blanked = SQL_COMMENT.sub(lambda m: " " * len(m.group(0)), blanked)
    blanked = SQL_STRING.sub(lambda m: " " * len(m.group(0)), blanked)
    for match in SQL_IDENTIFIER.finditer(blanked):
        identifier = match.group(0)
        check.asserted()
        reason = judge_identifier(identifier)
        if reason:
            line = blanked.count("\n", 0, match.start()) + 1
            check.violation(
                path,
                line,
                "execution interface (SQL identifier)",
                f"{reason} A table, column or function with this name is an execution "
                "pathway in the store, which outlives any code that reads it.",
            )


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    if not (root / "src").is_dir():
        return check.refuse(
            "src/ does not exist in this subject tree. There is no application source to "
            "scan, and an absent codebase must not read as a codebase with no execution "
            "interface in it."
        )

    scanned = 0
    for directory in SCAN_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix not in (".py", ".sql"):
                continue
            relative = path.relative_to(root).as_posix()
            if _excluded(relative):
                continue
            source = read_text(check, path)
            if source is None:
                continue
            scanned += 1
            if path.suffix == ".py":
                _scan_python(check, path, source)
            else:
                _scan_sql(check, path, source)

    if scanned == 0:
        return check.refuse(
            "no Python or SQL files were found in "
            + ", ".join(SCAN_DIRS)
            + ". Nothing was examined."
        )

    check.note(
        "EXCLUDED, with reason: "
        + ", ".join(EXCLUDED)
        + " — the register's own guards, which must name what they forbid in order to "
        "forbid it. Their content is vocabulary data, not an interface. Every other file "
        "under tools/ is scanned."
    )
    check.note(
        "THREE LAYERS ran over every file: L1 identifier composition, L2 signature shape "
        "(the field set of every callable and class, read WITHOUT its name), and L3 prose "
        "(docstrings, comments, string literals, SQL comments). L2 and L3 were added "
        "closing CD-PL-F32, where `submit_instruction(symbol, qty, side)` passed L1 both "
        "with and without a docstring saying it routed orders to a broker."
    )
    check.note(
        f"L3 DOES NOT READ a sentence carrying any of {len(PROSE_NEGATIONS)} negation "
        f"words or any of {len(PROSE_HYPOTHETICALS)} hypothetical words. That is WIDER "
        "than the obvious list: besides `no`, `never`, `forbidden`, `if` and `would`, it "
        "includes `must`, `free`, `advisory`, `zero`, `say`, `check`, `example`, "
        "`criterion` and `were`. MEASURED: \"The engine must send each instruction to the "
        "broker\" is not read by L3, on `must` alone (CD-ENG-F39, DECLARED not fixed, "
        "CD-D-017). The trade is deliberate — this project's own documentation says "
        "repeatedly that it places no orders — and it is affordable only because L1 and L2 "
        "never read prose. Read the DECLARED LIMIT in this file's header for the full "
        "account of the six boundaries; do not read a clean run here as proof that no "
        "execution pathway exists."
    )

    return check.done(
        f"{scanned} Python and SQL files under {', '.join(SCAN_DIRS)}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
