#!/usr/bin/env python3
"""CUT-AND-PASTE PORTABILITY, READ AS DATA (``PO-DECISIONS-0025`` ruling 2, BINDING).

    "Independent container; SQL + Redis in movable named volumes; ALL config via env;
    cut-and-paste dev (dell) -> prod (cloud); the deploy audit verifies cut-and-paste
    reproducibility before go-live."

**THIS IS THAT DEPLOY AUDIT, AND IT EXISTS BECAUSE THE CONSTRAINT WAS PREVIOUSLY ASSERTED IN
PROSE AND CHECKED BY NOTHING.** ``deploy/compose.yaml`` was already largely compliant when
this was written — that was measured, not assumed, and the measurement is in the WO-3
increment 16A Build Log entry. The gap this closes is not that the file was wrong. It is
that **nothing would have noticed when it became wrong**, and a portability property decays
in exactly the way a comment cannot detect: one absolute path, typed once, on the machine
where it happened to work.

===========================================================================================
IT READS THE FILE AS YAML DATA. NEVER AS PROSE, NEVER BY REGEX OVER LINES.
===========================================================================================
A regex over the raw text cannot tell a host baked into a ``ports`` entry from the same
characters inside a paragraph explaining why hosts are forbidden — and this file contains
both. ``check_egress_no_broker.py`` learned that at ``CD-ASR-F04``, where an auditor replaced
``api.ibkr.com`` with ``198.51.100.24`` and a name-recognising check went green.

So the document is parsed with :mod:`tools.register._yamlmin`, the project's existing
location-tracking stdlib-only YAML subset reader, and every judgement is made against a
NODE at a JSON POINTER. Nothing here is copied from that reader; it is imported, because two
YAML readers in one repository would be two readers that disagree.

*** **AND THE MERGE KEYS ARE RESOLVED, WHICH IS THE PART THAT WOULD HAVE MADE THIS VACUOUS.**
``_yamlmin`` records ``<<: *anchor`` UNRESOLVED, by design — it says so. Measured on the real
file, that means **every one of the six service bind mounts reads as the literal mapping
``{'<<': '*cd-contracts-mount'}``**, which declares no ``source`` and no ``target``. A bind
mount check that walked the unresolved tree would have examined SIX MOUNTS CARRYING NO
FIELDS, found nothing wrong with any of them, and reported a confident PASS. That is a
vacuous green, and it is the specific failure this project has named four times
(``CD-PL-F170``). :func:`_resolve_merges` is therefore not a convenience — it is the
difference between a check and a decoration, and :func:`main` asserts that the resolution
actually happened before it judges anything. ***

===========================================================================================
THE SEVEN REFUSALS
===========================================================================================
1  **an absolute host path as a bind source** — a dell path in the file IS the cut-and-paste
   failing. Also refused: a relative source that ESCAPES the repository, resolved against
   the compose file's own directory, because ``../../../srv/x`` is the same defect spelled
   portably.
2  **durable data outside a named volume** — a bind-mounted database directory does not
   travel. A named volume moves with a documented ``docker volume`` operation; a bind mount
   moves when somebody remembers the path.
3  **a hostname or address literal other than the declared loopback publication binds** —
   ``CD-HOLD-005`` keeps those two deliberately; anything else is a host baked in.
4  **any ``argus`` reference in any form** — ``PO-DECISIONS-0025`` r2: no ARGUS coupling.
5  **a config value that is a literal where it should be an env reference** — ruling 2: ALL
   config via env. Enforced as an ALLOWLIST of container-internal constants, each with a
   stated reason, so a NEW literal is a violation until somebody declares it here. An
   allowlist is the only form of this rule that is not guesswork.
6  **a secret-looking value rather than an env-var NAME** — ``PBG-SEC-002``, non-waivable.
7  *** **a config VALUE that names something this deployment does not establish** — added at
   WO-3 increment 16A-FIX, and it exists because rules 5 and 6 ask only whether a value is a
   REFERENCE and never WHAT it is. Two subjects passed with ``0 violations``: a dell path
   parked in an env DEFAULT (``${CD_CONTRACTS_DIR:-/srv/.../dell-only/contracts}``), which
   rule 5 skipped because the string begins ``${`` and rule 3 missed because it is not an
   IPv4; and ``CD_STORE_HOST: postgres.dell.matt.local``, admitted because the KEY is on
   ``INTERNAL_CONSTANTS`` while nothing checked the VALUE was the compose service name that
   allowlist's own comment claims it is. **THE ALLOWLIST WAS A LIST OF KEYS AND THE
   PORTABILITY LIVES IN THE VALUES.** So: a service-name value must name a service DECLARED
   IN THIS FILE, and an absolute path must sit under a container root THIS FILE (or the
   image's ``WORKDIR``) establishes — judged identically whether it is written plainly or
   hidden in a ``${VAR:-DEFAULT}``, because **A DEFAULT IS A VALUE.** ***

===========================================================================================
*** DECLARED LIMITS (``CD-RULE-004``). WHAT THIS CHECK DOES **NOT** CLAIM. ***
===========================================================================================
1  **IT READS ONE FILE.** A tree clean here can be deployed with
   ``docker compose -f compose.yaml -f override.yaml up``, and the override is outside the
   subject. This is the same boundary ``check_egress_no_broker.py`` declares, and it is not
   closable by reading harder.

2  **RULE 3 IS SCOPED TO CONFIGURATION-BEARING POSITIONS, NOT TO PROSE.** ``x-egress`` and
   ``x-cd-egress-contract`` carry long explanatory paragraphs that legitimately CONTAIN
   address literals — measured: three of them, all inside ``meaning`` and ``statement``
   fields describing why addresses are forbidden. Judging those would report the
   documentation of a control as a breach of it. :data:`PROSE_FIELDS` names the excluded
   fields exactly, and an address written anywhere else is judged. **A HOST HIDDEN IN A
   ``blocked_by`` STRING WOULD NOT BE CAUGHT HERE** — it is caught, for the egress subtree,
   by ``check_egress_no_broker.py``'s own invariants.

3  **IT DOES NOT RUN DOCKER, PULL AN IMAGE, OR MOVE A VOLUME.** "Cut-and-paste
   reproducibility" is verified here as a property of the DECLARATION. Whether the stack
   actually starts on a second host is an operational test nobody has run, and this check
   must not be cited as evidence that it would.

4  **REDIS IS NOT CHECKED, BECAUSE THERE IS NO REDIS.** Ruling 2's architecture sentence
   names Redis; ``BLUEPRINT`` §2's container set does not contain it, and
   ``grep -rin redis src/ deploy/ db/ contracts/`` returns nothing. Adding a service with no
   declared purpose, no role in the grant matrix and no egress posture would be worse than
   its absence, and adding one to ``BLUEPRINT`` §2 is a Product Owner act (``CD-D-115``).
   **RAISED AS ``Q31``. THE SQL HALF IS MADE TESTABLE HERE; THE REDIS HALF IS OPEN, NOT
   FINISHED.** This check will not start passing "more" when Redis arrives — rules 2 and 5
   will simply apply to it, which is the point of writing them over the document rather than
   over a service list.

5  **IT IS NOT WIRED TO A REQUIRED-TEST-REGISTER CRITERION, DELIBERATELY.** The register's
   rows are PID acceptance criteria; portability is a Product Owner ruling and has no
   ``CD-AC-`` row. Inventing one would be manufacturing a criterion nobody ratified
   (``PBG-AUTH-005``). It is run by ``tests/test_deploy_portability.py`` and by hand.
"""

