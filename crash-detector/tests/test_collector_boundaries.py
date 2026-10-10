"""Structural boundaries of the collector framework (BLUEPRINT §5, deliverable A4).

Three propositions, each asserted over the WHOLE package by walking its source rather
than over the modules somebody remembered. A guard that names its targets is a guard an
author steps around by adding a module.

1. **A collector fetches and records. It never computes.** Nothing under ``collectors/``
   imports the dial types or the engine. The boundary between "what we observed" and
   "what we concluded" is the boundary between the ``raw`` and ``dial`` schemas and
   between two containers; an import edge across it is that boundary quietly ceasing to
   exist in the one place nobody looks.
2. **No network access from the collector framework in this increment.** Nothing under
   ``src/`` imports a socket, an HTTP client or a name resolver.
3. **The §5/§7 boundary is not inverted.** The engine does not import the collector
   package — the reason ``observations`` and ``source_registry`` live at the package root
   (CD-D-008).
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from crash_detector.collectors.adapter import (
    ADAPTER_PROTOCOL_MEMBERS,
    AdapterFetchError,
    missing_adapter_members,
)

from collector_fakes import FakeInMemoryAdapter

SRC_ROOT = pathlib.Path(__file__).resolve().parents[1] / "src" / "crash_detector"
COLLECTORS_ROOT = SRC_ROOT / "collectors"
ENGINE_ROOT = SRC_ROOT / "engine"

#: Every stdlib and third-party route to a socket that could plausibly appear here.
#: Enumerated as data so the check tests the CLASS of violation. A module reached by any
#: of these names is a module that can leave the container.
NETWORK_MODULES: frozenset[str] = frozenset(
    {
        "aiohttp",
        "asyncio",
        "ftplib",
        "http",
        "httpcore",
        "httplib2",
        "httpx",
        "imaplib",
        "requests",
        "smtplib",
        "socket",
        "socketserver",
        "ssl",
        "telnetlib",
        "urllib",
        "urllib3",
        "websocket",
        "websockets",
        "xmlrpc",
    }
)


def _python_files(root: pathlib.Path) -> list[pathlib.Path]:
    found = sorted(path for path in root.rglob("*.py"))
    assert found, f"no Python files under {root}; the scan would pass vacuously"
    return found


def _imported_roots(path: pathlib.Path) -> set[str]:
    """Every top-level module name imported by ``path``, however it is spelled.

    Covers ``import x``, ``import x.y``, ``from x import y``, ``from x.y import z`` and
    the same inside a function body — a deferred import reaches the network exactly as
    well as a module-level one.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module:
                roots.add(node.module.split(".")[0])
    return roots


def _imported_dotted(path: pathlib.Path) -> set[str]:
    """Every fully-qualified module name imported by ``path``."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and not node.level:
                names.add(node.module)
    return names


# --- A COLLECTOR NEVER COMPUTES --------------------------------------------------------- #

def test_no_collector_module_imports_the_dial_types_or_the_engine():
    offenders = []
    for path in _python_files(COLLECTORS_ROOT):
        for name in _imported_dotted(path):
            if name.startswith("crash_detector.dials") or name.startswith(
                "crash_detector.engine"
            ):
                offenders.append(f"{path.name} imports {name}")
    assert offenders == [], (
        "a collector that imports the dial path can compute a conclusion on the wrong "
        f"side of the raw/dial boundary: {offenders}"
    )


def test_the_engine_does_not_import_the_collector_package():
    """The §5/§7 boundary is not inverted (CD-D-008).

    This is the reason ``observations`` and ``source_registry`` sit at the package root:
    they are the CONTRACT between the two layers, not a component of either.
    """
    offenders = []
    for path in _python_files(ENGINE_ROOT):
        for name in _imported_dotted(path):
            if name.startswith("crash_detector.collectors"):
                offenders.append(f"{path.name} imports {name}")
    assert offenders == []


def test_the_engine_does_not_import_the_publication_package_in_wo2():
    """Recorded rather than assumed. The engine builds envelopes in WO-3, not here.

    Stated so that when WO-3 wires them together it is a deliberate edit to this test
    with a reason, not a quiet drift.
    """
    offenders = []
    for path in _python_files(ENGINE_ROOT):
        for name in _imported_dotted(path):
            if name.startswith("crash_detector.publication"):
                offenders.append(f"{path.name} imports {name}")
    assert offenders == []


# --- NO NETWORK ------------------------------------------------------------------------- #

def test_nothing_in_the_application_tree_imports_a_network_module():
    """Over the whole of ``src/``, not only over ``collectors/``.

    "No network access from the collector framework in this increment" is cheap to satisfy
    if the socket is opened one package to the left.
    """
    offenders = []
    for path in _python_files(SRC_ROOT):
        for root in _imported_roots(path) & NETWORK_MODULES:
            offenders.append(f"{path.relative_to(SRC_ROOT)} imports {root}")
    assert offenders == [], f"network-capable imports in the application tree: {offenders}"


def test_the_network_scan_would_catch_a_deferred_import():
    """The guard must fail when the thing it guards is broken, at its own seam.

    A function-local ``import socket`` is exactly how somebody keeps a module-level
    import scanner quiet, so the scanner is proved against one here rather than assumed
    to cover it.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        planted = pathlib.Path(tmp) / "planted.py"
        planted.write_text(
            "def fetch():\n    import socket\n    return socket\n", encoding="utf-8"
        )
        assert "socket" in _imported_roots(planted)


