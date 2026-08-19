#!/usr/bin/env python3
"""CD-RT-003-ENGINE-NO-WITNESS-REACH — the engine cannot reach witness code, transitively.

    python3 tools/register/check_engine_no_witness_reach.py --root <subject tree>

CRITERION: CD-AC-003, "witnesses are side-by-side, never ingredients" (PID §6). PID doctrine
§3.4: a witness that is also an ingredient corroborates nothing. BLUEPRINT §13 requires that
"nothing reachable from src/crash_detector/engine/ reaches witness code".

The separation is held in TWO independent places, and this check is one of them. The other
is the store, where ``cd_engine`` holds no privilege of any kind on schema ``witness`` —
that is CD-RT-003-GRANT-MATRIX-LIVE, and it is a different instrument reading a different
substrate. Either alone would be a single point of failure for the product's most
consequential separation.

-------------------------------------------------------------------------------------------
WHAT CHANGED, AND WHY. THIS CHECK WAS DEFEATED AND THE REPAIR IS STRUCTURAL. CD-ASR-F05.
-------------------------------------------------------------------------------------------
An independent auditor (CD-ASR-WO2-01) appended ``from crash_detector.witness.panel import
Agrees`` to ``deploy/entrypoints/cd_engine.py`` — THE MODULE THAT IS THE ENGINE CONTAINER'S
PROCESS — and this check exited 0, PASS, 13 assertions, 0 violations, reproduced by this seat
at ``ba469b5`` before anything was repaired.

THE DEFECT WAS A MISMATCH OF SUBJECTS, NOT A MISSED SPELLING. The guard's subject was the
engine PACKAGE: it rooted its walk at the CONSTANT ``crash_detector.engine`` and scanned only
``src/crash_detector/``. The criterion's subject is the engine CONTAINER. ``cd_engine.py`` is
shipped into that container by ``COPY deploy/entrypoints/ /app/entrypoints/`` and started by
``ENTRYPOINT ["python3", "-B", "/app/entrypoints/cd_engine.py"]``, and it was outside both the
walk root and the scanned universe. No amount of extra import-route recognition would have
found it, because the file was never read.

THE REPAIR IS NOT "ALSO SCAN deploy/entrypoints/". That would be a second hard-coded path, and
the next escape is a third one — an entrypoint moved, renamed, overridden in compose, declared
through a YAML anchor, or pointed at a module in ``src/`` that is not under ``engine/``. The
structure is DERIVATION: the guard reads WHAT THE ENGINE CONTAINER ACTUALLY STARTS and roots
the walk there, and reads WHAT THE ENGINE IMAGE ACTUALLY SHIPS and scans that. Change the
artefact and the guard's subject follows; there is no constant in this file naming an
entrypoint path, and there cannot be one.

This is the same move CD-RT-012-EGRESS-NO-BROKER already makes for its service set, where the
Project Lead measured ``scanned: 7 -> 8`` by adding an eighth service (PL-S1, PL-T1). Here the
equivalent measurement is: change ``ENTRYPOINT`` and watch the derived root move with it.

-------------------------------------------------------------------------------------------
THE ROOT SET IS A UNION, AND THAT IS DELIBERATE
-------------------------------------------------------------------------------------------
    roots = the modules started by the declared process of EVERY CONTAINER BUILT FROM THE
            ENGINE'S IMAGE (DERIVED — CD-ENGINE-ROOT-001 and CD-ENGINE-ROOT-004)
          ∪ every module in the engine package ``src/crash_detector/engine/`` (BLUEPRINT §13)

NEITHER IS A SUPERSET OF THE OTHER, and this is measured rather than assumed. In WO-2 the
engine container's process is ``cd_engine.py`` -> ``_service.py`` ->
``crash_detector.runtime.lifecycle``: it does NOT reach ``crash_detector.engine`` at all,
because the WO-2 services start, tick and shut down and evaluate nothing (there is no
registered ingredient source; CD-D-005 is owed). So REPLACING the package root with the
derived root would have deleted the guard that catches ``import crash_detector.witness`` in
``evaluate.py`` — the original plant, and the thing this check was built for. Widening the
root must not narrow the rules, so the package root stays and the derived root is added to it.

-------------------------------------------------------------------------------------------
WHAT IS ASSERTED
-------------------------------------------------------------------------------------------
 CD-ENGINE-ROOT-001  THE ROOT SET IS DERIVED FROM THE CONTAINER, NOT FROM A CONSTANT. The
                     engine service is located in ``deploy/compose.yaml``; the Dockerfile it
                     names is read; the effective process is ``entrypoint + command`` with
                     compose overriding the image (and a compose ``entrypoint`` cancelling the
                     image ``CMD``, as Compose itself does); every argument of that process
                     that names a Python module the image ships becomes a walk root.

 CD-ENGINE-ROOT-004  THE SUBJECT IS THE ENGINE *IMAGE*, NOT THE SERVICE *NAME*. Every service
                     in ``deploy/compose.yaml`` that builds the SAME build context from a
                     BYTE-IDENTICAL Dockerfile is an engine container whatever it is called,
                     and every one of them contributes walk roots and has its shipped files
                     scanned against ITS OWN declared sys.path roots. Added closing CD-PL-F62
                     — see declared limit 5, which this clause replaces the name match in.

 CD-ENGINE-ROOT-002  THE SCANNED UNIVERSE IS WHAT THE IMAGE SHIPS. The module map is built
                     from the Dockerfile's own ``COPY`` instructions — every ``*.py`` that
                     lands in the image — named against the sys.path roots the image itself
                     declares (``ENV PYTHONPATH``, or the compose ``environment`` value that
                     overrides it, plus the entry script's own directory, plus ``WORKDIR``
                     when ``-m`` is used). ``src/`` is ALSO mapped directly, because
                     BLUEPRINT §13's subject is the source tree and not only the image.

 CD-ENGINE-ROOT-003  IT FAILS CLOSED ON A DERIVATION IT CANNOT MAKE. Every step that cannot
                     be completed is a NON-ZERO exit with the reason and a stable clause id —
                     never an empty root set and never a pass. The clauses are enumerated
                     below. This is the posture the first auditor praised in the dynamic-import
                     arm — "correct design, not a lucky string match" — applied to the
                     derivation itself.

 CD-AC-003           NO MODULE IN THE REACHABLE SET IS WITNESS CODE. The walk is to fixpoint
                     from the union root set, and every route the previous cut caught is
                     caught unchanged and now over a strictly larger universe:

  * TRANSITIVE reach. The engine imports a helper; three modules later the helper's helper
    imports witness code. The engine still reaches it. This is why the walk is to fixpoint
    rather than one level deep, and it is the route a plant author actually uses.
  * RELATIVE imports. ``from .. import witness``, ``from ..witness import panel``, at any
    depth. Resolved against the importing module's package, not pattern-matched.
  * ALIASED imports. ``import crash_detector.witness as anything``, ``from
    crash_detector.witness import Agrees as A`` — the alias is irrelevant, the target is not.
  * ATTRIBUTE reach without an import of the submodule. A module that imports the top-level
    ``crash_detector`` package and then writes ``crash_detector.witness.panel`` has reached
    witness code without ever naming it in an import statement.
  * DYNAMIC import by string. ``importlib.import_module("crash_detector.witness.panel")``,
    ``__import__(...)``. A literal argument naming witness code is a violation. A NON-literal
    argument — ``import_module(name)`` — is ALSO a violation, because the check cannot
    follow it and an import route the guard cannot follow is a hole with a comment in it.
    Failing closed here is the whole point: the alternative is passing on ignorance.
  * A WITNESS MODULE PATH IN A STRING, anywhere in a scanned module — the payload of an
    indirection whose mechanism the check has not seen.

PRECONDITIONS, all of which REFUSE rather than pass (PBG-CI-002): the engine package must
exist and contain modules; the witness package must exist — "the engine does not reach
witness code" is vacuously true of a tree with no witness code, and vacuously true is not
true; and the reachable set must be non-trivial, so a check that resolved no imports at all
cannot report a clean graph.

-------------------------------------------------------------------------------------------
THE FAIL-CLOSED CLAUSES, EACH WITH A STABLE ID SO AN AUDITOR CAN ASSERT ON IT
-------------------------------------------------------------------------------------------
 CD-ENGINE-ROOT-101  ``deploy/compose.yaml`` is absent, unreadable, unparseable by the
                     stdlib-only reader, or declares no services.
 CD-ENGINE-ROOT-102  the engine service is not declared, or declares no ``build`` naming a
                     Dockerfile inside this tree. An image this tree does not build is an
                     image whose process this tree cannot derive.
 CD-ENGINE-ROOT-103  a YAML merge key (``<<``) in the engine service resolves to an anchor
                     this reader cannot locate, or to an anchor that is not declared at the
                     top level. A declaration the guard cannot see is not a declaration the
                     guard may assume is empty — an ``entrypoint:`` hidden in a shared anchor
                     is exactly the shape this clause exists for.
 CD-ENGINE-ROOT-104  the Dockerfile is absent, unreadable, or declares neither ENTRYPOINT nor
                     CMD.
 CD-ENGINE-ROOT-105  a ``COPY`` cannot be resolved statically: ``--from=`` another stage, a
                     glob, a shell variable, a source that does not exist in this tree, or a
                     source or destination escaping the build context.
 CD-ENGINE-ROOT-106  the declared process is in SHELL FORM. Docker runs shell form through
                     ``/bin/sh -c``, so what the container starts is decided by a shell at run
                     time and cannot be derived from the artefact. (``deploy/Dockerfile.engine``
                     already uses exec form, for the unrelated and correct reason that shell
                     form does not forward SIGTERM — and a test asserts it.)
 CD-ENGINE-ROOT-107  the process is not a Python interpreter this check can reason about, or
                     it names code at run time (``python -c``). Both are processes whose
                     imports are not in any file.
 CD-ENGINE-ROOT-108  the process names NO Python module the image ships. An empty root set is
                     the failure this clause exists to prevent: it would make every subsequent
                     assertion vacuously true.
 CD-ENGINE-ROOT-109  two different files claim one module name in the image. Which one the
                     interpreter imports depends on sys.path order, so the graph is ambiguous
                     and an ambiguous graph is not a clean one.
 CD-ENGINE-ROOT-110  the image ships a ``*.py`` that cannot be named as a module under any
                     sys.path root the image declares. Code the guard cannot place in the
                     import graph is code whose reach is unknown. It is NOT named by
                     guesswork: naming it by its basename would be inventing the run-time
                     ``sys.path`` mutation that would make that name real, and a guessed fact
                     is worse than a stated refusal.

-------------------------------------------------------------------------------------------
DECLARED LIMITS (CD-RULE-004). WHAT THIS CHECK DOES NOT DO.
-------------------------------------------------------------------------------------------
 1  IT IS A STATIC READ OF DECLARATIONS AT ONE COMMIT. No image is built and no container is
    started (RT-B is forbidden in WO-2). A compose OVERRIDE file, a ``docker run
    --entrypoint``, a ``docker exec`` into the running container, or an orchestrator
    manifest that is not ``deploy/compose.yaml`` are all outside the subject.
    NOT PROVED TO BE CARRIED ANYWHERE. The override surface is owed at WO-3 — the same
    residue CD-RT-012-EGRESS-NO-BROKER declares at its own boundary 6, for the same reason.

 2  A SECOND PROCESS STARTED BY THE APPLICATION AT RUN TIME — ``subprocess.Popen``,
    ``os.execv``, a thread pool importing on demand — is not an import edge and is not
    derived from any declaration.
    PARTIALLY CARRIED, MEASURED: if the module it starts is named as a STRING LITERAL in a
    scanned module and that string names witness code, the string-literal clause fires; and
    if it is reached through ``import_module`` with a non-literal argument, the dynamic-import
    clause fires. FOR A SECOND PROCESS NAMED BY A PATH THAT IS NOT A WITNESS PATH,
    NOT PROVED TO BE CARRIED ANYWHERE.

 3  IMPORTING WITNESS TYPES IS NOT READING WITNESS DATA, and this check does not claim
    otherwise. The auditor made that point about E06 itself. The data half of CD-AC-003 is
    CD-RT-003-GRANT-MATRIX-LIVE, which proves ``cd_engine`` holds no privilege of any kind on
    schema ``witness`` by any of seven routes, in a real PostgreSQL session. CARRIED, and it
    is a different instrument on a different substrate.

 4  THE COMPOSE READER IS A STDLIB-ONLY YAML SUBSET (``tools/register/_yamlmin.py``). A
    non-empty FLOW collection — ``entrypoint: ["python3", "/app/x.py"]`` — is not supported and
    raises, which this check turns into CD-ENGINE-ROOT-101, a refusal. That is fail-closed and
    not a pass, but it is a shape a legitimate author could write, so it is declared rather
    than left to be discovered. Write compose sequences in block form.
    That reader ALSO has a known non-termination defect on a block sequence opened by the
    first key of a block-sequence item (CD-ENG-WO2R-F14 / CD-PL-F61, ruled CD-D-051 to a
    separate bounded dispatch). This check shares it. NOT REPAIRED HERE and NOT IN SCOPE.

 5  THE WALK ROOTS ARE THE ENGINE CONTAINER SET, DERIVED BY IMAGE IDENTITY — AMENDED AT
    CD-D-055 CLOSING CD-PL-F62, AND THE PREVIOUS TEXT OF THIS BOUNDARY IS WHY.
    It used to read "ONLY THE ENGINE SERVICE'S PROCESS IS DERIVED AS A ROOT ... the other
    five services' entrypoints are RESOLVED but are not walk roots". That distinguished
    services BY PURPOSE in prose while the code distinguished BY NAME, so it did not
    contemplate a SECOND SERVICE BUILT FROM THE ENGINE'S OWN IMAGE, and an auditor reading it
    would not have expected that case to escape. It was INCOMPLETE rather than false.
    WHAT THE GUARD NOW DOES: every service that builds the same build context from a
    BYTE-IDENTICAL Dockerfile as ``cd-engine`` is an engine container whatever it is called
    (CD-ENGINE-ROOT-004), and its process is a walk root. Services built from a DIFFERENT
    image are RESOLVED only — each must name a module its image ships, so a rename or
    restructure that breaks the derivation is loud rather than silent — but they are not
    walk roots, and witness code reachable from ``cd-witness`` is correct rather than a
    violation.
    MEASURED, FOUR WAYS, EACH EXECUTABLE:
      * ``V42`` appends ``from crash_detector.witness.panel import Agrees`` to
        ``deploy/entrypoints/cd_witness.py``: exits 0, PASS 23. Not an escape; the criterion.
      * ``PL-U6b`` (governance/reconciliation/WO-2R/, re-recorded at
        ``variants/WO-2R/CD-PL-F62/``) adds a sixth service ``cd-engine-worker`` built from
        ``deploy/Dockerfile.engine`` whose entrypoint imports ``crash_detector.witness.panel``.
        At ``be34fe4`` it exited 0, PASS 24 — the escape CD-PL-F62 reports. HERE it exits 1,
        naming the route ``crash_detector.witness.panel <- cd_worker``.
      * ``V45`` adds a seventh service ``cd-engine-shadow`` from the same Dockerfile with a
        CLEAN entrypoint: exits 0, PASS 27, and the engine container set grows 1 -> 2 with the
        derived roots growing ``cd_engine`` -> ``cd_engine, cd_shadow``. THE SUBJECT FOLLOWS
        THE ARTEFACT, and a legitimate second engine container is not a violation.
      * ``V46`` copies ``Dockerfile.engine`` byte-for-byte to ``Dockerfile.engine-clone`` and
        builds ``cd-analytics`` from it, reaching witness through the top-level package:
        exits 1. The identity is the image's CONTENT, so renaming the file does not evade it.
    WHAT IS STILL OUTSIDE IT: a service built from a Dockerfile that is NOT byte-identical —
    a near-copy differing by one comment — is a different image by the artefact's own account
    and is not a walk root. Closing that would mean deciding when two different Dockerfiles
    "mean" the same image, which is a judgement and not a derivation.
    CARRIED, MEASURED BY THIS SEAT (CD-RULE-006): the container-set test layer asserts the
    declared service set by EQUALITY, so it refuses ANY service added to
    ``deploy/compose.yaml`` regardless of which image it builds. On the PL-U6b tree, at
    ``be34fe4``, this seat observed ``8 failed, 1184 passed``:
    ``tests/test_runtime_lifecycle.py::test_there_is_one_entrypoint_per_application_service``
    and seven in ``tests/test_deploy_container_set.py`` —
    ``test_all_seven_services_are_declared``,
    ``test_every_service_declares_a_non_root_user``,
    ``test_the_declared_uid_matches_the_machine_readable_one``,
    ``test_every_service_has_a_distinct_uid``,
    ``test_every_service_declares_its_three_storage_classes``,
    ``test_only_the_store_declares_durable_storage``,
    ``test_every_build_passes_the_base_image_through_as_a_required_variable`` — while the six
    other static register checks all exited 0. The carrier is the container-set TEST layer
    specifically, not the register.

 6  RUN-TIME ``sys.path`` MUTATION IS NOT DERIVED, AND THIS IS THE RESIDUE OF THE DERIVATION
    ITSELF, SO IT IS STATED PLAINLY. The naming half of the universe comes from the sys.path
    roots the ARTEFACTS declare (``ENV PYTHONPATH``, the compose ``environment``, the entry
    script's directory, ``WORKDIR`` under ``-m``). A module that inserts a directory into
    ``sys.path`` at run time makes a name importable that no declaration mentions, and the
    graph does not carry that name.
    MEASURED EXAMPLE (variant ``V44``): ``deploy/entrypoints/cd_engine.py`` inserts
    ``/app/src/crash_detector/witness`` into ``sys.path`` and then writes ``import panel``.
    ``panel.py`` IS scanned — it is in the universe, and it IS witness code — but the edge is
    spelled ``panel``, which resolves to no module in the graph, and this check exits 0,
    PASS 23 assertions, 0 violations.
    WHY IT IS NOT CLOSED, STATED SO THE ARGUMENT CAN BE JUDGED RATHER THAN ASSUMED: closing it
    means either refusing every ``sys.path`` mutation — which the clean tree itself contains,
    legitimately, in ``deploy/entrypoints/_service.py``, so the guard would fire on the
    product — or symbolically evaluating the inserted path, which is interpreting code the
    check has already said it will not follow. Neither is a bounded change to this increment
    and both are worse than a declared limit.
    PARTIALLY CARRIED, MEASURED: if the smuggled module is named by a DOTTED witness path in
    a string, or reached through ``import_module`` with a non-literal argument, the existing
    clauses fire — those arms are unchanged and still bite. CD-ENGINE-ROOT-110 also closes the
    neighbouring route of shipping code OFF the declared path entirely (variant ``V43``,
    refused, exit 3). BUT FOR A SHORT-NAME IMPORT OF ALREADY-SCANNED WITNESS CODE AFTER A
    ``sys.path`` INSERT, NOT PROVED TO BE CARRIED ANYWHERE. Raised against this seat's own
    work as CD-ENG-WO2R-F17 and owed beyond this increment.

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import posixpath
import re
import shlex
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, read_text, resolve_root  # noqa: E402
from _yamlmin import YamlSubsetError, load_yaml  # noqa: E402

CHECK_ID = "CD-RT-003-ENGINE-NO-WITNESS-REACH"

COMPOSE = "deploy/compose.yaml"

#: The service that ANCHORS the engine image. Named, so a rename is a visible edit — and its
#: ABSENCE is CD-ENGINE-ROOT-102, a refusal, never a pass. This is the same treatment
#: CD-RT-012-EGRESS-NO-BROKER gives its own named service set, for the same reason.
#:
#: IT IS AN ANCHOR AND NO LONGER A FILTER (CD-PL-F62). The walk root set is every service whose
#: build resolves to the SAME image as this one — same context, byte-identical Dockerfile —
#: because "the engine container" is a property of the image and not of the service name. A
#: name match here is what let `cd-engine-worker`, built from the engine's own Dockerfile,
#: escape at be34fe4.
ENGINE_SERVICE = "cd-engine"

#: Every service that builds from a Dockerfile in this tree has its process RESOLVED (declared
#: limit 5). Not named here: the set is read out of compose.
SOURCE_ROOT = "src"
PACKAGE = "crash_detector"
ENGINE_PACKAGE = "crash_detector.engine"
WITNESS_PACKAGE = "crash_detector.witness"

_INTERPRETER = re.compile(r"^python(\d+(\.\d+)?)?$")

#: Interpreter flags that consume the NEXT argument. Getting this wrong would make the check
#: read a flag's value as a script path, which is a wrong derivation and not a safe one.
_FLAGS_WITH_A_VALUE = frozenset({"-W", "-X", "--check-hash-based-pycs"})

_ANCHOR = re.compile(r"^(\s*)(\S+)\s*:\s*&(\S+)\s*$")

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DerivationRefused(Exception):
    """A step of the derivation could not be made. Carries its stable clause id."""

    def __init__(self, clause: str, reason: str) -> None:
        super().__init__(f"{clause}: {reason}")
        self.clause = clause
        self.reason = reason


def _refuse(clause: str, reason: str) -> "DerivationRefused":
    return DerivationRefused(clause, reason)


# --------------------------------------------------------------------------------------- #
# THE DOCKERFILE, READ AS INSTRUCTIONS
# --------------------------------------------------------------------------------------- #
def _instructions(text: str):
    """``[(line, INSTRUCTION, argument)]`` with comments dropped and continuations folded."""
    out = []
    buffer = ""
    start = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if not buffer and (not line.strip() or line.lstrip().startswith("#")):
            continue
        if not buffer:
            start = number
        if line.rstrip().endswith("\\"):
            buffer += line.rstrip()[:-1] + " "
            continue
        buffer += line
        stripped = buffer.strip()
        buffer = ""
        if not stripped:
            continue
        head, _, rest = stripped.partition(" ")
        out.append((start, head.upper(), rest.strip()))
    if buffer.strip():
        head, _, rest = buffer.strip().partition(" ")
        out.append((start, head.upper(), rest.strip()))
    return out


def _argv_of(argument: str, clause_owner: str):
    """``(form, argv)`` for an ENTRYPOINT or CMD argument.

    EXEC form is a JSON array and is derivable. SHELL form is handed to ``/bin/sh -c`` by
    Docker, so what the container starts is decided by a shell at run time — CD-ENGINE-ROOT-106.
    """
    text = argument.strip()
    if text.startswith("["):
        try:
            value = json.loads(text)
        except ValueError as exc:
            raise _refuse(
                "CD-ENGINE-ROOT-104",
                f"{clause_owner} is written as a JSON array that does not parse ({exc}), so "
                "the process this container starts cannot be read from the artefact.",
            ) from None
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise _refuse(
                "CD-ENGINE-ROOT-104",
                f"{clause_owner} is not a list of strings.",
            )
        return "exec", [str(x) for x in value]
    return "shell", [text]


def _env_pairs(argument: str) -> dict:
    """``ENV`` in either form: ``ENV k=v k2=v2`` or the legacy ``ENV k v``."""
    try:
        tokens = shlex.split(argument)
    except ValueError:
        return {}
    if tokens and "=" not in tokens[0]:
        return {tokens[0]: " ".join(tokens[1:])}
    pairs = {}
    for token in tokens:
        key, sign, value = token.partition("=")
        if sign:
            pairs[key] = value
    return pairs


class ImageDeclaration:
    """What one Dockerfile declares, read as data rather than as prose."""

    def __init__(self, path: pathlib.Path, context: pathlib.Path, text: str) -> None:
        self.path = path
        self.context = context
        self.copies = []          # [(line, [source tokens], destination, flags)]
        self.env = {}
        self.workdir = "/"
        self.entrypoint = None    # (form, argv, line)
        self.cmd = None
        for line, instruction, argument in _instructions(text):
            if instruction == "COPY" or instruction == "ADD":
                self._copy(line, instruction, argument)
            elif instruction == "ENV":
                self.env.update(_env_pairs(argument))
            elif instruction == "WORKDIR":
                self.workdir = argument.strip().strip('"')
            elif instruction == "ENTRYPOINT":
                self.entrypoint = _argv_of(argument, "ENTRYPOINT") + (line,)
            elif instruction == "CMD":
                self.cmd = _argv_of(argument, "CMD") + (line,)

    def _copy(self, line: int, instruction: str, argument: str) -> None:
        text = argument.strip()
        if text.startswith("["):
            try:
                tokens = json.loads(text)
            except ValueError:
                raise _refuse(
                    "CD-ENGINE-ROOT-105",
                    f"{self.path.name}:{line}: a {instruction} written as a JSON array does "
                    "not parse, so what the image ships cannot be derived.",
                ) from None
        else:
            tokens = shlex.split(text)
        flags = [t for t in tokens if t.startswith("--")]
        rest = [t for t in tokens if not t.startswith("--")]
        if len(rest) < 2:
            raise _refuse(
                "CD-ENGINE-ROOT-105",
                f"{self.path.name}:{line}: {instruction} names fewer than two operands.",
            )
        self.copies.append((line, rest[:-1], rest[-1], flags))


# --------------------------------------------------------------------------------------- #
# THE COMPOSE DECLARATION, WITH MERGE KEYS RESOLVED
# --------------------------------------------------------------------------------------- #
def _anchor_blocks(raw: str, document: dict) -> dict:
    """``{anchor name: mapping}`` for every anchor declared at the TOP LEVEL.

    An anchor declared deeper is recorded as unresolvable rather than guessed at: the reader
    does not track anchors, and a merge this check cannot see must refuse (CD-ENGINE-ROOT-103)
    rather than read as an empty contribution. That is the whole point — an ``entrypoint:``
    parked in a shared fragment is a declaration, and a guard that cannot see it must say so.
    """
    blocks = {}
    for line in raw.splitlines():
        match = _ANCHOR.match(line.rstrip())
        if not match:
            continue
        indent, key, name = match.group(1), match.group(2), match.group(3)
        if indent:
            blocks[name] = None
            continue
        blocks[name] = document.get(key)
    return blocks


def _merged(mapping, anchors: dict, seen=()):  # noqa: ANN001
    """``mapping`` with its ``<<`` merge keys resolved. Own keys win, as YAML specifies."""
    if not isinstance(mapping, dict):
        return mapping
    merge = mapping.get("<<")
    if merge is None:
        return {k: v for k, v in mapping.items() if k != "<<"}
    references = merge if isinstance(merge, list) else [merge]
    base = {}
    for reference in references:
        if not isinstance(reference, str) or not reference.startswith("*"):
            raise _refuse(
                "CD-ENGINE-ROOT-103",
                f"a merge key resolves to {reference!r}, which this reader cannot follow.",
            )
        name = reference[1:]
        if name in seen:
            raise _refuse(
                "CD-ENGINE-ROOT-103", f"the anchor `{name}` merges into itself."
            )
        if name not in anchors or anchors[name] is None:
            raise _refuse(
                "CD-ENGINE-ROOT-103",
                f"the merge key `<<: *{name}` names an anchor this reader cannot locate at "
                "the top level of the document. A declaration merged in from a fragment the "
                "guard cannot see is not a declaration the guard may assume is empty — an "
                "`entrypoint:` written there would replace the image's, unseen.",
            )
        base.update(_merged(anchors[name], anchors, tuple(seen) + (name,)))
    for key, value in mapping.items():
        if key != "<<":
            base[key] = value
    return base


def _as_argv(value, where: str):  # noqa: ANN001
    """A compose ``entrypoint:``/``command:`` as argv, list form or string form."""
    if value is None:
        return None
    if isinstance(value, list):
        if not all(isinstance(x, str) for x in value):
            raise _refuse(
                "CD-ENGINE-ROOT-107",
                f"compose `{where}` is a list containing a non-scalar entry.",
            )
        return [str(x) for x in value]
    if isinstance(value, str):
        try:
            return shlex.split(value)
        except ValueError as exc:
            raise _refuse(
                "CD-ENGINE-ROOT-107", f"compose `{where}` does not split as a command: {exc}"
            ) from None
    raise _refuse("CD-ENGINE-ROOT-107", f"compose `{where}` is not a command.")


# --------------------------------------------------------------------------------------- #
# WHAT THE IMAGE SHIPS
# --------------------------------------------------------------------------------------- #
def _shipped(root: pathlib.Path, image: ImageDeclaration) -> dict:
    """``{image path: repository path}`` for every ``*.py`` the Dockerfile COPYs in."""
    shipped = {}
    for line, sources, destination, flags in image.copies:
        for flag in flags:
            if flag.startswith("--from"):
                raise _refuse(
                    "CD-ENGINE-ROOT-105",
                    f"{image.path.name}:{line}: this COPY takes its source from another "
                    f"build stage ({flag}), which is not a path in this tree. What the image "
                    "ships cannot be derived from the repository alone.",
                )
        for token in sources:
            if any(character in token for character in "*?[$"):
                raise _refuse(
                    "CD-ENGINE-ROOT-105",
                    f"{image.path.name}:{line}: the COPY source {token!r} contains a glob or "
                    "a variable. This check resolves paths statically and refuses rather "
                    "than guessing which files a build would select.",
                )
            source = (image.context / token).resolve()
            try:
                source.relative_to(image.context.resolve())
            except ValueError:
                raise _refuse(
                    "CD-ENGINE-ROOT-105",
                    f"{image.path.name}:{line}: the COPY source {token!r} escapes the build "
                    "context.",
                ) from None
            if not source.exists():
                raise _refuse(
                    "CD-ENGINE-ROOT-105",
                    f"{image.path.name}:{line}: the COPY source {token!r} does not exist in "
                    "this subject tree, so the image's contents cannot be derived.",
                )
            if "$" in destination:
                raise _refuse(
                    "CD-ENGINE-ROOT-105",
                    f"{image.path.name}:{line}: the COPY destination {destination!r} "
                    "contains a variable.",
                )
            if source.is_dir():
                base = destination.rstrip("/") or "/"
                for path in sorted(source.rglob("*.py")):
                    if "__pycache__" in path.parts:
                        continue
                    relative = path.relative_to(source).as_posix()
                    shipped[posixpath.join(base, relative)] = path
            elif source.suffix == ".py":
                target = (
                    posixpath.join(destination, source.name)
                    if destination.endswith("/")
                    else destination
                )
                shipped[target] = source
    return shipped


def _module_name_from(image_path: str, roots) -> "str | None":
    """The dotted name ``image_path`` would import as, given the image's sys.path roots."""
    best = None
    for root in roots:
        prefix = root.rstrip("/") or "/"
        if prefix == "/":
            candidate = image_path.lstrip("/")
        elif image_path.startswith(prefix + "/"):
            candidate = image_path[len(prefix) + 1 :]
        else:
            continue
        if best is None or len(prefix) > len(best[0]):
            best = (prefix, candidate)
    if best is None:
        return None
    parts = best[1][:-3].split("/") if best[1].endswith(".py") else best[1].split("/")
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts or not all(_IDENTIFIER.match(part) for part in parts):
        return None
    return ".".join(parts)


