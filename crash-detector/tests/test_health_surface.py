"""CD-RT-014 — runtime health externally observable.

The declared command for ``CD-AC-014`` (``required-tests.yaml``,
``contracts/execution/CD-RT-014-HEALTH-EXTERNALLY-OBSERVABLE.md``).

**THE PROPOSITION:** liveness, freshness, last-evaluation and degraded state are
INDEPENDENTLY readable, and stopping the service is detected inside fifteen minutes.

===========================================================================================
THE NEGATIVE CONTROL THE REGISTER DECLARES, HONOURED LITERALLY
===========================================================================================
    *"one planted violation PER OBSERVABLE, so that no observable is evidenced only by its
    siblings."*

So there is a refusing arm for **each** of the five observables separately, not one arm for
"the document" — a document rejected because of its ``regime`` field says nothing about
whether ``last_evaluation_utc`` was ever checked.

===========================================================================================
THE PROBE IS EXERCISED AGAINST A REAL SOCKET, INCLUDING ONE THAT IS NOT THERE
===========================================================================================
``tests/`` may import ``http.server`` — the network-module ban is asserted over
``src/crash_detector`` only, and deliberately: the application must not open a socket, and
an outside observer must. So the probe is not tested against a mock of a server. It is run
against a real one, and then against **the same address after the server is stopped**, which
is the closest this lane can get to *"the whole container set is down"* — and it is the
claim most easily asserted and least easily proved.

**NO SOURCE IS REGISTERED BY ANYTHING IN THIS FILE** (``Q25``, ``CD-PL-F154``).
"""

from __future__ import annotations

