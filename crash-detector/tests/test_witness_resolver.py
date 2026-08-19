"""The serving-layer resolver: absence and staleness land on UNAVAILABLE (CD-AC-005).

BLUEPRINT §6: "if cd-witness writes no panel row at all, or writes one older than its
staleness window, cd-public renders WITNESS UNAVAILABLE. Both the explicit and the
implicit failure path land on the same honest state, and neither has a route to AGREES."

The last test in this file is the one that matters most: it sweeps a wide space of
malformed, absent, stale, future-dated and unrecognised rows and asserts that **no input
whatsoever** produces ``Agrees``. That tests the proposition rather than the two cases
somebody thought of.
"""

from __future__ import annotations

import itertools
import math

import pytest

from crash_detector.serving.witness_resolver import (
    WITNESS_AGREES_TEXT,
    WITNESS_DIVERGES_TEXT,
    WITNESS_UNAVAILABLE_TEXT,
    PanelRow,
    render_panel,
    resolve_panel,
)
from crash_detector.staleness import (
    STALENESS_WINDOW_CEILING_SECONDS,
    FreshnessEvidence,
    FreshnessNotEstablished,
    StalenessWindow,
    StalenessWindowOutOfRange,
)
from crash_detector.witness.panel import (
    Agrees,
    AgreementWithoutFreshnessEvidence,
    Diverges,
    Unavailable,
)

from conftest import FIXED_NOW, WINDOW_SECONDS, ago, freshness_for


def _row(state="AGREES", seconds_ago=10, measures=None) -> PanelRow:
    if measures is None:
        measures = {"divergence_measure": 0.02, "threshold": 0.5}
    return PanelRow(
        state=state,
        as_of_utc=ago(seconds_ago),
        published_utc=ago(seconds_ago),
        measures=measures,
    )


def _resolve(row):
    return resolve_panel(
        row, now_utc=FIXED_NOW, staleness_window_seconds=WINDOW_SECONDS
    )


# --- the two routes BLUEPRINT §6 names explicitly ---------------------------------------- #

def test_an_absent_panel_row_resolves_to_unavailable():
    """cd-witness wrote nothing at all."""
    panel = _resolve(None)
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_ABSENT"


def test_a_stale_panel_row_resolves_to_unavailable():
    """Older than its staleness window. The implicit failure path."""
    panel = _resolve(_row(state="AGREES", seconds_ago=WINDOW_SECONDS + 1))
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_STALE"


def test_a_stale_row_that_said_agrees_does_not_keep_agreeing():
    """The specific plant CD-AC-005 exists for: yesterday's agreement rendering today."""
    fresh = _resolve(_row(state="AGREES", seconds_ago=10))
    assert isinstance(fresh, Agrees)
    stale = _resolve(_row(state="AGREES", seconds_ago=WINDOW_SECONDS + 1))
    assert isinstance(stale, Unavailable)


# --- the routes nobody wrote down, which is where the class of violation lives ------------ #

def test_a_future_dated_row_is_not_treated_as_fresh():
    """A row ahead of now would never age out of any window, so it would agree forever —
    and it would do so most confidently exactly when the witness clock is broken."""
    panel = _resolve(_row(state="AGREES", seconds_ago=-3600))
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_FUTURE_DATED"


def test_an_unrecognised_state_resolves_to_unavailable():
    for state in ("agrees", "AGREE", "OK", "", "TRUE", "UNKNOWN", "AGREES "):
        panel = _resolve(_row(state=state))
        assert isinstance(panel, Unavailable), state
        assert panel.reason == "PANEL_STATE_UNRECOGNISED", state


def test_an_agrees_row_with_no_measurement_is_incoherent_not_agreement():
    panel = _resolve(_row(state="AGREES", measures={}))
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_INCOHERENT"


def test_a_diverges_row_missing_its_threshold_is_incoherent():
    panel = _resolve(_row(state="DIVERGES", measures={"divergence_measure": 0.9}))
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_INCOHERENT"


