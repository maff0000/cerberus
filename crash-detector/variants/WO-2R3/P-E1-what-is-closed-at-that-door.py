"""PROBE E1 — RE-MEASURING EVERY CLAIM IN "WHAT IS CLOSED AT THAT DOOR AND IS NOT A LIMIT".

Run from the ROOT of a tree:  ``python3 -B variants/WO-2R3/P-E1-what-is-closed-at-that-door.py``

**NO VERDICT IS PRINTED.** Read the DATA lines. (`CD-ASR-WO2R3-01`'s F-C1: four probes in
this project print a verdict they did not earn.)

WHY IT EXISTS. `PO-DECISIONS-0011` ruling 3 ORDERS the `required-tests.yaml` "closed and not
a limit" list REWRITTEN to its measured reach. The dispatch adds: *"RE-READ THE WHOLE LIST,
NOT ONLY THE SENTENCE QUOTED."* The list makes FOUR claims and only one of them was the
sentence the auditor quoted. This probe runs all four, so the replacement wording is a
measurement and not a better-sounding sentence.

THE FOUR CLAIMS, VERBATIM FROM `required-tests.yaml` BEFORE THIS INCREMENT:

  (i)   "`policy` exact RetryPolicy (isinstance admitted a subclass shadowing max_attempts
        with a property until this increment)"
  (ii)  "`started_utc` exact datetime then rebuilt by ensure_utc"
  (iii) "`delay` exact DelayKind from a closed enum"
  (iv)  "every value the four Protocols RETURN exact-typed at its point of return"

AND THE ONE THE SAME LIST CARRIES BY IMPLICATION, which `CD-ASR-WO2R3-01` ESCAPE 2 defeated:
`runner.py`'s own `type(response) is not FetchedResponse` door.

**THE HOSTILE CALLER HERE IMPORTS NOTHING FROM `crash_detector` TO GET ITS LEVERAGE** — it
reaches the runner's module globals through the frame it is handed by being called. That is
the auditor's route and it is reproduced, not quoted.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from crash_detector.collectors import runner as runner_module  # noqa: E402
from crash_detector.collectors.adapter import FetchedResponse  # noqa: E402
from crash_detector.collectors.delay import DelayKind  # noqa: E402
from crash_detector.collectors.runner import RetryPolicy, collect  # noqa: E402
from crash_detector.observations import OK  # noqa: E402

NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reading"],
    "properties": {"reading": {"type": "number", "minimum": 0.0, "maximum": 1.0}},
}


class _Sink:
    def __init__(self) -> None:
        self.rows: list = []

    def record(self, attempt) -> None:
        self.rows.append(attempt)


class _Ledger:
    def __init__(self) -> None:
        self.seen: set = set()

    def admit_if_absent(self, key) -> bool:
        if key in self.seen:
            return False
        self.seen.add(key)
        return True


class _PlainAdapter:
    source_id = "src.probe.e1"
    adapter_id = "probe-e1.v0"
    response_schema = SCHEMA

    def fetch(self, *, timeout_seconds: float) -> FetchedResponse:
        return FetchedResponse(payload={"reading": 0.25}, source_as_of_utc=NOW)

    def is_empty(self, payload: object) -> bool:
        return False


def _run(adapter, *, policy=None, started_utc=NOW, delay=DelayKind.WALL_CLOCK) -> str:
    try:
        result = collect(
            adapter,
            policy=RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)
            if policy is None
            else policy,
            sink=_Sink(),
            ledger=_Ledger(),
            collector_run_id="probe-e1",
            started_utc=started_utc,
            delay=delay,
        )
    except Exception as exc:  # noqa: BLE001 — a probe reports, it does not classify
        return f"REFUSED  {type(exc).__name__}: {str(exc)[:150]}"
    outcome = result.final_outcome
    detail = f" {outcome.payload!r}" if isinstance(outcome, OK) else ""
    return f"ADMITTED final_outcome={type(outcome).__name__}{detail}"


# --- CLAIM (i) — `policy` exact RetryPolicy ------------------------------------------ #

class _ShadowingPolicy(RetryPolicy):
    @property
    def max_attempts(self):  # type: ignore[override]
        return 500


def claim_i_policy_subclass() -> None:
    print("(i)  policy: a RetryPolicy SUBCLASS shadowing max_attempts with a property")
    try:
        hostile = _ShadowingPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)
    except Exception as exc:  # noqa: BLE001
        print(f"     construction of the subclass itself: REFUSED {type(exc).__name__}: "
              f"{str(exc)[:120]}")
        print("     -> the door was never reached; the claim is not tested by this arm")
        print()
        return
    print(f"     at the door: {_run(_PlainAdapter(), policy=hostile)}")
    print()


def claim_i_policy_subclass_after_rebinding_the_name() -> None:
    """**THE ARM THE ORIGINAL CLAIM NEVER FACED.** Does exact-typing survive a REBOUND name?

    ESCAPE 2's leverage is that a caller-supplied object's own code runs inside the package
    and can rewrite the runner's module globals. If `policy`'s exact type were resolved from
    a module global AT CALL TIME, rebinding it would defeat the claim. `@admits` compiles its
    declarations at DECORATION time, so this arm measures whether that difference is real.
    """
    print("(i') policy: is the exact type resolved at CALL time or at DECORATION time?")
    print("     THE DISCRIMINATOR: rebind runner.RetryPolicy to an unrelated class and pass")
    print("     a GENUINE RetryPolicy. Call-time resolution would now REFUSE the genuine one.")
    original = runner_module.RetryPolicy

    class _NotAPolicy:
        pass

    genuine = RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)
    try:
        runner_module.RetryPolicy = _NotAPolicy
        print(f"     runner.RetryPolicy is now : {runner_module.RetryPolicy.__name__}")
        print(f"     a GENUINE RetryPolicy at the door: "
              f"{_run(_PlainAdapter(), policy=genuine)}")
        print(f"     a _NotAPolicy at the door        : "
              f"{_run(_PlainAdapter(), policy=_NotAPolicy())}")
    finally:
        runner_module.RetryPolicy = original
    print()


# --- CLAIM (ii) — `started_utc` exact datetime -------------------------------------- #

def claim_ii_started_utc() -> None:
    print("(ii) started_utc: a datetime SUBCLASS, and a naive datetime")

    class _Sub(datetime):
        pass

    sub = _Sub(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
    print(f"     datetime subclass : {_run(_PlainAdapter(), started_utc=sub)}")
    naive = datetime(2026, 8, 22, 12, 0)
    print(f"     naive datetime    : {_run(_PlainAdapter(), started_utc=naive)}")
    old = datetime(2016, 1, 1, tzinfo=timezone.utc)
    print(f"     an instant from 2016 (TYPE exact, VALUE untrue): "
          f"{_run(_PlainAdapter(), started_utc=old)}")
    print()


# --- CLAIM (iii) — `delay` exact DelayKind ------------------------------------------ #

def claim_iii_delay() -> None:
    print("(iii) delay: a look-alike carrying the same .value")

    @dataclass(frozen=True)
    class _FakeDelay:
        value = "wall_clock"
        name = "WALL_CLOCK"

    print(f"     look-alike        : {_run(_PlainAdapter(), delay=_FakeDelay())}")
    print(f"     the enum's .value : {_run(_PlainAdapter(), delay=DelayKind.WALL_CLOCK.value)}")
    print()


# --- CLAIM (iv) AND THE FetchedResponse DOOR ---------------------------------------- #

class _LookAlikeResponse:
    """Not a FetchedResponse. `payload` is a PROPERTY — the adapter's code, read as data."""

    def __init__(self) -> None:
        self.source_as_of_utc = NOW
        self.reads = 0

    @property
    def payload(self):
        self.reads += 1
        return {"reading": 0.25}


