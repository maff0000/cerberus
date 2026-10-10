"""CD-RT-009 — regime-aware staleness. **The same age that passes in calm fails in stress.**

The declared command for ``CD-AC-009`` (``required-tests.yaml``,
``contracts/execution/CD-RT-009-REGIME-AWARE-STALENESS.md``).

**THE PROPERTY IS A RELATION BETWEEN TWO REGIMES, NOT A CONSTANT**, so every assertion here
that a thing FAILS in stress has, beside it, the assertion that the SAME thing PASSES in
calm. A refusal with no admitting arm is indistinguishable from a guard that refuses
everything, and this project has made that mistake and named it (``CD-D-079``).

**THE POLICIES IN THIS FILE ARE OBVIOUSLY SYNTHETIC AND ARE THE TEST'S OWN.** They are not
a default, not a recommendation and not a product quantity: ``crash_detector.regime``
declares no policy at all, and one of the tests below asserts that by scanning the module.
The numbers here were picked to make the arithmetic legible in a failure message and mean
nothing outside this file.

**NO SOURCE IS REGISTERED BY ANYTHING IN THIS FILE** (``Q25``, ``CD-PL-F154``). Staleness is
a property of an age and a window; it needs no ingredient, and nothing here constructs a
``SourceRecord`` or touches ``raw.source_registry``.
"""

from __future__ import annotations

import ast
import pathlib
from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.regime import (
    REGIME_CALM,
    REGIME_ORDER,
    REGIME_STRESS,
    RegimeNotDeclared,
    RegimeStalenessPolicy,
    StalenessPolicyIncoherent,
)
from crash_detector.staleness import (
    STALENESS_WINDOW_CEILING_SECONDS,
    FreshnessEvidence,
    FreshnessNotEstablished,
    StalenessWindow,
    StalenessWindowOutOfRange,
)

#: A policy whose only job is to be legible. 600 s calm, 120 s stress.
SYNTHETIC_POLICY = {REGIME_CALM: 600.0, REGIME_STRESS: 120.0}

NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)

#: THE ONE AGE THE CRITERION IS ABOUT: strictly between the two windows, so it is inside
#: calm's and outside stress's. Every other number in this file is scenery.
THE_AGE_SECONDS = 300.0


def _observation_aged(seconds: float) -> datetime:
    return NOW - timedelta(seconds=seconds)


# --- THE CRITERION, BOTH ARMS ------------------------------------------------------------ #

def test_the_same_age_passes_in_calm():
    """THE ADMITTING ARM. Without it the refusal below proves nothing."""
    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    evidence = FreshnessEvidence(
        as_of_utc=_observation_aged(THE_AGE_SECONDS),
        observed_at_utc=NOW,
        window=policy.window_for(REGIME_CALM),
    )
    assert evidence.age_seconds == THE_AGE_SECONDS
    assert evidence.window.seconds == 600.0


def test_the_same_age_fails_in_stress():
    """THE REFUSING ARM. Same age, same instant, same constructor — only the regime moved."""
    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    with pytest.raises(FreshnessNotEstablished) as refusal:
        FreshnessEvidence(
            as_of_utc=_observation_aged(THE_AGE_SECONDS),
            observed_at_utc=NOW,
            window=policy.window_for(REGIME_STRESS),
        )
    # Read from the TEXT and not from the exception type alone: two refusals for different
    # reasons look identical in a summary (the CD-ENG-WO2R3-F12 standard).
    assert "300.0 seconds old" in str(refusal.value)
    assert "120.0 seconds" in str(refusal.value)
    assert "STALE" in str(refusal.value)


def test_the_two_arms_differ_ONLY_by_the_regime_argument():
    """The contrast is one argument wide, asserted rather than left to be read off above.

    If the two arms differed in the age, the instant or the constructor, the pair would
    demonstrate something other than the criterion.
    """
    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    as_of = _observation_aged(THE_AGE_SECONDS)

    def evidence_under(regime: str) -> FreshnessEvidence:
        return FreshnessEvidence(
            as_of_utc=as_of, observed_at_utc=NOW, window=policy.window_for(regime)
        )

    assert evidence_under(REGIME_CALM).age_seconds == THE_AGE_SECONDS
    with pytest.raises(FreshnessNotEstablished):
        evidence_under(REGIME_STRESS)


