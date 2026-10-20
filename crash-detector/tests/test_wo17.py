"""WO-1.7: gold_real_rate_cross (provisional correlation percentile), ism_manufacturing (regional z composite),
sloos_bank_lending (mean of two legs). Absence stays absence; a blocked gold feed is never shown live.

WO-1.19 rewrote the sloos section below. Its second leg was hand-entered until this WO replaced it with
``fred.DRTSCIS`` and deleted ``ingestion/manual.py``; the tests of that entry mechanism went with it, and
the tests of the row's own life were inverted rather than dropped. See the section comment there."""

from __future__ import annotations

import json
import random
import statistics
from datetime import date, datetime, timedelta, timezone

import pytest

from crash_detector.engine.derivations import DerivationUnavailable, derive
from ingestion.catalog import INGREDIENTS
from ingestion.report import indicator_states
from ingestion.store import SqliteStore
from ingestion.wiring import DERIVED_FROM, build_wiring, observations_from_store
from gui.state import build_state

from test_wiring import NOW, _gold_rates_series, _independent_gold_figure, _put

DAY = "2026-10-10"


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "raw.sqlite")


def _payload(rows):
    return {"unit": "x", "observation_date": rows[-1][0], "value": rows[-1][1], "history": rows}


# --- gold_real_rate_cross ----------------------------------------------------------------- #


def test_correlation_percentile_matches_an_independent_stdlib_derivation():
    gold, real = _gold_rates_series(DAY)
    got = derive("gold_real_rate_cross", {"gold": [_payload(gold)], "real_rate": [_payload(real)]})
    assert got.value == pytest.approx(_independent_gold_figure(gold, real))
    assert 0.0 < got.value <= 100.0 and got.observation_date == DAY and got.unit == "percentile_of_rolling_corr"


def test_a_flip_toward_positive_correlation_reads_high_and_the_normal_negative_regime_reads_low():
    rng = random.Random(3)
    end = date.fromisoformat(DAY)
    dates = [(end - timedelta(days=799 - i)).isoformat() for i in range(800)]
    shocks = [rng.gauss(0, 1) for _ in dates]
    sign = [-1.0] * 700 + [1.0] * 100  # the last 100 days gold moves WITH real yields
    gold, real, g, r = [], [], 2000.0, 1.0
    for d, sh, sg in zip(dates, shocks, sign):
        g *= 1.0 + 0.005 * sg * sh
        r += 0.03 * sh
        gold.append([d, g]); real.append([d, r])
    flipped = derive("gold_real_rate_cross", {"gold": [_payload(gold)], "real_rate": [_payload(real)]})
    assert flipped.value > 95.0
    normal = derive("gold_real_rate_cross", {"gold": [_payload(gold[:700])], "real_rate": [_payload(real[:700])]})
    assert normal.value < 90.0 and normal.value < flipped.value  # -1 regime throughout: nowhere near the top


def test_correlation_refuses_short_history_misaligned_dates_and_bad_prices_without_a_number():
    gold, real = _gold_rates_series(DAY)
    with pytest.raises(DerivationUnavailable, match="shared dates"):
        derive("gold_real_rate_cross", {"gold": [_payload(gold[:30])], "real_rate": [_payload(real[:30])]})
    with pytest.raises(DerivationUnavailable, match="earlier correlations"):
        derive("gold_real_rate_cross", {"gold": [_payload(gold[-200:])], "real_rate": [_payload(real[-200:])]})
    shifted = [[(date.fromisoformat(d) + timedelta(days=1000)).isoformat(), v] for d, v in real]
    with pytest.raises(DerivationUnavailable, match="shared dates"):
        derive("gold_real_rate_cross", {"gold": [_payload(gold)], "real_rate": [_payload(shifted)]})
    bad = [list(r) for r in gold]; bad[400][1] = 0.0
    with pytest.raises(DerivationUnavailable, match="non-positive"):
        derive("gold_real_rate_cross", {"gold": [_payload(bad)], "real_rate": [_payload(real)]})
    flat = [[d, 1.0] for d, _ in real]
    with pytest.raises(DerivationUnavailable, match="zero variance"):
        derive("gold_real_rate_cross", {"gold": [_payload(gold)], "real_rate": [_payload(flat)]})
    with pytest.raises(DerivationUnavailable, match="no raw history"):
        derive("gold_real_rate_cross", {"gold": [{"unit": "x", "observation_date": DAY, "value": 1.0}], "real_rate": [_payload(real)]})