def test_the_import_scan_reads_from_imports_as_well_as_plain_imports():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        planted = pathlib.Path(tmp) / "planted.py"
        planted.write_text("from urllib.request import urlopen\n", encoding="utf-8")
        assert "urllib" in _imported_roots(planted)


# --- THE ADAPTER PROTOCOL --------------------------------------------------------------- #

def test_the_only_adapter_in_the_tree_is_a_test_double_under_tests():
    """WO-2 delivers NO adapter for any real source (CD-D-005 is the PO's, and owed).

    Detected structurally: no class under ``src/`` declares the adapter's whole member
    set. An implementation in the application tree would be an ingredient registered by
    an Engineer seat, which is inventing product meaning (PBG-AUTH-005).
    """
    required = set(ADAPTER_PROTOCOL_MEMBERS)
    offenders = []
    for path in _python_files(SRC_ROOT):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name == "SourceAdapter":
                continue  # the Protocol itself, which implements nothing
            declared = {
                member.name
                for member in node.body
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            if required <= declared:
                offenders.append(f"{path.relative_to(SRC_ROOT)}::{node.name}")
    assert offenders == [], f"a source adapter exists in the application tree: {offenders}"


def test_the_test_double_conforms_to_the_whole_adapter_protocol():
    assert missing_adapter_members(FakeInMemoryAdapter(script=[])) == ()


def test_conformance_is_checked_against_every_member_not_the_ones_remembered():
    class NearlyAnAdapter:
        source_id = "x"
        adapter_id = "y"
        response_schema = {}

        def fetch(self, *, timeout_seconds: float):  # pragma: no cover
            raise NotImplementedError

    assert missing_adapter_members(NearlyAnAdapter()) == ("is_empty",)


def test_a_member_that_exists_but_is_not_callable_does_not_count_as_conformance():
    """``typing.runtime_checkable`` would pass this object. That is why it is not used."""

    class FetchIsAnInteger:
        source_id = "x"
        adapter_id = "y"
        response_schema = {}
        fetch = 7
        is_empty = True

    assert set(missing_adapter_members(FetchIsAnInteger())) == {"fetch", "is_empty"}


# --- THE FETCH ERROR CARRIES NO FREE TEXT ------------------------------------------------ #

def test_an_adapter_fetch_error_carries_a_class_and_a_status_and_no_message():
    """Secret hygiene, by construction (PBG-SEC-002, Standards Baseline §5).

    A transport failure's natural detail string is the request that failed, and the
    request that failed is the one carrying the source's credential.
    """
    error = AdapterFetchError("HTTP_ERROR", 503)
    assert error.error_class == "HTTP_ERROR"
    assert error.http_status == 503
    assert str(error) == "HTTP_ERROR"
    assert not hasattr(error, "detail")


def test_an_absent_http_status_is_absent_and_not_zero():
    """A zero status would sort, compare and aggregate alongside real statuses."""
    assert AdapterFetchError("CONNECTION_REFUSED").http_status is None


@pytest.mark.parametrize("bad", ["", None])
def test_an_unclassified_fetch_error_is_refused(bad):
    with pytest.raises(ValueError):
        AdapterFetchError(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [True, "503", 5.03])
def test_an_http_status_of_the_wrong_type_is_refused(bad):
    with pytest.raises(TypeError):
        AdapterFetchError("HTTP_ERROR", bad)  # type: ignore[arg-type]