@pytest.mark.parametrize("bad", ["0.0", 0, True, None, math.nan, math.inf, [0.0]])
def test_a_measurement_that_is_not_a_finite_float_is_incoherent_not_coerced(bad):
    """`float(bad)` would turn "0.0", 0 and True into a zero divergence measure — which
    is perfect agreement, manufactured from a type error (Baseline §4)."""
    panel = _resolve(_row(state="AGREES", measures={"divergence_measure": bad}))
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_INCOHERENT"


def test_a_row_that_says_unavailable_stays_unavailable():
    panel = _resolve(_row(state="UNAVAILABLE", measures={}))
    assert isinstance(panel, Unavailable)
    assert panel.reason == "WITNESS_FEED_UNREACHABLE"


# --- the staleness window itself cannot be neutralised ------------------------------------- #

@pytest.mark.parametrize("window", [math.inf, math.nan, 0.0, -1.0])
def test_a_window_that_abolishes_staleness_is_refused(window):
    """`inf` seconds is not a lenient window, it is the abolition of staleness."""
    with pytest.raises(ValueError):
        resolve_panel(_row(), now_utc=FIXED_NOW, staleness_window_seconds=window)


@pytest.mark.parametrize("window", ["3600", None, True, [3600]])
def test_a_window_that_is_not_a_number_is_refused(window):
    with pytest.raises(TypeError):
        resolve_panel(_row(), now_utc=FIXED_NOW, staleness_window_seconds=window)


# --- the happy paths, so the refusals are not passing by accident -------------------------- #

def test_a_fresh_agreeing_row_resolves_to_agrees():
    panel = _resolve(_row(state="AGREES", measures={"divergence_measure": 0.02}))
    assert isinstance(panel, Agrees)
    assert panel.divergence_measure == 0.02


def test_a_fresh_diverging_row_resolves_to_diverges():
    panel = _resolve(
        _row(state="DIVERGES", measures={"divergence_measure": 0.9, "threshold": 0.5})
    )
    assert isinstance(panel, Diverges)
    assert panel.threshold == 0.5


def test_freshness_is_judged_on_the_data_not_on_when_we_wrote_the_row():
    """"We published recently" is not "the witnesses are current"."""
    row = PanelRow(
        state="AGREES",
        as_of_utc=ago(WINDOW_SECONDS + 1),
        published_utc=ago(1),
        measures={"divergence_measure": 0.02},
    )
    panel = _resolve(row)
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_STALE"


# --- rendering ------------------------------------------------------------------------------ #

def test_each_panel_renders_its_own_text():
    assert render_panel(
        Agrees(
            divergence_measure=0.0, as_of_utc=FIXED_NOW, freshness=freshness_for()
        )
    ) == WITNESS_AGREES_TEXT
    assert render_panel(
        Diverges(divergence_measure=0.9, threshold=0.5, as_of_utc=FIXED_NOW)
    ) == WITNESS_DIVERGES_TEXT
    assert render_panel(
        Unavailable(reason="PANEL_ROW_ABSENT", since_utc=FIXED_NOW)
    ) == WITNESS_UNAVAILABLE_TEXT


def test_rendering_an_unrecognised_panel_raises_rather_than_showing_agreement():
    class LooksLikeAgrees:
        divergence_measure = 0.0
        as_of_utc = FIXED_NOW

    with pytest.raises(TypeError):
        render_panel(LooksLikeAgrees())  # type: ignore[arg-type]


def test_the_unavailable_text_cannot_be_confused_with_the_agrees_text():
    assert WITNESS_UNAVAILABLE_TEXT != WITNESS_AGREES_TEXT
    assert "AGREE" not in WITNESS_UNAVAILABLE_TEXT


# --- the proposition, swept ------------------------------------------------------------------ #