import ast
import http.server
import json
import pathlib
import socket
import subprocess
import sys
import threading
from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.health import (
    DEGRADED_CADENCE_BREACH,
    DEGRADED_CLASSES,
    DEGRADED_NONE,
    HEALTH_KEYS,
    STATE_KEYS,
    HealthSurfaceRefused,
    health_document,
    refuse_unless_health_safe,
    state_document,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "probe" / "external_probe.py"

NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _healthy(**overrides):
    document = dict(
        live=True,
        last_publication_utc=_iso(NOW),
        last_evaluation_utc=_iso(NOW),
        regime="CALM",
        degraded_classes=(),
    )
    document.update(overrides)
    return health_document(**document)


# ========================================================================================= #
# THE ADMITTING ARM — the surface serves the five observables
# ========================================================================================= #

def test_the_five_observables_are_independently_readable():
    document = _healthy()
    assert document["live"] is True
    assert document["last_publication_utc"] == _iso(NOW)
    assert document["last_evaluation_utc"] == _iso(NOW)
    assert document["regime"] == "CALM"
    assert document["degraded"] is False
    # Independently: each is its OWN key, not one rolled-up "ok".
    assert set(document) == set(HEALTH_KEYS)


def test_degradation_is_reported_as_a_class_and_the_flag_is_derived_from_it():
    document = _healthy(degraded_classes=(DEGRADED_CADENCE_BREACH,))
    assert document["degraded"] is True
    assert document["degraded_classes"] == [DEGRADED_CADENCE_BREACH]
    # Two copies of one fact is one fact with a bug scheduled: the flag cannot disagree.
    assert document["degraded"] == bool(
        [c for c in document["degraded_classes"] if c != DEGRADED_NONE]
    )


def test_no_degradation_says_so_explicitly_rather_than_by_omission():
    """A consumer must never have to distinguish 'not degraded' from 'the field was
    omitted' — the argument the envelope's honesty fields already make."""
    assert _healthy()["degraded_classes"] == [DEGRADED_NONE]


# ========================================================================================= #
# *** ONE PLANTED VIOLATION PER OBSERVABLE ***
# ========================================================================================= #

def test_a_dial_value_on_the_health_surface_is_refused():
    """The temptation named in the dispatch: explaining 'degraded' with the number that
    degraded."""
    with pytest.raises(HealthSurfaceRefused) as refusal:
        refuse_unless_health_safe(
            {**_healthy(), "equity_crash_score": 0.87}
        )
    assert refusal.value.reason_class == "UNKNOWN_KEY"
    assert refusal.value.key == "equity_crash_score"
    # The VALUE does not appear in the refusal message either.
    assert "0.87" not in str(refusal.value)


def test_a_witness_reading_on_the_health_surface_is_refused():
    with pytest.raises(HealthSurfaceRefused) as refusal:
        refuse_unless_health_safe({**_healthy(), "divergence_measure": 0.02})
    assert refusal.value.reason_class == "UNKNOWN_KEY"
    assert "0.02" not in str(refusal.value)


def test_a_source_name_on_the_health_surface_is_refused():
    with pytest.raises(HealthSurfaceRefused) as refusal:
        refuse_unless_health_safe({**_healthy(), "inputs_used": ["some-source"]})
    assert refusal.value.reason_class == "UNKNOWN_KEY"
    assert "some-source" not in str(refusal.value)


def test_a_private_envelope_key_on_the_health_surface_is_refused_by_NAME():
    """The classification register, which names the REASON where the allowlist only says
    'not declared'."""
    with pytest.raises(HealthSurfaceRefused) as refusal:
        refuse_unless_health_safe(
            {"portfolio_exposure": 1}, allowed_keys=("portfolio_exposure",)
        )
    assert refusal.value.reason_class == "PRIVATE_CLASSIFIED_KEY"


def test_a_secret_bearing_key_on_the_health_surface_is_refused():
    with pytest.raises(HealthSurfaceRefused) as refusal:
        refuse_unless_health_safe({"api_key": "x"}, allowed_keys=("api_key",))
    assert refusal.value.reason_class == "SECRET_BEARING_KEY"


def test_a_nested_offender_is_refused_at_every_depth():
    """A scan that stopped at the root is one an author steps around by nesting."""
    with pytest.raises(HealthSurfaceRefused):
        refuse_unless_health_safe(
            {**_healthy(), "alerts": [{"event_class": "X", "portfolio_value": 1}]},
            allowed_keys=STATE_KEYS,
        )


# --- ONE PER OBSERVABLE: each of the five is separately guarded --------------------------- #

def test_the_degraded_vocabulary_is_closed():
    """OBSERVABLE 5. Without this, ``degraded_classes`` is free text, and free text is
    where a number eventually gets written."""
    with pytest.raises(HealthSurfaceRefused) as refusal:
        refuse_unless_health_safe(
            {**_healthy(), "degraded_classes": ["equity_crash is at 0.87"]}
        )
    assert refusal.value.reason_class == "UNDECLARED_DEGRADED_CLASS"
    assert "0.87" not in str(refusal.value)


def test_every_declared_degraded_class_is_admitted():
    """THE ADMITTING ARM for the closed vocabulary."""
    for name in DEGRADED_CLASSES:
        refuse_unless_health_safe({**_healthy(), "degraded_classes": [name]})


def test_the_regime_field_cannot_carry_a_score_as_text():
    """OBSERVABLE 4, and the residue the module's declared limit 1 names.

    ``regime`` is a legitimate string field, so a closed vocabulary is what stops a number
    being smuggled out through it."""
    with pytest.raises(HealthSurfaceRefused) as refusal:
        refuse_unless_health_safe({**_healthy(), "regime": "0.87"})
    assert refusal.value.reason_class == "UNDECLARED_REGIME"
    assert "0.87" not in str(refusal.value)


def test_a_declared_regime_is_admitted():
    """THE ADMITTING ARM."""
    for name in ("CALM", "STRESS"):
        refuse_unless_health_safe({**_healthy(), "regime": name})


@pytest.mark.parametrize(
    "observable", ["live", "last_publication_utc", "last_evaluation_utc", "regime", "degraded"]
)
def test_each_observable_is_present_in_its_own_right(observable):
    """OBSERVABLES 1-5. No observable is evidenced only by its siblings: each is asserted
    to exist as its own key, so removing one fails here and not somewhere general."""
    assert observable in _healthy()


def test_the_builder_has_no_open_bag():
    """A builder with ``**extra`` is a builder through which anything reaches the surface."""
    import inspect

    for builder in (health_document, state_document):
        signature = inspect.signature(builder)
        kinds = {p.kind for p in signature.parameters.values()}
        assert inspect.Parameter.VAR_KEYWORD not in kinds, builder.__name__
        assert inspect.Parameter.VAR_POSITIONAL not in kinds, builder.__name__


# ========================================================================================= #
# THE MACHINE-READABLE STATE ENDPOINT (Q26) HAS THE IDENTICAL SAFETY PROPERTY
# ========================================================================================= #

def test_alerts_surface_as_class_severity_and_instant():
    rows = [("CADENCE_BREACH", "CRITICAL", "2026-08-23T11:59:00Z", "cd_engine", "ref")]
    document = state_document(
        live=True,
        last_publication_utc=_iso(NOW),
        last_evaluation_utc=_iso(NOW),
        regime="CALM",
        degraded_classes=(DEGRADED_CADENCE_BREACH,),
        alerts=rows,
    )
    assert document["alerts"] == [
        {
            "event_class": "CADENCE_BREACH",
            "severity": "CRITICAL",
            "raised_utc": "2026-08-23T11:59:00Z",
        }
    ]


def test_the_state_endpoint_drops_subject_ref():
    """*** ``subject_ref`` MAY LEGITIMATELY CARRY A ``source_id``, AND A SOURCE NAME IS
    MARKET INFORMATION ON AN UNAUTHENTICATED SURFACE. ***"""
    rows = [("CADENCE_BREACH", "CRITICAL", "2026-08-23T11:59:00Z", "cd_engine", "SRC-XYZ")]
    document = state_document(
        live=True,
        last_publication_utc=_iso(NOW),
        last_evaluation_utc=_iso(NOW),
        regime="CALM",
        alerts=rows,
    )
    assert "SRC-XYZ" not in json.dumps(document)
    assert all("subject_ref" not in entry for entry in document["alerts"])


def test_a_column_added_to_the_alert_select_cannot_arrive_on_the_surface_by_default():
    rows = [("CADENCE_BREACH", "CRITICAL", "2026-08-23T11:59:00Z", "cd_engine", "r", 0.87)]
    document = state_document(
        live=True,
        last_publication_utc=_iso(NOW),
        last_evaluation_utc=_iso(NOW),
        regime="CALM",
        alerts=rows,
    )
    assert "0.87" not in json.dumps(document)


def test_the_state_endpoint_goes_through_the_same_guard():
    with pytest.raises(HealthSurfaceRefused):
        state_document(
            live=True,
            last_publication_utc=_iso(NOW),
            last_evaluation_utc=_iso(NOW),
            regime="0.87",
        )


# ========================================================================================= #
# *** THE EXTERNAL PROBE — AGAINST A REAL SOCKET, AND AGAINST ONE THAT IS NOT THERE ***
# ========================================================================================= #

class _HealthServer:
    """A real HTTP server on a real loopback port. Stands in for the container set."""

    def __init__(self, document: dict, status: int = 200) -> None:
        body = json.dumps(document).encode("utf-8")

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args: object) -> None:
                return

        self._server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> "_HealthServer":
        self._thread.start()
        return self

    def __exit__(self, *exc_info: object) -> bool:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
        return False

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/health"


