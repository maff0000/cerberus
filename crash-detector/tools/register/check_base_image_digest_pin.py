#!/usr/bin/env python3
"""CD-BASE-IMAGE-DIGEST-PIN — every base image is an identity, not a mutable pointer.

    python3 tools/register/check_base_image_digest_pin.py --root <subject tree>

BUILT TO A CONTRACT THAT ALREADY EXISTED. ``deploy/base-images.json`` carries a
``register_check_contract`` block written in increment 3, naming what this check must scan,
what it must fail on, what it must accept and that it must not skip. This script implements
that contract clause by clause, and reads the contract OUT OF THE FILE at run time rather
than restating it — so a subject tree whose contract has been edited is checked against its
own contract, and a contract clause that has been deleted is a violation rather than a
clause the check quietly stops enforcing.

"A tag is a mutable pointer; a digest is an identity" (Standards Baseline §3). ``FROM
python:3.11-slim`` is a promise that whatever is behind that tag today is what you audited,
and nobody controls what is behind it tomorrow.

WHAT IT ASSERTS
----------------
 must_scan
   * every ``services.<name>.image`` in ``deploy/compose.yaml``
   * every ``FROM`` line in every ``deploy/Dockerfile.*``
   * every ``pins[].reference`` in ``deploy/base-images.json`` itself

 must_fail_on
   * a reference with a ``:`` tag separator and no ``@sha256:`` digest
   * a bare image name with no tag and no digest — an implicit ``:latest``, which is the
     most mutable pointer there is and the easiest to not notice
   * a digest that is not exactly 64 lowercase hex characters
   * ``FROM ${ARG}`` where ``ARG`` is declared WITH A DEFAULT. A default is a value nobody
     re-examined: the build succeeds with it, so nobody is ever told it was used.

 must_accept
   * ``<name>@sha256:<64 lowercase hex>``
   * ``FROM ${ARG}`` where ``ARG`` is declared with NO default AND the argument appears in
     ``base-images.json`` with an explicit status. That is the WO-2 state for the six
     application images: the Python base digest is unresolved (CD-OB-002, owed at WO-3 with
     RT-B), each Dockerfile declares ``ARG CD_PYTHON_BASE`` with no default, and compose
     passes it with ``${CD_PYTHON_BASE:?...}``. Both fail closed — ``docker build`` refuses
     a blank base and ``docker compose`` refuses an unset variable — so there is no tag
     literal anywhere for this check to have to forgive.

 must_not_skip
   A Dockerfile that cannot be parsed, a compose file that cannot be read, an unresolved
   pin with no stated status: each is a NON-ZERO exit with the reason printed. Never a
   pass, never a skip (PBG-CI-002).

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, read_text, resolve_root  # noqa: E402
from _yamlmin import YamlSubsetError, line_of, load_yaml  # noqa: E402

CHECK_ID = "CD-BASE-IMAGE-DIGEST-PIN"

COMPOSE = "deploy/compose.yaml"
BASE_IMAGES = "deploy/base-images.json"

DIGEST_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/:]*@sha256:([0-9a-f]{64})$")
ANY_DIGEST = re.compile(r"@sha256:([0-9A-Za-z]*)$")
BUILD_ARG = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)(?::[?\-+][^}]*)?\}$")
FROM_LINE = re.compile(r"^\s*FROM\s+(\S+)", re.IGNORECASE)
ARG_LINE = re.compile(r"^\s*ARG\s+([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*(.*))?\s*$", re.IGNORECASE)


def _judge_reference(reference: str) -> "str | None":
    """Why this image reference is not a digest pin, or None if it is one."""
    text = reference.strip()
    if not text:
        return "the reference is empty."
    if DIGEST_REFERENCE.match(text):
        return None
    malformed = ANY_DIGEST.search(text)
    if malformed:
        digest = malformed.group(1)
        return (
            f"the digest `{digest}` is {len(digest)} character(s) and must be exactly 64 "
            "lowercase hex. A digest of the wrong length is not a shorter identity, it is "
            "not an identity."
        )
    if "@" in text:
        return (
            f"`{text}` carries an `@` but not a well-formed `@sha256:<64 hex>` digest."
        )
    tail = text.rsplit("/", 1)[-1]
    if ":" in tail:
        return (
            f"`{text}` is pinned BY TAG and carries no `@sha256:` digest. A tag is a "
            "mutable pointer: whatever is behind it today is not what will be behind it "
            "tomorrow, and nothing here would notice."
        )
    return (
        f"`{text}` is a bare image name with no tag and no digest — an implicit `:latest`. "
        "That is the most mutable pointer there is and the easiest to not notice."
    )


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    base_images_path = root / BASE_IMAGES
    compose_path = root / COMPOSE
    dockerfiles = sorted((root / "deploy").glob("Dockerfile.*")) if (root / "deploy").is_dir() else []

    if not base_images_path.is_file():
        return check.refuse(
            f"{BASE_IMAGES} does not exist. This check reads its contract and its declared "
            "pins out of that file; without it there is no contract to check against and "
            "no declaration of which build arguments are legitimately unresolved."
        )
    if not compose_path.is_file():
        return check.refuse(f"{COMPOSE} does not exist in this subject tree.")
    if not dockerfiles:
        return check.refuse(
            "no deploy/Dockerfile.* files were found. The contract requires every FROM "
            "line to be scanned, and finding none means the scan failed, not that the "
            "tree is clean."
        )

    text = read_text(check, base_images_path)
    if text is None:
        return check.refuse(f"{BASE_IMAGES} could not be read.")
    try:
        declaration = json.loads(text)
    except json.JSONDecodeError as exc:
        return check.refuse(f"{BASE_IMAGES} is not valid JSON ({exc.msg}).")

    contract = declaration.get("register_check_contract")
    if not isinstance(contract, dict) or contract.get("id") != CHECK_ID:
        return check.refuse(
            f"{BASE_IMAGES} carries no register_check_contract with id {CHECK_ID}. This "
            "check implements a contract that is declared in the subject tree; a subject "
            "whose contract has been removed has removed the specification this check "
            "answers to, and that is a failure rather than a check with nothing to do."
        )
    for clause in ("must_scan", "must_fail_on", "must_accept", "must_not_skip"):
        check.asserted()
        if not contract.get(clause):
            check.violation(
                base_images_path,
                0,
                "the register check contract has been weakened",
                f"register_check_contract.{clause} is missing or empty in "
                f"{BASE_IMAGES}. Deleting a clause of the specification is how a check "
                "comes to enforce less than it was written to enforce.",
            )

    # -- the declared pins ------------------------------------------------------------- #
    pins = declaration.get("pins")
    if not isinstance(pins, list) or not pins:
        return check.refuse(f"{BASE_IMAGES} declares no pins. Nothing was examined.")

    unresolved_arguments: set = set()
    for pin in pins:
        check.asserted()
        identifier = pin.get("id", "<unnamed>")
        status = pin.get("status")
        reference = pin.get("reference")
        if status == "RESOLVED":
            reason = _judge_reference(str(reference or ""))
            if reason:
                check.violation(
                    base_images_path,
                    0,
                    "a RESOLVED pin is not a digest",
                    f"pin `{identifier}` is declared RESOLVED but {reason}",
                )
        elif isinstance(status, str) and status:
            if reference is not None:
                check.violation(
                    base_images_path,
                    0,
                    "an unresolved pin carries a reference",
                    f"pin `{identifier}` has status {status} and yet declares "
                    f"reference {reference!r}. An unresolved pin carrying a plausible "
                    "value is exactly the constructed evidence this file's own note "
                    "forbids.",
                )
            unresolved_arguments.add("CD_PYTHON_BASE")
            check.note(
                f"pin `{identifier}` is {status} and carries no reference. That is the "
                "declared WO-2 state (CD-OB-002, owed at WO-3 with RT-B) and it fails "
                "CLOSED: the Dockerfiles take the base as an ARG with no default and "
                "compose passes it with `:?`, so a build refuses rather than guessing."
            )
        else:
            check.violation(
                base_images_path,
                0,
                "a pin with no status",
                f"pin `{identifier}` declares no status. A pin that says neither "
                "RESOLVED nor why it is not is a pin nobody can act on.",
            )

    # -- compose service images --------------------------------------------------------- #
    try:
        document = load_yaml(compose_path)
    except YamlSubsetError as exc:
        return check.refuse(
            f"{COMPOSE} could not be parsed by this reader: {exc}. A compose file the "
            "check cannot read is a set of image references it cannot verify."
        )
    services = document.get("services")
    if not isinstance(services, dict) or not services:
        return check.refuse(f"{COMPOSE} declares no services.")

    images_seen = 0
    for name, body in sorted(services.items()):
        if not isinstance(body, dict):
            continue
        image = body.get("image")
        if image is None:
            continue
        images_seen += 1
        check.asserted()
        reason = _judge_reference(str(image))
        if reason:
            check.violation(
                compose_path,
                line_of(body, "image") or line_of(services, name),
                "compose service image is not digest-pinned",
                f"service `{name}`: {reason}",
            )

    # -- Dockerfile FROM lines ----------------------------------------------------------- #
    for path in dockerfiles:
        source = read_text(check, path)
        if source is None:
            continue
        lines = source.splitlines()
        arg_defaults: dict = {}
        for number, raw in enumerate(lines, start=1):
            match = ARG_LINE.match(raw)
            if match:
                arg_defaults[match.group(1)] = (
                    match.group(3).strip() if match.group(3) is not None else None,
                    number,
                )

        from_lines = [
            (number, match.group(1))
            for number, raw in enumerate(lines, start=1)
            for match in [FROM_LINE.match(raw)]
            if match
        ]
        if not from_lines:
            check.violation(
                path,
                0,
                "no FROM line",
                "this Dockerfile declares no FROM line that the check could parse. A "
                "Dockerfile whose base cannot be determined is a base that has not been "
                "shown to be pinned — the contract's must_not_skip clause, applied.",
            )
            continue

        for number, reference in from_lines:
            check.asserted()
            argument = BUILD_ARG.match(reference)
            if argument:
                argument_name = argument.group(1)
                if argument_name not in arg_defaults:
                    check.violation(
                        path,
                        number,
                        "FROM references an undeclared build argument",
                        f"`FROM {reference}` uses `{argument_name}`, which this "
                        "Dockerfile never declares with an ARG. An undeclared argument "
                        "expands to the empty string.",
                    )
                    continue
                default, arg_line = arg_defaults[argument_name]
                if default not in (None, ""):
                    check.violation(
                        path,
                        arg_line,
                        "the base image build argument has a DEFAULT",
                        f"`ARG {argument_name}={default}` gives the base image a default. "
                        "A default is a value nobody re-examined: the build succeeds with "
                        "it, so nobody is ever told it was used. Declare the ARG with no "
                        "default so an unset base is a refusal.",
                    )
                    continue
                if argument_name not in unresolved_arguments:
                    check.violation(
                        path,
                        number,
                        "FROM takes a build argument that no pin declares",
                        f"`FROM {reference}` defers the base image to `{argument_name}`, "
                        f"but {BASE_IMAGES} declares no pin with an explicit status for "
                        "it. Deferring a base to an argument is acceptable only when the "
                        "deferral is declared and dated; otherwise it is a hole with a "
                        "variable in it.",
                    )
                continue

            if "$" in reference:
                check.violation(
                    path,
                    number,
                    "FROM interpolates something the check cannot resolve",
                    f"`FROM {reference}` is neither a digest reference nor a plain "
                    "`${ARG}`. The check cannot establish what it resolves to, and it "
                    "fails closed rather than passing on ignorance.",
                )
                continue

            reason = _judge_reference(reference)
            if reason:
                check.violation(
                    path, number, "Dockerfile FROM is not digest-pinned", reason
                )

    if images_seen == 0:
        return check.refuse(
            f"{COMPOSE} declares no service with an `image:` key, so no compose image "
            "reference was examined."
        )

    return check.done(
        f"{len(pins)} declared pins, {images_seen} compose service images and "
        f"{len(dockerfiles)} Dockerfiles"
    )


if __name__ == "__main__":
    raise SystemExit(main())