from __future__ import annotations

import pathlib
import re
import sys

# The register harness is IMPORTED and never copied: two `Check` classes or two YAML readers
# in one repository are two instruments that disagree. `tools/` is READ here and not written —
# this file lives under `deploy/` because that is where the thing it audits lives, and because
# `tools/sweep/declared_dispositions.py` proved that `tools/` carries obligations an Engineer
# seat cannot discharge.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools" / "register"))

from _support import Check, parse_root, resolve_root  # noqa: E402
from _yamlmin import YamlSubsetError, load_yaml  # noqa: E402

CHECK_ID = "CD-DEPLOY-PORTABILITY"

COMPOSE = "deploy/compose.yaml"

#: Fields whose value is explanatory PROSE and is deliberately NOT judged for addresses.
#: See declared limit 2. Named exactly rather than pattern-matched, so widening the
#: exclusion is a visible edit to this list.
PROSE_FIELDS = frozenset(
    {"meaning", "statement", "declared_in", "blocked_by", "rationale", "why", "note"}
)

#: *** THE TWO ADDRESS LITERALS THAT MAY EXIST, AND NOWHERE ELSE. ***
#: ``CD-HOLD-005`` keeps the loopback publication binds deliberately (``CD-D-006``: the
#: public exposure route is loopback-only on DEV). ``0.0.0.0`` is admitted ONLY as the
#: IN-CONTAINER bind address: a process binding loopback inside its own network namespace
#: would be unreachable through the published port, so binding all interfaces inside the
#: container and restricting the PUBLICATION to 127.0.0.1 is the correct shape, and the
#: restriction that matters is the ``ports`` entry.
LOOPBACK = "127.0.0.1"
BIND_ALL = "0.0.0.0"

