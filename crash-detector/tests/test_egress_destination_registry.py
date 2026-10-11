"""The egress destination registry — the declaration CD-AC-012's egress half rests on.

WHY THIS MODULE EXISTS. `CD-ASR-F04` (MEDIUM): an independent auditor put the IP literal
``198.51.100.24`` into cd-collectors' egress allowlist where ``api.ibkr.com`` had been, and
``check_egress_no_broker.py`` exited 0. The check recognised brokers BY NAME and an address
has no name to recognise. The closure is DENY BY DEFAULT over an in-tree registry of
declared destinations: an allowlist entry is admissible only if somebody registered that
exact destination for that exact service, so an address literal is not a spelling to catch —
it is simply not a destination anyone declared.

WHAT THIS MODULE IS FOR, GIVEN THE GUARD ALREADY ASSERTS ALL OF IT. The register check is
the gate; these are the REGRESSION tests, and they exist so that a later seat which quietly
re-opens the class fails a test module as well as a register check. That is the same
reasoning ``tests/test_deploy_container_set.py`` already applies to the compose posture, and
this module deliberately reads the same artefacts with the same stdlib-only reader.

NOTHING HERE ENFORCES ANYTHING. Docker Compose has no per-host egress primitive; the lane
that makes ALLOWLIST mean more than NONE is owed at WO-3. What is asserted is that the
DECLARATION that lane will inherit is closed rather than holed.
"""

from __future__ import annotations

import pathlib

import pytest

from compose_reader import load_compose

DEPLOY = pathlib.Path(__file__).resolve().parents[1] / "deploy"
COMPOSE_PATH = DEPLOY / "compose.yaml"
REGISTRY_PATH = DEPLOY / "egress-destinations.yaml"

REGISTRY_CONTRACT = "CD-EGRESS-DESTINATION-REGISTRY-v1"

#: CD-EGRESS-005. Declared member sets, asserted by EQUALITY. A blacklist of forbidden keys
#: is defeated by a key nobody listed, which is the shape of defect this whole rework exists
#: to stop repeating.
REGISTRY_DOCUMENT_KEYS = frozenset({"version", "contract", "destinations"})
DESTINATION_KEYS = frozenset(
    {"id", "host", "operator", "purpose", "declared_in", "services"}
)
X_EGRESS_KEYS = frozenset({"policy", "hosts", "pending", "enforced_by"})

#: CD-EGRESS-007. The closed key set of a `pending` entry — the record of an endpoint whose
#: host is NOT KNOWN. It carries the clause that authorises the future endpoint and the reason
#: the host is not written, and nothing else, because a host is precisely the thing a pending
#: entry declares the absence of.
PENDING_KEYS = frozenset({"declared_in", "blocked_by"})


@pytest.fixture(scope="module")
def registry() -> dict:
    return load_compose(REGISTRY_PATH)


@pytest.fixture(scope="module")
def destinations(registry: dict) -> list:
    return registry["destinations"]


@pytest.fixture(scope="module")
def services() -> dict:
    return load_compose(COMPOSE_PATH)["services"]


# --- the registry exists and is readable by the instrument the guard uses --------------- #


def test_the_registry_file_exists():
    """An ABSENT registry must never read as an empty one.

    With no registry there is no admissible set at all, so a check that treated a missing
    file as "nothing is registered, therefore nothing is wrong" would be defeated by
    deleting a file. The guard refuses (exit 3) in that case; this test is the reason a
    deletion cannot arrive unnoticed.
    """
    assert REGISTRY_PATH.is_file(), (
        f"{REGISTRY_PATH} does not exist. Every egress allowlist entry is admissible only "
        "by being a registered destination, so its absence removes the admissible set."
    )


def test_the_registry_is_readable_with_the_stdlib_only_reader(registry: dict):
    """The guard is a stdlib-only standalone script and reads this file with no PyYAML."""
    assert isinstance(registry, dict)


def test_the_registry_declares_the_contract_the_guard_reads(registry: dict):
    assert registry.get("contract") == REGISTRY_CONTRACT, (
        "a registry answering to a contract the guard does not know is a registry whose "
        "entry shape the guard cannot assert"
    )


def test_the_registry_document_key_set_is_closed(registry: dict):
    assert set(registry) == REGISTRY_DOCUMENT_KEYS, (
        f"the registry declares {sorted(set(registry))}; the closed set is "
        f"{sorted(REGISTRY_DOCUMENT_KEYS)}. Equality, not absence of a blacklist."
    )


def test_the_destinations_field_is_a_list(registry: dict):
    """An absent list is not an empty one: it is a field nobody wrote."""
    assert isinstance(registry.get("destinations"), list)


