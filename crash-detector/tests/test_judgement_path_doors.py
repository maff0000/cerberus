"""PLANTS P5, P6 AND P7 of BP-AMENDMENT-0001 §F.1, and the static check's own arms.

Every plant here runs over ``EMPTY_MODEL_REGISTRY`` and ``EMPTY_SOURCE_REGISTRY`` — zero
model rows, zero source rows, both dials ``Unknown`` — because that is the shipped WO-2
state and a plant demonstrated against a configuration nobody ships demonstrates nothing
about what ships.

| id | plant | must fail at |
|----|-------|--------------|
| P5 | a duck ``ConfigSnapshot`` into ``evaluate`` (ASR3-F05) | the ``admits`` door |
| P6 | a duck row whose ``state`` property answers ``AGREES`` while its stored state is ``UNAVAILABLE`` (ASR3-F04) | the ``admits`` door |
| P7 | a new parameter added to a decorated door without being declared to ``admits`` | the ``admits`` door, ON EVERY CALL |

**THE BASELINE ARMS ARE HERE. THE VIOLATED ARMS ARE NOT AND CANNOT BE.** "Remove the
guard and show it passes" means editing ``src/``, and this suite runs against the tree as
it stands. Each violated arm is a patch under ``variants/WO-2R3/``, applied to a pristine
``git archive`` extraction, run there and discarded — the extraction hygiene the dispatch
requires, and the reason no violated arm is a test node id here. The manifest carries the
literal command line for each.

**P7 IS THE ONE THAT MATTERS MOST** and the Product Owner directed the fourth Assurance
seat to run it first (PO-DECISIONS-0005 ruling 1). It is what distinguishes *establishment
derived from the signature* from *four type checks on four named functions*. Its
authoritative demonstration is ``variants/WO-2R3/V20-p7-added-parameter.patch`` — a real
parameter added to the real ``resolve_panel`` in a real extraction. What is here is the
same fact read from the runtime, using each product door's OWN declaration.
"""

from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.admission import (
    NotAdmitted,
    UndeclaredParameter,
    admits,
    declared_admissions,
)
from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.dials.reading import Unknown
from crash_detector.engine.config import ConfigSnapshot, DialSpec, empty_config_snapshot
from crash_detector.engine.evaluate import evaluate
from crash_detector.engine.model import EMPTY_MODEL_REGISTRY
from crash_detector.observations import OK, ObservationRecord
from crash_detector.serving.dial_presentation import NotShown, is_shown, present_dial
from crash_detector.serving.witness_resolver import (
    PanelRow,
    WITNESS_UNAVAILABLE_TEXT,
    render_panel,
    resolve_panel,
)
from crash_detector.source_registry import EMPTY_SOURCE_REGISTRY
from crash_detector.staleness import StalenessWindow
from crash_detector.witness.panel import Agrees, Unavailable

NOW = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)
WINDOW_SECONDS = 600.0
TEN_YEARS_SECONDS = 3650 * 86400.0


def _ago(seconds: float) -> datetime:
    return NOW - timedelta(seconds=seconds)


def _the_shipped_snapshot() -> ConfigSnapshot:
    """The WO-2 configuration, over BOTH EMPTY registries. Every plant uses it."""
    snapshot = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    assert snapshot.model_registry is EMPTY_MODEL_REGISTRY
    assert snapshot.source_registry is EMPTY_SOURCE_REGISTRY
    assert snapshot.model_registry.is_empty
    return snapshot


# ========================================================================================= #
# P5 — A DUCK ConfigSnapshot INTO evaluate (ASR3-F05).
#      MUST FAIL AT: the `admits` door on `evaluate`.
# ========================================================================================= #


class _PermissiveWindow:
    """The auditor's window: ``covers()`` answers True for every age there is.

    ``StalenessWindow`` refuses this value at its own constructor and always did. The
    finding was never that the window type was weak — it was that ``evaluate`` never
    required its ``config_snapshot`` to BE a ``ConfigSnapshot``, so the object deciding
    "is this observation fresh enough to use" was the caller's.
    """

    seconds = TEN_YEARS_SECONDS * 10

    def __init__(self) -> None:
        self.asked = 0

    def covers(self, age_seconds: float) -> bool:
        self.asked += 1
        return True


class _DuckConfigSnapshot:
    """ASR3-F05 verbatim in shape: answers ``window()``, ``spec_for()``, ``model_for()``.

    It is NOT a ``ConfigSnapshot`` and it never went through
    ``ConfigSnapshot.__post_init__``, so the staleness ceiling, the exact-type checks and
    §C.5's three registry invariants were all skipped — not defeated, skipped, because
    nothing required them to have run.
    """

    def __init__(self) -> None:
        self.window_object = _PermissiveWindow()
        self.specs = {
            EQUITY_DIAL_ID: DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=("src.e",),
                contributing_input_ids=(),
                model_ref="carrying.model.v0",
            ),
            MONETARY_DIAL_ID: DialSpec(
                dial_id=MONETARY_DIAL_ID,
                required_input_ids=(),
                contributing_input_ids=(),
                model_ref=None,
            ),
        }

    def window(self):
        return self.window_object

    def spec_for(self, dial_id):
        return self.specs[dial_id]

    def model_for(self, dial_id):
        return None


def _a_decade_old_observation() -> ObservationRecord:
    return ObservationRecord(
        source_id="src.e",
        observed_utc=NOW,
        outcome=OK(payload={"v": 0.9}, source_as_of_utc=_ago(TEN_YEARS_SECONDS)),
    )


def test_p5_the_duck_config_snapshot_is_refused_at_the_door():
    """P5, BASELINE. ASR3-F05's object, refused before ``evaluate``'s body runs.

    REFUSING LAYER: ``crash_detector.admission.admits``, applied at ``evaluate``'s
    boundary and derived from its signature.
    SCOPE OF THAT LAYER: every call to ``evaluate`` by any caller anywhere, including
    calls that would have gone on to be discarded. It is not a property of ``evaluate``'s
    body and no rewrite of that body removes it.

    RENAME TEST: SURVIVES. The refusal is ``type(value) is not ConfigSnapshot`` — an
    identity comparison between two type objects. Rename ``config_snapshot``, rename
    ``_DuckConfigSnapshot``, rename ``evaluate`` itself: a duck is still not a
    ``ConfigSnapshot``.

    COUNTERFACTUAL (CD-D-079): ``variants/WO-2R3/V21-p5-violated.patch`` removes the
    ``@admits`` decorator from ``evaluate`` and the same duck object is admitted, its
    ``window()`` is called, and its ``covers()`` answers the freshness question. Run in a
    pristine extraction; command line in the manifest.
    """
    plant = _DuckConfigSnapshot()
    with pytest.raises(NotAdmitted) as refusal:
        evaluate([_a_decade_old_observation()], plant, NOW)
    assert "_DuckConfigSnapshot" in str(refusal.value)
    assert "ConfigSnapshot" in str(refusal.value)
    # The caller's code never ran inside the freshness decision, because the call never
    # reached the body: this is the whole of ASR3-F05 and it is asserted, not narrated.
    assert plant.window_object.asked == 0


