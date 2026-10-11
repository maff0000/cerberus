#!/usr/bin/env python3
"""CERBERUS WO-1.4 — the DEV collector loop: the WO-1.2b ingestion runner, on a timer, in a container.

Each pass calls ``ingestion.run.run_once`` (per-source poll intervals and the 15-minute failure
retry are the runner's own, so a pass that finds nothing due is cheap). Failures are logged and the
loop continues: a feed outage must show up in the GUI as FEED_FAILING / STALE, not as a dead
collector. SIGTERM ends the loop between passes.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
from datetime import datetime, timezone

from ingestion.run import run_once
from ingestion.store import SqliteStore

stop = threading.Event()


def main() -> int:
    db_path = os.environ.get("CD_DB_PATH")
    if not db_path:
        raise SystemExit("REFUSED: CD_DB_PATH is unset.")
    interval = float(os.environ.get("CD_COLLECT_INTERVAL_SECONDS", "300"))
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    print(f"cd-collector-loop db={db_path} interval={interval}s", flush=True)
    while not stop.is_set():
        started = datetime.now(timezone.utc).isoformat()
        try:
            with SqliteStore(db_path) as store:
                summary = run_once(store)
            due = [r for r in summary if r["state"] != "NOT_DUE"]
            bad = [r["source_id"] + ":" + r["state"] for r in due if r["state"] != "OK"]
            print(f"{started} pass: {len(summary)} sources, {len(due)} fetched, not-OK={bad}", flush=True)
        except Exception as failure:  # logged, never swallowed silently; the loop keeps going
            print(f"{started} pass FAILED: {type(failure).__name__}: {failure}", file=sys.stderr, flush=True)
        stop.wait(interval)
    print("cd-collector-loop stopping", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
