"""CLASS 2 — JUDGE VALUES, NEVER TYPES. The doctrine, at the door and end to end.

CD-AC-005, finding CD-ASR-WO2R-F02 (HIGH), auditor variant ASR2-005-A, and the
``_finite_measure`` sibling reported "not as a separate finding but as the same class".

THE CLASS UNDER TEST IS NOT "datetime subclasses". It is: ANY JUDGEMENT THIS SYSTEM MAKES
THAT DELEGATES ITS DECIDING OPERATION TO AN OBJECT THE SYSTEM DID NOT CONSTRUCT. So these
tests are written in two halves, and the second half matters as much as the first:

  * the ATTACK half — a supplied object that tries to decide staleness, agreement or
    reading-ness with its own method, and does not get to;
  * the FALSE-POSITIVE half — an ordinary library-shaped object that is still read
    correctly, because a closure that forbids the product is not a closure.

**NOTHING OUTSIDE THE STANDARD LIBRARY IS IMPORTED HERE, DELIBERATELY.** ``pandas``,
``numpy`` and ``pytz`` are not declared dependencies of this project — they are absent from
``requirements.txt`` and ``requirements.lock`` — and a test that needs an undeclared import
is a test that can skip, which is not evidence. The stand-ins below are exactly what those
library types ARE: ``pandas.Timestamp`` is a ``datetime`` subclass and ``numpy.float64`` is
a ``float`` subclass. The real libraries were measured separately as implementation
evidence and the versions and numbers are in this increment's Build Log entry.
"""

from datetime import datetime, timedelta, timezone, tzinfo

import pytest

from crash_detector.own_terms import (
    NotEstablishedOnOwnTerms,
    own_float,
    own_instant,
    own_str,
    own_utc_offset,
)
from crash_detector.serving.witness_resolver import (
    PanelRow,
    render_panel,
    resolve_panel,
)
from crash_detector.time_utc import age_seconds, ensure_utc
from crash_detector.witness.panel import Agrees, Unavailable

NOW = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
A_DECADE_AGO = datetime(2016, 8, 21, 0, 0, 0, tzinfo=timezone.utc)
WINDOW = 600.0


# --------------------------------------------------------------------------------------- #
# THE AUDITOR'S ROUTE — ASR2-005-A, in the shape it was reported
# --------------------------------------------------------------------------------------- #


class FeedInstant(datetime):
    """ASR2-005-A's type, verbatim in behaviour: the feed reports ages as zero."""

    def __rsub__(self, other):
        return timedelta(0)

    def __sub__(self, other):
        return timedelta(0)

    def astimezone(self, tz=None):
        return self


def test_a_datetime_subclass_does_not_control_the_subtraction_that_ages_it():
    """The whole of ASR2-005-A: `age_seconds` subtracts two datetimes and the supplied
    subclass owned `__rsub__`. Both operands are now re-built by `ensure_utc`, so the
    subtraction is CPython's between two objects this system made."""
    age = age_seconds(as_of_utc=FeedInstant(2016, 8, 21, tzinfo=timezone.utc), now_utc=NOW)
    assert age > 315_000_000.0, age


def test_the_normalised_timestamp_is_of_the_exact_base_type():
    """`PanelRow.__post_init__` normalises through `ensure_utc`. The auditor measured that
    the subclass SURVIVED that normalisation ("after PanelRow normalisation, as_of_utc
    type: FeedInstant"). It does not survive it now."""
    row = PanelRow(
        state="AGREES",
        as_of_utc=FeedInstant(2016, 8, 21, tzinfo=timezone.utc),
        published_utc=FeedInstant(2016, 8, 21, tzinfo=timezone.utc),
        measures={"divergence_measure": 0.01},
    )
    assert type(row.as_of_utc) is datetime
    assert type(row.published_utc) is datetime


