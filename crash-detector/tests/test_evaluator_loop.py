"""THE EVALUATOR LOOP: the container's timer, its two refusals, and its signal discipline.

WO-1.3a, the deployment round. ``deploy/live-dev/evaluator_loop.py`` is a deploy script and
not a package module, so it is loaded BY FILE LOCATION here, the same way
``test_health_surface.py`` loads the health probe. Nothing is added to ``sys.path``.

WHAT IS TESTED HERE AND WHAT IS NOT. This round is mostly infrastructure config, and the
honest split is:

* **pytest (this file)**: the loop. Interval parsing and its default, the two unset-path
  refusals, a failed pass not killing the loop, SIGTERM arriving MID-pass not truncating
  that pass, the history store being opened in WRITE mode, the raw store not being openable
  from this process at all, and one real pass writing real rows to a real file.
* **``docker compose config`` / inspection (not pytest)**: the compose service entry, the
  config-hash stability of the other two services, and the image's own contents. A compose
  file is not reachable from a Python assertion that would mean anything, and a test that
  re-parsed the YAML would only be asserting that the YAML says what it says.

NO STATE NAME IS ASSERTED BY THE ONE REAL-DATA TEST BELOW, and that is deliberate rather
than weak. The loop OWNS THE CLOCK (it reads ``datetime.now`` and hands it down as
``now_utc``), so which states ``test_wiring``'s fixture resolves to depends on how old that
fixture's dates are on the day the suite runs. ``test_evaluator_pass.py`` is where states
are asserted, against a FIXED ``NOW``. What this file asserts about that pass is what does
not drift: one row per dial, in the real table, through its real CHECK constraints.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import pathlib
import signal
from datetime import datetime, timezone

import pytest

from crash_detector.dials.dialset import DIAL_IDS
from evaluator.history_store import MachineStateHistoryStore
from evaluator.resolve import BREADTH_LOOKBACK_ROWS
from ingestion.store import SqliteStore
from ingestion.wiring import build_wiring

from test_wiring import CALM, _seed

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOOP_PATH = ROOT / "deploy/live-dev/evaluator_loop.py"
COLLECTOR_PATH = ROOT / "deploy/live-dev/collector_loop.py"


@pytest.fixture
def loop():
    """The deploy script, loaded fresh per test so its module-level ``stop`` is not shared."""
    specification = importlib.util.spec_from_file_location("_evaluator_loop", LOOP_PATH)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture
def paths(tmp_path, monkeypatch):
    """``CD_DB_PATH`` seeded with every live indicator, ``CD_STATE_PATH`` not yet created.

    The state file is deliberately ABSENT: the write-mode store creating it is part of what
    is under test, and a fixture that pre-created it would hide a reader-door regression.
    """
    raw = tmp_path / "raw.sqlite"
    with SqliteStore(str(raw)) as writer:
        _seed(writer, build_wiring(), CALM)
    state = tmp_path / "machine-state.sqlite"
    monkeypatch.setenv("CD_DB_PATH", str(raw))
    monkeypatch.setenv("CD_STATE_PATH", str(state))
    monkeypatch.delenv("CD_EVALUATE_INTERVAL_SECONDS", raising=False)
    return raw, state


@pytest.fixture(autouse=True)
def restore_signal_handlers():
    """``main`` installs real handlers in the real process. Put the originals back.

    Without this, a SIGTERM handler belonging to a module this test loaded would outlive the
    test and still be installed while the rest of the suite runs.
    """
    before = {number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGINT)}
    try:
        yield
    finally:
        for number, handler in before.items():
            signal.signal(number, handler)


class _Ticker:
    """A stand-in for the module's ``threading.Event`` that ends the loop after N passes.

    Substituted for the global ``stop``, which every reference in the module — including the
    two signal handlers' ``stop.set()`` — looks up as a module attribute at call time, so one
    ``monkeypatch.setattr`` reaches all of them.

    It also WRITES DOWN the timeout it was asked to wait for, which is the only way to
    observe the interval the loop actually decided on: a test that re-read the env var would
    be asserting its own arithmetic.
    """

    def __init__(self, passes: int = 1) -> None:
        self._passes = passes
        self._forced = False
        self.waits: list = []

    def is_set(self) -> bool:
        return self._forced or len(self.waits) >= self._passes

    def set(self) -> None:
        self._forced = True

    def wait(self, timeout) -> bool:
        self.waits.append(timeout)
        return self.is_set()


# --- the two refusals -------------------------------------------------------------------- #


@pytest.mark.parametrize("missing", ["CD_DB_PATH", "CD_STATE_PATH"])
def test_an_unset_store_path_is_refused_and_nothing_is_defaulted(loop, paths, monkeypatch, missing):
    """Neither path has a default. A default would create a database nobody is looking at."""
    monkeypatch.delenv(missing)
    with pytest.raises(SystemExit) as refusal:
        loop.main()
    assert missing in str(refusal.value) and "REFUSED" in str(refusal.value)


@pytest.mark.parametrize("blank", ["CD_DB_PATH", "CD_STATE_PATH"])
def test_an_empty_store_path_is_refused_too(loop, paths, monkeypatch, blank):
    """``os.environ.get`` answers ``""`` for a variable set to nothing, which is not a path."""
    monkeypatch.setenv(blank, "")
    with pytest.raises(SystemExit) as refusal:
        loop.main()
    assert "REFUSED" in str(refusal.value)


# --- the timer --------------------------------------------------------------------------- #


def test_the_interval_defaults_to_one_day(loop, paths, monkeypatch):
    """86400 seconds, read off what the loop actually waited for — and WHY 86400.

    It was 300 until WO-1.3e, which is R2D2's WO-1.3b finding B1: DECISION-RULE.md §4 counts
    persistence in READINGS and designs a reading as DAILY, so a 5-minute pass made
    ``PROVISIONAL_PERSISTENCE`` readings ~15 minutes and ``BREADTH_LOOKBACK_ROWS`` ~100
    minutes. The assertion is spelled as a day in seconds rather than as the literal 86400 so
    that what is under test reads as the UNIT it is: one reading, one day.
    """
    one_day_in_seconds = 24 * 60 * 60
    ticker = _Ticker(passes=1)
    monkeypatch.setattr(loop, "stop", ticker)
    monkeypatch.setattr(loop, "one_pass_for_both_dials", lambda **_: {})
    assert loop.main() == 0
    assert ticker.waits == [float(one_day_in_seconds)]


def test_the_interval_env_var_is_what_the_loop_waits_for(loop, paths, monkeypatch):
    ticker = _Ticker(passes=2)
    monkeypatch.setenv("CD_EVALUATE_INTERVAL_SECONDS", "7.5")
    monkeypatch.setattr(loop, "stop", ticker)
    monkeypatch.setattr(loop, "one_pass_for_both_dials", lambda **_: {})
    assert loop.main() == 0
    assert ticker.waits == [7.5, 7.5]


def test_one_clock_read_per_pass_dates_both_the_evaluation_and_its_log_line(
    loop, paths, monkeypatch, capsys
):
    """``now_utc`` and the log timestamp are the SAME instant, and it is timezone-aware UTC."""
    seen: list = []
    ticker = _Ticker(passes=1)
    monkeypatch.setattr(loop, "stop", ticker)
    monkeypatch.setattr(loop, "one_pass_for_both_dials",
                        lambda **kwargs: seen.append(kwargs["now_utc"]) or {})
    before = datetime.now(timezone.utc)
    loop.main()
    after = datetime.now(timezone.utc)

    (now_utc,) = seen
    assert now_utc.tzinfo is timezone.utc
    assert before <= now_utc <= after
    assert now_utc.isoformat() in capsys.readouterr().out


# --- a failed pass is not a dead loop ---------------------------------------------------- #


def test_a_failed_pass_is_logged_to_stderr_and_the_next_pass_still_runs(
    loop, paths, monkeypatch, capsys
):
    """The collector's own rule, for the same reason: an outage is a gap, not a dead process.

    The failure is raised from inside the pass, so the ``with`` block that opened the write
    handle unwinds through it — the next pass opening the store again is the evidence the
    handle was released and not leaked.
    """
    calls: list = []

    def flaky(**kwargs):
        calls.append(kwargs["now_utc"])
        if len(calls) == 1:
            raise RuntimeError("the raw store is mid-write")
        return {}

    ticker = _Ticker(passes=2)
    monkeypatch.setattr(loop, "stop", ticker)
    monkeypatch.setattr(loop, "one_pass_for_both_dials", flaky)
    assert loop.main() == 0, "a failed pass must not change the loop's exit status"
    assert len(calls) == 2, "the pass after a failure must still have run"

    captured = capsys.readouterr()
    assert "pass FAILED: RuntimeError: the raw store is mid-write" in captured.err
    assert "cd-evaluator-loop stopping" in captured.out


def test_a_failed_pass_still_waits_the_interval_rather_than_spinning(loop, paths, monkeypatch):
    """``stop.wait`` is after the ``except``, not inside the ``try``: a feed outage that fails
    every pass must not become a hot loop hammering the store.

    The interval is set EXPLICITLY rather than left to the module default, because what is
    under test here is that a failed pass waits *the configured interval* — not what that
    interval happens to be. The default is pinned by
    ``test_the_interval_defaults_to_one_day`` alone, so a future change to it moves one
    assertion rather than every test that merely needs *some* interval.
    """
    ticker = _Ticker(passes=2)
    monkeypatch.setenv("CD_EVALUATE_INTERVAL_SECONDS", "11.25")
    monkeypatch.setattr(loop, "stop", ticker)
    monkeypatch.setattr(loop, "one_pass_for_both_dials",
                        lambda **_: (_ for _ in ()).throw(RuntimeError("down")))
    loop.main()
    assert ticker.waits == [11.25, 11.25]


# --- signals ----------------------------------------------------------------------------- #


@pytest.mark.parametrize("number", [signal.SIGTERM, signal.SIGINT])
def test_a_signal_arriving_mid_pass_lets_that_pass_finish_and_then_ends_the_loop(
    loop, paths, monkeypatch, number
):
    """SIGTERM BETWEEN PASSES, NOT MID-PASS (spec §11), tested by signalling mid-pass.

    The handler only sets the event, so the pass it interrupted runs to its end — the
    ``finished`` sentinel is appended AFTER the signal was delivered, and it is there. A
    handler that raised instead would have truncated a pass between the two dials' rows.
    """
    progress: list = []
    ticker = _Ticker(passes=99)  # would run forever; the signal is what ends it
    monkeypatch.setattr(loop, "stop", ticker)

    def pass_that_is_signalled(**_):
        progress.append("started")
        os.kill(os.getpid(), number)
        progress.append("finished")
        return {}

    monkeypatch.setattr(loop, "one_pass_for_both_dials", pass_that_is_signalled)
    assert loop.main() == 0
    assert progress == ["started", "finished"], "the signalled pass was cut short"
    assert len(ticker.waits) == 1, "a second pass ran after the stop was requested"


def test_both_signals_are_handled_and_neither_is_left_to_the_default_disposition(
    loop, paths, monkeypatch
):
    """A container stopped by Docker gets SIGTERM; a hand-run one gets SIGINT. Both are ours."""
    monkeypatch.setattr(loop, "stop", _Ticker(passes=1))
    monkeypatch.setattr(loop, "one_pass_for_both_dials", lambda **_: {})
    loop.main()
    for number in (signal.SIGTERM, signal.SIGINT):
        installed = signal.getsignal(number)
        assert callable(installed) and installed not in (signal.SIG_DFL, signal.SIG_IGN)


# --- the two stores, held differently ---------------------------------------------------- #


def test_this_process_cannot_open_the_raw_store_because_it_never_imports_the_raw_store(loop):
    """The structural half of the read discipline, asserted on the file's own imports.

    ``pass_once._raw_reader`` is the one expression in the product that opens the collector's
    store for this process, and it opens it ``read_only=True``. This file never imports
    ``SqliteStore``, so there is no name in this process that could open it for writing —
    which is a property of the text and is therefore checked against the text.
    """
    imported = _imported_names(LOOP_PATH)
    assert "ingestion.store" not in imported and "SqliteStore" not in imported
    assert not hasattr(loop, "SqliteStore")
    assert "evaluator.history_store.MachineStateHistoryStore" in imported
    assert "evaluator.pass_once.one_pass_for_both_dials" in imported


def test_the_history_store_is_opened_in_write_mode_and_closed_again_each_pass(
    loop, paths, monkeypatch
):
    """WRITE mode, because this is the one process that writes it (spec §11).

    ``read_only`` is asserted ABSENT from the call rather than asserted ``False``: the
    store's default is write and the loop passing it explicitly would be a second place the
    mode is decided.
    """
    opened: list = []

    class _Watched(MachineStateHistoryStore):
        def __init__(self, path, **kwargs):
            opened.append((path, kwargs, "open"))
            super().__init__(path, **kwargs)

        def close(self):
            opened.append((None, None, "close"))
            super().close()

    _, state = paths
    monkeypatch.setattr(loop, "stop", _Ticker(passes=2))
    monkeypatch.setattr(loop, "MachineStateHistoryStore", _Watched)
    monkeypatch.setattr(loop, "one_pass_for_both_dials", lambda **_: {})
    loop.main()

    assert [event for _, _, event in opened] == ["open", "close", "open", "close"]
    assert {kwargs.get("read_only") for _, kwargs, event in opened if event == "open"} == {None}
    assert {path for path, _, event in opened if event == "open"} == {str(state)}


def test_one_real_pass_writes_one_real_row_per_dial_through_the_real_table(
    loop, paths, monkeypatch, capsys
):
    """END TO END, no fake pass: env vars in, a file on disk with two rows in it out.

    The state store does not exist when this starts. The write-mode handle creating it,
    bringing its schema forward and taking two appends is the whole claim; the rows are read
    back out through a SEPARATE read-only handle, so nothing is asserted about a row that
    only ever existed in the writer's memory.
    """
    _, state = paths
    assert not state.exists()
    monkeypatch.setattr(loop, "stop", _Ticker(passes=1))
    assert loop.main() == 0

    with MachineStateHistoryStore(str(state), read_only=True) as reader:
        for dial_id in DIAL_IDS:
            rows = reader.recent(dial_id, limit=BREADTH_LOOKBACK_ROWS)
            assert len(rows) == 1, f"{dial_id}: one pass, one row"
            assert rows[0].dial_id == dial_id

    line = capsys.readouterr().out
    for dial_id in DIAL_IDS:
        assert f"{dial_id}=" in line, "every dial evaluated is named in the pass's log line"


# --- the twin ---------------------------------------------------------------------------- #


def test_the_two_loops_are_the_same_loop(loop):
    """The pattern is the collector's, verbatim where it applies (spec §11).

    Asserted on the TEXT of both files: same stdlib imports for the machinery, the same
    module-level ``threading.Event`` named ``stop``, one ``stop.wait`` each, and the same
    ``main() -> int`` / ``sys.exit(main())`` shape. A second design here — a scheduler, a
    thread pool, a retry policy of its own — would show up as a difference in this list.
    """
    evaluator_text = LOOP_PATH.read_text(encoding="utf-8")
    collector_text = COLLECTOR_PATH.read_text(encoding="utf-8")
    for shared in (
        "stop = threading.Event()",
        "def main() -> int:",
        "signal.signal(signal.SIGTERM, lambda *_: stop.set())",
        "signal.signal(signal.SIGINT, lambda *_: stop.set())",
        "while not stop.is_set():",
        "stop.wait(interval)",
        'if __name__ == "__main__":\n    sys.exit(main())',
    ):
        assert shared in evaluator_text and shared in collector_text, shared
    # Counted on the SYNTAX TREE and not on the text: both files discuss `stop.wait` in
    # prose, and a prose mention is not a second wait.
    assert _stop_waits(evaluator_text) == _stop_waits(collector_text) == 1


def _stop_waits(text: str) -> int:
    """How many times the module actually CALLS ``stop.wait``. One, in both files."""
    return sum(
        1
        for node in ast.walk(ast.parse(text))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "wait"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "stop"
    )


def _imported_names(relative_path) -> set:
    """``module.name`` for every ``from x import y``, plus ``x`` for every ``import x``."""
    tree = ast.parse(pathlib.Path(relative_path).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names
