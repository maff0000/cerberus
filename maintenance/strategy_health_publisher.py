"""R2D2 strategy_health publisher — WO-R2D2-STRATEGY-HEALTH-PUBLICATION-CADENCE-0001.

Scheduled producer for r2d2:strategy_health:<strategy_id>:overall envelopes.
Architect-ratified 2026-05-13:
  - Single authoritative producer (this script). All other writers deprecated.
  - 4h cadence (00/04/08/12/16/20 UTC).
  - Option B layered classifier with explainability:
      FULL requires ALL of:
        sample_gate: n_fires_resolved >= 100
        reliability_gate: n_fires_resolved >= 100 AND wr >= 0.45
        direction_check_gate: expectancy_pts >= 0.30
      LIMITED_SAMPLE: n >= 30 (sample threshold) but at least one gate failed
      INSUFFICIENT_SAMPLE: n < 30 OR has_prices == 0
  - Source enum: R2D2_SCHEDULED_V1.

Consumer contract: r2d2:contract:strategy_health_consumer:v1 (binding).
Methodology lineage: r2d2:methodology:maintenance:v1.
UTC doctrine: shared:doctrine:utc_everything:v1 — tz-aware UTC throughout;
              no datetime.utcnow(); no naive datetime.

Outputs:
  - r2d2:strategy_health:<strategy_id>:overall   (per strategy, contract-shaped)
  - r2d2:strategy_health:publisher:state         (single state record)
  - r2d2:audit:strategy_health_publication:<ts>  (immutable per-run audit)
  - r2d2:audit:strategy_health_publication:latest (pointer to most recent)
  - r2d2:fault:strategy_health_publisher:<date>  (fault audit if tripwires RED)

Failure behaviour:
  - fail-loud: any tripwire RED → verdict=RED + fault audit emitted
  - no silent partial writes: per-strategy write failures captured + verdict=AMBER
  - no deletes: stale records preserved until next successful overwrite
  - DB unreachable: ABORT before any fabric write; publisher state unchanged

Run: python3 /opt/r2d2/maintenance/strategy_health_publisher.py [--dry-run]
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple

# ─────────────────────────── Constants ─────────────────────────────────────────

WO = "WO-R2D2-STRATEGY-HEALTH-PUBLICATION-CADENCE-0001"
SOURCE_ENUM = "R2D2_SCHEDULED_V1"
TIMER_CADENCE = "00:00/04:00/08:00/12:00/16:00/20:00 UTC"
LOOKBACK_DAYS = 90

# Layered classifier gates (architect-locked 2026-05-13)
N_FULL_THRESHOLD = 100
N_LIMITED_THRESHOLD = 30
RELIABILITY_WR_FLOOR = 0.45        # winrate floor for reliability_gate
DIRECTION_CHECK_EXPECTANCY_FLOOR = 0.30  # expectancy_pts floor for direction_check_gate

# Score formula (inherited from r2d2_health_overall V1 spec — methodology unchanged)
WR_NORM_FLOOR = 0.40
WR_NORM_CEIL = 0.80
EXPECTANCY_OFFSET = 1.0
EXPECTANCY_RANGE = 6.0
SAMPLE_FULL_AT = 100.0
W_WR = 0.40
W_EXPECTANCY = 0.40
W_SAMPLE = 0.20

# Outcome enums (inherited)
WIN_OUTCOMES = {"TP1_HIT", "TP2_HIT"}
LOSS_OUTCOMES = {"SL_HIT"}
NEUTRAL_TERMINAL_OUTCOMES = {"INVALIDATED", "EXPIRED"}
TERMINAL_OUTCOMES = WIN_OUTCOMES | LOSS_OUTCOMES | NEUTRAL_TERMINAL_OUTCOMES

# Fabric key namespaces
KEY_STRATEGY_HEALTH_PREFIX = "r2d2:strategy_health:"
KEY_STRATEGY_HEALTH_SUFFIX = ":overall"
KEY_PUBLISHER_STATE = "r2d2:strategy_health:publisher:state"
KEY_PUBLISHER_AUDIT_LATEST = "r2d2:audit:strategy_health_publication:latest"
KEY_PUBLISHER_AUDIT_PREFIX = "r2d2:audit:strategy_health_publication:"
KEY_PUBLISHER_FAULT_PREFIX = "r2d2:fault:strategy_health_publisher:"

# Consumer contract reference (must remain in sync with r2d2:contract:strategy_health_consumer:v1)
CONTRACT_VERSION = "r2d2:contract:strategy_health_consumer:v1"

# Dormant strategy publication (Phase C remediation 2026-05-13)
# Strategies in fabric :overall namespace with zero fires in the 90d window are
# REFRESHED with an explicit INSUFFICIENT_SAMPLE dormant envelope so no stale
# POST_33 records persist at canonical live keys. Architect ruling 2026-05-13.
DORMANT_HEALTH_SOURCE = "R2D2_DORMANT_V1"
DORMANT_HEALTH_STATUS_REASON = "no_fires_in_90d_window"

# Helios V3 freshness threshold (informational — for tripwire 2)
V3_FRESHNESS_GATE_HOURS = 30

# Allowed status enum (must match contract)
ALLOWED_HEALTH_STATUS = {"FULL", "LIMITED_SAMPLE", "INSUFFICIENT_SAMPLE"}

# Allowed reliability enum
ALLOWED_RELIABILITY_LABEL = {"TRUSTED", "WATCH", "UNTRUSTED"}

# Allowed direction-check enum
ALLOWED_DIRECTION_CHECK = {"POSITIVE", "NEUTRAL", "NEGATIVE"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03dZ %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("strategy_health_publisher")


# ─────────────────────────── Data classes ──────────────────────────────────────

@dataclass
class StrategyCoverage:
    strategy_id: str
    total_fired: int = 0
    has_prices: int = 0
    missing_prices: int = 0
    pending: int = 0
    earliest_fire_ts: Optional[str] = None
    latest_fire_ts: Optional[str] = None


@dataclass
class StrategyScore:
    strategy_id: str
    n_fires_resolved: int = 0
    win_count: int = 0
    loss_count: int = 0
    neutral_count: int = 0
    wr: Optional[float] = None
    expectancy_pts: Optional[float] = None
    avg_pnl_pts_win: Optional[float] = None
    avg_pnl_pts_loss: Optional[float] = None
    score: Optional[float] = None
    score_components: Optional[Dict[str, Any]] = None
    last_outcome_resolved_utc: Optional[str] = None


@dataclass
class FullEligibility:
    sample_gate_passed: bool
    reliability_gate_passed: bool
    direction_check_gate_passed: bool
    failed_gates: List[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return (
            self.sample_gate_passed
            and self.reliability_gate_passed
            and self.direction_check_gate_passed
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_gate_passed": self.sample_gate_passed,
            "reliability_gate_passed": self.reliability_gate_passed,
            "direction_check_gate_passed": self.direction_check_gate_passed,
            "failed_gates": list(self.failed_gates),
        }


# ─────────────────────────── Pure helpers (testable) ───────────────────────────

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def now_utc() -> datetime:
    """tz-aware UTC. Never datetime.utcnow()."""
    return datetime.now(timezone.utc)


def iso_z(dt_: datetime) -> str:
    """Render tz-aware datetime as %Y-%m-%dT%H:%M:%S.%fZ."""
    if dt_.tzinfo is None:
        raise ValueError("tz-naive datetime rejected per shared:doctrine:utc_everything:v1")
    return dt_.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def compute_score_components(
    wr: float,
    expectancy_pts: float,
    n_fires_resolved: int,
) -> Dict[str, Any]:
    """Compute score from per-component norms. Inherited V1 methodology."""
    wr_norm = clamp((wr - WR_NORM_FLOOR) / (WR_NORM_CEIL - WR_NORM_FLOOR))
    expectancy_norm = clamp((expectancy_pts + EXPECTANCY_OFFSET) / EXPECTANCY_RANGE)
    sample_quality = clamp(n_fires_resolved / SAMPLE_FULL_AT)
    score = (
        W_WR * wr_norm
        + W_EXPECTANCY * expectancy_norm
        + W_SAMPLE * sample_quality
    )
    return {
        "score": round(score, 4),
        "components": {
            "wr_norm": round(wr_norm, 4),
            "expectancy_norm": round(expectancy_norm, 4),
            "sample_quality": round(sample_quality, 4),
            "weights": {
                "wr": W_WR,
                "expectancy": W_EXPECTANCY,
                "sample": W_SAMPLE,
            },
        },
    }


def evaluate_full_eligibility(
    n_fires_resolved: int,
    wr: Optional[float],
    expectancy_pts: Optional[float],
) -> FullEligibility:
    """Layered classifier — architect-locked 2026-05-13.

    Returns explicit gate booleans + failed_gates list. Caller uses .all_passed
    to decide FULL vs LIMITED_SAMPLE. Caller maps n<30 to INSUFFICIENT_SAMPLE
    separately.
    """
    sample_gate = n_fires_resolved >= N_FULL_THRESHOLD
    # Reliability gate: enough sample AND non-flaky winrate.
    reliability_gate = (
        n_fires_resolved >= N_FULL_THRESHOLD
        and wr is not None
        and wr >= RELIABILITY_WR_FLOOR
    )
    # Direction-check gate: positive expectancy above noise floor.
    direction_check_gate = (
        expectancy_pts is not None
        and expectancy_pts >= DIRECTION_CHECK_EXPECTANCY_FLOOR
    )
    failed: List[str] = []
    if not sample_gate:
        failed.append("sample_gate")
    if not reliability_gate:
        failed.append("reliability_gate")
    if not direction_check_gate:
        failed.append("direction_check_gate")
    return FullEligibility(
        sample_gate_passed=sample_gate,
        reliability_gate_passed=reliability_gate,
        direction_check_gate_passed=direction_check_gate,
        failed_gates=failed,
    )


def classify_health_status(
    n_fires_resolved: int,
    has_prices: int,
    eligibility: FullEligibility,
) -> Tuple[str, str]:
    """Return (health_status, health_status_reason).

    Architect-locked layered classifier:
      INSUFFICIENT_SAMPLE if has_prices == 0 or n < 30
      FULL if all 3 gates passed
      LIMITED_SAMPLE if n >= 30 but at least one gate failed
    """
    if has_prices == 0:
        return (
            "INSUFFICIENT_SAMPLE",
            f"has_prices=0 (no resolvable fires); n<{N_LIMITED_THRESHOLD} threshold not met",
        )
    if n_fires_resolved < N_LIMITED_THRESHOLD:
        return (
            "INSUFFICIENT_SAMPLE",
            f"n_fires_resolved={n_fires_resolved} < {N_LIMITED_THRESHOLD} sample minimum",
        )
    if eligibility.all_passed:
        return (
            "FULL",
            f"all 3 gates passed: sample(n>={N_FULL_THRESHOLD}) AND reliability(wr>={RELIABILITY_WR_FLOOR}) AND direction_check(expectancy>={DIRECTION_CHECK_EXPECTANCY_FLOOR})",
        )
    failed = ",".join(eligibility.failed_gates)
    return (
        "LIMITED_SAMPLE",
        f"n_fires_resolved={n_fires_resolved} >= {N_LIMITED_THRESHOLD} but failed gates: [{failed}]",
    )


def derive_reliability_label(
    eligibility: FullEligibility,
    n_fires_resolved: int,
) -> str:
    """Producer-internal mapping from gate state → reliability_label enum."""
    if eligibility.reliability_gate_passed:
        return "TRUSTED"
    if n_fires_resolved >= N_LIMITED_THRESHOLD:
        return "WATCH"
    return "UNTRUSTED"


def derive_direction_check_status(
    eligibility: FullEligibility,
    expectancy_pts: Optional[float],
) -> str:
    """Producer-internal mapping from gate state → direction_check_status enum."""
    if eligibility.direction_check_gate_passed:
        return "POSITIVE"
    if expectancy_pts is None:
        return "NEUTRAL"
    if expectancy_pts < 0:
        return "NEGATIVE"
    return "NEUTRAL"


def build_envelope(
    coverage: StrategyCoverage,
    score: StrategyScore,
    eligibility: FullEligibility,
    window_start: datetime,
    window_end: datetime,
    computed_at: datetime,
) -> Dict[str, Any]:
    """Build the per-strategy contract-compliant envelope.

    Contract v1 required fields:
      - health_status, score, computed_at_utc, n_fires_resolved, version
    Plus architect explainability fields:
      - health_status_reason, full_eligibility{}
    Plus inherited optional fields preserved for consumer compat.
    """
    health_status, health_status_reason = classify_health_status(
        n_fires_resolved=score.n_fires_resolved,
        has_prices=coverage.has_prices,
        eligibility=eligibility,
    )

    reliability_label = derive_reliability_label(eligibility, score.n_fires_resolved)
    direction_check_status = derive_direction_check_status(
        eligibility, score.expectancy_pts
    )

    # INSUFFICIENT_SAMPLE → publish status-only (no trusted score)
    if health_status == "INSUFFICIENT_SAMPLE":
        published_score = None
        published_score_components = None
        published_health_source = "R2D2_INSUFFICIENT_V1"
    else:
        published_score = score.score
        published_score_components = score.score_components
        published_health_source = SOURCE_ENUM

    envelope = {
        # Contract v1 REQUIRED fields
        "health_status": health_status,
        "score": published_score,
        "computed_at_utc": iso_z(computed_at),
        "n_fires_resolved": score.n_fires_resolved,
        "version": SOURCE_ENUM,
        # Architect explainability (2026-05-13 ratification)
        "health_status_reason": health_status_reason,
        "full_eligibility": eligibility.to_dict(),
        # Contract v1 OPTIONAL fields preserved
        "score_components": published_score_components,
        "wr": score.wr,
        "expectancy_pts": score.expectancy_pts,
        "win_count": score.win_count,
        "loss_count": score.loss_count,
        "neutral_count": score.neutral_count,
        "pending_count": coverage.pending,
        "window_start_utc": iso_z(window_start),
        "window_end_utc": iso_z(window_end),
        "anchor_utc_canonical": iso_z(computed_at),
        "health_source": published_health_source,
        "reliability_label": reliability_label,
        "direction_check_status": direction_check_status,
        "last_outcome_resolved_utc": score.last_outcome_resolved_utc,
        "avg_pnl_pts_win": score.avg_pnl_pts_win,
        "avg_pnl_pts_loss": score.avg_pnl_pts_loss,
        # Decision-grade flag — Phase C remediation 2026-05-13.
        # Producer-side gate: True only when health_status == FULL. Consumer
        # ANDs this with its own freshness check per contract v1 rule 3.
        "decision_grade": health_status == "FULL",
        # Producer provenance
        "wo": WO,
        "writer_version": SOURCE_ENUM,
        "strategy_id": coverage.strategy_id,
        "contract_compatibility": CONTRACT_VERSION,
    }
    return envelope


# ─────────────────────────── Dormant strategy envelope ────────────────────────

def build_dormant_envelope(
    strategy_id: str,
    window_start: datetime,
    window_end: datetime,
    computed_at: datetime,
) -> Dict[str, Any]:
    """Build a fresh INSUFFICIENT_SAMPLE envelope for a dormant strategy.

    Phase C remediation 2026-05-13 (architect ruling): every expected strategy
    in fabric must have a FRESH scheduled :overall record. Strategies with zero
    fires in the 90d lookback window get a dormant envelope that explicitly
    documents the no-fires condition, overwriting any prior stale record.

    Contract v1 compliance: same field shape as the active envelope; score=null;
    all three gates explicitly failed with health_status_reason naming the
    dormant condition.
    """
    envelope = {
        # Contract v1 REQUIRED fields
        "health_status": "INSUFFICIENT_SAMPLE",
        "score": None,
        "computed_at_utc": iso_z(computed_at),
        "n_fires_resolved": 0,
        "version": SOURCE_ENUM,
        # Architect explainability (2026-05-13 ratification + remediation)
        "health_status_reason": DORMANT_HEALTH_STATUS_REASON,
        "full_eligibility": {
            "sample_gate_passed": False,
            "reliability_gate_passed": False,
            "direction_check_gate_passed": False,
            "failed_gates": [
                "sample_gate",
                "reliability_gate",
                "direction_check_gate",
            ],
        },
        # Contract v1 OPTIONAL fields preserved (all null for dormant)
        "score_components": None,
        "wr": None,
        "expectancy_pts": None,
        "win_count": 0,
        "loss_count": 0,
        "neutral_count": 0,
        "pending_count": 0,
        "window_start_utc": iso_z(window_start),
        "window_end_utc": iso_z(window_end),
        "anchor_utc_canonical": iso_z(computed_at),
        "health_source": DORMANT_HEALTH_SOURCE,
        "reliability_label": "UNTRUSTED",
        "direction_check_status": "NEUTRAL",
        "last_outcome_resolved_utc": None,
        "avg_pnl_pts_win": None,
        "avg_pnl_pts_loss": None,
        # Decision-grade flag — always False for dormant
        "decision_grade": False,
        # Producer provenance
        "wo": WO,
        "writer_version": SOURCE_ENUM,
        "strategy_id": strategy_id,
        "contract_compatibility": CONTRACT_VERSION,
        # Dormant marker — distinguishes from "no fires AND has_prices=0 blocked"
        "dormant_in_90d_window": True,
    }
    return envelope


# ─────────────────────────── Fabric strategy discovery ────────────────────────

def discover_existing_strategies_in_fabric(
    fabric_keys: Callable[[str], List[str]],
) -> List[str]:
    """Scan r2d2:strategy_health:*:overall keys (excluding snapshots).

    Returns the list of strategy_ids that currently have a live :overall key in
    fabric. This is the producer-side authoritative source of "previously
    published strategies"; combined with the DB-side active set, the union is
    the expected publication set per architect's 2026-05-13 ruling.
    """
    pattern = f"{KEY_STRATEGY_HEALTH_PREFIX}*{KEY_STRATEGY_HEALTH_SUFFIX}"
    keys = fabric_keys(pattern)
    if not keys:
        return []
    strategy_ids: List[str] = []
    prefix_len = len(KEY_STRATEGY_HEALTH_PREFIX)
    suffix_len = len(KEY_STRATEGY_HEALTH_SUFFIX)
    for k in keys:
        # Skip snapshot variants — r2d2:strategy_health:<id>:overall:snapshot:...
        if ":snapshot:" in k:
            continue
        if not (k.startswith(KEY_STRATEGY_HEALTH_PREFIX)
                and k.endswith(KEY_STRATEGY_HEALTH_SUFFIX)):
            continue
        # Skip the publisher-state key which shares the strategy_health prefix
        # but is NOT a strategy envelope.
        if k == KEY_PUBLISHER_STATE:
            continue
        sid = k[prefix_len:-suffix_len]
        # Defensive: a key like r2d2:strategy_health:publisher:state would have
        # sid="publisher" if state suffix weren't :overall — skip "publisher".
        if sid == "publisher":
            continue
        strategy_ids.append(sid)
    return sorted(strategy_ids)


def compute_expected_strategy_set(
    active_strategies: List[str],
    existing_in_fabric: List[str],
) -> Tuple[List[str], List[str]]:
    """Return (all_expected, dormant_only) — union of active + existing fabric.

    A dormant strategy is one that exists in fabric (was previously published)
    but does NOT appear in the active set (no fires in 90d).
    """
    expected = sorted(set(active_strategies) | set(existing_in_fabric))
    dormant = sorted(set(existing_in_fabric) - set(active_strategies))
    return expected, dormant


# ─────────────────────────── Tripwires ─────────────────────────────────────────

@dataclass
class TripwireResult:
    id: str
    name: str
    tier: str
    passed: bool
    detail: str


def tripwire_1_expected_count(
    expected: int, published: int
) -> TripwireResult:
    passed = published == expected
    return TripwireResult(
        id="TW-1",
        name="expected_strategy_count_published",
        tier="RED",
        passed=passed,
        detail=f"expected={expected} published={published}"
        + ("" if passed else " → missing strategies"),
    )


def tripwire_2_no_record_older_than_30h(
    records: Dict[str, Dict[str, Any]],
    now_utc_: datetime,
) -> TripwireResult:
    """Check freshness of every record this run is about to write OR has just written.
    Threshold: V3_FRESHNESS_GATE_HOURS (30h).
    """
    stale: List[Tuple[str, float]] = []
    for sid, env in records.items():
        ts_str = env.get("computed_at_utc")
        if not ts_str:
            stale.append((sid, -1.0))
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                stale.append((sid, -1.0))
                continue
            age_hours = (now_utc_ - ts).total_seconds() / 3600.0
            if age_hours > V3_FRESHNESS_GATE_HOURS:
                stale.append((sid, round(age_hours, 2)))
        except (ValueError, TypeError):
            stale.append((sid, -1.0))
    passed = len(stale) == 0
    return TripwireResult(
        id="TW-2",
        name="no_record_older_than_30h",
        tier="RED",
        passed=passed,
        detail=f"stale_count={len(stale)}"
        + (f" stale={stale[:5]}" if stale else ""),
    )


def tripwire_3_tz_aware_utc(records: Dict[str, Dict[str, Any]]) -> TripwireResult:
    """Verify every record's timestamp fields are tz-aware UTC."""
    violations: List[str] = []
    for sid, env in records.items():
        for field_name in ("computed_at_utc", "window_start_utc", "window_end_utc"):
            v = env.get(field_name)
            if v is None:
                continue
            if not isinstance(v, str):
                violations.append(f"{sid}.{field_name}=non-string")
                continue
            if not (v.endswith("Z") or "+" in v):
                violations.append(f"{sid}.{field_name}=tz-naive")
    passed = len(violations) == 0
    return TripwireResult(
        id="TW-3",
        name="computed_at_utc_tz_aware_UTC",
        tier="RED",
        passed=passed,
        detail=f"violations={len(violations)}"
        + (f" sample={violations[:5]}" if violations else ""),
    )


