"""Four-axis control-status resolver.

Implements PBG-CTRL-005 (enforcement, verification and applicability are separate facts) and
PBG-FWK-005 (the six conditions under which a mandatory control may never be GREEN).

The overall outcome is CALCULATED here and nowhere else. Any caller that asserts an outcome
instead of resolving one is bypassing the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

# --- Axis 1: does a mechanism actively constrain the action? -------------------------------- #
ENFORCED = "ENFORCED"
PARTIALLY_ENFORCED = "PARTIALLY_ENFORCED"
NOT_ENFORCED = "NOT_ENFORCED"
ENFORCEMENT_UNSUPPORTED = "UNSUPPORTED"
ENFORCEMENT_VALUES = {ENFORCED, PARTIALLY_ENFORCED, NOT_ENFORCED, ENFORCEMENT_UNSUPPORTED}

# --- Axis 2: was the outcome checked against the authentic target? --------------------------- #
VERIFIED = "VERIFIED"
PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
NOT_VERIFIED = "NOT_VERIFIED"
VERIFICATION_UNSUPPORTED = "UNSUPPORTED"
VERIFICATION_VALUES = {VERIFIED, PARTIALLY_VERIFIED, NOT_VERIFIED, VERIFICATION_UNSUPPORTED}

# --- Axis 3: is the control required for this authority record? ------------------------------ #
APPLICABLE = "APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"
EXCEPTED = "EXCEPTED"
APPLICABILITY_VALUES = {APPLICABLE, NOT_APPLICABLE, EXCEPTED}

# --- Axis 4: calculated ---------------------------------------------------------------------- #
PASS = "PASS"
PASS_NOT_APPLICABLE = "PASS_NOT_APPLICABLE"
PASS_EXCEPTED = "PASS_EXCEPTED"
AMBER = "AMBER"
FAIL = "FAIL"
BYPASS = "BYPASS"

#: Outcomes that a report may present as a clean result. Everything else is a named non-pass
#: and must be rendered as such (PBG-FWK-002).
CLEAN_OUTCOMES = {PASS, PASS_NOT_APPLICABLE}

#: PBG-FWK-005 — the six conditions. A mandatory control hitting any of these is BYPASS.
BYPASS_CONDITIONS = (
    "enforcement_unavailable_and_unverified",
    "verification_did_not_reach_authentic_target",
    "required_evidence_missing",
    "configuration_removed_control",
    "wrapper_transformed_state",
    "expired_exception_in_use",
)


class OutcomeModelError(ValueError):
    """Raised when a resolution request is internally incoherent."""


@dataclass
class Resolution:
    """A single control resolved for a single authority record on a single host."""

    control_id: str
    enforcement_status: str
    verification_status: str
    applicability_status: str
    mandatory: bool
    enforcement_note: str = ""
    verification_note: str = ""
    applicability_derivation: str = ""
    bypass_conditions: list[str] = field(default_factory=list)
    exception_expires_utc: str | None = None
    evidence_refs: list[str] = field(default_factory=list)

    # -- validation ------------------------------------------------------------------------- #
    def _validate(self) -> None:
        if self.enforcement_status not in ENFORCEMENT_VALUES:
            raise OutcomeModelError(f"{self.control_id}: bad enforcement_status {self.enforcement_status!r}")
        if self.verification_status not in VERIFICATION_VALUES:
            raise OutcomeModelError(f"{self.control_id}: bad verification_status {self.verification_status!r}")
        if self.applicability_status not in APPLICABILITY_VALUES:
            raise OutcomeModelError(f"{self.control_id}: bad applicability_status {self.applicability_status!r}")

        # PBG-FWK-002: "partially" without a named remainder is invalid.
        if self.enforcement_status == PARTIALLY_ENFORCED and not self.enforcement_note.strip():
            raise OutcomeModelError(
                f"{self.control_id}: PARTIALLY_ENFORCED requires enforcement_note naming the "
                f"portion not enforced (PBG-FWK-002)"
            )
        if self.verification_status == PARTIALLY_VERIFIED and not self.verification_note.strip():
            raise OutcomeModelError(
                f"{self.control_id}: PARTIALLY_VERIFIED requires verification_note naming the "
                f"part of the authentic target not reached (PBG-FWK-002)"
            )
        # PBG-CTRL-003: a NOT_APPLICABLE control must show why.
        if self.applicability_status == NOT_APPLICABLE and not self.applicability_derivation.strip():
            raise OutcomeModelError(
                f"{self.control_id}: NOT_APPLICABLE requires a recorded derivation (PBG-CTRL-003)"
            )
        for cond in self.bypass_conditions:
            if cond not in BYPASS_CONDITIONS:
                raise OutcomeModelError(f"{self.control_id}: unknown bypass condition {cond!r}")

    # -- resolution ------------------------------------------------------------------------- #
    def overall_outcome(self, now: datetime | None = None) -> str:
        """Calculate the outcome. Never asserted by a caller."""
        self._validate()

        # PBG-FWK-005 first: a named bypass condition overrides everything below it.
        if self.mandatory and self.bypass_conditions:
            return BYPASS

        if self.applicability_status == NOT_APPLICABLE:
            return PASS_NOT_APPLICABLE

        if self.applicability_status == EXCEPTED:
            if self.exception_expires_utc is None:
                raise OutcomeModelError(
                    f"{self.control_id}: EXCEPTED requires exception_expires_utc — an exception "
                    f"with no expiry is invalid"
                )
            now = now or datetime.now(timezone.utc)
            expiry = _parse_utc(self.exception_expires_utc)
            if expiry <= now:
                # An expired exception still in use is a bypass, not a warning.
                return BYPASS if self.mandatory else FAIL
            return PASS_EXCEPTED

        # APPLICABLE from here.
        unsupported = (
            self.enforcement_status == ENFORCEMENT_UNSUPPORTED
            or self.verification_status == VERIFICATION_UNSUPPORTED
        )
        partial = (
            self.enforcement_status == PARTIALLY_ENFORCED
            or self.verification_status == PARTIALLY_VERIFIED
        )
        satisfied = self.enforcement_status == ENFORCED or self.verification_status == VERIFIED

        if satisfied and not partial and not unsupported:
            return PASS
        if partial or unsupported:
            # A gap is AMBER, never a pass — even when the other axis is clean (PBG-FWK-002).
            return AMBER
        return FAIL

    def as_record(self, now: datetime | None = None) -> dict:
        """The attestation shape. Includes the axes, never just the outcome."""
        return {
            "control_id": self.control_id,
            "mandatory": self.mandatory,
            "enforcement_status": self.enforcement_status,
            "enforcement_note": self.enforcement_note,
            "verification_status": self.verification_status,
            "verification_note": self.verification_note,
            "applicability_status": self.applicability_status,
            "applicability_derivation": self.applicability_derivation,
            "bypass_conditions": list(self.bypass_conditions),
            "evidence_refs": list(self.evidence_refs),
            "overall_outcome": self.overall_outcome(now=now),
        }


def _parse_utc(value: str) -> datetime:
    """Parse an ISO-8601 UTC timestamp. Naive values are rejected — PBG-DATA-001."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise OutcomeModelError(f"timestamp {value!r} is timezone-naive; UTC required")
    return parsed.astimezone(timezone.utc)