def test_the_window_actually_tightens():
    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    assert (
        policy.window_for(REGIME_STRESS).seconds
        < policy.window_for(REGIME_CALM).seconds
    )


def test_the_boundary_is_inclusive_on_both_sides_of_the_same_rule():
    """An age exactly at the window is covered; one microsecond past it is not.

    Asserted for BOTH regimes with each regime's OWN window, so "tightens" is a statement
    about where each boundary sits and not only about which number is larger.
    """
    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    for regime in REGIME_ORDER:
        window = policy.window_for(regime)
        edge = window.seconds
        FreshnessEvidence(
            as_of_utc=_observation_aged(edge), observed_at_utc=NOW, window=window
        )
        with pytest.raises(FreshnessNotEstablished):
            FreshnessEvidence(
                as_of_utc=_observation_aged(edge + 0.000001),
                observed_at_utc=NOW,
                window=window,
            )


# --- THE POLICY REFUSES THE CRITERION'S OWN NAMED VIOLATIONS ----------------------------- #

def test_a_constant_window_is_refused():
    """``the window made constant`` — the register's first named violation."""
    with pytest.raises(StalenessPolicyIncoherent) as refusal:
        RegimeStalenessPolicy({REGIME_CALM: 600.0, REGIME_STRESS: 600.0})
    assert "does NOT tighten as stress rises" in str(refusal.value)


def test_an_inverted_window_is_refused():
    """``the comparison inverted so stress loosens it`` — the second named violation."""
    with pytest.raises(StalenessPolicyIncoherent) as refusal:
        RegimeStalenessPolicy({REGIME_CALM: 120.0, REGIME_STRESS: 600.0})
    assert "does NOT tighten as stress rises" in str(refusal.value)


def test_a_regime_with_no_declared_window_is_refused_and_inherits_nothing():
    """``the regime input ignored`` — the third. Deny by default, no fallback."""
    with pytest.raises(StalenessPolicyIncoherent) as refusal:
        RegimeStalenessPolicy({REGIME_CALM: 600.0})
    message = str(refusal.value)
    assert "declares no window for ['STRESS']" in message
    assert "does NOT inherit" in message


def test_an_undeclared_regime_name_is_refused():
    with pytest.raises(StalenessPolicyIncoherent) as refusal:
        RegimeStalenessPolicy(
            {REGIME_CALM: 600.0, REGIME_STRESS: 120.0, "PANIC": 10.0}
        )
    assert "['PANIC']" in str(refusal.value)


def test_a_policy_that_tightens_is_admitted():
    """THE ADMITTING ARM FOR THE FOUR REFUSALS ABOVE. A type that refused every policy
    would satisfy CD-AC-009 vacuously."""
    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    assert policy.declared_regimes() == REGIME_ORDER
    assert isinstance(policy.window_for(REGIME_CALM), StalenessWindow)


# --- THE CEILING STILL BINDS, THROUGH THE ONE DOOR --------------------------------------- #

def test_the_pid_ceiling_reaches_the_policy_without_being_restated_in_it():
    """A policy cannot widen a window past PID §5's 900 s by declaring it.

    The refusal must come from ``StalenessWindow`` — the existing door — and not from a
    second copy of the ceiling check inside ``regime.py``. Asserted by the exception TYPE,
    which is that module's own.
    """
    with pytest.raises(StalenessWindowOutOfRange) as refusal:
        RegimeStalenessPolicy(
            {REGIME_CALM: STALENESS_WINDOW_CEILING_SECONDS + 1.0, REGIME_STRESS: 120.0}
        )
    assert "exceeds the ceiling" in str(refusal.value)


def test_a_policy_at_the_ceiling_is_admitted():
    """THE ADMITTING ARM. 900 s exactly is admissible; 901 is not."""
    policy = RegimeStalenessPolicy(
        {REGIME_CALM: STALENESS_WINDOW_CEILING_SECONDS, REGIME_STRESS: 120.0}
    )
    assert policy.window_for(REGIME_CALM).seconds == STALENESS_WINDOW_CEILING_SECONDS