def tripwire_4_score_schema(records: Dict[str, Dict[str, Any]]) -> TripwireResult:
    """score must be float OR None+health_source=R2D2_INSUFFICIENT_V1."""
    violations: List[str] = []
    for sid, env in records.items():
        s = env.get("score")
        if s is None:
            if env.get("health_source") != "R2D2_INSUFFICIENT_V1":
                violations.append(
                    f"{sid}=null score but health_source={env.get('health_source')}"
                )
        elif not isinstance(s, (int, float)):
            violations.append(f"{sid}=non-numeric score type={type(s).__name__}")
    passed = len(violations) == 0
    return TripwireResult(
        id="TW-4",
        name="score_numeric_or_null_with_reason",
        tier="RED",
        passed=passed,
        detail=f"violations={len(violations)}"
        + (f" sample={violations[:5]}" if violations else ""),
    )


def tripwire_5_enum_allowed(records: Dict[str, Dict[str, Any]]) -> TripwireResult:
    """health_status MUST be in ALLOWED_HEALTH_STATUS."""
    violations: List[str] = []
    for sid, env in records.items():
        hs = env.get("health_status")
        if hs not in ALLOWED_HEALTH_STATUS:
            violations.append(f"{sid}={hs}")
    passed = len(violations) == 0
    return TripwireResult(
        id="TW-5",
        name="health_status_in_allowed_enum",
        tier="RED",
        passed=passed,
        detail=f"violations={len(violations)}"
        + (f" sample={violations[:5]}" if violations else ""),
    )