# --- WO-1.2b registers exactly the ratified data hosts (five since WO-1.6) ------------------------------ #

RATIFIED_DESTINATIONS = {
    "fred.stlouisfed.org": "DEST-FRED-001",
    "cdn-api.cboe.com": "DEST-CBOE-001",
    "query1.finance.yahoo.com": "DEST-YAHOO-001",
    "www.multpl.com": "DEST-MULTPL-001",
    "prices.lbma.org.uk": "DEST-LBMA-001",
}


def test_registry_holds_exactly_the_ratified_data_hosts_for_cd_collectors(destinations: list):
    """Each host is the feed a Matt-ratified mapping row declares (ratified 2026-08-24).

    A destination appearing beyond these is an engineering seat resolving product meaning;
    this test is what must be updated, deliberately, with the ratified row cited.
    """
    assert {d["host"]: d["id"] for d in destinations} == RATIFIED_DESTINATIONS
    for entry in destinations:
        assert entry["services"] == ["cd-collectors"], entry["id"]
        assert "indicator_mapping.yaml" in entry["declared_in"], entry["id"]


def test_only_cd_collectors_names_hosts_in_its_allowlist(services: dict):
    named = {
        name: sorted(service["x-egress"]["hosts"])
        for name, service in services.items()
        if service.get("x-egress", {}).get("hosts")
    }
    assert named == {"cd-collectors": sorted(RATIFIED_DESTINATIONS)}


# --- CD-EGRESS-004: DENY BY DEFAULT ------------------------------------------------------ #


def test_every_allowlist_entry_is_a_registered_destination_for_that_service(
    services: dict, destinations: list
):
    """The invariant, asserted over the artefacts rather than over a remembered list.

    This passes vacuously today because every allowlist is empty, and it is written anyway:
    it is the assertion that starts biting the moment the Product Owner's CD-D-005 lands and
    the first host is written into a compose allowlist. A test added only once a violation is
    possible is a test added after the violation.
    """
    entitled: dict = {}
    for entry in destinations:
        entitled.setdefault(entry["host"], set()).update(entry["services"])

    unregistered = []
    for name, service in services.items():
        for host in service.get("x-egress", {}).get("hosts") or []:
            if name not in entitled.get(host, set()):
                unregistered.append((name, host))

    assert unregistered == [], (
        f"allowlist entries that are not registered destinations for their own service: "
        f"{unregistered}. An entry is a violation BY DEFAULT when nobody declared it — no "
        "recognition is performed on it, so there is no pattern to write around."
    )


# --- CD-EGRESS-005: closed key sets ------------------------------------------------------ #


def test_every_x_egress_block_declares_exactly_the_contract_key_set(services: dict):
    """A posture arriving through ``hosts_extra:`` would be read by nothing.

    CD-EGRESS-003 argues that a check skipping a service it does not recognise is bypassed
    by adding a service. This is the same argument one level down, applied to keys.
    """
    stray = {
        name: sorted(set(service["x-egress"]) - X_EGRESS_KEYS)
        for name, service in services.items()
        if set(service.get("x-egress", {})) - X_EGRESS_KEYS
    }
    assert stray == {}, f"x-egress blocks declaring unknown keys: {stray}"


def test_every_registered_destination_declares_exactly_the_six_fields(destinations: list):
    for position, entry in enumerate(destinations):
        assert set(entry) == DESTINATION_KEYS, (
            f"destination #{position} declares {sorted(set(entry))}; a destination declares "
            f"exactly {sorted(DESTINATION_KEYS)}"
        )


# --- CD-EGRESS-006: a destination is well formed and attributable ------------------------ #


def _hostname_is_declarable(value: str) -> bool:
    """The POSITIVE permitted shape, restated here as the guard states it.

    Two or more DNS labels of lowercase letters, digits and hyphens, no leading or trailing
    hyphen, final label alphabetic and at least two characters. Deliberately duplicated
    rather than imported: the guard is a standalone script outside the package, and a test
    that imported the code under test would be asserting the code against itself.
    """
    if not isinstance(value, str) or value != value.strip().lower() or not value:
        return False
    labels = value.split(".")
    if len(labels) < 2:
        return False
    alphabet = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    for label in labels:
        if not label or len(label) > 63 or set(label) - alphabet:
            return False
        if label.startswith("-") or label.endswith("-"):
            return False
    return labels[-1].isalpha() and len(labels[-1]) >= 2


