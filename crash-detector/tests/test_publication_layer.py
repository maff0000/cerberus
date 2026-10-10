"""C1 — the publication layer. **Both envelopes judged before either is written.**

BLUEPRINT §8, ``CD-AC-006``, ``CD-AC-002``, ``CD-AC-008``.

The measurable claim is about ORDER, so every test here reads the recording connection's
JOURNAL rather than a return value: *"nothing was written"* is a statement about what
statements were issued, and a function that returns ``None`` after writing a row would
satisfy any assertion made about its return.

**NO SOURCE IS REGISTERED BY ANYTHING IN THIS FILE** (``Q25``, ``CD-PL-F154``). Both dials
are ``UNKNOWN`` with nothing to name, which is the shipped WO-2 state — see
``tests/publication_fakes.py``.
"""

from __future__ import annotations

import pytest

from crash_detector.publication.alerting import ALERT_PUBLICATION_REFUSAL, AlertRefused
from crash_detector.publication.envelope_contract import (
    REFUSAL_PRIVATE_CLASSIFIED_KEY,
    REFUSAL_SCHEMA_VIOLATION,
    REFUSAL_UNKNOWN_KEY,
    EnvelopeSurface,
    PublicationRefused,
)
from crash_detector.publication.publish import (
    PublishOutcome,
    publish_cycle,
    refusal_subject_ref,
)

from publication_fakes import (
    SYNTHETIC_CONFIG_SNAPSHOT_ID,
    RecordingConnection,
    private_envelope,
    public_envelope,
)

ENVELOPE_TABLES = (
    "publication.public_envelope",
    "publication.private_envelope",
    "publication.heartbeat",
)


# --- THE ADMITTING ARM ------------------------------------------------------------------- #

def test_a_conforming_pair_is_written():
    """Without this arm every refusal below is consistent with a layer that refuses all."""
    connection = RecordingConnection(returning_id=77)
    outcome = publish_cycle(
        connection,
        public_envelope=public_envelope(),
        private_envelope=private_envelope(),
    )
    assert isinstance(outcome, PublishOutcome)
    assert outcome.public_written and outcome.private_written and outcome.heartbeat_written
    assert outcome.public_envelope_id == 77
    for table in ENVELOPE_TABLES:
        assert len(connection.statements_touching(table)) == 1
    assert connection.statements_touching("alert.event") == []


def test_the_three_writes_happen_in_one_transaction_and_commit_once():
    connection = RecordingConnection()
    publish_cycle(
        connection,
        public_envelope=public_envelope(),
        private_envelope=private_envelope(),
    )
    kinds = [entry[0] for entry in connection.journal]
    assert kinds == ["execute", "execute", "execute", "commit"]


def test_the_heartbeat_names_the_envelope_it_attests():
    connection = RecordingConnection(returning_id=99)
    publish_cycle(
        connection,
        public_envelope=public_envelope(),
        private_envelope=private_envelope(),
    )
    (parameters,) = connection.parameters_for("publication.heartbeat")
    assert parameters[1] == 99


def test_the_inserted_columns_are_read_out_of_the_document():
    """``*_columns_agree_with_document`` is a CHECK constraint; a signature that let a
    caller pass a differing ``schema_version`` would let them build the row it refuses."""
    connection = RecordingConnection()
    publish_cycle(
        connection,
        public_envelope=public_envelope(),
        private_envelope=private_envelope(),
    )
    (public_params,) = connection.parameters_for("publication.public_envelope")
    schema_version, as_of, published, config_id, document = public_params
    assert schema_version == document["schema_version"]
    assert config_id == document["config_snapshot_id"] == SYNTHETIC_CONFIG_SNAPSHOT_ID
    assert as_of == document["as_of_utc"]
    assert published == document["published_utc"]


def test_the_stored_document_is_a_copy_the_caller_cannot_retune():
    connection = RecordingConnection()
    envelope = public_envelope()
    publish_cycle(
        connection, public_envelope=envelope, private_envelope=private_envelope()
    )
    envelope["regime"] = "MUTATED-AFTER-VALIDATION"
    (public_params,) = connection.parameters_for("publication.public_envelope")
    assert public_params[4]["regime"] == "CALM"