# WO-1.20 RETIRED ONE TEST FROM THIS SECTION AND INVERTED ANOTHER, the same two moves WO-1.19
# made below and for the same reasons.
#
# RETIRED: ``test_lbma_history_is_raw_pm_else_am_pairs_and_off_by_default``, the test of the LBMA
# PM-else-AM parse. ``parse_lbma_gold``, ``LbmaGoldAdapter``, ``LBMA_USER_AGENT`` and the ``lbma``
# kind are DELETED, so it had no subject left. Removed rather than skipped or xfailed: a skip is a
# claim that the behaviour still matters and is not being measured, and nothing here is owed a
# future measurement of a parser for a feed that answered 403 to this host for its entire life.
#
# INVERTED, NOT DELETED: the row's own life, below. It used to be asserted FEED_FAILING with no
# value and NO FUTURES SUBSTITUTE — the gap being that ``gold_real_rate_cross``'s gold leg was the
# LBMA fix while the ratified row said ``market:GC``, so a live ``yahoo.GC=F`` sitting in the store
# was deliberately NOT read for it. THAT GAP IS CLOSED (WO-1.20, Owner-confirmed 2026-10-17): the
# futures close IS the gold leg now, so the same row is asserted LIVE with a real value. The old
# test could not simply be re-pointed, because with the ``lbma`` kind and its ingredient gone there
# is nothing left to be "blocked": a row that was never declared reads as un-configured (MISSING),
# not as a failed fetch attempt, which is what made the inversion the honest move rather than a
# tweak to the expected state. ``_fail_attempt``, which forged that 403 against the retired
# adapter id, went with it.


def test_gold_history_ingredients_are_new_ids_and_the_futures_close_now_feeds_the_cross():
    """The two legs are the history rows, and each is a NEW id beside an untouched sibling.

    ROLE ORDER IS LOAD-BEARING: ``DERIVATIONS``' roles are ``("gold", "real_rate")`` and the legs
    are consumed positionally, so the gold leg being FIRST is asserted and not incidental.
    """
    by_id = {i.source_id: i for i in INGREDIENTS}
    assert DERIVED_FROM["gold_real_rate_cross"] == ("yahoo.GC=F.history", "fred.DFII10.history")
    gold_leg, real_leg = DERIVED_FROM["gold_real_rate_cross"]
    for sid in (gold_leg, real_leg):
        assert by_id[sid].serves == ("gold_real_rate_cross",) and by_id[sid].completes == "COMPONENT"
    # The SAME declared depth on both, so neither leg silently narrows the correlation's base.
    assert by_id[gold_leg].history == by_id[real_leg].history >= 2000
    # NEW ids, not a reuse of the history-less rows: the store keeps the first payload admitted per
    # source period, so each sibling must go on answering exactly as it did. Neither's own job,
    # depth, nor the indicator it serves changed in this WO.
    assert (gold_leg, real_leg) != ("yahoo.GC=F", "fred.DFII10")
    assert by_id["yahoo.GC=F"].serves == ("copper_gold",) and by_id["yahoo.GC=F"].history == 0
    assert by_id["fred.DFII10"].serves == ("real_rate_10y_tips",) and by_id["fred.DFII10"].history == 0
    # And the retired leg is GONE from the catalog, not merely unwired: no row, and no kind.
    assert "lbma.gold_fix_usd.history" not in by_id
    assert "lbma" not in {i.kind for i in INGREDIENTS}