def verdict(resolutions: list[Resolution], now: datetime | None = None) -> dict:
    """Roll a set of resolutions into an overall close verdict.

    A single BYPASS or FAIL on a mandatory control sinks the whole verdict. AMBER never
    aggregates away into GREEN (PBG-FWK-002).
    """
    records = [r.as_record(now=now) for r in resolutions]
    outcomes = {r["control_id"]: r["overall_outcome"] for r in records}

    mandatory_bad = [
        cid
        for cid, out in outcomes.items()
        if out in (BYPASS, FAIL)
        and next(r for r in records if r["control_id"] == cid)["mandatory"]
    ]
    ambers = [cid for cid, out in outcomes.items() if out == AMBER]

    if mandatory_bad:
        overall = "RED"
    elif ambers:
        overall = "AMBER"
    elif any(out not in CLEAN_OUTCOMES and out != PASS_EXCEPTED for out in outcomes.values()):
        overall = "AMBER"
    else:
        overall = "GREEN"

    return {
        "overall": overall,
        "controls": records,
        "counts": {
            "total": len(records),
            "pass": sum(1 for o in outcomes.values() if o == PASS),
            "pass_not_applicable": sum(1 for o in outcomes.values() if o == PASS_NOT_APPLICABLE),
            "pass_excepted": sum(1 for o in outcomes.values() if o == PASS_EXCEPTED),
            "amber": len(ambers),
            "fail": sum(1 for o in outcomes.values() if o == FAIL),
            "bypass": sum(1 for o in outcomes.values() if o == BYPASS),
        },
        "blocking": mandatory_bad,
        "gaps": ambers,
    }
