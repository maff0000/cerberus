"""nowic_at_validation_watcher — single-tick orchestrator.
Mirrors r2d2-tdr-watcher proven pattern for nowic_at_m15.
Carve-out: ONE_TIME_EXCEPTION_NOWIC_AT_VALIDATION_WATCHER.

UTC discipline: deploy anchor architect-stamped from PR #605 / f164a43f.
canonical_now from MAX(helios_v3_decisions.cycle_ts) — never NOW() or utcnow().
"""
import json, subprocess, sys, datetime, urllib.request

# Re-anchored at PR #614 GUARDRAIL_REACH (post-hardening sweep CLOSED GREEN).
# Architect directive 2026-05-01: ignore all fired rows before this anchor.
# Source: git log -1 a3e9a1af --format=%cI = 2026-05-01T09:06:32+01:00
DEPLOY_ANCHOR_UTC_STR = "2026-05-01T08:06:32+00:00"
DEADLINE_UTC_STR = "2026-05-08T08:06:32+00:00"
TRIGGER_THRESHOLD = 20
DELL = "root@192.168.11.10"
FABRIC_API = "http://localhost:8080/api/v1/redis"
EXCEPTION_ID = "ONE_TIME_EXCEPTION_NOWIC_AT_VALIDATION_WATCHER"

DEPLOY_ANCHOR = datetime.datetime.fromisoformat(DEPLOY_ANCHOR_UTC_STR)
DEADLINE = datetime.datetime.fromisoformat(DEADLINE_UTC_STR)
DEPLOY_SQL = DEPLOY_ANCHOR.strftime("%Y-%m-%d %H:%M:%S")


def fabric_get(key):
    try:
        r = urllib.request.urlopen(f"{FABRIC_API}/get/{key}", timeout=5)
        d = json.loads(r.read())
        v = d.get("value")
        return json.loads(v) if v else None
    except Exception:
        return None


def fabric_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(f"{FABRIC_API}/set", data=payload,
                                  headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=8).status


def remote_count_and_now():
    cmd_count = (
        f"mysql -h127.0.0.1 -P3307 -uroot -pPDAPass@R00t123 tradingScalp -sN -e "
        f"\"SELECT COUNT(*) FROM helios_strategy_signals WHERE strategy_id='nowic_at_m15' "
        f"AND fired=1 AND timestamp >= '{DEPLOY_SQL}'\""
    )
    cmd_now = (
        f"mysql -h127.0.0.1 -P3307 -uroot -pPDAPass@R00t123 tradingScalp -sN -e "
        f"\"SELECT MAX(cycle_ts) FROM helios_v3_decisions\""
    )
    out_count = subprocess.run(["ssh", DELL, cmd_count], capture_output=True, text=True, timeout=20)
    if out_count.returncode != 0:
        raise RuntimeError(f"FAIL_LOUD: count query failed: {out_count.stderr.strip()}")
    out_now = subprocess.run(["ssh", DELL, cmd_now], capture_output=True, text=True, timeout=20)
    if out_now.returncode != 0:
        raise RuntimeError(f"FAIL_LOUD: now query failed: {out_now.stderr.strip()}")
    try:
        post_count = int(out_count.stdout.strip())
    except ValueError:
        raise RuntimeError(f"FAIL_LOUD: cannot parse post_count: {out_count.stdout!r}")
    canonical_now_str = out_now.stdout.strip()
    if not canonical_now_str or canonical_now_str == "NULL":
        raise RuntimeError("FAIL_LOUD: canonical_now is NULL — no V3 cycles in DB")
    canonical_now = datetime.datetime.strptime(canonical_now_str, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=datetime.timezone.utc)
    if canonical_now < DEPLOY_ANCHOR:
        raise RuntimeError(f"FAIL_LOUD: canonical_now {canonical_now} < deploy_anchor {DEPLOY_ANCHOR}")
    return post_count, canonical_now


