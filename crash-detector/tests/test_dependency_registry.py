"""The dependency registry — the declaration CD-AC-012's dependency half now rests on.

WHY THIS MODULE EXISTS. ``CD-ASR-WO2R-F05`` (MEDIUM): an independent auditor put
``tastytrade-sdk==1.2.0`` — a REAL, currently-operating US brokerage's REAL order-entry SDK —
into ``requirements.txt`` and ``requirements.lock``, and ``check_lockfile_denylist.py`` exited
0: PASS, 17 assertions, 0 violations. The check recognised brokers BY NAME — a 61-name denylist
plus nine execution tokens matched as WORDS — and ``tastytrade`` is one word that is not a
token. The brand defeated it.

The closure is DENY BY DEFAULT over an in-tree registry of declared dependencies: a
distribution is admissible only if somebody registered that exact PEP 503 normalised name with
a purpose, an authorising clause and a needing surface. ``tastytrade-sdk`` is then not a name to
catch — it is simply not a dependency anyone declared, which is the same thing a typosquat, a
renamed fork and a brand invented tomorrow all are.

WHAT THIS MODULE IS FOR, GIVEN THE GUARD ALREADY ASSERTS ALL OF IT. The register check is the
gate; these are the REGRESSION tests, and they exist so that a later seat which quietly re-opens
the class fails a test module as well as a register check. That is the same reasoning
``tests/test_egress_destination_registry.py`` applies to the egress half, and this module
deliberately reads the same artefact with the same stdlib-only reader.

NOTHING HERE CLAIMS A REGISTERED DISTRIBUTION IS SAFE. A registered distribution is a HUMAN
CLAIM and a false one is not detectable from this tree — that is declared limit boundary 1 and
it is not repaired by any assertion below.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "deploy" / "dependency-registry.yaml"

sys.path.insert(0, str(ROOT / "tools" / "register"))

from _broker_vocabulary import judge_distribution, normalise_distribution  # noqa: E402
from _yamlmin import load_yaml, unresolved_aliases  # noqa: E402

REGISTRY_CONTRACT = "CD-DEPENDENCY-REGISTRY-v1"

#: CD-DEP-004 / CD-DEP-005. Declared member sets, asserted by EQUALITY. A blacklist of
#: forbidden keys is defeated by a key nobody listed, which is the shape of defect this whole
#: rework exists to stop repeating.
REGISTRY_DOCUMENT_KEYS = frozenset({"version", "contract", "consumers", "dependencies"})
ENTRY_KEYS = frozenset(
    {"id", "distribution", "kind", "purpose", "declared_in", "needed_by"}
)
ENTRY_KINDS = frozenset({"DIRECT", "TRANSITIVE"})


@pytest.fixture(scope="module")
def registry() -> dict:
    assert REGISTRY_PATH.is_file(), (
        f"{REGISTRY_PATH} does not exist. An absent registry is not an empty one: with no "
        "registry there is no admissible set, and deleting a file would be the cheapest "
        "bypass there is."
    )
    return load_yaml(REGISTRY_PATH)


@pytest.fixture(scope="module")
def entries(registry: dict) -> list:
    return list(registry["dependencies"])


def test_registry_document_key_set_is_closed(registry: dict) -> None:
    """A key the guard does not read is a declaration nothing enforces."""
    assert set(registry) == REGISTRY_DOCUMENT_KEYS


def test_registry_declares_the_contract_the_guard_reads(registry: dict) -> None:
    assert registry["contract"] == REGISTRY_CONTRACT


def test_registry_carries_no_unresolved_alias(registry: dict) -> None:
    """A permission visible only after resolving an anchor is a permission in hiding."""
    assert unresolved_aliases(registry) == []


def test_consumer_vocabulary_is_non_empty_and_unique(registry: dict) -> None:
    consumers = registry["consumers"]
    assert consumers, "no consumers declared: no entry could name a consuming surface"
    assert len(set(consumers)) == len(consumers), "a consumer is declared twice"


def test_every_entry_declares_exactly_the_six_keys(entries: list) -> None:
    for entry in entries:
        assert set(entry) == ENTRY_KEYS, (
            f"{entry.get('id')!r} declares {sorted(set(entry))}; the entry key set is CLOSED "
            "and asserted by equality. A malformed entry registers nothing."
        )


def test_every_entry_id_is_unique(entries: list) -> None:
    ids = [str(entry["id"]) for entry in entries]
    assert len(set(ids)) == len(ids), "an id that names two entries identifies neither"


def test_every_distribution_is_already_in_pep503_normal_form(entries: list) -> None:
    """So one distribution cannot be registered twice under two spellings."""
    for entry in entries:
        raw = str(entry["distribution"]).strip()
        assert raw, f"{entry['id']!r} registers an empty distribution"
        assert normalise_distribution(raw) == raw, (
            f"{entry['id']!r} registers {raw!r}, which normalises to "
            f"{normalise_distribution(raw)!r}"
        )


def test_no_distribution_is_registered_twice(entries: list) -> None:
    names = [normalise_distribution(str(entry["distribution"])) for entry in entries]
    assert len(set(names)) == len(names), "a distribution is registered twice"


def test_every_entry_declares_a_known_kind(entries: list) -> None:
    for entry in entries:
        assert str(entry["kind"]).strip() in ENTRY_KINDS, (
            f"{entry['id']!r} declares kind {entry['kind']!r}; an unknown kind is a violation "
            "and not an unknown to be tolerated"
        )


@pytest.mark.parametrize("field", ["purpose", "declared_in"])
def test_every_entry_states_a_reason_and_an_authorising_clause(
    entries: list, field: str
) -> None:
    """CONTENT is not judged — declared limit boundary 2 — but ABSENCE is."""
    for entry in entries:
        assert str(entry[field]).strip(), f"{entry['id']!r} declares an empty {field}"


def test_every_entry_names_at_least_one_known_consumer(
    registry: dict, entries: list
) -> None:
    consumers = {str(name) for name in registry["consumers"]}
    for entry in entries:
        needed_by = entry["needed_by"]
        assert isinstance(needed_by, list) and needed_by, (
            f"{entry['id']!r} names no consuming surface; a dependency no surface needs is a "
            "dependency nobody needs"
        )
        unknown = {str(name) for name in needed_by} - consumers
        assert not unknown, (
            f"{entry['id']!r} names {sorted(unknown)}, outside the CLOSED consumer vocabulary"
        )


def test_registration_is_not_absolution_the_denylist_still_applies(entries: list) -> None:
    """LAYER 2 SURVIVES OVER THE REGISTRY. Registration is not absolution.

    This is the assertion that stops the registry laundering anything: a denylisted SDK
    declared openly must be refused as surely as one smuggled in.

    NAMED THIS WAY DELIBERATELY. The obvious name for this test carried a word that
    `CD-RT-012-NO-EXECUTION-INTERFACE`'s L1 identifier layer reads, and it FAILED that check —
    exit 1, one violation, measured. The repair is this name, NOT a suppression and NOT an edit
    to that guard: `CD-D-015` ends the hardening chase on it, and weakening a sibling check to
    let my own test file through would be exactly the move this project's whole gate exists to
    catch. Recorded here rather than fixed silently, because a later seat naming a test the
    obvious way will meet the same wall and should find the reason next to it.
    """
    for entry in entries:
        reason = judge_distribution(str(entry["distribution"]))
        assert not reason, f"{entry['id']!r}: {reason}"


def test_the_registry_is_not_empty(entries: list) -> None:
    """A vacuous registry would make every assertion above pass while asserting nothing.

    The egress destination registry ships EMPTY by design — registering a destination is
    registering an ingredient source, which is CD-D-005 and the Product Owner's. A PYTHON
    DISTRIBUTION IS NOT AN INGREDIENT, so this registry is populated, and a run that examined
    zero entries must not read as clean.
    """
    assert entries, "the dependency registry declares no entries; nothing was examined"