def tripwire_6_registry_drift(
    expected_strategies: List[str],
    published_strategies: List[str],
) -> TripwireResult:
    """AMBER: any strategy_id published but NOT in registry → new strategy.
    Any in registry but NOT published is caught by TW-1.
    """
    new_strategies = sorted(set(published_strategies) - set(expected_strategies))
    passed = len(new_strategies) == 0
    return TripwireResult(
        id="TW-6",
        name="strategy_ids_match_falcon_registry",
        tier="AMBER",
        passed=passed,
        detail=f"new_strategies={len(new_strategies)}"
        + (f" sample={new_strategies[:5]}" if new_strategies else ""),
    )


def tripwire_8_no_stale_version_in_fabric(
    fabric_keys: Callable[[str], List[str]],
    fabric_get_envelope: Callable[[str], Optional[Dict[str, Any]]],
    accepted_versions: Optional[set] = None,
) -> TripwireResult:
    """Phase C remediation tripwire — architect ruling 2026-05-13.

    After a successful publication, scan all r2d2:strategy_health:<id>:overall
    keys (excluding snapshots) and verify EVERY record carries an accepted
    fresh version tag. Stale POST_33_REFRESH_V1 / R2D2_90D_OVERALL_V1 / any
    legacy enum at canonical live keys → RED.

    Snapshot keys are immutable historical refs and are NOT scanned.
    """
    if accepted_versions is None:
        accepted_versions = {SOURCE_ENUM}
    pattern = f"{KEY_STRATEGY_HEALTH_PREFIX}*{KEY_STRATEGY_HEALTH_SUFFIX}"
    keys = fabric_keys(pattern) or []
    stale: List[str] = []
    for k in keys:
        if ":snapshot:" in k:
            continue
        if k == KEY_PUBLISHER_STATE:
            continue
        env = fabric_get_envelope(k)
        if not isinstance(env, dict):
            stale.append(f"{k}=unreadable")
            continue
        v = env.get("version")
        if v not in accepted_versions:
            stale.append(f"{k}={v}")
    passed = len(stale) == 0
    return TripwireResult(
        id="TW-8",
        name="no_stale_version_at_canonical_keys_after_publication",
        tier="RED",
        passed=passed,
        detail=f"stale_records={len(stale)}"
        + (f" sample={stale[:5]}" if stale else ""),
    )


