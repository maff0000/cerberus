"""PROBE E2/E3 — RE-MEASURING THE "ABILITY TO EXECUTE CODE INSIDE THE PACKAGE" SENTENCES.

Run from the ROOT of a tree:
``python3 -B variants/WO-2R3/P-E23-what-the-in-package-execution-sentence-gets-wrong.py``

**NO VERDICT IS PRINTED.** Read the DATA lines (F-C1).

`PO-DECISIONS-0011` ruling 3 ORDERS two sentences REWRITTEN to their measured reach:

**E2 — `src/crash_detector/admission.py`, DECLARED LIMIT 1 (c):**

    *"WHAT IS AND IS NOT DEFEATED BY (c). It is NOT a caller route: it needs the ability to
     execute code inside the package."*

**E3 — `src/crash_detector/establishment.py` DECLARED LIMIT 3, and the SAME SENTENCE in
`src/crash_detector/admission.py`. ONE SENTENCE, TWO MODULES, LOAD-BEARING IN BOTH:**

    *"Every route requires the ability to execute code inside this package, which is the
     universal limit every in-process guard on this project lives inside."*

`CD-ASR-WO2R3-01`: **"The sentence is wrong in both directions at once."** TOO NARROW —
`Agrees.__new__` needs no package code at all. TOO WIDE — it treats in-package execution as a
high bar, and the CD-BP-003 door hands that ability to any caller.

**THIS PROBE CORRECTS A SENTENCE. IT DOES NOT CLOSE A ROUTE.** Closing the `__new__`/`__dict__`
route — the `__setstate__` technique this codebase already applies to the dial provenance types
— is a design change nobody has ruled, it is not among WO-2R3 increment 6's items, and it is
**explicitly not this seat's**. Arm 1 exists to measure the precondition, not to fix it.

THE THREE ARMS:

  1 TOO NARROW  — how much package code does `Agrees.__new__` + `__dict__` actually run?
  2 TOO WIDE    — does passing an object to the CD-BP-003 door hand a caller in-package
                  execution? Measured by COUNTING what `collect` calls on caller-supplied
                  objects, and by taking the frame from inside one of those calls.
  3 THE ASYMMETRY — the dials layer defends against exactly the arm-1 move and the
                  establishment layer does not. Measured, and RAISED AS A FINDING, NOT FIXED.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from crash_detector.collectors.adapter import FetchedResponse  # noqa: E402
from crash_detector.collectors.delay import DelayKind  # noqa: E402
from crash_detector.collectors.runner import RetryPolicy, collect  # noqa: E402
from crash_detector.establishment import (  # noqa: E402
    governed_types,
    is_establishing_type,
)
from crash_detector.witness.panel import Agrees  # noqa: E402

NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reading"],
    "properties": {"reading": {"type": "number", "minimum": 0.0, "maximum": 1.0}},
}


# --- ARM 1 — TOO NARROW ------------------------------------------------------------------ #

def arm_1_how_much_package_code_does_the_new_route_run() -> None:
    print("--- ARM 1 (E3, TOO NARROW): does the `__new__` route need to run package code?")

    #: A tracer that counts EVERY line executed inside `src/crash_detector/`. This is the
    #: measurement: "the ability to execute code inside the package" is a claim about lines,
    #: so it is answered by counting lines.
    package_root = str(Path(__file__).resolve().parents[2] / "src" / "crash_detector")
    executed: dict = {"lines": 0, "files": set()}

    def trace(frame, event, _arg):
        filename = frame.f_code.co_filename
        if filename.startswith(package_root):
            executed["lines"] += 1
            executed["files"].add(Path(filename).name)
        return trace

    print(f"    is_establishing_type(Agrees)            : {is_establishing_type(Agrees)}")
    print(f"    Agrees is in governed_types()           : {Agrees in set(governed_types())}")

    sys.settrace(trace)
    try:
        smuggled = Agrees.__new__(Agrees)
        smuggled.__dict__.update(
            divergence_measure=object(), as_of_utc="not a datetime", freshness=object()
        )
    finally:
        sys.settrace(None)

    print(f"    LINES OF PACKAGE CODE EXECUTED BY THAT  : {executed['lines']}")
    print(f"    package files touched                   : {sorted(executed['files'])}")
    print(f"    type(smuggled) is exactly Agrees        : {type(smuggled) is Agrees}")
    print(f"    isinstance(smuggled, Agrees)            : {isinstance(smuggled, Agrees)}")
    print(f"    smuggled.as_of_utc                      : {smuggled.as_of_utc!r}")
    print(f"    smuggled.divergence_measure             : "
          f"{type(smuggled.divergence_measure).__name__}")

    #: The control: the SAME type through the front door, traced the same way.
    executed["lines"] = 0
    executed["files"] = set()
    sys.settrace(trace)
    try:
        try:
            Agrees(divergence_measure=object(), as_of_utc="not a datetime", freshness=object())
        except Exception as exc:  # noqa: BLE001
            refusal = f"REFUSED {type(exc).__name__}"
        else:
            refusal = "***ACCEPTED***"
    finally:
        sys.settrace(None)
    print(f"    CONTROL — the same values through Agrees(...): {refusal}")
    print(f"    LINES OF PACKAGE CODE EXECUTED BY THE CONTROL: {executed['lines']}")
    print()


# --- ARM 2 — TOO WIDE -------------------------------------------------------------------- #

class _CountingAdapter:
    """Counts every member of itself that `collect` touches, and takes a frame from inside one.

    IT IMPORTS NOTHING FROM `crash_detector` for its leverage. Everything it reaches, it
    reaches through the frame stack it is standing in — which is what BEING CALLED gives it.
    """

    source_id = "src.probe.e23"
    adapter_id = "probe-e23.v0"
    response_schema = SCHEMA

    def __init__(self) -> None:
        self.touched: list = []
        self.reached_module: str = "<not reached>"
        self.rebound: object = None

    def __getattribute__(self, name):
        if not name.startswith("_"):
            object.__getattribute__(self, "touched").append(name)
        return object.__getattribute__(self, name)

    def fetch(self, *, timeout_seconds: float) -> FetchedResponse:
        #: THE WHOLE OF THE LEVERAGE, from inside a call the runner made to caller code.
        frame = sys._getframe(1)
        while frame is not None:
            module_globals = frame.f_globals
            if module_globals.get("__name__") == "crash_detector.collectors.runner":
                object.__setattr__(
                    self, "reached_module", module_globals["__name__"]
                )
                object.__setattr__(self, "rebound", module_globals.get("ensure_utc"))
                break
            frame = frame.f_back
        return FetchedResponse(payload={"reading": 0.25}, source_as_of_utc=NOW)

    def is_empty(self, payload: object) -> bool:
        return False


class _Sink:
    def __init__(self) -> None:
        self.rows: list = []
        self.touched: list = []

    def record(self, attempt) -> None:
        self.touched.append("record")
        self.rows.append(attempt)


class _Ledger:
    def __init__(self) -> None:
        self.seen: set = set()
        self.touched: list = []

    def admit_if_absent(self, key) -> bool:
        self.touched.append("admit_if_absent")
        if key in self.seen:
            return False
        self.seen.add(key)
        return True


def arm_2_does_the_door_hand_a_caller_in_package_execution() -> None:
    print("--- ARM 2 (E2/E3, TOO WIDE): does passing an object to the CD-BP-003 door hand a")
    print("    caller the ability to execute code inside the package?")

    adapter = _CountingAdapter()
    sink = _Sink()
    ledger = _Ledger()
    result = collect(
        adapter,
        policy=RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0),
        sink=sink,
        ledger=ledger,
        collector_run_id="probe-e23",
        started_utc=NOW,
        delay=DelayKind.WALL_CLOCK,
    )

    touched = adapter.touched
    print(f"    members of the ADAPTER `collect` touched : {len(touched)} — {sorted(set(touched))}")
    print(f"    ... of which are CALLS into caller code  : "
          f"{sorted({name for name in touched if name in ('fetch', 'is_empty')})}")
    print(f"    members of the SINK touched              : {sorted(set(sink.touched))}")
    print(f"    members of the LEDGER touched            : {sorted(set(ledger.touched))}")
    print(f"    reached module globals of                : {adapter.reached_module}")
    print(f"    could read runner.ensure_utc from there  : {adapter.rebound is not None}")
    print(f"    final_outcome                            : {type(result.final_outcome).__name__}")
    print("    (READING IT: every one of those calls runs CALLER CODE INSIDE A FRAME WHOSE")
    print("     f_back chain reaches the package's own module globals. THE DOOR HANDS THAT")
    print("     ABILITY TO ANY CALLER — it is not a precondition a caller has to acquire.)")
    print()


# --- ARM 3 — THE ASYMMETRY --------------------------------------------------------------- #

def arm_3_the_asymmetry() -> None:
    print("--- ARM 3: the asymmetry the auditor names — the dials layer defends against the")
    print("    arm-1 move and the establishment layer does not.")
    #: IMPORT THE WHOLE PACKAGE FIRST. `governed_types()` is a registry populated AT IMPORT, so
    #: its size depends on what has been imported — a probe that read it after importing four
    #: modules would report a number about the probe. Measured with and without, and printed
    #: both ways, because that difference is exactly the kind of thing this project keeps
    #: finding in its own counts.
    import importlib
    import pkgutil

    import crash_detector

    before_walk = len(list(governed_types()))
    for info in pkgutil.walk_packages(crash_detector.__path__, prefix="crash_detector."):
        importlib.import_module(info.name)
    print(f"    governed types BEFORE importing the whole package: {before_walk} "
          "(a number about the probe, not the product)")
    defenders = []
    for governed in governed_types():
        if getattr(governed, "__setstate__", None) is not None:
            defenders.append(governed.__name__)
    print(f"    governed types in total                  : {len(list(governed_types()))}")
    print(f"    governed types defining __setstate__     : {len(defenders)} — {sorted(defenders)}")
    print("    (`__setstate__` is the technique this codebase ALREADY applies elsewhere to")
    print("     refuse an object rebuilt without its constructor. THIS PROBE MEASURES THE GAP")
    print("     AND DOES NOT CLOSE IT: closing it is F-A4, it is a design change nobody has")
    print("     ruled, and it is EXPLICITLY NOT WO-2R3 INCREMENT 6's.)")
    print()


def main() -> int:
    print("PROBE E2/E3 — RE-MEASURING THE 'IN-PACKAGE EXECUTION' SENTENCES")
    print(f"tree: {Path(__file__).resolve().parents[2]}")
    print("NO VERDICT IS PRINTED. READ THE DATA LINES.")
    print()
    arm_1_how_much_package_code_does_the_new_route_run()
    arm_2_does_the_door_hand_a_caller_in_package_execution()
    arm_3_the_asymmetry()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
