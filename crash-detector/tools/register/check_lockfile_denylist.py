#!/usr/bin/env python3
"""CD-RT-012-LOCKFILE-DENYLIST — no broker SDK can arrive as a dependency.

    python3 tools/register/check_lockfile_denylist.py --root <subject tree>

CRITERION: CD-AC-012, "no execution pathway exists" (PID §6, BLUEPRINT §13: "lockfile
scanned against a broker-SDK denylist").

WHY A SEPARATE CHECK FROM THE SOURCE SCAN. ``check_no_execution_interface.py`` reads code
that exists. This reads what the project has given itself permission to import. A broker
SDK in the lockfile is an execution pathway that is one ``import`` away and needs no new
dependency review to become real — the review already happened, and it said yes. Catching
it at the manifest is catching it before the code that uses it is written.

WHAT IT READS
--------------
Every dependency manifest in the tree, and it must find all three of the declared ones:

  * ``pyproject.toml`` — ``[project].dependencies``, every ``[project.optional-dependencies]``
    group, and ``[build-system].requires``. Parsed with ``tomllib`` (stdlib since 3.11).
  * ``requirements.txt`` — the direct pins.
  * ``requirements.lock`` — the full resolved set. This is the one that matters most,
    because a transitive dependency is a dependency nobody chose and everybody installs.

plus any other ``requirements*.txt``, ``*.lock`` or ``constraints*.txt`` it finds, so
adding ``requirements-extra.txt`` does not create a blind spot.

HOW IT JUDGES — BUILT FOR THE CLASS. Names are normalised per PEP 503 (lowercased, runs of
``-``, ``_`` and ``.`` collapsed), so ``Alpaca_Trade_API`` and ``alpaca-trade-api`` are the
same name. Then two rules, either of which condemns:

  1  the normalised name is on the denylist of known broker, exchange and order-routing
     SDKs in ``_broker_vocabulary.py`` — which is how ``ccxt`` and ``ib-insync`` fail,
     since neither carries an execution word;
  2  the name carries an execution token (``broker``, ``order``, ``trade``, ``trading``,
     ``execution``, ``oms``, ``ems``, ``fix``, ``exchange`` …) — which is how a broker SDK
     nobody has heard of fails, because it is still named after what it does.

The denylist is explicitly a FLOOR and not an oracle, and the check says so in its own
output rather than letting a reader assume completeness.

PRECONDITIONS THAT REFUSE (PBG-CI-002): a missing ``pyproject.toml``, ``requirements.txt``
or ``requirements.lock`` is a non-zero exit — a dependency surface that cannot be read has
not been shown to be clean. So is a manifest from which zero distributions were extracted:
that means the parse failed, not that the file is empty of brokers.

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
"""

from __future__ import annotations

import pathlib
import re
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _broker_vocabulary import (  # noqa: E402
    BROKER_SDK_DISTRIBUTIONS,
    judge_distribution,
    normalise_distribution,
)
from _support import Check, parse_root, read_text, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-012-LOCKFILE-DENYLIST"

REQUIRED_MANIFESTS = ("pyproject.toml", "requirements.txt", "requirements.lock")

EXTRA_PATTERNS = ("requirements*.txt", "*.lock", "constraints*.txt")

#: `name[extra]==1.2.3 ; marker` — the leading distribution name is all this needs.
REQUIREMENT_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _requirements_names(text: str) -> list:
    """(name, line) for every requirement line. Comments, hashes and options skipped."""
    found: list = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        line = line.rstrip("\\").strip()
        if not line:
            continue
        if line.startswith("-"):
            # `--hash=...`, `-r other.txt`, `--require-hashes`, `--index-url`
            continue
        if line.startswith(("--hash", "sha256:")):
            continue
        match = REQUIREMENT_NAME.match(line)
        if not match:
            continue
        name = match.group(1)
        if name.lower() in {"sha256", "md5", "sha512"}:
            continue
        found.append((name, number))
    return found


def _toml_names(check: Check, path: pathlib.Path, text: str) -> list:
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        check.violation(
            path,
            0,
            "UNPARSEABLE",
            f"pyproject.toml is not valid TOML ({exc}). A dependency surface the check "
            "cannot read has not been shown to be clean.",
        )
        return []

    found: list = []
    project = document.get("project", {})
    for requirement in project.get("dependencies", []) or []:
        found.append((requirement, "[project].dependencies"))
    for group, requirements in (project.get("optional-dependencies", {}) or {}).items():
        for requirement in requirements or []:
            found.append((requirement, f"[project.optional-dependencies.{group}]"))
    for requirement in (document.get("build-system", {}) or {}).get("requires", []) or []:
        found.append((requirement, "[build-system].requires"))

    named: list = []
    for requirement, where in found:
        match = REQUIREMENT_NAME.match(str(requirement))
        if match:
            line = 0
            for number, raw in enumerate(text.splitlines(), start=1):
                if match.group(1) in raw:
                    line = number
                    break
            named.append((match.group(1), line, where))
    return named


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    missing = [name for name in REQUIRED_MANIFESTS if not (root / name).is_file()]
    if missing:
        return check.refuse(
            "a declared dependency manifest is missing from the subject tree: "
            + ", ".join(missing)
            + ". A dependency surface that cannot be read has not been shown to be free "
            "of broker SDKs, and its absence must not read as a pass."
        )

    manifests: list = []
    for name in REQUIRED_MANIFESTS:
        manifests.append(root / name)
    for pattern in EXTRA_PATTERNS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in manifests:
                manifests.append(path)

    for path in manifests:
        text = read_text(check, path)
        if text is None:
            continue
        if path.name == "pyproject.toml":
            entries = [
                (name, line, where) for name, line, where in _toml_names(check, path, text)
            ]
        else:
            entries = [(name, line, path.name) for name, line in _requirements_names(text)]

        if not entries:
            return check.refuse(
                f"zero distributions were extracted from {path.name}. That means the "
                "parse failed, not that the file names no brokers — and a check that "
                "examined nothing must never report clean."
            )

        for name, line, where in entries:
            check.asserted()
            reason = judge_distribution(name)
            if reason:
                check.violation(
                    path,
                    line,
                    "broker SDK in a dependency manifest",
                    f"{reason} Declared in {where}. CD-AC-012: no execution pathway "
                    "exists. A dependency is permission to import, and permission granted "
                    "is the review already done.",
                )

    check.note(
        f"the denylist carries {len(BROKER_SDK_DISTRIBUTIONS)} named distributions and is "
        "a FLOOR, not an oracle. The token rule is the part that generalises: a broker SDK "
        "nobody has heard of is still named after what it does."
    )
    check.note(
        "normalisation is PEP 503, so Alpaca_Trade_API and alpaca-trade-api are one name: "
        + normalise_distribution("Alpaca_Trade_API")
    )

    return check.done(
        f"{len(manifests)} dependency manifests: "
        + ", ".join(path.name for path in manifests)
    )


if __name__ == "__main__":
    raise SystemExit(main())
