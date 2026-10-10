"""Distribution verification — internal integrity versus external authenticity.

A bundle can prove it is internally unchanged relative to its own manifest. It cannot prove the
manifest itself came from a trusted release without an external trust anchor. These are different
claims and PBGv2 must never collapse them into one word.

Implements the verification-level model and the deterministic digest construction.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------------------------- #
# Verification levels — ordered weakest to strongest
# --------------------------------------------------------------------------------------------- #

UNVERIFIED = "UNVERIFIED"
STRUCTURE_VALID = "STRUCTURE_VALID"
INTERNALLY_CONSISTENT = "INTERNALLY_CONSISTENT"
DIGEST_MATCHED_TO_INSTALL_RECORD = "DIGEST_MATCHED_TO_INSTALL_RECORD"
MATCHED_TO_TRUSTED_RELEASE = "MATCHED_TO_TRUSTED_RELEASE"
SIGNATURE_VERIFIED = "SIGNATURE_VERIFIED"
INVALID = "INVALID"

LEVEL_ORDER = (
    UNVERIFIED,
    STRUCTURE_VALID,
    INTERNALLY_CONSISTENT,
    DIGEST_MATCHED_TO_INSTALL_RECORD,
    MATCHED_TO_TRUSTED_RELEASE,
    SIGNATURE_VERIFIED,
)

#: Levels at or above which the snapshot's origin has been established by something OUTSIDE it.
#: Below this line the snapshot is only self-consistent, which detects corruption and single-file
#: tampering but proves nothing about where it came from.
EXTERNALLY_ANCHORED = {
    DIGEST_MATCHED_TO_INSTALL_RECORD,
    MATCHED_TO_TRUSTED_RELEASE,
    SIGNATURE_VERIFIED,
}

LEVEL_MEANING = {
    UNVERIFIED: "No meaningful verification completed.",
    STRUCTURE_VALID: "Required files and schemas exist; content identity is not established.",
    INTERNALLY_CONSISTENT: (
        "Files, integrity manifest and provenance agree with each other. Detects corruption and "
        "partial tampering. Does NOT independently prove canonical origin."
    ),
    DIGEST_MATCHED_TO_INSTALL_RECORD: (
        "The distribution digest matches a digest recorded OUTSIDE the snapshot at install time."
    ),
    MATCHED_TO_TRUSTED_RELEASE: (
        "The digest matches a release identity from an independently trusted source."
    ),
    SIGNATURE_VERIFIED: (
        "A signature over the release manifest verified against a trusted external key."
    ),
    INVALID: "Verification failed; the snapshot must not be trusted as framework content.",
}


# --------------------------------------------------------------------------------------------- #
# Deterministic digest — Pattern C (release-manifest root), stated explicitly
# --------------------------------------------------------------------------------------------- #
#
# Two implementations must never compute different digests from the same distribution, so the
# construction is pinned here rather than left to whatever the filesystem happened to yield.
#
# The digest covers a CANONICAL RELEASE MANIFEST containing, in sorted order:
#   framework version · canonical source SHA · builder version · required-file classification ·
#   every distributed file path with its SHA-256 and executable bit
#
# PROVENANCE.json REFERENCES that digest and is excluded from it. This removes the self-reference
# that Pattern A and B have to work around: provenance can never affect the digest it quotes.
#
# Deliberately excluded, because they are not properties of the content:
#   modification times · ownership · filesystem enumeration order · platform path separators
#   · absolute paths · any generated field that is not reproducible

DIGEST_SPEC_VERSION = "1"

#: Never part of the digest, for two distinct reasons:
#:   PROVENANCE.json  — QUOTES the digest, so including it would be circular.
#:   RELEASE_MANIFEST — IS the canonical manifest, so it cannot be an entry within itself.
#: Both were found the hard way: the first build computed the manifest before writing it, and
#: verification then recomputed over a tree that contained it. Self-reference is easy to write
#: and silent until something independent recomputes the value.
DIGEST_EXCLUDED_FILES = ("PROVENANCE.json", "RELEASE_MANIFEST")


#: The ChatGPT handover prompt is a required copy-and-boot component. Validated STRUCTURALLY —
#: required headings and instructions — never by exact full text, which would make every
#: improvement a breaking change.
CHATGPT_PROMPT_REQUIRED_MARKERS = (
    "CREATE THE PROJECT LEAD BOOTSTRAP PROMPT",
    "will not have access to this conversation",
    "EXPLICIT PRODUCT AUTHORITY DECISION",
    "ROLE AND BOOT AUTHORITY",
    "PRODUCT AUTHORITY",
    "EXECUTIVE PRODUCT DEFINITION",
    "DETAILED PID DRAFT",
    "INITIAL BLUEPRINT FOUNDATION",
    "EXISTING PROJECT OR GREENFIELD CLASSIFICATION",
    "PBG BOOT REQUIREMENTS",
    "PROJECT-LEAD OPERATING RULES",
    "WORK MODEL",
    "ROLE DISPATCH",
    "INITIAL PROJECT ARTEFACTS",
    "FIRST BUILD PLAN",
    "REQUIRED FIRST RESPONSE FROM THE PROJECT LEAD",
    "PBG BOOT VERDICT",
    "PROPOSED_PID_FROM_PRODUCT_DISCOVERY",
    "CONTAINER_READY_DESIGN",
    "capability is not authority",
    "Do not begin building the application yourself",
    "PRODUCT ROADMAP, EPICS AND STORIES",
    "PID requirement trace",
    "PROPOSED_DELIVERY_MODEL_FROM_PRODUCT_DISCOVERY",
    "does not automatically require its own branch",
    "Attempted work is not completed work",
    "thin vertical slice",
)


def check_chatgpt_prompt(path: Path) -> list[str]:
    """Structural validation of the handover prompt. Returns missing markers."""
    if not path.is_file():
        return ["file absent"]
    text = path.read_text(encoding="utf-8")
    missing = [m for m in CHATGPT_PROMPT_REQUIRED_MARKERS if m not in text]
    if len(text) < 4000:
        missing.append("file is too short to be a usable handover prompt")
    return missing


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_release_manifest(
    root: Path,
    version: str,
    source_commit: str,
    builder_version: str = DIGEST_SPEC_VERSION,
    required_files: tuple[str, ...] = (),
) -> str:
    """Build the canonical manifest text. Deterministic across platforms and runs."""
    lines = [
        f"digest-spec\t{DIGEST_SPEC_VERSION}",
        f"framework-version\t{version}",
        f"source-commit\t{source_commit}",
        f"builder-version\t{builder_version}",
    ]
    for req in sorted(required_files):
        lines.append(f"required\t{req}")

    entries = []
    for path in root.rglob("*"):
        if path.is_symlink():
            # A distribution carries content, not links. A symlink in a bundle is either a
            # packaging error or an escape attempt; either way it is not distributable content.
            raise ValueError(f"symlink in distribution: {path.relative_to(root).as_posix()}")
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()   # POSIX separators on every platform
        if rel in DIGEST_EXCLUDED_FILES:
            continue
        mode = "x" if path.stat().st_mode & 0o111 else "-"
        entries.append(f"file\t{rel}\t{_file_digest(path)}\t{mode}")

    lines.extend(sorted(entries))
    return "\n".join(lines) + "\n"          # LF only, trailing newline, sorted


def distribution_digest(manifest_text: str) -> str:
    return "sha256:" + hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------------------------- #

@dataclass
class VerificationResult:
    level: str
    internal_integrity: str
    external_authenticity: str
    findings: list[str] = field(default_factory=list)
    computed_digest: str | None = None
    declared_digest: str | None = None
    trusted_digest_source: str | None = None

    @property
    def externally_anchored(self) -> bool:
        return self.level in EXTERNALLY_ANCHORED

    def render(self) -> str:
        out = [
            f"Framework integrity   : {self.internal_integrity}",
            f"External authenticity : {self.external_authenticity}",
            f"Verification level    : {self.level}",
            f"  {LEVEL_MEANING[self.level]}",
        ]
        if not self.externally_anchored and self.level != INVALID:
            out.append(
                "  NOTE: internal hashes agreeing does not make this snapshot cryptographically "
                "authenticated. Its origin has not been independently established."
            )
        for finding in self.findings:
            out.append(f"  - {finding}")
        return "\n".join(out)


def verify(
    snapshot_root: Path,
    install_record: dict | None = None,
    trusted_digests: dict[str, str] | None = None,
) -> VerificationResult:
    """Verify a copied framework snapshot and report an honest level.

    `install_record` is the project-owned record stored OUTSIDE the snapshot. `trusted_digests`
    maps release identifier to digest from an independently trusted source. Neither may live
    inside the snapshot being verified — a bundle cannot vouch for its own origin.
    """
    findings: list[str] = []

    required = ("VERSION", "manifest.yaml", "INTEGRITY", "PROVENANCE.json")
    absent = [r for r in required if not (snapshot_root / r).is_file()]
    if absent:
        return VerificationResult(
            level=UNVERIFIED,
            internal_integrity="INCOMPLETE",
            external_authenticity="NOT_INDEPENDENTLY_VERIFIED",
            findings=[f"missing required file: {a}" for a in absent],
        )

    try:
        provenance = json.loads((snapshot_root / "PROVENANCE.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return VerificationResult(
            level=INVALID,
            internal_integrity="UNREADABLE",
            external_authenticity="NOT_INDEPENDENTLY_VERIFIED",
            findings=[f"provenance unreadable: {exc}"],
        )

    declared = provenance.get("distribution_digest")
    version = str(provenance.get("version", "")).strip()
    source_commit = str(provenance.get("source_commit", "")).strip()

    try:
        manifest_text = canonical_release_manifest(
            snapshot_root, version, source_commit,
            required_files=tuple(provenance.get("required_files", ()) or ()),
        )
    except ValueError as exc:
        return VerificationResult(
            level=INVALID,
            internal_integrity="STRUCTURALLY_INVALID",
            external_authenticity="NOT_INDEPENDENTLY_VERIFIED",
            findings=[str(exc)],
        )

    computed = distribution_digest(manifest_text)

    if declared != computed:
        findings.append("distribution digest does not match the snapshot contents")
        return VerificationResult(
            level=INVALID,
            internal_integrity="MISMATCH",
            external_authenticity="NOT_INDEPENDENTLY_VERIFIED",
            findings=findings,
            computed_digest=computed,
            declared_digest=declared,
        )

    level = INTERNALLY_CONSISTENT
    external = "NOT_INDEPENDENTLY_VERIFIED"
    trusted_source = None

    # An external anchor: a digest recorded outside the snapshot at install or approval time.
    if install_record:
        expected = install_record.get("expected_distribution_digest")
        if expected and expected == computed:
            level = DIGEST_MATCHED_TO_INSTALL_RECORD
            external = "MATCHED_TO_INSTALL_RECORD"
            trusted_source = install_record.get("trusted_digest_source") or "project install record"
        elif expected:
            findings.append(
                "install record expects a different distribution digest — the snapshot is "
                "internally consistent but is NOT the release this project approved"
            )
            return VerificationResult(
                level=INVALID,
                internal_integrity="CONSISTENT",
                external_authenticity="CONFLICTS_WITH_INSTALL_RECORD",
                findings=findings,
                computed_digest=computed,
                declared_digest=declared,
            )

    if trusted_digests:
        release = provenance.get("source_release")
        want = trusted_digests.get(release) if release else None
        if want and want == computed:
            level = MATCHED_TO_TRUSTED_RELEASE
            external = "MATCHED_TO_TRUSTED_RELEASE"
            trusted_source = "trusted release catalogue"
        elif want:
            findings.append(f"trusted catalogue digest for release {release!r} does not match")
            return VerificationResult(
                level=INVALID,
                internal_integrity="CONSISTENT",
                external_authenticity="CONFLICTS_WITH_TRUSTED_RELEASE",
                findings=findings,
                computed_digest=computed,
                declared_digest=declared,
            )

    if level == INTERNALLY_CONSISTENT:
        findings.append(
            "no external trust anchor was supplied; origin is not independently established"
        )

    return VerificationResult(
        level=level,
        internal_integrity="CONSISTENT",
        external_authenticity=external,
        findings=findings,
        computed_digest=computed,
        declared_digest=declared,
        trusted_digest_source=trusted_source,
    )


# --------------------------------------------------------------------------------------------- #
# Adapter command fidelity (PBG-PORT-003)
# --------------------------------------------------------------------------------------------- #

#: Files that tell an agent what to run. If one names a command that does not exist, the agent
#: either improvises or stops -- and both are the adapter's fault, not the agent's.
COMMAND_ADVERTISING_GLOBS = ("adapters/**/*.md", "roles/*.md", "QUICKSTART.md",
                             "CLAUDE.md", "PBG.md")

_COMMAND_PATTERNS = (
    # Flags may sit between the interpreter and -m; -B in particular is REQUIRED so that boot
    # does not write bytecode into the pinned snapshot.
    re.compile(r"python3\s+(?:-\w+\s+)*-m\s+pbg\.cli\s+([a-z][a-z-]*)"),
    re.compile(r"python3\s+(?:-\w+\s+)*\S*pbg/tools/pbg\s+([a-z][a-z-]*)"),
    # N-1: the negative lookbehind excluded a leading backtick, so `pbg verify-adapters` -- a
    # command that never existed, advertised in BOTH shipped adapters -- was invisible to the very
    # check built to catch it. Documentation markup is not a hiding place: strip it, then match.
    re.compile(r"(?<![\w/-])pbg\s+([a-z][a-z-]*)\b(?!\.)"),
)

#: Prose reads "pbg boot" the same way a shell does. These are words, not commands.
_NOT_COMMANDS = frozenset({
    "is", "as", "at", "in", "on", "to", "and", "or", "the", "a", "an", "it", "its", "itself",
    "core", "maintenance", "framework", "utility", "snapshot", "repair", "commands", "command",
    "provides", "remains", "must", "does", "plugs", "governs", "controls", "roles", "installation",
    "upgrades", "version", "identity", "development", "extension", "project", "itself",
})


def advertised_commands(root: Path) -> dict[str, set[str]]:
    """Every `pbg <command>` an agent-facing file tells someone to run."""
    found: dict[str, set[str]] = {}
    for pattern in COMMAND_ADVERTISING_GLOBS:
        for path in sorted(Path(root).glob(pattern)):
            if not path.is_file():
                continue
            raw = path.read_text(encoding="utf-8", errors="ignore")
            # Normalise markup so bare, backticked and fenced forms are all seen alike.
            text = raw.replace("`", " ").replace("~~~", " ")
            cmds = set()
            for rx in _COMMAND_PATTERNS:
                cmds |= {m.group(1) for m in rx.finditer(text)}
            cmds -= _NOT_COMMANDS
            if cmds:
                found[str(path.relative_to(root))] = cmds
    return found


def check_adapter_commands(root: Path, registered: set[str]) -> list[str]:
    """PBG-PORT-003: an adapter may not advertise a command the framework does not provide.

    Adapters are generated wiring. A rename that leaves them behind produces a file that instructs
    an agent to run something that no longer exists -- the failure is silent until a fresh agent
    boots, which is the worst possible moment to discover it.
    """
    problems = []
    for rel, cmds in advertised_commands(root).items():
        for cmd in sorted(cmds - registered):
            problems.append(f"{rel} advertises `pbg {cmd}`, which the CLI does not provide")
    return problems


SNAPSHOT_ARTEFACT_PATTERNS = ("__pycache__", ".pyc", ".pyo", ".lock", ".tmp", ".cache", ".log")


def snapshot_artefacts(snapshot_root: Path) -> list[str]:
    """Anything a read-only command should never have created inside the pinned snapshot."""
    found = []
    for path in sorted(Path(snapshot_root).rglob("*")):
        rel = path.relative_to(snapshot_root).as_posix()
        if any(pat in rel for pat in SNAPSHOT_ARTEFACT_PATTERNS):
            found.append(rel)
    return found


def check_snapshot_write_safety(root: Path) -> list[str]:
    """PBG-FWK-013: an ordinary boot must not write into the pinned snapshot.

    Python writes __pycache__ beside any module it imports, so `python3 -m pbg.cli` mutates the
    framework directory merely by running. Measured in the behavioural fixture: a clean project
    became dirty, and every PL boot reported uncommitted changes -- inside pbg/, which ordinary
    work is not permitted to touch at all. `-B` suppresses it.
    """
    problems = []
    for rel, cmds in advertised_commands(root).items():
        text = (Path(root) / rel).read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if "pbg.cli" in line or "pbg/tools/pbg" in line:
                if "python3" in line and " -B" not in line and "PYTHONDONTWRITEBYTECODE" not in line:
                    problems.append(
                        f"{rel}: `{line.strip()}` would write bytecode into the pinned snapshot; "
                        f"use `python3 -B`")
    return problems
