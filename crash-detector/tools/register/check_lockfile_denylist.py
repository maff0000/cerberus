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

-------------------------------------------------------------------------------------------
WHAT CHANGED, AND WHY. THIS CHECK WAS DEFEATED AND THE REPAIR IS STRUCTURAL.
-------------------------------------------------------------------------------------------
CD-ASR-WO2R-F05 (MEDIUM). An independent auditor (CD-ASR-WO2-02) put
``tastytrade-sdk==1.2.0`` — a REAL, currently-operating US brokerage's REAL order-entry SDK —
into ``requirements.txt`` AND ``requirements.lock``, and this check exited 0: PASS, 17
assertions, 0 violations. REPLICATED BY CD-ENG-WO2R2-02 at the AUDITED tree ``50fc231``
before anything was repaired, with the auditor's own controls in the same batch:

    clean                         exit 0  PASS — 15 assertions, 0 violations
    tastytrade-sdk==1.2.0         exit 0  PASS — 17 assertions, 0 violations   ESCAPED
    meridian-fix-connect==0.4.1   exit 1  FAIL — 2 violation(s)                CAUGHT
    lattice-client==2.0.0         exit 0  PASS — 17 assertions, 0 violations   ESCAPED

It recognised brokers BY NAME — a 61-name denylist plus nine execution tokens matched as
WORDS — and ``tastytrade`` is one word that is not an execution token. The brand defeated it.

THE REPAIR IS NOT A LONGER DENYLIST. Adding ``tastytrade`` would recognise one more NAME, and
the next name is Robinhood, Webull, Tradier, Schwab, a brokerage founded next year, or a brand
sharing no morpheme with anything financial. A longer list is the instance game with more
instances. The structure is DENY BY DEFAULT over a declared, in-tree dependency registry:
a distribution is admissible only if somebody REGISTERED that exact normalised name.
``tastytrade-sdk`` then stops being a name to catch and is simply not a dependency anyone
declared — the same thing a typosquat, a renamed fork and a brand invented tomorrow all are.
THIS CHECK PERFORMS NO RECOGNITION ON AN UNREGISTERED DISTRIBUTION, so there is no pattern to
write around.

RESOLUTION IS PROHIBITED, DELIBERATELY (CD-PL-F48, and the dispatch in terms). Deciding
whether an arbitrary package can reach a broker is undecidable offline, and a check whose
verdict depends on PyPI or DNS is not reproducible, cannot be run offline by an auditor and
therefore cannot be a gate. What a distribution IS gets decided from data in the tree and from
nothing else. THIS CHECK OPENS NO SOCKET.

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

and ``deploy/dependency-registry.yaml`` — the declared registry, read with the stdlib-only
YAML subset reader. A comment is not a permission, because a comment cannot be read by the
thing that has to refuse.

WHAT IS ASSERTED
-----------------
 CD-DEP-001  LAYER 1, DENY BY DEFAULT. Every distribution named in every manifest is, after
             PEP 503 normalisation, the ``distribution`` of a registered entry. An
             unregistered distribution is a violation and NOTHING IS RECOGNISED ABOUT IT.

 CD-DEP-002  LAYER 2, SURVIVING. Every REGISTERED distribution is still judged by the broker
             denylist in ``_broker_vocabulary.py`` and by the execution-token rule, so a
             distribution somebody DOES register is still judged: ``ib-insync`` fails on the
             denylist and ``meridian-fix-connect`` fails on the ``fix`` token. The same
             judgement is applied at the manifest site as well, so a violation is reported
             where a reader will look for it. NEITHER LAYER IS SOLE.

 CD-DEP-003  SET EQUALITY RUNS BOTH WAYS. A registered distribution appearing in NO manifest
             is a violation. Without this the registry accumulates permissions nobody uses,
             and — worse — the manifest line a complaint names could be deleted to silence
             the guard. Equality in both directions means the entry that complains cannot be
             made to stop complaining by removing something.

 CD-DEP-004  THE REGISTRY DOCUMENT'S KEY SET IS CLOSED, its ``contract`` is the one this
             check knows, ``consumers`` is a non-empty list of unique names and
             ``dependencies`` is a list. A key the guard does not read is a declaration
             nothing enforces.

 CD-DEP-005  EVERY ENTRY DECLARES EXACTLY THE SIX KEYS — ``id``, ``distribution``, ``kind``,
             ``purpose``, ``declared_in``, ``needed_by`` — with a unique ``id``, a
             ``distribution`` ALREADY IN PEP 503 NORMAL FORM (so one distribution cannot be
             registered twice under two spellings), a ``kind`` of DIRECT or TRANSITIVE, and a
             non-empty ``needed_by`` drawn entirely from ``consumers``.
             A MALFORMED ENTRY REGISTERS NOTHING — otherwise the cheapest bypass would be to
             register a broker SDK in an entry deliberately broken enough to be skipped.