def _run_probe(url: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(PROBE), "--health-url", url, *extra],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(ROOT),
    )


def _free_port() -> int:
    with socket.socket() as probe_socket:
        probe_socket.bind(("127.0.0.1", 0))
        return probe_socket.getsockname()[1]


def test_the_probe_reports_healthy_against_a_live_surface():
    """THE ADMITTING ARM. Without it, the UNREACHABLE arm below is consistent with a probe
    that reports failure at all times."""
    document = health_document(
        live=True,
        last_publication_utc=_iso(datetime.now(timezone.utc)),
        last_evaluation_utc=_iso(datetime.now(timezone.utc)),
        regime="CALM",
        degraded_classes=(),
    )
    with _HealthServer(document) as server:
        result = _run_probe(server.url)
    assert result.returncode == 0, result.stderr
    assert "HEALTHY" in result.stdout


def test_stopping_the_service_is_DETECTED_and_the_probe_survives_it():
    """*** THE CLAIM MOST EASILY ASSERTED AND LEAST EASILY PROVED. ***

    The server is started, the probe confirms it healthy, the server is then STOPPED, and
    the probe is run again against the same address. It exits ``2 UNREACHABLE``.

    **The probe is still running because it was never part of what failed.** A checker
    inside the container set cannot produce this verdict: it is not running either.
    """
    document = health_document(
        live=True,
        last_publication_utc=_iso(datetime.now(timezone.utc)),
        last_evaluation_utc=_iso(datetime.now(timezone.utc)),
        regime="CALM",
        degraded_classes=(),
    )
    with _HealthServer(document) as server:
        url = server.url
        alive = _run_probe(url)
    assert alive.returncode == 0, alive.stderr

    # The container set is now down. Same address, nothing listening.
    dead = _run_probe(url)
    assert dead.returncode == 2, (dead.returncode, dead.stdout, dead.stderr)
    assert "UNREACHABLE" in dead.stderr