def test_both_real_legs_present_gold_real_rate_cross_resolves_to_a_real_value(db_path):
    """THE INVERSION of the old no-futures-substitute test (see the section note above).

    Both legs are stored as the live collector would store them — the futures close under its OWN
    new id, ``yahoo.GC=F.history``, and NOT under the ``yahoo.GC=F`` the old test put it in — and
    the row reaches LIVE with the figure an independent stdlib derivation computes from the same
    two series.

    THE ROW IS STILL A DISCLOSED SUBSTITUTE AND ``why`` MUST STILL SAY SO. Only the FEED stopped
    being a substitution here; the CONSTRUCTION is unchanged and remains Trinity's provisional,
    uncalibrated, not-Owner-ratified one, so the same two words are asserted as before. A reading
    that arrived without that disclosure would be the failure this assertion exists to catch.
    """
    gold, real = _gold_rates_series(DAY)
    with SqliteStore(db_path) as w:
        _put(w, "fred.DFII10.history", _payload(real), DAY + "T00:00:00Z")
        _put(w, "yahoo.GC=F.history", _payload(gold), DAY + "T00:00:00Z")
    with SqliteStore(db_path, read_only=True) as ro:
        row = next(i for i in build_state(ro, NOW)["indicators"] if i["id"] == "gold_real_rate_cross")
        wiring = build_wiring()
        assert "gold_real_rate_cross" in {o.source_id for o in observations_from_store(ro, wiring, NOW)}
    assert row["state"] == "LIVE"
    assert row["value"] == pytest.approx(_independent_gold_figure(gold, real))
    assert "PROVISIONAL" in row["why"] and "NOT-OWNER-RATIFIED" in row["why"]


# --- ism_manufacturing --------------------------------------------------------------------- #


def _survey(values, last_day):
    """Monthly rows ending at `last_day`, one calendar month apart going back."""
    year, month = int(last_day[:4]), int(last_day[5:7])
    dates = []
    for back in range(len(values) - 1, -1, -1):
        index = year * 12 + month - 1 - back
        dates.append(f"{index // 12}-{index % 12 + 1:02d}-01")
    return [[d, v] for d, v in zip(dates, values)]


def _three(values_each, last_day="2026-09-01"):
    return {role: [_payload(_survey(v, last_day))] for role, v in zip(("philadelphia", "new_york", "dallas"), values_each)}


def test_ism_composite_is_the_equal_weighted_mean_of_each_regions_own_z_score():
    rng = random.Random(11)
    series = [[rng.gauss(10 * k, 5 + k) for _ in range(300)] for k in range(3)]
    got = derive("ism_manufacturing", _three(series))
    expected = statistics.mean((s[-1] - statistics.fmean(s)) / statistics.pstdev(s) for s in series)
    assert got.value == pytest.approx(expected) and got.observation_date == "2026-09-01"
    assert got.unit == "regional_survey_z_composite"


def test_ism_uses_the_newest_month_all_regions_share_and_refuses_thin_or_flat_histories():
    rng = random.Random(5)
    a, b = [rng.gauss(0, 1) for _ in range(200)], [rng.gauss(0, 1) for _ in range(200)]
    inputs = _three([a, b, [rng.gauss(0, 1) for _ in range(200)]])
    inputs["dallas"] = [_payload(_survey([rng.gauss(0, 1) for _ in range(199)], "2026-08-01"))]  # Dallas has not reported Sep
    assert derive("ism_manufacturing", inputs).observation_date == "2026-08-01"
    with pytest.raises(DerivationUnavailable, match="at least 120"):
        derive("ism_manufacturing", _three([a[:50], b, b]))
    with pytest.raises(DerivationUnavailable, match="zero variance"):
        derive("ism_manufacturing", _three([[3.0] * 200, b, b]))
    no_overlap = _three([a, b, b])
    no_overlap["new_york"] = [_payload(_survey(b, "2000-01-01"))]  # ends 200 months before the others begin to overlap
    with pytest.raises(DerivationUnavailable, match="every regional survey"):
        derive("ism_manufacturing", no_overlap)


