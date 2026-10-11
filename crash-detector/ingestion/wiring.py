"""Wire real ingestion-store readings into the engine's two dials (CERBERUS WO-1.3).

Reads the ratified mapping (``governance/mapping/indicator_mapping.yaml``), the ingredient
catalog and the PROVISIONAL scaling (``deploy/indicator-scaling.json``) and builds a
``ConfigSnapshot`` plus the ``ObservationRecord`` list ``evaluate`` consumes. It lives
outside ``src/`` for the same reason the rest of ingestion does: it reads a file store and
YAML, and the application tree does neither.

WHICH INDICATORS ARE LIVE. Two kinds, and only these:

* DIRECT: the catalog delivers the indicator's WHOLE scored quantity (at least one ``DIRECT``
  ingredient and no ``COMPONENT`` ingredient).
* DERIVED (WO-1.5): the catalog delivers COMPONENT ingredients and ``DERIVED_FROM`` below names
  which, in which role. The ENGINE (``crash_detector.engine.derivations``) computes the figure
  from the stored readings; this module only fetches those readings and hands them over.

Everything else (the partial SLOOS leg, the intractable five, ``gold_real_rate_cross`` and the
held bindings below) is PENDING: it gets no observation, so a dial that needs it is Unknown and a
dial that merely lists it is Degraded. Nothing is defaulted, estimated or carried forward.

TWO DIALS, NEVER BLENDED. One ``ModelSpec`` per dial, each over only the indicators bound to
that dial, each with its own band for that dial's polarity.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from crash_detector.dials.dialset import DialSet
from crash_detector.engine.derivations import DERIVATIONS, DerivationKind, DerivationUnavailable, derive
from crash_detector.engine.config import ConfigSnapshot, DialSpec
from crash_detector.engine.evaluate import evaluate
from crash_detector.engine.model import (
    DeclaredParameter,
    MappingKind,
    ModelProvenance,
    ModelRegistry,
    ModelSpec,
)
from crash_detector.observations import OK, ObservationRecord
from crash_detector.source_registry import (
    Criticality,
    DialBinding,
    IndicatorMapping,
    IndicatorMappingRegistry,
    MappingProvenance,
    Polarity,
    ProvisionalTier,
    SourceRecord,
    SourceRegistry,
    WiringState,
)
from crash_detector.staleness import RelevanceWindow
from crash_detector.time_utc import ensure_utc

from ingestion.adapters import as_of_for
from ingestion.catalog import INGREDIENTS, NOT_TRACTABLE, PARTIAL, Ingredient, window_seconds
from ingestion.store import SqliteStore

__all__ = ["Wiring", "build_wiring", "coverage", "observations_from_store", "evaluate_from_store",
           "DERIVED_FROM", "HELD_BINDINGS", "derive_from_store", "derived_as_of"]

ROOT = Path(__file__).resolve().parents[1]
MAPPING_YAML = ROOT / "governance" / "mapping" / "indicator_mapping.yaml"
SCALING_JSON = ROOT / "deploy" / "indicator-scaling.json"

#: The tier -> weight rule of PO-DECISIONS-0025 r1 (x3/x2/x1). Provisional, pending backtest.
TIER_WEIGHT = {1: 3.0, 2: 2.0, 3: 1.0}
TIER_ENUM = {1: ProvisionalTier.X3, 2: ProvisionalTier.X2, 3: ProvisionalTier.X1}
POLARITY = {
    "high_is_worse": Polarity.RISING_MEANS_MORE_RISK,
    "low_is_better": Polarity.RISING_MEANS_MORE_RISK,
    "low_is_worse": Polarity.RISING_MEANS_LESS_RISK,
    "high_is_better": Polarity.RISING_MEANS_LESS_RISK,
}
DIALS = ("equity_crash", "monetary_debasement")

#: Derived indicator -> the catalog ingredients that fill the engine derivation's roles, in the
#: order ``DERIVATIONS[...].roles`` lists them. The calculation itself is the engine's.
DERIVED_FROM: dict = {
    "breadth_rsp_spy": ("yahoo.RSP", "yahoo.SPY"),
    "credit_stress_hyg_lqd": ("yahoo.HYG", "yahoo.LQD"),
    "copper_gold": ("yahoo.HG=F", "yahoo.GC=F"),
    "vix_term_structure": ("cboe.VIX", "cboe.VIX3M"),
    "spx_vs_200dma": ("yahoo.^GSPC",),
    "shiller_cape": ("multpl.shiller_pe_table",),
    # WO-1.6 (substitutions recorded in ingestion.catalog.SUBSTITUTED_FEEDS):
    "buffett_indicator": ("fred.NCBEILQ027S", "fred.GDP"),
    "fiscal_dominance": ("fred.WALCL", "fred.CPILFESL"),
}

#: (indicator, dial) bindings that are NOT scored although the indicator is live on its other dial.
HELD_BINDINGS: dict = {
    ("copper_gold", "monetary_debasement"): "HELD: the ratified row declares polarity `low_is_better` for this dial "
    "while its own comment says falling copper/gold = gold strength = debasement. Under every other row's "
    "vocabulary ('worse' = more debasement) that comment would be `low_is_worse`. The two cannot both be right "
    "and which is intended is the Owner's call; scoring either way would be a guess on a x2 weight.",
}

#: The as-of rule for a DERIVED figure whose date is the quarter START (the engine returns the components' own
#: date). Everything else is aged from its own date.
DERIVED_AS_OF_RULE: dict = {"buffett_indicator": "quarter_end"}


def derived_as_of(indicator: str, observation_date: str, now_utc: datetime) -> datetime:
    """The instant a derived figure refers to (see :func:`ingestion.adapters.as_of_for`)."""
    return as_of_for(observation_date, DERIVED_AS_OF_RULE.get(indicator, "obs_date"), now_utc)


#: Newest source periods fetched per component: enough to find the latest date both share.
DERIVATION_LOOKBACK = 10

#: Why a derived indicator that is NOT wired cannot be.
DERIVATION_BLOCKED: dict = {
    "gold_real_rate_cross": "BLOCKED on definition (re-examined WO-1.6, unchanged): the row says 'gold vs 10y TIPS "
    "divergence, normalised 0-100'. Neither 'divergence' (a residual? a rolling correlation break? a spread of "
    "z-scores?) nor the 0-100 normalisation (percentile of what window?) is defined. Spot gold "
    "(LBMA) does not touch that: it is the DEFINITION that is missing, not an input (and LBMA is itself currently "
    "refusing this host, see gold_spot). The legacy ARGUS engine has no gold-vs-TIPS tell to port (its two gold tells are SPX-in-gold and a gold/SPX "
    "correlation flip: different quantities). Any formula chosen here would be invented product meaning (CD-D-005). "
    "Needs an Owner definition.",
}


@dataclass(frozen=True)
class Wiring:
    snapshot: ConfigSnapshot
    #: indicator id -> the catalog ingredient that is its whole scored quantity.
    ingredient_for: dict
    #: indicator id -> the component ingredients (in role order) the ENGINE derives it from.
    derived_for: dict
    #: (indicator id, dial id) -> why a live indicator is not scored on that dial.
    held: dict
    #: indicator id -> why it is not live. Never scored, never defaulted.
    pending: dict

    @property
    def live_ids(self) -> set:
        return set(self.ingredient_for) | set(self.derived_for)


def _rows() -> list:
    return yaml.safe_load(MAPPING_YAML.read_text(encoding="utf-8"))["indicators"]


def _direct_ingredients() -> dict:
    """indicator id -> its single DIRECT ingredient, only if no COMPONENT ingredient serves it."""
    direct: dict[str, Ingredient] = {}
    component: set[str] = set()
    for ing in INGREDIENTS:
        for indicator in ing.serves:
            if ing.completes == "DIRECT":
                direct.setdefault(indicator, ing)
            else:
                component.add(indicator)
    return {k: v for k, v in direct.items() if k not in component}


def _polarities(row: dict) -> dict:
    dials = row["dial"] if isinstance(row["dial"], list) else [row["dial"]]
    pol = row["polarity"]
    return {d: (pol[d] if isinstance(pol, dict) else pol) for d in dials}


def _pending_reason(row: dict, all_serving: dict) -> str:
    sid = row["id"]
    if sid in NOT_TRACTABLE:
        return "NOT_TRACTABLE: " + NOT_TRACTABLE[sid]
    if sid in PARTIAL:
        return "PARTIAL: " + PARTIAL[sid]
    if sid in DERIVATION_BLOCKED:
        return DERIVATION_BLOCKED[sid]
    if sid in all_serving:
        return "DERIVED: component ingredients are ingested but no engine derivation is registered for it"
    return "UNWIRED: no ingestion ingredient serves this indicator"


def build_wiring(config_snapshot_id: str = "cfg-wo-1.3-live") -> Wiring:
    rows = _rows()
    scaling = json.loads(SCALING_JSON.read_text(encoding="utf-8"))
    direct = _direct_ingredients()
    by_id = {ing.source_id: ing for ing in INGREDIENTS}
    derived = {}
    for indicator, source_ids in DERIVED_FROM.items():
        if indicator not in DERIVATIONS or len(source_ids) != len(DERIVATIONS[indicator].roles):
            raise ValueError(f"{indicator}: DERIVED_FROM does not match the engine derivation's roles")
        parts = tuple(by_id[sid] for sid in source_ids)
        if any(indicator not in ing.serves for ing in parts):
            raise ValueError(f"{indicator}: a named component ingredient does not serve it in the catalog")
        derived[indicator] = parts
    serving = {i for ing in INGREDIENTS for i in ing.serves}
    live = [r for r in rows
            if (r["id"] in direct or r["id"] in derived) and r.get("status") != "registration_pending"]
    live_ids = {r["id"] for r in live}
    pending = {r["id"]: _pending_reason(r, serving) for r in rows if r["id"] not in live_ids}

    mappings, sources, cache = [], [], {}
    for r in live:
        pols = {d: p for d, p in _polarities(r).items() if (r["id"], d) not in HELD_BINDINGS}
        parts = derived.get(r["id"])
        ing = direct[r["id"]] if parts is None else parts[0]
        cadence = max(i.poll_seconds for i in parts) if parts else ing.poll_seconds
        adapter_id = ing.source_id if parts is None else f"engine.derive.{DERIVATIONS[r['id']].kind.value}"
        stands_for = ing.stands_for if parts is None else (
            f"derived by the engine ({DERIVATIONS[r['id']].kind.value}) from " + ", ".join(i.source_id for i in parts))
        # Criticality is per SOURCE; the scaling file's `required` flags must agree across dials.
        flags = {bool(scaling[d][r["id"]]["required"]) for d in pols if r["id"] in scaling[d]}
        if len(flags) != 1:
            raise ValueError(f"{r['id']}: scaling must declare the same `required` on every dial it binds")
        required = flags.pop()
        if required and len(pols) != 1:
            raise ValueError(f"{r['id']}: a two-dial indicator cannot be REQUIRED (criticality is per source)")
        cache[r["id"]] = (r, pols, required)
        mappings.append(IndicatorMapping(
            source_id=r["id"],
            dial_bindings=tuple(DialBinding(dial_id=d, polarity=POLARITY[p]) for d, p in pols.items()),
            provisional_tier=TIER_ENUM[r["tier"]],
            staleness_window=RelevanceWindow(seconds=window_seconds(r["id"], r["staleness_window_seconds"])),
            provenance=MappingProvenance(
                ruling_ref="PO-DECISIONS-0025",
                mapping_artefact="governance/mapping/indicator_mapping.yaml",
                mapping_version=str(yaml.safe_load(MAPPING_YAML.read_text(encoding="utf-8"))["schema_version"]),
                stands_for=f"{r['name']}: {stands_for}",
            ),
            wiring_state=WiringState.WIRED,
        ))
        sources.append(SourceRecord(
            source_id=r["id"], adapter_id=adapter_id, cadence_seconds=int(cadence),
            criticality=Criticality.REQUIRED if required else Criticality.CONTRIBUTING,
            stands_for=stands_for or ing.source_id,
        ))

    specs, models = [], []
    for dial in DIALS:
        ids = [r["id"] for r in live if dial in cache[r["id"]][1]]
        req = tuple(i for i in ids if cache[i][2])
        con = tuple(i for i in ids if not cache[i][2])
        params = []
        for i in ids:
            band = scaling[dial][i]
            params += [
                DeclaredParameter(name=f"calm::{i}", value=float(band["calm"])),
                DeclaredParameter(name=f"stress::{i}", value=float(band["stress"])),
                DeclaredParameter(name=f"weight::{i}", value=TIER_WEIGHT[cache[i][0]["tier"]]),
            ]
        model_id = f"banded-weighted-mean::{dial}::v0-provisional"
        models.append(ModelSpec(
            model_id=model_id, dial_id=dial, required_input_ids=req, contributing_input_ids=con,
            mapping=MappingKind.BANDED_WEIGHTED_MEAN, parameters=tuple(params),
            provenance=ModelProvenance(
                stands_for="Weighted mean of linearly banded indicator stresses for this dial only",
                account="deploy/indicator-scaling.json (bands) and the ratified mapping's tiers (weights); "
                        "ALL PROVISIONAL, uncalibrated, no backtest run (PO-DECISIONS-0025 r3)",
                decided_by="Owner direction 2026-10-11 (WO-1.3); numbers are placeholders pending backtest",
            ),
        ))
        specs.append(DialSpec(dial_id=dial, required_input_ids=req, contributing_input_ids=con, model_ref=model_id))

    snapshot = ConfigSnapshot(
        config_snapshot_id=config_snapshot_id,
        dial_specs=tuple(specs),
        staleness_window_seconds=900.0,
        source_registry=SourceRegistry(sources=tuple(sources)),
        model_registry=ModelRegistry(models=tuple(models)),
        indicator_mapping_registry=IndicatorMappingRegistry(mappings=tuple(mappings)),
    )
    return Wiring(snapshot=snapshot,
                  ingredient_for={i: direct[i] for i in live_ids if i in direct},
                  derived_for={i: derived[i] for i in live_ids if i in derived},
                  held=dict(HELD_BINDINGS), pending=pending)


def derive_from_store(store: SqliteStore, wiring: Wiring) -> dict:
    """indicator id -> the engine's ``Derived``, or the plain-text reason it cannot be computed.

    Fetches the component readings and hands them to ``crash_detector.engine.derivations``;
    nothing is computed here. A ratio gets the newest few source periods of each component so
    the engine can find the latest date both share; a series derivation needs only the newest.
    """
    out: dict = {}
    for indicator, parts in sorted(wiring.derived_for.items()):
        spec = DERIVATIONS[indicator]
        depth = DERIVATION_LOOKBACK if spec.kind is DerivationKind.RATIO else 1
        inputs = {role: store.recent_readings(ing.source_id, depth) for role, ing in zip(spec.roles, parts)}
        try:
            out[indicator] = derive(indicator, inputs)
        except DerivationUnavailable as why:
            out[indicator] = str(why)
    return out


def observations_from_store(store: SqliteStore, wiring: Wiring, observed_utc: datetime) -> list:
    """One OK observation per live indicator that has a finite numeric stored reading.

    A missing reading, or a value that is not a plain finite number, yields NO observation:
    the engine then sees absence, never a default. A derived indicator yields one only when the
    engine could compute it from real stored readings.
    """
    out = []
    for indicator, derived in sorted(derive_from_store(store, wiring).items()):
        if isinstance(derived, str):
            continue
        out.append(ObservationRecord(
            source_id=indicator,
            observed_utc=ensure_utc(observed_utc),
            outcome=OK(payload={"unit": derived.unit, "observation_date": derived.observation_date,
                                "value": derived.value},
                       source_as_of_utc=derived_as_of(indicator, derived.observation_date, observed_utc)),
        ))
    for indicator, ing in sorted(wiring.ingredient_for.items()):
        reading = store.latest_reading(ing.source_id)
        if reading is None:
            continue
        payload = reading["payload"]
        value = payload.get("value")
        if type(value) not in (int, float) or not math.isfinite(value):
            continue
        out.append(ObservationRecord(
            source_id=indicator,
            observed_utc=ensure_utc(observed_utc),
            outcome=OK(payload=payload,
                       source_as_of_utc=datetime.fromisoformat(reading["source_as_of_utc"].replace("Z", "+00:00"))),
        ))
    return out


def evaluate_from_store(store: SqliteStore, now_utc: datetime, wiring: "Wiring | None" = None) -> DialSet:
    wiring = wiring or build_wiring()
    return evaluate(observations_from_store(store, wiring, now_utc), wiring.snapshot, now_utc)


def coverage(wiring: Wiring) -> dict:
    """Per dial: the share of the ratified nominal tier weight that is WIRED (Auditor F1, WO-1.3).

    A dial built from only the live indicators reads as a full ``Value`` because the pending
    rows are not in its spec. This is the disclosure that closes that gap for any consumer: it
    counts every ratified row bound to the dial, live or not, and names the pending ones.
    """
    out = {}
    for dial in DIALS:
        total = live = 0.0
        pending = []
        for r in _rows():
            if dial not in _polarities(r):
                continue
            w = TIER_WEIGHT[r["tier"]]
            total += w
            if r["id"] in wiring.live_ids and (r["id"], dial) not in wiring.held:
                live += w
            else:
                pending.append(r["id"])
        out[dial] = {"wired_weight": live, "nominal_weight": total,
                     "fraction": live / total if total else 0.0, "pending": pending}
    return out
