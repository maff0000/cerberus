"""Two roots, two types (independent Assurance finding N3).

THE DEFECT. One value did two jobs. `_framework_root()` walks up from `cli.py` looking for
`VERSION` + `controls/` — which is the right way to locate the CODE — and the result was then used as
PROJECT_ROOT as well. In a consuming project that vendors PBG at `<project>/pbg`, the framework root
is `<project>/pbg`, so:

    PBG-BOOT-001   evaluated the project's instruction boundary at <project>/pbg, and told a
                   correctly-adopted project that its OWN CLAUDE.md "would be inherited" as foreign
    PBG-CTRL-004   looked for <project>/pbg/pbg-manifest.yaml and reported ABSENT while
                   <project>/pbg-manifest.yaml sat there being ignored

and `--root <project>` was not a workaround, because the framework checks then failed with
"canonical VERSION not found", exit 4. The documented QUICKSTART command produced both symptoms.

THE DOCTRINE. PROJECT_ROOT is the governed CONSUMING PROJECT root. It is never the internal directory
containing the vendored implementation. The framework source root is a different thing with a
different job, and they are now different fields that cannot be swapped by accident.

WHAT THIS MODULE MUST NOT DO. It must not resolve the project root by searching UPWARD for project
markers. F19 and F21 exist because upward search is the defect: a project that inherits governance
from a parent directory has no boundary at all. So the project root is derived STRUCTURALLY from a
recognised layout, or supplied explicitly, or the situation is AMBIGUOUS and fails closed. There is
no third option and no fallback.

Locating the framework by walking up from `__file__` is NOT that defect and is retained: it finds the
code that is already executing, in the tree it was imported from. It reads no governance and inherits
no instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

#: Where a consuming project may vendor the framework, relative to the project root. Declared, not
#: guessed, and deliberately shallow: a deeper location is not refused, it is AMBIGUOUS and must be
#: resolved by the operator with an explicit root.
VENDOR_LOCATIONS = ("pbg", "governance/pbg")

#: Files that make a directory recognisable as a governed project rather than an arbitrary parent.
#: A vendor directory alone is NOT one of them — `<anything>/pbg` existing proves nothing about
#: `<anything>`.
PROJECT_MARKERS = ("PID.md", "CLAUDE.md", "AGENTS.md", "pbg-manifest.yaml",
                   "governance/pbg-installation.yaml", "governance/authority")

RESOLVED = "RESOLVED"
AMBIGUOUS = "AMBIGUOUS"

CANONICAL_SOURCE = "CANONICAL_FRAMEWORK_SOURCE"
VENDORED = "VENDORED"
SUPPLIED = "SUPPLIED"


@dataclass(frozen=True)
class Roots:
    """The governed project root and the framework source root, never interchangeable."""
    status: str
    project_root: Path | None
    framework_root: Path | None
    layout: str = ""
    detail: str = ""

    @property
    def resolved(self) -> bool:
        return self.status == RESOLVED and self.project_root is not None

    @property
    def vendored(self) -> bool:
        return self.layout == VENDORED

    def render(self) -> str:
        return "\n".join([
            f"  governed project root  {self.project_root or '<unresolved>'}",
            f"  framework source root  {self.framework_root or '<unresolved>'}",
            f"  layout                 {self.layout or self.status}",
        ])


def is_framework(path: Path) -> bool:
    """A directory holding the framework implementation."""
    return (path / "VERSION").is_file() and (path / "controls").is_dir()


def is_canonical_source(path: Path) -> bool:
    """The repository PBG is BUILT in, as opposed to a snapshot a project consumes."""
    return is_framework(path) and (path / "tests").is_dir() and (path / "docs").is_dir()


def has_project_markers(path: Path) -> bool:
    return any((path / marker).exists() for marker in PROJECT_MARKERS)


def find_framework_root(start: Path | None = None) -> Path | None:
    """Locate the executing framework by walking up from this module.

    This finds CODE, not governance. It reads no instruction file, resolves no manifest, and cannot
    make one project inherit another's rules.
    """
    here = (start or Path(__file__).resolve()).resolve()
    for candidate in [here, *here.parents]:
        if is_framework(candidate):
            return candidate
    return None


def framework_within(project_root: Path) -> Path | None:
    """The framework a project vendors, at a DECLARED location inside it."""
    project_root = Path(project_root)
    if is_framework(project_root):
        return project_root
    for location in VENDOR_LOCATIONS:
        candidate = project_root / location
        if is_framework(candidate):
            return candidate
    return None


def resolve(explicit_root: Path | None = None, *, start: Path | None = None) -> Roots:
    """Resolve both roots, or refuse and say what would disambiguate it.

    `explicit_root` is the `--root` flag and always names the GOVERNED PROJECT root — which is what
    made `--root <project>` fail before: it was taken as the framework root, and a project has no
    VERSION.
    """
    if explicit_root is not None:
        project_root = Path(explicit_root).resolve()
        if not project_root.is_dir():
            return Roots(AMBIGUOUS, None, None, SUPPLIED,
                         f"--root {project_root} is not a directory; a project root that cannot be "
                         "located cannot be governed")
        framework = framework_within(project_root) or find_framework_root(start)
        if framework is None:
            return Roots(AMBIGUOUS, project_root, None, SUPPLIED,
                         f"no framework implementation found inside {project_root} (looked for "
                         f"{', '.join(VENDOR_LOCATIONS)}) and none could be located from the "
                         "executing module")
        layout = CANONICAL_SOURCE if framework == project_root else VENDORED
        return Roots(RESOLVED, project_root, framework, layout,
                     f"project root supplied explicitly; framework resolved at {framework}")

    framework = find_framework_root(start)
    if framework is None:
        return Roots(AMBIGUOUS, None, None, "",
                     "no framework implementation could be located from the executing module")

    # The canonical repository IS the project. There is nothing above it to govern.
    if is_canonical_source(framework):
        return Roots(RESOLVED, framework, framework, CANONICAL_SOURCE,
                     "this is the canonical framework repository; project root and framework source "
                     "root are the same directory")

    # Each declared vendor location has a known DEPTH, so the project root it implies is a fixed
    # number of levels up — computed, not searched. `governance/pbg` is two levels, `pbg` is one.
    for location in VENDOR_LOCATIONS:
        depth = len(Path(location).parts)
        if len(framework.parents) < depth:
            continue
        candidate = framework.parents[depth - 1]
        if framework_within(candidate) == framework and has_project_markers(candidate):
            return Roots(RESOLVED, candidate, framework, VENDORED,
                         f"framework vendored at {location}/ inside the governed project {candidate}")

    parent = framework.parent

    # Everything else is genuinely ambiguous, and guessing is how upward inheritance gets
    # reintroduced by the back door. Refuse, and say exactly what would settle it.
    return Roots(
        AMBIGUOUS, None, framework, "",
        f"the framework is at {framework}, and which directory it governs cannot be determined "
        f"structurally — {parent} carries none of the project markers "
        f"({', '.join(PROJECT_MARKERS)}). No parent directory is searched, because upward search is "
        "the defect F19 and F21 exist to prevent. Supply --root <project> to state it.")
