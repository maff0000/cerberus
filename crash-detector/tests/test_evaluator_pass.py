"""THE EVALUATOR PASS: real raw data in, one ``machine_state_history`` row per dial out.

WO-1.3a round 6. :mod:`evaluator.pass_once` is the only module in this WO that is NOT
tested against constructed inputs: ``test_engine_masters.py``, ``test_engine_candidate_state.py``
and ``test_resolve_official_state.py`` all build ``Contribution``/``Acute``/``MachineStateRow``
values directly, because the units they test take one dial's numbers and return one answer.
This unit's whole content is the WIRING — which store, which handle, which dial's masters,
which clock — so a constructed input would test nothing that is here.

So this file PIPES. It seeds a real SQLite raw store with ``test_wiring``'s own ``CALM``
fixture (the same one ``test_gui.py`` runs the GUI's view-model over), runs the pass against
it, and reads the row back out of a real ``machine_state_history`` file. Both stores are
``tmp_path`` throwaways, the same pattern every store test in this WO uses.

WHAT THE FIXTURE'S NUMBERS ARE. ``CALM`` is mid-band, fresh values for every live
indicator; it is a WIRING fixture and not a market scenario, and the states it happens to
produce (equity CALM, monetary WATCH on ``real_rate_master``) follow from PROVISIONAL,
uncalibrated bands (PO-DECISIONS-0025 r3) and claim nothing about either dial's real
distribution. The assertions below are therefore about the row's SHAPE and PROVENANCE —
every statistic present, the masters being this dial's masters, the breadth being the
number the GUI shows — and the two places a specific state IS asserted say which constant
decided it.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.engine.statistics import PROVISIONAL_WARNING, State
from evaluator import pass_once
from evaluator.history_store import MachineStateHistoryStore
from evaluator.pass_once import (
    TREND_NOT_COMPUTED,
    PassWiringBroken,
    _raw_reader,
    one_pass_for_both_dials,
    one_pass_for_dial,
)
from evaluator.resolve import BREADTH_LOOKBACK_ROWS
from gui.state import build_state
from ingestion.store import SqliteStore
from ingestion.wiring import build_wiring

from test_wiring import CALM, NOW, _seed

#: The masters each dial's row must score, WRITTEN OUT rather than read off
#: ``EQUITY_CRASH_MASTERS``/``MONETARY_DEBASEMENT_MASTERS``, following
#: ``test_engine_masters.py``'s rule: a test that reads its expectation out of the artefact
#: under test asserts only that the artefact equals itself.
EXPECTED_MASTERS = {
    "equity_crash": {
        "credit_master",
        "curve_master",
        "volatility_master",
        "financial_conditions_master",
    },
    "monetary_debasement": {"fiscal_master", "real_rate_master", "currency_master"},
}

STATISTICS = (
    "acute_rising",
    "breadth",
    "acute",
    "acute_from_master_id",
    "master_scores",
    "indicator_count",
    "count_at_or_beyond",
)


@pytest.fixture
def raw_path(tmp_path):
    """A raw store seeded with every live indicator at its CALM fixture value."""
    path = str(tmp_path / "raw.sqlite")
    with SqliteStore(path) as writer:
        _seed(writer, build_wiring(), CALM)
    return path


@pytest.fixture
def empty_raw_path(tmp_path):
    """A raw store that exists and holds no reading at all."""
    path = str(tmp_path / "empty-raw.sqlite")
    with SqliteStore(path):
        pass
    return path


@pytest.fixture
def history(tmp_path):
    with MachineStateHistoryStore(str(tmp_path / "machine-state.sqlite")) as store:
        yield store


class _RecordingHistory:
    """A real history store with the window it was asked for written down.

    A DELEGATING WRAPPER and not a monkeypatch: :class:`MachineStateHistoryStore` declares
    ``__slots__``, so ``store.recent = ...`` raises and there is no instance attribute to
    replace — the same sealing ``ingestion.store`` and every score type in this product use.
    A wrapper keeps the real store underneath, so the append below still goes through the
    real table and its CHECK constraints; only the question asked is observed.
    """

    def __init__(self, store: MachineStateHistoryStore) -> None:
        self._store = store
        self.asked: list = []

    def recent(self, dial_id: str, *, limit: int) -> tuple:
        self.asked.append((dial_id, limit))
        return self._store.recent(dial_id, limit=limit)

    def append(self, row, *, written_utc) -> None:
        self._store.append(row, written_utc=written_utc)


# --- one pass, both dials, over real seeded data ----------------------------------------- #


def test_one_pass_writes_one_resolvable_row_per_dial(raw_path, history):
    """The round's central claim: a dial with all its master components present resolves.

    Everything asserted here is read BACK OUT of the file rather than taken from the return
    value, so the row went through the table's CHECK constraints (CD-RT-001) and not only
    through the resolver.
    """
    returned = one_pass_for_both_dials(raw_store_path=raw_path, history=history, now_utc=NOW)
    assert tuple(returned) == DIAL_IDS  # two rows, side by side, in the product's own order

    for dial_id in DIAL_IDS:
        stored = history.recent(dial_id, limit=BREADTH_LOOKBACK_ROWS)
        assert len(stored) == 1, f"{dial_id}: one pass must write exactly one row"
        row = stored[0]
        assert row == returned[dial_id]  # what the pass said it wrote is what the file holds

        assert row.dial_id == dial_id
        assert row.machine_state is not State.UNKNOWN
        # A dial with every master component present has a number for every statistic.
        assert all(getattr(row, name) is not None for name in STATISTICS), (
            f"{dial_id}: a resolvable row must carry every statistic"
        )
        # EVERY master, not only the one that won the maximum (spec §3 rules 2/4/5 read per
        # master), and this dial's masters only — the other dial's table is not reachable.
        assert set(row.master_scores) == EXPECTED_MASTERS[dial_id]
        assert row.acute_from_master_id in EXPECTED_MASTERS[dial_id]
        assert row.acute == max(row.master_scores.values())
        assert row.indicator_count == len(row.count_at_or_beyond)

        # FIRST EVER ROW FOR THIS DIAL: nothing to persist against, so the candidate IS the
        # official state and the clock reads 0 (resolve.py's first-evaluation branch).
        assert row.candidate_state is row.machine_state
        assert row.persistence_counter == 0
        # `acute_rising` cannot be confirmed with no preceding row, and the column's only
        # honest answer is the one that claims less.
        assert row.acute_rising is False

        assert row.as_of.tzinfo is not None  # dated by the reading's inputs, not by the pass


def test_the_breadth_written_is_the_number_the_GUI_SHOWS_for_that_dial(raw_path, history):
    """``breadth`` is the EXISTING composite, read out of the existing evaluation (spec §1).

    Not "a weighted mean computed the same way" — the SAME number, off the same path. The
    comparison is against ``gui.state.build_state``, which is the live consumer of that
    path today, so if the pass ever grew its own mean this test would catch the divergence
    rather than a reviewer having to notice two implementations.
    """
    rows = one_pass_for_both_dials(raw_store_path=raw_path, history=history, now_utc=NOW)
    with SqliteStore(raw_path, read_only=True) as reader:
        shown = {dial["dial_id"]: dial for dial in build_state(reader, NOW)["dials"]}

    for dial_id in DIAL_IDS:
        assert shown[dial_id]["status"] == "VALUE"
        assert rows[dial_id].breadth == shown[dial_id]["value"]


def test_the_two_dials_are_resolved_independently(raw_path, history):
    """One dial's pass reads, scores and appends for that dial and touches nothing else."""
    one_pass_for_dial("equity_crash", raw_store_path=raw_path, history=history, now_utc=NOW)

    assert len(history.recent("equity_crash", limit=BREADTH_LOOKBACK_ROWS)) == 1
    assert history.recent("monetary_debasement", limit=BREADTH_LOOKBACK_ROWS) == ()