def tripwire_7_audit_canary(
    last_audit_at_utc: Optional[datetime],
    now_utc_: datetime,
    cadence_hours: float = 4.0,
) -> TripwireResult:
    """Audit must have been emitted within 1.5x cadence interval."""
    if last_audit_at_utc is None:
        return TripwireResult(
            id="TW-7",
            name="publisher_emits_audit_every_run",
            tier="RED",
            passed=False,
            detail="last_audit_at_utc=None (first run OR audit-chain broken)",
        )
    age_hours = (now_utc_ - last_audit_at_utc).total_seconds() / 3600.0
    threshold = cadence_hours * 1.5
    passed = age_hours <= threshold
    return TripwireResult(
        id="TW-7",
        name="publisher_emits_audit_every_run",
        tier="RED",
        passed=passed,
        detail=f"last_audit_age_hours={age_hours:.2f} threshold={threshold:.2f}",
    )


def run_all_tripwires(
    expected_strategies: List[str],
    published_records: Dict[str, Dict[str, Any]],
    now_utc_: datetime,
    last_audit_at_utc: Optional[datetime],
    fabric_keys: Optional[Callable[[str], List[str]]] = None,
    fabric_get_envelope: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None,
) -> Tuple[str, List[TripwireResult]]:
    """Run all 8 tripwires. Return (verdict, results).

    verdict:
      RED   → any RED-tier tripwire failed
      AMBER → all RED passed but at least one AMBER failed
      GREEN → all passed

    Phase C remediation: TW-8 added (no_stale_version_at_canonical_keys). Runs
    only when fabric_keys + fabric_get_envelope are supplied (test fakes may
    omit them; live run always supplies them).
    """
    results = [
        tripwire_1_expected_count(len(expected_strategies), len(published_records)),
        tripwire_2_no_record_older_than_30h(published_records, now_utc_),
        tripwire_3_tz_aware_utc(published_records),
        tripwire_4_score_schema(published_records),
        tripwire_5_enum_allowed(published_records),
        tripwire_6_registry_drift(expected_strategies, list(published_records.keys())),
        tripwire_7_audit_canary(last_audit_at_utc, now_utc_),
    ]
    if fabric_keys is not None and fabric_get_envelope is not None:
        results.append(tripwire_8_no_stale_version_in_fabric(
            fabric_keys, fabric_get_envelope,
        ))
    red_failed = [r for r in results if r.tier == "RED" and not r.passed]
    amber_failed = [r for r in results if r.tier == "AMBER" and not r.passed]
    if red_failed:
        verdict = "RED"
    elif amber_failed:
        verdict = "AMBER"
    else:
        verdict = "GREEN"
    return verdict, results