# --------------------------------------------------------------------------------------- #
# THE DERIVATION
# --------------------------------------------------------------------------------------- #
class Derivation:
    """What one service's container starts, and what its image ships, derived from artefacts."""

    def __init__(self, service: str) -> None:
        self.service = service
        self.argv = []
        self.origin = ""
        self.shipped = {}
        self.path_roots = []
        self.entry_modules = []      # dotted names
        self.entry_files = {}        # dotted name -> repository path
        self.dockerfile = None
        self.context = None
        self.dockerfile_text = ""

    def image_identity(self) -> tuple:
        """WHICH IMAGE this service builds, as a property of the ARTEFACT, not of a name.

        Two services share an identity when they build the SAME build context from a
        BYTE-IDENTICAL Dockerfile. That covers the two spellings of the same image: the
        same ``dockerfile:`` path named twice, and a copy of that file under another name.
        It deliberately does NOT read the service name, because the name is exactly what
        CD-PL-F62 showed the guard must stop distinguishing by.
        """
        digest = hashlib.sha256(self.dockerfile_text.encode("utf-8")).hexdigest()
        return (str(self.context), digest)


def _derive(root: pathlib.Path, services: dict, anchors: dict, service: str) -> Derivation:
    """Derive ``service``'s process and shipped module set. Raises DerivationRefused."""
    derivation = Derivation(service)
    body = services.get(service)
    if not isinstance(body, dict):
        raise _refuse(
            "CD-ENGINE-ROOT-102",
            f"`{COMPOSE}` declares no service `{service}`. The subject of CD-AC-003 is that "
            "container, so with no such service there is no process to root the walk at, and "
            "an absent subject must never read as a clean one.",
        )
    body = _merged(body, anchors)

    build = body.get("build")
    if not isinstance(build, dict):
        raise _refuse(
            "CD-ENGINE-ROOT-102",
            f"service `{service}` declares no `build` section naming a Dockerfile in this "
            "tree, so what its container starts is not derivable from this repository.",
        )
    dockerfile_token = build.get("dockerfile")
    context_token = build.get("context") or "."
    if not isinstance(dockerfile_token, str) or not dockerfile_token:
        raise _refuse(
            "CD-ENGINE-ROOT-102",
            f"service `{service}` declares a build with no `dockerfile`.",
        )
    compose_dir = (root / COMPOSE).parent
    context = (compose_dir / str(context_token)).resolve()
    dockerfile = (context / dockerfile_token).resolve()
    for path, what in ((context, "build context"), (dockerfile, "dockerfile")):
        try:
            path.relative_to(root.resolve())
        except ValueError:
            raise _refuse(
                "CD-ENGINE-ROOT-102",
                f"service `{service}`'s {what} resolves outside the subject tree ({path}).",
            ) from None
    if not dockerfile.is_file():
        raise _refuse(
            "CD-ENGINE-ROOT-104",
            f"service `{service}` names `{dockerfile_token}`, which does not exist in this "
            "subject tree.",
        )
    try:
        text = dockerfile.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise _refuse(
            "CD-ENGINE-ROOT-104",
            f"`{dockerfile_token}` could not be read ({type(exc).__name__}: {exc}).",
        ) from None

    image = ImageDeclaration(dockerfile, context, text)
    derivation.dockerfile = dockerfile
    derivation.context = context
    derivation.dockerfile_text = text

    # -- the effective process ---------------------------------------------------------- #
    # Compose overrides the image, and a compose `entrypoint` CANCELS the image's CMD, which
    # is what Compose itself does. Read from the artefacts in that order, never assumed.
    compose_entrypoint = _as_argv(body.get("entrypoint"), "entrypoint")
    compose_command = _as_argv(body.get("command"), "command")

    if compose_entrypoint is not None:
        argv = list(compose_entrypoint)
        origin = f"{COMPOSE} services.{service}.entrypoint"
        if compose_command is not None:
            argv += compose_command
            origin += f" + services.{service}.command"
    else:
        if image.entrypoint is None and image.cmd is None:
            raise _refuse(
                "CD-ENGINE-ROOT-104",
                f"`{dockerfile_token}` declares neither ENTRYPOINT nor CMD, so the image "
                "declares no process at all.",
            )
        argv = []
        origin_parts = []
        if image.entrypoint is not None:
            form, tokens, line = image.entrypoint
            if form == "shell":
                raise _refuse(
                    "CD-ENGINE-ROOT-106",
                    f"`{dockerfile_token}`:{line} declares ENTRYPOINT in SHELL FORM. Docker "
                    "runs shell form through `/bin/sh -c`, so what the container starts is "
                    "decided by a shell at run time and is not derivable from the artefact. "
                    "This refuses rather than guessing, for the same reason the dynamic "
                    "import arm refuses an import it cannot follow.",
                )
            argv += tokens
            origin_parts.append(f"{dockerfile_token}:{line} ENTRYPOINT")
        if compose_command is not None:
            argv += compose_command
            origin_parts.append(f"{COMPOSE} services.{service}.command")
        elif image.cmd is not None:
            form, tokens, line = image.cmd
            if form == "shell":
                raise _refuse(
                    "CD-ENGINE-ROOT-106",
                    f"`{dockerfile_token}`:{line} declares CMD in SHELL FORM.",
                )
            argv += tokens
            origin_parts.append(f"{dockerfile_token}:{line} CMD")
        origin = " + ".join(origin_parts)

    derivation.argv = argv
    derivation.origin = origin
    if not argv:
        raise _refuse(
            "CD-ENGINE-ROOT-104", f"service `{service}` resolves to an empty command."
        )

    # -- what the image ships ----------------------------------------------------------- #
    derivation.shipped = _shipped(root, image)

    # -- the argv, read as an interpreter invocation ------------------------------------ #
    program = posixpath.basename(argv[0])
    if not _INTERPRETER.match(program):
        raise _refuse(
            "CD-ENGINE-ROOT-107",
            f"service `{service}` starts `{argv[0]}`, which this check does not recognise as "
            "a Python interpreter. The import graph of a process this check cannot read is "
            "unknown, and unknown is a refusal rather than a pass.",
        )

    script_tokens = []
    module_tokens = []
    index = 1
    while index < len(argv):
        token = argv[index]
        index += 1
        if token in _FLAGS_WITH_A_VALUE:
            index += 1
            continue
        if token == "-c":
            raise _refuse(
                "CD-ENGINE-ROOT-107",
                f"service `{service}` starts `python -c`, which names its code inline. There "
                "is no file whose imports this check could read.",
            )
        if token == "-m":
            if index >= len(argv):
                raise _refuse(
                    "CD-ENGINE-ROOT-107", f"service `{service}` ends with a bare `-m`."
                )
            module_tokens.append(argv[index])
            index += 1
            continue
        if token.startswith("-") and token != "-":
            continue
        script_tokens.append(token)

    # -- the sys.path roots the image itself declares ------------------------------------ #
    # compose `environment` overrides the image's ENV at run time, so it is read first.
    environment = body.get("environment")
    python_path = None
    if isinstance(environment, dict) and isinstance(environment.get("PYTHONPATH"), str):
        python_path = environment["PYTHONPATH"]
    elif isinstance(image.env.get("PYTHONPATH"), str):
        python_path = image.env["PYTHONPATH"]

    path_roots = []
    if python_path:
        path_roots += [p for p in python_path.split(":") if p]
    for token in script_tokens:
        if token in derivation.shipped:
            path_roots.append(posixpath.dirname(token) or "/")
    if module_tokens:
        path_roots.append(image.workdir or "/")
    # Order-preserving dedupe; the longest match wins when a name is computed.
    derivation.path_roots = list(dict.fromkeys(path_roots))

    # -- the roots ----------------------------------------------------------------------- #
    for token in script_tokens:
        if token not in derivation.shipped:
            continue
        name = _module_name_from(token, derivation.path_roots)
        if name is None:
            raise _refuse(
                "CD-ENGINE-ROOT-108",
                f"service `{service}` starts `{token}`, which the image ships but which "
                "cannot be named as a module under any sys.path root the image declares "
                f"({derivation.path_roots}).",
            )
        derivation.entry_modules.append(name)
        derivation.entry_files[name] = derivation.shipped[token]
    for name in module_tokens:
        derivation.entry_modules.append(name)

    if not derivation.entry_modules:
        raise _refuse(
            "CD-ENGINE-ROOT-108",
            f"service `{service}` starts `{' '.join(argv)}`, and NONE of its arguments names "
            "a Python module this image ships. The walk would have no root derived from the "
            "container, and an empty root set makes every assertion below it vacuously true. "
            "This is the failure this clause exists to prevent.",
        )
    return derivation