def test_a_missing_required_input_leaves_the_other_dial_resolvable(tmp_path, history):
    """``hy_oas`` is REQUIRED on equity: that dial reads UNKNOWN and monetary still resolves.

    The same seeding ``test_gui.py`` uses for its own per-dial isolation claim. It matters
    here because it is the one route to an UNKNOWN row on a store that is otherwise full,
    and because an UNKNOWN row must not be able to carry a number.
    """
    raw = str(tmp_path / "raw-no-hy-oas.sqlite")
    with SqliteStore(raw) as writer:
        _seed(writer, build_wiring(), CALM, skip=("hy_oas",))

    rows = one_pass_for_both_dials(raw_store_path=raw, history=history, now_utc=NOW)

    equity = history.recent("equity_crash", limit=1)[0]
    assert equity == rows["equity_crash"]
    assert equity.machine_state is State.UNKNOWN
    assert equity.candidate_state is State.UNKNOWN
    assert equity.persistence_counter == 0
    assert all(getattr(equity, name) is None for name in STATISTICS), (
        "an UNKNOWN row may carry no number at all (CD-RT-001)"
    )

    assert history.recent("monetary_debasement", limit=1)[0].machine_state is not State.UNKNOWN


def test_an_empty_raw_store_writes_UNKNOWN_for_both_dials_and_not_calm(empty_raw_path, history):
    """THE ONE THAT MUST NEVER READ AS CALM: no data at all is UNKNOWN, on both dials."""
    rows = one_pass_for_both_dials(
        raw_store_path=empty_raw_path, history=history, now_utc=NOW
    )

    for dial_id in DIAL_IDS:
        stored = history.recent(dial_id, limit=1)[0]
        assert stored == rows[dial_id]
        assert stored.machine_state is State.UNKNOWN
        assert stored.machine_state is not State.CALM
        assert all(getattr(stored, name) is None for name in STATISTICS)
        # Dated by the pass's own instant: there are no inputs to date this row by.
        assert stored.as_of == NOW