def test_nothing_listening_at_all_is_UNREACHABLE_and_not_a_crash():
    result = _run_probe(f"http://127.0.0.1:{_free_port()}/health")
    assert result.returncode == 2
    assert "UNREACHABLE" in result.stderr


def test_a_publication_older_than_the_pid_budget_is_detected():
    """PID §5: independently detectable within fifteen minutes."""
    stale = datetime.now(timezone.utc) - timedelta(seconds=1200)
    document = health_document(
        live=True,
        last_publication_utc=_iso(stale),
        last_evaluation_utc=_iso(stale),
        regime="CALM",
        degraded_classes=(),
    )
    with _HealthServer(document) as server:
        result = _run_probe(server.url)
    assert result.returncode == 1
    assert "PID §5 budget" in result.stderr


def test_a_publication_inside_the_budget_is_not_flagged():
    """THE ADMITTING ARM for the budget check."""
    recent = datetime.now(timezone.utc) - timedelta(seconds=60)
    document = health_document(
        live=True,
        last_publication_utc=_iso(recent),
        last_evaluation_utc=_iso(recent),
        regime="CALM",
        degraded_classes=(),
    )
    with _HealthServer(document) as server:
        result = _run_probe(server.url)
    assert result.returncode == 0, result.stderr


def test_a_surface_reporting_degradation_is_detected():
    document = health_document(
        live=True,
        last_publication_utc=_iso(datetime.now(timezone.utc)),
        last_evaluation_utc=_iso(datetime.now(timezone.utc)),
        regime="STRESS",
        degraded_classes=(DEGRADED_CADENCE_BREACH,),
    )
    with _HealthServer(document) as server:
        result = _run_probe(server.url)
    assert result.returncode == 1
    assert "CADENCE_BREACH" in result.stderr


def test_a_misconfigured_probe_is_distinguished_from_an_unreachable_service():
    """'Nobody is listening' and 'I was pointed at the wrong thing' have different causes
    and different fixes."""
    with _HealthServer({"not": "a health document"}) as server:
        result = _run_probe(server.url)
    assert result.returncode == 3
    assert "PROBE_FAULT" in result.stderr


# ========================================================================================= #
# *** THE PROBE IS OUTSIDE THE CONTAINER SET — PROVED, NOT ASSERTED ***
# ========================================================================================= #

def test_the_probe_is_not_a_service_in_the_container_set():
    """Adding it to ``compose.yaml`` would put it inside the unit that fails."""
    compose = (ROOT / "deploy" / "compose.yaml").read_text(encoding="utf-8")
    assert "external_probe" not in compose
    assert "cd-probe" not in compose

    from compose_reader import load_compose  # the project's own reader

    services = load_compose(ROOT / "deploy" / "compose.yaml")["services"]
    for name in services:
        assert "probe" not in name, f"{name} looks like a probe service inside the set"


