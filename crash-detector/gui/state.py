"""The GUI's view-model (CERBERUS WO-1.4): two dials, never blended, and every indicator's state.

Pure: a store and a clock in, a plain dict out. No HTTP, no HTML, no writes. It lives outside
``src/`` for the same reason ``ingestion/wiring.py`` does.

WHAT THIS IS NOT. It is a DEV live view over the WO-1.3 wiring, not the BLUEPRINT's cd-public
(which "computes nothing; reads one row and renders it" and needs the engine and the Postgres
store, neither deployed). This computes the dials on request from the ingestion store, using
PROVISIONAL, uncalibrated bands. The dict says so in ``provisional`` and the page prints it.

The dial block goes through ``present_dial`` (the surface tier's own sum type), so an Unknown
dial is a ``NotShown`` carrying a reason and no number. There is no key that holds both dials'
numbers together: ``dials`` is a list of two independent entries and nothing here adds them.
"""

from __future__ import annotations

from datetime import datetime

from crash_detector.dials.reading import Degraded, Value
from crash_detector.serving.dial_presentation import Shown, present_dial
from ingestion.report import indicator_states
from ingestion.store import SqliteStore
from ingestion.wiring import DIALS, _rows, build_wiring, observations_from_store
from crash_detector.engine.evaluate import evaluate

__all__ = ["build_state"]

DIAL_TITLES = {
    "equity_crash": "Equity crash",
    "monetary_debasement": "Monetary debasement",
}
PROVISIONAL_NOTICE = (
    "PROVISIONAL. The scaling bands are placeholders (deploy/indicator-scaling.json): "
    "uncalibrated, no backtest run. The numbers below are not probabilities and not advice."
)


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _dial_entry(dial_id: str, reading: object) -> dict:
    shown = present_dial(dial_id, reading)
    entry = {"dial_id": dial_id, "title": DIAL_TITLES[dial_id]}
    if isinstance(shown, Shown):
        entry["status"] = "DEGRADED" if type(reading) is Degraded else "VALUE"
        entry["value"] = shown.magnitude.quantity_for(dial_id)
        entry["as_of_utc"] = _iso(reading.as_of_utc)
        entry["missing_inputs"] = list(reading.missing_inputs) if type(reading) is Degraded else []
        entry["reason"] = reading.reason if type(reading) is Degraded else ""
        entry["inputs_used"] = list(reading.inputs_used) if type(reading) is Value else []
    else:
        entry["status"] = "NO READING"
        entry["value"] = None
        entry["as_of_utc"] = None
        entry["missing_inputs"] = list(shown.missing_inputs)
        entry["reason"] = shown.reason
        entry["inputs_used"] = []
    return entry


def build_state(store: SqliteStore, now_utc: datetime) -> dict:
    wiring = build_wiring()
    observations = observations_from_store(store, wiring, now_utc)
    dialset = evaluate(observations, wiring.snapshot, now_utc)
    dials = [_dial_entry("equity_crash", dialset.equity), _dial_entry("monetary_debasement", dialset.monetary)]

    ingest = {row["id"]: row for row in indicator_states(store, now_utc)}
    scored_in = {
        dial: {m.source_id for m in wiring.snapshot.indicator_mapping_registry.mappings
               if any(b.dial_id == dial for b in m.dial_bindings)}
        for dial in DIALS
    }
    indicators = []
    for row in _rows():
        ind = row["id"]
        info = ingest.get(ind, {"state": "UNKNOWN", "detail": ""})
        live_candidate = ind in wiring.ingredient_for
        entry = {
            "id": ind,
            "name": row["name"],
            "tier": row["tier"],
            "dials": [d for d in DIALS if ind in scored_in[d]] if live_candidate else [],
            "wired": live_candidate,
            "value": None,
            "unit": "",
            "as_of_utc": None,
            "age_days": None,
            "window_days": round(row["staleness_window_seconds"] / 86400, 2),
        }
        if not live_candidate:
            entry["state"] = "PENDING"
            entry["why"] = wiring.pending.get(ind, "not wired")
            entry["ingest_state"] = info["state"]
        else:
            ing = wiring.ingredient_for[ind]
            reading = store.latest_reading(ing.source_id)
            if reading is not None:
                as_of = datetime.fromisoformat(reading["source_as_of_utc"].replace("Z", "+00:00"))
                entry["as_of_utc"] = _iso(as_of)
                entry["age_days"] = round((now_utc - as_of).total_seconds() / 86400, 2)
                entry["unit"] = str(reading["payload"].get("unit", ""))
            entry["state"] = info["state"]
            entry["why"] = "" if info["state"] == "LIVE" else info["detail"]
            # A number is shown only for a LIVE indicator: a stale or failing one is not shown as a value.
            if info["state"] == "LIVE" and reading is not None:
                entry["value"] = reading["payload"].get("value")
        indicators.append(entry)

    counts: dict = {}
    for entry in indicators:
        counts[entry["state"]] = counts.get(entry["state"], 0) + 1
    return {
        "generated_utc": _iso(now_utc),
        "provisional": PROVISIONAL_NOTICE,
        "dials": dials,
        "indicators": indicators,
        "counts": counts,
    }