@pytest.mark.parametrize(
    "value",
    [
        "198.51.100.24",          # the exact escape that produced CD-ASR-F04
        "10.0.0.0/8",             # a CIDR block
        "https://api.example.com/v1",  # a URL
        "*.example.org",          # a wildcard
        "cd-store",               # a container-network service name
        "0xc6.33.64.18",          # a hex-dotted address
        "API.EXAMPLE.COM",        # not canonical lower case
        "example.com.",           # a trailing dot
        "api.example.com:443",    # a port
        "-bad.example.com",       # a leading hyphen
        "localhost",              # a single label
        "",                       # nothing
    ],
)
def test_these_forms_are_not_declarable_destinations(value: str):
    """None of these is REJECTED — each simply fails to be the one admissible shape.

    That distinction is the finding. A rule that rejected IP literals would be a rule about
    IP literals, and the next auditor would write a CIDR. This rule never asks what the value
    is.
    """
    assert not _hostname_is_declarable(value)


@pytest.mark.parametrize(
    "value",
    ["data.example.org", "api.example.co.uk", "a-b.example.com", "xn--bcher-kva.example"],
)
def test_an_ordinary_hostname_is_declarable(value: str):
    """A closure that forbids the product is not a closure."""
    assert _hostname_is_declarable(value)


def test_every_registered_host_is_declarable_and_unique(destinations: list):
    hosts = [entry["host"] for entry in destinations]
    for host in hosts:
        assert _hostname_is_declarable(host), f"{host!r} is not a declarable hostname"
    assert len(set(hosts)) == len(hosts), "a host is registered more than once"


def test_every_registered_destination_is_attributable(destinations: list):
    """An operator, a purpose and the clause of product intent that authorises it."""
    for position, entry in enumerate(destinations):
        for field in ("id", "operator", "purpose", "declared_in"):
            assert str(entry.get(field) or "").strip(), (
                f"destination #{position} declares no {field}. A destination with no "
                "operator cannot be attributed, one with no purpose cannot be reviewed, and "
                "one with no declared_in clause is a route nobody with product authority "
                "agreed to."
            )


def test_every_registered_destination_names_only_allowlist_services(
    destinations: list, services: dict
):
    """BLUEPRINT §13 gives cd-engine, cd-public, cd-private and cd-store no egress at all.

    A destination registered for one of them is a declaration that contradicts the criterion
    before any allowlist names it.
    """
    for position, entry in enumerate(destinations):
        named = entry["services"]
        assert isinstance(named, list) and named, (
            f"destination #{position} names no services"
        )
        for service_name in named:
            assert service_name in services, (
                f"destination #{position} names service {service_name!r}, which does not "
                "exist in the compose file"
            )
            policy = services[service_name]["x-egress"]["policy"]
            assert policy == "ALLOWLIST", (
                f"destination #{position} is registered for {service_name!r}, which "
                f"declares policy {policy!r}"
            )


def test_destination_ids_are_unique(destinations: list):
    identifiers = [entry["id"] for entry in destinations]
    assert len(set(identifiers)) == len(identifiers)


# --- the declaration says what it does not do -------------------------------------------- #


def test_the_compose_contract_declares_the_deny_by_default_invariants():
    """The invariants live in the compose file's own contract block, not only in the guard.

    CD-RULE-004 requires a declared limit to be stated consistently in the check header, the
    register entry and the execution contract. The compose contract is the fourth place, and
    it is the one the WO-3 egress lane will read first.
    """
    contract = load_compose(COMPOSE_PATH)["x-cd-egress-contract"]
    declared = {invariant["id"] for invariant in contract["invariants"]}
    assert {
        "CD-EGRESS-001",
        "CD-EGRESS-002",
        "CD-EGRESS-003",
        "CD-EGRESS-004",
        "CD-EGRESS-005",
        "CD-EGRESS-006",
        "CD-EGRESS-007",
    } <= declared


def test_the_registry_states_that_it_enforces_nothing():
    """Compose has no per-host egress primitive and the file must keep saying so.

    A declaration that implied it stopped a packet would misdirect the auditor to a layer
    that does not hold, which is the specific failure CD-RULE-006 was written for.
    """
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    assert "no per-host egress primitive" in text
    assert "WO-3" in text


# --- CD-EGRESS-007: a pending entry declares an OMISSION, not a destination -------------- #
#
# CD-PL-F59. `pending` had layer 2 and no layer 1, so `198.51.100.24` written there passed
# exactly as it had passed in `hosts` before deny-by-default arrived. Layer 1 here is NOT the
# destination registry — a pending entry exists BECAUSE the host is unknown, so requiring it
# to name a registered destination would either be unsatisfiable or would force this seat to
# invent the hostname the project recorded as owed (CD-RULE-003). It is the CLOSED ENTRY
# SHAPE instead: there is no field in a pending entry that can hold a destination at all.


