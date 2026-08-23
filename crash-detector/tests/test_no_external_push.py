"""C6 / ``Q26`` — **there is NO code path from this system to a third party.**

``PO-DECISIONS-0024`` ruling 3: the detector is advisory, so alerts surface on the
publication surface and on a machine-readable state endpoint, **with no external push
channel until the Product Authority names one.** The ruling calls the eventual channel *"a
one-line addition when he says so"*.

    *** THIS FILE IS THE EVIDENCE THAT THE LINE IS NOT WRITTEN, AND CANNOT BE WRITTEN
        WITHOUT FAILING A TEST. ***

===========================================================================================
IT IS DENY BY DEFAULT, AND THAT IS THE WHOLE LESSON OF ``CD-ASR-F04`` AND ``CD-PL-F59``
===========================================================================================
An obvious version of this check enumerates the channels — ``smtplib``, ``requests``,
``slack_sdk``, ``discord``, ``twilio`` — and refuses anything it recognises.

**THAT CHECK HAS ALREADY BEEN DEFEATED TWICE ON THIS PROJECT.** An independent auditor put
the IP literal ``198.51.100.24`` into an egress allowlist where ``api.ibkr.com`` had been and
``check_egress_no_broker.py`` exited 0 — *"it recognised brokers BY NAME and an address has
no name to recognise"* (``CD-ASR-F04``). The repair was not a better matcher, because *"the
next spelling is a CIDR, a URL, an unregistered hostname, a punycode host, a hex-dotted
address"*. The repair was **deny by default over a declared registry**, so that an
unregistered entry *"stops being a spelling to catch and is simply not a destination anyone
declared"*.

**SO THIS CHECK PERFORMS NO RECOGNITION.** It declares
:data:`PERMITTED_IMPORT_ROOTS` — the complete set of top-level modules the application tree
is allowed to import — and fails on **anything else**, whatever it is called. ``smtplib`` is
refused. So is ``requests``. So are ``subprocess``, ``ctypes``, ``webbrowser``, ``pty``,
``multiprocessing``, ``asyncio``, a vendored HTTP client, and the module a future engineer
invents that nobody has thought of — **not because anything was recognised about them, but
because nobody declared them.** There is no pattern to write around.

That is strictly stronger than
``tests/test_collector_boundaries.py::test_nothing_in_the_application_tree_imports_a_network_module``,
which enumerates ~19 network module names. That test is not replaced and not weakened; this
one sits beside it and closes the class it leaves open — **a shell-out is egress, and
``subprocess`` is not on any list of network modules.**

===========================================================================================
THE POPULATION IS MEASURED, NOT ASSUMED
===========================================================================================
:data:`PERMITTED_IMPORT_ROOTS` was produced by parsing every module under
``src/crash_detector`` at this increment's tip and taking the set. It is **21 names**, every
one of them a pure-computation stdlib module, ``jsonschema``, or the package itself. A test
below asserts the declared set is not wider than what is actually imported, so the allowlist
cannot be quietly pre-widened for a channel somebody intends to add later.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

SRC_ROOT = pathlib.Path(__file__).resolve().parents[1] / "src" / "crash_detector"

#: THE COMPLETE DECLARED IMPORT SURFACE OF THE APPLICATION TREE. Deny by default: a module
#: not on this list is refused, whatever it is and whatever it is called.
#:
#: Every member is a pure-computation module. NOT ONE of them can open a socket, spawn a
#: process, load a shared library or launch a browser. ``os`` is here for ``os.environ`` —
#: configuration from the environment (PBG-SEC-001) — and a test below asserts that the
#: process-spawning half of ``os`` is not reached.
PERMITTED_IMPORT_ROOTS: frozenset = frozenset(
    {
        "__future__",
        "collections",
        "copy",
        "crash_detector",
        "dataclasses",
        "datetime",
        "enum",
        "functools",
        "hashlib",
        "inspect",
        "json",
        "jsonschema",
        "math",
        "os",
        "pathlib",
        "re",
        "signal",
        "sys",
        "time",
        "types",
        "typing",
    }
)

#: The attributes of ``os`` and ``sys`` that reach outside this process. ``os`` is admitted
#: for ``environ``; admitting the module must not admit ``os.system``.
FORBIDDEN_ATTRIBUTES: frozenset = frozenset(
    {
        "system",
        "popen",
        "execv",
        "execve",
        "execvp",
        "execl",
        "execlp",
        "spawnv",
        "spawnl",
        "fork",
        "forkpty",
        "posix_spawn",
        "startfile",
    }
)


def _python_files() -> list:
    found = sorted(SRC_ROOT.rglob("*.py"))
    assert found, f"no Python files under {SRC_ROOT}; this scan would pass vacuously"
    return found


def _imported_roots(tree: ast.AST) -> set:
    """Top-level module names imported, however spelled — **including inside a function**.

    A deferred import reaches a third party exactly as well as a module-level one, and a
    function-local ``import smtplib`` is precisely how somebody keeps a module-level scan
    clean.
    """
    roots = set()
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


# ========================================================================================= #
# THE CLAIM
# ========================================================================================= #

def test_the_application_tree_imports_nothing_outside_the_declared_surface():
    """*** NO EXTERNAL PUSH CHANNEL EXISTS, AND NONE CAN BE ADDED SILENTLY. ***"""
    offenders = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for root in _imported_roots(tree) - PERMITTED_IMPORT_ROOTS:
            offenders.append(f"{path.relative_to(SRC_ROOT)} imports {root}")
    assert offenders == [], (
        "the application tree imports something nobody declared: "
        f"{offenders}. This is DENY BY DEFAULT — the import is refused because it is not on "
        "the declared surface, not because anything was recognised about it. If this is an "
        "alert channel, Q26 rules that the Product Authority names it first "
        "(PO-DECISIONS-0024 ruling 3); if it is not, widen PERMITTED_IMPORT_ROOTS "
        "deliberately and say why."
    )


def test_no_process_spawning_attribute_is_reached():
    """A shell-out is egress. ``os`` is admitted for ``environ`` and for nothing else."""
    offenders = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRIBUTES:
                offenders.append(f"{path.relative_to(SRC_ROOT)}:{node.lineno} .{node.attr}")
    assert offenders == [], offenders


def test_the_declared_surface_is_not_wider_than_what_is_actually_imported():
    """**THE ANTI-PRE-WIDENING GUARD.**

    An allowlist quietly extended today for a channel somebody means to add tomorrow would
    make the test above pass on the day the channel lands. So the declared set must not
    exceed the measured one: an unused permission is a permission nobody needs.
    """
    actually = set()
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        actually |= _imported_roots(tree)
    surplus = sorted(PERMITTED_IMPORT_ROOTS - actually)
    assert surplus == [], (
        f"PERMITTED_IMPORT_ROOTS declares {surplus}, which nothing imports. An allowlist "
        "entry with no user is a door standing open for a future arrival."
    )


def test_the_alerting_module_offers_a_read_and_no_send():
    """``Q26``'s surfacing mechanism is a READ. The public names say so."""
    import crash_detector.publication.alerting as module

    assert "recent_alerts" in module.__all__
    for forbidden in ("send", "push", "notify", "post", "publish_to", "webhook", "dispatch"):
        assert not any(
            forbidden in name.lower() for name in module.__all__
        ), f"{forbidden!r} appears in the alerting module's public surface"


