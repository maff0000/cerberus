"""THE MASTERS TABLES, THE ACUTE STATISTIC AND THE COUNT (WO-1.3a round 2).

Three tests, and the middle one is the one that matters: it establishes that the
UNKNOWN propagation in :func:`crash_detector.engine.statistics.equity_crash_acute` is
UNCONDITIONAL — one unscoreable master is enough, even when every other master on the
dial would score perfectly well and even when the master that cannot be scored is NOT
the one that would have won the maximum.

CONSTRUCTED, NOT PIPED. These tests build :class:`~crash_detector.dials.scores.Contribution`
values directly, exactly as ``test_scores.py`` and ``test_dialset.py`` do, rather than
running a reading through ``evaluate()``. The unit under test takes ONE dial's
contributions and returns ONE dial's statistic; routing a model spec, a registry and a
banded mean in front of that would put three other modules between the input and the
assertion without strengthening a single claim made here.

EVERY SCORE IN THIS FILE IS A TEST FIXTURE AND NOTHING ELSE. 0.2, 0.7, 0.95, 0.9 and 0.1
below are PLAINLY CHOSEN so that a named master wins the maximum unambiguously; they are
not readings, not calibrated, and claim nothing about any indicator's real distribution or
about ``real_rate_10y_tips``'s polarity conversion. The thresholds they are chosen against
(``COUNT_THRESHOLD`` = 0.9) are themselves PROVISIONAL per PO-DECISIONS-0025 r3.

The expected ids and orders are WRITTEN OUT rather than derived from the tables under test,
following ``test_scores.py``'s rule: a test that reads its expectation out of the artefact
it is testing asserts only that the artefact equals itself.
"""

from __future__ import annotations

from crash_detector.dials.scores import (
    EQUITY_DIAL_ID,
    MONETARY_DIAL_ID,
    Contribution,
)
from crash_detector.engine.statistics import (
    PROVISIONAL_STRESS,
    Acute,
    AcuteUnknown,
    Count,
    MasterScore,
    MasterUnknown,
    State,
    candidate_state_for_one_reading,
    count_for_one_dial,
    equity_crash_acute,
    equity_crash_masters,
    monetary_debasement_acute,
)


def contributions_of(scores: dict) -> tuple:
    """``{indicator_id: scaled score}`` as the tuple of contributions one dial carries.

    ``weight`` is 1.0 and ``category`` is a fixed label throughout: neither is read by
    anything under test here — ``_scaled_scores`` takes ``source_id`` and ``contribution``
    and nothing else — so varying them would suggest they mattered to these assertions.
    """
    return tuple(
        Contribution(
            source_id=indicator,
            category="test.fixture",
            weight=1.0,
            contribution=score,
        )
        for indicator, score in scores.items()
    )


def test_a_clean_equity_reading_names_the_master_that_is_extreme():
    """Every equity component present: a stated maximum, the master it came from, a count."""
    # All six components the equity table needs. Flat at 0.2 except vix_level, which is
    # put at 0.95 — above 0.9 — so this one tuple exercises BOTH statistics: it is the
    # unambiguous acute maximum AND the one indicator at or beyond the count threshold.
    reading = contributions_of(
        {
            "hy_oas": 0.2,
            "yield_curve_10y3m": 0.2,
            "yield_curve_10y2y": 0.2,
            "vix_level": 0.95,
            "vix_term_structure": 0.2,
            "chicago_fed_nfci": 0.2,
        }
    )

    acute = equity_crash_acute(reading)

    # EXACT TYPE, not isinstance: an Acute and an AcuteUnknown are a closed set of two and
    # the whole design turns on which one came back.
    assert type(acute) is Acute
    assert acute.dial_id == EQUITY_DIAL_ID
    assert acute.score == 0.95
    # vix_level belongs to volatility_master, whose combine is MAX over
    # (vix_level, vix_term_structure) -> max(0.95, 0.2).
    assert acute.from_master_id == "volatility_master"
    # Every master's own score is carried for explainability, in the table's order.
    assert tuple(type(result) for result in acute.masters) == (MasterScore,) * 4
    assert tuple(result.master_id for result in acute.masters) == (
        "credit_master",
        "curve_master",
        "volatility_master",
        "financial_conditions_master",
    )
    assert tuple(result.score for result in acute.masters) == (0.2, 0.2, 0.95, 0.2)

    count = count_for_one_dial(reading)

    assert type(count) is Count
    assert count.at_or_beyond == ("vix_level",)
    assert count.count == 1
    # COUNT V2 (WO-1.3b-II): counted over the FAST, market-priced indicators the reading carried (R2D2's FAST2 set),
    # which is a subset of what breadth averages over: chicago_fed_nfci is a weekly survey-index and is not
    # considered, however high it scores.
    assert count.considered == (
        "hy_oas",
        "vix_level",
        "vix_term_structure",
    )


