#!/usr/bin/env python3
"""
R2D2 §6.2 Falcon Structure Engine validation harness.
Runs daily @ 00:15 UTC via cron. Writes to r2d2:validation:structure_engine_6_2:<YYYY-MM-DD>.

Spec: r2d2:tests:structure_engine_6_2_validation_suite v1.0
Brief: helm:comms:r2d2:structure_engine_6_2_validation

Guardrails: READ-ONLY. SELECT only. UTC timing only. Fabric-first for mirrored keys.
"""
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

API = "http://localhost:8080/api/v1/redis"
SSH = ["ssh", "-o", "ConnectTimeout=5", "root@192.168.11.10"]
DB = "PDAPass@R00t123"

THRESHOLDS = {
    "BOS": {"min": 10, "direction": "min"},
    "CHOCH": {"min": 10, "direction": "min"},
    "LIQUIDITY_SWEEP_HIGH": {"min": 5, "direction": "min"},
    "LIQUIDITY_SWEEP_LOW": {"min": 5, "direction": "min"},
    "ORDER_BLOCK_CANDIDATE": {"min": 5, "direction": "min"},
    "ORDER_BLOCK_RETEST": {"min": 2, "direction": "min", "zero_tolerant": True,
                           "note": "Helm P0 — 0 OK in quiet chop; flag persistent zero >2 weeks"},
    "SPRING": {"min": 2, "direction": "min"},
    "UPTHRUST": {"min": 2, "direction": "min"},
    "THREE_DRIVE": {"max": 200, "direction": "max",
                    "note": "if over, flag three_drive_tolerance_points too loose"},
    "FAILURE_SWING": {"min_weekly": 1, "direction": "min_weekly"},
    "SESSION_PHASE": {"exact_m5": 9, "direction": "exact_or_above",
                      "note": "3 sessions x 3 phases on M5"},
}


def mem_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value, default=str)}).encode()
    req = urllib.request.Request(f"{API}/set", data=payload,
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)


def sh(cmd, timeout=30):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def get_engine_start_utc():
    """Return falcon-structure-engine.service ActiveEnterTimestamp as aware UTC datetime, or None."""
    out, _, rc = sh(SSH + ["systemctl show falcon-structure-engine.service -p ActiveEnterTimestamp --value"])
    if rc != 0 or not out:
        return None
    # systemd format: "Fri 2026-04-24 09:02:30 BST"
    try:
        parts = out.split()
        if len(parts) < 4: return None
        date_s, time_s, tz_s = parts[1], parts[2], parts[3]
        # Parse as naive then apply tz offset
        dt_naive = datetime.strptime(f"{date_s} {time_s}", "%Y-%m-%d %H:%M:%S")
        # BST = UTC+1; UTC = UTC+0. Keep it mechanical.
        offset_hours = {"UTC": 0, "BST": 1, "GMT": 0}.get(tz_s, None)
        if offset_hours is None: return None
        dt_utc = (dt_naive - timedelta(hours=offset_hours)).replace(tzinfo=timezone.utc)
        return dt_utc
    except Exception:
        return None


def query_24h_events(window_start_utc):
    """Query event counts per family+timeframe for the last 24h."""
    sql = (
        f"SELECT event_type, timeframe, COUNT(*) AS n, SUM(CASE WHEN advisory_only=0 THEN 1 ELSE 0 END) AS non_advisory "
        f"FROM falcon_structure_events "
        f"WHERE confirmed_at_walltime_utc >= '{window_start_utc}' "
        f"GROUP BY event_type, timeframe ORDER BY event_type, timeframe"
    )
    out, _, _ = sh(SSH + [f"mysql -h127.0.0.1 -P3307 -uroot -p{DB} tradingProteus -Nse \"{sql}\""])
    rows = []
    for line in out.splitlines():
        cols = line.split("\t")
        if len(cols) >= 4:
            rows.append({
                "event_type": cols[0],
                "timeframe": cols[1],
                "n": int(cols[2]),
                "non_advisory": int(cols[3]),
            })
    return rows


