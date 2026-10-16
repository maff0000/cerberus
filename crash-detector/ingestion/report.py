"""Per-indicator ingestion state against the ratified staleness windows.

This is an INGESTION-HEALTH view, not a dial input and not a score. For each of the 30
ratified indicators it says which of these it is, and nothing warmer:

    LIVE       every ingredient has a reading inside the indicator's staleness window
    FEED_FAILING the latest fetch attempt of an ingredient was not OK, whatever the age of
               the last good reading
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

from ingestion import release_calendar
from ingestion.catalog import INGREDIENTS, NOT_TRACTABLE, PARTIAL, QUORUM, window_seconds
from ingestion.store import SqliteStore

MAPPING = Path(__file__).resolve().parents[1] / "governance" / "mapping" / "indicator_mapping.yaml"

#: The two quarterly rows whose relevance window is DERIVED from real measured release lag in
#: ``ingestion.release_calendar`` instead of being looked up from the ratified figure. Both
#: constants reproduce their ratified windows EXACTLY (18,144,000 s and 12,960,000 s, neither
#: row carrying an override), so reading them here resolves the SAME number this module already
#: resolved — what changes is only that the number is now traceable to the measured evidence it
#: came from rather than read off a flat figure. One constant per row and no as_of-date logic is
#: the whole model: LIVE/STALE is binary here and the engine holds no intermediate state for a
#: phase-aware window to populate, which that module's docstring sets out at length.
RELEASE_CALENDAR_WINDOWS: dict[str, float] = {
    "buffett_indicator": float(release_calendar.BUFFETT_INDICATOR_RELEVANCE_SECONDS),
    "sloos_bank_lending": float(release_calendar.SLOOS_BANK_LENDING_RELEVANCE_SECONDS),
}


def indicator_states(store: SqliteStore, now: datetime) -> list[dict]:
    rows = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))["indicators"]
    out = []
    for row in rows:
        ind = row["id"]
        if ind in NOT_TRACTABLE:
            out.append({"id": ind, "state": "NOT_TRACTABLE", "detail": NOT_TRACTABLE[ind]})
            continue
        ings = [i for i in INGREDIENTS if ind in i.serves]
        if ind in RELEASE_CALENDAR_WINDOWS:
            window = RELEASE_CALENDAR_WINDOWS[ind]
        else:
            window = window_seconds(ind, row["staleness_window_seconds"])
        worst, parts = "LIVE", []
        failing = []
        healthy = 0  # components with a fresh reading whose latest attempt was OK (the QUORUM rows only count these)
        for ing in ings:
            last = store.last_attempt(ing.source_id)
            ok_attempt = last is None or last[1] == "OK"
            if not ok_attempt:
                failing.append(f"{ing.source_id}: last attempt {last[1]} at {last[0].isoformat()}")
            reading = store.latest_reading(ing.source_id)
            if reading is None:
                worst, parts = "MISSING", parts + [f"{ing.source_id}: never read"]
                continue
            as_of = datetime.fromisoformat(reading["source_as_of_utc"].replace("Z", "+00:00"))
            age = (now - as_of).total_seconds()
            if age > window and worst != "MISSING":
                worst = "STALE"
            elif age <= window and ok_attempt:
                healthy += 1
            parts.append(f"{ing.source_id}={reading['payload'].get('value')} as_of={as_of.date()} age={age/86400:.1f}d")
        if ind in QUORUM:
            # WO-1.10: a sample-defined indicator tolerates absent components down to its floor and no further. At or
            # above the floor it is as live as any derived row (the engine still decides whether a number exists);
            # below it, the worst component state speaks.
            if healthy >= QUORUM[ind]:
                out.append({"id": ind, "state": "DERIVED",
                            "detail": f"{healthy}/{len(ings)} components fresh (floor {QUORUM[ind]})"})
                continue
            parts = [f"only {healthy}/{len(ings)} components fresh (floor {QUORUM[ind]})"] + (failing + parts)[:6]
        if failing:
            # Auditor finding 1 (WO-1.2b): a feed whose latest attempt failed must not read
            # LIVE just because its last good reading is still inside the window.
            out.append({"id": ind, "state": "FEED_FAILING", "detail": "; ".join(failing + parts)})
            continue
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