PRECONDITIONS THAT REFUSE (PBG-CI-002): a missing ``pyproject.toml``, ``requirements.txt`` or
``requirements.lock`` is a non-zero exit — a dependency surface that cannot be read has not
been shown to be clean. So is a manifest from which zero distributions were extracted: that
means the parse failed, not that the file is empty of brokers. So is a MISSING OR UNPARSEABLE
REGISTRY, and so is a registry carrying an unresolved YAML alias: an absent registry must not
read as an empty one, because an empty registry is a decision somebody wrote down and an
absent one is a file somebody removed, and treating the second as the first would make
deleting a file the cheapest bypass there is.

===========================================================================================
DECLARED LIMIT (CD-RULE-004). Stated identically here, in ``required-tests.yaml`` and in
``contracts/execution/CD-RT-012-LOCKFILE-DENYLIST.md``. Each hand-off names a layer that was
MEASURED or says NOT PROVED TO BE CARRIED ANYWHERE (CD-RULE-006).

THIS CHECK'S SCOPE IS `DECLARED_SURFACE`, NOT `CLASS`, AND THE REGISTER NOW SAYS SO. It closes
the class of UNDECLARED dependency — which is what CD-ASR-WO2R-F05 exercised — and it does NOT
close the class of "a dependency that can reach a broker", which is not decidable from this
tree at all. Before this rework the register declared `scope: CLASS`, and an auditor relying on
it was told the class was closed. It was not, and that mis-declaration is the half of F05 that
CD-RULE-004 actually prohibits.
===========================================================================================
 1  A REGISTERED DISTRIBUTION IS A HUMAN CLAIM AND A FALSE ONE IS NOT DETECTABLE HERE. If a
    person registers a distribution whose code in fact reaches a broker — under a name the
    denylist does not hold and carrying no execution token — layer 1 admits it because it is
    registered and layer 2 clears it because it is not recognisable. EXECUTABLE EXAMPLE: add
    to ``requirements.txt`` and ``requirements.lock`` a line ``quiet-market-client==1.0.0``
    AND a matching six-key entry in ``deploy/dependency-registry.yaml``; this check exits 0.
    That is the residue, stated rather than papered over: what the structure buys is that the
    claim must be WRITTEN DOWN, given a purpose, cited to a clause, attributed to a consuming
    surface and reviewed by a person at a named line — not that it is true.
    CARRIED BY: no layer in this repository judges the TRUTH of a registered purpose.
    NOT PROVED TO BE CARRIED ANYWHERE.

 2  ``purpose`` AND ``declared_in`` ARE NOT JUDGED FOR CONTENT. The guard asserts they are
    present and non-empty. It does not and cannot decide whether the English is honest or
    whether the cited clause says what the entry claims it says. A purpose reading "market
    data for the equity dial" on a distribution that is an order-entry SDK is refused by
    layer 2 IF the name is recognisable, and by nothing at all if it is not.
    NOT PROVED TO BE CARRIED ANYWHERE.

 3  THIS IS A STATIC READ OF DECLARED MANIFESTS AT ONE COMMIT. It does not read the installed
    environment, ``site-packages``, a vendored directory, a git submodule, a wheel committed
    into the tree, a ``pip install`` in a Dockerfile RUN line, or anything a container image
    brings with it. A broker SDK VENDORED AS SOURCE under ``src/`` is not a dependency and
    never appears in a manifest. MEASURED: this check reads exactly the three required
    manifests plus any ``requirements*.txt`` / ``*.lock`` / ``constraints*.txt`` glob match,
    and its own output names every manifest it read.
    CARRIED BY, AND MEASURED: ``CD-RT-012-NO-EXECUTION-INTERFACE`` reads ``.py`` and ``.sql``
    under ``src/``, ``db/``, ``deploy/``, ``tests/`` and ``tools/``, so vendored SOURCE is in
    ITS subject set — measured at this SHA, exit 0 over 42812 assertions on the clean tree.
    ITS OWN six declared boundaries apply and are not restated here. FOR A BROKER SDK
    ARRIVING AS A COMPILED WHEEL OR INSIDE A BASE IMAGE, NOT PROVED TO BE CARRIED ANYWHERE.

 4  A DEPENDENCY IS PERMISSION TO IMPORT, NOT A PATHWAY. The auditor's own mitigation
    reasoning, and it is the reason F05 is MEDIUM and not HIGH. The pathway needs somewhere to
    go. CARRIER MEASURED BY THIS SEAT ON ITS OWN EXTRACTION, not transcribed from the
    auditor's numbers (CD-RULE-006): ``deploy/egress-destinations.yaml`` declares
    ``destinations: []`` — the admissible set is EMPTY, 0 registered destinations — and every
    service's ``x-egress.hosts`` in ``deploy/compose.yaml`` is empty, with
    ``CD-RT-012-EGRESS-NO-BROKER`` exiting 0 over 69 assertions.
    ITS SCOPE, STATED HONESTLY: it carries the PATHWAY and NOT the DEPENDENCY. It says nothing
    about what may be imported; it says there is nowhere registered to send anything. AND IT
    IS A WO-2-STATE FACT THAT WO-3 WILL CHANGE — the lane that makes ALLOWLIST mean more than
    NONE is owed at WO-3, and the moment a destination is registered this carrier weakens by
    exactly that much. It is not a permanent property and must not be read as one.

 5  THE REGISTRY IS AN IN-TREE FILE AND A COMMIT MAY EDIT IT. Registering a broker SDK is a
    two-line diff: the manifest line and the registry entry. That is the SAME residue the
    egress destination registry carries and it is the deliberate design — the structure makes
    the permission EXPLICIT, ATTRIBUTED AND REVIEWABLE AT A NAMED LINE, not unforgeable. What
    it removes is the SILENT admission, which is what F05 exercised: ``tastytrade-sdk`` needed
    no registry edit and produced no diff anyone had to justify.
    CARRIED BY, AND MEASURED: layer 2 over the registry itself — a registered ``ib-insync``
    is refused by CD-DEP-002 and a registered ``meridian-fix-connect`` by the token rule, both
    measured. FOR A REGISTERED DISTRIBUTION LAYER 2 DOES NOT RECOGNISE, see boundary 1:
    NOT PROVED TO BE CARRIED ANYWHERE.