# --- VALIDATED BEFORE WRITTEN: THE REFUSING ARMS ------------------------------------------ #

def test_a_public_envelope_violating_its_schema_is_refused_and_NOTHING_is_written():
    connection = RecordingConnection()
    with pytest.raises(PublicationRefused) as refusal:
        publish_cycle(
            connection,
            public_envelope=public_envelope(combined_stress=0.9),
            private_envelope=private_envelope(),
        )
    assert refusal.value.reason_class == REFUSAL_UNKNOWN_KEY
    assert refusal.value.key == "combined_stress"
    assert connection.wrote_nothing_to(*ENVELOPE_TABLES)


def test_a_PRIVATE_envelope_violating_its_schema_also_writes_NO_PUBLIC_ENVELOPE():
    """*** THE TEST THAT DISTINGUISHES 'BOTH BEFORE EITHER' FROM 'EACH BEFORE ITS OWN'. ***

    A layer that validated the public envelope, wrote it, then validated the private one
    would leave a published public envelope for a cycle whose private counterpart never
    existed — and the public one is the one consumers have already seen. The private
    envelope is the broken one here and the PUBLIC table must still be untouched.
    """
    connection = RecordingConnection()
    with pytest.raises(PublicationRefused) as refusal:
        publish_cycle(
            connection,
            public_envelope=public_envelope(),
            private_envelope=private_envelope(book_exposure=1_000_000),
        )
    assert refusal.value.surface is EnvelopeSurface.PRIVATE
    assert connection.statements_touching("publication.public_envelope") == []
    assert connection.wrote_nothing_to(*ENVELOPE_TABLES)


def test_each_envelope_is_judged_against_ITS_OWN_contract():
    """One schema shared by both surfaces would admit each in the other's place.

    A public envelope is not a valid PRIVATE one — it lacks ``classification``, which the
    private contract marks required — and a private envelope is not a valid PUBLIC one,
    because ``classification`` is not on the public allowlist. Both directions, so the
    contrast cannot be satisfied by a single-sided check.
    """
    connection = RecordingConnection()
    with pytest.raises(PublicationRefused) as refusal:
        publish_cycle(
            connection,
            public_envelope=private_envelope(),  # carries `classification`
            private_envelope=private_envelope(),
        )
    assert refusal.value.surface is EnvelopeSurface.PUBLIC
    assert refusal.value.reason_class == REFUSAL_UNKNOWN_KEY
    assert refusal.value.key == "classification"
    assert connection.wrote_nothing_to(*ENVELOPE_TABLES)

    connection = RecordingConnection()
    with pytest.raises(PublicationRefused) as refusal:
        publish_cycle(
            connection,
            public_envelope=public_envelope(),
            private_envelope=public_envelope(),  # lacks `classification`
        )
    assert refusal.value.surface is EnvelopeSurface.PRIVATE
    assert refusal.value.reason_class == REFUSAL_SCHEMA_VIOLATION
    assert connection.wrote_nothing_to(*ENVELOPE_TABLES)


# --- CD-AC-006: THE PUBLIC SURFACE CARRIES NO PRIVATE DATA -------------------------------- #

def test_a_private_classified_key_on_the_public_surface_is_refused():
    connection = RecordingConnection()
    with pytest.raises(PublicationRefused) as refusal:
        publish_cycle(
            connection,
            public_envelope=public_envelope(portfolio_value=250_000),
            private_envelope=private_envelope(),
        )
    assert refusal.value.reason_class == REFUSAL_PRIVATE_CLASSIFIED_KEY
    assert connection.wrote_nothing_to(*ENVELOPE_TABLES)