# ─────────────────────────── DB / fabric I/O ──────────────────────────────────

def http_fabric_get(
    key: str, fabric_url: str = "http://127.0.0.1:8080/api/v1/redis"
) -> Optional[Any]:
    try:
        r = urllib.request.urlopen(
            f"{fabric_url}/get/{urllib.parse.quote(key, safe=':')}", timeout=10
        )
        d = json.loads(r.read())
        v = d.get("value")
        if v is None:
            return None
        try:
            return json.loads(v)
        except (json.JSONDecodeError, ValueError):
            return v
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None


def http_fabric_keys(
    pattern: str, fabric_url: str = "http://127.0.0.1:8080/api/v1/redis"
) -> List[str]:
    """Path-style /keys/<pattern> endpoint (per repo grep evidence).

    Returns the matched keys or an empty list. Defensive on transient errors —
    fail-soft to empty list to avoid aborting publication on a transient
    fabric-API hiccup, since the publisher's union set degrades gracefully:
    missing dormant set → just no dormant publication this cycle, not a fault
    (TW-8 will catch genuinely-stale records on next cycle).
    """
    try:
        r = urllib.request.urlopen(
            f"{fabric_url}/keys/{urllib.parse.quote(pattern, safe=':*')}",
            timeout=10,
        )
        d = json.loads(r.read())
        keys = d.get("keys", [])
        return keys if isinstance(keys, list) else []
    except Exception as e:
        log.warning("fabric_keys failed for pattern=%s: %s", pattern, e)
        return []


def http_fabric_set(
    key: str,
    value: Any,
    fabric_url: str = "http://127.0.0.1:8080/api/v1/redis",
) -> bool:
    body = json.dumps({
        "key": key,
        "value": json.dumps(value, default=_json_default)
        if not isinstance(value, str)
        else value,
    }).encode()
    req = urllib.request.Request(
        f"{fabric_url}/set",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10).read()
        return True
    except Exception as e:
        log.error("fabric_set failed key=%s err=%s", key, e)
        return False


def _json_default(o: Any) -> Any:
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, datetime):
        return iso_z(o)
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


# ─────────────────────────── Per-strategy publish ─────────────────────────────

def publish_envelope(
    strategy_id: str,
    envelope: Dict[str, Any],
    fabric_set: Callable[[str, Any], bool],
    dry_run: bool = False,
) -> bool:
    key = f"{KEY_STRATEGY_HEALTH_PREFIX}{strategy_id}{KEY_STRATEGY_HEALTH_SUFFIX}"
    if dry_run:
        log.info("[dry-run] would publish key=%s", key)
        return True
    return fabric_set(key, envelope)


# ─────────────────────────── Publisher state + audit ──────────────────────────

