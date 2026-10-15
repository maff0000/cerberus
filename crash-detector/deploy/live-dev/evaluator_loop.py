#!/usr/bin/env python3
"""CERBERUS WO-1.3a — the DEV evaluator loop: the WO-1.3a evaluator pass, on a timer, in a container.

The deliberate twin of ``collector_loop.py``: same ``threading.Event``, same per-pass
``try``/``except``, same two signal handlers, same single ``stop.wait(interval)``. Where
this file differs from that one it is because the WORK differs, and each of those places
says so below. Nothing here is a second design.

Each pass calls :func:`evaluator.pass_once.one_pass_for_both_dials`, which appends one
``machine_state_history`` row per dial (spec §9 item 2). Failures are logged and the loop
continues: an evaluator pass failing must not kill the loop any more than a collector fetch
failing does — a pass that cannot read the raw store is a gap in the history, which the
history's own ``as_of`` column makes visible, not a reason for the dials to stop being
evaluated for ever. SIGTERM ends the loop between passes.

THE TWO STORES ARE NOT THE SAME KIND OF THING, AND THIS PROCESS HOLDS THEM DIFFERENTLY.

The raw store is passed down as a PATH and never opened here: ``pass_once._raw_reader`` is
the only expression in the product that opens it for this process, and it opens it
``read_only=True``. There is deliberately no ``SqliteStore`` import in this file, so there
is no handle in this process through which the collector's data could be written — the
discipline is structural, exactly as that module's docstring describes it.

The history store IS opened here, in WRITE mode, because this is the one process that
writes it (spec §11). It is opened per pass and closed per pass, mirroring the collector's
``with SqliteStore(db_path) as store``: the handle is held for exactly as long as the pass
takes, so a wedged pass cannot sit on the WAL between ticks, and the store's
idempotent schema-on-write-open is re-asserted every pass rather than once at boot.

ONE PASS A DAY, BECAUSE A READING IS A DAY — AND WHAT THAT STILL DOES NOT GUARANTEE.

``CD_EVALUATE_INTERVAL_SECONDS`` defaults to **86400** and the deployed service sets 86400.
It read 300 until WO-1.3e, and R2D2's WO-1.3b finding B1 is what that cost: DECISION-RULE.md
§4 designs this instrument around readings "computed daily" and counts persistence in
READINGS, so at a 300-second pass ``PROVISIONAL_PERSISTENCE`` was ~15 minutes rather than
3 days and ``BREADTH_LOOKBACK_ROWS`` reached back ~100 minutes rather than ~20 days. R2D2
observed the dials flapping live for exactly that reason. The fix is HERE, at the cadence,
and not in the state machine: ``MachineStateHistoryStore``'s invariant that one row is one
reading stays simple and TRUE, and no reading has to be classified as one that "does not
count".

**A PLAIN INTERVAL FROM PROCESS START, NOT AN ALIGNMENT TO A UTC HOUR. ROGUE'S CALL, AND
THE LIMIT IS DISCLOSED RATHER THAN ARGUED AWAY.** ``stop.wait(86400)`` means the daily pass
happens at whatever time of day this container last started, plus the few seconds each pass
takes. Three things decided it:

* **Drift from the interval itself is immaterial.** The slip is one pass's duration per day —
  seconds — against a 3-12 month-horizon instrument whose inputs are daily closes.
* **Alignment does not fix the thing that actually perturbs this cadence.** The loop's first
  act is a PASS, so every restart — redeploy, host reboot — writes a reading immediately,
  whatever grid the waits are on. Pinning the hour would make the steady-state readings land
  at the same moment each day; it would not stop a container restarted three times in an
  afternoon from writing three "daily" readings. **THAT RESIDUAL IS REAL AND IS THIS FILE'S
  KNOWN LIMIT**: curing it needs either a store-side "one row per UTC day" guard or a
  suppressed pass at startup, both of which are the day-bucketing this round deliberately
  did NOT retrofit. Recorded for Trinity and the PO, not quietly absorbed.
* **WHICH hour is doctrine, and doctrine is not mine to place.** An aligned pass would have
  to be aligned to something — after the US close, after FRED's publish lag — and picking
  that is a Product Owner decision about when a day's inputs are in. An arbitrary hour
  chosen here would read as a calibrated one later, which is the mistake this product keeps
  writing ``PROVISIONAL`` on numbers to avoid.

Import route: ``PYTHONPATH=/app/src:/app`` — the image's own (see the Dockerfile's ENV).
"""