def test_the_same_key_nested_inside_a_dial_is_refused_too():
    """A scan that stopped at the root is a scan an author steps around by nesting."""
    connection = RecordingConnection()
    dial = {
        "state": "UNKNOWN",
        "reason": "NO_SOURCE_REGISTERED",
        "since_utc": "2026-08-23T12:00:00Z",
        "missing_inputs": [],
        "position_size": 42,
    }
    with pytest.raises(PublicationRefused) as refusal:
        publish_cycle(
            connection,
            public_envelope=public_envelope(equity_crash=dial),
            private_envelope=private_envelope(),
        )
    assert refusal.value.reason_class == REFUSAL_PRIVATE_CLASSIFIED_KEY
    assert connection.wrote_nothing_to(*ENVELOPE_TABLES)


def test_a_legitimate_public_envelope_passes_the_same_gate():
    """THE ADMITTING ARM for CD-AC-006. A gate that refused every envelope would satisfy
    the criterion vacuously."""
    connection = RecordingConnection()
    publish_cycle(
        connection,
        public_envelope=public_envelope(),
        private_envelope=private_envelope(),
    )
    assert len(connection.statements_touching("publication.public_envelope")) == 1


def test_a_secret_bearing_key_is_refused_on_BOTH_surfaces():
    for which in ("public", "private"):
        connection = RecordingConnection()
        pair = {
            "public_envelope": public_envelope(),
            "private_envelope": private_envelope(),
        }
        pair[f"{which}_envelope"] = (
            public_envelope(api_key="x") if which == "public"
            else private_envelope(api_key="x")
        )
        with pytest.raises(PublicationRefused) as refusal:
            publish_cycle(connection, **pair)
        assert refusal.value.reason_class == "SECRET_BEARING_KEY"
        assert connection.wrote_nothing_to(*ENVELOPE_TABLES)


# --- A REFUSAL IS A DURABLE ALERT, AND IT CARRIES NO VALUE -------------------------------- #

def test_a_refusal_writes_exactly_one_alert_row_and_no_envelope():
    connection = RecordingConnection()
    with pytest.raises(PublicationRefused):
        publish_cycle(
            connection,
            public_envelope=public_envelope(combined_stress=0.9),
            private_envelope=private_envelope(),
        )
    alerts = connection.statements_touching("alert.event")
    assert len(alerts) == 1
    (parameters,) = connection.parameters_for("alert.event")
    assert parameters[0] == ALERT_PUBLICATION_REFUSAL
    assert connection.wrote_nothing_to(*ENVELOPE_TABLES)


def test_the_alert_reference_names_the_key_and_never_the_value_behind_it():
    """``alert.event`` is APPEND-ONLY with no DELETE grant: a value written here is
    permanent (``PBG-SEC-002``)."""
    connection = RecordingConnection()
    with pytest.raises(PublicationRefused):
        publish_cycle(
            connection,
            public_envelope=public_envelope(portfolio_value=250_000),
            private_envelope=private_envelope(),
        )
    (parameters,) = connection.parameters_for("alert.event")
    reference = parameters[3]
    assert "portfolio_value" in reference
    assert "250000" not in reference and "250_000" not in reference
    assert len(reference) <= 200


def test_the_reference_is_truncated_rather_than_lost_when_it_would_be_too_long():
    class LongRefusal(PublicationRefused):
        pass

    refusal = PublicationRefused(
        "UNKNOWN_KEY",
        surface=EnvelopeSurface.PUBLIC,
        pointer="/" + "a" * 500,
        key="k" * 300,
    )
    reference = refusal_subject_ref(refusal)
    assert len(reference) == 200
    # The classification survives truncation; it is what the reference is FOR.
    assert reference.startswith("public|UNKNOWN_KEY")


def test_a_failure_to_record_the_alert_does_not_replace_the_refusal():
    """The publication refusal is the fact of record. An alerting failure is chained onto
    it, never substituted for it."""
    connection = RecordingConnection(raise_on_execute=RuntimeError("store unreachable"))
    with pytest.raises(PublicationRefused) as raised:
        publish_cycle(
            connection,
            public_envelope=public_envelope(combined_stress=0.9),
            private_envelope=private_envelope(),
        )
    assert isinstance(raised.value.__cause__, RuntimeError)


# --- WHAT THIS LAYER IS NOT ALLOWED TO REACH ---------------------------------------------- #

