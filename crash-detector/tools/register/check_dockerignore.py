#!/usr/bin/env python3
"""CD-BUILD-CONTEXT-RESTRICTED — the governance record never enters a build context.

    python3 tools/register/check_dockerignore.py --root <subject tree>

AUTHORITY: ``.dockerignore`` was added to this seat's writable scope by CD-D-013
(BL-20260819T052900Z-0007). The dispatch left it to this seat's judgement whether a
register check belongs with it. It does, and here is the reasoning, since a judgement call
should carry one: every other protection in this project is enforced by something. An
ignore file that nothing checks is a convention, and a convention is what you have instead
of a control. The specific failure it prevents — ``governance/`` and ``pbg/`` uploaded to
the Docker daemon and baked into image layers — is silent, is invisible in a passing build,
and is not undone by noticing it later, because the layers are already published.

WHAT IT ASSERTS
----------------
 1  ``.dockerignore`` exists at the repository root — the only place ``docker build``
    reads it from when the context is the root, which compose declares it to be.
 2  Every REQUIRED exclusion below is actually excluded. The dispatch names
    ``.git/``, ``__pycache__/``, ``.pytest_cache/``, ``.env*``, ``*.pem``, ``*.key``,
    ``plants/``, ``governance/`` and ``pbg/``; each is checked here.
 3  Nothing the build NEEDS has been excluded. ``src/``, ``deploy/entrypoints/`` and
    ``contracts/`` are copied by the Dockerfiles or mounted by compose, and an ignore file
    that excluded them would break the build in a way that is obvious — but an ignore file
    that excluded one of them behind a broad pattern would break it in a way that is not.

BUILT FOR THE CLASS, NOT THE INSTANCE. It would be easy, and wrong, to check that the file
CONTAINS the line ``governance``. Docker's ignore syntax has several spellings of the same
exclusion — ``pbg``, ``pbg/``, ``pbg/**``, ``**/pbg``, ``./pbg`` — and a negation
(``!governance``) can re-include a path that an earlier broad pattern excluded. So this
check does not search for text. It IMPLEMENTS Docker's matching semantics (``Path.Match``
over slash-separated components, with ``*``, ``?``, ``**`` and leading ``!`` negation,
last-match-wins) and asks the question that actually matters: given this pattern set, is
this path excluded from the context? Every spelling above answers yes; a negation that
re-includes it answers no, and fails.

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import fnmatch
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, read_text, resolve_root  # noqa: E402

CHECK_ID = "CD-BUILD-CONTEXT-RESTRICTED"

DOCKERIGNORE = ".dockerignore"

#: Paths that MUST be excluded from the build context, each with why it matters. The first
#: nine are named in the dispatch; the rest are the same classes of harm.
REQUIRED_EXCLUSIONS = (
    (".git", "the whole repository history, including every file ever deleted"),
    (".git/config", "a git config can carry credentials in a remote URL"),
    ("__pycache__", "host bytecode that can shadow the source it was compiled from"),
    (
        "src/crash_detector/__pycache__/__init__.cpython-311.pyc",
        "a nested __pycache__, which a root-anchored pattern would miss",
    ),
    (".pytest_cache", "test residue naming files and outcomes from the host"),
    (".env", "environment files carry secret VALUES; this project carries only names"),
    (".env.production", "the .env family, not just the bare name"),
    ("server.pem", "a certificate or private key in PEM form"),
    ("id_rsa.key", "a private key"),
    ("plants/CD-AC-001/numeric-default.patch", "the planted violations are audit "
     "instruments and must never be inside a runnable image"),
    ("governance/authority/CD-AUTH-0001-project-lead.yaml", "the authority record"),
    (
        "governance/engineering/build-log/BL-20260818T175100Z-0001.yaml",
        "the Build Log — the project's own account of its controls",
    ),
    ("pbg/manifest.yaml", "the pinned framework, read-only to every seat"),
    ("pbg/controls/PBG-SEC-002.yaml", "a control definition"),
    (".venv/lib/python3.11/site-packages/x.py", "host-specific binaries"),
)

#: Paths the build NEEDS. Excluding one of these breaks the build, and a broad pattern that
#: swallowed one would break it in a way nobody would attribute to this file.
REQUIRED_INCLUSIONS = (
    ("src/crash_detector/__init__.py", "COPY src/ /app/src/ in every Dockerfile"),
    ("src/crash_detector/engine/evaluate.py", "the same, nested"),
    (
        "deploy/entrypoints/cd_engine.py",
        "COPY deploy/entrypoints/ /app/entrypoints/ in every Dockerfile",
    ),
    (
        "contracts/public_envelope.schema.json",
        "bind-mounted read-only into every service that validates an envelope",
    ),
    ("requirements.lock", "the artefact a build installs from"),
    ("requirements.txt", "the direct pins"),
    ("pyproject.toml", "the project declaration"),
)


def _parse_patterns(text: str) -> list:
    """(negated, pattern, line) for every meaningful line, in file order."""
    patterns: list = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        if negated:
            line = line[1:].strip()
        line = line.rstrip("/")
        while line.startswith("./"):
            line = line[2:]
        if not line:
            continue
        patterns.append((negated, line, number))
    return patterns


def _matches(pattern: str, path: str) -> bool:
    """Docker's ignore matching: component-wise, with ``**`` spanning components.

    Docker matches a pattern against a path and, because excluding a directory excludes
    everything under it, against every ancestor prefix of that path as well.
    """
    pattern_parts = pattern.split("/")
    path_parts = path.split("/")

    def match_from(pattern_index: int, path_index: int) -> bool:
        while pattern_index < len(pattern_parts):
            token = pattern_parts[pattern_index]
            if token == "**":
                if pattern_index + 1 == len(pattern_parts):
                    return True
                for skip in range(path_index, len(path_parts) + 1):
                    if match_from(pattern_index + 1, skip):
                        return True
                return False
            if path_index >= len(path_parts):
                return False
            if not fnmatch.fnmatchcase(path_parts[path_index], token):
                return False
            pattern_index += 1
            path_index += 1
        # A pattern that matched every one of its components excludes the path it named
        # AND everything beneath it: `governance` excludes `governance/authority/x.yaml`.
        return True

    return match_from(0, 0)


def is_excluded(patterns: list, path: str) -> "tuple[bool, int, str]":
    """(excluded, line, pattern) — LAST matching pattern wins, as Docker does it."""
    verdict = False
    line = 0
    winner = ""
    for negated, pattern, number in patterns:
        if _matches(pattern, path):
            verdict = not negated
            line = number
            winner = ("!" if negated else "") + pattern
    return verdict, line, winner


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)
    path = root / DOCKERIGNORE

    if not path.is_file():
        return check.refuse(
            f"{DOCKERIGNORE} does not exist at the repository root. compose.yaml sets "
            "every build context to the repository root, so without this file `docker "
            "build` uploads the entire repository — the git history, the whole governance "
            "record and the pinned pbg/ framework — to the daemon, and any COPY that "
            "widens later bakes it into a layer. An absent ignore file must never read as "
            "a clean one."
        )

    text = read_text(check, path)
    if text is None:
        return check.refuse(f"{DOCKERIGNORE} could not be read.")

    patterns = _parse_patterns(text)
    if not patterns:
        return check.refuse(
            f"{DOCKERIGNORE} declares no patterns. An empty ignore file excludes nothing "
            "and is indistinguishable in effect from having none."
        )

    for subject, why in REQUIRED_EXCLUSIONS:
        check.asserted()
        excluded, line, winner = is_excluded(patterns, subject)
        if not excluded:
            detail = (
                f"the last pattern to match it was `{winner}` on line {line}, which "
                "RE-INCLUDES it"
                if winner
                else "no pattern in the file matches it at all"
            )
            check.violation(
                path,
                line,
                "a required exclusion is not excluded",
                f"`{subject}` would be sent to the Docker daemon as part of the build "
                f"context — {why}. {detail}. This is judged by resolving the path against "
                "the whole pattern set with Docker's own last-match-wins semantics, not "
                "by looking for a line of text, so every spelling of the exclusion "
                "counts and a negation that undoes one is caught.",
            )

    for subject, why in REQUIRED_INCLUSIONS:
        check.asserted()
        excluded, line, winner = is_excluded(patterns, subject)
        if excluded:
            check.violation(
                path,
                line,
                "the build context excludes something the build needs",
                f"`{subject}` is excluded by pattern `{winner}` on line {line}, but the "
                f"build needs it: {why}. An ignore file that swallows a needed path "
                "behind a broad pattern breaks the build in a way nobody attributes to "
                "this file.",
            )

    check.note(
        f"{len(patterns)} patterns parsed; {len(REQUIRED_EXCLUSIONS)} required exclusions "
        f"and {len(REQUIRED_INCLUSIONS)} required inclusions resolved against them"
    )

    return check.done(f"{DOCKERIGNORE} at the repository root")


if __name__ == "__main__":
    raise SystemExit(main())