def _module_name(root: pathlib.Path, path: pathlib.Path) -> str:
    relative = path.relative_to(root / SOURCE_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _is_witness(module: str) -> bool:
    return module == WITNESS_PACKAGE or module.startswith(WITNESS_PACKAGE + ".")


def _resolve(module: str, is_package: bool, node: ast.ImportFrom) -> str:
    """Resolve a relative ``from .. import x`` against the importing module.

    The anchor differs for a package and a plain module, and getting it wrong is not a
    cosmetic error: for ``crash_detector.engine.model``, ``from ..witness import panel``
    resolves to ``crash_detector.witness``, and an off-by-one produces the non-existent
    ``crash_detector.engine.witness``, which resolves to nothing and reads as clean. That
    is exactly how this check passed variant IG-V3 on its first run — see CD-ENG-F27.

    For a package (``__init__.py``) level 1 is the package itself; for a plain module
    level 1 is its containing package.
    """
    if not node.level:
        return node.module or ""
    parts = module.split(".")
    anchor = parts if is_package else parts[:-1]
    keep = len(anchor) - (node.level - 1)
    if keep < 0:
        return ""
    base = anchor[:keep]
    if node.module:
        base = base + node.module.split(".")
    return ".".join(base)


class ModuleImports:
    """The edges out of one module, plus the reach routes that are not import edges."""

    def __init__(
        self, check: Check, path: pathlib.Path, module: str, tree: ast.AST
    ) -> None:
        self.check = check
        self.path = path
        self.module = module
        self.is_package = path.name == "__init__.py"
        self.targets: set = set()
        self.local_package_names: set = set()
        self._collect(tree)

    def _add(self, dotted: str) -> None:
        if dotted:
            self.targets.add(dotted)

    def _collect(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._add(alias.name)
                    if alias.name == PACKAGE:
                        self.local_package_names.add(alias.asname or PACKAGE)
            elif isinstance(node, ast.ImportFrom):
                base = _resolve(self.module, self.is_package, node)
                self._add(base)
                for alias in node.names:
                    # `from crash_detector import witness` is an import of the SUBMODULE.
                    self._add(f"{base}.{alias.name}" if base else alias.name)
                    if base == PACKAGE and alias.name == PACKAGE:
                        self.local_package_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Call):
                self._collect_dynamic(node)

        # Attribute reach: `crash_detector.witness...` where only the package was imported.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            base = node.value
            if isinstance(base, ast.Name) and base.id in self.local_package_names:
                self._add(f"{PACKAGE}.{node.attr}")

        # A witness module path carried as a string, in a module the engine can reach.
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if _is_witness(node.value.strip()):
                    self.check.violation(
                        self.path,
                        node.lineno,
                        "witness module path in a string literal",
                        f'the string "{node.value}" names witness code inside a module '
                        "the engine can reach. Whatever consumes it, the payload of an "
                        "indirection is a route, and a route the import graph cannot see "
                        "is the one worth reporting.",
                    )

    def _collect_dynamic(self, node: ast.Call) -> None:
        name = (
            node.func.attr
            if isinstance(node.func, ast.Attribute)
            else node.func.id if isinstance(node.func, ast.Name) else ""
        )
        if name not in {"import_module", "__import__", "find_spec", "load_module"}:
            return
        if not node.args:
            return
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            self._add(first.value)
            return
        self.check.violation(
            self.path,
            node.lineno,
            "dynamic import the graph cannot follow",
            f"`{ast.unparse(node)[:120]}` imports a module named at run time. This check "
            "cannot follow it, so it cannot establish that the engine does not reach "
            "witness code through it. An import route the guard cannot follow is a hole "
            "with a comment in it, and this fails closed rather than passing on ignorance.",
        )


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    package_dir = root / SOURCE_ROOT / PACKAGE.replace(".", "/")
    engine_dir = root / SOURCE_ROOT / ENGINE_PACKAGE.replace(".", "/")
    witness_dir = root / SOURCE_ROOT / WITNESS_PACKAGE.replace(".", "/")
    if not package_dir.is_dir():
        return check.refuse(f"{package_dir} does not exist in this subject tree.")
    if not engine_dir.is_dir():
        return check.refuse(
            f"{engine_dir} does not exist. There is no engine package to walk out from, "
            "so 'the engine reaches nothing' would be a statement about nothing."
        )
    if not witness_dir.is_dir():
        return check.refuse(
            f"{witness_dir} does not exist. 'The engine does not reach witness code' is "
            "VACUOUSLY true of a tree with no witness code, and vacuously true is not "
            "true. A guard that passes because its subject was deleted is the failure "
            "this refusal exists to prevent."
        )

    # -- CD-ENGINE-ROOT-001: read what the container actually starts --------------------- #
    compose_path = root / COMPOSE
    if not compose_path.is_file():
        return check.refuse(
            f"CD-ENGINE-ROOT-101: {COMPOSE} does not exist in this subject tree. The walk "
            "root is DERIVED from the engine container's own declaration, so with no "
            "declaration there is no derivable subject. This check will not fall back to a "
            "hard-coded path: falling back to a constant is the defect CD-ASR-F05 reported."
        )
    try:
        document = load_yaml(compose_path)
    except YamlSubsetError as exc:
        return check.refuse(
            f"CD-ENGINE-ROOT-101: {COMPOSE} could not be parsed by this reader: {exc}. A "
            "declaration the check cannot read is a declaration the check cannot derive a "
            "subject from. It refuses rather than guessing."
        )
    services = document.get("services")
    if not isinstance(services, dict) or not services:
        return check.refuse(f"CD-ENGINE-ROOT-101: {COMPOSE} declares no services.")

    try:
        raw_compose = compose_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return check.refuse(f"CD-ENGINE-ROOT-101: {COMPOSE} is unreadable: {exc}.")
    anchors = _anchor_blocks(raw_compose, document)

    check.asserted()  # CD-ENGINE-ROOT-001, the engine container's process is derivable
    try:
        engine = _derive(root, services, anchors, ENGINE_SERVICE)
    except DerivationRefused as exc:
        return check.refuse(
            f"{exc.clause}: {exc.reason}\n    The walk root is DERIVED from the engine "
            "container's declaration and this derivation could not be made. That is a "
            "non-zero exit with a stated reason, never an empty root set and never a pass "
            "(CD-ENGINE-ROOT-003, PBG-CI-002)."
        )

    # -- CD-ENGINE-ROOT-004: THE ENGINE CONTAINER SET, BY IMAGE AND NOT BY NAME ---------- #
    # Every buildable service is derived. Those that build the ENGINE'S OWN IMAGE — same
    # build context, byte-identical Dockerfile — are engine containers whatever they are
    # called, and every one of them contributes walk roots. The rest are RESOLVED only, so
    # a rename or a restructure that breaks the derivation is loud rather than silent.
    #
    # This replaces a name match on `cd-engine`, which was CD-PL-F62: a sixth service
    # `cd-engine-worker` built from deploy/Dockerfile.engine, whose entrypoint imported
    # crash_detector.witness.panel, exited 0 at PASS 24 because only the literally-named
    # service became a root.
    engine_identity = engine.image_identity()
    engine_containers = {}       # service -> Derivation, engine image, WALK ROOTS
    resolved_elsewhere = {}      # service -> Derivation, resolved but NOT a walk root
    for name in sorted(services):
        if name == ENGINE_SERVICE:
            continue
        body = services.get(name)
        if not isinstance(body, dict):
            continue
        try:
            merged = _merged(body, anchors)
        except DerivationRefused as exc:
            return check.refuse(
                f"{exc.clause}: service `{name}`: {exc.reason} A merge the guard cannot "
                "follow is refused wherever it appears, not only on the engine."
            )
        if not isinstance(merged.get("build"), dict):
            continue  # an external image; nothing in this tree declares its process
        check.asserted()
        try:
            derived = _derive(root, services, anchors, name)
        except DerivationRefused as exc:
            return check.refuse(
                f"{exc.clause}: service `{name}` builds from this tree but its process does "
                f"not resolve: {exc.reason}\n    Every service built here must resolve, so a "
                "rename or a restructure that breaks the derivation is loud rather than "
                "silent. The engine's own derivation is only trustworthy if the machinery "
                "that makes it works on every service in the file."
            )
        if derived.image_identity() == engine_identity:
            engine_containers[name] = derived
        else:
            resolved_elsewhere[name] = derived

    #: The engine service first, then every other container built from the engine's image.
    #: This is the set whose processes are walk roots and whose shipped files are scanned.
    engine_set = [engine] + [engine_containers[name] for name in sorted(engine_containers)]

    # -- CD-ENGINE-ROOT-002: the universe is what the image ships ------------------------ #
    modules: dict = {}
    conflicts: list = []

    def _place(name: str, path: pathlib.Path) -> None:
        previous = modules.get(name)
        if previous is not None and previous != path:
            conflicts.append((name, previous, path))
            return
        modules[name] = path

    # (a) the source tree, named as BLUEPRINT §13 names it. This arm does not depend on any
    #     container declaration, so a Dockerfile edit can never remove it.
    for path in sorted((root / SOURCE_ROOT).rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        name = _module_name(root, path)
        if name:
            _place(name, path)

    # (b) everything the engine image ships, named against the sys.path roots the image
    #     declares. A shipped file that CANNOT be named under any declared sys.path root is
    #     CD-ENGINE-ROOT-110, a refusal: the image carries Python the guard cannot place in
    #     the import graph, and unplaceable code is a hole in exactly the sense the
    #     dynamic-import clause already refuses. It is deliberately NOT named by guesswork —
    #     naming it by its basename would be inventing the sys.path mutation that would make
    #     that name real, and a guessed fact is worse than a stated refusal.
    #     This runs over EVERY container in the engine set, each named against ITS OWN
    #     declared sys.path roots — a second service may override PYTHONPATH in compose even
    #     when it builds the identical image, so borrowing the engine service's roots would
    #     be assuming a fact rather than reading one.
    for container in engine_set:
        for image_path, repository_path in sorted(container.shipped.items()):
            name = _module_name_from(image_path, container.path_roots)
            if name is None:
                return check.refuse(
                    "CD-ENGINE-ROOT-110: the engine image, as built by service "
                    f"`{container.service}`, ships `{image_path}` "
                    f"({repository_path.relative_to(root) if repository_path.is_relative_to(root) else repository_path}), "
                    "which cannot be named as a module under any sys.path root that "
                    f"container declares ({', '.join(container.path_roots) or 'none'}). "
                    "Python shipped into the container that this check cannot place in the "
                    "import graph is code whose reach is unknown, and unknown is a refusal "
                    "rather than a pass. Put it on a declared path, or do not ship it."
                )
            _place(name, repository_path)

    if conflicts:
        first = conflicts[0]
        return check.refuse(
            f"CD-ENGINE-ROOT-109: the module name `{first[0]}` is claimed by two different "
            f"files ({first[1]} and {first[2]}), and by {len(conflicts)} name(s) in total. "
            "Which one the interpreter imports depends on sys.path order, so the import "
            "graph is ambiguous — and an ambiguous graph is not a clean one."
        )

    # -- the union root set --------------------------------------------------------------#
    package_roots = sorted(
        name
        for name in modules
        if name == ENGINE_PACKAGE or name.startswith(ENGINE_PACKAGE + ".")
    )
    if not package_roots:
        return check.refuse("the engine package contains no Python modules.")

    derived_roots = []
    for container in engine_set:
        if container is not engine:
            # CD-ENGINE-ROOT-004: a second container built from the engine's image is an
            # engine container, and its process is a walk root. Asserted per container so
            # the count follows the artefact rather than being fixed at one.
            check.asserted()
        for name in container.entry_modules:
            if name in modules:
                derived_roots.append(name)
                continue
            return check.refuse(
                f"CD-ENGINE-ROOT-108: engine container `{container.service}` starts "
                f"`{name}`, which is not a module in the scanned universe. The process the "
                "criterion is about would be walked from nothing."
            )
    derived_roots = sorted(set(derived_roots))

    check.asserted()  # CD-ENGINE-ROOT-002, the derived roots are inside the scanned universe
    roots = sorted(set(package_roots) | set(derived_roots))

    edges: dict = {}
    for name, path in modules.items():
        source = read_text(check, path)
        if source is None:
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            check.violation(
                path,
                exc.lineno or 0,
                "UNPARSEABLE",
                f"this application module could not be parsed ({exc.msg}), so its import "
                "edges are unknown. Unknown edges are a failure, never a pass.",
            )
            continue
        edges[name] = ModuleImports(check, path, name, tree)

    # -- walk to fixpoint -------------------------------------------------------------- #
    reached: dict = {name: (name, 0) for name in roots}
    frontier = list(roots)
    while frontier:
        current = frontier.pop()
        node = edges.get(current)
        if node is None:
            continue
        for target in sorted(node.targets):
            # Only project modules are edges. A stdlib or third-party import is not a
            # route to witness code, and following it would need the whole environment.
            candidate = target
            while candidate and candidate not in modules:
                if "." not in candidate:
                    candidate = ""
                    break
                candidate = candidate.rsplit(".", 1)[0]
            if not candidate:
                if _is_witness(target):
                    check.violation(
                        node.path,
                        0,
                        "engine reaches witness code",
                        f"`{current}` imports `{target}`, which is witness code that does "
                        "not exist as a module in this tree. The reach is real whether or "
                        "not the target resolves.",
                    )
                continue
            if candidate not in reached:
                reached[candidate] = (current, reached[current][1] + 1)
                frontier.append(candidate)

    check.asserted(len(reached))
    if len(reached) < 2:
        return check.refuse(
            f"only {len(reached)} module(s) were reached from the engine package. The "
            "import graph resolved to almost nothing, which means the walk failed rather "
            "than that the graph is clean."
        )

    # -- the assertion ----------------------------------------------------------------- #
    check.asserted()
    for name in sorted(reached):
        if not _is_witness(name):
            continue
        trail = [name]
        cursor = name
        while reached[cursor][0] != cursor and len(trail) < 20:
            cursor = reached[cursor][0]
            trail.append(cursor)
        check.violation(
            modules.get(name, root),
            0,
            "engine reaches witness code",
            "witness module `"
            + name
            + "` is REACHABLE from the engine container's root set. Route (nearest first): "
            + " <- ".join(trail)
            + ". CD-AC-003: witnesses are side-by-side, never ingredients. A witness that "
            "is also an ingredient corroborates nothing (PID §3.4).",
        )

    witness_modules = sorted(name for name in modules if _is_witness(name))
    check.note(
        f"{len(witness_modules)} witness module(s) exist and were the subject of the "
        f"assertion: {', '.join(witness_modules)}"
    )
    check.note(
        "the ENGINE CONTAINER SET, derived by IMAGE IDENTITY and not by service name "
        f"(build context + byte-identical Dockerfile): {len(engine_set)} service(s) — "
        + ", ".join(
            f"{c.service} [{c.origin}: {' '.join(c.argv)}]" for c in engine_set
        )
    )
    check.note(
        "derived walk root(s) from the engine container set: "
        + (", ".join(derived_roots) or "(none)")
        + "; sys.path roots inside the image(s): "
        + "; ".join(
            f"{c.service}={', '.join(c.path_roots) or '(none)'}" for c in engine_set
        )
    )
    check.note(
        f"package walk root(s) from BLUEPRINT §13: {len(package_roots)} module(s) under "
        f"{ENGINE_PACKAGE}"
    )
    check.note(
        f"{sum(len(c.shipped) for c in engine_set)} Python file(s) shipped into the engine "
        "image(s) by their own COPY instructions, every one of them named and placed in "
        "the graph"
    )
    if resolved_elsewhere:
        check.note(
            "services built from a DIFFERENT image in this tree, entrypoint RESOLVED but "
            "not a walk root: "
            + ", ".join(
                f"{name}={'/'.join(sorted(d.entry_modules))}"
                for name, d in sorted(resolved_elsewhere.items())
            )
        )

    return check.done(
        f"{len(modules)} modules in the scanned universe; {len(reached)} reachable "
        f"from {len(roots)} root(s) — {len(package_roots)} engine-package, "
        f"{len(derived_roots)} derived from {len(engine_set)} engine container(s) — "
        "walked to fixpoint"
    )


if __name__ == "__main__":
    raise SystemExit(main())