def test_a_clean_monetary_reading_names_the_master_that_is_extreme():
    """The same, against the SEPARATE monetary table and its three masters."""
    reading = contributions_of(
        {
            "monetisation_flag": 0.2,
            "real_rate_10y_tips": 0.2,
            "broad_dollar": 0.95,
        }
    )

    acute = monetary_debasement_acute(reading)

    assert type(acute) is Acute
    assert acute.dial_id == MONETARY_DIAL_ID
    assert acute.score == 0.95
    # All three monetary masters are IDENTITY over one component, so broad_dollar's own
    # score IS currency_master's score.
    assert acute.from_master_id == "currency_master"
    assert tuple(type(result) for result in acute.masters) == (MasterScore,) * 3
    assert tuple(result.master_id for result in acute.masters) == (
        "fiscal_master",
        "real_rate_master",
        "currency_master",
    )
    assert tuple(result.score for result in acute.masters) == (0.2, 0.2, 0.95)

    count = count_for_one_dial(reading)

    assert type(count) is Count
    # COUNT V2 (WO-1.3b-II): only R2D2's FAST2 indicators are counted, and of the monetary dial's three only
    # real_rate_10y_tips is among them, so broad_dollar at 0.95 is NOT counted and the monetary count can never reach
    # k = 2. That is a property of the measured set, not an oversight: R2D2 measured count v2 on the equity dial only.
    assert count.at_or_beyond == ()
    assert count.count == 0
    assert count.considered == ("real_rate_10y_tips",)


