"""CD-ENG-WO3-14's OWN live-gate probe. Takes the tree as argv[1].

Twenty-four rows: twelve document shapes x two surfaces. Nothing here is hard-coded to a
path: `sys.path.insert(0, argv[1] + "/src")` and the last line prints the resolved
`crash_detector.__file__` so a reader can see WHICH TREE produced the table (CD-PL-F98).

Every row prints its EXPECTATION beside its OUTCOME, and the last-but-one line counts
STALE-CALM ADMISSIONS: a MUST-REFUSE row the gate ADMITTED. Baseline refusals are counted
separately, because a refused baseline means every refusal below is attributable to the
document skeleton and not to the stamp under test (CD-PL-F74).
"""

import sys

TREE = sys.argv[1]
sys.path.insert(0, TREE + "/src")

import crash_detector  # noqa: E402
from crash_detector.publication.envelope_contract import (  # noqa: E402
    EnvelopeSurface,
    PublicationRefused,
    refuse_unless_publishable,
)

SID = "SYNTHETIC-ENG14-PROBE-NOT-A-SOURCE"
SID2 = "SYNTHETIC-ENG14-PROBE-NOT-A-SOURCE-2"
PUB = "2026-08-24T18:00:00Z"
FRESH = "2026-08-24T17:59:30Z"
EDGE = "2026-08-24T17:50:00Z"
PAST = "2026-08-24T17:49:59.999999Z"
ANCIENT = "1970-01-01T00:00:00Z"
FUTURE = "2099-01-01T00:00:00Z"


def dial(stamp, level="calm", inputs=None):
    return {
        "state": "VALUE",
        "score": 0.01,
        "as_of_utc": stamp,
        "inputs_used": list(inputs or [SID]),
        "contributions": [],
        "detail_level": level,
    }


def env(slot_stamp, level="calm", slot="equity_crash", window=600.0,
        regime="normal", inputs=None):
    doc = {
        "schema_version": "1.1.0",
        "as_of_utc": FRESH,
        "published_utc": PUB,
        "regime": regime,
        "staleness_window_seconds": window,
        "inputs_used": list(inputs or [SID]),
        "degraded_inputs": [],
        "config_snapshot_id": "SYNTHETIC-ENG14-PROBE-NOT-A-CONFIG",
        "equity_crash": dial(FRESH, "calm", inputs),
        "monetary_debasement": dial(FRESH, "calm", inputs),
    }
    doc[slot] = dial(slot_stamp, level, inputs)
    return doc


R = "MUST REFUSE"
A = "MUST ADMIT"

ROWS = [
    ("BASELINE-ALL-FRESH-CALM             ", A, env(FRESH)),
    ("EQUITY-ANCIENT-CALM                 ", R, env(ANCIENT)),
    ("EQUITY-FUTURE-CALM                  ", R, env(FUTURE)),
    ("EQUITY-ONE-MICROSECOND-PAST         ", R, env(PAST)),
    ("EQUITY-EXACTLY-THE-WINDOW           ", A, env(EDGE)),
    ("MONETARY-ANCIENT-CALM               ", R, env(ANCIENT, slot="monetary_debasement")),
    ("MONETARY-FUTURE-CALM                ", R, env(FUTURE, slot="monetary_debasement")),
    ("EQUITY-ANCIENT-ELEVATED             ", A, env(ANCIENT, level="elevated")),
    ("EQUITY-ANCIENT-ACUTE                ", A, env(ANCIENT, level="acute")),
    # The two shapes A313-F1 names. Both are ORDINARY admissible documents.
    ("EQUITY-ANCIENT-CALM+regime=calm     ", R, env(ANCIENT, regime="calm")),
    ("EQUITY-ANCIENT-CALM+2-INPUTS        ", R, env(ANCIENT, inputs=[SID, SID2])),
    ("EQUITY-FUTURE-CALM+2-INPUTS         ", R, env(FUTURE, inputs=[SID, SID2])),
]

admissions = 0
baseline_refusals = 0
for name, expect, doc in ROWS:
    outs = []
    for surface in (EnvelopeSurface.PUBLIC, EnvelopeSurface.PRIVATE):
        cand = dict(doc)
        if surface is EnvelopeSurface.PRIVATE:
            cand["classification"] = "PRIVATE"
        try:
            refuse_unless_publishable(cand, surface=surface)
            outs.append("ADMITTED")
            if expect == R:
                admissions += 1
        except PublicationRefused as exc:
            outs.append("REFUSED [%s] at %s" % (exc.reason_class, exc.pointer or "<root>"))
            if expect == A:
                baseline_refusals += 1
        except Exception as other:  # noqa: BLE001
            outs.append("ERROR %s: %s" % (type(other).__name__, other))
            if expect == A:
                baseline_refusals += 1
    print("%-36s %-11s PUBLIC=%-40s PRIVATE=%s" % (name, expect, outs[0], outs[1]))

print("ROWS=%d  MUST-ADMIT ROWS REFUSED=%d  STALE-CALM ADMISSIONS=%d"
      % (len(ROWS) * 2, baseline_refusals, admissions))
print("TREE:", TREE, "|", crash_detector.__file__)