def build_publisher_state(
    run_started_at: datetime,
    run_finished_at: datetime,
    expected_count: int,
    published_count: int,
    counts_by_status: Dict[str, int],
    stale_count: int,
    missing_count: int,
    verdict: str,
    next_run_at: datetime,
) -> Dict[str, Any]:
    """All 12 architect-required fields per Phase B requirement B."""
    return {
        "wo": WO,
        "last_run_at_utc": iso_z(run_started_at),
        "last_success_at_utc": iso_z(run_finished_at)
        if verdict in ("GREEN", "AMBER")
        else None,
        "expected_strategy_count": expected_count,
        "published_strategy_count": published_count,
        "full_count": counts_by_status.get("FULL", 0),
        "limited_sample_count": counts_by_status.get("LIMITED_SAMPLE", 0),
        "insufficient_sample_count": counts_by_status.get("INSUFFICIENT_SAMPLE", 0),
        "stale_count": stale_count,
        "missing_count": missing_count,
        "verdict": verdict,
        "source_enum": SOURCE_ENUM,
        "timer_cadence": TIMER_CADENCE,
        "next_expected_run_at_utc": iso_z(next_run_at),
        "contract_compatibility": CONTRACT_VERSION,
    }


def build_per_run_audit(
    run_id: str,
    run_started_at: datetime,
    run_finished_at: datetime,
    expected_strategies: List[str],
    published_records: Dict[str, Dict[str, Any]],
    tripwire_results: List[TripwireResult],
    verdict: str,
    missing_strategies: List[str],
    new_strategies: List[str],
    counts_by_status: Dict[str, int],
    previous_run_audit_at: Optional[datetime],
    per_strategy_failures: List[Dict[str, Any]],
) -> Dict[str, Any]:
    duration = (run_finished_at - run_started_at).total_seconds()
    return {
        "wo": WO,
        "writer_version": SOURCE_ENUM,
        "run_id": run_id,
        "ran_at_utc": iso_z(run_started_at),
        "finished_at_utc": iso_z(run_finished_at),
        "duration_seconds": round(duration, 3),
        "strategies_expected": len(expected_strategies),
        "strategies_published": len(published_records),
        "strategies_status_only": counts_by_status.get("INSUFFICIENT_SAMPLE", 0),
        "strategies_skipped_blocked": sum(
            1 for s in expected_strategies if s not in published_records
        ),
        "strategies_missing": sorted(missing_strategies),
        "strategies_new": sorted(new_strategies),
        "counts_by_status": counts_by_status,
        "tripwires": [
            {
                "id": r.id,
                "name": r.name,
                "tier": r.tier,
                "passed": r.passed,
                "detail": r.detail,
            }
            for r in tripwire_results
        ],
        "verdict": verdict,
        "previous_run_ts": iso_z(previous_run_audit_at)
        if previous_run_audit_at
        else None,
        "per_strategy_failures": per_strategy_failures,
        "contract_compatibility": CONTRACT_VERSION,
    }


def build_fault_record(
    audit: Dict[str, Any],
    failed_tripwires: List[TripwireResult],
    now_utc_: datetime,
) -> Dict[str, Any]:
    return {
        "wo": WO,
        "writer_version": SOURCE_ENUM,
        "ts_utc": iso_z(now_utc_),
        "fault_code": "STRATEGY_HEALTH_PUBLICATION_TRIPWIRE_RED",
        "is_red": True,
        "run_id": audit.get("run_id"),
        "verdict": audit.get("verdict"),
        "failed_tripwires": [
            {"id": r.id, "name": r.name, "detail": r.detail}
            for r in failed_tripwires
        ],
        "strategies_missing": audit.get("strategies_missing", []),
        "detail": (
            "Strategy health publication run failed one or more RED tripwires. "
            "Consumers should treat advisory-only until next successful run."
        ),
    }


# ─────────────────────────── DB resolved-rows fetch (deferred to Phase B+) ────
# The actual DB query path requires runtime DB access. The DB-fetch wrapper
# below is mocked in tests. The live invocation in main() reads canonical
# rows from helios_strategy_signals (post-resolver) per V1 methodology.

def fetch_active_strategies_and_coverage(
    db_query: Callable[[str], List[Dict[str, Any]]],
    lookback_days: int = LOOKBACK_DAYS,
    now_utc_: Optional[datetime] = None,
) -> Tuple[List[str], Dict[str, StrategyCoverage]]:
    """Returns (expected_strategy_ids, per_strategy_coverage)."""
    if now_utc_ is None:
        now_utc_ = now_utc()
    window_start = now_utc_ - timedelta(days=lookback_days)
    sql = (
        "SELECT strategy_id, "
        "COUNT(*) AS total_fired, "
        "SUM(CASE WHEN entry_price IS NOT NULL AND sl_price IS NOT NULL "
        "          AND tp1_price IS NOT NULL THEN 1 ELSE 0 END) AS has_prices, "
        "SUM(CASE WHEN outcome IN ('TP1_HIT','TP2_HIT','SL_HIT','INVALIDATED','EXPIRED') "
        "          THEN 0 ELSE 1 END) AS pending, "
        "MIN(timestamp) AS earliest_fire_ts, "
        "MAX(timestamp) AS latest_fire_ts "
        f"FROM helios_strategy_signals WHERE timestamp >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}' AND fired=1 "
        "GROUP BY strategy_id ORDER BY strategy_id"
    )
    rows = db_query(sql)
    if rows is None:
        raise RuntimeError("DB_UNREACHABLE: fetch_active_strategies_and_coverage")
    coverage: Dict[str, StrategyCoverage] = {}
    for r in rows:
        sid = r["strategy_id"]
        coverage[sid] = StrategyCoverage(
            strategy_id=sid,
            total_fired=int(r.get("total_fired") or 0),
            has_prices=int(r.get("has_prices") or 0),
            missing_prices=int(r.get("total_fired") or 0) - int(r.get("has_prices") or 0),
            pending=int(r.get("pending") or 0),
            earliest_fire_ts=r.get("earliest_fire_ts"),
            latest_fire_ts=r.get("latest_fire_ts"),
        )
    expected = sorted(coverage.keys())
    return expected, coverage