#: Pointer SUFFIXES at which an address literal is admitted, with the literal it admits.
ADMITTED_ADDRESSES = (
    ("/ports/", LOOPBACK),
    ("/x-surface/bind", LOOPBACK),
    ("/environment/CD_BIND_HOST", BIND_ALL),
)

#: Rule 5's allowlist: environment keys whose value may be a LITERAL rather than a ``${}``
#: reference, each because the value is a CONTAINER-INTERNAL constant that does not vary
#: between the dell and the cloud. **A key that is not here and carries a literal is a
#: violation.** Widening this is a deliberate edit, which is the friction intended.
INTERNAL_CONSTANTS = {
    "CD_CONTRACTS_DIR": "a path inside the container's own filesystem, not a host path",
    "PYTHONPATH": "a path inside the image",
    "PYTHONDONTWRITEBYTECODE": "an interpreter flag",
    "PYTHONUNBUFFERED": "an interpreter flag",
    "PGDATA": "a path inside the named volume's mount point",
    "POSTGRES_INITDB_ARGS": "an initdb flag, not an address or a credential",
    "TZ": "UTC, and pinning it is what makes timestamps portable",
    "CD_STORE_HOST": "a COMPOSE SERVICE NAME resolved by the compose network's own DNS; "
                     "it travels with the file and names no host",
    "CD_STORE_PORT": "the port inside the compose network",
    "CD_STORE_ROLE": "a database role name, part of the schema, not of the environment",
    "CD_BIND_HOST": "the in-container bind address; see ADMITTED_ADDRESSES",
    "CD_BIND_PORT": "the port inside the container",
}

#: Rule 6: a key carrying any of these tokens must hold an env REFERENCE and never a value.
SECRET_TOKENS = ("password", "passwd", "secret", "token", "credential", "apikey", "api_key")

#: Rule 2: a mount target matching any of these carries DURABLE DATA and must be a named
#: volume. Substring match on the target path, lowercased.
DURABLE_TARGETS = ("/var/lib/", "/pgdata", "/data")

