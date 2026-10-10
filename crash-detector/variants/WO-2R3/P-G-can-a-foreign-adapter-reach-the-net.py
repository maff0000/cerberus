"""P-G — HALF (a) OF PO-DECISIONS-0012 RULING 4, ASKED OF THE **DECLARED-FOREIGN ACTOR**.

P-F establishes that in-process code of the attacker's own authorship can obtain the net by
``getattr``, by an explicit ``from ... import`` of the private name, and out of
``sys.modules``. **THAT ANSWER IS UNINTERESTING ON ITS OWN** — it is arbitrary code
execution, which ruling 4 explicitly puts outside the settled threat model, and it is
equally true of every module-level callable in the package.

**THE ANSWER THAT IS NOT UNINTERESTING IS THIS ONE.** ``collect()`` accepts a
``SourceAdapter`` — an object this system DECLARES it will take from outside (CD-BP-003,
BLUEPRINT §17). An adapter is foreign code that runs in-process by design, not by breach.
So the threat-model question is:

    **CAN A CONFORMING HOSTILE ADAPTER, ARRIVING THROUGH THE DOOR THE SYSTEM ADVERTISES,
    OBTAIN AND CALL THE NET?**

The fifth Assurance seat said of the ``__wrapped__`` route: *"I did not demonstrate a route
to it from ``collect``."* This probe attempts exactly that demonstration and reports the
result whichever way it falls.

**DISCIPLINE.** This module imports NOTHING from ``crash_detector.engine`` at module level,
and the adapter's own code imports nothing at all. If the net becomes reachable it is
because the RUNTIME put it within reach, not because this probe handed it over.

    PYTHONPATH=<tree>/src python3 -B variants/WO-2R3/P-G-can-a-foreign-adapter-reach-the-net.py
"""

from __future__ import annotations

import datetime as _dt
import sys

TARGET = "crash_detector.engine.evaluate"

FINDINGS: dict[str, str] = {}


def _short(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {str(exc).splitlines()[0][:120]}"


class HostileAdapter:
    """Conforms to ``SourceAdapter``. Its ``fetch`` does the reaching.

    It imports nothing. Every route below uses only what the interpreter hands any object
    that is being called: its own frame, and the interpreter's module table.

    The four declarative members are what ``missing_adapter_members`` requires; supplying
    them is what makes this adapter CONFORMING rather than merely hostile. It gets through
    the advertised door on the strength of them.
    """

    source_id = "src.a"
    adapter_id = "hostile"
    response_schema: dict = {"type": "object"}

    def is_empty(self, payload) -> bool:
        return False

    def fetch(self, *, timeout_seconds: float):
        # ---- ROUTE 1: the interpreter's module table -------------------------------
        module = sys.modules.get(TARGET)
        if module is None:
            FINDINGS["R1 sys.modules"] = (
                f"{TARGET} IS NOT IN sys.modules at the moment collect() calls the adapter "
                "— the collection path has not imported it"
            )
        else:
            net = getattr(module, "_evaluate_dial", None)
            FINDINGS["R1 sys.modules"] = (
                f"{TARGET} IS in sys.modules; _evaluate_dial obtained: {net is not None}"
            )
            if net is not None:
                FINDINGS["R1 call"] = _try_call(net)

        # ---- ROUTE 2: walk this adapter's own call frames ---------------------------
        # The E2/E3 mechanism, re-run for THIS target: an adapter reads the globals of
        # every frame between it and the interpreter, looking for the module or the object.
        frame = sys._getframe()
        depth = 0
        seen_modules: list[str] = []
        reached_via_frames = None
        while frame is not None and depth < 64:
            g = frame.f_globals
            name = g.get("__name__", "?")
            seen_modules.append(name)
            if "_evaluate_dial" in g:
                reached_via_frames = g["_evaluate_dial"]
                break
            # a frame's globals may hold the MODULE rather than the object
            for value in list(g.values()):
                if getattr(value, "__name__", None) == TARGET:
                    reached_via_frames = getattr(value, "_evaluate_dial", None)
                    break
            if reached_via_frames is not None:
                break
            frame = frame.f_back
            depth += 1
        FINDINGS["R2 frame walk"] = (
            f"frames walked: {depth + 1}; modules on the stack: {seen_modules}; "
            f"_evaluate_dial reached: {reached_via_frames is not None}"
        )

        # ---- ROUTE 3: import it, which is what any in-process code may do ------------
        # Recorded for completeness and labelled honestly: this IS arbitrary code
        # execution and ruling 4 puts it outside the threat model. It is here so the
        # contrast between R1/R2 and R3 is visible rather than asserted.
        try:
            import importlib

            forced = importlib.import_module(TARGET)
            net = getattr(forced, "_evaluate_dial")
            FINDINGS["R3 explicit import (OUT OF THREAT MODEL)"] = (
                f"obtained {net!r}"[:110]
            )
            FINDINGS["R3 call"] = _try_call(net)
        except Exception as exc:  # noqa: BLE001
            FINDINGS["R3 explicit import (OUT OF THREAT MODEL)"] = f"failed -> {_short(exc)}"

        raise RuntimeError("the adapter fetched nothing; reaching was its whole purpose")


def _try_call(net) -> str:
    """Call the net with operands no door established, and say what happened."""
    try:
        import importlib

        cfg = importlib.import_module("crash_detector.engine.config")
        obs = importlib.import_module("crash_detector.observations")
        now = _dt.datetime(2026, 8, 23, tzinfo=_dt.timezone.utc)
        spec = cfg.DialSpec(
            dial_id="equity_crash",
            required_input_ids=("src.a",),
            contributing_input_ids=(),
            model_ref="never-resolved",
        )
        reading = net(spec, {"src.a": obs.OK(payload={}, source_as_of_utc=now)}, now)
        return f"CALLED — returned {type(reading).__name__}"
    except Exception as exc:  # noqa: BLE001
        return f"call raised -> {_short(exc)}"


def main() -> int:
    from crash_detector.collectors.delay import DelayKind
    from crash_detector.collectors.runner import RetryPolicy, collect

    runner = sys.modules["crash_detector.collectors.runner"]
    print(f"tree: {runner.__file__}")
    print(f"python: {sys.version.split()[0]}")
    print()
    print(f"{TARGET} in sys.modules BEFORE collect(): {TARGET in sys.modules}")
    print("  (this probe imported the COLLECTION path only, as a host would)")
    print()

    now = _dt.datetime(2026, 8, 23, tzinfo=_dt.timezone.utc)
    try:
        collect(
            HostileAdapter(),
            policy=RetryPolicy(max_attempts=1, timeout_seconds=1.0, backoff_seconds=0.0),
            sink=_NullSink(),
            ledger=_NullLedger(),
            collector_run_id="P-G",
            started_utc=now,
            delay=DelayKind.WALL_CLOCK,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"collect() returned control by raising: {_short(exc)}")
    print()

    print("WHAT THE ADAPTER REACHED, FROM INSIDE collect():")
    if not FINDINGS:
        print("  (the adapter's fetch was never called — see above)")
    for route, outcome in FINDINGS.items():
        print(f"  {route:<42} {outcome}")
    print()
    print(f"{TARGET} in sys.modules AFTER collect():  {TARGET in sys.modules}")
    return 0


class _NullSink:
    def record(self, *a, **k):
        return None

    def __getattr__(self, name):
        return lambda *a, **k: None


class _NullLedger:
    def __getattr__(self, name):
        return lambda *a, **k: True


if __name__ == "__main__":
    raise SystemExit(main())