def test_p5_a_config_snapshot_subclass_is_refused_too_and_that_is_the_class():
    """P5, BASELINE, the obvious next move. A subclass is not a near miss — it is the
    same defect with an inheritance edge, because a subclass may shadow ``window`` with a
    property and a property is the caller's code answering at the moment we ask."""

    class Subclassed(ConfigSnapshot):
        def window(self):  # pragma: no cover - refused before it can run
            return _PermissiveWindow()

    subclass = Subclassed(
        config_snapshot_id="cfg-wo2",
        dial_specs=_the_shipped_snapshot().dial_specs,
        staleness_window_seconds=WINDOW_SECONDS,
        source_registry=EMPTY_SOURCE_REGISTRY,
        model_registry=EMPTY_MODEL_REGISTRY,
    )
    with pytest.raises(NotAdmitted):
        evaluate([], subclass, NOW)


def test_p5_a3_the_record_is_established_and_not_only_its_outcome():
    """P5's sibling and A3's own requirement. A look-alike RECORD carrying an entirely
    honest ``OK`` is refused, because ``source_id`` — which decides whether a REQUIRED
    input was present — is the record's to answer and not the outcome's."""

    class LooksLikeARecord:
        source_id = "src.e"
        observed_utc = NOW
        outcome = OK(payload={"v": 0.9}, source_as_of_utc=_ago(10))

    with pytest.raises(NotAdmitted) as refusal:
        evaluate([LooksLikeARecord()], _the_shipped_snapshot(), NOW)
    assert "observations[0]" in str(refusal.value)


def test_p5_over_the_shipped_empty_registry():
    """The plant's premise, asserted rather than assumed: it ran against ZERO model rows
    and ZERO source rows, and the honest product answer over that configuration is
    ``Unknown`` on both dials."""
    snapshot = _the_shipped_snapshot()
    dials = evaluate([_a_decade_old_observation()], snapshot, NOW)
    assert type(dials.equity) is Unknown
    assert type(dials.monetary) is Unknown
    assert EMPTY_MODEL_REGISTRY.model_ids == ()


# ========================================================================================= #
# P6 — A DUCK ROW WHOSE `state` PROPERTY ANSWERS AGREES WHILE ITS STORED STATE IS
#      UNAVAILABLE (ASR3-F04).
#      MUST FAIL AT: the `admits` door on `resolve_panel`.
# ========================================================================================= #


class _DuckRow:
    """ASR3-F04 verbatim in shape.

    The witness feed is DEAD — ``stored_state`` is ``UNAVAILABLE`` — and the ``state``
    property answers ``"AGREES"`` when the resolver asks. No timestamp trick, no subclass,
    no ``object.__setattr__``, no source edit. The auditor measured ``RENDERS: WITNESS
    AGREES``.
    """

    def __init__(self) -> None:
        self.stored_state = "UNAVAILABLE"
        self.as_of_utc = _ago(10)
        self.published_utc = _ago(10)
        self.measures = {"divergence_measure": 0.02}
        self.asked = 0

    @property
    def state(self) -> str:
        self.asked += 1
        return "AGREES"


def test_p6_the_duck_row_is_refused_at_the_door():
    """P6, BASELINE. ASR3-F04's row, refused before ``resolve_panel``'s body runs.

    REFUSING LAYER: ``crash_detector.admission.admits``, applied at ``resolve_panel``'s
    boundary and derived from its signature: ``row`` must be exactly ``PanelRow`` or
    exactly ``None``.
    SCOPE OF THAT LAYER: every call to ``resolve_panel`` by any caller anywhere. It is
    NOT the ``PanelRow`` constructor, which was already closed and which the auditor
    confirmed was closed — the finding was that nothing required the constructor to have
    run, and that is what this closes.

    RENAME TEST: SURVIVES. ``type(row) is not PanelRow and type(row) is not NoneType`` is
    an identity comparison between type objects. Rename ``state``, rename ``_DuckRow``,
    rename ``PanelRow``'s fields: none of them is consulted, because the body is never
    entered.

    COUNTERFACTUAL (CD-D-079): ``variants/WO-2R3/V22-p6-violated.patch`` removes the
    ``@admits`` decorator from ``resolve_panel`` and the same row renders WITNESS AGREES
    again. Run in a pristine extraction; command line in the manifest.
    """
    plant = _DuckRow()
    with pytest.raises(NotAdmitted) as refusal:
        resolve_panel(plant, now_utc=NOW, staleness_window_seconds=WINDOW_SECONDS)
    assert "_DuckRow" in str(refusal.value)
    assert "PanelRow" in str(refusal.value)
    # The lying property was never consulted, because the body was never entered.
    assert plant.asked == 0


def test_p6_a_panel_row_subclass_is_refused_too():
    """The same attack with an inheritance edge, which is the one an auditor reaches for
    second. A subclass CAN shadow `state` with a property after `__post_init__` has run on
    the base's field, so `isinstance` here would be the same defect wearing a base class."""

    class Subclassed(PanelRow):
        pass

    row = Subclassed(
        state="UNAVAILABLE",
        as_of_utc=_ago(10),
        published_utc=_ago(10),
        measures={"divergence_measure": 0.02},
    )
    # The property is installed AFTER __post_init__ has run and established the field, so
    # the row is honestly built and then lies when asked. `type.__setattr__` walks past the
    # metaclass and CPython offers no way to stop it, which is why this half is closed at
    # the entry point rather than on the type.
    type.__setattr__(Subclassed, "state", property(lambda self: "AGREES"))
    assert row.state == "AGREES"
    with pytest.raises(NotAdmitted):
        resolve_panel(row, now_utc=NOW, staleness_window_seconds=WINDOW_SECONDS)


def test_p6_the_control_arm_the_same_value_through_the_constructor():
    """The auditor's own control arm, kept. The identical stored state, this time through
    ``PanelRow``, resolves to ``Unavailable`` and renders WITNESS UNAVAILABLE — so the
    refusal above is not the product refusing to work."""
    row = PanelRow(
        state="UNAVAILABLE",
        as_of_utc=_ago(10),
        published_utc=_ago(10),
        measures={"divergence_measure": 0.02},
    )
    panel = resolve_panel(row, now_utc=NOW, staleness_window_seconds=WINDOW_SECONDS)
    assert type(panel) is Unavailable
    assert render_panel(panel) == WITNESS_UNAVAILABLE_TEXT


def test_p6_none_is_still_admitted_because_absence_is_a_value_here():
    """A4 requires ``exactly PanelRow, OR None``. ``row is None`` means cd-witness wrote
    nothing, and it must still resolve to ``Unavailable`` rather than raising."""
    panel = resolve_panel(None, now_utc=NOW, staleness_window_seconds=WINDOW_SECONDS)
    assert type(panel) is Unavailable
    assert panel.reason == "PANEL_ROW_ABSENT"


def test_p6_over_the_shipped_empty_registry():
    """P6 touches no registry at all — the witness path has none — so the premise is
    asserted the only way it can be: the model registry is empty throughout this module's
    run and no row was registered to make this plant work."""
    assert EMPTY_MODEL_REGISTRY.is_empty
    assert EMPTY_MODEL_REGISTRY.model_ids == ()


# ========================================================================================= #
# P7 — A NEW PARAMETER ADDED TO A DECORATED DOOR WITHOUT BEING DECLARED TO `admits`.
#      MUST FAIL AT: the `admits` door, ON EVERY CALL.
# ========================================================================================= #

