"""The container set as DESIGN — BLUEPRINT §2, deliverable A6.

Nothing here builds or starts anything. RT-B is forbidden in WO-2, and the state recorded
is CONTAINER_READY_DESIGN with CONTAINER_BUILD_NOT_YET_AUTHORISED (``PBG-RT-010``). These
are assertions over the declared design: the compose file and the Dockerfiles.

The compose file is read with :mod:`compose_reader`, a stdlib-only reader, deliberately.
The register checks that will guard these properties (deliverable B1) are stdlib-only
standalone scripts, so proving the posture readable with an instrument those checks cannot
use would prove nothing they need.

Every assertion below is written against the CLASS rather than the instance. "cd-engine
has no egress" is asserted by enumerating every service and requiring each to declare a
policy, not by looking up the four services somebody remembered.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from compose_reader import ComposeParseError, load_compose, parse_block_yaml

DEPLOY = pathlib.Path(__file__).resolve().parents[1] / "deploy"
COMPOSE_PATH = DEPLOY / "compose.yaml"
BASE_IMAGES_PATH = DEPLOY / "base-images.json"

#: The seven containers of BLUEPRINT §2. Declared here so a service added to the compose
#: file without a decision fails this test rather than arriving unnoticed.
EXPECTED_SERVICES: frozenset[str] = frozenset(
    {
        "cd-store",
        "cd-collectors",
        "cd-witness",
        "cd-engine",
        "cd-public",
        "cd-private",
        "cd-review",
    }
)

#: BLUEPRINT §2: "engine, both surfaces and the store have no route out of the network at
#: all". These four declare policy NONE; the other three declare an allowlist.
NO_EGRESS_SERVICES: frozenset[str] = frozenset(
    {"cd-engine", "cd-public", "cd-private", "cd-store"}
)
ALLOWLIST_SERVICES: frozenset[str] = frozenset(
    {"cd-collectors", "cd-witness", "cd-review"}
)

EXPECTED_NETWORKS: frozenset[str] = frozenset({"cd-net-private", "cd-net-public"})

#: The two surfaces, and the only two published ports in the system.
EXPECTED_PORTS: dict[str, str] = {
    "cd-public": "127.0.0.1:8710:8710",
    "cd-private": "127.0.0.1:8711:8711",
}

DOCKERFILES: tuple[pathlib.Path, ...] = tuple(sorted(DEPLOY.glob("Dockerfile.*")))

_DIGEST_REFERENCE = re.compile(r"^[a-z0-9./_-]+@sha256:[0-9a-f]{64}$")


@pytest.fixture(scope="module")
def compose() -> dict:
    return load_compose(COMPOSE_PATH)


@pytest.fixture(scope="module")
def services(compose: dict) -> dict:
    return compose["services"]


# --- THE READER ITSELF, PROVED AT ITS OWN SEAM ------------------------------------------- #

def test_the_compose_file_is_machine_readable_with_the_standard_library_alone():
    """The posture is DATA, not prose. A comment is not a posture.

    If this fails, every other assertion in this module is unverifiable and so is the
    register check that will read the same file, which is why it is the first test here.
    """
    document = load_compose(COMPOSE_PATH)
    assert isinstance(document, dict)
    assert "services" in document


def test_the_reader_refuses_what_it_cannot_parse_rather_than_guessing():
    """A parser that guesses is a check that passes for a reason nobody can state."""
    with pytest.raises(ComposeParseError):
        parse_block_yaml("services:\n  cd-engine:\n    ports: [1, 2, 3]\n")
    with pytest.raises(ComposeParseError):
        parse_block_yaml("a:\n\tb: 1\n")


def test_the_reader_does_not_expand_aliases_so_a_hidden_posture_reads_as_absent():
    """Every posture field is written literally on each service, and this is why.

    A field reachable only by expanding a YAML anchor would be invisible to a stdlib
    check. Recording the alias unresolved makes that failure loud instead of silent.
    """
    document = parse_block_yaml(
        "x-common: &common\n  policy: NONE\nservices:\n  s:\n    <<: *common\n"
    )
    assert document["services"]["s"] == {"<<": "*common"}


# --- THE SEVEN SERVICES AND THE TWO NETWORKS ---------------------------------------------- #

def test_all_seven_services_are_declared(services: dict):
    assert set(services) == EXPECTED_SERVICES


def test_exactly_two_networks_are_declared(compose: dict):
    """BLUEPRINT §2 describes two. A third would be a Blueprint change, not a compose edit."""
    assert set(compose["networks"]) == EXPECTED_NETWORKS


def test_both_networks_are_internal(compose: dict):
    """`internal: true` is what makes "no egress" structural rather than a firewall habit."""
    for name, network in compose["networks"].items():
        assert network.get("internal") == "true", (
            f"network {name} is not internal; a service attached to it would have egress "
            "by topology, whatever its x-egress block claims"
        )


def test_every_service_is_attached_to_at_least_one_declared_network(services: dict):
    for name, service in services.items():
        attached = service.get("networks")
        assert attached, f"{name} declares no network"
        unknown = set(attached) - EXPECTED_NETWORKS
        assert not unknown, f"{name} attaches to undeclared network(s) {sorted(unknown)}"


def test_only_cd_public_is_on_the_public_network(services: dict):
    """BLUEPRINT §2: cd-net-public carries cd-public and nothing else."""
    on_public = {
        name
        for name, service in services.items()
        if "cd-net-public" in (service.get("networks") or [])
    }
    assert on_public == {"cd-public"}


# --- EGRESS, WHICH CD-AC-012 IS PLANTED AGAINST -------------------------------------------- #

def test_every_service_declares_an_egress_policy(services: dict):
    """CD-EGRESS-003. A service with no block is a violation, never a default.

    A check that skips a service it does not recognise is a check an author bypasses by
    adding a service (``PBG-CI-002``).
    """
    missing = [name for name, service in services.items() if "x-egress" not in service]
    assert missing == [], f"services with no declared egress posture: {missing}"


def test_every_egress_policy_is_a_declared_member_of_the_enum(services: dict):
    for name, service in services.items():
        policy = service["x-egress"].get("policy")
        assert policy in {"NONE", "ALLOWLIST"}, (
            f"{name} declares egress policy {policy!r}, which is not one of the two "
            "declared values. An unrecognised policy is not a lenient policy."
        )


def test_the_four_zero_egress_services_declare_none_with_an_empty_allowlist(services: dict):
    """CD-EGRESS-001, CD-AC-012: there is nowhere for an execution pathway to go."""
    for name in sorted(NO_EGRESS_SERVICES):
        egress = services[name]["x-egress"]
        assert egress["policy"] == "NONE", f"{name} must have no egress at all"
        assert egress["hosts"] == [], (
            f"{name} declares policy NONE and a non-empty allowlist; those cannot both "
            "be true"
        )
        assert egress.get("pending") == [], (
            f"{name} declares a pending egress endpoint. A service with no egress has "
            "nothing pending — recording one is planning to widen it later."
        )


def test_the_zero_egress_services_are_structurally_unable_to_reach_out(
    compose: dict, services: dict
):
    """The policy is not taken on trust: it must follow from the network topology.

    A service whose declared policy is NONE while it sits on an externally routed network
    is a claim contradicted by the file that carries it.
    """
    for name in sorted(NO_EGRESS_SERVICES):
        for network in services[name]["networks"]:
            assert compose["networks"][network].get("internal") == "true", (
                f"{name} declares no egress but is attached to {network}, which is not "
                "internal"
            )


def test_the_three_allowlist_services_are_exactly_the_ones_blueprint_names(services: dict):
    declared = {
        name
        for name, service in services.items()
        if service["x-egress"]["policy"] == "ALLOWLIST"
    }
    assert declared == ALLOWLIST_SERVICES


#: The ONLY hosts any allowlist may name (WO-1.2b). Each is the feed a Matt-ratified
#: mapping row declares (governance/mapping/indicator_mapping.yaml, 2026-08-24). Widening
#: this set is a decision with a record: change it here, deliberately, and cite the row.
#:
#: NARROWING IS ALSO A DECISION WITH A RECORD, and WO-1.20 is one: ``prices.lbma.org.uk`` was
#: added at WO-1.6 for the LBMA gold fix and is REMOVED here with the ingredient and adapter
#: that were its only caller (Owner-confirmed 2026-10-17). ``gold_real_rate_cross``'s gold leg
#: is now the COMEX front-month close on ``query1.finance.yahoo.com``, which the ratified row
#: declares as ``market:GC`` and which is already on this list — so the retirement takes a host
#: AWAY and adds none, and the count goes from five back to four.
RATIFIED_COLLECTOR_HOSTS = [
    "fred.stlouisfed.org",
    "cdn-api.cboe.com",
    "query1.finance.yahoo.com",
    "www.multpl.com",
]


def test_only_cd_collectors_names_hosts_and_exactly_the_ratified_ones(services: dict):
    """WO-1.2b state: cd-collectors carries the ratified data hosts (four since WO-1.20), nothing else.

    cd-witness and cd-review stay empty (their endpoints are still undecided). Any extra
    or missing host in cd-collectors fails here.
    """
    for name, service in services.items():
        expected = RATIFIED_COLLECTOR_HOSTS if name == "cd-collectors" else []
        assert sorted(service["x-egress"]["hosts"]) == sorted(expected), (
            f"{name}: egress allowlist {service['x-egress']['hosts']} != {expected}. "
            "Changing an allowlist is a decision with a record, not an edit."
        )


def test_every_empty_allowlist_service_records_why_and_a_populated_one_has_nothing_pending(services: dict):
    """An empty allowlist with no explanation is indistinguishable from a forgotten one."""
    for name in sorted(ALLOWLIST_SERVICES):
        egress = services[name]["x-egress"]
        pending = egress.get("pending")
        if egress["hosts"]:
            assert not pending, f"{name} has hosts AND still lists pending entries"
            continue
        assert pending, (
            f"{name} declares an empty allowlist and records nothing pending. The "
            "omission must be visible now rather than discovered later."
        )
        for entry in pending:
            assert entry.get("declared_in"), f"{name}: a pending entry names no source"
            assert entry.get("blocked_by"), f"{name}: a pending entry states no blocker"


def test_every_service_states_what_enforces_its_egress_policy(services: dict):
    for name, service in services.items():
        assert service["x-egress"].get("enforced_by"), (
            f"{name} declares a policy and names no instrument that makes it true. A "
            "policy nothing enforces is a preference."
        )


# --- BOTH SURFACES BOUND TO LOOPBACK ONLY --------------------------------------------------- #

def test_only_the_two_surfaces_publish_a_port(services: dict):
    publishing = {name for name, service in services.items() if service.get("ports")}
    assert publishing == set(EXPECTED_PORTS)


def test_the_store_publishes_no_port(services: dict):
    """The store is reachable only from containers on cd-net-private."""
    assert not services["cd-store"].get("ports")


def test_every_published_port_is_bound_to_loopback(services: dict):
    """CD-D-006, CD-HOLD-005: nothing is publicly reachable until Matt says so.

    Asserted over EVERY published port rather than the two expected ones, so a third port
    added later is caught by the same line.
    """
    for name, service in services.items():
        for published in service.get("ports") or []:
            assert published.startswith("127.0.0.1:"), (
                f"{name} publishes {published!r}, which is not bound to loopback. A "
                "port without the 127.0.0.1 prefix is reachable from the network."
            )


def test_the_two_surfaces_publish_the_ports_blueprint_declares(services: dict):
    for name, expected in EXPECTED_PORTS.items():
        assert services[name]["ports"] == [expected]


def test_each_surface_records_that_it_is_not_publicly_reachable(services: dict):
    for name in EXPECTED_PORTS:
        surface = services[name]["x-surface"]
        assert surface["publicly_reachable"] == "false"
        assert surface["held_by"]


# --- NON-ROOT, DECLARED PER SERVICE (PBG-RT-012) --------------------------------------------- #

def test_every_service_declares_a_non_root_user(services: dict):
    for name, service in services.items():
        user = service.get("user")
        assert user, f"{name} declares no user and would inherit the image's default"
        uid_text = user.split(":")[0]
        assert uid_text.isdigit(), (
            f"{name} declares user {user!r} by name. Some orchestrators enforce "
            "runAsNonRoot by inspecting the UID and cannot resolve a name."
        )
        assert int(uid_text) != 0, f"{name} runs as root"


def test_the_declared_uid_matches_the_machine_readable_one(services: dict):
    """Two statements of the same fact must agree, or one of them is a bug scheduled."""
    for name, service in services.items():
        assert str(service["x-uid"]) == service["user"].split(":")[0], name


def test_every_service_has_a_distinct_uid(services: dict):
    """A compromised container's identity must not be every container's identity."""
    uids = [service["x-uid"] for service in services.values()]
    assert len(set(uids)) == len(uids), f"duplicate UIDs across services: {uids}"


# --- THE THREE STORAGE CLASSES, SEPARATED (PBG-RT-013) ---------------------------------------- #

def test_every_service_declares_its_three_storage_classes(services: dict):
    for name, service in services.items():
        storage = service.get("x-storage")
        assert storage, f"{name} declares no storage classes"
        assert set(storage) == {"image", "tmpfs", "durable"}, name


def test_only_the_store_declares_durable_storage(services: dict):
    """One named volume, and it belongs to the store alone."""
    with_durable = {
        name for name, service in services.items() if service["x-storage"]["durable"]
    }
    assert with_durable == {"cd-store"}


def test_exactly_one_named_volume_exists_and_it_is_the_stores(compose: dict, services: dict):
    assert set(compose["volumes"]) == {"cd-store-data"}
    mounting = set()
    for name, service in services.items():
        for mount in service.get("volumes") or []:
            if isinstance(mount, dict) and mount.get("source") == "cd-store-data":
                mounting.add(name)
    assert mounting == {"cd-store"}


@pytest.mark.parametrize("path", DOCKERFILES, ids=lambda p: p.name)
def test_no_dockerfile_declares_a_volume(path: pathlib.Path):
    """PBG-RT-013. `VOLUME` declares the DURABLE class, and no application image has one.

    An earlier draft declared `VOLUME ["/contracts"]`. /contracts is read-only
    configuration — the IMAGE class — and mixing the two is not cosmetic: outside compose,
    `VOLUME` makes Docker create an anonymous writable volume at that path, so a system
    whose design says "exactly one named volume exists and it is the store's" would grow
    six more that nobody declared and nothing cleans up.

    Asserted over INSTRUCTIONS rather than the word, so the reasoning above can be written
    in a comment without the test failing on its own explanation.
    """
    instructions = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("VOLUME ")
    ]
    assert instructions == [], (
        f"{path.name} declares {instructions}. The store's named volume is the only "
        "durable storage in this system, and it is declared in compose, not in an image."
    )


def test_the_only_durable_storage_in_the_system_is_declared_in_compose(compose: dict):
    """The same property from the other end: one named volume, and it is the store's.

    This is the assertion the Dockerfile check protects. Together they say the durable
    class is declared in exactly one place, which is what makes it reviewable.
    """
    assert set(compose["volumes"]) == {"cd-store-data"}


def test_no_service_may_write_into_its_own_code_directory():
    """`read_only: true` is inherited from the shared hardening fragment.

    Asserted on the file's text rather than through the reader, because the reader
    deliberately does not expand anchors. The fragment is the single place the property is
    declared, so the property is checked where it is declared.
    """
    text = COMPOSE_PATH.read_text(encoding="utf-8")
    assert "read_only: true" in text
    assert "read_only: false" not in text


def test_every_service_that_validates_an_envelope_mounts_contracts_read_only():
    """`contracts/` is mounted read-only and located through $CD_CONTRACTS_DIR."""
    text = COMPOSE_PATH.read_text(encoding="utf-8")
    assert "source: ../contracts" in text
    assert "target: /contracts" in text
    assert "read_only: true" in text
    assert "CD_CONTRACTS_DIR: /contracts" in text


# --- IMAGE IDENTITY IS THE DIGEST ------------------------------------------------------------- #

def test_every_compose_image_reference_is_pinned_by_digest(services: dict):
    """A tag is a mutable pointer. A digest is an identity (Standards Baseline §3)."""
    for name, service in services.items():
        reference = service.get("image")
        if reference is None:
            assert service.get("build"), f"{name} declares neither an image nor a build"
            continue
        assert _DIGEST_REFERENCE.match(reference), (
            f"{name} references {reference!r}, which is not <name>@sha256:<64 hex>"
        )


def test_the_store_uses_the_digest_this_seat_observed_on_this_host(services: dict):
    """Recorded because it was observed, not because it was expected."""
    pins = json.loads(BASE_IMAGES_PATH.read_text(encoding="utf-8"))["pins"]
    store_pin = next(pin for pin in pins if pin["id"] == "cd-store-base")
    assert store_pin["status"] == "RESOLVED"
    assert services["cd-store"]["image"] == store_pin["reference"]
    assert store_pin["observed_how"].startswith("docker image inspect")


def test_the_unresolved_python_base_is_recorded_as_unresolved_and_not_invented():
    """A digest nobody verified must not appear anywhere. Absence is the honest answer."""
    pins = json.loads(BASE_IMAGES_PATH.read_text(encoding="utf-8"))["pins"]
    python_pin = next(pin for pin in pins if pin["id"] == "cd-python-base")
    assert python_pin["status"] == "DIGEST_NOT_RESOLVED"
    assert python_pin["reference"] is None
    assert python_pin["why_unresolved"]
    assert python_pin["owed_at"].startswith("WO-3")


def test_every_build_passes_the_base_image_through_as_a_required_variable(services: dict):
    for name, service in services.items():
        build = service.get("build")
        if build is None:
            continue
        base = build["args"]["CD_PYTHON_BASE"]
        assert base.startswith("${CD_PYTHON_BASE:?"), (
            f"{name} would build with an unchecked base image reference; `:?` is what "
            "makes an unset variable a refusal rather than an empty string"
        )


# --- THE DOCKERFILES ----------------------------------------------------------------------------- #

def test_there_is_one_dockerfile_per_application_service():
    """cd-store uses a pinned upstream image and has no Dockerfile."""
    names = {path.name.split(".", 1)[1] for path in DOCKERFILES}
    assert names == {"collectors", "witness", "engine", "public", "private", "review"}


def test_the_dockerfile_scan_is_not_vacuous():
    assert len(DOCKERFILES) == 6


@pytest.mark.parametrize("path", DOCKERFILES, ids=lambda p: p.name)
def test_no_dockerfile_carries_a_tag_only_base_reference(path: pathlib.Path):
    """A tag-only FROM must be impossible here, not merely absent today."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("FROM "):
            continue
        reference = line.split()[1]
        if reference.startswith("${"):
            continue
        assert _DIGEST_REFERENCE.match(reference), (
            f"{path.name}: FROM {reference!r} is not pinned by digest"
        )


