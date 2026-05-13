"""[DEPRECATED 2026-05-13 — DO NOT INVOKE]
==============================================================================
This script is HISTORICAL.

Architect ratified WO-R2D2-STRATEGY-HEALTH-PUBLICATION-CADENCE-0001 on
2026-05-13. The single authoritative producer for
r2d2:strategy_health:<strategy_id>:overall is now:

    /opt/r2d2/maintenance/strategy_health_publisher.py
    (source: /srv/r2d2/maintenance/strategy_health_publisher.py)
    timer:  r2d2-strategy-health-publisher.timer (4h cadence)
    source_enum: R2D2_SCHEDULED_V1
    contract: r2d2:contract:strategy_health_consumer:v1

This historical script:
  - Uses simple n-tier classifier (no reliability/direction_check gates)
  - Has NO explainability fields (no health_status_reason / full_eligibility)
  - Stamps version=R2D2_90D_OVERALL_V1 (DEPRECATED enum)
  - Was last run manually on 2026-05-06 with override tag
    R2D2_POST_33_REFRESH_V1

DO NOT invoke this script. Running it would overwrite live envelopes with
deprecated-classifier output and break consumer contract v1 explainability.

Preserved here for git-history reference only.
==============================================================================

R2D2 Falcon Health Overall Pass — WO-R2D2-FALCON-BACKTEST-OVERALL-0001.

Reads canonical outcome data from helios_strategy_signals (post-WO-OUTCOME-
RESOLVER-METHODOLOGY-0001), computes per-strategy health scores over a
90-day primary window, and publishes to fabric:

    r2d2:strategy_health:<plugin_id>:overall

Architect-locked V1 rules:
  - 90D primary lookback only. No session/regime weighting.
  - Coverage-gated preflight: rows missing entry/sl/tp1 prices are excluded
    from scoring (R2D2 boundary — does not synthesise truth).
  - Sample-size tiers (publish-aware):
      n_fires_resolved >= 100 -> health_status FULL
      30 <= n < 100           -> LIMITED_SAMPLE
      n < 30                  -> INSUFFICIENT_SAMPLE (status only, NO trusted score)
  - When has_prices == 0: do NOT publish. The strategy is structurally
    unscoreable until producer-side fix.
  - Source enum locked: R2D2_90D_OVERALL_V1.
  - No outcome-resolver changes. No Helios changes. No Falcon-strategy changes.
  - DB resolver is canonical. R2D2 reads outcome_* columns; never writes them.

Score formula (v1, locked):
    wr_norm         = clamp((wr - 0.40) / 0.40)        # 0 at 40% WR, 1 at >=80%
    expectancy_norm = clamp((expectancy_pts + 1.0) / 6.0)  # -1pt -> 0, 5pts -> 1
    sample_quality  = clamp(n_fires_resolved / 100.0)
    score = 0.40 * wr_norm + 0.40 * expectancy_norm + 0.20 * sample_quality

R-multiple is computed and published as audit (not in the score formula
since expectancy already integrates win-loss magnitude). r_multiple_avg
becomes meaningful when Helios V3 enables single-strategy GO authority,
which requires r_multiple_avg >= 1.0 per architect.

Run: PYTHONPATH=/srv-dev:/srv-dev/falcon python3 -m falcon.maintenance.r2d2_health_overall
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import pymysql
import pymysql.cursors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03dZ %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("r2d2_health_overall")

DB_HOST = os.environ.get("FALCON_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("FALCON_DB_PORT", "3306"))
DB_USER = os.environ.get("FALCON_DB_USER", "root")
DB_PASS = os.environ.get("FALCON_DB_PASSWORD", os.environ.get("FALCON_DB_PASS", ""))

FABRIC_URL = os.environ.get("HELIOS_V3_FABRIC_URL", "http://127.0.0.1:18080/api/v1/redis")

LOOKBACK_DAYS = 90
SOURCE_ENUM = "R2D2_90D_OVERALL_V1"

# Locked sample-size tiers (architect 2026-04-29)
N_FULL_THRESHOLD = 100
N_LIMITED_THRESHOLD = 30

# Score formula constants (v1, locked)
WR_FLOOR = 0.40
WR_CEIL = 0.80
EXPECTANCY_OFFSET = 1.0   # shift to positive
EXPECTANCY_RANGE = 6.0    # 5pts above floor
SAMPLE_FULL_AT = 100.0
W_WR = 0.40
W_EXPECTANCY = 0.40
W_SAMPLE = 0.20

WIN_OUTCOMES = {"TP1_HIT", "TP2_HIT"}
LOSS_OUTCOMES = {"SL_HIT"}
NEUTRAL_TERMINAL_OUTCOMES = {"INVALIDATED", "EXPIRED"}
TERMINAL_OUTCOMES = WIN_OUTCOMES | LOSS_OUTCOMES | NEUTRAL_TERMINAL_OUTCOMES


def conn(database: str = "tradingScalp"):
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=database, cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10, read_timeout=60,
    )


# --------------------------------------------------------------------------- #
# Coverage preflight — gates whether any score is published per strategy
# --------------------------------------------------------------------------- #

@dataclass
class StrategyCoverage:
    strategy_id: str
    is_legacy_sf: bool
    total_fired: int = 0
    has_prices: int = 0
    missing_prices: int = 0
    pending: int = 0
    n_fires_resolved: int = 0
    win_count: int = 0
    loss_count: int = 0
    neutral_count: int = 0
    earliest_fire_ts: Optional[str] = None
    latest_fire_ts: Optional[str] = None

    def health_status(self) -> str:
        if self.has_prices == 0:
            return "BLOCKED_INSUFFICIENT_DATA"
        if self.n_fires_resolved >= N_FULL_THRESHOLD:
            return "FULL"
        if self.n_fires_resolved >= N_LIMITED_THRESHOLD:
            return "LIMITED_SAMPLE"
        return "INSUFFICIENT_SAMPLE"

    def is_publishable(self) -> bool:
        """True iff a trusted score should be published. Otherwise status-only."""
        if self.has_prices == 0:
            return False
        return self.health_status() in ("FULL", "LIMITED_SAMPLE")


def fetch_coverage(window_start: datetime) -> dict[str, StrategyCoverage]:
    """Per-strategy coverage for the lookback window (resolver-only — terminal outcomes only)."""
    sql = """
    SELECT
        strategy_id,
        COUNT(*) AS total_fired,
        SUM(CASE WHEN entry_price IS NOT NULL
                  AND sl_price IS NOT NULL
                  AND tp1_price IS NOT NULL
                THEN 1 ELSE 0 END) AS has_prices,
        SUM(CASE WHEN outcome = 'PENDING' THEN 1 ELSE 0 END) AS pending,
        SUM(CASE WHEN outcome IN ('TP1_HIT','TP2_HIT','SL_HIT','INVALIDATED','EXPIRED') THEN 1 ELSE 0 END) AS n_resolved,
        SUM(CASE WHEN outcome IN ('TP1_HIT','TP2_HIT') THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN outcome = 'SL_HIT' THEN 1 ELSE 0 END) AS losses,
        SUM(CASE WHEN outcome IN ('INVALIDATED','EXPIRED') THEN 1 ELSE 0 END) AS neutrals,
        MIN(timestamp) AS earliest,
        MAX(timestamp) AS latest
    FROM helios_strategy_signals
    WHERE fired = 1
      AND instrument = 'XAU_USD'
      AND timestamp >= %s
    GROUP BY strategy_id
    ORDER BY strategy_id
    """
    out: dict[str, StrategyCoverage] = {}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(sql, (window_start,))
            for r in cur.fetchall():
                cov = StrategyCoverage(
                    strategy_id=r["strategy_id"],
                    is_legacy_sf=r["strategy_id"].startswith("SF-"),
                    total_fired=int(r["total_fired"]),
                    has_prices=int(r["has_prices"]),
                    pending=int(r["pending"]),
                    n_fires_resolved=int(r["n_resolved"]),
                    win_count=int(r["wins"]),
                    loss_count=int(r["losses"]),
                    neutral_count=int(r["neutrals"]),
                    earliest_fire_ts=r["earliest"].isoformat() if r["earliest"] else None,
                    latest_fire_ts=r["latest"].isoformat() if r["latest"] else None,
                )
                cov.missing_prices = cov.total_fired - cov.has_prices
                out[cov.strategy_id] = cov
    return out


# --------------------------------------------------------------------------- #
# Scorer — per-strategy, only on rows with full prices and terminal outcomes
# --------------------------------------------------------------------------- #

@dataclass
class StrategyScore:
    strategy_id: str
    score: Optional[float] = None
    score_components: dict = field(default_factory=dict)
    n_fires: int = 0
    n_fires_resolved: int = 0
    wr: Optional[float] = None
    expectancy_pts: Optional[float] = None
    r_multiple_avg: Optional[float] = None
    avg_pnl_pts_win: Optional[float] = None
    avg_pnl_pts_loss: Optional[float] = None
    last_outcome_resolved_utc: Optional[str] = None
    health_status: str = "UNAVAILABLE"
    health_source: str = SOURCE_ENUM


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def fetch_resolved_rows(strategy_id: str, window_start: datetime) -> list[dict]:
    """Per-row resolved data for the score computation. Excludes rows without prices."""
    sql = """
    SELECT outcome, outcome_pnl_pts, outcome_resolved_at_utc, outcome_resolved_at,
           entry_price, sl_price, tp1_price, tp2_price, direction
    FROM helios_strategy_signals
    WHERE fired = 1
      AND instrument = 'XAU_USD'
      AND strategy_id = %s
      AND timestamp >= %s
      AND outcome IN ('TP1_HIT','TP2_HIT','SL_HIT','INVALIDATED','EXPIRED')
      AND entry_price IS NOT NULL
      AND sl_price IS NOT NULL
      AND tp1_price IS NOT NULL
    ORDER BY timestamp ASC
    """
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(sql, (strategy_id, window_start))
            return cur.fetchall()


def compute_score(strategy_id: str, rows: list[dict]) -> StrategyScore:
    """Compute the per-strategy score from resolved rows.

    Excludes INVALIDATED + EXPIRED from WR denominator (they're neither wins
    nor losses). They DO count toward expectancy_pts since pnl_pts captures
    the outcome impact.
    """
    n_resolved = len(rows)
    s = StrategyScore(strategy_id=strategy_id, n_fires_resolved=n_resolved, n_fires=n_resolved)
    if n_resolved == 0:
        return s

    wins = 0
    losses = 0
    pnl_sum_pts = 0.0
    pnl_win_sum = 0.0
    pnl_loss_sum = 0.0
    r_multiples: list[float] = []
    last_resolved_iso: Optional[str] = None

    for r in rows:
        outcome = r["outcome"]
        pnl_raw = r["outcome_pnl_pts"]
        pnl = float(pnl_raw) if pnl_raw is not None else 0.0
        pnl_sum_pts += pnl

        if outcome in WIN_OUTCOMES:
            wins += 1
            pnl_win_sum += pnl
        elif outcome in LOSS_OUTCOMES:
            losses += 1
            pnl_loss_sum += pnl

        # R-multiple: pnl normalised by the per-trade SL distance
        try:
            entry = float(r["entry_price"])
            sl = float(r["sl_price"])
            sl_distance = abs(entry - sl)
            if sl_distance > 0:
                r_multiples.append(pnl / sl_distance)
        except (TypeError, ValueError):
            pass

        # Track last resolved time
        last_ts = r.get("outcome_resolved_at_utc") or r.get("outcome_resolved_at")
        if last_ts:
            iso = last_ts.isoformat() if isinstance(last_ts, datetime) else str(last_ts)
            if last_resolved_iso is None or iso > last_resolved_iso:
                last_resolved_iso = iso

    wr_denominator = wins + losses
    wr = (wins / wr_denominator) if wr_denominator > 0 else 0.0
    expectancy = pnl_sum_pts / n_resolved if n_resolved > 0 else 0.0
    r_avg = sum(r_multiples) / len(r_multiples) if r_multiples else 0.0
    avg_win = (pnl_win_sum / wins) if wins > 0 else None
    avg_loss = (pnl_loss_sum / losses) if losses > 0 else None

    # Score components
    wr_norm = _clamp((wr - WR_FLOOR) / (WR_CEIL - WR_FLOOR))
    expectancy_norm = _clamp((expectancy + EXPECTANCY_OFFSET) / EXPECTANCY_RANGE)
    sample_quality = _clamp(n_resolved / SAMPLE_FULL_AT)
    score = round(W_WR * wr_norm + W_EXPECTANCY * expectancy_norm + W_SAMPLE * sample_quality, 4)

    s.score = score
    s.score_components = {
        "wr_norm": round(wr_norm, 4),
        "expectancy_norm": round(expectancy_norm, 4),
        "sample_quality": round(sample_quality, 4),
        "weights": {"wr": W_WR, "expectancy": W_EXPECTANCY, "sample": W_SAMPLE},
    }
    s.wr = round(wr, 4)
    s.expectancy_pts = round(expectancy, 2)
    s.r_multiple_avg = round(r_avg, 4)
    s.avg_pnl_pts_win = round(avg_win, 2) if avg_win is not None else None
    s.avg_pnl_pts_loss = round(avg_loss, 2) if avg_loss is not None else None
    s.last_outcome_resolved_utc = last_resolved_iso

    # Set status from sample size (architect tiers)
    if n_resolved >= N_FULL_THRESHOLD:
        s.health_status = "FULL"
    elif n_resolved >= N_LIMITED_THRESHOLD:
        s.health_status = "LIMITED_SAMPLE"
    else:
        s.health_status = "INSUFFICIENT_SAMPLE"

    return s


# --------------------------------------------------------------------------- #
# Publisher — only writes for FULL or LIMITED_SAMPLE; status-only for INSUFFICIENT
# --------------------------------------------------------------------------- #

def fabric_set(key: str, value: dict) -> bool:
    body = json.dumps({"key": key, "value": json.dumps(value, default=str)}).encode("utf-8")
    req = urllib.request.Request(
        f"{FABRIC_URL}/set", data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            r.read()
        return True
    except Exception as e:
        log.warning("fabric SET %s failed: %s", key, e)
        return False


def build_envelope(s: StrategyScore, cov: StrategyCoverage,
                   window_start: datetime, window_end: datetime) -> dict:
    """JSON envelope per architect spec from R2D2 review 2026-04-29."""
    base = {
        "score": s.score,
        "score_components": s.score_components,
        "n_fires": cov.total_fired,
        "n_fires_resolved": s.n_fires_resolved,
        "wr": s.wr,
        "expectancy_pts": s.expectancy_pts,
        "r_multiple_avg": s.r_multiple_avg,
        "avg_pnl_pts_win": s.avg_pnl_pts_win,
        "avg_pnl_pts_loss": s.avg_pnl_pts_loss,
        "win_count": cov.win_count,
        "loss_count": cov.loss_count,
        "neutral_count": cov.neutral_count,
        "window_start_utc": window_start.replace(tzinfo=timezone.utc).isoformat() if window_start.tzinfo is None else window_start.isoformat(),
        "window_end_utc": window_end.replace(tzinfo=timezone.utc).isoformat() if window_end.tzinfo is None else window_end.isoformat(),
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
        "last_outcome_resolved_utc": s.last_outcome_resolved_utc,
        "health_status": s.health_status,
        "health_source": s.health_source,
    }
    return base


def publish_strategy_health(plugin_id: str, envelope: dict, dry_run: bool) -> bool:
    key = f"r2d2:strategy_health:{plugin_id}:overall"
    if dry_run:
        log.info("dry-run: would publish key=%s envelope=%s", key, json.dumps(envelope, default=str))
        return True
    return fabric_set(key, envelope)


# --------------------------------------------------------------------------- #
# Main orchestrator
# --------------------------------------------------------------------------- #

def run(dry_run: bool = False, lookback_days: int = LOOKBACK_DAYS) -> dict:
    now_utc = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)
    window_start = now_naive - timedelta(days=lookback_days)
    log.info("R2D2 overall health pass starting | window=%dd source=%s dry_run=%s",
             lookback_days, SOURCE_ENUM, dry_run)

    # Preflight: per-strategy coverage
    coverage = fetch_coverage(window_start)
    log.info("coverage preflight: %d strategies in window", len(coverage))

    summary = {
        "wo_id": "WO-R2D2-FALCON-BACKTEST-OVERALL-0001",
        "computed_at_utc": now_utc.isoformat(),
        "window_start_utc": window_start.replace(tzinfo=timezone.utc).isoformat(),
        "window_end_utc": now_utc.isoformat(),
        "lookback_days": lookback_days,
        "source_enum": SOURCE_ENUM,
        "dry_run": dry_run,
        "tier_thresholds": {
            "FULL": f"n_fires_resolved >= {N_FULL_THRESHOLD}",
            "LIMITED_SAMPLE": f"{N_LIMITED_THRESHOLD} <= n < {N_FULL_THRESHOLD}",
            "INSUFFICIENT_SAMPLE": f"n < {N_LIMITED_THRESHOLD}",
            "BLOCKED_INSUFFICIENT_DATA": "has_prices == 0 (not published)",
        },
        "score_formula": (
            "wr_norm = clamp((wr - 0.40) / 0.40); "
            "expectancy_norm = clamp((expectancy_pts + 1.0) / 6.0); "
            "sample_quality = clamp(n_fires_resolved / 100); "
            "score = 0.40*wr_norm + 0.40*expectancy_norm + 0.20*sample_quality"
        ),
        "strategies": {},
        "counts": {
            "FULL": 0, "LIMITED_SAMPLE": 0,
            "INSUFFICIENT_SAMPLE": 0, "BLOCKED_INSUFFICIENT_DATA": 0,
            "PUBLISHED": 0, "STATUS_ONLY": 0, "SKIPPED": 0,
        },
    }

    for plugin_id, cov in sorted(coverage.items()):
        # Architect: don't publish for blocked strategies (no prices anywhere)
        status_pre = cov.health_status()
        summary["counts"][status_pre] += 1

        if status_pre == "BLOCKED_INSUFFICIENT_DATA":
            log.info("[%s] BLOCKED: 0 of %d rows have entry/sl/tp prices — NOT publishing",
                     plugin_id, cov.total_fired)
            summary["strategies"][plugin_id] = {
                "is_legacy_sf": cov.is_legacy_sf,
                "coverage": asdict(cov),
                "publish_decision": "NOT_PUBLISHED_BLOCKED_INSUFFICIENT_DATA",
                "envelope": None,
            }
            summary["counts"]["SKIPPED"] += 1
            continue

        # Pull resolved rows (all of which carry prices) and score
        resolved_rows = fetch_resolved_rows(plugin_id, window_start)
        s = compute_score(plugin_id, resolved_rows)
        envelope = build_envelope(s, cov, window_start, now_utc)

        # Architect publish-aware rule:
        #   FULL / LIMITED_SAMPLE → publish trusted score
        #   INSUFFICIENT_SAMPLE → publish status only (score=null), source=R2D2_INSUFFICIENT_V1
        if s.health_status == "INSUFFICIENT_SAMPLE":
            envelope["score"] = None
            envelope["score_components"] = None
            envelope["health_source"] = "R2D2_INSUFFICIENT_V1"
            log.info("[%s] INSUFFICIENT_SAMPLE: n=%d (<%d) — status only, no trusted score",
                     plugin_id, s.n_fires_resolved, N_LIMITED_THRESHOLD)
            summary["counts"]["STATUS_ONLY"] += 1
            decision = "STATUS_ONLY_INSUFFICIENT_SAMPLE"
        else:
            log.info("[%s] %s: n=%d wr=%s exp=%s r=%s score=%s",
                     plugin_id, s.health_status, s.n_fires_resolved,
                     s.wr, s.expectancy_pts, s.r_multiple_avg, s.score)
            summary["counts"]["PUBLISHED"] += 1
            decision = "PUBLISHED"

        publish_strategy_health(plugin_id, envelope, dry_run)
        summary["strategies"][plugin_id] = {
            "is_legacy_sf": cov.is_legacy_sf,
            "coverage": asdict(cov),
            "publish_decision": decision,
            "envelope": envelope,
        }

    log.info("done — counts=%s", json.dumps(summary["counts"]))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't write to fabric, just log decisions")
    parser.add_argument("--lookback-days", type=int, default=LOOKBACK_DAYS)
    parser.add_argument("--summary-only", action="store_true",
                        help="Print only counts + per-strategy decisions, not full envelopes")
    args = parser.parse_args()

    summary = run(dry_run=args.dry_run, lookback_days=args.lookback_days)

    if args.summary_only:
        print(json.dumps({"counts": summary["counts"],
                          "strategies": {sid: s["publish_decision"]
                                         for sid, s in summary["strategies"].items()}},
                         default=str, indent=2))
    else:
        print(json.dumps(summary, default=str, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