def test_the_publication_layer_holds_no_witness_path(monkeypatch):
    """``CD-AC-005``: *a publication layer is exactly where an absent witness gets quietly
    rendered as agreement.* There is no route to one here — the package imports nothing from
    ``crash_detector.witness``, which is also what keeps an engine-to-witness edge from
    arriving by the back door (``CD-AC-003``)."""
    import ast
    import pathlib

    package = pathlib.Path(__file__).resolve().parents[1] / "src" / "crash_detector" / "publication"
    paths = sorted(package.rglob("*.py"))
    assert paths, "no publication modules found; this scan would pass vacuously"

    offenders = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module]
            for name in names:
                if name.startswith("crash_detector.witness"):
                    offenders.append(f"{path.name}:{node.lineno} imports {name}")
    assert offenders == [], offenders


def test_the_publication_layer_registers_no_source():
    """``Q25``. Asserted over the CODE and not over the prose.

    **This test was written as a substring scan of the file text and it failed — on the
    docstring that says the module never touches ``raw.source_registry``.** A check that
    cannot tell a statement from a sentence about a statement reports a violation for a
    module doing exactly the right thing, and the repair for a false positive in a
    fail-closed check is to delete the sentence, which is the wrong repair. So it parses.

    It scans, per module: every string constant that is NOT a docstring (an emitted SQL
    statement is one of those), and every identifier reached as a name or an attribute.
    """
    import ast
    import pathlib

    package = (
        pathlib.Path(__file__).resolve().parents[1]
        / "src"
        / "crash_detector"
        / "publication"
    )
    paths = sorted(package.rglob("*.py"))
    assert paths, "no publication modules found; this scan would pass vacuously"

    offenders = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                body = getattr(node, "body", None) or []
                if (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                ):
                    docstrings.add(id(body[0].value))

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in docstrings:
                    continue
                if "source_registry" in node.value:
                    offenders.append(f"{path.name}:{node.lineno} emits source_registry")
            elif isinstance(node, ast.Name) and node.id == "SourceRecord":
                offenders.append(f"{path.name}:{node.lineno} names SourceRecord")
            elif isinstance(node, ast.Attribute) and node.attr == "SourceRecord":
                offenders.append(f"{path.name}:{node.lineno} reaches SourceRecord")

    assert offenders == [], (
        f"the publication layer touches the source registry: {offenders}. The ingredient "
        "set is held with the Product Authority (Q25) and no seat registers one."
    )


def test_that_scan_would_catch_a_real_registration():
    """**THE VACUITY GUARD.** The scan above passes; this proves it can fail.

    A check whose only evidence is that it passed on a clean tree is indistinguishable from
    a check that passes on everything (``CD-D-079``).
    """
    import ast

    planted = ast.parse(
        'STATEMENT = "INSERT INTO raw.source_registry (source_id) VALUES (%s)"\n'
    )
    found = [
        node
        for node in ast.walk(planted)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and "source_registry" in node.value
    ]
    assert len(found) == 1

    planted_name = ast.parse("row = SourceRecord(source_id='x')\n")
    named = [
        node
        for node in ast.walk(planted_name)
        if isinstance(node, ast.Name) and node.id == "SourceRecord"
    ]
    assert len(named) == 1


def test_an_alert_class_nobody_declared_is_refused():
    connection = RecordingConnection()
    from crash_detector.publication.alerting import raise_alert

    with pytest.raises(AlertRefused):
        raise_alert(
            connection,
            event_class="LOOKS_BAD",
            severity="CRITICAL",
            raised_by="cd_engine",
        )
    assert connection.statements_touching("alert.event") == []


def test_the_external_probe_may_not_raise_an_alert():
    """It holds no database credential — that is the property that makes it external."""
    connection = RecordingConnection()
    from crash_detector.publication.alerting import raise_alert

    with pytest.raises(AlertRefused) as refusal:
        raise_alert(
            connection,
            event_class="CADENCE_BREACH",
            severity="CRITICAL",
            raised_by="cd_probe",
        )
    assert "may not raise an alert" in str(refusal.value)