def test_every_service_declares_pending_as_a_list(services: dict):
    """An absent or differently typed `pending` is the whole field leaving the guard's reach.

    The guard reached `pending` through `isinstance(pending, list)` and nothing else, so
    writing it as a mapping made every assertion over it disappear — silently, visible only
    as an assertion count that dropped from 53 to 52 and that nobody was watching. This is
    CD-EGRESS-003's argument about unrecognised services, applied to the container of a field.
    """
    for name, body in sorted(services.items()):
        pending = body["x-egress"].get("pending")
        assert isinstance(pending, list), (
            f"service `{name}` declares `pending` as "
            f"{'nothing at all' if pending is None else type(pending).__name__}; the "
            "contract admits a LIST and nothing else."
        )


def test_every_pending_entry_declares_exactly_the_two_omission_fields(services: dict):
    """The key set is asserted by EQUALITY, so an unrecognised key is a violation.

    `host:`, `endpoint:`, `url:`, `address:`, `target:` and every key nobody has thought of
    fail one clause, because none of them is in the declared set. That is the difference
    between this and an IP-literal detector: nothing is recognised about the VALUE at all.
    """
    for name, body in sorted(services.items()):
        for position, entry in enumerate(body["x-egress"]["pending"]):
            assert isinstance(entry, dict), (
                f"service `{name}`'s pending entry #{position} is "
                f"{type(entry).__name__}, not a mapping. A bare value here is a place "
                "somebody wrote where the record of a MISSING place belongs."
            )
            assert set(entry) == PENDING_KEYS, (
                f"service `{name}`'s pending entry #{position} declares {sorted(entry)}; a "
                f"pending entry declares EXACTLY {sorted(PENDING_KEYS)}. A host is the one "
                "thing a pending entry cannot carry — it is the record that a host is NOT "
                "KNOWN."
            )


def test_every_pending_entry_field_is_non_empty_prose(services: dict):
    """A nested mapping or list beneath an admissible key is where a destination would hide.

    The key set cannot constrain a structure it does not descend into, so the values are
    constrained instead: both fields are prose written for a human reviewer.
    """
    for name, body in sorted(services.items()):
        for position, entry in enumerate(body["x-egress"]["pending"]):
            for field_name in sorted(PENDING_KEYS):
                value = entry.get(field_name)
                assert isinstance(value, str) and value.strip(), (
                    f"service `{name}`'s pending entry #{position} declares `{field_name}` "
                    f"as {'an empty scalar' if isinstance(value, str) else type(value).__name__}"
                )


def test_no_pending_entry_carries_a_host_bearing_key(services: dict):
    """The named forms, asserted separately from the key-set equality that already covers them.

    This test would be redundant if the key set were the only rule, and that is the point:
    it is here so that WIDENING PENDING_KEYS to admit a destination field fails a test whose
    name says what was lost, rather than silently satisfying the equality test alongside it.
    """
    forbidden = {"host", "hosts", "endpoint", "endpoints", "url", "uri", "address",
                 "addr", "ip", "target", "destination", "upstream", "server"}
    assert not (PENDING_KEYS & forbidden), (
        "a pending entry's declared key set has been widened to admit a destination field. "
        "A pending entry declares the ABSENCE of a host; a field that can hold one is a "
        "contradiction in terms and reopens CD-PL-F59."
    )
    for name, body in sorted(services.items()):
        for position, entry in enumerate(body["x-egress"]["pending"]):
            stray = sorted(set(entry) & forbidden)
            assert not stray, (
                f"service `{name}`'s pending entry #{position} carries {', '.join(stray)}"
            )


def test_the_guard_declares_the_pending_residue_it_does_not_close():
    """CD-RULE-004 and CD-RULE-006. The prose residue is DECLARED, and boundary 4 is corrected.

    The defect CD-PL-F59 records is not only that an address passed in `pending`; it is that
    NONE of the six boundaries mentioned the field, while boundary 4 asserted a compensating
    layer 1 that did not exist for it. A guard closes its class or declares its limit, and
    this asserts that the declaration is present rather than trusting it to stay written.
    """
    header = (
        pathlib.Path(__file__).resolve().parents[1]
        / "tools" / "register" / "check_egress_no_broker.py"
    ).read_text(encoding="utf-8")
    assert "CD-EGRESS-007" in header
    assert "in `pending`: LAYER 1 is CD-EGRESS-007" in header, (
        "boundary 4 must name the layer-1 rule that applies to `pending` specifically"
    )
    assert "in `pending` PROSE: THERE IS NO LAYER 1" in header, (
        "boundary 4 must NOT be read as covering the prose residue declared at boundary 7"
    )
    assert "NOT PROVED TO BE CARRIED ANYWHERE" in header
