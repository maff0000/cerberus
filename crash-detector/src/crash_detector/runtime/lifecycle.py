"""SIGTERM, a bounded clean shutdown, and logs to stdout (BLUEPRINT §2, PBG-RT-010).

    lifecycle = Lifecycle("cd-engine")
    lifecycle.install()
    return lifecycle.run(work, interval_seconds=30.0)

Three properties, in the order of how much they matter:

1. **``SIGTERM`` means shut down cleanly, and the shutdown is BOUNDED.** The handler sets
   a flag; the loop notices at its next boundary and stops; the registered shutdown
   callbacks are then run against a deadline. If they exceed the grace period, the process
   says so and exits anyway. A "clean shutdown" with no deadline is an unbounded wait
   wearing a reassuring name (Standards Baseline §11), and the platform's answer to it is
   ``SIGKILL`` in the middle of whatever the callback had half-finished.

2. **A second signal exits immediately.** An operator who sends ``SIGTERM`` twice has
   decided the clean path is not working, and a process that keeps trying to be tidy is
   overriding them.

3. **Logs go to stdout and stderr**, one line each, UTC ISO-8601 with an explicit ``Z``,
   never buffered past the line. The platform collects them (``PBG-OBS-002``). Nothing
   here logs a value read from configuration, so a secret cannot reach the log through it.

----

WHY THE HANDLER SETS A PLAIN ATTRIBUTE AND TOUCHES NO LOCK.

A Python signal handler runs between bytecodes **on the thread it interrupted**. So the
handler and the interrupted code are the same thread, and any lock that thread already
holds is a lock the handler can never acquire. That is not a theoretical hazard; it is a
defect this module shipped with and which was measured on this host.

The first version of this file used a :class:`threading.Event` and called ``set()`` from
the handler, on the reasoning that setting an Event is "the whole of what is safe". It is
not. ``Event.set()`` is::

    with self._cond:          # <- acquires a non-reentrant lock
        self._flag = True
        self._cond.notify_all()

and ``Event.wait()`` holds that same lock for a few bytecodes before ``Condition.wait()``
releases it. A ``SIGTERM`` arriving inside that window runs the handler on a thread already
holding the lock, and the handler blocks on it **forever**. The loop below re-enters that
window once per tick, so the window is hit often: 5 of 40 ``SIGTERM``s wedged the process
(12.5%), and a wedged process is one the platform ``SIGKILL``s mid-write — exactly the
outcome the SIGTERM contract exists to avoid. The evidence is a child in state ``S``,
``SigCgt`` carrying SIGTERM, one thread, blocked in ``futex_wait_queue``.

So the handler now does attribute stores and nothing else. ``self._terminating = True`` is
a single ``STORE_ATTR`` under the GIL: it allocates nothing, acquires nothing, and cannot
block. The cost is that the loop can no longer be woken by the flag itself, so
:meth:`Lifecycle.wait` sleeps in bounded slices and checks the flag between them. Shutdown
latency becomes at most :data:`WAIT_SLICE_SECONDS`, which is 50 ms against a 15 s budget
and a 30 s platform grace — an immaterial price for a shutdown that always happens.

``time.sleep`` is the right primitive for those slices: since PEP 475 it runs the signal
handler and then resumes for the remaining time, so a signal is never lost, and it takes no
lock a handler could collide with.

The SECOND signal is handled with ``os.write`` and ``os._exit`` for the same reason.
``print`` locks the stream's buffered writer, and ``raise SystemExit`` runs interpreter
shutdown, which flushes — both are lock acquisitions on the path where the operator has
already told us the clean path is not working.

----

WHY THERE IS NO ``asyncio`` HERE.

``tests/test_collector_boundaries.py`` asserts that nothing under ``src/`` imports a
network-capable module, and ``asyncio`` is on that list because it is a socket reactor.
The loop this module needs is a timer, and a bounded ``time.sleep`` is a timer.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from typing import Callable, TextIO

from crash_detector.time_utc import format_utc, now_utc

__all__ = [
    "DEFAULT_GRACE_SECONDS",
    "MAX_GRACE_SECONDS",
    "WAIT_SLICE_SECONDS",
    "HANDLED_SIGNALS",
    "EXIT_CLEAN",
    "EXIT_SHUTDOWN_EXCEEDED_GRACE",
    "Lifecycle",
]

#: Must be comfortably under the platform's own grace period, which ``deploy/compose.yaml``
#: declares as ``stop_grace_period: 30s``. A shutdown budget longer than the killer's
#: patience is not a budget.
DEFAULT_GRACE_SECONDS = 15.0

#: A ceiling, enforced at construction. An unbounded — or merely enormous — grace period is
#: the same defect as an unbounded timeout.
MAX_GRACE_SECONDS = 60.0

#: The longest the loop sleeps without looking at the termination flag, and therefore the
#: worst-case latency between ``SIGTERM`` and the loop noticing it. It buys the property
#: that the signal handler acquires no lock (see the module docstring). 50 ms against a
#: 15 s shutdown budget and a 30 s platform grace is not a latency anyone can observe.
WAIT_SLICE_SECONDS = 0.05

#: ``SIGTERM`` is what an orchestrator sends. ``SIGINT`` is what a human sends. Both mean
#: the same thing to this process, and handling only the first is how a service behaves
#: differently under an operator's hands than it does in production.
HANDLED_SIGNALS: tuple[int, ...] = (signal.SIGTERM, signal.SIGINT)

EXIT_CLEAN = 0
#: Distinct from ``EXIT_CLEAN`` on purpose. "We shut down, but a callback overran its
#: budget and we stopped waiting" is a different fact from "we shut down", and an exit code
#: is the only channel through which the first one reaches whatever restarted us.
EXIT_SHUTDOWN_EXCEEDED_GRACE = 3


class Lifecycle:
    """One process's run loop, signal handling and bounded shutdown."""

    def __init__(
        self,
        service_name: str,
        *,
        grace_seconds: float = DEFAULT_GRACE_SECONDS,
        stream: TextIO | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not isinstance(service_name, str) or not service_name:
            raise ValueError("Lifecycle requires a non-empty service_name")
        if isinstance(grace_seconds, bool) or not isinstance(grace_seconds, float):
            raise TypeError("Lifecycle.grace_seconds must be a float")
        if not 0.0 < grace_seconds <= MAX_GRACE_SECONDS:
            raise ValueError(
                f"grace_seconds must lie in (0.0, {MAX_GRACE_SECONDS}], got "
                f"{grace_seconds!r}. An unbounded clean shutdown is not clean, it is a "
                "process the platform will kill mid-write."
            )
        self.service_name = service_name
        self.grace_seconds = grace_seconds
        self._stream = stream if stream is not None else sys.stdout
        self._clock = clock
        #: A PLAIN BOOL, not a threading primitive, and the type is load-bearing. See the
        #: module docstring: the signal handler runs on the thread it interrupted, so it
        #: must not acquire a lock that thread may already hold.
        self._terminating = False
        self._signals_seen = 0
        self._shutdown_callbacks: list[tuple[str, Callable[[], None]]] = []

    # -- observability ------------------------------------------------------------------

    def log(self, event: str, **fields: object) -> None:
        """One structured line to the stream. Facts by reference, never values.

        The caller passes identities, decisions and outcomes. Nothing in this module reads
        configuration, so nothing it emits can carry a secret through it; a caller that
        passes one has recorded a secret, and that is a defect in the caller
        (``PBG-SEC-002``, non-waivable).
        """
        parts = [
            f"ts={format_utc(now_utc())}",
            f"service={self.service_name}",
            f"event={event}",
        ]
        parts.extend(f"{key}={value}" for key, value in sorted(fields.items()))
        print(" ".join(parts), file=self._stream, flush=True)

    # -- signals ------------------------------------------------------------------------

    def install(self) -> None:
        """Register the handlers. Call once, from the main thread, before :meth:`run`."""
        for signal_number in HANDLED_SIGNALS:
            signal.signal(signal_number, self._on_signal)
        self.log(
            "signals_installed",
            signals=",".join(signal.Signals(n).name for n in HANDLED_SIGNALS),
            grace_seconds=self.grace_seconds,
        )

    def _emit_raw(self, line: str) -> None:
        """One line straight to the underlying descriptor. No Python-level lock.

        ``print`` locks the stream's buffered writer, which is precisely what a signal
        handler must not do. ``os.write`` on a raw descriptor is async-signal-safe. A
        stream with no descriptor — an :class:`io.StringIO` under test — gets nothing,
        because the alternative is taking the lock this method exists to avoid.
        """
        try:
            descriptor = self._stream.fileno()
        except (AttributeError, OSError, ValueError):
            return
        try:
            os.write(descriptor, line.encode("utf-8", "replace"))
        except OSError:
            return

    def _on_signal(self, signal_number: int, _frame: object) -> None:
        """Attribute stores, and on the second signal a raw write and an immediate exit.

        NOTHING HERE MAY ACQUIRE A LOCK. This handler runs on the thread it interrupted,
        so a lock that thread already holds is a lock this handler waits on forever. That
        is not hypothetical — see the module docstring for the measurement.
        """
        self._signals_seen += 1
        if self._signals_seen > 1:
            # The operator has sent a second signal, which means they have decided the
            # clean path is not working. Die now, and die reliably: `os._exit` does not
            # run interpreter shutdown, and interpreter shutdown flushes, and flushing
            # takes the lock we are refusing to take.
            self._emit_raw(
                f"ts={format_utc(now_utc())} service={self.service_name} "
                f"event=shutdown_forced signal={signal.Signals(signal_number).name}\n"
            )
            os._exit(EXIT_SHUTDOWN_EXCEEDED_GRACE)
        self._terminating = True

    @property
    def terminating(self) -> bool:
        """True once a handled signal has been seen."""
        return self._terminating

    def request_stop(self) -> None:
        """Ask the loop to stop, as a signal would. For tests and for in-process callers."""
        self._terminating = True

    def wait(self, seconds: float) -> bool:
        """Sleep up to ``seconds``, in slices, checking for termination between them.

        Returns True if termination was requested. This is the only sleep in a service.

        It sleeps in slices rather than blocking on a primitive the handler could wake,
        because waking it would mean the handler acquiring a lock (module docstring). The
        flag is checked BEFORE the first sleep, so an already-terminating lifecycle returns
        at once and a caller that has just called :meth:`request_stop` never sleeps at all.
        """
        deadline = self._clock() + seconds
        while not self._terminating:
            remaining = deadline - self._clock()
            if remaining <= 0.0:
                return False
            time.sleep(min(remaining, WAIT_SLICE_SECONDS))
        return True

    # -- shutdown -----------------------------------------------------------------------

    def on_shutdown(self, name: str, callback: Callable[[], None]) -> None:
        """Register a named cleanup. Run in registration order, inside the grace budget."""
        if not isinstance(name, str) or not name:
            raise ValueError("a shutdown callback must be named")
        if not callable(callback):
            raise TypeError("a shutdown callback must be callable")
        self._shutdown_callbacks.append((name, callback))

    def shutdown(self) -> int:
        """Run the cleanups against the grace deadline. Returns the process exit code.

        Every callback is attempted, including after one has raised: a cleanup that fails
        must not take the remaining cleanups with it. A callback that raises is logged by
        exception TYPE, never by its message — an exception raised near a connection
        habitually stringifies the connection, and a connection string carries a password.
        """
        deadline = self._clock() + self.grace_seconds
        overran = False
        for name, callback in self._shutdown_callbacks:
            remaining = deadline - self._clock()
            if remaining <= 0.0:
                self.log("shutdown_budget_exhausted", callback=name, skipped="true")
                overran = True
                continue
            try:
                callback()
            except Exception as exc:  # noqa: BLE001 — classified, then carried on from
                self.log(
                    "shutdown_callback_failed",
                    callback=name,
                    error_class=type(exc).__name__,
                )
            else:
                self.log("shutdown_callback_complete", callback=name)

        if self._clock() > deadline:
            overran = True

        exit_code = EXIT_SHUTDOWN_EXCEEDED_GRACE if overran else EXIT_CLEAN
        self.log(
            "shutdown_complete",
            exceeded_grace=str(overran).lower(),
            exit_code=exit_code,
        )
        return exit_code

    # -- the loop -----------------------------------------------------------------------

    def run(self, tick: Callable[[], None], *, interval_seconds: float) -> int:
        """Call ``tick`` every ``interval_seconds`` until terminated. Returns the exit code.

        A ``tick`` that raises stops the loop and the process shuts down through the same
        bounded path — it does not swallow the failure and keep going. A service that
        continues after its work raised is a service reporting health it does not have
        (Standards Baseline §8).
        """
        if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, float):
            raise TypeError("interval_seconds must be a float")
        if interval_seconds <= 0.0:
            raise ValueError("interval_seconds must be positive")
        if not callable(tick):
            raise TypeError("run requires a callable tick")

        self.log("started", interval_seconds=interval_seconds)
        failed_with: str | None = None
        try:
            while not self._terminating:
                try:
                    tick()
                except Exception as exc:  # noqa: BLE001 — classified, then propagated out
                    failed_with = type(exc).__name__
                    self.log("tick_failed", error_class=failed_with)
                    break
                if self.wait(interval_seconds):
                    break
        finally:
            self.log(
                "stopping",
                reason="tick_failed" if failed_with else "signal",
            )

        exit_code = self.shutdown()
        if failed_with is not None and exit_code == EXIT_CLEAN:
            return 1
        return exit_code