#: *** WHERE A CONTAINER-INTERNAL ABSOLUTE PATH MAY LIVE THAT IS NOT DECLARED IN THE
#: COMPOSE FILE ITSELF. *** Every other admissible root is DERIVED from the document (see
#: :func:`container_roots`) rather than listed, because a root this file does not establish
#: is a root that does not travel. ``/app`` is the exception and it is MEASURED, not
#: assumed: ``deploy/Dockerfile.*`` declare ``WORKDIR /app`` and copy ``src/`` to
#: ``/app/src/`` and ``deploy/entrypoints/`` to ``/app/entrypoints/``. It is a path the
#: IMAGE establishes, so the compose file cannot show it and rule 7 would otherwise refuse
#: the legitimate ``PYTHONPATH: /app/src``.
IMAGE_ROOTS = ("/app",)

#: *** RULE 7's VALUE CONTRACTS — THE ANSWER TO "ALLOWLISTED BY KEY, UNCHECKED BY VALUE". ***
#: ``INTERNAL_CONSTANTS`` says a key MAY carry a literal. It never said WHICH literal, so
#: ``CD_STORE_HOST: postgres.dell.matt.local`` satisfied it exactly as well as
#: ``CD_STORE_HOST: cd-store`` (``CD-ASR-WO3-03`` / ``BL-20260824T084141Z-0160``). A key
#: named here has its VALUE verified against what THIS DOCUMENT actually declares.
#: ``"service"`` -> must be a service declared in this same compose file.
#: ``"container_path"`` -> must be at or under a container root this file establishes.
VALUE_CONTRACTS = {
    "CD_STORE_HOST": "service",
    "CD_CONTRACTS_DIR": "container_path",
    "PGDATA": "container_path",
    "PYTHONPATH": "container_path",
}

_IPV4 = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
_ENV_REF = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*")

#: *** THE WHOLE ``${...}`` FORM, INCLUDING THE PART :data:`_ENV_REF` CANNOT SEE. ***
#: ``_ENV_REF`` has no closing brace and no default group, so it matches the PREFIX
#: ``${CD_CONTRACTS_DIR`` and stops. Everything after it — crucially the ``:-DEFAULT`` — was
#: never examined by any rule, and a dell path parked in a default therefore passed with
#: ``0 violations``. This pattern captures the operator and the default so rule 7 can judge
#: a default exactly as it judges a bare literal.
_ENV_REF_FULL = re.compile(
    r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::(?P<op>[-?])(?P<rest>[^}]*))?\}"
)
_ANCHOR_DECL = re.compile(r"^(?P<key>[^\s:#][^:]*):\s*&(?P<anchor>\S+)\s*$")


# ------------------------------------------------------------------------------------- #
# MERGE RESOLUTION — see the module docstring. Without this the check is vacuous.
# ------------------------------------------------------------------------------------- #

def anchor_table(text: str) -> dict:
    """Map ``anchor name -> top-level key`` from the RAW text.

    ``_yamlmin`` drops the ``&name`` token when it records the block, so the association
    between an anchor and the node it names survives only in the source. Read here rather
    than inferred from a naming convention: ``x-cd-hardening: &cd-hardening`` happens to
    follow one, and a check that relied on the convention would break silently the first
    time somebody did not.
    """
    table = {}
    for line in text.splitlines():
        match = _ANCHOR_DECL.match(line)
        if match:
            table[match.group("anchor")] = match.group("key").strip()
    return table


def _resolve_merges(node, document: dict, anchors: dict, depth: int = 0):
    """Return ``node`` with every ``<<: *alias`` replaced by the anchored mapping.

    Merge semantics: keys already present on the node WIN over the merged ones, which is
    what YAML specifies and what compose relies on (a service overrides the shared
    environment block). Recursion is depth-limited rather than cycle-detected, and a
    breach RAISES: silently returning a partly-resolved tree is how a check goes vacuous.
    """
    if depth > 10:
        raise YamlSubsetError(
            "merge resolution exceeded 10 levels; refusing to guess at a cycle"
        )
    if isinstance(node, list):
        return [_resolve_merges(item, document, anchors, depth + 1) for item in node]
    if not isinstance(node, dict):
        return node

    merged = {}
    alias = node.get("<<")
    if isinstance(alias, str) and alias.startswith("*"):
        name = alias[1:]
        if name not in anchors:
            raise YamlSubsetError(f"alias *{name} names no anchor declared in this file")
        target = document.get(anchors[name])
        if not isinstance(target, dict):
            raise YamlSubsetError(f"anchor &{name} does not name a mapping")
        merged.update(_resolve_merges(target, document, anchors, depth + 1))

    for key, value in node.items():
        if key == "<<":
            continue
        merged[key] = _resolve_merges(value, document, anchors, depth + 1)
    return merged