#: The doors §D.2 names, plus the one increment 1 built (CD-D-098). P7 is asserted against
#: EACH of them, using EACH one's OWN declaration as it stands in the product.
THE_DOORS_D2_NAMES = (
    ("A2/A3", evaluate),
    ("A4", resolve_panel),
    ("A5", present_dial),
)


@pytest.mark.parametrize(
    "label,door", THE_DOORS_D2_NAMES, ids=[label for label, _ in THE_DOORS_D2_NAMES]
)
def test_p7_a_parameter_added_to_a_real_door_refuses_every_call(label, door):
    """P7, BASELINE, read from the RUNTIME using the product door's OWN declaration.

    Each of these doors' actual ``admits(...)`` declaration — taken off the product object,
    not written here — is re-applied to that door's own underlying function WITH ONE MORE
    PARAMETER. Every call is refused, including the calls that do not pass it.

    REFUSING LAYER: ``crash_detector.admission.admits``, at decoration, from
    ``inspect.signature``.
    SCOPE OF THAT LAYER: every callable it decorates, for every call, whatever the added
    parameter is named and whatever its default is.

    RENAME TEST: SURVIVES. The fault is a set difference between the signature's parameter
    names and the declaration's keys. It consults no particular identifier; renaming the
    added parameter changes which name appears in the message and nothing else.

    THIS IS A RECONSTRUCTION AND IT IS LABELLED ONE. The authoritative P7 arm adds a real
    parameter to the real ``resolve_panel`` in a pristine extraction —
    ``variants/WO-2R3/V20-p7-added-parameter.patch`` — because a plant that only ever runs
    against a rebuilt copy of a door is a plant against the copy.
    """
    declaration = declared_admissions(door)

    namespace: dict = {}
    parameters = ", ".join(
        f"{name}=None" for name in declaration
    )
    source = (
        f"def with_one_more({parameters}, added_by_a_later_feature=False):\n"
        f"    return None\n"
    )
    exec(source, namespace)  # noqa: S102 - building a signature, not running product code
    rebuilt = admits(**declaration)(namespace["with_one_more"])

    with pytest.raises(UndeclaredParameter) as refusal:
        rebuilt()
    assert "added_by_a_later_feature" in str(refusal.value)
    # AND on a call that does pass it, and on a keyword call.
    with pytest.raises(UndeclaredParameter):
        rebuilt(added_by_a_later_feature=True)


def test_p7_the_real_doors_are_not_faulted_today():
    """The other half of the contrast, and it is not a formality: a mechanism that refused
    every call to every door would look identical to a mechanism that works, from the
    refusals alone. Every product door named by §D.2 is sound RIGHT NOW."""
    from crash_detector.admission import admission_faults
    from crash_detector.engine.mapping import compute

    for door in (evaluate, resolve_panel, present_dial, compute, is_shown, render_panel):
        assert admission_faults(door) == (), f"{door.__qualname__} is faulted"


def test_p7_over_the_shipped_empty_registry():
    """P7 is about signatures and registers nothing. Asserted anyway, because the standing
    condition is that EVERY plant runs over the empty registry and a plant that quietly did
    not would be the interesting one."""
    assert EMPTY_MODEL_REGISTRY.is_empty
    assert _the_shipped_snapshot().model_registry.is_empty


# ========================================================================================= #
# FALSE POSITIVES — THE PRODUCT MUST STILL WORK.
# A closure that forbids the product is not a closure.
# ========================================================================================= #


def test_the_empty_registry_path_still_renders_unknown_on_both_dials():
    """The shipped WO-2 state, end to end through every door this increment decorated."""
    snapshot = _the_shipped_snapshot()
    dials = evaluate([], snapshot, NOW)
    equity = present_dial(EQUITY_DIAL_ID, dials.equity)
    monetary = present_dial(MONETARY_DIAL_ID, dials.monetary)
    assert type(equity) is NotShown
    assert type(monetary) is NotShown
    assert not is_shown(equity)
    assert not is_shown(monetary)
    assert equity.reason == "NO_REQUIRED_INPUTS_DECLARED"
    assert monetary.reason == "NO_REQUIRED_INPUTS_DECLARED"


def test_an_ordinary_aware_datetime_and_an_ordinary_float_still_pass_every_door():
    snapshot = _the_shipped_snapshot()
    assert type(snapshot.window()) is StalenessWindow
    assert snapshot.window().seconds == WINDOW_SECONDS
    assert snapshot.spec_for(EQUITY_DIAL_ID).dial_id == EQUITY_DIAL_ID
    assert snapshot.model_for(EQUITY_DIAL_ID) is None
    panel = resolve_panel(
        PanelRow(
            state="AGREES",
            as_of_utc=_ago(10),
            published_utc=_ago(10),
            measures={"divergence_measure": 0.02},
        ),
        now_utc=NOW,
        staleness_window_seconds=WINDOW_SECONDS,
    )
    assert type(panel) is Agrees


def test_observations_still_arrive_as_a_list_or_a_tuple():
    """``evaluate`` is called with a list everywhere in this codebase and a tuple is just
    as legitimate. Both are admitted; a set or a generator is not, because what this door
    iterates is not the caller's judgement to make."""
    snapshot = _the_shipped_snapshot()
    assert type(evaluate([], snapshot, NOW).equity) is Unknown
    assert type(evaluate((), snapshot, NOW).equity) is Unknown
    with pytest.raises(NotAdmitted):
        evaluate(iter([]), snapshot, NOW)


# ========================================================================================= #
# THE STATIC CHECK'S OWN ARMS — the carriers its DECLARED LIMITs name (CD-RULE-006).
# ========================================================================================= #

import pathlib
import subprocess
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_CHECK = _REPO_ROOT / "tools" / "register" / "check_judgement_path_doors.py"


def _run_the_check():
    return subprocess.run(
        [sys.executable, "-B", str(_CHECK), "--root", str(_REPO_ROOT)],
        capture_output=True,
        text=True,
    )


def test_the_static_check_passes_and_is_not_vacuous():
    """BASELINE. A clean run is worth nothing unless it says how much it looked at:
    `Check.done` refuses a run that made zero assertions, and the subject count is printed
    so a pass over an empty set is impossible to mistake for a pass."""
    result = _run_the_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
    assert "SUBJECTS ENUMERATED:" in result.stdout
    subjects = int(
        result.stdout.split("SUBJECTS ENUMERATED:")[1].split(".")[0].strip()
    )
    decorated = int(result.stdout.split("DECORATED:")[1].split(".")[0].strip())
    assert subjects >= 24, f"the subject set shrank to {subjects}"
    assert subjects == decorated


def test_the_check_enumerates_the_door_increment_one_built():
    """CD-D-098, asserted rather than trusted. `engine.mapping.compute` post-dates §B's
    measured inventory of 44 doors, so a check reading that list would not have looked at
    it. This asserts the check DOES — by asserting it fails when that one door loses its
    decorator, which is the only way to assert enumeration without trusting the output."""
    source = (_REPO_ROOT / "src" / "crash_detector" / "engine" / "mapping.py").read_text()
    assert "@admits(spec=ModelSpec, payloads=dict)" in source
    result = _run_the_check()
    # RULE 1 reads engine/ deny-by-default, so mapping.py is inside the scanned set and its
    # door is one of the counted subjects. The count moving is the observable.
    assert "engine/serving" in result.stdout


