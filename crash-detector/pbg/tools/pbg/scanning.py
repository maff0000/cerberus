"""Evidence scanning and wrapper classification.

Implements:
  PBG-EVID-003 / PBG-EVID-004 — no secret material in code, evidence, records or documentation.
  PBG-FWK-004 — project-local wrappers around framework tooling are reported and classified.

The secret scanner never prints a matched secret. It reports the pattern class and location only
— an evidence scanner that logs what it found has become the leak.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------------------------- #
# Secrets
# --------------------------------------------------------------------------------------------- #

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key_block", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{24,}={0,2}")),
    ("url_embedded_credentials", re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/:@]+:[^\s/@]+@")),
    ("connection_string_password", re.compile(r"(?i)\b(?:password|pwd)\s*=\s*[^\s;'\"]{4,}")),
    ("assigned_secret", re.compile(
        r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    )),
)

#: Applied ONLY to files that are env files by name. The shape `NAME=value` is unremarkable in
#: source code — an early draft of this scanner flagged every Python constant in its own
#: implementation, which is a false-positive generator, and a scanner nobody trusts gets muted.
ENV_VALUE_PATTERN = re.compile(r"(?m)^\s*[A-Z][A-Z0-9_]{2,}\s*=\s*\S{8,}\s*$")

#: Explicit, greppable exemption for a line that must contain secret-SHAPED material — a test
#: fixture, or documentation of what a secret looks like. Exemptions are marked, never implicit.
# ------------------------------------------------------------------------------------------------
# DECLARED THREAT MODEL — what this scanner does and does not claim.
#
# CLAIMS TO DETECT
#   Recognised credential SHAPES in text the framework governs: private-key blocks, URLs with
#   embedded credentials, provider key formats, and values in files that are env files by name.
#   It reports CLASS and LOCATION only, never the matched value (PBG-EVID-003, non-waivable).
#
# DOES NOT CLAIM TO DETECT
#   - a secret with no recognisable shape: a bare password, a random token in a generic string
#   - base64, hex, gzip or otherwise encoded material. NO decoding is attempted, so an encoded
#     secret passes. Stated plainly because the alternative is a scanner that implies coverage
#     it does not have.
#   - secrets in binary files, images or anything that fails a UTF-8 read
#   - secrets split across lines: matching is line-by-line by construction
#   - secrets in files outside the scanned tree, in Git history, or already pushed
#   - whether a detected credential is live, rotated or revoked
#
# It is a LAST-LINE HYGIENE CHECK, not a guarantee. A clean scan means no recognised shape was
# found in the current tree. It is not evidence that no secret is present, and must never be
# reported as such.
# ------------------------------------------------------------------------------------------------

FIXTURE_EXEMPTION = re.compile(r"pbg:allow-secret-fixture")

#: The marker suppresses ONLY when it stands on its own line -- comment punctuation and whitespace
#: around it, nothing else. A trailing marker appended to a line of code suppresses nothing.
#:
#: independent Assurance finding F-11. Three bypasses, all from matching the marker anywhere on a line:
#:   1. trailing marker hid a live credential on that line;
#:   2. any line MENTIONING a placeholder word ("not an EXAMPLE, this is live") was skipped whole;
#:   3. worst -- a trailing marker anywhere in the first ten lines exempted the ENTIRE file, so one
#:      appended comment silently disabled scanning for everything below it.
#: Hiding a secret now requires inserting a deliberate standalone line directly above it, which is
#: visible as an intent in review rather than invisible at the end of a line someone already reads
#: as code.
_OWN_LINE_MARKER = re.compile(r"^[\s#/*;<!-]*pbg:allow-secret-fixture[\s#*/>-]*$")

#: Whole-file exemption needs a DISTINCT token, so the line-level marker can never widen into one.
#: My first attempt at this fix reused the same marker for both, and an own-line marker on line 2
#: silently exempted a live credential on line 4 -- the exact adjacency masking the repair was
#: supposed to prevent. It must be a deliberate, differently-spelled header, placed before any code.
_FILE_MARKER = re.compile(r"^[\s#/*;<!-]*pbg:allow-secret-fixture-file[\s#*/>-]*$")

#: Placeholder shapes that are not secrets. A governance framework must be able to document
#: what a secret looks like without tripping its own scanner.
_PLACEHOLDER = re.compile(
    r"(?i)(REDACTED|EXAMPLE|PLACEHOLDER|CHANGE[_-]?ME|YOUR[_-]|<[^>]+>|\$\{[^}]+\}|xxx+|\*\*\*+|"
    r"dummy|sample|\bfake\b|\bnoop\b|localhost\.invalid)"
)

#: Files that legitimately name variables without values.
SECRET_SCAN_SKIP = (".env.example", "SECURITY.md")


@dataclass(frozen=True)
class SecretFinding:
    path: str
    line: int
    pattern: str  # the CLASS of secret, never the matched text

    def render(self) -> str:
        return f"{self.path}:{self.line}: possible {self.pattern} (value not shown)"


def scan_secrets(root: Path, paths: list[Path] | None = None) -> list[SecretFinding]:
    """Scan for secret material. Returns classes and locations, never values."""
    findings: list[SecretFinding] = []
    targets = paths if paths is not None else _text_files(root)
    for path in targets:
        if path.name in SECRET_SCAN_SKIP:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix() if path.is_absolute() else path.as_posix()
        is_env_file = path.name.startswith(".env") or path.suffix == ".env"

        lines = text.splitlines()

        # Whole-file exemption: a distinct header token, on its own line, before any code.
        file_exempt = False
        for candidate in lines[:5]:
            if _FILE_MARKER.match(candidate):
                file_exempt = True
                break
            if candidate.strip() and not candidate.lstrip().startswith(("#", "//", "/*", "*", "<!--")):
                break   # code has started; a header marker below this point is not a header

        # Line exemption: an own-line marker suppresses the line immediately BELOW it.
        suppressed_next = {i + 2 for i, l in enumerate(lines) if _OWN_LINE_MARKER.match(l)}

        for lineno, line in enumerate(lines, start=1):
            if file_exempt or lineno in suppressed_next or _OWN_LINE_MARKER.match(line):
                continue
            matched = None
            for name, pattern in SECRET_PATTERNS:
                hit = pattern.search(line)
                if hit:
                    # The placeholder test applies to the MATCHED VALUE, not the whole line.
                    # Otherwise a real credential is hidden by the word "example" appearing
                    # anywhere else on the line.
                    if _PLACEHOLDER.search(hit.group(0)):
                        continue
                    matched = name
                    break
            if matched is None and is_env_file:
                hit = ENV_VALUE_PATTERN.search(line)
                if hit and not _PLACEHOLDER.search(hit.group(0)):
                    matched = "env_file_content"
            if matched:
                findings.append(SecretFinding(path=rel, line=lineno, pattern=matched))
    return findings


def check_env_files(root: Path) -> list[str]:
    """A committed .env is a finding regardless of content (PBG-EVID-004)."""
    hits = []
    for path in root.rglob(".env*"):
        if path.name in (".env.example", ".env.sample", ".env.template"):
            continue
        if ".git/" in path.as_posix():
            continue
        hits.append(path.relative_to(root).as_posix())
    return sorted(hits)


# --------------------------------------------------------------------------------------------- #
# Framework identity — PBG-FWK-013
# --------------------------------------------------------------------------------------------- #

#: Marker files that make a directory a candidate framework root.
_FRAMEWORK_MARKERS = ("VERSION", "manifest.yaml")


def find_framework_root(path: Path, stop_at: Path | None = None) -> Path | None:
    """Walk up for an enclosing framework root. Candidate only — identity is proven separately."""
    current = path if path.is_dir() else path.parent
    for candidate in [current, *current.parents]:
        if all((candidate / m).is_file() for m in _FRAMEWORK_MARKERS) and (candidate / "controls").is_dir():
            return candidate
        if stop_at is not None and candidate == stop_at:
            break
    return None


def is_framework_owned(path: Path, validating_root: Path) -> bool:
    """Is this file authentic framework content?

    Two ways to be framework-owned, both evidence-based:

    1. It is inside an INSTALLED framework snapshot and its SHA-256 appears in that snapshot's
       INTEGRITY manifest. A file added to, or altered inside, a pinned snapshot fails this — which
       is the point: a tampered snapshot must not exempt itself.
    2. It is a module of the framework SOURCE TREE currently being validated. Here there is no
       installed manifest, because this tree IS the framework.

    A directory merely named "pbg/" satisfies neither.
    """
    fw_root = find_framework_root(path)
    if fw_root is None:
        return False

    integrity = fw_root / "INTEGRITY"
    if integrity.is_file():
        # The manifest itself must be vouched for, or a hostile manifest could simply bless
        # whatever it liked. PROVENANCE.json carries sha256(INTEGRITY) as `integrity_digest`,
        # written at build time from the canonical tree. It is NOT distribution_digest, which
        # vouches for the RELEASE_MANIFEST -- comparing against that was the defect that made
        # every shipped distribution report its own modules as project wrappers.
        if not _manifest_is_vouched(fw_root, integrity):
            return False

        try:
            resolved = path.resolve()
            rel = resolved.relative_to(fw_root.resolve()).as_posix()
        except ValueError:
            # The path escapes the framework root — a symlink out, or traversal. Not owned.
            return False
        if rel == "INTEGRITY":
            return True

        want = _digest(path)
        matches = [
            line.partition("  ")
            for line in integrity.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        found = [digest for digest, _, name in matches if name == rel]
        if len(found) != 1:
            # Absent, or listed more than once. A duplicate entry lets one line contradict
            # another, so the manifest no longer states a single fact about this file.
            return False
        return found[0] == want                               # tampered content is NOT exempt

    # No INTEGRITY manifest: only the tree under validation may claim source identity.
    return fw_root.resolve() == validating_root.resolve()


def _manifest_is_vouched(fw_root: Path, integrity: Path) -> bool:
    """Does an independent record vouch for this integrity manifest?

    Without this, `is_framework_owned` reduces to "the manifest says so", and a hostile snapshot
    would author its own exemption. PROVENANCE.json is written by the distribution builder from
    the canonical tree and records sha256(INTEGRITY) as `integrity_digest`.

    It previously read `distribution_digest`, which vouches for the RELEASE_MANIFEST and is a
    different value. The comparison therefore failed in EVERY shipped distribution, no file was
    framework-owned, and the classifier treated framework modules as project wrappers -- including
    scanning.py, which contains the bypass vocabulary it searches for and so matched itself.

    This is not unbreakable — an attacker who rewrites both files defeats it — but it removes the
    single-file forgery, and a mismatch between the two is a signal a project can act on.
    """
    provenance = fw_root / "PROVENANCE.json"
    if not provenance.is_file():
        return False
    try:
        record = json.loads(provenance.read_text(encoding="utf-8"))
        declared = record.get("integrity_digest") or ""
        if not declared:
            # A distribution built before integrity_digest existed cannot vouch for its manifest.
            # Fail closed rather than fall back to a field that vouches for something else.
            return False
    except (json.JSONDecodeError, OSError):
        return False
    actual = "sha256:" + hashlib.sha256(integrity.read_bytes()).hexdigest()
    return declared == actual


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# --------------------------------------------------------------------------------------------- #
# Wrapper classification — PBG-FWK-004
# --------------------------------------------------------------------------------------------- #

ADAPTER_DECLARED = "ADAPTER_DECLARED"
COMPATIBILITY_SMELL = "COMPATIBILITY_SMELL"
CONTROL_TRANSFORMATION = "CONTROL_TRANSFORMATION"
CONTROL_BYPASS = "CONTROL_BYPASS"

WRAPPER_SEVERITY = {
    ADAPTER_DECLARED: "INFO",
    COMPATIBILITY_SMELL: "WARN",
    CONTROL_TRANSFORMATION: "AMBER",
    CONTROL_BYPASS: "RED",
}

#: Invocation of framework tooling from a project-local script.
_INVOKES_FRAMEWORK_TOOL = re.compile(r"(?i)\b(pbg_close|pbg[_ -]?validate|pbg\.py|\bpbg\b\s+(close|validate|verify|status|boot))")

#: Rewriting the state the control is about to read.
_TRANSFORM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("rewrites_commit_dates", re.compile(r"GIT_(?:AUTHOR|COMMITTER)_DATE\s*=")),
    ("synthesises_upstream", re.compile(r"(?i)set-upstream-to|git\s+init\s+(?:-q\s+)?--bare")),
    ("copies_into_expected_layout", re.compile(r"(?i)mktemp\s+-d.*|cp\s+-a\s+.*docs/(work_orders|audit|evidence)")),
)

#: Supplying the answer the control was meant to determine.
#: These must catch the shapes a real adapter uses — a terminal status passed as an argument, a
#: sed/awk rewrite, a helper named for the act — not only a literal `status: GREEN` line.
_BYPASS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("rewrites_status_to_pass", re.compile(
        r"(?i)"
        r"status\s*[:=]\s*[\"']?(?:GREEN|CLOSED|DONE|PASS)\b"          # status: GREEN
        r"|_?(?:re)?write[_-]?status\b[^\n]*?(?:GREEN|CLOSED|DONE|PASS)\b"  # helper "CLOSED"
        r"|\bSTATUS\s*=\s*[\"']?(?:GREEN|CLOSED|DONE|PASS)\b"          # STATUS=GREEN
    )),
    ("normalises_verdict", re.compile(
        r"(?i)_rewrite_status|normalise\w*[_ ]?verdict|sed[^\n]*status[^\n]*(GREEN|CLOSED)"
    )),
)


@dataclass(frozen=True)
class WrapperFinding:
    path: str
    classification: str
    severity: str
    signals: list[str]

    def render(self) -> str:
        sig = ", ".join(self.signals) if self.signals else "invokes framework tooling"
        return f"[{self.severity}] {self.path}: {self.classification} ({sig})"


def classify_wrappers(root: Path, declared_adapters: list[str] | None = None) -> list[WrapperFinding]:
    """Find and classify project-local wrappers around framework tooling.

    Not every wrapper is a defect. Severity depends on whether it maps an interface or changes
    the semantic state being validated.
    """
    declared = set(declared_adapters or [])
    findings: list[WrapperFinding] = []

    for path in _text_files(root, suffixes=(".sh", ".bash", ".py", ".mk", "")):
        rel = path.relative_to(root).as_posix()
        # Framework-owned files are not project wrappers. Recognition is by VERIFIED IDENTITY,
        # never by path: a hostile or merely project-local script placed in a directory named
        # "pbg/" would otherwise exempt itself from the check designed to catch it. A file is
        # framework-owned only where its digest appears in an enclosing framework's INTEGRITY
        # manifest, or it is a source-tree module of the framework being validated.
        if is_framework_owned(path, root) or rel.startswith("tests/") or "/tests/" in rel:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not _INVOKES_FRAMEWORK_TOOL.search(text):
            continue

        signals: list[str] = []
        classification = ADAPTER_DECLARED if rel in declared else COMPATIBILITY_SMELL

        for name, pattern in _TRANSFORM_PATTERNS:
            if pattern.search(text):
                signals.append(name)
                classification = CONTROL_TRANSFORMATION
        for name, pattern in _BYPASS_PATTERNS:
            if pattern.search(text):
                signals.append(name)
                classification = CONTROL_BYPASS

        findings.append(
            WrapperFinding(
                path=rel,
                classification=classification,
                severity=WRAPPER_SEVERITY[classification],
                signals=signals,
            )
        )
    return findings


# --------------------------------------------------------------------------------------------- #

_TEXT_SUFFIXES = (".md", ".yaml", ".yml", ".json", ".py", ".sh", ".bash", ".toml", ".cfg", ".txt", "")
#: Build outputs are copies of the tree, not independent content. Scanning them double-reports
#: every finding and — worse — re-detects the framework's own implementation as if it were a
#: project artefact.
_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv", "dist", "build"}


def _text_files(root: Path, suffixes: tuple[str, ...] = _TEXT_SUFFIXES) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in suffixes:
            out.append(path)
    return sorted(out)