def test_asr2_005_a_end_to_end_renders_unavailable_not_agrees():
    """The auditor's measured result was `RENDERS: WITNESS AGREES` on a row dated 2016 read
    in 2026 with a 600 s window. The control arm — the identical instant as a plain
    datetime — rendered WITNESS UNAVAILABLE. The two arms must now agree."""
    subclass_arm = resolve_panel(
        PanelRow(
            state="AGREES",
            as_of_utc=FeedInstant(2016, 8, 21, tzinfo=timezone.utc),
            published_utc=FeedInstant(2016, 8, 21, tzinfo=timezone.utc),
            measures={"divergence_measure": 0.01},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW,
    )
    control_arm = resolve_panel(
        PanelRow(
            state="AGREES",
            as_of_utc=A_DECADE_AGO,
            published_utc=A_DECADE_AGO,
            measures={"divergence_measure": 0.01},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW,
    )
    assert isinstance(subclass_arm, Unavailable)
    assert subclass_arm.reason == "PANEL_ROW_STALE"
    assert render_panel(subclass_arm) == "WITNESS UNAVAILABLE"
    assert render_panel(subclass_arm) == render_panel(control_arm)
    assert subclass_arm.reason == control_arm.reason


def test_the_rename_test_the_refusal_consults_no_identifier():
    """CD-PL-F74, executed rather than asserted. ASR2-005-A with EVERY identifier renamed —
    the class, the module-level factory, the parameter names — refuses identically, because
    `own_instant` reads C-struct offsets through descriptors and consults no name."""

    class Zq7(datetime):
        def __rsub__(self, xyzzy):
            return timedelta(0)

        def __sub__(self, xyzzy):
            return timedelta(0)

        def astimezone(self, plugh=None):
            return self

    renamed = resolve_panel(
        PanelRow(
            state="AGREES",
            as_of_utc=Zq7(2016, 8, 21, tzinfo=timezone.utc),
            published_utc=Zq7(2016, 8, 21, tzinfo=timezone.utc),
            measures={"divergence_measure": 0.01},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW,
    )
    assert isinstance(renamed, Unavailable)
    assert renamed.reason == "PANEL_ROW_STALE"


def test_overriding_the_field_accessors_themselves_does_not_help():
    """The next thing an attacker reaches for once `__rsub__` stops working: lie about the
    primitives. `datetime.year` is a getset_descriptor over the C struct, so a `property`
    of the same name on the subclass is never consulted."""

    class LiesAboutItsFields(datetime):
        @property
        def year(self):
            return 2026

        @property
        def month(self):
            return 8

        @property
        def day(self):
            return 19

    established = ensure_utc(LiesAboutItsFields(2016, 8, 21, tzinfo=timezone.utc))
    assert established.year == 2016
    assert established == A_DECADE_AGO


# --------------------------------------------------------------------------------------- #
# THE SIBLING THE AUDITOR NAMED IN THE SAME BREATH — the measurement
# --------------------------------------------------------------------------------------- #


class LyingMeasure(float):
    """A float subclass that answers every question about itself the way it prefers."""

    def __float__(self):
        return 0.0

    def __eq__(self, other):
        return True

    def __hash__(self):
        return hash(0.0)

    def __lt__(self, other):
        return True


def test_a_float_subclass_does_not_decide_whether_it_is_finite():
    """`math.isfinite` consults `__float__`, so `_finite_measure`'s finiteness test was the
    supplied object's to answer. `own_float` reads the stored double instead."""
    assert own_float(LyingMeasure(float("inf"))) == float("inf")
    assert type(own_float(LyingMeasure(0.25))) is float


def test_an_infinite_measurement_wearing_a_float_subclass_is_incoherent_not_agreement():
    panel = resolve_panel(
        PanelRow(
            state="AGREES",
            as_of_utc=NOW,
            published_utc=NOW,
            measures={"divergence_measure": LyingMeasure(float("inf"))},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW,
    )
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_INCOHERENT"
    assert render_panel(panel) == "WITNESS UNAVAILABLE"


def test_a_measurement_that_is_admitted_is_stored_as_a_plain_float():
    panel = resolve_panel(
        PanelRow(
            state="AGREES",
            as_of_utc=NOW,
            published_utc=NOW,
            measures={"divergence_measure": LyingMeasure(0.02)},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW,
    )
    assert isinstance(panel, Agrees)
    assert type(panel.divergence_measure) is float
    assert panel.divergence_measure == 0.02


# --------------------------------------------------------------------------------------- #
# THE ROUTE THIS SEAT FOUND ITSELF — the discriminator label
# --------------------------------------------------------------------------------------- #


class SaysWhateverSuitsIt(str):
    """A `str` subclass that compares equal to "AGREES" whatever it actually holds."""

    def __eq__(self, other):
        return other == "AGREES"

    def __ne__(self, other):
        return not (other == "AGREES")

    def __hash__(self):
        return hash("AGREES")


def test_a_str_subclass_does_not_decide_which_panel_constructor_is_reached():
    """A row whose stored state is UNAVAILABLE — the witness feed is DEAD — must not become
    agreement because the label object answered `== "AGREES"`. No timestamp is involved."""
    panel = resolve_panel(
        PanelRow(
            state=SaysWhateverSuitsIt("UNAVAILABLE"),
            as_of_utc=NOW,
            published_utc=NOW,
            measures={"divergence_measure": 0.01},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW,
    )
    assert isinstance(panel, Unavailable)
    assert panel.reason == "WITNESS_FEED_UNREACHABLE"
    assert render_panel(panel) == "WITNESS UNAVAILABLE"


def test_the_stored_state_is_the_truth_the_row_carried():
    row = PanelRow(
        state=SaysWhateverSuitsIt("UNAVAILABLE"),
        as_of_utc=NOW,
        published_utc=NOW,
        measures={},
    )
    assert type(row.state) is str
    assert row.state == "UNAVAILABLE"


def test_a_measure_key_cannot_answer_to_a_name_it_does_not_hold():
    """`key not in row.measures` is decided by the STORED keys' `__hash__`/`__eq__`."""

    class AnswersToAnything(str):
        def __eq__(self, other):
            return True

        def __hash__(self):
            return hash("divergence_measure")

    panel = resolve_panel(
        PanelRow(
            state="AGREES",
            as_of_utc=NOW,
            published_utc=NOW,
            measures={AnswersToAnything("something_else"): 0.01},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW,
    )
    assert isinstance(panel, Unavailable)
    assert panel.reason == "PANEL_ROW_INCOHERENT"


def test_an_unavailable_reason_outside_the_declared_set_is_still_refused():
    class PassesForDeclared(str):
        def __eq__(self, other):
            return True

        def __hash__(self):
            return hash("PANEL_ROW_ABSENT")

    with pytest.raises(ValueError):
        Unavailable(reason=PassesForDeclared("MADE_IT_UP"), since_utc=NOW)


# --------------------------------------------------------------------------------------- #
# THE FALSE-POSITIVE HALF. A closure that forbids the product is not a closure.
# --------------------------------------------------------------------------------------- #


class LibraryTimestamp(datetime):
    """What `pandas.Timestamp` and `freezegun`'s type ARE: ordinary datetime subclasses.

    Handing the resolver one of these is not an attack, it is Tuesday, and a structure that
    made it unusable would have traded a defect for a defect.
    """


class LibraryFloat(float):
    """What `numpy.float64` IS: an ordinary float subclass."""


def test_an_ordinary_library_timestamp_subclass_is_read_not_refused():
    fresh = LibraryTimestamp(2026, 8, 19, 11, 59, 55, tzinfo=timezone.utc)
    panel = resolve_panel(
        PanelRow(
            state="AGREES",
            as_of_utc=fresh,
            published_utc=fresh,
            measures={"divergence_measure": LibraryFloat(0.02)},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW,
    )
    assert isinstance(panel, Agrees)
    assert render_panel(panel) == "WITNESS AGREES"
    assert type(panel.as_of_utc) is datetime
    assert type(panel.divergence_measure) is float
    assert panel.freshness.age_seconds == 5.0


def test_a_non_utc_offset_is_still_converted_rather_than_refused():
    """The behaviour `ensure_utc` documented before this change and still owes its callers:
    an aware datetime carrying any offset is an unambiguous instant, so there is nothing to
    guess and nothing to refuse."""
    plus_two = datetime(2026, 8, 19, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    assert ensure_utc(plus_two) == NOW
    assert type(ensure_utc(plus_two)) is datetime


def test_a_stdlib_timezone_of_any_offset_round_trips():
    for hours in (-11, -5, 0, 1, 5, 13):
        offset = timezone(timedelta(hours=hours))
        local = NOW.astimezone(offset)
        assert ensure_utc(local) == NOW


def test_microseconds_survive():
    precise = datetime(2026, 8, 19, 12, 0, 0, 123456, tzinfo=timezone.utc)
    assert ensure_utc(precise).microsecond == 123456


def test_the_six_routes_to_unavailable_are_all_still_reached():
    """CD-AC-005's six declared routes. None of them may be lost to this closure."""
    stale = A_DECADE_AGO
    future = datetime(2030, 1, 1, tzinfo=timezone.utc)
    cases = {
        "PANEL_ROW_ABSENT": None,
        "PANEL_ROW_FUTURE_DATED": PanelRow(
            state="AGREES", as_of_utc=future, published_utc=future, measures={}
        ),
        "PANEL_ROW_STALE": PanelRow(
            state="AGREES", as_of_utc=stale, published_utc=stale, measures={}
        ),
        "WITNESS_FEED_UNREACHABLE": PanelRow(
            state="UNAVAILABLE", as_of_utc=NOW, published_utc=NOW, measures={}
        ),
        "PANEL_ROW_INCOHERENT": PanelRow(
            state="AGREES", as_of_utc=NOW, published_utc=NOW, measures={}
        ),
        "PANEL_STATE_UNRECOGNISED": PanelRow(
            state="SOMETHING_ELSE", as_of_utc=NOW, published_utc=NOW, measures={}
        ),
    }
    for expected_reason, row in cases.items():
        panel = resolve_panel(row, now_utc=NOW, staleness_window_seconds=WINDOW)
        assert isinstance(panel, Unavailable), expected_reason
        assert panel.reason == expected_reason
        assert render_panel(panel) == "WITNESS UNAVAILABLE"


# --------------------------------------------------------------------------------------- #
# THE DECLARED LIMIT, MEASURED (CD-RULE-004, CD-RULE-006)
# --------------------------------------------------------------------------------------- #


class LyingTimezone(tzinfo):
    """A tzinfo that reports an offset of its own choosing.

    A tzinfo cannot be refused without refusing `zoneinfo`, `pytz` and `pandas`, all of
    which supply their own. It is boundary 1 of `own_terms`'s declared limit.
    """

    def __init__(self, offset):
        self._offset = offset

    def utcoffset(self, when):
        return self._offset

    def dst(self, when):
        return timedelta(0)

    def tzname(self, when):
        return "LIE"


def test_a_lying_tzinfo_is_bounded_to_under_a_day():
    """BOUNDARY 1, MEASURED. The carrier is the CPython interpreter and it carries the
    BOUND, not the truth: a lying tzinfo moves the instant, and cannot move it by a day."""
    stated = datetime(2026, 8, 19, 12, 0, 0)
    almost_a_day = stated.replace(tzinfo=LyingTimezone(timedelta(hours=-23)))
    assert ensure_utc(almost_a_day) == datetime(
        2026, 8, 20, 11, 0, 0, tzinfo=timezone.utc
    )
    # ... and one day is where CPython itself stops it, before this module sees anything.
    with pytest.raises(ValueError):
        ensure_utc(stated.replace(tzinfo=LyingTimezone(timedelta(days=1))))
    with pytest.raises(ValueError):
        ensure_utc(stated.replace(tzinfo=LyingTimezone(timedelta(days=-1))))


def test_a_tzinfo_that_returns_something_other_than_a_timedelta_is_refused():
    """CPython refuses it first; this asserts the refusal exists, not who makes it."""
    stated = datetime(2026, 8, 19, 12, 0, 0)
    with pytest.raises(TypeError):
        ensure_utc(stated.replace(tzinfo=LyingTimezone(3600)))


def test_sub_microsecond_precision_is_dropped_and_never_rounded_up():
    """BOUNDARY 2, MEASURED. A `datetime` stores microseconds, so anything finer is lost.
    It is a TRUNCATION, so nothing is ever made to look FRESHER than it is."""

    class CarriesNanoseconds(datetime):
        nanosecond = 789

    precise = CarriesNanoseconds(2026, 8, 19, 12, 0, 0, 123456, tzinfo=timezone.utc)
    established = ensure_utc(precise)
    assert established.microsecond == 123456
    assert established <= precise.replace(tzinfo=timezone.utc)
    assert type(established) is datetime
    assert not hasattr(established, "nanosecond")


def test_the_offset_is_rebuilt_so_a_timedelta_subclass_cannot_carry_the_arithmetic():
    """`datetime.utcoffset` validates by `isinstance`, so a `timedelta` SUBCLASS reaches
    this module. It is rebuilt from its own three primitive fields before it is used."""

    class SubtractsNothing(timedelta):
        def __rsub__(self, other):
            return other

    offered = datetime(
        2026, 8, 19, 12, 0, 0, tzinfo=LyingTimezone(SubtractsNothing(hours=2))
    )
    established = own_utc_offset(offered)
    assert type(established) is timedelta
    assert established == timedelta(hours=2)
    assert ensure_utc(offered) == datetime(2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------------------- #
# THE DOOR ITSELF
# --------------------------------------------------------------------------------------- #


def test_own_instant_refuses_an_offset_that_is_not_a_plain_timedelta():
    class NotQuiteATimedelta(timedelta):
        pass

    with pytest.raises(NotEstablishedOnOwnTerms):
        own_instant(NOW, offset=NotQuiteATimedelta(0))


def test_own_float_refuses_bool_ahead_of_the_float_test():
    with pytest.raises(NotEstablishedOnOwnTerms):
        own_float(True)
    with pytest.raises(NotEstablishedOnOwnTerms):
        own_float(False)


def test_own_float_refuses_what_it_cannot_read_rather_than_coercing_it():
    for offered in ("0.0", 0, None, [0.0], object()):
        with pytest.raises(NotEstablishedOnOwnTerms):
            own_float(offered)


def test_own_str_returns_the_code_points_the_object_actually_holds():
    established = own_str(SaysWhateverSuitsIt("UNAVAILABLE"))
    assert type(established) is str
    assert established == "UNAVAILABLE"


def test_own_str_refuses_a_non_string():
    for offered in (None, 0, 0.0, b"AGREES", object()):
        with pytest.raises(NotEstablishedOnOwnTerms):
            own_str(offered)


def test_an_exact_value_is_returned_unchanged_so_the_door_costs_nothing_ordinary():
    plain_float = 0.25
    plain_str = "AGREES"
    assert own_float(plain_float) is plain_float
    assert own_str(plain_str) is plain_str


def test_own_utc_offset_reports_naive_as_none_matching_datetime_utcoffset():
    assert own_utc_offset(datetime(2026, 8, 19, 12, 0, 0)) is None
    assert own_utc_offset(NOW) == timedelta(0)


def test_own_utc_offset_refuses_a_non_datetime():
    with pytest.raises(NotEstablishedOnOwnTerms):
        own_utc_offset("2026-08-19T12:00:00Z")