def test_the_probe_has_no_dockerfile():
    dockerfiles = sorted((ROOT / "deploy").glob("Dockerfile*"))
    assert dockerfiles, "no Dockerfiles found; this scan would pass vacuously"
    for path in dockerfiles:
        assert "probe" not in path.read_text(encoding="utf-8").lower(), path.name


def test_the_probe_imports_nothing_from_the_application():
    """*** An observer that shares code with the thing it observes is not independent. ***

    If the application's parsing of its own health document is wrong, a probe built on that
    parsing is wrong in exactly the same way and cannot see it.
    """
    tree = ast.parse(PROBE.read_text(encoding="utf-8"), filename=str(PROBE))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            imported.add(node.module.split(".")[0])
    assert "crash_detector" not in imported, imported


def _non_docstring_strings(tree: ast.AST) -> list:
    """Every string constant in ``tree`` that is not a docstring.

    **THIS HELPER EXISTS BECAUSE THE OBVIOUS VERSION OF THE TEST BELOW WAS WRITTEN AS A
    SUBSTRING SCAN OF THE FILE TEXT AND IT FAILED — on the probe's own docstring, which
    lists the things the probe does not contain** (*"no DSN, no PGPASSWORD, no private
    envelope"*). A check that cannot tell a statement from a sentence about a statement
    reports a violation for a file doing exactly the right thing, and the repair for a false
    positive in a fail-closed check is to delete the sentence — which is the wrong repair.

    Three separate scans in this increment hit that same class. It is worth the helper.
    """
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
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def test_the_probe_holds_no_database_credential_and_issues_no_query():
    """It sees exactly what an outside party sees: the public surface, over HTTP.

    Scanned over the CODE — imports, and string constants that are not docstrings. A DSN, a
    credential variable name and a SQL statement are all strings the program would have to
    EVALUATE, so they are exactly what this looks at.
    """
    tree = ast.parse(PROBE.read_text(encoding="utf-8"), filename=str(PROBE))

    drivers = {"psycopg", "psycopg2", "sqlalchemy", "asyncpg", "pg8000", "sqlite3"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in drivers, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in drivers, node.module

    live_strings = _non_docstring_strings(tree)
    forbidden = (
        "SELECT ", "INSERT ", "postgresql://", "PGPASSWORD", "DATABASE_URL",
        "private_envelope", "alert.event", "publication.heartbeat",
    )
    offenders = [
        (token, value)
        for value in live_strings
        for token in forbidden
        if token in value
    ]
    assert offenders == [], offenders


def test_that_credential_scan_would_catch_a_real_one():
    """**THE VACUITY GUARD.** The scan above passes; this proves it can still fail."""
    planted = ast.parse(
        '"""A docstring mentioning PGPASSWORD harmlessly."""\n'
        'DSN = "postgresql://user@host/db"\n'
    )
    live = _non_docstring_strings(planted)
    assert any("postgresql://" in value for value in live)
    assert not any("PGPASSWORD" in value for value in live)


def test_the_probe_runs_without_the_application_package_importable():
    """The strongest available form of 'outside': run it with ``src/`` absent from the path.

    A probe that needs the application installed to run is a probe that cannot be deployed
    to a second machine, which is where an independent observer belongs.
    """
    import os

    environment = dict(os.environ)
    environment["PYTHONPATH"] = ""
    result = subprocess.run(
        [
            sys.executable, "-B", str(PROBE),
            "--health-url", f"http://127.0.0.1:{_free_port()}/health",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        cwd="/tmp",
        env=environment,
    )
    assert result.returncode == 2, (result.returncode, result.stderr)
    assert "UNREACHABLE" in result.stderr


def test_the_only_ratified_number_in_the_probe_is_the_pid_budget():
    import importlib.util

    specification = importlib.util.spec_from_file_location("_probe", PROBE)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    assert module.PID_ASSURANCE_LATENCY_BUDGET_SECONDS == 900.0