def test_the_second_pass_resolves_against_the_row_the_first_one_wrote(raw_path, history):
    """Step 3 is wired: the pass reads this dial's history and hands it to the resolver.

    Two passes over the SAME data. The second reading's candidate equals the first row's
    official state, which is the resolver's "the dial is where it says it is" branch — so
    the state is unchanged and the clock reads 0. If the pass passed an empty history
    instead, the second row would be another "first ever evaluation" and this test could
    not tell the difference — which is why ``acute_rising`` is asserted too: it is ``False``
    only because the preceding row's ``acute`` was read and was not exceeded.
    """
    first = one_pass_for_dial("equity_crash", raw_store_path=raw_path, history=history, now_utc=NOW)
    second = one_pass_for_dial(
        "equity_crash", raw_store_path=raw_path, history=history, now_utc=NOW
    )

    stored = history.recent("equity_crash", limit=BREADTH_LOOKBACK_ROWS)
    assert len(stored) == 2 and stored[0] == second  # most recent first
    assert second.machine_state is first.machine_state
    assert second.persistence_counter == 0
    assert second.acute == first.acute and second.acute_rising is False


# --- the raw store's door --------------------------------------------------------------- #


def test_the_raw_store_handle_this_pass_opens_cannot_write(raw_path):
    """THE READ-ONLY DOOR, provoked against a real SQLite and not inspected for a flag.

    Same assertion style as ``test_machine_state_history.py``'s own reader-door test: the
    refusal asserted is :exc:`sqlite3.OperationalError` from SQLite itself, so a test that
    merely declined to call a writer would not pass this.

    ``register`` is a collector write method and the two DDL/DML statements after it are
    the routes that would bypass it; all three are issued through the handle the pass
    itself opened, and all three are refused.

    The read asserted first is by INGREDIENT source id and not by indicator id: the raw
    store is keyed by the feed that was fetched, and ``hy_oas`` is the indicator the engine
    derives from it. Reading by the wrong key would return ``None`` and the handle would
    look inert when it is not.
    """
    hy_oas_feed = build_wiring().ingredient_for["hy_oas"].source_id

    with _raw_reader(raw_path) as reader:
        # It can read: the handle is useful, not merely inert.
        assert reader.latest_reading(hy_oas_feed) is not None

        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            reader.register(
                source_id="not_a_feed",
                adapter_id="test.none",
                poll_seconds=60,
                stands_for="a write this process may not make",
                declared_feed="none",
                serves=(),
                now=NOW,
            )
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            reader._db.execute("DELETE FROM raw_reading")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            reader._db.execute("CREATE TABLE smuggled (x TEXT)")


