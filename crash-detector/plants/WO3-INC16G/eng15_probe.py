"""CD-ENG-WO3-15's OWN live-gate probe. Takes the tree as argv[1].

*** WHY A SECOND PROBE AND NOT `plants/WO3-INC16F/eng14_probe.py`. *** That probe is sound and
this seat ran it; it simply cannot see these arms. It builds every document with
``config_snapshot_id = "SYNTHETIC-ENG14-PROBE-NOT-A-CONFIG"`` and every dial with
``score = 0.01``, and the two arms measured here trigger on ``config_snapshot_id == "BYPASS"``
(`Z5`) and ``score == 0.1234`` (`Z7`). **A PROBE THAT DOES NOT CARRY THE TRIGGER MEASURES A
DOCUMENT THE ARM DECLINED TO ATTACK, AND WOULD REPORT ZERO ADMISSIONS ON A LIVE BYPASS.** That
is the same class as `CD-ASR-WO3-11`'s unpatched tree: a green obtained by not looking.

Nothing here is hard-coded to a path: ``sys.path.insert(0, argv[1] + "/src")`` and the last line
prints the resolved ``crash_detector.__file__`` so a reader can see WHICH TREE produced the
table (`CD-PL-F98`).

Every row prints its EXPECTATION beside its OUTCOME. The last-but-one line counts STALE-CALM
ADMISSIONS — a MUST-REFUSE row the gate ADMITTED — and counts MUST-ADMIT refusals SEPARATELY,
because a refused baseline means the refusals below are attributable to the document skeleton
and not to the arm (`CD-PL-F74`).
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

SID = "SYNTHETIC-ENG15-PROBE-NOT-A-SOURCE"
PUB = "2026-08-24T18:00:00Z"
FRESH = "2026-08-24T17:59:30Z"
ANCIENT = "1970-01-01T00:00:00Z"

#: `Z5`'s trigger, read from the ROOT by the swallowing handler.
Z5_TRIGGER = "BYPASS"
#: `Z7`'s trigger, read from the NODE by the starved shared walk.
Z7_TRIGGER = 0.1234


def dial(stamp, level="calm", score=0.01):
    return {
        "state": "VALUE",
        "score": score,
        "as_of_utc": stamp,
        "inputs_used": [SID],
        "contributions": [],
        "detail_level": level,
    }


def env(slot_stamp, level="calm", slot="equity_crash", config="SYNTHETIC-ENG15-NOT-A-CONFIG",
        score=0.01):
    doc = {
        "schema_version": "1.1.0",
        "as_of_utc": FRESH,
        "published_utc": PUB,
        "regime": "normal",
        "staleness_window_seconds": 600.0,
        "inputs_used": [SID],
        "degraded_inputs": [],
        "config_snapshot_id": config,
        "equity_crash": dial(FRESH, "calm"),
        "monetary_debasement": dial(FRESH, "calm"),
    }
    doc[slot] = dial(slot_stamp, level, score)
    return doc


R = "MUST REFUSE"
A = "MUST ADMIT"

ROWS = [
    # ---- the baselines. If any of these is REFUSED, nothing below is attributable. ----
    ("BASELINE-ALL-FRESH-CALM              ", A, env(FRESH)),
    ("BASELINE-FRESH-CALM+Z5-TRIGGER       ", A, env(FRESH, config=Z5_TRIGGER)),
    ("BASELINE-FRESH-CALM+Z7-TRIGGER       ", A, env(FRESH, score=Z7_TRIGGER)),
    ("BASELINE-ANCIENT-ELEVATED            ", A, env(ANCIENT, level="elevated")),
    # ---- the control: a stale calm dial carrying NEITHER trigger. Caught on every arm. ----
    ("STALE-CALM-NO-TRIGGER                ", R, env(ANCIENT)),
    # ---- the two arms' own documents. ORDINARY documents both contracts admit. ----
    ("STALE-CALM+Z5-TRIGGER-config=BYPASS  ", R, env(ANCIENT, config=Z5_TRIGGER)),
    ("STALE-CALM+Z7-TRIGGER-score=0.1234   ", R, env(ANCIENT, score=Z7_TRIGGER)),
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
    print("%-37s %-11s PUBLIC=%-42s PRIVATE=%s" % (name, expect, outs[0], outs[1]))

print("ROWS=%d  MUST-ADMIT ROWS REFUSED=%d  STALE-CALM ADMISSIONS=%d"
      % (len(ROWS) * 2, baseline_refusals, admissions))
print("TREE:", TREE, "|", crash_detector.__file__)