def test_the_alerting_module_declares_no_destination():
    """No URL, no host, no address anywhere in the code it executes."""
    path = SRC_ROOT / "publication" / "alerting.py"
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
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            for scheme in ("http://", "https://", "smtp://", "tcp://", "@"):
                assert scheme not in node.value, (node.lineno, scheme)


# ========================================================================================= #
# THE VACUITY GUARDS — a check whose only evidence is that it passed is not evidence
# ========================================================================================= #

@pytest.mark.parametrize(
    "planted",
    [
        "import smtplib\n",
        "import requests\n",
        "from urllib.request import urlopen\n",
        "import subprocess\n",
        "import ctypes\n",
        "import webbrowser\n",
        "def notify():\n    import slack_sdk\n",          # deferred, inside a function
        "def notify():\n    from discord import Webhook\n",
    ],
)
def test_the_scan_would_catch_each_of_these(planted):
    """**Eight planted channels, each of a different KIND**, and two of them deferred
    inside a function body — which is exactly how a module-level scan is kept clean.

    Note that ``slack_sdk`` and ``discord`` are caught **without appearing anywhere in this
    file's vocabulary**. That is the deny-by-default property: the check does not know what
    they are and does not need to.
    """
    tree = ast.parse(planted)
    assert _imported_roots(tree) - PERMITTED_IMPORT_ROOTS != set()


def test_the_scan_admits_the_genuine_article():
    """**THE ADMITTING ARM.** A check that refused every import would be vacuous."""
    tree = ast.parse(
        "import json\nfrom datetime import datetime\n"
        "from crash_detector.publication.alerting import recent_alerts\n"
    )
    assert _imported_roots(tree) - PERMITTED_IMPORT_ROOTS == set()


def test_the_process_spawn_scan_would_catch_a_shell_out():
    tree = ast.parse("import os\nos.system('curl -X POST https://hooks.example/x')\n")
    reached = [
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRIBUTES
    ]
    assert reached == ["system"]