def test_the_two_watch_only_masters_are_carried_as_demoted_and_still_set_the_acute():
    """THE REAL DEMOTED ROWS, THROUGH THE REAL TABLES (WO-1.3e, R2D2's finding B3).

    ``test_engine_candidate_state.py`` measures what rule 2 DOES with ``alarm_eligible``
    using constructed masters. This test measures the other half, which only the real tables
    can answer: that ``curve_master`` and ``fiscal_master`` are the rows carrying
    ``alarm_eligible=False``, that every other master is still armed, and that the field
    survives the one and only place a :class:`Master` becomes a
    :class:`MasterScore` (``_master_result``). A demotion that were correct in the table and
    lost in the copy would pass every test in the other file.

    Both demoted rows are put at 0.95 — past ``PROVISIONAL_STRESS`` — with everything else
    on their dial flat at 0.2, so each is unambiguously its dial's acute maximum. **IT IS
    STILL THE ACUTE READING AND IT IS STILL NAMED.** Excluded from rule 2 and from nothing
    else: ``score`` and ``from_master_id`` are the demoted master's, so the dial still
    reports WHICH signal is extreme while declining to call it a crash.

    The last pair of assertions runs the real acute through the real rule and is the end-to-
    end sentence this WO exists for: a demoted master past its stress threshold is ``WATCH``
    and not ``ALARM``. ``breadth`` is 0.0 rather than this reading's own banded mean — the
    function's DECLARED LIMIT is that it cannot check the three statistics came from one
    reading, and 0.0 is the strongest available form of "nothing but the master contributed",
    which is what makes the ``WATCH`` attributable to rule 4's master limb alone.
    """
    equity = contributions_of(
        {
            "hy_oas": 0.2,
            "yield_curve_10y3m": 0.95,
            "yield_curve_10y2y": 0.2,
            "vix_level": 0.2,
            "vix_term_structure": 0.2,
            "chicago_fed_nfci": 0.2,
        }
    )
    monetary = contributions_of(
        {
            "monetisation_flag": 0.95,
            "real_rate_10y_tips": 0.2,
            "broad_dollar": 0.2,
        }
    )
    assert 0.95 >= PROVISIONAL_STRESS

    equity_acute = equity_crash_acute(equity)
    monetary_acute = monetary_debasement_acute(monetary)

    # WHICH ROWS ARE DEMOTED, read off the tables rather than asserted as a count: the two
    # ``False`` rows are named, and naming them is what makes a third demotion a test
    # failure instead of an unnoticed policy change.
    assert {
        result.master_id: result.alarm_eligible for result in equity_acute.masters
    } == {
        "credit_master": True,
        "curve_master": False,
        "volatility_master": True,
        "financial_conditions_master": True,
    }
    assert {
        result.master_id: result.alarm_eligible for result in monetary_acute.masters
    } == {
        "fiscal_master": False,
        "real_rate_master": True,
        "currency_master": True,
    }

    # DEMOTED, NOT REMOVED: each one is still its dial's maximum and is still named for it.
    assert equity_acute.score == 0.95
    assert equity_acute.from_master_id == "curve_master"
    assert monetary_acute.score == 0.95
    assert monetary_acute.from_master_id == "fiscal_master"

    for acute in (equity_acute, monetary_acute):
        state = candidate_state_for_one_reading(
            breadth=0.0,
            acute=acute,
            count=Count(at_or_beyond=(), considered=()),
            breadth_20_rows_ago=None,
            trend_confirmed=False,
        )

        assert state is State.WATCH
        assert state is not State.ALARM


def test_one_unscoreable_master_makes_the_whole_dial_unknown():
    """THE PROPAGATION, AND IT IS UNCONDITIONAL — the module docstring's central claim.

    This test is built so that "all the masters were missing, so of course it is UNKNOWN"
    cannot explain the result. THREE conditions hold simultaneously:

    1. volatility_master's BOTH components are absent, so it cannot be scored;
    2. EVERY other master's components are fully present and DO score — asserted directly
       against ``equity_crash_masters`` below, not assumed;
    3. the master that cannot be scored is NOT the one that would have won. credit_master
       scores 0.7 here and is the maximum of the three computable masters, so a
       max-over-what-we-could-compute would have returned a confident 0.7 rather than
       degrading visibly.

    Under those three conditions the dial still refuses to produce a number. That is the
    difference between a propagation that is unconditional and one that merely survives
    the total-absence case.
    """
    thinned = contributions_of(
        {
            "hy_oas": 0.7,
            "yield_curve_10y3m": 0.2,
            "yield_curve_10y2y": 0.3,
            "chicago_fed_nfci": 0.2,
            # vix_level and vix_term_structure DELIBERATELY ABSENT.
        }
    )

    # CONDITION 2 AND 3, ESTABLISHED FIRST: the other three masters each produce a real
    # score off this very tuple, and 0.7 is the maximum a thinned max would have returned.
    results = equity_crash_masters(thinned)
    assert tuple(type(result) for result in results) == (
        MasterScore,
        MasterScore,
        MasterUnknown,
        MasterScore,
    )
    scored = tuple(result for result in results if type(result) is MasterScore)
    assert tuple((result.master_id, result.score) for result in scored) == (
        ("credit_master", 0.7),
        ("curve_master", 0.3),
        ("financial_conditions_master", 0.2),
    )
    would_have_been = max(result.score for result in scored)
    assert would_have_been == 0.7

    # AND YET: the dial's acute statistic is UNKNOWN.
    acute = equity_crash_acute(thinned)

    assert type(acute) is AcuteUnknown
    assert acute.dial_id == EQUITY_DIAL_ID
    assert acute.unknown_master_ids == ("volatility_master",)
    # Both dropped components are named, so the absence is explicable from the reading.
    assert acute.missing_component_ids == ("vix_level", "vix_term_structure")
    assert "vix_level" in acute.missing_component_ids
    assert "vix_term_structure" in acute.missing_component_ids

    # NO NUMBER CAME BACK AT ALL. Not 0.0, not 0.7, not a None in a score field: the type
    # has no score attribute, which is why it is a separate type rather than an optional
    # field (CD-AC-001).
    assert not hasattr(acute, "score")
    assert "score" not in dir(acute)
    assert "score" not in AcuteUnknown.__slots__