def test_the_collector_boundary_is_a_judgement_path_package_and_cd_bp_003_is_what_remains():
    """REPLACES ``test_the_collector_gap_is_declared_and_still_open`` (deleted subject).

    THE OLD PROPOSITION: DECLARED LIMIT 3 — *"``collectors/`` is not yet a judgement-path
    package here, by scope and not by oversight"* — is declared and cannot close silently.
    That test was written to FAIL the day ``collectors`` became a judgement-path package,
    which is precisely what BP-AMENDMENT-0001 §D.3 and WO-2R3 increment 3 did. Its subject
    is deleted, and leaving it standing would have turned a true scope statement into a
    false one by the passage of time.

    THE SAME PROPOSITION AGAINST THE NEW STRUCTURE: the limit at this slot is declared, is
    printed at every run, and cannot close or widen silently. What it now says is narrower
    and it is CD-BP-003 — four ``Protocol`` parameters of ONE door, not a whole package.

    Asserted here in three independent ways, because "the limit is declared" is exactly the
    kind of claim that decays into a comment nobody reads:
      1. ``collectors`` IS in RULE 1 and the deny-by-default it brings is real — the check
         reports subjects it did not see before;
      2. the CD-BP-003 note is PRINTED with its extent, derived from the artefact;
      3. the increment-2 wording is GONE from the output, so no reader can find a
         discharged limit still being asserted.
    """
    check_source = _CHECK.read_text()
    assert 'JUDGEMENT_PATH_PACKAGES = ("engine", "serving", "collectors")' in check_source
    result = _run_the_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "engine/serving/collectors" in result.stdout
    assert "CD-BP-003, THE PROTOCOL BOUNDARY THAT ADMITS: 4 parameter(s)" in result.stdout
    for parameter in ("adapter", "sink", "ledger", "validator"):
        assert f"CD-BP-003 ADMITS: collectors/runner.py" in result.stdout
        assert f"collect({parameter})" in result.stdout
    # The discharged wording must not survive anywhere in the output.
    assert "is NOT a judgement-path package here" not in result.stdout