class _RebindingAdapter:
    """Rewrites the runner's module globals from inside a call the runner made to it.

    IMPORTS NOTHING FROM `crash_detector`. It reaches the module through the frame stack it
    is standing in — which is what BEING CALLED BY THE RUNNER gives it.
    """

    source_id = "src.probe.e1"
    adapter_id = "probe-e1.rebind"
    response_schema = SCHEMA

    def __init__(self) -> None:
        self.reached = "<not reached>"
        self.rebound = False
        self.look_alike = _LookAlikeResponse()

    def fetch(self, *, timeout_seconds: float):
        frame = sys._getframe(1)
        while frame is not None:
            module_globals = frame.f_globals
            if module_globals.get("__name__") == "crash_detector.collectors.runner":
                self.reached = module_globals["__name__"]
                module_globals["FetchedResponse"] = type(self.look_alike)
                self.rebound = module_globals["FetchedResponse"] is type(self.look_alike)
                break
            frame = frame.f_back
        return self.look_alike

    def is_empty(self, payload: object) -> bool:
        return False


def claim_iv_and_the_fetchedresponse_door() -> None:
    print("(iv) the FetchedResponse door + 'every value the four Protocols RETURN "
          "exact-typed at its point of return'")
    original = runner_module.FetchedResponse
    adapter = _RebindingAdapter()
    try:
        outcome = _run(adapter)
    finally:
        runner_module.FetchedResponse = original
    print(f"     reached module globals of : {adapter.reached}")
    print(f"     runner.FetchedResponse rebound: {adapter.rebound}")
    print(f"     at the door               : {outcome}")
    print(f"     times the payload PROPERTY was read by package code: "
          f"{adapter.look_alike.reads}")
    print("     (each read is the adapter's own code running inside the runner, and each "
          "may answer differently)")
    print()


def main() -> int:
    print("PROBE E1 — RE-MEASURING 'WHAT IS CLOSED AT THAT DOOR AND IS NOT A LIMIT'")
    print(f"tree: {Path(__file__).resolve().parents[2]}")
    print("NO VERDICT IS PRINTED. READ THE DATA LINES.")
    print()
    claim_i_policy_subclass()
    claim_i_policy_subclass_after_rebinding_the_name()
    claim_ii_started_utc()
    claim_iii_delay()
    claim_iv_and_the_fetchedresponse_door()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
