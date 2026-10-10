"""Drive the LIVE gate of whatever tree the CWD is. Prints ADMITTED/REFUSED per row per surface.

Imports the EXTRACTION's own src/ and contracts/, never the worktree's.
"""
import os
import sys

root = os.getcwd()
sys.path.insert(0, os.path.join(root, "src"))
os.environ["CD_CONTRACTS_DIR"] = os.path.join(root, "contracts")

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


def drive(name, doc):
    out = []
    for surface in (EnvelopeSurface.PUBLIC, EnvelopeSurface.PRIVATE):
        cand = dict(doc)
        if surface is EnvelopeSurface.PRIVATE:
            cand["classification"] = "PRIVATE"
        try:
            refuse_unless_publishable(cand, surface=surface)
            out.append("ADMITTED")
        except PublicationRefused as exc:
            out.append(f"REFUSED[{exc.reason_class}]@{exc.pointer or '<root>'}")
        except Exception as other:
            out.append(f"CRASH {type(other).__name__}")
    print(f"{name:<46} pub={out[0]:<34} priv={out[1]}")


drive("1970 stamp + calm, window 1", envelope("1970-01-01T00:00:00Z", 1))
drive("2099 stamp (FUTURE) + calm, window 1", envelope("2099-01-01T00:00:00Z", 1))
drive("FRESH stamp + calm, window 1 [MUST ADMIT]", envelope(PUBLISHED, 1))

arm_h = envelope(PUBLISHED, 86400, level="elevated")
arm_h["degraded_inputs"] = [{"source_id": "SRC-A", "detail_level": "calm"}]
drive("ARM H degraded_inputs=[{src,calm}]", arm_h)

arm_h3 = envelope(PUBLISHED, 86400, level="elevated")
arm_h3["degraded_inputs"] = [[{"source_id": "SRC-A", "detail_level": "calm"}]]
drive("ARM H3 degraded_inputs=[[{src,calm}]]", arm_h3)

arm_h2 = envelope(PUBLISHED, 86400, level="elevated")
arm_h2["degraded_inputs"] = [{"source_id": "SRC-A", "detail_level": "calm"}]
drive("ARM H2 (open objects) same document", arm_h2)

unk = envelope(PUBLISHED, 86400, level="elevated")
unk["equity_crash"] = {
    "state": "UNKNOWN", "reason": "none", "since_utc": PUBLISHED,
    "missing_inputs": [], "detail_level": "calm",
}
drive("CTRL UNKNOWN + calm [MUST REFUSE]", unk)
spin = envelope(PUBLISHED, 86400, level="elevated")
spin["equity_crash"] = {"state": "SPINDRIFT", "detail_level": "calm"}
drive("CTRL SPINDRIFT + calm [MUST REFUSE]", spin)
drive("CTRL baseline fresh+elevated [MUST ADMIT]", envelope(PUBLISHED, 600.0, level="elevated"))
