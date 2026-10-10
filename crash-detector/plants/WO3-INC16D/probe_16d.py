"""CD-ENG-WO3-12 own-shell A311-F2 / A311-F1 probe. READ-ONLY against the live gate.

Drives ``refuse_unless_publishable`` at /srv/crash-detector-wo3 on BOTH surfaces.
The private contract requires ``classification`` const ``PRIVATE`` and the public
contract declares no such property at all, so the surface key is added per-surface
and one fixture never serves both.

Nothing here writes into the lane. It prints one line per (row, surface).
"""
import sys

sys.path.insert(0, "/srv/crash-detector-wo3/src")

from crash_detector.publication.envelope_contract import (  # noqa: E402
    EnvelopeSurface,
    PublicationRefused,
    refuse_unless_publishable,
)

PUBLISHED = "2026-08-24T18:00:00Z"


def envelope(dial_as_of, window, level="calm"):
    dial = {
        "state": "VALUE",
        "score": 0.1,
        "as_of_utc": dial_as_of,
        "inputs_used": ["SRC-A"],
        "contributions": [],
        "detail_level": level,
    }
    return {
        "schema_version": "1.1.0",
        "as_of_utc": dial_as_of,
        "published_utc": PUBLISHED,
        "regime": "calm",
        "staleness_window_seconds": window,
        "inputs_used": ["SRC-A"],
        "degraded_inputs": [],
        "config_snapshot_id": "CFG-1",
        "equity_crash": dial,
        "monetary_debasement": dial,
    }


RESULTS = []


def drive(name, doc):
    row = [name]
    for surface in (EnvelopeSurface.PUBLIC, EnvelopeSurface.PRIVATE):
        cand = dict(doc)
        if surface is EnvelopeSurface.PRIVATE:
            cand["classification"] = "PRIVATE"
        try:
            refuse_unless_publishable(cand, surface=surface)
            outcome = "ADMITTED"
        except PublicationRefused as exc:
            outcome = f"REFUSED [{exc.reason_class}] at {exc.pointer or '<root>'}"
        except Exception as other:  # neither an admission nor a declared refusal
            outcome = f"CRASH {type(other).__name__}"
        row.append(outcome)
        print(f"  {name:<54} {surface.value:<8} {outcome}")
    RESULTS.append(row)


print("=== A311-F2 GRADED ROWS — the VALUE dial whose stamp value was never read ===")
drive("F2-a 1970 stamp, window 1", envelope("1970-01-01T00:00:00Z", 1))
drive("F2-b 1970 stamp, window 86400", envelope("1970-01-01T00:00:00Z", 86400))
drive("F2-c 2099 stamp (FUTURE), window 1", envelope("2099-01-01T00:00:00Z", 1))
drive("F2-d fresh stamp (== published), window 1  [MUST STAY ADMITTED]",
      envelope(PUBLISHED, 1))

print()
print("=== EXTRA FRESHNESS ROWS (this seat's own, not dispatched) ===")
drive("F2-e stamp 1s before published, window 1 (age==window, boundary)",
      envelope("2026-08-24T17:59:59Z", 1))
drive("F2-f stamp 2s before published, window 1 (age>window)",
      envelope("2026-08-24T17:59:58Z", 1))
drive("F2-g fresh stamp, window 86400 [MUST STAY ADMITTED]",
      envelope("2026-08-24T17:00:00Z", 86400))
drive("F2-h 1970 stamp but detail_level ELEVATED [MUST STAY ADMITTED]",
      envelope("1970-01-01T00:00:00Z", 1, level="elevated"))

print()
print("=== A311-F1 — root degraded_inputs one container deeper ===")
deep = envelope(PUBLISHED, 86400)
deep["degraded_inputs"] = [{"source_id": "SRC-A", "detail_level": "calm"}]
drive("F1 degraded_inputs=[{source_id,detail_level:calm}]", deep)
flat = envelope(PUBLISHED, 86400)
flat["degraded_inputs"] = {"source_id": "SRC-A", "detail_level": "calm"}
drive("F1 degraded_inputs={source_id,detail_level:calm}", flat)

print()
print("=== CONTROLS — Rule CC's closure. MUST STAY REFUSED x2, UNMOVED ===")
unk = envelope(PUBLISHED, 86400)
unk["equity_crash"] = {
    "state": "UNKNOWN",
    "reason": "no source registered",
    "since_utc": PUBLISHED,
    "missing_inputs": [],
    "detail_level": "calm",
}
drive("CTRL UNKNOWN dial + calm", unk)
deg = envelope(PUBLISHED, 86400)
deg["equity_crash"] = {
    "state": "DEGRADED",
    "score": 0.1,
    "as_of_utc": PUBLISHED,
    "missing_inputs": ["SRC-B"],
    "reason": "input missing",
    "contributions": [],
    "detail_level": "calm",
}
drive("CTRL DEGRADED dial + calm", deg)
spin = envelope(PUBLISHED, 86400)
spin["equity_crash"] = {"state": "SPINDRIFT", "detail_level": "calm"}
drive("CTRL never-before-named state SPINDRIFT + calm", spin)
nost = envelope(PUBLISHED, 86400)
nost["equity_crash"] = {"detail_level": "calm"}
drive("CTRL no-state dial + calm", nost)

print()
print("=== BASELINE CONTROL — the wholly conforming envelope MUST BE ADMITTED ===")
drive("CTRL baseline VALUE dial, fresh, elevated, window 600",
      envelope(PUBLISHED, 600.0, level="elevated"))