def test_ism_ingredients_are_the_three_verified_fred_series_and_none_of_richmond_or_kansas_city():
    refs = {i.ref for i in INGREDIENTS if "ism_manufacturing" in i.serves}
    assert refs == {"GACDFSA066MSFRBPHI", "GACDISA066MSFRBNY", "BACTSAMFRBDAL"}


# --- sloos_bank_lending ---------------------------------------------------------------------- #
#
# WO-1.19 RETIRED SIX TESTS FROM THIS SECTION AND INVERTED A SEVENTH, and the two moves are
# deliberately different.
#
# RETIRED: the tests of the manual-entry mechanism — ``manual.record``'s date and percentage
# refusals, the CLI's preview-by-default / ``--confirm`` / duplicate-survey behaviour, its
# refusal of an abbreviated flag and of an unreadable DB, and the guard that the collector loop
# never polled the hand-entered source. ``ingestion/manual.py``, ``MANUAL_SLOOS_NDFI`` and its
# Ingredient row are DELETED (09643ad), so those tests had no subject left. They were removed
# rather than skipped or xfailed: a skip is a claim that the behaviour still matters and is not
# being measured, and nothing here is owed a future measurement. If a hand-entered ingredient is
# ever wanted again it arrives with its own mechanism and its own tests, not with these.
#
# INVERTED, NOT DELETED: the row's own life. It used to be asserted MISSING with
# "AWAITING MANUAL ENTRY" on one fetched leg, because the other leg could only be typed in. Both
# legs are now automatic FRED feeds, so the same three-step life is asserted with the second leg
# FETCHED — see the test's docstring, which records what it used to say.


def test_sloos_is_the_mean_of_its_two_fred_legs_dated_by_the_older_and_needs_both():
    """WO-1.19's formula: the PLAIN MEAN of two fully-automatic FRED feeds of the SAME question.

    Both legs are the net percent of banks tightening C&I lending standards, read for the two
    firm-size cohorts the SLOOS reports separately — large and medium firms (``fred.DRTSCILM``)
    and small firms (``fred.DRTSCIS``). Neither is hand-entered any more; the second leg replaced
    ``manual.sloos_ndfi`` in 08f546e and the roles were renamed with it, from
    ``("commercial_industrial", "ndfi")`` to ``("large_medium_firms", "small_firms")``.

    The readings below are shaped like the real feeds: quarterly survey dates, the feeds' own
    ``net_percent_tightening`` unit, and values inside the [-100, 100] band the derivation
    enforces. The legs are deliberately UNEQUAL and the small-firm leg is deliberately the tighter
    and the OLDER of the two, so neither half of the claim can pass by coincidence — a mean that
    read one leg twice, and a date taken from the newer leg, both go red here.
    """
    leg = lambda day, v: [{"unit": "net_percent_tightening", "observation_date": day, "value": v}]  # noqa: E731
    large_medium, small = leg("2026-07-01", 10.0), leg("2026-04-01", 30.0)

    got = derive("sloos_bank_lending", {"large_medium_firms": large_medium, "small_firms": small})

    assert got.value == (10.0 + 30.0) / 2.0 == 20.0
    assert got.observation_date == "2026-04-01"  # the OLDER leg: small firms have not reported Q3 here
    assert got.unit == "net_percent_tightening"
    # One leg is never half a reading, and a figure outside the band is absence rather than a number.
    with pytest.raises(DerivationUnavailable):
        derive("sloos_bank_lending", {"large_medium_firms": large_medium, "small_firms": []})
    with pytest.raises(DerivationUnavailable, match="not a net percentage"):
        derive("sloos_bank_lending", {"large_medium_firms": large_medium, "small_firms": leg("2026-07-01", 250.0)})
    # The pre-WO-1.19 role names are NOT a second accepted spelling: the rename is a hard edge.
    with pytest.raises(ValueError):
        derive("sloos_bank_lending", {"commercial_industrial": large_medium, "ndfi": small})


