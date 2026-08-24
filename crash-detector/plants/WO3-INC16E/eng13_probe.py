"""WO-3 INCREMENT 16E — CD-ENG-WO3-13's OWN live-gate probe.

*** IT TAKES THE TREE AS ``argv[1]`` AND THAT IS THE WHOLE POINT. ***

``plants/WO3-INC16D/probe_16d.py`` hard-codes ``sys.path.insert(0,
"/srv/crash-detector-wo3/src")``, so it measures **THE LANE** no matter which tree it is
pointed at. Reusing it on a patched extraction produces a CLEAN result that means NOTHING and
reads like a refutation. ``PROJECT_LEAD_SEAT_06`` hit that and wrote its own probe; this is
this seat's, written for the same reason and not copied from the Engineer's.

    python3 -B plants/WO3-INC16E/eng13_probe.py <tree>

Read-only. It writes nothing, it registers no source (``Q25``, ``CD-PL-F154``) — every id here
is the unmistakable synthetic token below — and it never touches a worktree.

The last line prints the resolved ``crash_detector.__file__``, so a reader can see WHICH TREE
produced the table above it (``CD-PL-F98``: a contrast run against the wrong tree is
indistinguishable from a fix that does nothing).
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

SYNTHETIC_ID = "SYNTHETIC-16E-PROBE-NOT-A-SOURCE"
PUBLISHED = "2026-08-24T18:00:00Z"


def envelope(dial_as_of, window, level="calm"):
    dial = {
        "state": "VALUE",
        "score": 0.1,
        "as_of_utc": dial_as_of,
        "inputs_used": [SYNTHETIC_ID],
        "contributions": [],
        "detail_level": level,
    }
    return {
        "schema_version": "1.1.0",
        "as_of_utc": dial_as_of,
        "published_utc": PUBLISHED,
        "regime": "calm",
        "staleness_window_seconds": window,
        "inputs_used": [SYNTHETIC_ID],
        "degraded_inputs": [],
        "config_snapshot_id": "SYNTHETIC-16E-PROBE-NOT-A-CONFIG",
        "equity_crash": dial,
        "monetary_debasement": dial,
    }


#: *** THE REFUSING AND THE ADMITTING ROWS CARRY EQUAL WEIGHT. *** A stage that refused
#: everything would satisfy PID §3.2 by making the dial incapable of reading calm at all, which
#: is the VACUOUS direction and is the half this project's history says gets missed.
ROWS = [
    ("STALE-1970-CALM      MUST REFUSE", envelope("1970-01-01T00:00:00Z", 600.0)),
    ("FUTURE-2099-CALM     MUST REFUSE", envelope("2099-01-01T00:00:00Z", 600.0)),
    ("BOUNDARY-600s-CALM   MUST ADMIT ", envelope("2026-08-24T17:50:00Z", 600.0)),
    ("BOUNDARY-600s+1us    MUST REFUSE", envelope("2026-08-24T17:49:59.999999Z", 600.0)),
    ("FRESH-CALM           MUST ADMIT ", envelope("2026-08-24T17:59:30Z", 600.0)),
    ("STALE-1970-ELEVATED  MUST ADMIT ", envelope("1970-01-01T00:00:00Z", 600.0, "elevated")),
    ("STALE-1970-ACUTE     MUST ADMIT ", envelope("1970-01-01T00:00:00Z", 600.0, "acute")),
]

for name, doc in ROWS:
    outs = []
    for surface in (EnvelopeSurface.PUBLIC, EnvelopeSurface.PRIVATE):
        cand = dict(doc)
        if surface is EnvelopeSurface.PRIVATE:
            cand["classification"] = "PRIVATE"
        try:
            refuse_unless_publishable(cand, surface=surface)
            outs.append("ADMITTED")
        except PublicationRefused as exc:
            outs.append("REFUSED [%s] at %s" % (exc.reason_class, exc.pointer or "<root>"))
        except Exception as other:  # noqa: BLE001 - reported, never swallowed
            outs.append("ERROR %s: %s" % (type(other).__name__, other))
    print("%-36s PUBLIC=%-42s PRIVATE=%s" % (name, outs[0], outs[1]))

print("TREE:", TREE, "|", crash_detector.__file__)