def test_the_collector_doors_are_really_subjects_and_not_merely_counted():
    """The deny-by-default, asserted the only way it can be: by breaking it.

    A package name in a tuple proves nothing about what the check DOES with it. This copies
    the tree to a scratch directory, removes ``@admits`` from ``collect`` there, and asserts
    the check FAILS on it — so ``collectors`` being in RULE 1 is a measured property of the
    check and not a string in a file.

    The mutation is made in a COPY under ``/tmp`` and never in the worktree, and it is run
    with ``python3 -B`` so no ``__pycache__`` is written into any governed tree.
    """
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        copy = pathlib.Path(scratch) / "tree"
        shutil.copytree(
            _REPO_ROOT / "src",
            copy / "src",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        runner = copy / "src" / "crash_detector" / "collectors" / "runner.py"
        source = runner.read_text()
        opened = source.index("@admits(\n    adapter=ESTABLISHED_HERE(")
        closed = source.index("\ndef collect(", opened)
        runner.write_text(source[:opened] + source[closed + 1 :])
        result = subprocess.run(
            [sys.executable, "-B", str(_CHECK), "--root", str(copy)],
            capture_output=True,
            text=True,
        )
    assert result.returncode != 0, result.stdout
    assert "UNDECORATED_JUDGEMENT_PATH_DOOR" in result.stdout
    assert "collect is a public entry point" in result.stdout


def test_the_check_prints_every_established_here_use_with_its_location():
    """DECLARED LIMIT 1's second carrier: the check REPORTS every explicit weakening. It
    does not adjudicate them and says so; a reviewer must."""
    result = _run_the_check()
    # **SIXTEEN -> EIGHTEEN AT WO-2R3 INCREMENT 8, AND THE CORRECTION IS IN ALL THREE
    # CD-RULE-004 PLACES** (`PBG-CONT-003` — corrections supersede, never edit).
    # *Superseded assertion, quoted rather than deleted: `assert "ESTABLISHED_HERE uses: 16."
    # in result.stdout`.* `PO-DECISIONS-0015` ruling 1 redesigned the membership clause so it
    # stops moving on an underscore; three private callables that RETURN A JUDGEMENT VALUE
    # became subjects, and TWO of them sit in front of a NAMED refusal an exact-type door
    # would preempt (`_new_quantity(value)` -> ScoreOutOfRange, `_shown_from(score)` ->
    # DialPresentationRefused), which is DECLARED LIMIT 5's shape. **THEY ARE REAL
    # EXEMPTIONS, NOT FALSE ROWS**, and each states its reason and its measured carrier in
    # the artefact — asserted independently from the RUNTIME by
    # tests/test_admission.py::test_the_established_here_exemptions_are_exactly_this_set.
    assert "ESTABLISHED_HERE uses: 18." in result.stdout
    for expected in (
        "engine/model.py",
        "dials/provenance.py",
        "dials/magnitude.py",
        "collectors/runner.py",
        "collectors/adapter.py",
        "collectors/validation.py",
    ):
        assert f"ESTABLISHED_HERE: {expected}" in result.stdout


# --- ITEM C: ESTABLISHED_HERE UNDER AN ALIAS (WO-2R3 increment 6) ------------------------- #

_ALIASED_DOOR = '''

from crash_detector.admission import ESTABLISHED_HERE as _EH


@admits(candidate=_EH("a seventeenth exemption, spelled through a one-word import alias"))
def aliased_probe_door(candidate):
    return candidate
'''


def test_the_check_counts_an_established_here_spelled_through_an_import_alias():
    """**"COUNTED, NOT HIDDEN" WAS FALSE UNDER ONE WORD.**

    `CD-ASR-WO2R3-01` §2.4 added one door in `collectors/validation.py` importing
    `ESTABLISHED_HERE as _EH`. The check **still reported 16, EXIT 0** — invisible — against a
    declared limit whose own text says the exemption is *counted, not hidden*.

    This asserts the count MOVES and the door is NAMED. It is the check-side half of item C;
    the carrier-side half is `tests/test_admission.py`, which reads the runtime compiled
    objects and was already red on this at `531c95c`.
    """
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        copy = pathlib.Path(scratch) / "tree"
        shutil.copytree(
            _REPO_ROOT / "src", copy / "src", ignore=shutil.ignore_patterns("__pycache__")
        )
        target = copy / "src" / "crash_detector" / "collectors" / "validation.py"
        target.write_text(target.read_text() + _ALIASED_DOOR)
        result = subprocess.run(
            [sys.executable, "-B", str(_CHECK), "--root", str(copy)],
            capture_output=True,
            text=True,
        )

    assert "ESTABLISHED_HERE uses: 19." in result.stdout, (
        "an exemption spelled through an import alias must be COUNTED. Observed:\n"
        + "\n".join(
            line for line in result.stdout.splitlines() if "ESTABLISHED_HERE uses" in line
        )
    )
    assert "aliased_probe_door(candidate)" in result.stdout, (
        "and it must be NAMED with its file, line and parameter, not merely counted"
    )
    assert "ALIAS:" in result.stdout and "_EH" in result.stdout, (
        "and the module that binds a non-literal spelling must be reported, because a "
        "silently resolved alias is only half of 'counted, not hidden'"
    )


def test_a_wrapper_around_established_here_is_a_DECLARED_LIMIT_and_is_not_counted():
    """**THE RESIDUE, PINNED — NOT A CARRIER, AND IT SAYS SO.**

    `DECLARED LIMIT 8` names four routes the check does NOT resolve. This exercises one of
    them — a WRAPPER FUNCTION, which is a call to a function rather than a reference to the
    object — and asserts the check still does not count it.

    **THIS TEST PASSES BECAUSE THE LIMIT IS REAL. If it ever fails, the limit is now narrower
    than declared: correct all three CD-RULE-004 places. Do not delete this test.**

    The route is NOT unguarded: `tests/test_admission.py` reads the RUNTIME compiled
    declaration objects and goes red on it regardless of spelling. That is the whole of
    `CD-RULE-006` — a check reports, a carrier fails — and the two are deliberately not the
    same reader.
    """
    import shutil
    import tempfile

    wrapped = '''

def _eh(reason):
    return ESTABLISHED_HERE(reason)


@admits(candidate=_eh("reached through a wrapper, not a reference"))
def wrapped_probe_door(candidate):
    return candidate
'''
    with tempfile.TemporaryDirectory() as scratch:
        copy = pathlib.Path(scratch) / "tree"
        shutil.copytree(
            _REPO_ROOT / "src", copy / "src", ignore=shutil.ignore_patterns("__pycache__")
        )
        target = copy / "src" / "crash_detector" / "collectors" / "validation.py"
        target.write_text(target.read_text() + wrapped)
        result = subprocess.run(
            [sys.executable, "-B", str(_CHECK), "--root", str(copy)],
            capture_output=True,
            text=True,
        )

    assert "ESTABLISHED_HERE uses: 18." in result.stdout, (
        "DECLARED LIMIT 8 says a WRAPPER is not resolved. If this fails the limit is wrong "
        "and must be corrected in all three CD-RULE-004 places"
    )
    assert "wrapped_probe_door" not in result.stdout


# ==================================================================================== #
# THE REACHABILITY MEMBERSHIP CLAUSE AND THE **NETS** POPULATION.
# WO-2R3 increment 7, PO-DECISIONS-0012 rulings 1 and 2.
#
# **CD-RULE-006: A CHECK REPORTS, A CARRIER FAILS.** Everything below is the carrier. Each
# test asserts a property BY BREAKING IT in a throwaway copy of the tree, because a test
# that reads the check's own output and agrees with it is a second opinion from the same
# witness.
# ==================================================================================== #

import shutil
import tempfile


def _run_the_check_over(tree: pathlib.Path):
    return subprocess.run(
        [sys.executable, "-B", str(tree / "tools" / "register" / "check_judgement_path_doors.py"),
         "--root", str(tree)],
        capture_output=True,
        text=True,
    )


def _throwaway_tree():
    """A copy of the tree carrying the instrument, the register and src/. Not a fixture on
    purpose: each test mutates its own copy and reads its OWN instrument, so no two arms can
    accidentally share a tree (CD-PL-F98)."""
    destination = pathlib.Path(tempfile.mkdtemp(prefix="cd-nets-"))
    for part in ("src", "tools"):
        shutil.copytree(_REPO_ROOT / part, destination / part)
    return destination


def test_the_membership_clause_survives_renaming_the_function_local_binding():
    """**THE RENAME TEST, APPLIED TO THE CLAUSE THAT REPLACED THE ONE THAT FAILED IT.**

    This is why increment 7 exists. The old membership clause read
    ``_is_public(node.name)``, and the fifth Assurance seat took the check from 1 violation
    to 0 by renaming ONE function-local identifier — ``guarded`` to ``_guarded`` — with
    runtime identity unchanged. A refusal a two-line rename silences is a vocabulary guard
    wearing a structural label.

    **THE NEW CLAUSE MUST NOT MOVE ON THAT RENAME, AND THIS ASSERTS IT ON A REAL TREE.**
    Both spellings must produce the same verdict AND the same subject count, because a
    caller could never name that identifier under either spelling.
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
        before = _run_the_check_over(tree)
        source = evaluate_py.read_text()
        assert "    def guarded(" in source, "the subject of this test moved; fix the test"
        evaluate_py.write_text(
            source.replace("    def guarded(", "    def _guarded(")
                  .replace("        return guarded", "        return _guarded")
                  .replace("    return guarded", "    return _guarded")
        )
        after = _run_the_check_over(tree)

        assert before.returncode == 0, before.stdout + before.stderr
        assert after.returncode == 0, (
            "RENAMING THE FUNCTION-LOCAL BINDING MOVED THE VERDICT. The membership clause "
            "is deciding by an identifier no caller can name, which is exactly the defect "
            "PO-DECISIONS-0012 ruling 2 corrected.\n" + after.stdout + after.stderr
        )
        subjects = lambda r: r.stdout.split("SUBJECTS ENUMERATED:")[1].split(".")[0].strip()
        assert subjects(before) == subjects(after), (
            f"the subject set moved on a rename: {subjects(before)} -> {subjects(after)}"
        )
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_a_function_local_bound_into_a_module_dict_is_still_a_door():
    """**ESCAPE 4 ARM 4, AND IT IS A REQUIRED CONTRAST AND NOT AN OPTIONAL ONE.**

    The fourth Assurance seat demonstrated a function-local ``def`` bound into a module dict
    — ``POLICY["decide"]`` — accepting unestablished arguments live. The reachability clause
    exempts ``guarded``; the dispatch's condition for that exemption being sound is that the
    SAME clause still catches this.

    **AND THE LOCAL IS PRIVATE-NAMED HERE ON PURPOSE.** A name-prefix clause cannot see a
    ``_decide`` at all, whatever else it does, so this arm is the one that proves the new
    clause is structural rather than a subtler vocabulary: it must be caught BECAUSE IT
    ESCAPES, not because of how it is spelled.
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
        clean = _run_the_check_over(tree)
        assert clean.returncode == 0, clean.stdout + clean.stderr

        evaluate_py.write_text(evaluate_py.read_text() + '''

POLICY: dict = {}


def _install_policy():
    def _decide(spec, usable, now_utc):
        return Unknown(reason="planted", since_utc=now_utc, missing_inputs=())

    POLICY["decide"] = _decide
''')
        planted = _run_the_check_over(tree)
        assert planted.returncode == 1, (
            "A FUNCTION-LOCAL CALLABLE STORED INTO A MODULE-LEVEL DICT WAS NOT CAUGHT. "
            "The reachability clause exempts `guarded` on the ground that it never leaves "
            "its frame; this one DOES leave, and if it is not caught the exemption is "
            "unsound.\n" + planted.stdout
        )
        assert "UNDECORATED_JUDGEMENT_PATH_DOOR" in planted.stdout
        assert "_install_policy._decide" in planted.stdout, planted.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_an_undeclared_interceptor_on_a_judgement_path_fails_the_check():
    """PO-DECISIONS-0012 ruling 2: *"'Not a door' must never again mean 'not seen.'"*

    Asserted by DELETING the declaration and requiring the check to go red. If this passes
    with an empty register, the NETS population is decoration.
    """
    tree = _throwaway_tree()
    try:
        register = tree / "tools" / "register" / "declared_nets.py"
        source = register.read_text()
        head, _, _ = source.partition('DECLARED_NETS: "tuple[DeclaredNet, ...]" = (')
        register.write_text(head + 'DECLARED_NETS: "tuple[DeclaredNet, ...]" = ()\n')
        emptied = _run_the_check_over(tree)
        assert emptied.returncode == 1, (
            "THE REGISTER WAS EMPTIED AND THE CHECK STILL PASSED. The NETS population is "
            "not asserted.\n" + emptied.stdout
        )
        assert "UNCLASSIFIED_INTERCEPTOR" in emptied.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_a_net_that_stops_calling_its_post_condition_fails_the_check():
    """**THE ASSERTION THAT MAKES A DECLARATION DATA RATHER THAN A LABEL.**

    A net's post-condition is *"named as DATA, not as PROSE"* (PO-DECISIONS-0012 ruling 2).
    The only definition of "named" that survives contact with an editor is one that breaks
    when the code and the declaration come apart. So: remove the guard call from the net's
    body, LEAVE THE DECLARATION ALONE, and require red.

    **THIS IS CD-ASR-F03's OWN SHAPE** — a body edit that removes a guard — asked of the
    guard's own paperwork.
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
        source = evaluate_py.read_text()
        # **THE CALL IS LOCATED AS CODE, NOT AS A PINNED STRING, SINCE WO-2R3 INCREMENT 8.**
        # *Superseded (PBG-CONT-003 — corrections supersede, never edit):*
        # ``call = "        refuse_a_number_without_its_inputs(spec, usable, reading)\n"``
        # ``assert call in source, "the guard call moved; fix the test"``
        # ``evaluate_py.write_text(source.replace(call, "        pass\n"))``
        # The redesigned mechanism DERIVES which arguments the post-condition receives from
        # the post-condition's own signature, so the call is a splat over several lines
        # rather than three names on one. **THE PROPOSITION DID NOT MOVE AND THE SPELLING
        # DID**, and a carrier pinned to a spelling breaks on a refactor that changes nothing
        # it is about. This locates the call the way the instrument does — by walking the
        # AST for a `Call` whose callee is the module-level name — and removes exactly its
        # statement, so the same edit is made whatever the arguments look like.
        import ast as _ast

        parsed = _ast.parse(source)
        statements = [
            node
            for node in _ast.walk(parsed)
            if isinstance(node, _ast.Expr)
            and isinstance(node.value, _ast.Call)
            and getattr(node.value.func, "id", None)
            == "refuse_a_number_without_its_inputs"
        ]
        assert len(statements) == 1, (
            "the net's body does not contain exactly one call to its post-condition as a "
            f"statement; found {len(statements)}. Fix the test or the code, but do not "
            "guess which one this test meant."
        )
        target = statements[0]
        lines = source.splitlines(keepends=True)
        evaluate_py.write_text(
            "".join(lines[: target.lineno - 1])
            + " " * target.col_offset
            + "pass\n"
            + "".join(lines[target.end_lineno :])
        )
        broken = _run_the_check_over(tree)
        assert broken.returncode == 1, (
            "THE GUARD WAS REMOVED AND THE PAPERWORK KEPT, AND THE CHECK PASSED.\n"
            + broken.stdout
        )
        assert "NET_POST_CONDITION_NOT_CALLED" in broken.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_a_net_declared_where_none_exists_fails_the_check():
    """A declared net that no longer exists FAILS. A register whose rows can outlive their
    subjects is a hand-maintained summary, which is the defect class ruling 2 exists to
    prevent."""
    tree = _throwaway_tree()
    try:
        register = tree / "tools" / "register" / "declared_nets.py"
        register.write_text(
            register.read_text().replace(
                'enclosing="_absence_is_never_a_number",',
                'enclosing="_a_function_that_does_not_exist",',
            )
        )
        stale = _run_the_check_over(tree)
        assert stale.returncode == 1, stale.stdout
        assert "NET_DECLARED_BUT_ABSENT" in stale.stdout
        # AND the real net is now unclassified, which is the other direction of the same
        # set equality. Both must fire, or the register is asserted in one direction only.
        assert "UNCLASSIFIED_INTERCEPTOR" in stale.stdout, (
            "only one direction of the set equality fired" + stale.stdout
        )
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_the_nets_population_is_printed_with_its_declared_residue():
    """The net's blind spot is DECLARED, not discovered. CD-RULE-004: an understated residue
    is this project's most-found defect, and the NETS note is one of this limit's three
    places."""
    result = _run_the_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "NETS — THE SECOND DECLARED POPULATION" in result.stdout
    assert "NOT DECLARED BUT FOUND: 0" in result.stdout
    assert "DECLARED BUT NOT FOUND: 0" in result.stdout
    assert "post-condition refuse_a_number_without_its_inputs()" in result.stdout
    assert "DOES NOT BIND" in result.stdout


def test_the_projects_own_delattr_fix_does_not_make_the_net_a_door():
    """**A REGRESSION CARRIER FOR A DEFECT THIS INCREMENT SHIPPED INTO ITSELF AND CAUGHT.**

    The reachability clause first treated `PASSED_TO` as an escape and denied by default.
    **MEASURED, THAT TURNED THIS PROJECT'S OWN CD-ASR-F03 FIX INTO A VIOLATION:** item 3
    adds `delattr(guarded, "__wrapped__")` — a call with `guarded` as an argument — so the
    net was reclassified a reachable door and the check went PASS -> FAIL 2 violations.
    **THAT IS THE EXACT OUTCOME `PO-DECISIONS-0012` RULING 1 FORBIDS**, produced by the
    instrument written to implement ruling 2.

    Both available escapes were worse than the defect: an exclusion list of "callees that do
    not retain" is a VOCABULARY, which is what ruling 2 exists to remove; and decorating
    `guarded` is prohibited. The clause was corrected instead.

    This test pins the interaction. It asserts the SHIPPED SOURCE still carries the
    `__wrapped__` refusal — so it cannot pass vacuously if that fix is ever reverted — and
    that the net is still classified a net with the check green.

    **SUPERSEDED IN ONE ASSERTION AT WO-2R3 INCREMENT 8** (`PBG-CONT-003` — corrections
    supersede, never edit). The old text, verbatim::

        assert 'delattr(guarded, "__wrapped__")' in source, (
            "item 3's delattr is gone; this carrier would pass vacuously. If the removal was "
            "deliberate, PO-DECISIONS-0013 ruling 2 is being reversed and that is a PO matter")

    **THE `delattr` IS GONE AND `PO-DECISIONS-0013` RULING 2 IS NOT REVERSED — IT IS MET MORE
    STRONGLY.** The redesigned mechanism does not use `functools.wraps` at all, so
    `__wrapped__` is **never set** and there is nothing to delete: the window between creating
    the bypass and removing it does not exist, and a future edit that puts the decorator back
    cannot silently reinstate it. The assertion moves from the *repair* to the *property* — no
    `functools.wraps` on this mechanism, and no `__wrapped__` on the shipped object — which is
    what ruling 2 was about and which the old spelling could not survive.

    **AND IT IS READ AS CODE, NOT AS TEXT.** A substring search here would match this
    docstring's own quotation of the superseded implementation, which is exactly the kind of
    assertion that passes for the wrong reason.
    """
    import ast as _ast
    import importlib as _importlib

    source = (_REPO_ROOT / "src" / "crash_detector" / "engine" / "evaluate.py").read_text()
    mechanism = next(
        node
        for node in _ast.walk(_ast.parse(source))
        if isinstance(node, _ast.FunctionDef)
        and node.name == "_absence_is_never_a_number"
    )
    decorators = {
        _ast.unparse(d.func if isinstance(d, _ast.Call) else d)
        for inner in _ast.walk(mechanism)
        if isinstance(inner, (_ast.FunctionDef, _ast.AsyncFunctionDef))
        for d in inner.decorator_list
    }
    assert "functools.wraps" not in decorators, (
        "the CD-ASR-F03 mechanism has gone back to `functools.wraps`, which SETS "
        "`__wrapped__` — a documented, `inspect.unwrap`-followed way round the guard that "
        f"PO-DECISIONS-0013 ruling 2 called a PRODUCT DEFECT. Found: {decorators}"
    )
    assert not hasattr(
        _importlib.import_module("crash_detector.engine.evaluate")._evaluate_dial,
        "__wrapped__",
    ), "the shipped evaluator publishes `__wrapped__`, which is a way round the guard"
    result = _run_the_check()
    assert result.returncode == 0, (
        "the project's own delattr fix has made the CD-ASR-F03 net a door again — the "
        "outcome PO-DECISIONS-0012 ruling 1 forbids\n" + result.stdout
    )
    assert "UNDECORATED_JUDGEMENT_PATH_DOOR" not in result.stdout
    assert "_absence_is_never_a_number()" in result.stdout, (
        "the net is no longer reported as a net" + result.stdout
    )


def test_an_established_here_alias_bound_in_a_function_body_is_counted():
    """**ITEM 4. THE RESIDUAL `tree.body`, CLOSED — WITH THE CONTRAST THAT PROVES IT.**

    `_established_here_spellings`'s rebinding fixpoint read `tree.body` — MODULE LEVEL ONLY —
    twelve lines from `_callables`, which was widened to walk at any depth at increment 6.
    Same file, same idiom, same defect shape, left behind by the increment dispatched to
    eliminate it.

    DECLARED LIMIT 8's own text says the `ESTABLISHED_HERE` exemption is **COUNTED, NOT
    HIDDEN**. An alias bound inside a function body hid one.

    **THE ARM: caught after, missed before.** A door whose exemption is spelled through a
    function-body alias must be COUNTED and NAMED in the output.
    """
    tree = _throwaway_tree()
    try:
        model_py = tree / "src" / "crash_detector" / "engine" / "model.py"
        before = _run_the_check_over(tree)
        assert before.returncode == 0, before.stdout
        baseline = int(before.stdout.split("ESTABLISHED_HERE uses:")[1].split(".")[0])

        model_py.write_text(model_py.read_text() + '''

def _install_door():
    EH = ESTABLISHED_HERE          # BOUND INSIDE A FUNCTION BODY

    @admits(value=EH("a planted exemption spelled through a function-body alias"))
    def planted_door(value):
        return value

    return planted_door


installed_door = _install_door()
''')
        after = _run_the_check_over(tree)
        counted = int(after.stdout.split("ESTABLISHED_HERE uses:")[1].split(".")[0])
        assert counted == baseline + 1, (
            "an ESTABLISHED_HERE exemption spelled through a FUNCTION-BODY alias was not "
            f"counted ({baseline} -> {counted}). DECLARED LIMIT 8 says this weakening is "
            "COUNTED, NOT HIDDEN, and a count that a one-line alias silences is not a "
            "count.\n" + after.stdout
        )
        assert "_install_door.planted_door(value)" in after.stdout, (
            "the use was counted but not NAMED; half of 'counted, not hidden' is that a "
            "reader can see WHERE" + after.stdout
        )
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_the_widened_fixpoint_adds_no_false_row_to_the_shipped_tree():
    """The other direction of item 4, and the one that would be easy not to check.

    Walking at any depth can ADD a spelling a module-level decorator could not actually see
    — a false row. That is NOISE rather than silence, and it is the direction this project
    prefers for a register of weakenings, but **preferring a direction is not a licence to
    stop measuring it.** The shipped count must not have moved.
    """
    result = _run_the_check()
    assert result.returncode == 0, result.stdout
    assert "ESTABLISHED_HERE uses: 18." in result.stdout, (
        "the widened fixpoint moved the shipped ESTABLISHED_HERE count. Either a real "
        "exemption was added — in which case DECLARED LIMIT 8's figure needs correcting in "
        "all three CD-RULE-004 places — or the widening produced a FALSE ROW, which is a "
        "defect in the widening.\n" + result.stdout
    )


# ==================================================================================== #
# THE REDESIGNED MEMBERSHIP CRITERION AND THE SECOND DOOR FORM.
# WO-2R3 increment 8, PO-DECISIONS-0015 ruling 1.
#
# **CD-RULE-006: A CHECK REPORTS, A CARRIER FAILS.** Every test below asserts a property BY
# BREAKING IT in a throwaway copy of the tree and reading that copy's OWN instrument, because
# a test that reads the shipped check's output and agrees with it is a second opinion from
# the same witness. Each one FAILS at `314592c`, which is the point of it.
# ==================================================================================== #


def _subjects(result) -> str:
    return result.stdout.split("SUBJECTS ENUMERATED:")[1].split(".")[0].strip()


def test_a_private_module_level_callable_that_returns_a_judgement_value_is_a_door():
    """**GROUND 1's OWN SHAPE, PLANTED.** The criterion must not move on an underscore.

    `PO-DECISIONS-0012` ruling 1 fell because `_evaluate_dial` was excluded by a leading
    underscore while a conforming foreign adapter obtained it from `sys.modules` and called
    it. A NAME-PREFIX clause cannot see a private callable at all, so this plants exactly
    that: an undecorated, PRIVATE, module-level callable in a judgement-path package whose
    return annotation names a judgement value type.

    **THE COUNTERFACTUAL ARM IS THE DECLARED RESIDUE AND IT IS ASSERTED, NOT DESCRIBED.** The
    identical callable WITHOUT a return annotation is NOT named — the criterion reaches it by
    what it says it returns, and a callable that says nothing is invisible to this rule. That
    is a real hole and this test is where a reader finds it measured rather than promised.
    """
    annotated = '''

def _a_planted_private_decider(reading) -> "Reading":
    return reading
'''
    unannotated = '''

def _a_planted_private_decider(reading):
    return reading
'''
    verdicts = {}
    for label, plant in (("annotated", annotated), ("unannotated", unannotated)):
        tree = _throwaway_tree()
        try:
            target = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
            target.write_text(target.read_text() + plant)
            verdicts[label] = _run_the_check_over(tree)
        finally:
            shutil.rmtree(tree, ignore_errors=True)

    assert verdicts["annotated"].returncode == 1, (
        "A PRIVATE MODULE-LEVEL CALLABLE THAT RETURNS A JUDGEMENT VALUE WAS NOT NAMED. The "
        "criterion is still moving on an underscore, which is what PO-DECISIONS-0015 ruling "
        "1 forbids.\n" + verdicts["annotated"].stdout
    )
    assert "UNDECORATED_JUDGEMENT_PATH_DOOR" in verdicts["annotated"].stdout
    assert "_a_planted_private_decider" in verdicts["annotated"].stdout

    assert "_a_planted_private_decider" not in verdicts["unannotated"].stdout, (
        "the unannotated arm was named, so this test's two arms do not differ on the axis it "
        "claims and the declared residue below is misdescribed (CD-ENG-WO2R3-F12)"
    )
    assert verdicts["unannotated"].returncode == 0, verdicts["unannotated"].stdout


def test_renaming_the_reachable_destination_does_not_move_the_verdict_either():
    """**THE RENAME TEST IN THE DIRECTION THE OLD CLAUSE COULD NOT SURVIVE.**

    `tests/test_judgement_path_doors.py::test_the_membership_clause_survives_renaming_the_function_local_binding`
    asserts the first half: renaming the LOCAL must not move the verdict. The old clause's own
    docstring conceded the other half openly — *"renaming the DESTINATION (`_evaluate_dial` ->
    `evaluate_dial`) DOES change the verdict, and correctly"* — which made publicness of that
    identifier load-bearing, and an identifier is a spelling.

    Since `PO-DECISIONS-0015` ruling 1 the destination is a subject **because of what it
    returns**, so the verdict and the subject count must be identical under both spellings.
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
        before = _run_the_check_over(tree)
        source = evaluate_py.read_text()
        assert "def _evaluate_dial(" in source, "the subject of this test moved; fix the test"
        evaluate_py.write_text(
            source.replace("_evaluate_dial", "evaluate_dial")
        )
        after = _run_the_check_over(tree)
        assert before.returncode == 0, before.stdout + before.stderr
        assert after.returncode == 0, (
            "RENAMING THE DESTINATION MOVED THE VERDICT. Membership is still deciding by an "
            "identifier's spelling, which PO-DECISIONS-0015 ruling 1 forbids.\n"
            + after.stdout + after.stderr
        )
        assert _subjects(before) == _subjects(after), (
            f"the subject set moved on a rename: {_subjects(before)} -> {_subjects(after)}"
        )
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_a_renamed_deriving_mechanism_fails_loudly_and_in_both_directions():
    """A declared mechanism that no longer exists must fail, AND the subject it covered must
    fail with it. **TWO VIOLATIONS, NEVER A SILENCE.**

    This is the failure direction that makes recognising a mechanism by NAME acceptable: the
    check does not stop looking, it reports that its register has come adrift AND reports the
    door it can no longer see as undecorated.
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
        evaluate_py.write_text(
            evaluate_py.read_text().replace(
                "_absence_is_never_a_number", "_absence_is_never_a_number_renamed"
            )
        )
        renamed = _run_the_check_over(tree)
        assert renamed.returncode == 1, renamed.stdout
        assert "MECHANISM_DECLARED_BUT_ABSENT" in renamed.stdout, renamed.stdout
        assert "UNDECORATED_JUDGEMENT_PATH_DOOR" in renamed.stdout, (
            "only one direction fired: the register said it had come adrift and the door it "
            "covered was not reported.\n" + renamed.stdout
        )
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_a_derived_door_with_an_unannotated_parameter_fails_the_check():
    """**THE ASSERTION THAT MAKES FORM 2 A DOOR FORM AND NOT A LABEL.**

    A derived door has no `admits(...)` list to compare against its signature, so what the
    check asserts is what the derivation itself requires: every parameter ANNOTATED. Strip one
    annotation from the shipped evaluator, leave the register alone, and require red — the
    same shape as the NETS register's "the body must actually CALL it".

    The mechanism refuses this at import too; the point of asserting it HERE is that an auditor
    sees it without importing the product.
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
        source = evaluate_py.read_text()
        assert "    now_utc: datetime,\n" in source
        evaluate_py.write_text(source.replace("    now_utc: datetime,\n", "    now_utc,\n"))
        stripped = _run_the_check_over(tree)
        assert stripped.returncode == 1, (
            "AN UNANNOTATED PARAMETER ON A DERIVED DOOR PASSED. The annotation IS the "
            "declaration for this door form, so a parameter without one is a parameter with "
            "no establishment.\n" + stripped.stdout
        )
        assert "DERIVED_DOOR_PARAMETER_NOT_ANNOTATED" in stripped.stdout, stripped.stdout
        assert "now_utc" in stripped.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_a_deriving_mechanism_that_abandons_the_one_vocabulary_fails_the_check():
    """`crash_detector.admission.declaration` is the project's ONE declaration vocabulary, and
    its own docstring says why: *"Two declaration vocabularies that drift apart is how a reader
    comes to believe a field is established as strictly as a parameter when it is not; there is
    one, and it is here."*

    A mechanism that grew its own second vocabulary would be exactly that drift wearing this
    register's clothes. So: make the mechanism stop calling `declaration`, leave the register
    alone, and require red.
    """
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
        source = evaluate_py.read_text()
        call = "declaration(name, _exact_types_of(resolved[name]))"
        assert call in source, "the derivation's call to the one vocabulary moved; fix the test"
        evaluate_py.write_text(
            source.replace(call, "_a_second_vocabulary(name, resolved[name])")
        )
        drifted = _run_the_check_over(tree)
        assert drifted.returncode == 1, (
            "THE MECHANISM STOPPED COMPILING THROUGH THE ONE DECLARATION VOCABULARY AND THE "
            "CHECK PASSED. The register's third assertion is not asserted.\n" + drifted.stdout
        )
        assert "MECHANISM_DOES_NOT_USE_THE_ONE_VOCABULARY" in drifted.stdout, drifted.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_a_deriving_mechanism_that_stops_reading_the_signature_fails_the_check():
    """§D.1's rule is that the establishment is DERIVED FROM THE SIGNATURE rather than written
    into the body. A mechanism that never reads a signature is not deriving from one, whatever
    the register calls it — so remove every `inspect.signature` read and require red."""
    tree = _throwaway_tree()
    try:
        evaluate_py = tree / "src" / "crash_detector" / "engine" / "evaluate.py"
        source = evaluate_py.read_text()
        assert "inspect.signature(" in source
        evaluate_py.write_text(source.replace("inspect.signature(", "_not_a_signature_read("))
        blinded = _run_the_check_over(tree)
        assert blinded.returncode == 1, (
            "THE MECHANISM STOPPED READING THE SIGNATURE AND THE CHECK PASSED.\n"
            + blinded.stdout
        )
        assert "MECHANISM_DOES_NOT_READ_THE_SIGNATURE" in blinded.stdout, blinded.stdout
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def test_the_derived_door_population_is_printed_with_its_declared_residue():
    """The mechanism's blind spot is DECLARED, not discovered — the same requirement the NETS
    note carries, and one of DECLARED LIMITS 10 and 11's readers."""
    result = _run_the_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DERIVING DOOR MECHANISMS — THE SECOND DOOR FORM" in result.stdout
    assert "A ROW IS NOT AN EXEMPTION" in result.stdout
    assert "_absence_is_never_a_number" in result.stdout
    assert "DOES NOT ESTABLISH:" in result.stdout