@pytest.mark.parametrize("bad", [float("inf"), float("nan"), 0.0, -1.0])
def test_the_windows_admission_rules_reach_the_policy(bad):
    with pytest.raises((StalenessWindowOutOfRange, TypeError)):
        RegimeStalenessPolicy({REGIME_CALM: bad, REGIME_STRESS: 1.0})


# --- NO DEFAULT POLICY EXISTS ANYWHERE --------------------------------------------------- #

def test_the_regime_module_declares_no_policy():
    """*** THERE IS NO DEFAULT POLICY, AND THIS IS HOW THAT IS EVIDENCE RATHER THAN A
    CLAIM IN A DOCSTRING. ***

    Scanned over the module's OWN attributes at runtime, so a policy constructed under any
    name — ``DEFAULT_POLICY``, ``_FALLBACK``, anything — is caught. A number that carries
    product meaning is derived with its clause cited or the seat fails closed
    (``CD-RULE-003``); no clause gives an operating window, so none is declared.
    """
    import crash_detector.regime as module

    constructed = [
        name
        for name, value in vars(module).items()
        if isinstance(value, RegimeStalenessPolicy)
    ]
    assert constructed == [], (
        f"crash_detector.regime declares a ready-made policy: {constructed}. The operating "
        "windows are not derivable from any ratified clause and must not be invented here."
    )


def test_no_module_under_src_constructs_a_policy_from_literals():
    """And no other module in the package quietly supplies the default either.

    Walked over the source, because a default constructed inside a function body would be
    invisible to the runtime scan above until that function ran.
    """
    src_root = pathlib.Path(__file__).resolve().parents[1] / "src" / "crash_detector"
    paths = sorted(src_root.rglob("*.py"))
    assert paths, "no source files found; this scan would pass vacuously"

    offenders = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else None
            )
            if name == "RegimeStalenessPolicy":
                offenders.append(f"{path.name}:{node.lineno}")
    assert offenders == [], (
        "a regime staleness policy is constructed inside the application tree: "
        f"{offenders}. The policy is the deployment's declaration and arrives as an "
        "argument; a policy built from literals in src/ is an invented product quantity."
    )


# --- THE VOCABULARY IS THE RATIFIED ONE -------------------------------------------------- #

def test_the_vocabulary_is_exactly_the_two_regimes_the_pid_names():
    assert REGIME_ORDER == ("CALM", "STRESS")


def test_the_order_is_ascending_stress_and_that_is_what_the_check_walks():
    """The check is over ``REGIME_ORDER``, so the ORDER is load-bearing, not decorative."""
    assert REGIME_ORDER.index(REGIME_CALM) < REGIME_ORDER.index(REGIME_STRESS)


def test_an_unknown_regime_gets_no_window_rather_than_the_widest_one():
    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    with pytest.raises(RegimeNotDeclared) as refusal:
        policy.window_for("TRANQUIL")
    assert "not a declared regime" in str(refusal.value)


def test_a_str_subclass_is_not_a_regime_name():
    class Sneaky(str):
        def __eq__(self, other: object) -> bool:  # pragma: no cover - never reached
            return True

        __hash__ = str.__hash__

    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    with pytest.raises(RegimeNotDeclared):
        policy.window_for(Sneaky("ANYTHING"))


def test_the_policy_may_not_be_subclassed():
    with pytest.raises(TypeError) as refusal:
        class Lenient(RegimeStalenessPolicy):  # pragma: no cover - class body never runs
            pass

    assert "may not subclass" in str(refusal.value)


def test_the_policy_does_not_alias_the_callers_mapping():
    """A caller keeping a reference must not be able to retune the policy afterwards."""
    supplied = dict(SYNTHETIC_POLICY)
    policy = RegimeStalenessPolicy(supplied)
    supplied[REGIME_STRESS] = 899.0
    assert policy.window_for(REGIME_STRESS).seconds == 120.0


def test_an_undeclared_attribute_cannot_be_injected():
    policy = RegimeStalenessPolicy(SYNTHETIC_POLICY)
    with pytest.raises(AttributeError):
        object.__setattr__(policy, "smuggled", 1e18)
