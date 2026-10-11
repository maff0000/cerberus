"""Per-indicator ingestion state against the ratified staleness windows.

This is an INGESTION-HEALTH view, not a dial input and not a score. For each of the 30
ratified indicators it says which of these it is, and nothing warmer:

    LIVE       every ingredient has a reading inside the indicator's staleness window
    STALE      a reading exists but is older than the window — NOT shown as a value
    MISSING    an ingredient has never produced a reading
    DERIVED    all ingredients live, but the quantity is derived by the engine, which has no
               computing mapping yet — the indicator has no number of its own
    NOT_TRACTABLE / PARTIAL  see catalog

The window comparison here mirrors the rule, not the engine's regime-tightened windows
(``staleness.py``); the engine remains the only authority on freshness for a dial.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ingestion.catalog import INGREDIENTS, NOT_TRACTABLE, PARTIAL
from ingestion.store import SqliteStore

MAPPING = Path(__file__).resolve().parents[1] / "governance" / "mapping" / "indicator_mapping.yaml"


def indicator_states(store: SqliteStore, now: datetime) -> list[dict]:
    rows = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))["indicators"]
    out = []
    for row in rows:
        ind = row["id"]
        if ind in NOT_TRACTABLE:
            out.append({"id": ind, "state": "NOT_TRACTABLE", "detail": NOT_TRACTABLE[ind]})
            continue
        ings = [i for i in INGREDIENTS if ind in i.serves]
        window = row["staleness_window_seconds"]
        worst, parts = "LIVE", []
        for ing in ings:
            reading = store.latest_reading(ing.source_id)
            if reading is None:
                worst, parts = "MISSING", parts + [f"{ing.source_id}: never read"]
                continue
            as_of = datetime.fromisoformat(reading["source_as_of_utc"].replace("Z", "+00:00"))
            age = (now - as_of).total_seconds()
            if age > window and worst != "MISSING":
                worst = "STALE"
            parts.append(f"{ing.source_id}={reading['payload'].get('value')} as_of={as_of.date()} age={age/86400:.1f}d")
        complete = all(i.completes == "DIRECT" for i in ings)
        state = worst if worst != "LIVE" or complete else "DERIVED"
        if ind in PARTIAL and state in ("LIVE", "DERIVED"):
            state = "PARTIAL"
        out.append({"id": ind, "state": state, "detail": "; ".join(parts)})
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    args = parser.parse_args(argv)
    with SqliteStore(args.db) as store:
        states = indicator_states(store, datetime.now(timezone.utc))
    for s in states:
        print(f"{s['id']:26} {s['state']:14} {s['detail'][:150]}")
    counts: dict = {}
    for s in states:
        counts[s["state"]] = counts.get(s["state"], 0) + 1
    print("-- " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