def test_real_rate_10y_tips_is_read_from_the_tuple_it_arrived_in():
    """The one indicator bound to BOTH dials does not cross over between them (spec §5).

    TWO tuples, each giving ``real_rate_10y_tips`` a DIFFERENT score, read by the two
    dials' entry points in the same test. The two numbers are SYNTHETIC and are chosen
    only to be distinguishable: this asserts the PLUMBING does not mix the tables up, and
    asserts nothing whatever about the real opposite-polarity conversion, which happens in
    each dial's own model spec and not in the module under test.
    """
    # 0.9 on the equity-flavoured tuple. Note that real_rate_10y_tips is not a component
    # of ANY equity master, so a 0.9 showing up anywhere in the equity answer could only
    # have come from the other dial's table.
    equity_reading = contributions_of(
        {
            "hy_oas": 0.2,
            "yield_curve_10y3m": 0.2,
            "yield_curve_10y2y": 0.2,
            "vix_level": 0.2,
            "vix_term_structure": 0.2,
            "chicago_fed_nfci": 0.2,
            "real_rate_10y_tips": 0.9,
        }
    )
    # 0.1 on the monetary one, for the SAME indicator id.
    monetary_reading = contributions_of(
        {
            "monetisation_flag": 0.3,
            "real_rate_10y_tips": 0.1,
            "broad_dollar": 0.3,
        }
    )

    equity_acute = equity_crash_acute(equity_reading)
    monetary_acute = monetary_debasement_acute(monetary_reading)

    # THE EQUITY SIDE: the 0.9 did not leak in. The maximum is 0.2, not 0.9, and no
    # master on the answer carries the other dial's number or names its table.
    assert type(equity_acute) is Acute
    assert equity_acute.dial_id == EQUITY_DIAL_ID
    assert equity_acute.score == 0.2
    assert equity_acute.from_master_id == "credit_master"  # 0.2 all round; table order
    assert all(result.score == 0.2 for result in equity_acute.masters)
    assert 0.9 not in tuple(result.score for result in equity_acute.masters)
    assert "real_rate_master" not in tuple(
        result.master_id for result in equity_acute.masters
    )
    assert all(result.dial_id == EQUITY_DIAL_ID for result in equity_acute.masters)

    # THE MONETARY SIDE: real_rate_master read 0.1, its OWN tuple's value, not the 0.9
    # the equity tuple carried for the same indicator id.
    assert type(monetary_acute) is Acute
    assert monetary_acute.dial_id == MONETARY_DIAL_ID
    real_rate = tuple(
        result
        for result in monetary_acute.masters
        if result.master_id == "real_rate_master"
    )
    assert len(real_rate) == 1
    assert real_rate[0].score == 0.1
    assert real_rate[0].score != 0.9
    assert monetary_acute.score == 0.3
    assert monetary_acute.from_master_id == "fiscal_master"  # 0.3 tie; table order
    assert all(result.dial_id == MONETARY_DIAL_ID for result in monetary_acute.masters)
