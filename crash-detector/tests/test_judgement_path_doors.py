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