def fetch_resolved_rows(
    db_query: Callable[[str], List[Dict[str, Any]]],
    strategy_id: str,
    lookback_days: int = LOOKBACK_DAYS,
    now_utc_: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    if now_utc_ is None:
        now_utc_ = now_utc()
    window_start = now_utc_ - timedelta(days=lookback_days)
    safe_sid = strategy_id.replace("'", "''")
    sql = (
        "SELECT outcome, "
        "CASE WHEN outcome IN ('TP1_HIT','TP2_HIT') THEN (tp1_price - entry_price) "
        "     WHEN outcome='SL_HIT' THEN (sl_price - entry_price) "
        "     ELSE 0 END AS signed_pnl_pts, "
        "outcome_resolved_at_utc "
        f"FROM helios_strategy_signals WHERE strategy_id='{safe_sid}' "
        f"AND timestamp >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}' AND fired=1 "
        "AND outcome IN ('TP1_HIT','TP2_HIT','SL_HIT','INVALIDATED','EXPIRED') "
        "AND entry_price IS NOT NULL AND sl_price IS NOT NULL AND tp1_price IS NOT NULL"
    )
    rows = db_query(sql)
    if rows is None:
        raise RuntimeError(f"DB_UNREACHABLE: fetch_resolved_rows for {strategy_id}")
    return rows


def compute_strategy_score(
    strategy_id: str, resolved_rows: List[Dict[str, Any]]
) -> StrategyScore:
    s = StrategyScore(strategy_id=strategy_id)
    wins = losses = neutrals = 0
    pnls: List[float] = []
    win_pnls: List[float] = []
    loss_pnls: List[float] = []
    last_resolved: Optional[str] = None
    for r in resolved_rows:
        outcome = r.get("outcome")
        if outcome in WIN_OUTCOMES:
            wins += 1
            pnl = float(r.get("signed_pnl_pts") or 0)
            pnls.append(pnl)
            win_pnls.append(pnl)
        elif outcome in LOSS_OUTCOMES:
            losses += 1
            pnl = float(r.get("signed_pnl_pts") or 0)
            pnls.append(pnl)
            loss_pnls.append(pnl)
        elif outcome in NEUTRAL_TERMINAL_OUTCOMES:
            neutrals += 1
        ts_ = r.get("outcome_resolved_at_utc")
        if ts_ and (last_resolved is None or str(ts_) > last_resolved):
            last_resolved = str(ts_)
    s.n_fires_resolved = wins + losses + neutrals
    s.win_count = wins
    s.loss_count = losses
    s.neutral_count = neutrals
    s.last_outcome_resolved_utc = last_resolved
    n_wl = wins + losses
    if n_wl > 0:
        s.wr = round(wins / n_wl, 4)
        s.expectancy_pts = (
            round(statistics.mean(pnls), 4) if pnls else 0.0
        )
        if win_pnls:
            s.avg_pnl_pts_win = round(statistics.mean(win_pnls), 4)
        if loss_pnls:
            s.avg_pnl_pts_loss = round(statistics.mean(loss_pnls), 4)
        if s.wr is not None and s.expectancy_pts is not None:
            components = compute_score_components(
                s.wr, s.expectancy_pts, s.n_fires_resolved
            )
            s.score = components["score"]
            s.score_components = components["components"]
    return s


# ─────────────────────────── Run orchestrator ─────────────────────────────────

def run_publisher(
    db_query: Callable[[str], List[Dict[str, Any]]],
    fabric_get: Callable[[str], Any],
    fabric_set: Callable[[str, Any], bool],
    fabric_keys: Optional[Callable[[str], List[str]]] = None,
    now_utc_: Optional[datetime] = None,
    dry_run: bool = False,
    cadence_hours: float = 4.0,
) -> Dict[str, Any]:
    """Single scheduled run.

    Returns the per-run audit dict (also written to fabric).
    Raises RuntimeError on fail-loud DB unreachable.

    Phase C remediation: discovers dormant strategies in fabric and publishes
    fresh INSUFFICIENT_SAMPLE envelopes for them so no stale POST_33 records
    persist at canonical :overall keys. Pass fabric_keys for full live behaviour;
    omit in tests with no dormant set.
    """
    if now_utc_ is None:
        now_utc_ = now_utc()

    run_started_at = now_utc_
    run_id = f"shp-{run_started_at.strftime('%Y%m%dT%H%M%SZ')}"
    log.info("publisher run %s started", run_id)

    # Step 1 — DB preflight + coverage fetch (fail-loud on DB unreachable)
    active_strategies, coverage = fetch_active_strategies_and_coverage(
        db_query, lookback_days=LOOKBACK_DAYS, now_utc_=run_started_at
    )
    window_start = run_started_at - timedelta(days=LOOKBACK_DAYS)
    window_end = run_started_at

    # Step 1b — Phase C remediation: discover existing-in-fabric strategies
    # and compute the union expected set. Dormant = in fabric but not in active.
    if fabric_keys is not None:
        existing_in_fabric = discover_existing_strategies_in_fabric(fabric_keys)
    else:
        existing_in_fabric = []
    expected_strategies, dormant_strategies = compute_expected_strategy_set(
        active_strategies, existing_in_fabric,
    )
    log.info(
        "active=%d existing_in_fabric=%d expected=%d dormant=%d",
        len(active_strategies), len(existing_in_fabric),
        len(expected_strategies), len(dormant_strategies),
    )

    # Step 2 — per-strategy fetch + score + classify + publish (active path)
    # PLUS dormant publish path for strategies with no fires in 90d
    published_records: Dict[str, Dict[str, Any]] = {}
    counts_by_status: Dict[str, int] = {
        "FULL": 0,
        "LIMITED_SAMPLE": 0,
        "INSUFFICIENT_SAMPLE": 0,
    }
    per_strategy_failures: List[Dict[str, Any]] = []
    dormant_published_count = 0
    for sid in expected_strategies:
        if sid in dormant_strategies:
            # Dormant: write fresh INSUFFICIENT_SAMPLE envelope (no DB fetch)
            envelope = build_dormant_envelope(
                strategy_id=sid,
                window_start=window_start,
                window_end=window_end,
                computed_at=run_started_at,
            )
            if publish_envelope(sid, envelope, fabric_set, dry_run=dry_run):
                published_records[sid] = envelope
                counts_by_status["INSUFFICIENT_SAMPLE"] += 1
                dormant_published_count += 1
            else:
                per_strategy_failures.append(
                    {"strategy_id": sid, "reason": "FABRIC_WRITE_FAULT_DORMANT"}
                )
            continue
        # Active path
        cov = coverage[sid]
        try:
            resolved_rows = fetch_resolved_rows(
                db_query, sid, lookback_days=LOOKBACK_DAYS, now_utc_=run_started_at
            )
        except RuntimeError as e:
            per_strategy_failures.append({"strategy_id": sid, "reason": str(e)})
            continue
        score = compute_strategy_score(sid, resolved_rows)
        eligibility = evaluate_full_eligibility(
            n_fires_resolved=score.n_fires_resolved,
            wr=score.wr,
            expectancy_pts=score.expectancy_pts,
        )
        envelope = build_envelope(
            coverage=cov,
            score=score,
            eligibility=eligibility,
            window_start=window_start,
            window_end=window_end,
            computed_at=run_started_at,
        )
        if publish_envelope(sid, envelope, fabric_set, dry_run=dry_run):
            published_records[sid] = envelope
            counts_by_status[envelope["health_status"]] = (
                counts_by_status.get(envelope["health_status"], 0) + 1
            )
        else:
            per_strategy_failures.append(
                {"strategy_id": sid, "reason": "FABRIC_WRITE_FAULT"}
            )

    missing_strategies = sorted(
        set(expected_strategies) - set(published_records.keys())
    )
    new_strategies: List[str] = []  # populated by TW-6 logic below

    run_finished_at = now_utc()

    # Step 3 — read previous audit for TW-7 canary
    prev_audit = fabric_get(KEY_PUBLISHER_AUDIT_LATEST)
    prev_audit_at: Optional[datetime] = None
    if isinstance(prev_audit, dict) and prev_audit.get("ran_at_utc"):
        try:
            prev_audit_at = datetime.fromisoformat(
                prev_audit["ran_at_utc"].replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            prev_audit_at = None

    # Step 4 — run 8 tripwires (TW-8 only if fabric_keys + fabric_get available)
    if fabric_keys is not None:
        # Use fabric_get as envelope reader for TW-8
        verdict, tripwire_results = run_all_tripwires(
            expected_strategies=expected_strategies,
            published_records=published_records,
            now_utc_=run_finished_at,
            last_audit_at_utc=prev_audit_at,
            fabric_keys=fabric_keys,
            fabric_get_envelope=fabric_get,
        )
    else:
        verdict, tripwire_results = run_all_tripwires(
            expected_strategies=expected_strategies,
            published_records=published_records,
            now_utc_=run_finished_at,
            last_audit_at_utc=prev_audit_at,
        )
    # TW-6 surfaces new_strategies
    for r in tripwire_results:
        if r.id == "TW-6" and not r.passed:
            new_strategies = sorted(
                set(published_records.keys()) - set(expected_strategies)
            )

    if per_strategy_failures and verdict == "GREEN":
        verdict = "AMBER"

    # Step 5 — build audit + state
    audit = build_per_run_audit(
        run_id=run_id,
        run_started_at=run_started_at,
        run_finished_at=run_finished_at,
        expected_strategies=expected_strategies,
        published_records=published_records,
        tripwire_results=tripwire_results,
        verdict=verdict,
        missing_strategies=missing_strategies,
        new_strategies=new_strategies,
        counts_by_status=counts_by_status,
        previous_run_audit_at=prev_audit_at,
        per_strategy_failures=per_strategy_failures,
    )
    next_run_at = run_finished_at + timedelta(hours=cadence_hours)
    state = build_publisher_state(
        run_started_at=run_started_at,
        run_finished_at=run_finished_at,
        expected_count=len(expected_strategies),
        published_count=len(published_records),
        counts_by_status=counts_by_status,
        stale_count=sum(
            1 for r in tripwire_results if r.id == "TW-2" and not r.passed
        ),
        missing_count=len(missing_strategies),
        verdict=verdict,
        next_run_at=next_run_at,
    )

    # Step 6 — write audit + state + fault if RED
    if not dry_run:
        audit_key = (
            KEY_PUBLISHER_AUDIT_PREFIX + run_started_at.strftime("%Y%m%dT%H%M%SZ")
        )
        fabric_set(audit_key, audit)
        fabric_set(KEY_PUBLISHER_AUDIT_LATEST, audit)
        fabric_set(KEY_PUBLISHER_STATE, state)
        if verdict == "RED":
            failed = [r for r in tripwire_results if r.tier == "RED" and not r.passed]
            fault = build_fault_record(audit, failed, run_finished_at)
            fault_key = (
                KEY_PUBLISHER_FAULT_PREFIX + run_started_at.strftime("%Y-%m-%d")
            )
            existing_faults = fabric_get(fault_key)
            faults_list = (
                existing_faults if isinstance(existing_faults, list) else []
            )
            faults_list.append(fault)
            fabric_set(fault_key, faults_list)

    log.info(
        "publisher run %s done verdict=%s published=%d expected=%d",
        run_id, verdict, len(published_records), len(expected_strategies),
    )
    return audit


# ─────────────────────────── CLI entry ─────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="R2D2 scheduled strategy_health publisher"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip all fabric writes; log decisions only.")
    parser.add_argument("--fabric-url",
                        default=os.environ.get(
                            "R2D2_FABRIC_URL",
                            "http://127.0.0.1:8080/api/v1/redis",
                        ))
    args = parser.parse_args(argv)

    # Build live wrappers
    def _db_query_via_ssh(sql: str) -> Optional[List[Dict[str, Any]]]:
        # Mirrors _common.remote_query — kept local so the publisher is
        # self-contained and importable for tests.
        sys.path.insert(0, "/opt/r2d2/maintenance")
        sys.path.insert(0, "/srv/r2d2/maintenance")
        try:
            from _common import remote_query  # type: ignore
            return remote_query(sql)
        except Exception as e:
            log.error("remote_query import failed: %s", e)
            return None

    def _fabric_get(key: str) -> Any:
        return http_fabric_get(key, fabric_url=args.fabric_url)

    def _fabric_set(key: str, value: Any) -> bool:
        return http_fabric_set(key, value, fabric_url=args.fabric_url)

    def _fabric_keys(pattern: str) -> List[str]:
        return http_fabric_keys(pattern, fabric_url=args.fabric_url)

    try:
        audit = run_publisher(
            db_query=_db_query_via_ssh,
            fabric_get=_fabric_get,
            fabric_set=_fabric_set,
            fabric_keys=_fabric_keys,
            dry_run=args.dry_run,
        )
    except RuntimeError as e:
        log.error("FAIL_LOUD: %s", e)
        return 2
    except Exception as e:
        log.exception("publisher run crashed: %s", e)
        return 2

    verdict = audit.get("verdict")
    print(json.dumps(audit, default=_json_default, indent=2))
    if verdict == "RED":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