def test_no_absent_stale_future_or_malformed_input_ever_resolves_to_agrees():
    """The class, not the instance.

    Every combination of state, age and measurement shape below is resolved, and the
    assertion is the PROPOSITION: nothing that is not a fresh, coherent, explicitly
    agreeing row may come back as ``Agrees``. A guard that only refused the two rows
    BLUEPRINT §6 names would pass the tests above and fail this one.
    """
    states = ["AGREES", "DIVERGES", "UNAVAILABLE", "agrees", "", "OK", "AGREES\n"]
    ages = [-86400, -1, 10, WINDOW_SECONDS + 1, 10**7]
    measure_sets = [
        {},
        {"divergence_measure": 0.02},
        {"divergence_measure": 0.02, "threshold": 0.5},
        {"divergence_measure": "0.0"},
        {"divergence_measure": 0},
        {"divergence_measure": True},
        {"divergence_measure": math.nan},
        {"threshold": 0.5},
        {"unexpected_key": 1.0},
    ]

    agreed = []
    for state, age, measures in itertools.product(states, ages, measure_sets):
        panel = _resolve(_row(state=state, seconds_ago=age, measures=measures))
        if isinstance(panel, Agrees):
            honest = (
                state == "AGREES"
                and 0.0 <= age <= WINDOW_SECONDS
                and isinstance(measures.get("divergence_measure"), float)
                and not isinstance(measures.get("divergence_measure"), bool)
                and math.isfinite(measures["divergence_measure"])
            )
            if not honest:
                agreed.append((state, age, measures))

    assert agreed == [], f"absence resolved to agreement for: {agreed}"


def test_the_absent_row_case_is_included_in_the_sweep_separately():
    """`None` is not a PanelRow, so it cannot be in the product above."""
    assert not isinstance(_resolve(None), Agrees)


# --- CD-ASR-F06 / E07: a window wide enough to make staleness meaningless ------------------ #

TEN_YEARS_SECONDS = 3650 * 24 * 3600.0


def test_e07_verbatim_a_decade_old_row_and_a_1e18_window_does_not_render_agreement():
    """The auditor's variant, run exactly as reported.

    At the WO-2 gate this returned `Agrees` and rendered "WITNESS AGREES" with no source
    edit at all. Now the window never becomes usable, so the resolver refuses before it
    resolves anything — which is the correct answer to an inadmissible configuration:
    an unusable window is not a lenient one.
    """
    row = PanelRow(
        state="AGREES",
        as_of_utc=ago(TEN_YEARS_SECONDS),
        published_utc=ago(TEN_YEARS_SECONDS),
        measures={"divergence_measure": 0.02, "threshold": 0.10},
    )
    with pytest.raises(StalenessWindowOutOfRange):
        resolve_panel(row, now_utc=FIXED_NOW, staleness_window_seconds=1e18)


@pytest.mark.parametrize(
    "window", [1e18, 901.0, 3600.0, 86400.0, TEN_YEARS_SECONDS, 1e308]
)
def test_no_window_above_the_ceiling_can_be_applied_by_the_resolver(window):
    """The CLASS, not E07's number: every finite positive window above the ceiling."""
    with pytest.raises(StalenessWindowOutOfRange):
        resolve_panel(_row(), now_utc=FIXED_NOW, staleness_window_seconds=window)


@pytest.mark.parametrize("window", [0.001, 1.0, 60.0, 600.0, 900.0])
def test_a_decade_old_row_resolves_to_unavailable_under_every_usable_window(window):
    """The other half: where the window IS admissible, the old row lands on the honest
    state rather than on a refusal. Both halves are needed — a closure that only ever
    raises would be hiding a resolver that still agreed."""
    panel = resolve_panel(
        _row(state="AGREES", seconds_ago=TEN_YEARS_SECONDS),
        now_utc=FIXED_NOW,
        staleness_window_seconds=window,
    )
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_STALE"
    assert render_panel(panel) == WITNESS_UNAVAILABLE_TEXT


def test_the_window_ceiling_is_the_derived_one_and_the_resolver_uses_it():
    """The boundary itself, from the caller's side."""
    assert isinstance(
        resolve_panel(
            _row(),
            now_utc=FIXED_NOW,
            staleness_window_seconds=STALENESS_WINDOW_CEILING_SECONDS,
        ),
        Agrees,
    )
    with pytest.raises(StalenessWindowOutOfRange):
        resolve_panel(
            _row(),
            now_utc=FIXED_NOW,
            staleness_window_seconds=STALENESS_WINDOW_CEILING_SECONDS + 1e-9,
        )


