"""Canonical framework-version authority.

Implements PBG-FWK-010 (one manually maintained version authority) and PBG-FWK-011 (no
hand-embedded framework versions).

PBGv1 declared its own version five contradictory ways at the commit tagged PBG-1.0.10, because
one fact was maintained by hand in seven files. This module makes that defect a validation
failure rather than a discipline problem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: The only hand-maintained framework-version authority.
VERSION_FILE = "VERSION"

#: Any PBG-style version literal. Classification of whether it is a SELF-declaration or a
#: HISTORICAL reference to a predecessor is decided against the canonical VERSION at scan time —
#: never hardcoded to a major version. Hardcoding "major >= 2" would silently stop working at
#: PBGv3, which is exactly the class of latent defect this module exists to prevent.
_PBG_VERSION_ANY = re.compile(r"(?i)\bPBG[-_ ]v?(\d+)\.(\d+)\.(\d+)(?:-[0-9A-Za-z.]+)?\b")

#: Assignment forms are ALWAYS self-declarations regardless of the value they carry.
_PBG_VERSION_ASSIGNMENT = re.compile(
    r"""(?ix)
    (?:
        \b pbg[_-]?version           \s* [:=] \s* ["']? v? \d+\.\d+\.\d+
      | \b governance[-_]version     \s* [:=] \s* ["']? (?:PBG[-_])? v? \d+\.\d+\.\d+
      | \b framework[-_]version      \s* [:=] \s* ["']? v? \d+\.\d+\.\d+
      | \b GOVERNANCE_VERSION        \s* [:=] \s* ["']? (?:PBG[-_])? v? \d+\.\d+\.\d+
    )
    """
)

SELF_DECLARATION = "SELF_DECLARATION"
HISTORICAL_REFERENCE = "HISTORICAL_REFERENCE"
STALE_GENERATED_VALUE = "STALE_GENERATED_VALUE"


def classify(literal: str, canonical: str) -> str:
    """Is this literal the framework declaring its own version, or citing a predecessor?

    A predecessor major version can never be this framework's own version, so citing it is
    history. Anything at or above the canonical major IS a self-declaration — including future
    majors, so a stale or premature value is caught rather than waved through.
    """
    match = _PBG_VERSION_ANY.search(literal)
    if not match:
        return SELF_DECLARATION
    major = int(match.group(1))
    canonical_major = int(canonical.split(".")[0])
    if major < canonical_major:
        return HISTORICAL_REFERENCE
    return SELF_DECLARATION


#: Locations where a hand-maintained framework version is prohibited outright (PBG-FWK-011).
PROHIBITED_GLOBS = (
    "roles/**/*.md",
    "templates/**/*",
    "skills/**/*",
    "adapters/**/*",
    "schemas/**/*",
    "examples/**/*",
    "policies/**/*",
    "standards/**/*",      # N-2: omitted, so a hand-stamped version here was invisible
    "tools/**/*.py",
    "README.md",
    "docs/CONTRIBUTING.md",
)

#: Paths where discussing versions is legitimate: history, archaeology, migration and changelog.
#: These describe PBGv1's versions or record supersession; they are not framework self-declaration.
EXEMPT_PREFIXES = (
    "docs/archaeology/",
    "docs/migration/",
    "docs/architecture/",
    "docs/proposals/",
    "CHANGELOG.md",
    "PROVENANCE.md",
)


@dataclass(frozen=True)
class VersionFinding:
    path: str
    line: int
    text: str
    reason: str
    classification: str = "SELF_DECLARATION"


def read_version(root: Path) -> str:
    """Read the canonical framework version. The single source of truth."""
    path = root / VERSION_FILE
    if not path.is_file():
        raise FileNotFoundError(f"canonical {VERSION_FILE} not found at {path}")
    raw = path.read_text(encoding="utf-8").strip()
    if not raw or "\n" in raw:
        raise ValueError(f"{VERSION_FILE} must contain exactly one version scalar, got {raw!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?", raw):
        raise ValueError(f"{VERSION_FILE} is not a valid semantic version: {raw!r}")
    return raw


def _is_exempt(rel: str) -> bool:
    return any(rel.startswith(prefix) for prefix in EXEMPT_PREFIXES)


def scan(root: Path) -> list[VersionFinding]:
    """Find every hand-maintained framework-version declaration outside the authority.

    Returns findings; an empty list means the tree declares its version in exactly one place.
    Classification is relative to the canonical VERSION, so this keeps working across future
    major versions.
    """
    canonical = read_version(root)
    findings: list[VersionFinding] = []
    seen: set[Path] = set()

    for pattern in PROHIBITED_GLOBS:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            rel = path.relative_to(root).as_posix()
            if _is_exempt(rel):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                assignment = _PBG_VERSION_ASSIGNMENT.search(line)
                literal = _PBG_VERSION_ANY.search(line)

                if assignment:
                    findings.append(VersionFinding(
                        path=rel, line=lineno, text=assignment.group(0).strip(),
                        reason=("framework-version assignment in a prohibited location "
                                "(PBG-FWK-011); resolve it at generation time from VERSION"),
                        classification=SELF_DECLARATION))
                    continue

                if literal:
                    kind = classify(literal.group(0), canonical)
                    if kind == HISTORICAL_REFERENCE:
                        continue  # citing a predecessor is history, not self-declaration
                    stale = literal.group(0).endswith(canonical)
                    findings.append(VersionFinding(
                        path=rel, line=lineno, text=literal.group(0).strip(),
                        reason=("hand-embedded framework version in a prohibited location "
                                "(PBG-FWK-011); resolve it at generation time from VERSION"),
                        classification=STALE_GENERATED_VALUE if not stale else SELF_DECLARATION))
    return findings


def check_manifest(root: Path, manifest: dict | None) -> list[VersionFinding]:
    """manifest.yaml must agree with VERSION exactly (PBG-FWK-010)."""
    if manifest is None:
        return []
    canonical = read_version(root)
    declared = str(manifest.get("framework_version", "")).strip()
    if declared != canonical:
        return [
            VersionFinding(
                path="manifest.yaml",
                line=0,
                text=declared or "<absent>",
                reason=(
                    f"manifest framework_version {declared!r} disagrees with canonical "
                    f"VERSION {canonical!r} (PBG-FWK-010)"
                ),
            )
        ]
    return []