def walk(node, pointer=""):
    """Every ``(pointer, node)`` in the document, depth first."""
    yield pointer, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk(value, f"{pointer}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk(value, f"{pointer}/{index}")


def _is_prose(pointer: str) -> bool:
    return pointer.rsplit("/", 1)[-1] in PROSE_FIELDS


def _address_admitted(pointer: str, literal: str) -> bool:
    for suffix, admitted in ADMITTED_ADDRESSES:
        if (suffix in pointer or pointer.endswith(suffix)) and literal == admitted:
            return True
    return False


def judged_literals(text: str):
    """Every part of ``text`` that is a VALUE rather than a reference, with how to name it.

    *** THIS IS THE HALF OF ``${VAR:-DEFAULT}`` THAT NOTHING USED TO LOOK AT. ***

    Yields ``(description, literal)``:

    * a value containing no ``${}`` at all yields itself — an ordinary literal;
    * ``${VAR:-DEFAULT}`` yields ``DEFAULT``, because **a default IS a value**. It is the
      value this deployment uses when the environment is silent, which on a fresh host is
      always. A dell path parked there is exactly as unportable as one written plainly, and
      more dangerous for looking like configuration;
    * ``${VAR:?message}`` yields NOTHING. There is no default — the deployment refuses to
      start unless the variable is set — and the message is prose, not a value;
    * ``${VAR}`` yields nothing, for the same reason.
    """
    if not _ENV_REF.search(text):
        yield "the literal", text
        return
    for match in _ENV_REF_FULL.finditer(text):
        if match.group("op") == "-":
            yield f"the default of ${{{match.group('name')}:-…}}", match.group("rest")


def container_roots(document) -> tuple:
    """Every absolute path THIS FILE establishes inside a container, plus the image roots.

    Derived from the document rather than listed, because the point of the check is that
    the deployment travels: a path is container-internal precisely when this same file (or
    the image it names) creates it. Mount targets, tmpfs targets and :data:`IMAGE_ROOTS`.

    A tmpfs entry is ``/tmp:size=16m,mode=1777`` — the options are stripped here, so the
    root recorded is ``/tmp``. The final ``startswith("/")`` filter is what keeps the
    OPTIONS out: the YAML subset parser splits ``/tmp:size=16m,...`` on its colon, so the
    option string arrives here as a node in its own right. It is not a path, it can never
    be an ancestor of one, and admitting it would put noise in every rule 7 finding.
    """
    roots = set(IMAGE_ROOTS)
    for pointer, node in walk(document):
        if not isinstance(node, str):
            continue
        if pointer.endswith("/target"):
            roots.add(node)
        elif "/tmpfs/" in f"{pointer}/":
            roots.add(node.split(":", 1)[0])
            # The parser may have made the path the KEY and the options the value.
            roots.add(pointer.rsplit("/", 1)[-1])
    return tuple(sorted(root for root in roots if root.startswith("/")))


def _looks_like_path(literal: str) -> bool:
    """An ABSOLUTE POSIX path. A relative path travels and is not judged here."""
    return literal.startswith("/")


def _under_a_container_root(literal: str, roots) -> bool:
    """``literal`` is at, or beneath, one of ``roots``. Segment-wise, never by prefix.

    ``str.startswith`` would admit ``/apple`` under ``/app``; ``PurePosixPath.parts`` will
    not, and the whole value of this check is that a near-miss is a miss.
    """
    parts = pathlib.PurePosixPath(literal).parts
    for root in roots:
        root_parts = pathlib.PurePosixPath(root).parts
        if parts[: len(root_parts)] == root_parts:
            return True
    return False


# ------------------------------------------------------------------------------------- #
# THE SEVEN RULES
# ------------------------------------------------------------------------------------- #

def rule_1_and_2_mounts(check, path, root, services, top_volumes) -> None:
    """Bind sources travel, and durable data lives in a named volume."""
    compose_dir = (root / COMPOSE).parent
    for service, spec in services.items():
        for index, mount in enumerate(spec.get("volumes") or []):
            pointer = f"/services/{service}/volumes/{index}"
            if not isinstance(mount, dict):
                check.violation(
                    path, 0, "1: a mount this audit cannot read",
                    f"{pointer} is not a mapping. The short `host:container` string form "
                    "is not used in this file and is not supported here, because its "
                    "source and its mode cannot be judged separately.",
                )
                continue

            kind = mount.get("type")
            source = mount.get("source")
            target = str(mount.get("target") or "")

            check.asserted()
            if kind == "bind" and isinstance(source, str):
                if pathlib.PurePosixPath(source).is_absolute():
                    check.violation(
                        path, 0, "1: an absolute host path as a bind source",
                        f"{pointer} binds {source!r}. An absolute host path is the "
                        "cut-and-paste failing itself: it names a directory that exists on "
                        "the machine this was written on and on no other.",
                    )
                else:
                    resolved = (compose_dir / source).resolve()
                    try:
                        resolved.relative_to(root)
                    except ValueError:
                        check.violation(
                            path, 0, "1: a bind source escaping the repository",
                            f"{pointer} binds {source!r}, which resolves to {resolved} — "
                            f"outside {root}. A relative path that climbs out of the tree "
                            "is an absolute path spelled portably.",
                        )

            check.asserted()
            if any(token in target.lower() for token in DURABLE_TARGETS):
                if kind != "volume":
                    check.violation(
                        path, 0, "2: durable data outside a named volume",
                        f"{pointer} mounts {target!r} as type {kind!r}. Durable data must "
                        "sit in a NAMED VOLUME: a volume travels by a documented "
                        "`docker volume` operation, and a bind mount travels when somebody "
                        "remembers the path.",
                    )
                elif source not in (top_volumes or {}):
                    check.violation(
                        path, 0, "2: a volume nobody declared",
                        f"{pointer} names volume {source!r}, which is not declared in the "
                        "top-level `volumes:` block. An undeclared volume is created "
                        "anonymously and does not travel.",
                    )


def rule_3_addresses(check, path, document) -> None:
    """No host baked in, bar the two the Product Owner kept."""
    for pointer, node in walk(document):
        if not isinstance(node, str) or _is_prose(pointer):
            continue
        check.asserted()
        for literal in _IPV4.findall(node):
            if _address_admitted(pointer, literal):
                continue
            check.violation(
                path, 0, "3: an address literal baked into the deployment",
                f"at {pointer}: the literal {literal!r}. The only addresses this "
                f"deployment may name are {LOOPBACK} in a `ports` entry or an "
                f"`x-surface/bind` (CD-HOLD-005, the deliberate loopback publication "
                f"binds) and {BIND_ALL} as CD_BIND_HOST (the in-container bind). "
                "Anything else is a host that does not travel.",
            )


def rule_4_argus(check, path, document) -> None:
    """No ARGUS coupling, in any form, anywhere in the document."""
    for pointer, node in walk(document):
        check.asserted()
        haystack = pointer if not isinstance(node, str) else f"{pointer} {node}"
        if "argus" in haystack.lower():
            check.violation(
                path, 0, "4: an ARGUS reference",
                f"at {pointer}. PO-DECISIONS-0025 ruling 2 requires an INDEPENDENT "
                "container with no ARGUS coupling. A reference here is a dependency on "
                "another product's deployment, and it does not travel with this one.",
            )


def rule_5_and_6_config(check, path, services) -> None:
    """ALL config via env; secrets by NAME only."""
    for service, spec in services.items():
        blocks = [(f"/services/{service}/environment", spec.get("environment") or {})]
        build = spec.get("build")
        if isinstance(build, dict):
            blocks.append((f"/services/{service}/build/args", build.get("args") or {}))

        for base, block in blocks:
            if not isinstance(block, dict):
                continue
            for key, value in block.items():
                pointer = f"{base}/{key}"
                text = "" if value is None else str(value)
                is_reference = bool(_ENV_REF.search(text))

                # -- 6: a secret must be an env-var NAME, never a value ---------------- #
                check.asserted()
                if any(token in key.lower() for token in SECRET_TOKENS):
                    if not is_reference:
                        # The VALUE is never echoed. PBG-SEC-002 is non-waivable, and a
                        # refusal that quotes the secret has published it.
                        check.violation(
                            path, 0, "6: a secret-looking value rather than a name",
                            f"{pointer} carries a literal. A secret is referenced by "
                            "ENV-VAR NAME and never reproduced in a governed file "
                            "(PBG-SEC-002, non-waivable). The offending value is "
                            "deliberately not quoted in this finding.",
                        )
                    continue

                # -- 5: config comes from the environment ------------------------------ #
                check.asserted()
                if not is_reference and key not in INTERNAL_CONSTANTS:
                    check.violation(
                        path, 0, "5: a config literal where an env reference belongs",
                        f"{pointer} is a literal. PO-DECISIONS-0025 ruling 2 requires ALL "
                        "config via env. If this value is a CONTAINER-INTERNAL constant "
                        "that cannot differ between the dell and the cloud, declare it in "
                        "INTERNAL_CONSTANTS in this file with the reason — that edit is "
                        "the friction intended, and it is how the next reader learns why.",
                    )


def rule_7_config_values(check, path, services, document) -> None:
    """*** THE VALUE, NOT JUST THE KEY — AND INSIDE ``${VAR:-DEFAULT}``. ***

    Rules 5 and 6 ask whether a value is a reference. Neither ever asks WHAT the value is,
    so two whole classes of unportable deployment passed with ``0 violations``:

    * a dell path parked in an env DEFAULT, which rule 5 skipped because the string starts
      with ``${``, and which rule 3 could not see because it is not an IPv4;
    * a dell HOSTNAME in an allowlisted key, admitted because ``CD_STORE_HOST`` is on a
      list of keys that may hold a literal — with nothing checking the literal is the
      compose service name the allowlist's own comment claims it is. An IPv4 in that same
      key IS caught, by rule 3, so the check FIRED but could not see a name.

    Both are the same defect wearing two hats: **the allowlist was a list of keys and the
    portability lives in the values.** This rule judges the value, and it judges the inside
    of a ``${VAR:-DEFAULT}`` exactly as it judges a bare literal.
    """
    roots = container_roots(document)
    declared_services = tuple(services)

    for service, spec in services.items():
        blocks = [(f"/services/{service}/environment", spec.get("environment") or {})]
        build = spec.get("build")
        if isinstance(build, dict):
            blocks.append((f"/services/{service}/build/args", build.get("args") or {}))

        for base, block in blocks:
            if not isinstance(block, dict):
                continue
            for key, value in block.items():
                pointer = f"{base}/{key}"
                text = "" if value is None else str(value)

                # A secret's value is never inspected and never echoed (PBG-SEC-002).
                if any(token in key.lower() for token in SECRET_TOKENS):
                    continue

                for described, literal in judged_literals(text):
                    if not literal:
                        continue
                    contract = VALUE_CONTRACTS.get(key)

                    # -- 7a: a declared SERVICE NAME must name a service in THIS file --- #
                    check.asserted()
                    if contract == "service" and literal not in declared_services:
                        check.violation(
                            path, 0, "7: a config value that names something this file does "
                            "not declare",
                            f"at {pointer}, {described} is {literal!r}, which is not a "
                            f"service declared in this compose file. The declared services "
                            f"are {list(declared_services)}. INTERNAL_CONSTANTS admits this "
                            "key because its value is 'a COMPOSE SERVICE NAME resolved by "
                            "the compose network's own DNS' — that is a claim about the "
                            "VALUE, and until now nothing checked it. A hostname resolved "
                            "by somebody's LAN is precisely the host that does not travel.",
                        )

                    # -- 7b: an absolute path must be one this deployment establishes ---- #
                    check.asserted()
                    if (
                        _looks_like_path(literal)
                        and contract in ("container_path", None)
                        and not _under_a_container_root(literal, roots)
                    ):
                        check.violation(
                            path, 0, "7: a host path in a config value",
                            f"at {pointer}, {described} is {literal!r}. That is an absolute "
                            "path under no root this deployment establishes — the container "
                            f"roots this file creates are {list(roots)} (mount targets, "
                            "tmpfs targets, and the image's WORKDIR). An absolute host path "
                            "is the cut-and-paste failing itself: it names a directory that "
                            "exists on the machine this was written on and on no other. "
                            "**A DEFAULT IS A VALUE** — parking it inside ${VAR:-DEFAULT} "
                            "hides it from a reader, not from the deployment.",
                        )


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)
    path = root / COMPOSE
    if not path.is_file():
        return check.refuse(f"{COMPOSE} does not exist under {root}.")

    text = path.read_text(encoding="utf-8")
    try:
        raw = load_yaml(path)
        anchors = anchor_table(text)
        document = _resolve_merges(raw, raw, anchors)
    except YamlSubsetError as exc:
        return check.refuse(f"{COMPOSE} could not be read as YAML data: {exc}")

    services = document.get("services")
    if not isinstance(services, dict) or not services:
        return check.refuse(f"{COMPOSE} declares no services; there is nothing to audit.")

    # *** THE ANTI-VACUITY PRECONDITION. *** Unresolved merges would leave every bind mount
    # an empty mapping and every rule below trivially satisfied. Refuse rather than pass.
    unresolved = [p for p, n in walk(document) if isinstance(n, dict) and "<<" in n]
    if unresolved:
        return check.refuse(
            f"{len(unresolved)} merge key(s) survived resolution, first at "
            f"{unresolved[0]}. Every rule below would be judging a mapping with no fields, "
            "so a PASS would mean 'I looked at nothing'."
        )
    mounts = sum(len(s.get("volumes") or []) for s in services.values())
    if mounts == 0:
        return check.refuse(
            "no service declares a volume. Rules 1 and 2 would pass vacuously."
        )

    rule_1_and_2_mounts(check, path, root, services, document.get("volumes"))
    rule_3_addresses(check, path, document)
    rule_4_argus(check, path, document)
    rule_5_and_6_config(check, path, services)
    rule_7_config_values(check, path, services, document)

    check.note(
        f"{len(anchors)} anchor(s) resolved, {mounts} mount(s) judged with their fields "
        "present. Merge resolution is a PRECONDITION of this check, not a convenience."
    )
    check.note(
        "REDIS IS ABSENT FROM THIS DESIGN AND IS NOT CHECKED. PO-DECISIONS-0025 r2 names "
        "it; BLUEPRINT §2's container set does not. Raised as Q31; the SQL half is what is "
        "made testable here. See declared limit 4."
    )
    return check.done(
        f"{COMPOSE} as YAML data: {len(services)} services, {mounts} mounts, "
        f"seven refusals over the resolved document"
    )


if __name__ == "__main__":
    raise SystemExit(main())