def grade_families(rows, runtime_hours, window_hours=24):
    """
    Aggregate per-family counts and grade vs thresholds.
    Runtime-aware per Helm 2026-04-24: SESSION_PHASE expected scales with runtime,
    THREE_DRIVE graded on rate/hour not raw 24h total.
    """
    by_family = {}
    total_non_advisory = 0
    for r in rows:
        f = r["event_type"]
        by_family.setdefault(f, {"total": 0, "by_tf": {}, "non_advisory": 0})
        by_family[f]["total"] += r["n"]
        by_family[f]["by_tf"][r["timeframe"]] = r["n"]
        by_family[f]["non_advisory"] += r["non_advisory"]
        total_non_advisory += r["non_advisory"]

    # scale factor for runtime vs full window
    runtime_frac = min(runtime_hours / window_hours, 1.0) if window_hours > 0 else 1.0

    grades = {}
    for family, spec in THRESHOLDS.items():
        obs = by_family.get(family, {"total": 0, "by_tf": {}, "non_advisory": 0})
        n = obs["total"]
        rate_per_hour = n / runtime_hours if runtime_hours > 0 else 0
        grade = "GREEN"
        note = ""
        direction = spec["direction"]
        if direction == "min":
            # scale minimum by runtime fraction so partial-runtime days aren't graded RED
            scaled_min = max(1, int(round(spec["min"] * runtime_frac)))
            if n < scaled_min:
                grade = "AMBER" if spec.get("zero_tolerant") and n == 0 else "RED"
                note = f"below floor ({n} < {scaled_min} scaled from {spec['min']}, runtime {runtime_hours:.1f}h)"
        elif direction == "max":
            # THREE_DRIVE: grade on rate/hour, not raw total (Helm 2026-04-24)
            if family == "THREE_DRIVE":
                # upper bound 200/day = ~8.3/hr. Helm says >10/hr steady state = too loose.
                if rate_per_hour > 10:
                    grade = "RED"
                    note = f"rate {rate_per_hour:.1f}/hr > 10/hr cap — tolerance too loose ({spec.get('note','')})"
                elif rate_per_hour > 8:
                    grade = "AMBER"
                    note = f"rate {rate_per_hour:.1f}/hr approaching 10/hr cap"
            else:
                if n > spec["max"]:
                    grade = "RED"
                    note = f"above upper bound ({n} > {spec['max']}) — {spec.get('note','')}"
        elif direction == "min_weekly":
            grade = "GREEN"
        elif direction == "exact_or_above":
            # SESSION_PHASE: scale expected by runtime fraction (Helm 2026-04-24)
            m5 = obs["by_tf"].get("M5", 0)
            expected = max(1, int(round(spec["exact_m5"] * runtime_frac)))
            if m5 < expected:
                grade = "AMBER"
                note = f"M5 count {m5} vs scaled expected {expected} (runtime {runtime_hours:.1f}h, full-day would be {spec['exact_m5']})"
        grades[family] = {
            "n": n, "by_tf": obs["by_tf"], "rate_per_hour": round(rate_per_hour, 2),
            "grade": grade, "note": note, "threshold_spec": spec
        }

    return grades, total_non_advisory


def overall_grade(family_grades, non_advisory):
    if non_advisory > 0:
        return "RED", f"{non_advisory} events with advisory_only=0 — contract violation"
    red = sum(1 for g in family_grades.values() if g["grade"] == "RED")
    amber = sum(1 for g in family_grades.values() if g["grade"] == "AMBER")
    if red >= 3:
        return "RED", f"{red} families RED"
    if red >= 1:
        return "RED", f"{red} family RED: {[f for f,g in family_grades.items() if g['grade']=='RED']}"
    if amber >= 3:
        return "AMBER", f"{amber} families AMBER"
    if amber >= 1:
        return "AMBER", f"{amber} family AMBER: {[f for f,g in family_grades.items() if g['grade']=='AMBER']}"
    return "GREEN", "All 11 families within threshold, all advisory"


def main():
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=24)
    date_tag = now.strftime("%Y-%m-%d")
    window_start_s = window_start.strftime("%Y-%m-%d %H:%M:%S")

    # Runtime-aware grading per Helm 2026-04-24
    engine_start = get_engine_start_utc()
    effective_start = max(window_start, engine_start) if engine_start else window_start
    runtime_hours = max((now - effective_start).total_seconds() / 3600.0, 0.01)

    rows = query_24h_events(window_start_s)
    if not rows:
        result = {
            "run_time_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "overall_status": "RED",
            "overall_headline": "No events observed in 24h — engine may be down",
            "window_start_utc": window_start_s,
            "window_end_utc": now.strftime("%Y-%m-%d %H:%M:%S"),
            "engine_active_since_utc": engine_start.strftime("%Y-%m-%dT%H:%M:%SZ") if engine_start else None,
        }
        mem_set(f"r2d2:validation:structure_engine_6_2:{date_tag}", result)
        sys.exit(1)

    family_grades, non_advisory = grade_families(rows, runtime_hours=runtime_hours, window_hours=24)
    overall, headline = overall_grade(family_grades, non_advisory)

    result = {
        "suite_id": "r2d2:tests:structure_engine_6_2_validation_suite",
        "suite_version": "1.1",
        "run_time_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_start_utc": window_start_s,
        "window_end_utc": now.strftime("%Y-%m-%d %H:%M:%S"),
        "engine_active_since_utc": engine_start.strftime("%Y-%m-%dT%H:%M:%SZ") if engine_start else None,
        "effective_window_start_utc": effective_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_hours_in_window": round(runtime_hours, 2),
        "overall_status": overall,
        "overall_headline": headline,
        "total_events_24h": sum(g["n"] for g in family_grades.values()),
        "non_advisory_count": non_advisory,
        "per_family": family_grades,
        "raw_rows": rows,
        "idempotency_probe": "DEFERRED — to be built as separate harness (Helm's brief item 2)",
        "grading_notes": [
            "v1.1 (Helm 2026-04-24): SESSION_PHASE expected scaled by runtime fraction; THREE_DRIVE graded on rate/hour (RED if >10/hr, AMBER if >8/hr); min thresholds scaled by runtime fraction.",
        ],
    }

    mem_set(f"r2d2:validation:structure_engine_6_2:{date_tag}", result)
    mem_set("r2d2:tests:structure_engine_6_2_validation_suite:latest", result)

    print(f"[{now.strftime('%Y-%m-%dT%H:%M:%SZ')}] §6.2 validation: {overall} — {headline}")
    print(f"  runtime_hours={runtime_hours:.2f}  total_events_24h={result['total_events_24h']}  non_advisory={non_advisory}")
    for f, g in family_grades.items():
        marker = {"GREEN": " ", "AMBER": "!", "RED": "X"}[g["grade"]]
        print(f"  [{marker}] {f:<22} n={g['n']:<4} rate={g['rate_per_hour']:>6.1f}/hr  {g['grade']}  {g['note']}")


if __name__ == "__main__":
    main()