def test_the_agrees_it_returns_carries_the_evidence_that_justifies_it():
    """Not a flag someone set: the evidence is bound to this row's own instant."""
    row = _row(state="AGREES", seconds_ago=10, measures={"divergence_measure": 0.02})
    panel = resolve_panel(row, now_utc=FIXED_NOW, staleness_window_seconds=WINDOW_SECONDS)
    assert isinstance(panel, Agrees)
    assert panel.freshness.as_of_utc == row.as_of_utc
    assert panel.freshness.observed_at_utc == FIXED_NOW
    assert panel.freshness.window.seconds == WINDOW_SECONDS
    assert panel.freshness.age_seconds == 10.0


# --- CD-ASR-F07 / E08, reported as a CONSEQUENCE and not as scope -------------------------- #

def test_an_exception_handler_cannot_manufacture_agreement_from_a_stale_row():
    """E08's route: `try: ... except Exception: return Agrees(...)`.

    The auditor could not make the planted handler fire and recorded it LOW for that
    reason. What is asserted here is the thing that makes the route dead whether it fires
    or not: the handler has nothing to construct `Agrees` FROM. It cannot omit the
    evidence, it cannot fabricate it, and it cannot make it for a stale row.
    """
    stale_row = _row(state="AGREES", seconds_ago=TEN_YEARS_SECONDS)
    window = StalenessWindow(seconds=WINDOW_SECONDS)

    def resolver_with_a_swallowing_handler(row):
        try:
            raise RuntimeError("whatever went wrong in the age computation")
        except Exception:
            # the three things such a handler could try, all of them refused
            return Agrees(
                divergence_measure=0.0,
                as_of_utc=row.as_of_utc,
                freshness=FreshnessEvidence(
                    as_of_utc=row.as_of_utc,
                    observed_at_utc=FIXED_NOW,
                    window=window,
                ),
            )

    with pytest.raises(FreshnessNotEstablished):
        resolver_with_a_swallowing_handler(stale_row)

    # (b) omit the evidence entirely
    with pytest.raises(TypeError):
        Agrees(divergence_measure=0.0, as_of_utc=stale_row.as_of_utc)  # type: ignore[call-arg]

    # (c) borrow evidence about some other, fresher observation
    with pytest.raises(AgreementWithoutFreshnessEvidence):
        Agrees(
            divergence_measure=0.0,
            as_of_utc=stale_row.as_of_utc,
            freshness=FreshnessEvidence(
                as_of_utc=ago(10), observed_at_utc=FIXED_NOW, window=window
            ),
        )


# --- the proposition, swept again, now over the window as well ----------------------------- #

def test_no_row_of_any_age_under_any_usable_window_ever_resolves_to_agrees_dishonestly():
    """The increment-4 sweep, extended along the axis CD-ASR-F06 attacked: THE WINDOW.

    The original sweep held the window fixed, which is exactly why E07 was invisible to
    it. This one varies the window across everything that can be constructed, including
    the ceiling itself, and adds a decade-old row to the ages.
    """
    windows = [1.0, 60.0, 600.0, 900.0]
    states = ["AGREES", "DIVERGES", "UNAVAILABLE", "agrees", "", "OK"]
    ages = [-86400, -1, 10, 601, 901, 10**7, TEN_YEARS_SECONDS]
    measure_sets = [
        {},
        {"divergence_measure": 0.02},
        {"divergence_measure": "0.0"},
        {"divergence_measure": 0},
        {"divergence_measure": True},
        {"divergence_measure": math.nan},
    ]

    agreed = []
    for window in windows:
        for state, age, measures in itertools.product(states, ages, measure_sets):
            panel = resolve_panel(
                _row(state=state, seconds_ago=age, measures=measures),
                now_utc=FIXED_NOW,
                staleness_window_seconds=window,
            )
            if isinstance(panel, Agrees):
                honest = (
                    state == "AGREES"
                    and 0.0 <= age <= window
                    and isinstance(measures.get("divergence_measure"), float)
                    and not isinstance(measures.get("divergence_measure"), bool)
                    and math.isfinite(measures["divergence_measure"])
                )
                if not honest:
                    agreed.append((window, state, age, measures))

    assert agreed == [], f"a stale or malformed input agreed: {agreed}"
