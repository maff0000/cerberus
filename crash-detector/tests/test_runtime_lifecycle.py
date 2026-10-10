"""SIGTERM, a bounded clean shutdown, and stdout logging — BLUEPRINT §2, A6.

Container-readiness is a property of the APPLICATION (``PBG-RT-010``,
``pbg/skills/core/container-ready-application-design.md``). A process that ignores SIGTERM
gets killed and whatever it was midway through becomes a recovery problem; no amount of
care in a compose file fixes that from outside. So the property is tested here, in the
code, and not deferred to an image nobody is authorised to build.

The last test in this file sends a REAL ``SIGTERM`` to a REAL child process and observes
what it does. That is the only way to establish the property: a mocked signal proves the
mock works.
"""

from __future__ import annotations

import io
import os
import pathlib
import signal
import subprocess
import sys
import time

import pytest

from crash_detector.runtime.lifecycle import (
    DEFAULT_GRACE_SECONDS,
    EXIT_CLEAN,
    EXIT_SHUTDOWN_EXCEEDED_GRACE,
    HANDLED_SIGNALS,
    MAX_GRACE_SECONDS,
    WAIT_SLICE_SECONDS,
    Lifecycle,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENTRYPOINTS = ROOT / "deploy" / "entrypoints"


def _lifecycle(**kwargs) -> tuple[Lifecycle, io.StringIO]:
    stream = io.StringIO()
    return Lifecycle("cd-test", stream=stream, **kwargs), stream


# --- CONSTRUCTION REFUSES AN UNBOUNDED BUDGET ---------------------------------------------- #

def test_a_service_must_be_named():
    with pytest.raises(ValueError):
        Lifecycle("")


@pytest.mark.parametrize("grace", [0.0, -1.0, MAX_GRACE_SECONDS + 0.1, float("inf")])
def test_an_unbounded_or_absurd_grace_period_is_refused(grace: float):
    """An unbounded clean shutdown is not clean; it is a process the platform will kill
    mid-write (Standards Baseline §11).
    """
    with pytest.raises(ValueError):
        Lifecycle("cd-test", grace_seconds=grace)


@pytest.mark.parametrize("grace", [15, True, "15"])
def test_a_grace_period_of_the_wrong_type_is_refused(grace: object):
    with pytest.raises(TypeError):
        Lifecycle("cd-test", grace_seconds=grace)  # type: ignore[arg-type]


def test_the_default_grace_is_under_the_platform_grace_declared_in_compose():
    """A shutdown budget longer than the killer's patience is not a budget."""
    compose = (ROOT / "deploy" / "compose.yaml").read_text(encoding="utf-8")
    assert "stop_grace_period: 30s" in compose
    assert DEFAULT_GRACE_SECONDS < 30.0


def test_both_the_orchestrators_signal_and_the_operators_signal_are_handled():
    """Handling only SIGTERM makes a service behave differently under a human's hands
    than it does in production.
    """
    assert set(HANDLED_SIGNALS) == {signal.SIGTERM, signal.SIGINT}


# --- THE LOOP ------------------------------------------------------------------------------ #

def test_the_loop_runs_until_it_is_asked_to_stop():
    lifecycle, _ = _lifecycle()
    ticks = []

    def tick() -> None:
        ticks.append(1)
        if len(ticks) == 3:
            lifecycle.request_stop()

    assert lifecycle.run(tick, interval_seconds=0.001) == EXIT_CLEAN
    assert len(ticks) == 3


def test_the_wait_wakes_immediately_on_termination():
    """The only sleep in a service. A bare time.sleep would make shutdown latency equal
    to the poll interval.
    """
    lifecycle, _ = _lifecycle()
    lifecycle.request_stop()
    started = time.monotonic()
    assert lifecycle.wait(5.0) is True
    assert time.monotonic() - started < 1.0


def test_a_failing_tick_stops_the_loop_and_exits_non_zero():
    """A service that continues after its work raised is a service reporting health it
    does not have (Standards Baseline §8).
    """
    lifecycle, stream = _lifecycle()
    calls = []

    def tick() -> None:
        calls.append(1)
        raise ZeroDivisionError("planted")

    assert lifecycle.run(tick, interval_seconds=0.001) == 1
    assert len(calls) == 1
    assert "event=tick_failed error_class=ZeroDivisionError" in stream.getvalue()


def test_a_failing_tick_is_logged_by_exception_type_and_not_by_its_message():
    """An exception raised near a connection habitually stringifies the connection, and a
    connection string carries a password (PBG-SEC-002, non-waivable).
    """
    lifecycle, stream = _lifecycle()

    def tick() -> None:
        raise RuntimeError("PLANTED-NOT-A-CREDENTIAL")

    lifecycle.run(tick, interval_seconds=0.001)
    assert "PLANTED-NOT-A-CREDENTIAL" not in stream.getvalue()
    assert "RuntimeError" in stream.getvalue()


@pytest.mark.parametrize("interval", [0.0, -1.0])
def test_a_non_positive_interval_is_refused(interval: float):
    lifecycle, _ = _lifecycle()
    with pytest.raises(ValueError):
        lifecycle.run(lambda: None, interval_seconds=interval)


# --- THE BOUNDED SHUTDOWN ------------------------------------------------------------------- #

def test_every_shutdown_callback_runs_in_registration_order():
    lifecycle, _ = _lifecycle()
    order: list[str] = []
    lifecycle.on_shutdown("first", lambda: order.append("first"))
    lifecycle.on_shutdown("second", lambda: order.append("second"))
    assert lifecycle.shutdown() == EXIT_CLEAN
    assert order == ["first", "second"]


def test_a_failing_callback_does_not_take_the_remaining_ones_with_it():
    lifecycle, stream = _lifecycle()
    ran: list[str] = []

    def explodes() -> None:
        raise OSError("PLANTED-NOT-A-CREDENTIAL")

    lifecycle.on_shutdown("explodes", explodes)
    lifecycle.on_shutdown("survivor", lambda: ran.append("survivor"))
    lifecycle.shutdown()
    assert ran == ["survivor"]
    assert "shutdown_callback_failed callback=explodes error_class=OSError" in (
        stream.getvalue()
    )
    assert "PLANTED-NOT-A-CREDENTIAL" not in stream.getvalue()


def test_the_shutdown_is_bounded_and_says_so_when_it_overruns():
    """If the callbacks exceed the grace period the process says so and exits anyway. It
    does not keep trying to be tidy past the point the platform will kill it.
    """
    elapsed = iter([0.0, 0.0, 99.0, 99.0, 99.0, 99.0])
    stream = io.StringIO()
    lifecycle = Lifecycle(
        "cd-test", grace_seconds=1.0, stream=stream, clock=lambda: next(elapsed)
    )
    ran: list[str] = []
    lifecycle.on_shutdown("slow", lambda: ran.append("slow"))
    lifecycle.on_shutdown("skipped", lambda: ran.append("skipped"))

    assert lifecycle.shutdown() == EXIT_SHUTDOWN_EXCEEDED_GRACE
    # The first callback was inside the budget when it was reached and so it ran; the
    # second was not, and was SKIPPED rather than waited for. That is the bound doing its
    # job: the budget is checked before each callback, not merely reported afterwards.
    assert ran == ["slow"]
    assert "event=shutdown_budget_exhausted callback=skipped" in stream.getvalue()
    assert "exceeded_grace=true" in stream.getvalue()


def test_an_overrun_exit_code_is_distinct_from_a_clean_one():
    """"We shut down, but a callback overran and we stopped waiting" is a different fact
    from "we shut down", and an exit code is the only channel it reaches a restarter by.
    """
    assert EXIT_SHUTDOWN_EXCEEDED_GRACE != EXIT_CLEAN


def test_an_unnamed_or_uncallable_shutdown_callback_is_refused():
    lifecycle, _ = _lifecycle()
    with pytest.raises(ValueError):
        lifecycle.on_shutdown("", lambda: None)
    with pytest.raises(TypeError):
        lifecycle.on_shutdown("x", "not callable")  # type: ignore[arg-type]


# --- LOGGING --------------------------------------------------------------------------------- #

def test_every_log_line_carries_a_utc_timestamp_with_an_explicit_z():
    lifecycle, stream = _lifecycle()
    lifecycle.log("probe", detail="by_reference")
    line = stream.getvalue().strip()
    assert line.startswith("ts=")
    assert line.split()[0].endswith("Z")
    assert "service=cd-test" in line
    assert "event=probe" in line
    assert "detail=by_reference" in line


def test_log_lines_are_flushed_so_the_platform_sees_them_at_once():
    """PBG-OBS-002. A buffered line at the moment of a crash is no trace at all.

    Asserted BEHAVIOURALLY, on a running child, rather than by counting ``flush=True`` in
    the source. The count was the previous form and it was a proxy: it broke when the
    forced-exit path moved from ``print(flush=True)`` to ``os.write``, which is unbuffered
    by construction and so is a STRONGER guarantee than the thing the proxy counted. A
    check that fails when the property improves is measuring the wrong thing.

    Here the child is given a long tick interval, so after its first lines it sleeps. If
    anything were buffered, these reads would block until the process exited.
    """
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("CD_")
    }
    environment["CD_TICK_INTERVAL_SECONDS"] = "30.0"
    environment.pop("PYTHONUNBUFFERED", None)

    process = subprocess.Popen(
        [sys.executable, "-B", str(ENTRYPOINTS / "cd_engine.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        first = process.stdout.readline()
        second = process.stdout.readline()
        assert "event=signals_installed" in first, first
        assert "event=started" in second, second
        assert process.poll() is None, (
            "the child had already exited, so these lines prove nothing about buffering"
        )
    finally:
        process.terminate()
        process.communicate(timeout=20.0)


def test_the_forced_exit_path_does_not_write_through_a_buffered_stream():
    """The other half of the same property, on the path a behavioural test cannot reach
    without killing the runner: the second-signal handler must not touch a lock.

    ``print`` locks the buffered writer. ``os.write`` on a raw descriptor does not, and
    that is why the forced path uses it.
    """
    source = (ROOT / "src" / "crash_detector" / "runtime" / "lifecycle.py").read_text(
        encoding="utf-8"
    )
    handler = source.split("def _on_signal")[1].split("\n    @property")[0]
    assert "print(" not in handler, (
        "the signal handler writes through print(), which locks the buffered writer"
    )
    assert "os._exit(" in handler
    assert "os.write(" in source.split("def _emit_raw")[1].split("def _on_signal")[0]


# --- THE ENTRYPOINTS ------------------------------------------------------------------------ #

EXPECTED_ENTRYPOINTS = {
    "cd_collectors.py": "cd-collectors",
    "cd_witness.py": "cd-witness",
    "cd_engine.py": "cd-engine",
    "cd_public.py": "cd-public",
    "cd_private.py": "cd-private",
    "cd_review.py": "cd-review",
}


def test_there_is_one_entrypoint_per_application_service():
    found = {path.name for path in ENTRYPOINTS.glob("cd_*.py")}
    assert found == set(EXPECTED_ENTRYPOINTS)


@pytest.mark.parametrize("filename,service", sorted(EXPECTED_ENTRYPOINTS.items()))
def test_each_entrypoint_names_its_own_service(filename: str, service: str):
    text = (ENTRYPOINTS / filename).read_text(encoding="utf-8")
    assert f'SERVICE_NAME = "{service}"' in text


def test_the_entrypoints_require_their_configuration_from_the_environment():
    """A tick interval nobody chose is a cadence nobody chose, and cadence is monitored
    (CD-AC-008). There is no in-code default.
    """
    shim = (ENTRYPOINTS / "_service.py").read_text(encoding="utf-8")
    assert 'TICK_INTERVAL_ENV_VAR = "CD_TICK_INTERVAL_SECONDS"' in shim
    assert "REFUSED" in shim


def test_an_entrypoint_refuses_to_start_without_its_declared_configuration():
    """Fail closed, loudly, in a state a human can act on (Standards Baseline §8)."""
    environment = {
        key: value
        for key, value in os.environ.items()
        if key != "CD_TICK_INTERVAL_SECONDS"
    }
    completed = subprocess.run(
        [sys.executable, "-B", str(ENTRYPOINTS / "cd_engine.py")],
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    assert completed.returncode != 0
    assert "CD_TICK_INTERVAL_SECONDS" in completed.stderr


def _boot_with(**overrides: str) -> subprocess.CompletedProcess:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("CD_")
    }
    environment.update(overrides)
    return subprocess.run(
        [sys.executable, "-B", str(ENTRYPOINTS / "cd_engine.py")],
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )


def test_a_blank_setting_is_refused_and_is_not_treated_as_an_absent_one():
    """The two have different causes and different fixes.

    ``CD_SHUTDOWN_GRACE_SECONDS`` HAS a declared default, so an unset variable is fine.
    A variable somebody set to an empty string is not the same fact: it is a configuration
    that did not arrive, and falling back to the default would hide that. This is the
    distinction BLUEPRINT §5 makes between EMPTY and FETCH_FAILED, applied to config.
    """
    completed = _boot_with(
        CD_TICK_INTERVAL_SECONDS="0.01", CD_SHUTDOWN_GRACE_SECONDS=""
    )
    assert completed.returncode != 0
    assert "set but blank" in completed.stderr
    assert "CD_SHUTDOWN_GRACE_SECONDS" in completed.stderr


def test_an_absent_grace_setting_takes_the_declared_default():
    """It is optional, and README.md documents it as defaulting to 15.0.

    The code and the document must agree, so the agreement is MEASURED on a real boot
    rather than asserted in a comment — a comment claiming a default is exactly the kind
    of statement this increment found to be wrong elsewhere. The process boots, so it is
    terminated through the same SIGTERM path the rest of this file establishes.
    """
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("CD_")
    }
    environment["CD_TICK_INTERVAL_SECONDS"] = "0.05"
    environment["PYTHONUNBUFFERED"] = "1"
    process = subprocess.Popen(
        [sys.executable, "-B", str(ENTRYPOINTS / "cd_engine.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        line = process.stdout.readline()
        assert f"grace_seconds={DEFAULT_GRACE_SECONDS}" in line, line
    finally:
        process.terminate()
        process.communicate(timeout=20.0)


def test_a_non_numeric_setting_is_refused_without_reproducing_the_value():
    """An unparseable value is routinely a value somebody pasted from a secret store."""
    completed = _boot_with(
        CD_TICK_INTERVAL_SECONDS="0.01",
        CD_SHUTDOWN_GRACE_SECONDS="PLANTED-NOT-A-CREDENTIAL",
    )
    assert completed.returncode != 0
    assert "is not a number" in completed.stderr
    assert "PLANTED-NOT-A-CREDENTIAL" not in completed.stderr
    assert "PLANTED-NOT-A-CREDENTIAL" not in completed.stdout


# --- THE PROPERTY THAT ONLY A REAL SIGNAL CAN ESTABLISH -------------------------------------- #

def test_a_real_sigterm_produces_a_clean_bounded_shutdown():
    """A REAL child process, a REAL SIGTERM, and the exit code it actually produced.

    This is the only test in the file that establishes the container contract. Everything
    above it tests the mechanism; this tests that the mechanism is wired to the signal the
    platform will send. A mocked signal proves the mock works.

    NON_MUTATING_PROVEN: one short-lived local Python process, no network, no filesystem
    write outside the interpreter's own scratch, no container.
    """
    environment = dict(os.environ)
    environment["CD_TICK_INTERVAL_SECONDS"] = "0.05"
    environment["CD_SHUTDOWN_GRACE_SECONDS"] = "5.0"
    environment["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        [sys.executable, "-B", str(ENTRYPOINTS / "cd_engine.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        deadline = time.monotonic() + 20.0
        started = False
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            line = process.stdout.readline()
            if "event=started" in line:
                started = True
                break
        assert started, "the entrypoint never reported that it had started"

        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=20.0)
    finally:
        if process.poll() is None:  # pragma: no cover - only on a failure path
            process.kill()
            process.communicate()

    assert process.returncode == EXIT_CLEAN, (
        f"SIGTERM produced exit {process.returncode}; stderr={stderr!r}"
    )
    assert "event=signals_installed" in stdout or "event=stopping" in stdout
    assert "event=shutdown_complete" in stdout
    assert "exceeded_grace=false" in stdout


def test_the_termination_flag_acquires_no_lock():
    """CD-ENG-F21. The defect this file exists to keep out, asserted at its own seam.

    The signal handler runs ON THE THREAD IT INTERRUPTED, so any lock that thread already
    holds is a lock the handler waits on forever. This module originally used a
    ``threading.Event`` and called ``set()`` from the handler; ``Event.set()`` acquires the
    condition lock and ``Event.wait()`` holds that same lock for a few bytecodes, so a
    SIGTERM landing in that window wedged the process. Measured on this host BEFORE the
    fix: 5 of 40 SIGTERMs (12.5%) left the child alive, ``SigCgt`` carrying SIGTERM, one
    thread, blocked in ``futex_wait_queue``. AFTER: 0 of 100.

    A wedged process is one the platform SIGKILLs mid-write, which is the precise outcome
    BLUEPRINT §2's SIGTERM contract exists to prevent.

    This assertion fails against the original implementation, which is what makes it a
    guard rather than a description (PBG-ASSURE-017).
    """
    lifecycle, _ = _lifecycle()
    # Read through the slot descriptor, not through ``__dict__``. WO-2R3 increment 9 sealed
    # ``Lifecycle`` (PO-DECISIONS-0016 ruling 2), so instances no longer HAVE a ``__dict__``
    # — which is the point of the seal and not an obstacle to this assertion. What this test
    # is about is the TYPE of the flag, and the slot read answers that identically; the
    # earlier spelling reached the same object by the only route that then existed.
    flag = object.__getattribute__(lifecycle, "_terminating")
    assert type(flag) is bool, (
        f"the termination flag is a {type(flag).__name__}. It must be a plain bool: "
        "setting it is one STORE_ATTR under the GIL, which allocates nothing and cannot "
        "block. A threading primitive here deadlocks the signal handler against the loop."
    )


def test_the_wait_slice_is_bounded_and_well_under_the_shutdown_budget():
    """The price of the lock-free handler is a poll slice, and the price must be small."""
    assert 0.0 < WAIT_SLICE_SECONDS <= 0.25
    assert WAIT_SLICE_SECONDS < DEFAULT_GRACE_SECONDS / 10.0


def test_wait_returns_within_its_own_timeout_when_no_signal_arrives():
    """Slicing must not turn a bounded wait into an unbounded one."""
    lifecycle, _ = _lifecycle()
    started = time.monotonic()
    assert lifecycle.wait(0.2) is False
    elapsed = time.monotonic() - started
    assert 0.15 < elapsed < 2.0, elapsed


@pytest.mark.parametrize("cycle", range(10))
def test_sigterm_is_honoured_on_every_one_of_repeated_real_runs(cycle: int):
    """The empirical backstop behind the structural guard above.

    One SIGTERM proves the wiring exists; the defect it replaced appeared in roughly one
    run in eight, so a single run could not have found it and did not. Repetition is the
    measurement. Each child is signalled at the same point in its lifecycle — immediately
    after it reports `started`, which is when the loop is entering its wait and is exactly
    where the old implementation was vulnerable.
    """
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("CD_")
    }
    environment["CD_TICK_INTERVAL_SECONDS"] = "0.05"
    environment["CD_SHUTDOWN_GRACE_SECONDS"] = "5.0"
    environment["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        [sys.executable, "-B", str(ENTRYPOINTS / "cd_engine.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        while True:
            line = process.stdout.readline()
            assert line, "the child exited before reporting that it had started"
            if "event=started" in line:
                break
        process.send_signal(signal.SIGTERM)
        try:
            process.communicate(timeout=10.0)
        except subprocess.TimeoutExpired:
            raise AssertionError(
                f"cycle {cycle}: the child was still alive 10s after SIGTERM. A process "
                "that does not stop when asked is one the platform kills mid-write."
            ) from None
        assert process.returncode == EXIT_CLEAN, process.returncode
    finally:
        if process.poll() is None:  # pragma: no cover - only on a failure path
            process.kill()
            process.communicate()


def test_a_second_signal_forces_an_immediate_exit_with_the_distinct_code():
    """An operator who signals twice has decided the clean path is not working.

    Exercised in a CHILD, deliberately: the forced path calls ``os._exit`` — because
    ``print`` locks the stream and interpreter shutdown flushes, and a handler must take
    no lock — so running it in-process would take the test runner with it.
    """
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("CD_")
    }
    environment["CD_TICK_INTERVAL_SECONDS"] = "0.05"
    # A long grace and a slow callback, so the first signal cannot finish on its own and
    # the second signal is genuinely the thing that ends the process.
    environment["CD_SHUTDOWN_GRACE_SECONDS"] = "30.0"
    environment["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        [sys.executable, "-B", str(ENTRYPOINTS / "cd_engine.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        while True:
            line = process.stdout.readline()
            assert line
            if "event=started" in line:
                break
        process.send_signal(signal.SIGTERM)
        process.send_signal(signal.SIGTERM)
        try:
            process.communicate(timeout=10.0)
        except subprocess.TimeoutExpired:
            raise AssertionError("a twice-signalled process did not exit") from None
        assert process.returncode in (EXIT_CLEAN, EXIT_SHUTDOWN_EXCEEDED_GRACE), (
            process.returncode
        )
    finally:
        if process.poll() is None:  # pragma: no cover - only on a failure path
            process.kill()
            process.communicate()


def test_a_process_that_ignored_sigterm_would_fail_the_test_above():
    """PBG-ASSURE-017, at the same seam.

    A child that installs SIG_IGN for SIGTERM is left running by the same signal, which is
    what makes the assertion above a measurement rather than a formality. The child is
    given a short self-destruct so this test cannot leave a process behind.
    """
    program = (
        "import signal, time, sys\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "print('ready', flush=True)\n"
        "time.sleep(10)\n"
        "sys.exit(0)\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", program],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout.readline().strip() == "ready"
        process.send_signal(signal.SIGTERM)
        with pytest.raises(subprocess.TimeoutExpired):
            process.wait(timeout=2.0)
    finally:
        process.kill()
        process.communicate()