def publish_inconclusive_waiting():
    state = fabric_get("r2d2:watcher:nowic_at_validation:state") or {}
    canonical_now_str = state.get("last_check_canonical_now_utc")
    report = {
        "report_id": f"r2d2:audit:nowic_at_m15_formula_validation:{canonical_now_str or DEADLINE_UTC_STR}",
        "wo": "WO-FALCON-CONFIDENCE-FORMULA-NOWIC-AT-M15-0001",
        "validator": "R2D2 (autonomous via nowic_at_validation_watcher)",
        "exception_ref": EXCEPTION_ID,
        "label": "INCONCLUSIVE_WAITING_FOR_FIRES",
        "label_rationale": (
            f"7 calendar days elapsed since deploy ({DEPLOY_ANCHOR_UTC_STR}) without reaching "
            f"TRIGGER_THRESHOLD={TRIGGER_THRESHOLD} post-deploy fires. Watcher auto-disabling per architect carve-out."
        ),
        "deploy_anchor_utc": DEPLOY_ANCHOR_UTC_STR,
        "deadline_utc": DEADLINE_UTC_STR,
        "completed_at_anchor_utc": canonical_now_str,
        "constraints_held": ["nowic_at_m15 only", "READ-ONLY", "UTC canonical from cycle_ts"]
    }
    fabric_set(report["report_id"], report)
    fabric_set("r2d2:audit:nowic_at_m15_formula_validation:latest", report)
    state["status"] = "DISABLED"
    state["final_label"] = "INCONCLUSIVE_WAITING_FOR_FIRES"
    state["final_label_published_at_utc"] = canonical_now_str
    state["auto_disable_reason"] = "DEADLINE_REACHED_WITHOUT_TRIGGER"
    history = state.get("history", [])
    history.append({"event": "deadline_disable", "label": "INCONCLUSIVE_WAITING_FOR_FIRES",
                    "at_utc": canonical_now_str})
    state["history"] = history
    fabric_set("r2d2:watcher:nowic_at_validation:state", state)
    return "INCONCLUSIVE_WAITING_FOR_FIRES"


def heartbeat(post_count, canonical_now):
    state = fabric_get("r2d2:watcher:nowic_at_validation:state") or {}
    state["last_check_utc"] = canonical_now.isoformat()
    state["last_check_post_count"] = post_count
    state["last_check_canonical_now_utc"] = canonical_now.isoformat()
    history = state.get("history", [])
    history.append({"event": "heartbeat", "at_utc": canonical_now.isoformat(), "post_count": post_count})
    if len(history) > 200:
        history = history[-200:]
    state["history"] = history
    fabric_set("r2d2:watcher:nowic_at_validation:state", state)


def trigger_full_validation():
    out = subprocess.run(["python3", "/opt/r2d2/nowic_at_validation_full.py"],
                          capture_output=True, text=True, timeout=240)
    if out.returncode != 0:
        raise RuntimeError(f"FAIL_LOUD: nowic_at_validation_full.py failed: {out.stderr.strip()}")
    return out.stdout.strip()


def main():
    try:
        state = fabric_get("r2d2:watcher:nowic_at_validation:state")
        if not state:
            raise RuntimeError("FAIL_LOUD: watcher state missing")
        if state.get("status") == "DISABLED":
            print("STATUS=DISABLED — exiting silently")
            return 0
        post_count, canonical_now = remote_count_and_now()
        print(f"post_count={post_count} canonical_now={canonical_now.isoformat()}")
        if post_count >= TRIGGER_THRESHOLD:
            print(f"THRESHOLD_REACHED — triggering full validation")
            result = trigger_full_validation()
            print(f"VALIDATION_RESULT: {result}")
            return 0
        if canonical_now >= DEADLINE:
            print(f"DEADLINE_REACHED at canonical_now={canonical_now.isoformat()}")
            label = publish_inconclusive_waiting()
            print(f"PUBLISHED: {label}")
            return 0
        heartbeat(post_count, canonical_now)
        days_remaining = (DEADLINE - canonical_now).total_seconds() / 86400
        print(f"HEARTBEAT post_count={post_count}/{TRIGGER_THRESHOLD} days_remaining={days_remaining:.2f}")
        return 0
    except Exception as e:
        err_state = fabric_get("r2d2:watcher:nowic_at_validation:state") or {}
        errors = err_state.get("errors", [])
        errors.append({"exception": str(e), "context": "nowic_at_watcher_tick.py main()"})
        if len(errors) > 50: errors = errors[-50:]
        err_state["errors"] = errors
        try: fabric_set("r2d2:watcher:nowic_at_validation:state", err_state)
        except Exception: pass
        print(f"ERROR={e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