def _sloos_state(db_path, now):
    with SqliteStore(db_path, read_only=True) as ro:
        return next(i for i in build_state(ro, now)["indicators"] if i["id"] == "sloos_bank_lending")


def test_a_second_fetched_leg_completes_the_row_missing_then_live_then_ages_out(db_path):
    """THE INVERSION. This test asserted the opposite until WO-1.19, and deliberately still exists.

    What it used to say: with the automatic C&I leg fetched and the NDFI leg not yet typed in, the
    row read ``MISSING`` with "AWAITING MANUAL ENTRY (python3 -m ingestion.manual sloos-ndfi
    --help)" in its reason, and only ``manual.record`` could complete it. Every clause of that is
    now false — the hand-entered leg is replaced by ``fred.DRTSCIS``, the note is deleted from
    ``ingestion/report.py``, and the CLI it named does not exist. Deleting the assertion would
    have left the row with no test that it completes AT ALL, which is the hole this WO is most
    able to open: it is the one row that moved from permanently-MISSING to LIVE.

    So the three-step life is asserted unchanged in shape, with the second leg FETCHED rather than
    typed. One leg alone is still absence, and it still says WHY by naming the leg it has not
    read — no longer by pointing a reader at a command. Both legs make it LIVE at the mean. It
    still ages out of its window on the OLDER leg's date, so a row completed by a second
    automatic feed is no more permanent than one completed by hand. That window is 150 days, not the
    120 this test was written against: WO-1.19 (Owner-confirmed 2026-10-16) ratified it wider on the
    measured SLOOS release lag, so the row stays LIVE ~29 days longer than it used to and the ageing
    step below had to be recomputed rather than renumbered.
    """
    survey = {"unit": "net_percent_tightening", "observation_date": "2026-07-01"}
    with SqliteStore(db_path) as w:  # only the large/medium-firm leg has been collected
        _put(w, "fred.DRTSCILM", {**survey, "value": 6.0}, "2026-07-01T00:00:00Z")
    row = _sloos_state(db_path, NOW)
    assert row["state"] == "MISSING" and row["value"] is None
    assert "fred.DRTSCIS: never read" in row["why"]  # the unread leg, named
    assert "AWAITING MANUAL ENTRY" not in row["why"]  # the note, and the CLI it named, are both gone

    with SqliteStore(db_path) as w:  # ...and now the small-firm leg, for the SAME survey
        _put(w, "fred.DRTSCIS", {**survey, "value": 18.0}, "2026-07-01T00:00:00Z")
    live = _sloos_state(db_path, NOW)  # 2026-10-11: 102 days after the survey
    assert live["state"] == "LIVE" and live["value"] == 12.0 and live["dials"] == ["equity_crash"]
    assert live["window_days"] == 150.0 and live["as_of_utc"].startswith("2026-07-01")

    # 102.5 days old at NOW, so the 150-day window has ~47.5 days left to run: at the OLD 120-day
    # window this row aged out 19 days after NOW, and it no longer does. 49 days puts it 151.5 days
    # past the survey date, genuinely beyond the ratified window rather than beyond the retired one.
    later = NOW + timedelta(days=49)
    gone = _sloos_state(db_path, later)
    assert gone["state"] == "STALE" and gone["value"] is None
    with SqliteStore(db_path, read_only=True) as ro:
        states = {s["id"]: s["state"] for s in indicator_states(ro, later)}
    assert states["sloos_bank_lending"] == "STALE"