from __future__ import annotations

import os
import signal
import sys
import threading
from datetime import datetime, timezone

from evaluator.history_store import MachineStateHistoryStore
from evaluator.pass_once import one_pass_for_both_dials

stop = threading.Event()


def main() -> int:
    raw_store_path = os.environ.get("CD_DB_PATH")
    if not raw_store_path:
        raise SystemExit("REFUSED: CD_DB_PATH is unset.")
    # A SECOND REFUSAL AND NOT A DEFAULT. The collector refuses an unset CD_DB_PATH rather
    # than inventing a path, for the reason that a default would silently create an empty
    # database somewhere nobody is looking; the state store is the same kind of file and
    # gets the same door. The image sets both (Dockerfile ENV), so neither refusal fires in
    # the container — they fire for a hand-run that forgot one, which is when they matter.
    state_store_path = os.environ.get("CD_STATE_PATH")
    if not state_store_path:
        raise SystemExit("REFUSED: CD_STATE_PATH is unset.")
    # 86400 — ONE PASS A DAY, AND IT IS A UNIT FIX RATHER THAN A TUNING CHANGE (R2D2's
    # WO-1.3b finding B1, remediated in WO-1.3e; the module docstring's own section has the
    # reasoning and the limit this default does NOT cure).
    interval = float(os.environ.get("CD_EVALUATE_INTERVAL_SECONDS", "86400"))
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    print(
        f"cd-evaluator-loop raw={raw_store_path} state={state_store_path} interval={interval}s",
        flush=True,
    )
    while not stop.is_set():
        # ONE CLOCK READ PER PASS, and it is the pass's `now_utc` as well as the log's
        # timestamp. `one_pass_for_both_dials` takes the instant as a parameter (it decides
        # which readings are fresh enough to use), so the loop is the component that owns
        # the clock here; reading it twice would date the log line and the evaluation
        # differently for no gain.
        started = datetime.now(timezone.utc)
        try:
            with MachineStateHistoryStore(state_store_path) as history:
                rows = one_pass_for_both_dials(
                    raw_store_path=raw_store_path,
                    history=history,
                    now_utc=started,
                )
            # THE STATES, SIDE BY SIDE, AND NO NUMBERS. Each dial's own state name and its
            # own persistence counter, printed per dial, with nothing computed across them:
            # no combined score, no "worst of", no count of how many dials are elevated.
            # The returned dict is two rows side by side (pass_once's docstring) and this
            # line keeps it that way — a summary number over both dials is the one thing
            # CD-AC-002 refuses, and a log line is not an exemption from it.
            states = " ".join(
                f"{dial_id}={row.machine_state.name}/{row.persistence_counter}"
                for dial_id, row in rows.items()
            )
            print(f"{started.isoformat()} pass: {states}", flush=True)
        except Exception as failure:  # logged, never swallowed silently; the loop keeps going
            # A pass that raised after the first dial's row was appended leaves that row
            # written, and that is correct: the table is append-only, each row is dated by
            # its own inputs, and a dial that WAS evaluated this pass did get evaluated.
            print(
                f"{started.isoformat()} pass FAILED: {type(failure).__name__}: {failure}",
                file=sys.stderr,
                flush=True,
            )
        stop.wait(interval)
    print("cd-evaluator-loop stopping", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