DO NOT read a clean run of this check as proof that no dependency of this project can reach a
broker. Read it as proof of exactly three things: that every distribution in every declared
manifest was REGISTERED by somebody, with a purpose and a cited clause; that no registered or
manifest distribution is on the denylist or carries an execution token; and that the registry
holds no permission that no manifest uses. It is NOT proof about boundaries 1, 2 or 5.
===========================================================================================

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
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
from _yamlmin import (  # noqa: E402
    YamlSubsetError,
    line_of,
    load_yaml,
    unresolved_aliases,
)

CHECK_ID = "CD-RT-012-LOCKFILE-DENYLIST"

REQUIRED_MANIFESTS = ("pyproject.toml", "requirements.txt", "requirements.lock")

EXTRA_PATTERNS = ("requirements*.txt", "*.lock", "constraints*.txt")

REGISTRY = "deploy/dependency-registry.yaml"

REGISTRY_CONTRACT = "CD-DEPENDENCY-REGISTRY-v1"

REGISTRY_DOCUMENT_KEYS = frozenset({"version", "contract", "consumers", "dependencies"})

ENTRY_KEYS = frozenset(
    {"id", "distribution", "kind", "purpose", "declared_in", "needed_by"}
)

ENTRY_KINDS = frozenset({"DIRECT", "TRANSITIVE"})