def test_the_raw_store_door_creates_nothing(tmp_path):
    """An absent raw store is an error, never a new empty database.

    A created-on-open file would hold no readings, and "no indicator is live" is a sentence
    this pass would then write to history as UNKNOWN for a reason that was its own doing.
    """
    absent = tmp_path / "never-collected.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        _raw_reader(str(absent))
    assert not absent.exists()


def test_the_pass_does_not_write_to_the_raw_store(raw_path, history):
    """MEASURED, not reasoned: the raw file is byte-identical after a pass over both dials."""
    with open(raw_path, "rb") as handle:
        before = handle.read()

    one_pass_for_both_dials(raw_store_path=raw_path, history=history, now_utc=NOW)

    with open(raw_path, "rb") as handle:
        assert handle.read() == before


# --- trend_confirmed: the disclosed placeholder ------------------------------------------ #


def test_trend_confirmed_is_the_disclosed_placeholder_and_is_False(raw_path, history, monkeypatch):
    """The value the pass hands the resolver is ``False``, and it is named as uncomputed.

    Asserted BEHAVIOURALLY — the resolver is replaced and the keyword it actually received
    is captured — rather than by reading the call site, so this cannot pass against a pass
    that computed something and discarded it.

    Spec §7 cut the trend computation from WO-1.3a. ``False`` is the conservative answer:
    rule 5 NEEDS ``trend_confirmed`` to reach RECOVERY, so a hardcoded ``False`` can only
    keep a dial in ALARM longer and can never manufacture a recovery. When a real indicator
    is wired, :data:`~evaluator.pass_once.TREND_NOT_COMPUTED` is deleted and this test is
    the one that has to be rewritten.
    """
    assert TREND_NOT_COMPUTED is False

    seen = {}
    real = pass_once.official_state_for_dial

    def spy(**kwargs):
        seen.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(pass_once, "official_state_for_dial", spy)
    one_pass_for_dial("equity_crash", raw_store_path=raw_path, history=history, now_utc=NOW)

    assert seen["trend_confirmed"] is False
    assert seen["trend_confirmed"] is TREND_NOT_COMPUTED
    # The window asked for is the one rule 4's lookback needs (spec §7).
    assert len(seen["history"]) <= BREADTH_LOOKBACK_ROWS


def test_the_pass_asks_for_the_full_breadth_lookback_window(raw_path, history):
    """``recent`` is called with :data:`BREADTH_LOOKBACK_ROWS` and not a smaller window.

    A pass that asked for 3 rows would satisfy persistence and silently disable rule 4's
    breadth limb for ever: ``_breadth_rows_ago`` reads ``None`` — "cannot confirm rising" —
    from a history that is short, and a short history it was handed deliberately is
    indistinguishable from a young one.
    """
    recorder = _RecordingHistory(history)

    one_pass_for_dial("equity_crash", raw_store_path=raw_path, history=recorder, now_utc=NOW)

    assert recorder.asked == [("equity_crash", BREADTH_LOOKBACK_ROWS)]
    assert len(history.recent("equity_crash", limit=1)) == 1  # the append still went through


# --- this module's own wiring ----------------------------------------------------------- #


def test_an_unknown_dial_id_is_refused_and_writes_nothing(raw_path, history):
    """A dial this pass has no masters table for is a defect, not a reading."""
    with pytest.raises(PassWiringBroken, match="not a dial this pass knows"):
        one_pass_for_dial("gold_dial", raw_store_path=raw_path, history=history, now_utc=NOW)

    for dial_id in DIAL_IDS:
        assert history.recent(dial_id, limit=1) == ()


def test_the_provisional_warning_band_is_what_put_monetary_above_calm(raw_path, history):
    """The one state this file asserts by name, with the constant that decided it.

    Named so a recalibration in WO-1.3b moves this expectation instead of silently
    inverting what the test above proves: the CALM fixture's ``real_rate_10y_tips`` scores
    at/above ``PROVISIONAL_WARNING`` on the monetary dial, which is spec §3 rule 3.
    """
    rows = one_pass_for_both_dials(raw_store_path=raw_path, history=history, now_utc=NOW)
    monetary = rows["monetary_debasement"]

    assert monetary.master_scores["real_rate_master"] >= PROVISIONAL_WARNING
    assert monetary.machine_state is State.WATCH