@pytest.mark.parametrize("path", DOCKERFILES, ids=lambda p: p.name)
def test_every_dockerfile_base_argument_has_no_default(path: pathlib.Path):
    """`ARG CD_PYTHON_BASE=<anything>` would be a value nobody re-examined."""
    text = path.read_text(encoding="utf-8")
    assert "ARG CD_PYTHON_BASE\n" in text
    assert "ARG CD_PYTHON_BASE=" not in text
    assert "FROM ${CD_PYTHON_BASE}" in text


@pytest.mark.parametrize("path", DOCKERFILES, ids=lambda p: p.name)
def test_every_dockerfile_declares_a_numeric_non_root_user(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    users = [line for line in text.splitlines() if line.startswith("USER ")]
    assert len(users) == 1, f"{path.name}: expected exactly one USER instruction"
    uid = users[0].split()[1].split(":")[0]
    assert uid.isdigit() and int(uid) != 0, f"{path.name}: USER {uid!r}"


def test_the_dockerfile_uid_matches_the_compose_uid(services: dict):
    for path in DOCKERFILES:
        service = "cd-" + path.name.split(".", 1)[1]
        text = path.read_text(encoding="utf-8")
        uid = next(
            line for line in text.splitlines() if line.startswith("USER ")
        ).split()[1].split(":")[0]
        assert uid == str(services[service]["x-uid"]), path.name


@pytest.mark.parametrize("path", DOCKERFILES, ids=lambda p: p.name)
def test_every_dockerfile_handles_sigterm_and_uses_exec_form(path: pathlib.Path):
    """Shell form makes /bin/sh PID 1, and the shell does not forward SIGTERM."""
    text = path.read_text(encoding="utf-8")
    assert "STOPSIGNAL SIGTERM" in text
    entrypoints = [
        line for line in text.splitlines() if line.startswith("ENTRYPOINT ")
    ]
    assert len(entrypoints) == 1, path.name
    assert entrypoints[0].startswith('ENTRYPOINT ["'), (
        f"{path.name}: ENTRYPOINT is not in exec form"
    )
    assert "python3" in entrypoints[0]


@pytest.mark.parametrize("path", DOCKERFILES, ids=lambda p: p.name)
def test_no_dockerfile_writes_bytecode_into_its_read_only_code_directory(
    path: pathlib.Path,
):
    text = path.read_text(encoding="utf-8")
    assert "PYTHONDONTWRITEBYTECODE=1" in text
    assert '"-B"' in text


# --- NO SECRET VALUE ANYWHERE (PBG-SEC-002, non-waivable) -------------------------------------- #

_SECRET_ENV_NAMES = (
    "CD_STORE_MIGRATOR_PASSWORD",
    "CD_STORE_COLLECTOR_PASSWORD",
    "CD_STORE_WITNESS_PASSWORD",
    "CD_STORE_ENGINE_PASSWORD",
    "CD_STORE_PUBLIC_PASSWORD",
    "CD_STORE_PRIVATE_PASSWORD",
    "CD_STORE_REVIEW_PASSWORD",
    "CD_MODEL_API_KEY",
)


@pytest.mark.parametrize("variable", _SECRET_ENV_NAMES)
def test_every_secret_is_referenced_by_name_and_never_carries_a_value(variable: str):
    """Every occurrence of a secret name in the deploy tree is a reference, never an
    assignment of a literal.

    Checked over the whole deploy directory rather than over compose.yaml alone: a secret
    smuggled into a Dockerfile ARG is in the image regardless of what compose says.
    """
    reference = re.compile(r"\$\{[^}]*\}")
    assignment = re.compile(rf"{re.escape(variable)}\s*[:=]\s*(?P<value>\S.*)$")
    for path in sorted(DEPLOY.rglob("*")):
        if not path.is_file():
            continue
        # CD-ENG-F30, found in increment 4. `__pycache__` is EXCLUDED, and nothing else
        # is. A .pyc is compiled output of a .py this sweep already reads, so excluding it
        # loses no coverage — and including it made this test raise UnicodeDecodeError on
        # any tree where an entrypoint had ever been imported. A test that fails because
        # the interpreter cached bytecode is a test that gets ignored, which is a worse
        # outcome for a secret guard than the one it was protecting against.
        if "__pycache__" in path.parts:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            # NOT a skip. Any OTHER undecodable file in deploy/ is a FAILURE: a binary
            # blob is exactly where a credential would not be looked for, and this sweep
            # must not pass over what it cannot read (PBG-CI-002).
            raise AssertionError(
                f"{path.relative_to(DEPLOY)} in the deploy tree is not UTF-8 text "
                f"({exc}), so this secret sweep cannot read it. An unreadable file is a "
                "failure, never a file to pass over: it is precisely where a credential "
                "would not be looked for. Remove it or state why it belongs here."
            ) from exc
        for number, line in enumerate(content.splitlines(), start=1):
            if variable not in line:
                continue
            # Every `${...}` on the line is a REFERENCE and carries no value. Remove them
            # first, then look at what is left: if the name still appears with something
            # assigned to it, that something is a literal.
            residue = reference.sub("", line)
            match = assignment.search(residue)
            if match is None:
                continue
            literal = match.group("value").strip().strip("\"'").strip()
            assert not literal, (
                f"{path.name}:{number}: {variable} is assigned {literal!r} outside a "
                "${...} reference. Secrets are referenced by env-var NAME only "
                "(PBG-SEC-002, non-waivable)."
            )


def test_the_secret_guard_bites_when_a_literal_is_planted():
    """PBG-ASSURE-017: prove the check fails when the thing it checks is broken.

    A guard nobody has seen refuse anything is a rumour. The planted string is obviously
    not a credential — a real one must never be written anywhere, including into a test
    that exists to prove real ones are refused.
    """
    reference = re.compile(r"\$\{[^}]*\}")
    variable = "CD_STORE_ENGINE_PASSWORD"
    assignment = re.compile(rf"{re.escape(variable)}\s*[:=]\s*(?P<value>\S.*)$")

    def refuses(line: str) -> bool:
        match = assignment.search(reference.sub("", line))
        return match is not None and bool(match.group("value").strip().strip("\"'").strip())

    assert refuses(f'      {variable}: "PLANTED-NOT-A-CREDENTIAL"')
    assert refuses(f"      {variable}=PLANTED-NOT-A-CREDENTIAL")
    assert not refuses(f'      {variable}: "${{{variable}:?must be set}}"')


def test_the_deploy_tree_contains_no_env_file():
    """A committed .env is a secret in Git, and Git history is not erased by a deletion."""
    offenders = [
        path.name
        for path in DEPLOY.rglob("*")
        if path.is_file() and path.name.startswith(".env")
    ]
    assert offenders == []