#: `name[extra]==1.2.3 ; marker` — the leading distribution name is all this needs.
REQUIREMENT_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _text(value) -> str:
    """A scalar as plain text. A missing or non-scalar value reads as empty, never as absent."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


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


def _load_registry(check: Check, root: pathlib.Path):
    """The declared registry, or a refusal code. An absent registry is never an empty one."""
    registry_path = root / REGISTRY
    if not registry_path.is_file():
        return None, check.refuse(
            f"{REGISTRY} does not exist in this subject tree. Every distribution in every "
            "manifest is admissible only by being a REGISTERED dependency (CD-DEP-001), so "
            "with no registry there is no admissible set and nothing can be judged. An "
            "absent registry must not read as an empty one: an empty registry is a decision "
            "somebody wrote down, and an absent one is a file somebody removed."
        )
    try:
        registry = load_yaml(registry_path)
    except YamlSubsetError as exc:
        return None, check.refuse(
            f"{REGISTRY} could not be parsed by this reader: {exc}. A registry the check "
            "cannot read is an admissible set the check cannot establish. It refuses rather "
            "than guessing at a construct it does not understand."
        )
    if not isinstance(registry, dict):
        return None, check.refuse(
            f"{REGISTRY} did not read as a mapping (found {type(registry).__name__}). "
            "A registry whose shape the check cannot establish admits nothing."
        )
    aliases = unresolved_aliases(registry)
    if aliases:
        return None, check.refuse(
            f"{REGISTRY} carries an unresolved YAML alias at {aliases[0]}. A permission that "
            "can only be seen after resolving an anchor is a permission hiding behind an "
            "indirection, and this reader does not resolve them. It refuses rather than "
            "reading a registered distribution as absent because it is merely aliased."
        )
    return (registry, registry_path), 0


def _registered(check: Check, registry, registry_path: pathlib.Path):
    """The admissible set: normalised distribution -> entry id. A malformed entry registers nothing."""
    check.asserted()
    stray = sorted(set(registry) - REGISTRY_DOCUMENT_KEYS)
    if stray:
        check.violation(
            registry_path,
            line_of(registry, stray[0]),
            "CD-DEP-004: the registry document declares an unknown key",
            f"{REGISTRY} declares {', '.join('`' + key + '`' for key in stray)}, which is "
            f"not one of {', '.join(sorted(REGISTRY_DOCUMENT_KEYS))}. The key set is CLOSED "
            "and asserted by equality with the declared set, not by absence of a blacklist: "
            "a key the guard does not read is a declaration nothing enforces.",
        )

    check.asserted()
    if _text(registry.get("contract")) != REGISTRY_CONTRACT:
        check.violation(
            registry_path,
            line_of(registry, "contract") or 1,
            "CD-DEP-004: the registry declares no known contract",
            f"{REGISTRY} declares contract {registry.get('contract')!r}; this check reads "
            f"{REGISTRY_CONTRACT}. A registry answering to a contract this guard does not "
            "know is a registry whose entry shape this guard cannot assert, and reading it "
            "anyway would be guessing.",
        )

    consumers = registry.get("consumers")
    check.asserted()
    if not isinstance(consumers, list) or not consumers:
        check.violation(
            registry_path,
            line_of(registry, "consumers") or 1,
            "CD-DEP-004: the registry declares no `consumers` vocabulary",
            f"{REGISTRY} declares no non-empty `consumers` list (found "
            f"{type(consumers).__name__}). Every `needed_by` value is drawn from it, so "
            "without one no entry can name a consuming surface and nothing is admissible.",
        )
        consumer_set: set = set()
    else:
        consumer_set = {_text(name) for name in consumers}
        check.asserted()
        if len(consumer_set) != len(consumers):
            check.violation(
                registry_path,
                line_of(registry, "consumers") or 1,
                "CD-DEP-004: a consumer is declared twice",
                f"{REGISTRY} declares {len(consumers)} consumers of which "
                f"{len(consumer_set)} are distinct. A duplicated consumer makes the "
                "vocabulary ambiguous about what was actually reviewed.",
            )

    entries = registry.get("dependencies")
    check.asserted()
    if not isinstance(entries, list):
        check.violation(
            registry_path,
            line_of(registry, "dependencies") or 1,
            "CD-DEP-004: the registry declares no `dependencies` list",
            f"{REGISTRY} declares no `dependencies` list (found "
            f"{type(entries).__name__}). An absent list is not an empty one: it is a field "
            "nobody wrote, and it must not read as 'nothing is registered'.",
        )
        return {}, consumer_set

    admissible: dict = {}
    seen_ids: dict = {}
    for index, entry in enumerate(entries):
        where = line_of(entries, index) or line_of(registry, "dependencies") or 1
        check.asserted()
        if not isinstance(entry, dict):
            check.violation(
                registry_path,
                where,
                "CD-DEP-005: a registry entry is not a mapping",
                f"entry {index} read as {type(entry).__name__}. A malformed entry registers "
                "nothing, so whatever it meant to permit is not permitted.",
            )
            continue

        entry_id = _text(entry.get("id")) or f"<entry {index}>"
        line = line_of(entry, "id") or where
        well_formed = True

        check.asserted()
        if set(entry) != ENTRY_KEYS:
            missing = sorted(ENTRY_KEYS - set(entry))
            unknown = sorted(set(entry) - ENTRY_KEYS)
            detail = []
            if missing:
                detail.append("missing " + ", ".join("`" + k + "`" for k in missing))
            if unknown:
                detail.append("unknown " + ", ".join("`" + k + "`" for k in unknown))
            check.violation(
                registry_path,
                line,
                "CD-DEP-005: a registry entry does not declare exactly the six keys",
                f"{entry_id}: {'; '.join(detail)}. The entry key set is CLOSED and asserted "
                "by equality. A field the guard does not read is a declaration nothing "
                "enforces, and a missing one is a review that did not happen. A MALFORMED "
                "ENTRY REGISTERS NOTHING.",
            )
            well_formed = False

        check.asserted()
        if entry_id in seen_ids:
            check.violation(
                registry_path,
                line,
                "CD-DEP-005: a registry entry id is not unique",
                f"{entry_id} is declared at line {seen_ids[entry_id]} and again here. An id "
                "that names two entries cannot identify either.",
            )
            well_formed = False
        else:
            seen_ids[entry_id] = line

        raw_distribution = _text(entry.get("distribution"))
        check.asserted()
        if not raw_distribution:
            check.violation(
                registry_path,
                line_of(entry, "distribution") or line,
                "CD-DEP-005: a registry entry names no distribution",
                f"{entry_id} declares an empty `distribution`. An entry that names nothing "
                "permits nothing.",
            )
            well_formed = False
        elif normalise_distribution(raw_distribution) != raw_distribution:
            check.violation(
                registry_path,
                line_of(entry, "distribution") or line,
                "CD-DEP-005: a registered distribution is not in PEP 503 normal form",
                f"{entry_id} registers {raw_distribution!r}, which normalises to "
                f"{normalise_distribution(raw_distribution)!r}. Entries are written in "
                "normal form so that one distribution cannot be registered twice under two "
                "spellings and reviewed as though it were two things.",
            )
            well_formed = False

        check.asserted()
        if _text(entry.get("kind")) not in ENTRY_KINDS:
            check.violation(
                registry_path,
                line_of(entry, "kind") or line,
                "CD-DEP-005: a registry entry declares an unknown kind",
                f"{entry_id} declares kind {entry.get('kind')!r}; the vocabulary is "
                f"{', '.join(sorted(ENTRY_KINDS))}. An unknown kind is a violation and not "
                "an unknown to be tolerated.",
            )
            well_formed = False

        for field in ("purpose", "declared_in"):
            check.asserted()
            if not _text(entry.get(field)):
                check.violation(
                    registry_path,
                    line_of(entry, field) or line,
                    f"CD-DEP-005: a registry entry declares an empty `{field}`",
                    f"{entry_id} declares no {field}. A dependency with no stated "
                    f"{'reason' if field == 'purpose' else 'authorising clause'} is a "
                    "dependency nobody agreed to. Its CONTENT is not judged — see declared "
                    "limit boundary 2 — but its ABSENCE is.",
                )
                well_formed = False

        needed_by = entry.get("needed_by")
        check.asserted()
        if not isinstance(needed_by, list) or not needed_by:
            check.violation(
                registry_path,
                line_of(entry, "needed_by") or line,
                "CD-DEP-005: a registry entry names no consuming surface",
                f"{entry_id} declares no non-empty `needed_by` list. A dependency no surface "
                "needs is a dependency nobody needs.",
            )
            well_formed = False
        else:
            unknown_consumers = sorted(
                {_text(name) for name in needed_by} - consumer_set
            )
            check.asserted()
            if unknown_consumers:
                check.violation(
                    registry_path,
                    line_of(entry, "needed_by") or line,
                    "CD-DEP-005: a registry entry names an unknown consumer",
                    f"{entry_id} names {', '.join(unknown_consumers)}, which is not in the "
                    "declared `consumers` vocabulary. The vocabulary is CLOSED: a consumer "
                    "the guard does not know is a declaration nobody reviewed.",
                )
                well_formed = False

        if not well_formed:
            # A MALFORMED ENTRY REGISTERS NOTHING. Otherwise the cheapest bypass is to
            # register a broker SDK in an entry broken just enough to be skipped.
            continue

        normalised = normalise_distribution(raw_distribution)

        # LAYER 2 OVER THE REGISTRY ITSELF. A distribution somebody DOES register is still
        # judged. Neither layer is sole.
        check.asserted()
        reason = judge_distribution(raw_distribution)
        if reason:
            check.violation(
                registry_path,
                line_of(entry, "distribution") or line,
                "CD-DEP-002: a broker SDK is REGISTERED as a dependency",
                f"{reason} Registered as {entry_id}. Registration is not absolution: the "
                "denylist and the token rule survive as a second layer over this registry "
                "precisely so that declaring a broker SDK openly is refused as surely as "
                "smuggling one. CD-AC-012: no execution pathway exists.",
            )
            continue

        admissible[normalised] = entry_id

    return admissible, consumer_set


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

    loaded, code = _load_registry(check, root)
    if loaded is None:
        return code
    registry, registry_path = loaded

    admissible, _consumers = _registered(check, registry, registry_path)

    manifests: list = []
    for name in REQUIRED_MANIFESTS:
        manifests.append(root / name)
    for pattern in EXTRA_PATTERNS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in manifests:
                manifests.append(path)

    #: every normalised distribution actually seen in a manifest, for CD-DEP-003
    seen_in_manifests: set = set()

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
            normalised = normalise_distribution(name)
            seen_in_manifests.add(normalised)

            # LAYER 2, at the manifest site, so a violation is reported where a reader looks.
            check.asserted()
            reason = judge_distribution(name)
            if reason:
                check.violation(
                    path,
                    line,
                    "CD-DEP-002: broker SDK in a dependency manifest",
                    f"{reason} Declared in {where}. CD-AC-012: no execution pathway "
                    "exists. A dependency is permission to import, and permission granted "
                    "is the review already done.",
                )
                continue

            # LAYER 1, DENY BY DEFAULT. Nothing is recognised about an unregistered name.
            check.asserted()
            if normalised not in admissible:
                check.violation(
                    path,
                    line,
                    "CD-DEP-001: a distribution is not a REGISTERED dependency",
                    f"{name!r} (normalised {normalised!r}) is declared in {where} and is "
                    f"registered nowhere in {REGISTRY}. It is refused BY DEFAULT — not "
                    "because anything was recognised about it, but because nobody declared "
                    "it. A dependency is admissible by being registered with a purpose, an "
                    "authorising clause and a needing surface; it is not admissible by "
                    "failing to look like a broker. CD-AC-012: no execution pathway exists.",
                )

    # CD-DEP-003 — SET EQUALITY IN THE OTHER DIRECTION.
    for normalised, entry_id in sorted(admissible.items()):
        check.asserted()
        if normalised not in seen_in_manifests:
            check.violation(
                registry_path,
                line_of(registry, "dependencies") or 1,
                "CD-DEP-003: a REGISTERED dependency appears in no manifest",
                f"{entry_id} registers {normalised!r}, which no dependency manifest in this "
                "tree declares. The correspondence is asserted BY EQUALITY IN BOTH "
                "DIRECTIONS: a permission nobody uses is a permission nobody re-reviewed, "
                "and without this rule the manifest line a complaint names could simply be "
                "deleted to silence the guard.",
            )

    check.note(
        f"LAYER 1 is DENY BY DEFAULT over {REGISTRY}: {len(admissible)} registered "
        "distributions form the admissible set, and an unregistered distribution is refused "
        "without anything being recognised about it."
    )
    check.note(
        f"LAYER 2 SURVIVES over both the registry and the manifests: the denylist carries "
        f"{len(BROKER_SDK_DISTRIBUTIONS)} named distributions and is a FLOOR, not an oracle, "
        "and the token rule is the part that generalises. NEITHER LAYER IS SOLE."
    )
    check.note(
        "normalisation is PEP 503, so Alpaca_Trade_API and alpaca-trade-api are one name: "
        + normalise_distribution("Alpaca_Trade_API")
    )
    check.note(
        "SCOPE IS DECLARED_SURFACE, NOT CLASS. A clean run means every manifest distribution "
        "was registered by somebody and none is recognisable as a broker SDK. It does NOT "
        "mean no dependency can reach a broker — see declared limit boundaries 1, 2 and 5."
    )

    return check.done(
        f"{len(manifests)} dependency manifests: "
        + ", ".join(path.name for path in manifests)
        + f"; {len(seen_in_manifests)} distinct distributions; registry {REGISTRY} with "
        f"{len(admissible)} admissible"
    )


if __name__ == "__main__":
    raise SystemExit(main())
