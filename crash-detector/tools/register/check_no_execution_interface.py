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
``deploy/``, ``tests/`` and ``tools/`` — and inside each, the things that are INTERFACES
rather than prose:

  * Python: the names of functions, classes, parameters, variables, attributes, keyword
    arguments and imports; plus string literals that look like an endpoint (a URL, or a
    path with segments).
  * SQL: identifiers — table names, column names, function names.

DOCSTRINGS, COMMENTS AND ORDINARY PROSE ARE DELIBERATELY NOT MATCHED, and the boundary is
stated rather than left to be discovered. A docstring saying "this system places no orders"
is not an order interface; a function called ``place_order`` is. Matching prose would fill
the output with the project's own descriptions of what it refuses to do, and a check whose
findings are mostly noise is a check nobody reads.

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

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _broker_vocabulary import (  # noqa: E402
    BROKER_SDK_MODULES,
    EXECUTION_OBJECTS,
    STRONG_NOUNS,
    judge_identifier,
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

    for node in ast.walk(tree):
        candidates: list = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            candidates.append((node.name, "definition"))
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
                    bare = sorted(tokens(segment) & (EXECUTION_OBJECTS | STRONG_NOUNS))
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
    """SQL identifiers only. Comments and string literals are blanked out first."""
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
        "docstrings, comments and prose are deliberately not matched: a sentence saying "
        "this system places no orders is not an order interface."
    )

    return check.done(
        f"{scanned} Python and SQL files under {', '.join(SCAN_DIRS)}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
