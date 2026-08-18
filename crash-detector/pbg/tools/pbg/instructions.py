"""Project instruction resolution, bounded to PROJECT_ROOT (independent Assurance finding F21).

WHAT WAS ACTUALLY WRONG. Not a bad read — no read at all. No PBGv2 code has ever loaded a CLAUDE.md
as an instruction source, so the boundary was satisfied "by construction". That is a weaker
guarantee than it sounds, and the audit said so precisely: PBGv2 already ships a real defence in
`behavioural.harness.contamination_report()`, which walks parents for CLAUDE.md / AGENTS.md and
refuses to build a fixture below one — and it was applied ONLY to behavioural fixtures, never to the
framework's own root. Pointed at the framework's own working location it reports that a host file
one directory up would be inherited.

"By construction" is a claim about code that exists today. It is not a control, it cannot fail, and
it says nothing about the RUNTIME: both Claude Code and OpenCode walk upward for instruction files,
so an agent working in a project nested under a host doctrine file inherits governance the project
never declared, and a run that appears to follow project discipline because an unrelated parent
supplied it is worse than a failed run — it reads as a pass.

So this module does two separable things, and the separation is the point:

    resolve()     WHERE the project's own instructions come from. Exactly <PROJECT_ROOT>/CLAUDE.md.
                  No parent search, no host fallback, no ambient current-working-directory.

    inherited()   WHAT a runtime that walks upward would ALSO pick up. Named, with sizes, so the
                  condition is visible and actionable instead of advisory.

Neither grants anything. An instruction file confers no role and no authority (PBG-BOOT-001); that
is true of the project's own file as much as of a foreign one. What this module establishes is
which bytes are the project's, and which are the host's.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from . import evidence_resolution as er

#: INSIDE the package, so the classification cannot be separated from the code that applies it.
CONTROL_FILE_REGISTRY = ("data", "project-control-files.yaml")

AUTHORITATIVE = "AUTHORITATIVE"
ADVISORY = "ADVISORY"
UNSUPPORTED = "UNSUPPORTED"
PROHIBITED = "PROHIBITED"


class ControlFileRegistryMissing(RuntimeError):
    """The registry ships with the package. Its absence is a refusal, not an empty default."""


def _registry_path() -> Path:
    return Path(__file__).resolve().parent.joinpath(*CONTROL_FILE_REGISTRY)


@lru_cache(maxsize=1)
def _registry_cached(path: str, mtime: float) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def control_file_registry() -> dict:
    path = _registry_path()
    try:
        return _registry_cached(str(path), path.stat().st_mtime)
    except OSError as exc:
        raise ControlFileRegistryMissing(
            f"the control-file registry {path} cannot be read ({exc}); the standing of a file at "
            "PROJECT_ROOT cannot be established and must not be assumed") from exc

#: The project's own instruction files, in preference order, read from PROJECT_ROOT and nowhere else.
#:
#: TWO names, not one. PBGv2 ships three adapters — claude-code installs CLAUDE.md, opencode and
#: generic install AGENTS.md — so a rule that recognised only CLAUDE.md would report every OpenCode
#: project as having no instructions at all, and would then have to be widened later by whoever hit
#: it. The boundary being enforced is "the project's own file, at PROJECT_ROOT"; the filename is the
#: runtime's business, not the boundary's.
PROJECT_INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md")

#: What an upward-walking runtime picks up. Necessarily the same set: a boundary that knows one
#: runtime's filename has a hole the size of the other runtime.
INHERITABLE_INSTRUCTION_FILES = PROJECT_INSTRUCTION_FILES

RESOLVED = "RESOLVED"
ABSENT = "ABSENT"
AMBIGUOUS_PROJECT_ROOT = "AMBIGUOUS_PROJECT_ROOT"
OUTSIDE_PROJECT_ROOT = "OUTSIDE_PROJECT_ROOT"


@dataclass(frozen=True)
class InstructionResolution:
    """Where project instructions came from, what would be inherited, and whether that is safe."""
    status: str
    path: Path | None
    detail: str
    inherited: list[str] = field(default_factory=list)
    #: A-5. Every OTHER recognised instruction file that also exists at PROJECT_ROOT. Previously
    #: CLAUDE.md won and AGENTS.md was never mentioned; a reader could not tell whether the second
    #: file had been merged, ignored, or never looked for.
    shadowed: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        return self.status == RESOLVED

    @property
    def contaminated(self) -> bool:
        """True when a runtime walking upward would inherit an instruction file we do not own."""
        return bool(self.inherited)

    def render(self) -> str:
        lines = [f"{self.status}: {self.detail}"]
        lines += [f"  - {f}" for f in self.findings]
        return "\n".join(lines)


def inherited(project_root: Path) -> list[str]:
    """Instruction files ABOVE PROJECT_ROOT that an upward-walking runtime would inherit.

    This is `harness.contamination_report` promoted out of the behavioural test harness and into the
    shipped package, so a consuming project gets it too. The harness kept it to itself; the finding
    is that the framework never ran it on the framework.
    """
    project_root = Path(project_root).resolve()
    found = []
    for parent in project_root.parents:
        for name in INHERITABLE_INSTRUCTION_FILES:
            candidate = parent / name
            if candidate.is_file():
                found.append(f"{candidate} ({candidate.stat().st_size} bytes) would be inherited")
    return found


def resolve(project_root: Path) -> InstructionResolution:
    """Resolve project instructions from exactly <PROJECT_ROOT>/CLAUDE.md, or say why not.

    Fails closed in every direction. An ambiguous PROJECT_ROOT is not resolved to "probably the
    parent"; a missing local file is not backfilled from the host; a symlink out of the tree is
    judged by where it lands, not by where it sits.
    """
    root = Path(project_root)

    if not root.exists():
        return InstructionResolution(
            AMBIGUOUS_PROJECT_ROOT, None,
            f"PROJECT_ROOT {root} does not exist; instruction resolution cannot proceed and is "
            "not attempted from any other location")
    if not root.is_dir():
        return InstructionResolution(
            AMBIGUOUS_PROJECT_ROOT, None,
            f"PROJECT_ROOT {root} is not a directory; PROJECT_ROOT is ambiguous and a boundary "
            "that cannot be located cannot be enforced")

    resolved_root = root.resolve()
    inherited_files = inherited(resolved_root)
    local = [resolved_root / name for name in PROJECT_INSTRUCTION_FILES
             if (resolved_root / name).is_file()]

    if not local:
        names = " or ".join(PROJECT_INSTRUCTION_FILES)
        return InstructionResolution(
            ABSENT, None,
            f"no {names} at PROJECT_ROOT {resolved_root}. No parent directory and no host location "
            "is consulted, so this project declares no instructions"
            + (f"; note that {len(inherited_files)} instruction file(s) above it would be "
               "inherited by a runtime that walks upward" if inherited_files else ""),
            inherited_files)

    candidate = local[0]
    shadowed = [p.name for p in local[1:]]
    findings = []
    if shadowed:
        # A-5. Both names are recognised, one is selected, and the other used to vanish. Saying so is
        # the whole repair: a project with two instruction files should learn that from the tool
        # rather than from an agent that read the one the tool did not.
        findings.append(
            f"instruction sources: {candidate.name} is selected at PROJECT_ROOT; "
            f"{', '.join(shadowed)} also exist(s) there and are NOT read. Both names are ADVISORY "
            "and neither grants anything (PBG-BOOT-001), so this changes no authority — but a "
            "second control-like file that nobody reads and nobody mentions is the defect class, "
            "not its severity")

    # A symlinked CLAUDE.md pointing out of the tree is the host's file wearing the project's name.
    try:
        candidate.resolve().relative_to(resolved_root)
    except ValueError:
        return InstructionResolution(
            OUTSIDE_PROJECT_ROOT, candidate,
            f"{candidate} resolves to {candidate.resolve()}, outside PROJECT_ROOT {resolved_root}. "
            "A project's instructions are part of the project; a link out of the tree is host "
            "doctrine under a local name. Refused.",
            inherited_files, shadowed, findings)

    return InstructionResolution(
        RESOLVED, candidate, f"project instructions read from {candidate}", inherited_files,
        shadowed, findings)


# --------------------------------------------------------------------------------------------- #
# A-5: what every control-like root file IS, and whether it was consumed
# --------------------------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ControlFileStanding:
    """One declared root file: its classification, whether it is here, and what was done with it."""
    name: str
    classification: str
    present: bool
    consumed: bool
    locations: tuple = ()
    note: str = ""

    #: What each classification MEANS when the file is present, in the words a reader needs.
    DISPOSITION = {
        AUTHORITATIVE: "READ, and its content changes framework behaviour",
        ADVISORY: "LOCATED and reported; it grants nothing and decides nothing (PBG-BOOT-001)",
        UNSUPPORTED: "NOT read by any PBG code path; it changes nothing",
        PROHIBITED: "NEVER permitted to influence behaviour",
    }

    def render(self) -> str:
        where = f" at {', '.join(self.locations)}" if self.locations else ""
        state = "present" if self.present else "absent"
        return (f"{self.name}: {self.classification}, {state}{where} — "
                f"{self.DISPOSITION.get(self.classification, 'NOT read by PBG')}")


def classify_control_files(project_root: Path) -> list[ControlFileStanding]:
    """Every declared control-like root file, classified and reported (A-5).

    Reported whether present or absent. An UNSUPPORTED file that exists must be named precisely so
    it cannot APPEAR to be consumed, and a classification a reader can only discover by reading the
    source is not a disclosure.
    """
    root = Path(project_root)
    registry = control_file_registry().get("files") or {}
    standing: list[ControlFileStanding] = []
    for name, rule in sorted(registry.items()):
        locations = tuple(rule.get("permitted_locations") or [])
        present_at = tuple(loc for loc in (locations or (name,)) if (root / loc).is_file())
        classification = str(rule.get("classification") or UNSUPPORTED)
        consumed = bool(present_at) and classification == AUTHORITATIVE
        standing.append(ControlFileStanding(
            name, classification, bool(present_at), consumed, present_at,
            str(rule.get("note") or "").strip()))
    return standing


def shadowed_control_files(project_root: Path) -> list[str]:
    """Declared files whose permitted locations are multiply occupied, named rather than ignored."""
    root = Path(project_root)
    registry = control_file_registry().get("files") or {}
    findings: list[str] = []
    for name, rule in sorted(registry.items()):
        locations = tuple(rule.get("permitted_locations") or ())
        if len(locations) < 2:
            continue
        found = er.resolve_canonical_file(name, root, locations)
        findings += found.findings
    return findings
