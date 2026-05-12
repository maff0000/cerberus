#!/usr/bin/env python3
"""WO-FALCON-ENRICHED-HANDLER-CONTROL-TRUTH-0001 (P2B) — cron-driven detector.

Architect-locked READ-ONLY split-brain monitor for the falcon_enriched_signal
handler. Runs as a Helm-side cron tool against the audited system.

Reads:
  - falcon:signal:enriched:handler:state                (audit/visibility key)
  - fabric:mirror:manifest                              (runtime gate)
  - falcon:signal:enriched:handler:control_truth_config  (grace_window_seconds)
  - last cycle timestamp via journalctl -u fabric-mirror.service (read-only)

Writes (only on RED detection):
  - falcon:signal:enriched:handler:fault:<date_utc>
  - r2d2:audit:falcon_enriched_handler:fault:<date_utc>

Exit code:
  0  OK (no split-brain)
  1  RED (split-brain detected — fault emitted to 3 sinks)
  2  fail-loud (config missing OR detector itself errored)

Schedule (proposed cron):
  * * * * * /usr/bin/python3 /srv/r2d2/tools/falcon_enriched_split_brain_detector.py >> /srv/NEO/logs/p2b_split_brain_detector.log 2>&1

NOT installed by P2B branch — see deployment_runbook in the WO evidence pack.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Allow importing the library from /srv/fabric-mirror
FABRIC_MIRROR_PATH = os.environ.get("FABRIC_MIRROR_PATH", "/srv/fabric-mirror")
if FABRIC_MIRROR_PATH not in sys.path:
    sys.path.insert(0, FABRIC_MIRROR_PATH)

from falcon_enriched import handler_control as hc

FABRIC_API = os.environ.get("FABRIC_API", "http://127.0.0.1:8080/api/v1/redis")
HANDLER_NAME = os.environ.get(
    "FALCON_ENRICHED_HANDLER_NAME", "falcon_enriched_signal_XAU_USD"
)
JOURNAL_LOOKBACK_MINUTES = int(
    os.environ.get("P2B_JOURNAL_LOOKBACK_MINUTES", "30")
)

logger = logging.getLogger("p2b_split_brain_detector")


def fabric_get(key):
    try:
        r = urllib.request.urlopen(f"{FABRIC_API}/get/{key}", timeout=5)
        data = json.loads(r.read())
        v = data.get("value")
        return json.loads(v) if v else None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fabric_set(key, value):
    body = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(
        f"{FABRIC_API}/set", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    urllib.request.urlopen(req, timeout=10).read()


JOURNAL_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z?.*"
    r"INFO cycle name=(?P<name>[A-Za-z0-9_]+).*state="
)


def find_last_handler_cycle_ts_utc(handler_name: str,
                                    lookback_minutes: int = JOURNAL_LOOKBACK_MINUTES):
    """Return the ISO-8601 UTC timestamp of the most recent handler PROCESSING
    cycle, or None if unavailable.

    WO-FABRIC-MIRROR-DECONTENTION-0001 (Phase B): the falcon_enriched handler is
    being split out of the shared fabric-mirror loop into a dedicated
    falcon-enriched.service. The RED_B "no cycles after grace" check therefore can
    no longer rely on `journalctl -u fabric-mirror.service`; it now sources the
    last-PROCESS timestamp from the fabric heartbeat key written by whichever
    process runs the cycle:

        fabric:mirror:health:<handler_name>.last_process_at_utc

    `last_process_at_utc` is updated ONLY when the cycle actually executes (the new
    standalone service carries it forward across disabled skip-loops), so it is the
    correct RED_B input — distinct from `last_loop_at_utc`, which ticks every loop
    even while disabled. `last_loop_at_utc` is logged here for diagnostic context.

    Backwards-compatible: if the heartbeat key still carries the legacy fabric-mirror
    schema (`last_cycle_at_utc`, no `last_process_at_utc`), that value is used as a
    fallback. If neither is present, returns None and RED_B stays conservative.

    Scope of this WO's detector change is THIS FUNCTION ONLY — RED_A/RED_B/RED_C
    constants, detect_split_brain, emit_split_brain_fault, the 3-sink fanout,
    read_canonical_handler_state and the exit codes are unchanged.

    `lookback_minutes` is retained for signature compatibility but is no longer used
    (the heartbeat key is a point-in-time value, not a journal window).
    """
    health_key = f"fabric:mirror:health:{handler_name}"
    health = fabric_get(health_key)
    if not isinstance(health, dict):
        logger.warning("health key %s missing/not-a-dict — RED_B conservative", health_key)
        return None
    last_loop = health.get("last_loop_at_utc")
    if last_loop:
        logger.info("health %s last_loop_at_utc=%s state=%s",
                    health_key, last_loop, health.get("state"))
    last_process = health.get("last_process_at_utc")
    if last_process is None:
        # Legacy fabric-mirror schema fallback (write_health wrote last_cycle_at_utc).
        last_process = health.get("last_cycle_at_utc")
    return last_process if last_process else None


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s p2b_split_brain_detector: %(message)s",
    )

    # Step 1 — load config (fail loud on missing)
    try:
        cfg = hc.load_control_truth_config(fabric_get)
    except hc.ControlTruthConfigMissing as e:
        det = hc.SplitBrainDetection(
            code=hc.DETECTION_FAILED_CONFIG_MISSING,
            is_red=True,
            handler_name=HANDLER_NAME,
            captured_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            canonical={"config_missing": True},
            grace_window_seconds=None,
            last_cycle_seen_at_utc=None,
            seconds_since_last_cycle=None,
            seconds_since_state_enabled_at_utc=None,
            detail=f"control_truth_config missing: {e}",
            fault_code="FAILED_CONFIG_MISSING",
        )
        emit = hc.emit_split_brain_fault(det, fabric_get=fabric_get, fabric_set=fabric_set)
        print(json.dumps({"detection": det.__dict__, "emit": emit}, default=str))
        return 2
    except Exception as e:
        logger.exception("config load failed unexpectedly: %s", e)
        return 2

    grace = int(cfg["split_brain_grace_window_seconds"])

    # Step 2 — read canonical state + last cycle timestamp
    try:
        canonical = hc.read_canonical_handler_state(fabric_get, HANDLER_NAME)
    except Exception as e:
        logger.exception("canonical state read failed: %s", e)
        return 2

    last_cycle = find_last_handler_cycle_ts_utc(HANDLER_NAME)

    # Step 3 — detect
    now_utc = datetime.now(timezone.utc)
    detection = hc.detect_split_brain(
        canonical,
        last_cycle_seen_at_utc=last_cycle,
        grace_window_seconds=grace,
        now_utc=now_utc,
    )

    # Step 4 — emit if RED
    emit_record = None
    if detection.is_red:
        emit_record = hc.emit_split_brain_fault(
            detection, fabric_get=fabric_get, fabric_set=fabric_set, now_utc=now_utc,
        )

    summary = {
        "wo": hc.WO,
        "writer_version": hc.WRITER_VERSION,
        "ran_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "config_grace_window_seconds": grace,
        "last_cycle_seen_at_utc": last_cycle,
        "code": detection.code,
        "is_red": detection.is_red,
        "detail": detection.detail,
        "canonical": detection.canonical,
        "emit_record": emit_record,
    }
    print(json.dumps(summary, default=str))
    return 1 if detection.is_red else 0


if __name__ == "__main__":
    sys.exit(main())
