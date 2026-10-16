"""D4 — the indicator→dial mapping carrier, its refusals, and the ZERO rows it ships.

``PO-DECISIONS-0025`` r1/r2/r6. Every refusal here has **both arms** — the refusing one and
the **admitting** one — because *a carrier that refuses everything satisfies every invariant
vacuously*, which is the third-arm discipline increments 12 and 13 established.

*** **NO SOURCE AND NO INDICATOR IS REGISTERED BY ANYTHING IN THIS FILE.** *** Every fixture
identifier carries :data:`SYNTHETIC_ID_MARKER` — ``PLANT_SYNTH_`` — and
:func:`test_no_synthetic_identifier_can_appear_in_the_shipped_registry_data_file` asserts that
none of them reaches ``deploy/indicator-mapping.json``. ``CD-PL-F154`` is what a fixture
escaping onto a real branch costs, and a fixture id of ``CREDIT_HY_OAS`` or ``DRTSCILM``
would be exactly that defect wearing a plausible face.
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

import pytest

from crash_detector.dials.dialset import (
    DIAL_FIELDS,
    DIAL_IDS,
    EQUITY_DIAL_ID,
    MONETARY_DIAL_ID,
)
from crash_detector.engine.config import empty_config_snapshot
from crash_detector.publication.detail_level import (
    DETAIL_CALM,
    DETAIL_ELEVATED,
    DetailPolicy,
    detail_level_for,
)
from crash_detector.source_registry import (
    EMPTY_INDICATOR_MAPPING_REGISTRY,
    INDICATOR_MAPPING_PATH_ENV_VAR,
    POLARITY_NAMES,
    PROVISIONAL_TIER_NAMES,
    SYNTHETIC_ID_MARKER,
    WIRING_STATE_NAMES,
    DialBinding,
    DialBoundTwice,
    IndicatorMapping,
    IndicatorMappingRegistry,
    MappingProvenance,
    MappingRefused,
    PendingSourceMayNotRenderAsValue,
    PendingSourceMayNotRenderAsValue as _Pending,
    Polarity,
    ProvisionalTier,
    StalenessWindowTooWideForTheCeiling,
    WiringState,
    admit_staleness_window,
    indicator_mapping_path,
    load_indicator_mapping_registry,
)
from crash_detector.staleness import (
    STALENESS_WINDOW_CEILING_SECONDS,
    StalenessWindow,
    StalenessWindowOutOfRange,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SHIPPED = REPO_ROOT / "deploy" / "indicator-mapping.json"

#: SYNTHETIC. Unmistakable on sight, and asserted never to reach the shipped file.
SYNTH_A = f"{SYNTHETIC_ID_MARKER}A"
SYNTH_B = f"{SYNTHETIC_ID_MARKER}B"

WINDOW = 600.0


def _provenance(**overrides) -> MappingProvenance:
    fields = {
        "ruling_ref": "PLANT_SYNTH_RULING",
        "mapping_artefact": "PLANT_SYNTH_ARTEFACT",
        "mapping_version": "PLANT_SYNTH_V0",
        "stands_for": "a synthetic stand-in that names no real indicator",
    }
    fields.update(overrides)
    return MappingProvenance(**fields)


def _mapping(**overrides) -> IndicatorMapping:
    fields = {
        "source_id": SYNTH_A,
        "dial_bindings": (
            DialBinding(dial_id=EQUITY_DIAL_ID, polarity=Polarity.RISING_MEANS_MORE_RISK),
        ),
        "provisional_tier": ProvisionalTier.X2,
        "staleness_window": admit_staleness_window(WINDOW),
        "provenance": _provenance(),
        "wiring_state": WiringState.WIRED,
    }
    fields.update(overrides)
    return IndicatorMapping(**fields)


# ========================================================================================= #
# *** THE ADMITTING ARM, FIRST. A CARRIER THAT REFUSES EVERYTHING IS VACUOUSLY CORRECT. ***
# ========================================================================================= #

def test_a_fully_declared_mapping_IS_admitted():
    mapping = _mapping()
    assert mapping.source_id == SYNTH_A
    assert mapping.bound_dial_ids == (EQUITY_DIAL_ID,)
    assert mapping.provisional_tier is ProvisionalTier.X2
    assert mapping.wiring_state is WiringState.WIRED


def test_a_BOTH_indicator_is_TWO_bindings_with_TWO_polarities_and_is_admitted():
    """*** ``PO-DECISIONS-0025`` r7: TWO DIALS ARE NEVER BLENDED. ***

    This is the admitting arm of the whole no-blend shape: an indicator that genuinely moves
    both dials registers fine, and it registers as TWO bindings carrying TWO independent
    polarities — which may DIFFER, and here they do. Nothing reconciles them.
    """
    mapping = _mapping(
        dial_bindings=(
            DialBinding(dial_id=EQUITY_DIAL_ID, polarity=Polarity.RISING_MEANS_MORE_RISK),
            DialBinding(dial_id=MONETARY_DIAL_ID, polarity=Polarity.RISING_MEANS_LESS_RISK),
        )
    )
    assert sorted(mapping.bound_dial_ids) == sorted(DIAL_IDS)
    assert mapping.polarity_for(EQUITY_DIAL_ID) is Polarity.RISING_MEANS_MORE_RISK
    assert mapping.polarity_for(MONETARY_DIAL_ID) is Polarity.RISING_MEANS_LESS_RISK


def test_there_is_no_method_that_returns_one_answer_for_BOTH_dials():
    """``CD-AC-002`` is about the EXISTENCE of the function, not about the word 'blend'.

    ``polarity_for`` takes ONE dial. There is deliberately no ``polarities`` property and no
    ``combined_``/``overall_`` anything: a pair handed out for something else to reconcile is
    where a blend gets assembled.
    """
    import inspect

    signature = inspect.signature(IndicatorMapping.polarity_for)
    assert list(signature.parameters) == ["self", "dial_id"]

    forbidden = ("polarities", "combined", "overall", "blended", "total", "aggregate")
    for name in dir(IndicatorMapping):
        assert not any(word in name.lower() for word in forbidden), name
    for name in dir(IndicatorMappingRegistry):
        assert not any(word in name.lower() for word in forbidden), name


# ========================================================================================= #
# *** THE __class__ FORGERY, AGAINST EVERY ONE OF THE THREE NEW ENUMS ***
#
# source_registry.py:174-200 records why. An enum CPython refuses to SUBCLASS can still be
# WORN, and that exact forgery was LIVE AND ADMITTED at `ids_with` until increment 10.
# ========================================================================================= #

@pytest.mark.parametrize("enum_type", [Polarity, ProvisionalTier, WiringState])
def test_the_enum_cannot_be_SUBCLASSED_which_is_the_half_that_was_already_true(enum_type):
    # A CLASS STATEMENT, not `type("Evil", (enum_type,), {})`. MEASURED: the three-argument
    # form bypasses EnumMeta.__prepare__ and dies with an incidental
    # `AttributeError: 'dict' object has no attribute '_member_names'` — which would have
    # made this test pass for the WRONG REASON, proving that a malformed call fails rather
    # than that the enum is closed. The class statement is the route an attacker takes.
    namespace: dict = {"enum_type": enum_type}
    with pytest.raises(TypeError):
        exec("class Evil(enum_type):\n    pass\n", namespace)


@pytest.mark.parametrize("enum_type", [Polarity, ProvisionalTier, WiringState])
def test_but_it_CAN_be_WORN_and_isinstance_is_fooled_by_it(enum_type):
    """**THE ASYMMETRY, REPRODUCED RATHER THAN ASSERTED.** This test does not check the
    product; it checks that the ATTACK still works, so the refusals below are refusing
    something real. If CPython ever closed this, this test fails and the refusals become
    guards against an impossibility — which is worth knowing."""

    class Forged:
        @property
        def __class__(self):  # noqa: A003
            return enum_type

    forgery = Forged()
    assert isinstance(forgery, enum_type) is True      # isinstance CONSULTS __class__
    assert (type(forgery) is enum_type) is False       # exact type does NOT


def test_a_WORN_Polarity_is_REFUSED_at_the_binding_door():
    class Forged:
        @property
        def __class__(self):  # noqa: A003
            return Polarity

    with pytest.raises((MappingRefused, TypeError)) as refusal:
        DialBinding(dial_id=EQUITY_DIAL_ID, polarity=Forged())
    assert "polarity" in str(refusal.value).lower() or "Polarity" in str(refusal.value)


def test_a_WORN_ProvisionalTier_is_REFUSED():
    class Forged:
        @property
        def __class__(self):  # noqa: A003
            return ProvisionalTier

    with pytest.raises((MappingRefused, TypeError)):
        _mapping(provisional_tier=Forged())


def test_a_WORN_WiringState_is_REFUSED_and_that_is_the_false_green_door():
    """**THE MOST LOAD-BEARING OF THE THREE.** ``wiring_state`` is what
    :meth:`assert_may_render_as_value` consults, so an object WEARING ``WiringState.WIRED``
    would walk a PENDING feed straight past the false-green refusal."""

    class Forged:
        @property
        def __class__(self):  # noqa: A003
            return WiringState

    with pytest.raises((MappingRefused, TypeError)):
        _mapping(wiring_state=Forged())


# ========================================================================================= #
# THE REFUSALS, EACH WITH BOTH ARMS
# ========================================================================================= #

def test_a_binding_naming_a_token_that_means_BOTH_is_REFUSED():
    """There is no field for a second dial, so the only way to try is to smuggle a collapsed
    token into ``dial_id`` — and DIAL_IDS membership refuses it."""
    for collapsed in ("both", "BOTH", "equity+monetary", "all"):
        with pytest.raises(MappingRefused) as refusal:
            DialBinding(dial_id=collapsed, polarity=Polarity.RISING_MEANS_MORE_RISK)
        assert "ONE dial" in str(refusal.value) or "unknown dial_id" in str(refusal.value)


def test_the_ADMITTING_ARM_each_real_dial_id_binds():
    for dial_id in DIAL_IDS:
        binding = DialBinding(dial_id=dial_id, polarity=Polarity.RISING_MEANS_LESS_RISK)
        assert binding.dial_id == dial_id


def test_two_bindings_for_the_SAME_dial_are_REFUSED():
    """Two directions for one dial is the collapse reached from the inside."""
    with pytest.raises(DialBoundTwice) as refusal:
        _mapping(
            dial_bindings=(
                DialBinding(dial_id=EQUITY_DIAL_ID, polarity=Polarity.RISING_MEANS_MORE_RISK),
                DialBinding(dial_id=EQUITY_DIAL_ID, polarity=Polarity.RISING_MEANS_LESS_RISK),
            )
        )
    assert "twice" in str(refusal.value)


def test_binding_NO_dial_is_REFUSED():
    with pytest.raises(MappingRefused) as refusal:
        _mapping(dial_bindings=())
    assert "binds no dial" in str(refusal.value)


@pytest.mark.parametrize("no_polarity", [None, "", "RISING", 0])
def test_a_bound_dial_with_NO_polarity_is_REFUSED(no_polarity):
    with pytest.raises((MappingRefused, TypeError)):
        DialBinding(dial_id=EQUITY_DIAL_ID, polarity=no_polarity)


@pytest.mark.parametrize("bad", [0.0, -1.0, -600.0])
def test_a_staleness_window_that_is_zero_or_negative_is_REFUSED(bad):
    with pytest.raises(StalenessWindowOutOfRange):
        admit_staleness_window(bad)


def test_a_MISSING_staleness_window_is_REFUSED_and_there_is_no_global_default():
    """``PO-PRODUCT-0001`` R2: declared PER INDICATOR, never global. A row cannot omit it."""
    with pytest.raises((MappingRefused, TypeError)):
        IndicatorMapping(
            source_id=SYNTH_A,
            dial_bindings=(
                DialBinding(dial_id=EQUITY_DIAL_ID, polarity=Polarity.RISING_MEANS_MORE_RISK),
            ),
            provisional_tier=ProvisionalTier.X1,
            staleness_window=WINDOW,       # a bare number has not passed the door
            provenance=_provenance(),
            wiring_state=WiringState.WIRED,
        )


def test_the_ADMITTING_ARM_a_window_inside_the_ceiling_is_admitted():
    window = admit_staleness_window(600.0)
    assert type(window) is StalenessWindow
    assert window.seconds == 600.0


@pytest.mark.parametrize("bad", ["x3", 3, 3.0, None, "X3"])
def test_a_tier_outside_the_declared_three_is_REFUSED(bad):
    """A bare number is not a tier: it is a weight that skipped the backtest ruling 3
    requires. Note ``"x3"`` — the STRING — is refused too: it is the persisted discriminator,
    not the admitted member."""
    with pytest.raises((MappingRefused, TypeError)):
        _mapping(provisional_tier=bad)


def test_the_ADMITTING_ARM_each_of_the_three_declared_tiers_is_admitted():
    for tier in ProvisionalTier:
        assert _mapping(provisional_tier=tier).provisional_tier is tier
    assert sorted(PROVISIONAL_TIER_NAMES) == ["x1", "x2", "x3"]


def test_the_tier_type_carries_the_word_PROVISIONAL_and_cannot_be_multiplied():
    """*** RULING 3: 'No weight is trusted on assertion.' ***

    The NAME is the only part of a type that travels into every call site, and a member
    defines no arithmetic dunder — so a starting value cannot be laundered into an
    authoritative one by somebody multiplying by it before the backtest happens.
    """
    assert "PROVISIONAL" in ProvisionalTier.__name__.upper()
    with pytest.raises(TypeError):
        ProvisionalTier.X3 * 2.0
    with pytest.raises(TypeError):
        ProvisionalTier.X3 + ProvisionalTier.X2


@pytest.mark.parametrize(
    "field", ["ruling_ref", "mapping_artefact", "mapping_version", "stands_for"]
)
@pytest.mark.parametrize("empty", ["", "   ", None])
def test_provenance_that_is_absent_or_empty_is_REFUSED(field, empty):
    """*** An unexplained mapping cannot be admitted (PID doctrine §3.6, CD-D-005). ***
    Whitespace is not content, and every one of the four fields is load-bearing."""
    with pytest.raises((MappingRefused, TypeError)):
        _provenance(**{field: empty})


def test_the_ADMITTING_ARM_a_complete_provenance_is_admitted():
    provenance = _provenance()
    assert provenance.ruling_ref == "PLANT_SYNTH_RULING"
    assert provenance.stands_for.strip()


def test_a_mapping_with_NO_provenance_object_is_REFUSED():
    with pytest.raises((MappingRefused, TypeError)):
        _mapping(provenance={"ruling_ref": "x"})


# --- *** PENDING NEVER RENDERS AS A VALUE. RULING 4: 'never a false green'. *** ----------- #

def test_a_PENDING_row_asked_to_render_as_a_value_is_REFUSED():
    pending = _mapping(wiring_state=WiringState.PENDING)
    with pytest.raises(PendingSourceMayNotRenderAsValue) as refusal:
        pending.assert_may_render_as_value()
    assert "false green" in str(refusal.value)


def test_the_ADMITTING_ARM_a_WIRED_row_may_render():
    """**WITHOUT THIS ARM THE REFUSAL ABOVE IS VACUOUS** — a method that raised for every row
    would satisfy 'PENDING never renders' by making nothing render at all."""
    _mapping(wiring_state=WiringState.WIRED).assert_may_render_as_value()  # no raise


def test_a_PENDING_row_still_REGISTERS_because_PENDING_is_a_real_state():
    """``PO-DECISIONS-0025`` r4: SLOOS's NDFI leg is manual-quarterly and will be ``PENDING``
    FOR REAL. Refusing to register it would force the alternative the ruling forbids —
    leaving it out, so its absence is invisible instead of declared."""
    registry = IndicatorMappingRegistry(
        mappings=(_mapping(wiring_state=WiringState.PENDING),)
    )
    assert registry.pending_source_ids() == (SYNTH_A,)


# --- the registry ------------------------------------------------------------------------ #

def test_two_rows_for_one_indicator_are_REFUSED():
    with pytest.raises(MappingRefused) as refusal:
        IndicatorMappingRegistry(mappings=(_mapping(), _mapping()))
    assert "duplicate" in str(refusal.value)


def test_the_ADMITTING_ARM_two_DIFFERENT_indicators_register():
    registry = IndicatorMappingRegistry(
        mappings=(_mapping(), _mapping(source_id=SYNTH_B))
    )
    assert sorted(registry.source_ids) == sorted([SYNTH_A, SYNTH_B])


def test_asking_for_an_unmapped_indicator_REFUSES_rather_than_defaulting():
    with pytest.raises(MappingRefused):
        EMPTY_INDICATOR_MAPPING_REGISTRY.get(SYNTH_A)


def test_mappings_for_dial_takes_ONE_dial_and_refuses_anything_else():
    registry = IndicatorMappingRegistry(mappings=(_mapping(),))
    assert registry.mappings_for_dial(EQUITY_DIAL_ID)[0].source_id == SYNTH_A
    assert registry.mappings_for_dial(MONETARY_DIAL_ID) == ()
    with pytest.raises(MappingRefused):
        registry.mappings_for_dial("both")


# ========================================================================================= #
# *** THE STALENESS CEILING COLLISION. THIS IS THE FINDING, AS AN EXECUTABLE FACT. ***
# ========================================================================================= #

@pytest.mark.parametrize(
    "label,seconds",
    [("quarterly", 91 * 86400.0), ("monthly", 30 * 86400.0), ("daily", 86400.0),
     ("hourly", 3600.0), ("sixteen minutes", 960.0)],
)
def test_every_window_RULING_6_would_need_is_REFUSED_by_the_derived_ceiling(label, seconds):
    """*** ``PO-DECISIONS-0025`` RULING 6 REQUIRES A **WIDE** WINDOW FOR PRIVATE CREDIT
    STRESS, AND RULING 4 REGISTERS SLOOS's NDFI LEG AS MANUAL-**QUARTERLY**. NEITHER FITS. ***

    ``STALENESS_WINDOW_CEILING_SECONDS`` is 900.0 — fifteen minutes — DERIVED from ``PID.md``
    §5's ratified assurance latency budget with its clause cited. **NOTHING SLOWER THAN
    INTRADAY PASSES THIS DOOR**, so the carrier cannot today hold the rows 16B must write.

    **THIS TEST ASSERTS THE CURRENT STATE, NOT THAT THE STATE IS CORRECT.** The bound was NOT
    widened: it is derived from a ratified clause, and reversing a derivation to suit the data
    is the invention ``CD-RULE-003`` forbids. Raised to the Product Owner. When the collision
    is ruled on, this test fails and is the place the decision gets recorded.
    """
    assert seconds > STALENESS_WINDOW_CEILING_SECONDS
    with pytest.raises(StalenessWindowTooWideForTheCeiling) as refusal:
        admit_staleness_window(seconds)
    message = str(refusal.value)
    assert "KNOWN COLLISION" in message
    assert "not this code's to widen" in message


def test_the_collision_refusal_is_DISTINGUISHABLE_from_an_ordinary_bad_window():
    """A window that is too wide is a KNOWN COLLISION; a window that is zero is a mistake.
    They raise different types, so 16B can tell 'this needs a ruling' from 'this is a typo'.
    """
    assert issubclass(StalenessWindowTooWideForTheCeiling, MappingRefused)
    with pytest.raises(StalenessWindowTooWideForTheCeiling):
        admit_staleness_window(86400.0)
    with pytest.raises(StalenessWindowOutOfRange) as ordinary:
        admit_staleness_window(0.0)
    assert not isinstance(ordinary.value, StalenessWindowTooWideForTheCeiling)


# ========================================================================================= #
# *** THE SHIPPED DATA FILE: ZERO ROWS, AND NO FIXTURE MAY REACH IT ***
# ========================================================================================= #

def test_the_shipped_registry_data_file_contains_ZERO_indicators():
    """*** THE DELIVERABLE, NOT A GAP. *** The rows are ``Q30`` and they wait for the Product
    Authority. A placeholder would be inventing the meaning the ruling exists to supply."""
    document = json.loads(SHIPPED.read_text(encoding="utf-8"))
    assert document["indicators"] == []


def test_loading_the_shipped_file_yields_an_EMPTY_registry():
    registry = load_indicator_mapping_registry(SHIPPED)
    assert registry.is_empty
    assert registry.source_ids == ()
    assert registry.pending_source_ids() == ()


def test_no_synthetic_identifier_can_appear_in_the_shipped_registry_data_file():
    """*** ``CD-PL-F154`` IS WHAT A FIXTURE ESCAPING ONTO A REAL BRANCH COSTS. ***

    Every fixture in this project's mapping tests carries ``PLANT_SYNTH_``. If one is ever
    committed into the shipped data file, this fails. The marker is deliberately
    unmistakable so that the check is possible at all — a fixture id of ``CREDIT_HY_OAS``
    would be indistinguishable from a real row, which is the whole reason for the convention.
    """
    document = json.loads(SHIPPED.read_text(encoding="utf-8"))

    def _scan(node, pointer="") -> list:
        if isinstance(node, dict):
            return [h for k, v in node.items() for h in _scan(v, f"{pointer}/{k}")]
        if isinstance(node, list):
            return [h for i, v in enumerate(node) for h in _scan(v, f"{pointer}/{i}")]
        return [pointer] if isinstance(node, str) and SYNTHETIC_ID_MARKER in node else []

    # *** THE `$comment` HEADER IS EXCLUDED, AND THE EXCLUSION IS THE POINT RATHER THAN A
    # HOLE. *** That header DOCUMENTS the convention — it says in terms that no identifier
    # may carry the marker — so scanning it would make the file fail for explaining its own
    # rule. The first draft of this test did exactly that. What is scanned is every string
    # that could BE an identifier: the rows, and the artefact and version fields.
    subject = {k: v for k, v in document.items() if k != "$comment"}
    hits = _scan(subject)
    assert hits == [], (
        f"a synthetic test identifier reached {SHIPPED} at {hits}. That is a fixture on a "
        "real branch, which is CD-PL-F154."
    )
    # And the DATA is empty anyway, which is the stronger statement.
    assert document["indicators"] == []


def test_the_data_file_header_NAMES_what_is_owed_rather_than_being_silently_empty():
    """An empty file nobody explained is indistinguishable from one nobody finished."""
    text = SHIPPED.read_text(encoding="utf-8")
    for owed in ("Q30", "Q31", "indicator_dial_mapping:v1", "PLANT_SYNTH_"):
        assert owed in text, owed


def test_the_top_level_key_set_is_asserted_by_EQUALITY_so_a_global_default_cannot_hide(tmp_path):
    """An extra top-level key is a place to smuggle a GLOBAL staleness window or a default
    polarity past the per-indicator declaration ``PO-PRODUCT-0001`` R2 requires."""
    document = json.loads(SHIPPED.read_text(encoding="utf-8"))
    document["default_staleness_window_seconds"] = 900.0
    path = tmp_path / "smuggled.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(MappingRefused) as refusal:
        load_indicator_mapping_registry(path)
    assert "EQUALITY" in str(refusal.value)


def test_a_missing_data_file_REFUSES_rather_than_defaulting_to_empty(tmp_path):
    """**An empty registry that arrived by OMISSION is not evidence of anything.** The
    shipped emptiness is a decision; a missing file is an accident, and they must not look
    the same."""
    with pytest.raises(MappingRefused) as refusal:
        load_indicator_mapping_registry(tmp_path / "absent.json")
    assert "does not exist" in str(refusal.value)


def test_the_data_file_path_comes_from_the_environment(monkeypatch, tmp_path):
    """``PO-DECISIONS-0025`` r2: ALL config via env. No host path in the source."""
    assert indicator_mapping_path() == SHIPPED
    monkeypatch.setenv(INDICATOR_MAPPING_PATH_ENV_VAR, str(tmp_path / "elsewhere.json"))
    assert indicator_mapping_path() == tmp_path / "elsewhere.json"


def test_the_loader_makes_NO_judgement_of_its_own_a_bad_row_dies_in_the_constructor(tmp_path):
    """A loader with its own copy of the rules is a second place the rules live, and the two
    come apart in the direction nobody is testing. Here a row whose window is wider than the
    RELEVANCE ceiling (210 days — WO-1.3 derived it at 120, WO-1.19 raised it to 210 on
    2026-10-16 when the Owner ratified buffett_indicator's window on measured release lag)
    fails with the SAME refusal a hand-built RelevanceWindow gets; a quarterly row is still
    ADMITTED, and more comfortably than before (see the admitting arm below).

    The planted window must stay WIDER THAN THE CEILING to test anything at all, so it moved
    with the ceiling: 121 days was over the old 120 and is now well under 210, which would have
    turned this into a test that the loader refuses nothing. 211 days is one day past the
    current ceiling, the same hair's breadth 121 was past the old one."""
    path = tmp_path / "wide.json"
    path.write_text(json.dumps({
        "$comment": [], "mapping_artefact": "PLANT_SYNTH_ARTEFACT",
        "mapping_version": "PLANT_SYNTH_V0",
        "indicators": [{
            "source_id": SYNTH_A,
            "dial_bindings": [
                {"dial_id": EQUITY_DIAL_ID, "polarity": "RISING_MEANS_MORE_RISK"}
            ],
            "provisional_tier": "x3",
            "staleness_window_seconds": 211 * 86400.0,  # one day past the 210-day ceiling
            "provenance": {
                "ruling_ref": "PLANT_SYNTH_RULING",
                "mapping_artefact": "PLANT_SYNTH_ARTEFACT",
                "mapping_version": "PLANT_SYNTH_V0",
                "stands_for": "synthetic",
            },
            "wiring_state": "PENDING",
        }],
    }), encoding="utf-8")
    with pytest.raises(StalenessWindowOutOfRange):
        load_indicator_mapping_registry(path)


def test_the_ADMITTING_ARM_the_loader_DOES_admit_a_well_formed_synthetic_row(tmp_path):
    """*** WITHOUT THIS THE LOADER'S REFUSALS ARE ALL VACUOUS. *** A loader that refused
    every row would pass every test above by never admitting anything, and the shipped zero
    rows would hide it perfectly. This row is admitted — and it is SYNTHETIC, and it never
    touches the shipped file."""
    path = tmp_path / "ok.json"
    path.write_text(json.dumps({
        "$comment": [], "mapping_artefact": "PLANT_SYNTH_ARTEFACT",
        "mapping_version": "PLANT_SYNTH_V0",
        "indicators": [{
            "source_id": SYNTH_B,
            "dial_bindings": [
                {"dial_id": EQUITY_DIAL_ID, "polarity": "RISING_MEANS_MORE_RISK"},
                {"dial_id": MONETARY_DIAL_ID, "polarity": "RISING_MEANS_LESS_RISK"},
            ],
            "provisional_tier": "x1",
            "staleness_window_seconds": 600.0,
            "provenance": {
                "ruling_ref": "PLANT_SYNTH_RULING",
                "mapping_artefact": "PLANT_SYNTH_ARTEFACT",
                "mapping_version": "PLANT_SYNTH_V0",
                "stands_for": "a synthetic stand-in that names no real indicator",
            },
            "wiring_state": "WIRED",
        }],
    }), encoding="utf-8")
    registry = load_indicator_mapping_registry(path)
    assert registry.source_ids == (SYNTH_B,)
    row = registry.get(SYNTH_B)
    assert sorted(row.bound_dial_ids) == sorted(DIAL_IDS)
    assert row.polarity_for(MONETARY_DIAL_ID) is Polarity.RISING_MEANS_LESS_RISK
    row.assert_may_render_as_value()


# ========================================================================================= #
# *** D4.5 — THE CARRIER IS CALLED. NOT A WRITER WITH NO CALLER (CD-PL-F167/CD-PL-F170). ***
# ========================================================================================= #

def test_the_config_snapshot_CARRIES_the_mapping_registry():
    snapshot = empty_config_snapshot("cfg-16a", staleness_window_seconds=WINDOW)
    assert type(snapshot.indicator_mapping_registry) is IndicatorMappingRegistry
    assert snapshot.indicator_mapping_registry.is_empty


def test_the_mapping_registry_is_REQUIRED_on_the_snapshot_with_no_default():
    """A registry nobody chose is not evidence of anything — the same rule the source and
    model registries are held to, and for the same reason."""
    from crash_detector.engine.config import ConfigSnapshot, DialSpec
    from crash_detector.engine.model import EMPTY_MODEL_REGISTRY
    from crash_detector.source_registry import EMPTY_SOURCE_REGISTRY

    with pytest.raises(TypeError):
        ConfigSnapshot(  # type: ignore[call-arg]
            config_snapshot_id="cfg-no-mapping",
            dial_specs=tuple(
                DialSpec(
                    dial_id=dial_id,
                    required_input_ids=(),
                    contributing_input_ids=(),
                    model_ref=None,
                )
                for dial_id in DIAL_IDS
            ),
            staleness_window_seconds=WINDOW,
            source_registry=EMPTY_SOURCE_REGISTRY,
            model_registry=EMPTY_MODEL_REGISTRY,
        )


def test_a_mapped_indicator_that_is_NOT_a_registered_source_is_REFUSED_by_the_snapshot():
    """The mapping cannot bind a dial to an indicator the source registry has never heard
    of: the criticality contract — which decides whether an absence forces Unknown or
    Degraded — would never be consulted for it."""
    from crash_detector.engine.config import ConfigSnapshot, DialSpec
    from crash_detector.engine.model import EMPTY_MODEL_REGISTRY
    from crash_detector.source_registry import EMPTY_SOURCE_REGISTRY, SourceNotRegistered

    with pytest.raises(SourceNotRegistered):
        ConfigSnapshot(
            config_snapshot_id="cfg-unregistered",
            dial_specs=tuple(
                DialSpec(
                    dial_id=dial_id,
                    required_input_ids=(),
                    contributing_input_ids=(),
                    model_ref=None,
                )
                for dial_id in DIAL_IDS
            ),
            staleness_window_seconds=WINDOW,
            source_registry=EMPTY_SOURCE_REGISTRY,
            model_registry=EMPTY_MODEL_REGISTRY,
            indicator_mapping_registry=IndicatorMappingRegistry(mappings=(_mapping(),)),
        )


def test_END_TO_END_the_shipped_zero_row_mapping_leaves_every_dial_UNKNOWN_and_NEVER_CALM():
    """*** THE PROOF D4.5 ASKS FOR, END TO END, THROUGH THE PATH THAT ALREADY RUNS. ***

    Load the SHIPPED zero-row file → put it in the snapshot the engine evaluates → every dial
    reads ``UNKNOWN`` → ``detail_level`` renders ``policy.absent_data_level`` → **and that is
    never ``calm``**, because ``DetailPolicy`` refuses to be constructed if it were.

    ``PID`` §3.2 is constitutional: *"Missing data must never render as calm."* With zero
    registered sources this is not a corner case — **it is the only case**, and it is 100% of
    what a deployment would render today.
    """
    from crash_detector.dials.reading import Unknown
    from crash_detector.engine.evaluate import evaluate

    registry = load_indicator_mapping_registry(SHIPPED)
    assert registry.is_empty

    snapshot = empty_config_snapshot("cfg-16a-e2e", staleness_window_seconds=WINDOW)
    assert snapshot.indicator_mapping_registry.is_empty

    now = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    dials = evaluate([], snapshot, now)

    policy = DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=DETAIL_ELEVATED)
    # DIAL_FIELDS are the DialSet's attribute names ('equity', 'monetary'); DIAL_IDS are the
    # slot ids ('equity_crash', 'monetary_debasement'). Paired by position, which is how
    # dialset.py declares them, and asserted below rather than assumed.
    assert len(DIAL_FIELDS) == len(DIAL_IDS) == 2
    for field, dial_id in zip(DIAL_FIELDS, DIAL_IDS):
        reading = getattr(dials, field)
        assert type(reading) is Unknown, (dial_id, type(reading))
        level = detail_level_for(reading, dial_slot=dial_id, policy=policy)
        assert level == policy.absent_data_level
        assert level != DETAIL_CALM, (
            f"{dial_id} rendered as calm with no data. PID §3.2 is constitutional."
        )
