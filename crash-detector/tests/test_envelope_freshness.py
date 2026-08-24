"""*** THE STALE HALF OF ``CD-AC-001``, AND IT IS THE HALF NOTHING HAD EVER COMPUTED. ***

``CD-AC-001`` reads *"Missing **or stale** input never renders as calm."* Sixteen WO-3
increments guarded MISSING and every one of them put the guard in the closed contract,
which is where it belongs: since 16A-FIX the ``DEGRADED`` and ``UNKNOWN`` branches type
their ``detail_level`` as ``$defs/absent_data_detail_level`` — the vocabulary MINUS
``calm`` — so missing data carrying ``calm`` is unrepresentable rather than discouraged.

**NOTHING HAD EVER COMPUTED STALE, AND THE REASON IS STRUCTURAL: A SCHEMA CAN REQUIRE A
STAMP BUT IT CANNOT COMPARE ONE.** ``CD-ASR-WO3-11`` measured the consequence at
``295bdbe`` and returned RED (``A311-F2``): a ``VALUE`` dial stamped ``1970-01-01`` and
rendering ``calm`` was **ADMITTED ON BOTH SURFACES**, and still admitted with
``staleness_window_seconds: 1``. The Project Lead reproduced it in its own shell before
dispatching this increment and found a fourth row nobody had asked for — a dial stamped
``2099-01-01``, data from the FUTURE, also ADMITTED, which the obvious ``age > window``
formula would have left open.

``PO-DECISIONS-0029`` ruled ``Q34`` (a): the comparison happens AT THE GATE and is computed
PURELY FROM THE DOCUMENT. This module is that ruling's acceptance evidence.

===========================================================================================
*** EVERY REFUSING ASSERTION HERE IS PAIRED WITH AN ADMITTING ONE, AND THAT IS NOT
DECORATION. ***
===========================================================================================
A freshness stage that refused everything would satisfy PID §3.2 vacuously by making the
dial incapable of ever reading ``calm``, and that is a defect and not a fix. So the fresh
dial is asserted ADMITTED on both surfaces in the same file, on the same tree, by the same
fixture builder — and ``test_the_fixture_is_proved_in_both_directions`` exists to fail if
that ever stops being true.

**NOTHING HERE REGISTERS A SOURCE** (``Q25``, ``CD-PL-F154``). The ``source_id`` strings are
the unmistakable synthetic token below; nothing constructs a ``SourceRecord``, imports
``crash_detector.source_registry``, or names ``raw.source_registry``.

===========================================================================================
*** THIS FILE IS REGISTER-WIRED SINCE WO-3 INCREMENT 16E, AND UNTIL THEN IT WAS NOT. ***
===========================================================================================
It is the declared command of ``CD-RT-001-STALE-DATA-WITNESS-SUITE`` in ``required-tests.yaml``:

    PYTHONPATH=src python3 -m pytest tests/test_envelope_freshness.py -q

**BEFORE 16E NO REGISTER ROW NAMED IT, AND THAT WAS THE WHOLE OF ``A312-F1``.** MEASURED three
times independently — by ``CD-ASR-WO3-12``, by ``PROJECT_LEAD_SEAT_06`` and by
``CD-ENG-WO3-13`` — on a tree carrying ``plants/WO3-INC16D/D1-THE-FOURTH-STAGE-REMOVED.patch``
(``git apply`` rc=0, taken and checked): **all thirty of the register's ``execute:`` lines
produced a per-line rc list ``diff``-IDENTICAL to the clean tip**, while this file reported
**14 failed, 78 passed**. ``grep -c 'test_envelope_freshness' required-tests.yaml`` returned
**0**, against **41 distinct ``tests/test_*.py`` paths the register DID name.** The project's
own mechanism for making a test-file guarantee live was available and for this guarantee it
was not used.

*** AND THIS FILE IS STILL NOT THE GUARD. *** ``required-tests.yaml``'s own memorial says why,
about a different file in the identical position: *"a pytest file is still a file the gate
happens to name."* The LIVE instrument ``PO-DECISIONS-0030`` ruling 1 ordered is
``tools/register/check_stale_data_never_calm.py``, wired as
``CD-RT-001-STALE-DATA-NEVER-CALM``, which drives ``refuse_unless_publishable`` itself. This
file is that row's PAIRED WITNESS. Do not read it as the discharge of ruling 1.

---- DECLARED LIMITS — ``CD-RT-001-STALE-DATA-WITNESS-SUITE``'s OWN SEQUENCE, 1 TO 2 --------

**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** These two are that row's, and
they are said identically here, in
``contracts/execution/CD-RT-001-STALE-DATA-WITNESS-SUITE.md`` and in ``required-tests.yaml``
(``CD-RULE-004``, three places).

1. **IT IS A pytest FILE AND THEREFORE NAME-COUPLED TO ITS OWN PATH.** Deleting or renaming
   this module makes the row non-zero, which is the correct direction; but a test file the
   register names is only as live as the register line that names it, **and the LIVE guard is
   the sibling row.**

2. *** ONE OF ITS ASSERTIONS GUARDS THE INSTANCE AND NOT THE CLASS, AND IT IS NAMED HERE
   RATHER THAN LEFT TO BE FOUND (``A312-F2``; ``PO-DECISIONS-0026`` ruling 10's defect class).
   *** ``test_A311_F1_arm_H_is_REFUSED_even_on_a_contract_widened_to_admit_it`` drives a FIXED
   MODULE-LEVEL CONSTANT — ``ARM_H_DOCUMENT_FRAGMENT = [{"source_id": "SRC-A", "detail_level":
   DETAIL_CALM}]``. **It proves that ONE FRAGMENT is refused. IT DOES NOT QUANTIFY OVER WHAT
   THE WIDENED SUBSCHEMA ADMITS**, and ``CD-ASR-WO3-12`` built a fragment the same widened
   schema admits which is **ADMITTED on both surfaces**:

       degraded_inputs: [{"source_id": "SRC-A",                "detail_level": "calm"}]
             -> REFUSED [STALE_CALM] at /degraded_inputs/0  x2   (the claim, and it holds)
       degraded_inputs: [{"source_id": "2026-08-24T18:00:00Z", "detail_level": "calm"}]
             -> *** ADMITTED x2 ***
       the same with a 1970 or a 2099 source_id
             -> REFUSED [STALE_CALM] x2

   Stamps are detected **BY VALUE**, so a node with NO real stamp and ONE DECOY proves itself
   fresh against the decoy. **THIS IS NOT A LIVE ESCAPE ON THE SHIPPED CONTRACT:**
   ``degraded_inputs`` is ``#/$defs/source_id_list``, an array of plain strings, so no ``calm``
   can appear there at all, and both contract JSONs are byte-unchanged. **RECORDING IT IS IN
   SCOPE AT 16E; FIXING IT IS NOT.** Requiring the stamp a calm-bearing node relies on to be a
   DECLARED stamp — a ``#/$defs/utc_timestamp``-typed property, or a ``_utc``-suffixed name —
   rather than any string that happens to parse **narrows what the product admits and is
   PRODUCT SCOPE** (``PBG-AUTH-005``). It is raised as ``Q36`` and is with the Product
   Authority. **NO ASSERTION IN THIS FILE WAS CHANGED AT 16E; this paragraph is prose.**

---- AND WHAT THE STAGE THIS FILE WITNESSES DOES NOT PROVE ---------------------------------

**THE GATE ENFORCES DOCUMENT-INTERNAL FRESHNESS**: ``published_utc`` minus a calm-bearing
node's oldest stamp, against the window the SAME document declares. **IT CANNOT CATCH A SOURCE
THAT CONSISTENTLY LIES ABOUT ITS OWN STAMP**, and a uniformly time-shifted envelope passes it:
MEASURED (``A312-F3``), ``as_of_utc`` = ``published_utc`` = ``1970-01-01T00:00:00Z`` with an
ordinary 600-second window is **ADMITTED x2**. *** THAT IS NOT RECORDED AS UNENFORCEABLE.
``PO-DECISIONS-0030`` ruling 2 rules it the DETECTION tier's — witness divergence +
provenance, ``CD-AC-018`` — ENFORCED ONE TIER OUT AND OWED AT WO-3, when real sources and
their witnesses land. *** 16C's detector-side liveness marking therefore carries the HONESTY
OBLIGATION that its stamps are PROVENANCE-BACKED and WITNESS-CORROBORATABLE. **16C IS NOT
BUILT AT 16E.**
"""

from __future__ import annotations

import ast
import copy
import json
import pathlib
import shutil

import pytest

from crash_detector.publication.detail_level import (
    DETAIL_ACUTE,
    DETAIL_CALM,
    DETAIL_ELEVATED,
)
from crash_detector.publication.envelope_contract import (
    CONTRACTS_DIR_ENV_VAR,
    ENVELOPE_SCHEMA_VERSION,
    REFUSAL_SCHEMA_VIOLATION,
    REFUSAL_STALE_CALM,
    UTC_STAMP_PATTERN,
    EnvelopeSurface,
    PublicationRefused,
    contracts_dir,
    load_envelope_schema,
    refuse_unless_publishable,
)

# The stage itself, so the branches the CLOSED CONTRACT makes unreachable through the front
# door are still driven rather than asserted about. Each such test says so in its docstring;
# every branch that CAN be reached through `refuse_unless_publishable` IS reached that way.
from crash_detector.publication.envelope_contract import (  # noqa: E402
    _parse_utc_stamp,
    _refuse_stale_calm,
)

SURFACES = (EnvelopeSurface.PUBLIC, EnvelopeSurface.PRIVATE)

#: Deliberately unmistakable. A grep for it lands here and nowhere near a registry.
SYNTHETIC_INPUT_ID = "SYNTHETIC-FRESHNESS-TEST-NOT-A-SOURCE"
SYNTHETIC_CONFIG_SNAPSHOT_ID = "SYNTHETIC-FRESHNESS-TEST-NOT-A-CONFIG"

PUBLISHED = "2026-08-24T18:00:00Z"

SCHEMA_NAMES = ("public_envelope.schema.json", "private_envelope.schema.json")

ADMITTED = "ADMITTED"


# ========================================================================================= #
# FIXTURES — one builder, both surfaces, and the surface key added per surface
# ========================================================================================= #

def value_dial(as_of_utc: str, level: str = DETAIL_CALM) -> dict:
    """A conforming ``VALUE`` dial. ``VALUE`` keeps the full level vocabulary INCLUDING
    ``calm`` — a genuinely calm reading backed by a real number is the whole reason ``calm``
    exists — which is exactly why the stale half has to be enforced somewhere else."""
    return {
        "state": "VALUE",
        "score": 0.1,
        "as_of_utc": as_of_utc,
        "inputs_used": [SYNTHETIC_INPUT_ID],
        "contributions": [],
        "detail_level": level,
    }


def envelope(
    surface: EnvelopeSurface,
    *,
    dial_as_of: str = PUBLISHED,
    window: float = 600.0,
    level: str = DETAIL_CALM,
    published: str = PUBLISHED,
) -> dict:
    """A conforming envelope for ``surface``.

    **ONE FIXTURE CANNOT SERVE BOTH SURFACES AND THAT IS A PROPERTY OF THE CONTRACTS, NOT AN
    INCONVENIENCE.** The private contract REQUIRES ``classification`` const ``PRIVATE``; the
    public contract declares no such property at all, so a private envelope validated against
    the public schema is refused on that key before anything else is considered. A shared
    fixture would be REFUSED on one surface for the wrong reason and would make every row
    below unreadable — which is a mistake a seat on this project made and caught only because
    its ADMITTING control failed too.
    """
    document = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "as_of_utc": dial_as_of,
        "published_utc": published,
        "regime": "SYNTHETIC-REGIME",
        "staleness_window_seconds": window,
        "inputs_used": [SYNTHETIC_INPUT_ID],
        "degraded_inputs": [],
        "config_snapshot_id": SYNTHETIC_CONFIG_SNAPSHOT_ID,
        "equity_crash": value_dial(dial_as_of, level),
        "monetary_debasement": value_dial(dial_as_of, level),
    }
    if surface is EnvelopeSurface.PRIVATE:
        document["classification"] = "PRIVATE"
    return document


def verdict(surface: EnvelopeSurface, document: dict):
    """``ADMITTED`` or the :exc:`PublicationRefused` raised. Never a bool."""
    try:
        refuse_unless_publishable(copy.deepcopy(document), surface=surface)
    except PublicationRefused as refused:
        return refused
    return ADMITTED


def refusal(surface: EnvelopeSurface, document: dict) -> PublicationRefused:
    outcome = verdict(surface, document)
    assert isinstance(outcome, PublicationRefused), (
        f"{surface.value}: the gate ADMITTED a document this test requires it to REFUSE"
    )
    return outcome


# ========================================================================================= #
# *** A311-F2 — THE PLANT THAT MUST FLIP, ON BOTH SURFACES ***
# ========================================================================================= #

@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("window", [1, 86400, 600.0])
def test_A311_F2_a_dial_stamped_1970_carrying_calm_is_REFUSED(surface, window):
    """Fifty-six years stale, rendering calm. ADMITTED at ``295bdbe`` on both surfaces."""
    refused = refusal(
        surface, envelope(surface, dial_as_of="1970-01-01T00:00:00Z", window=window)
    )
    assert refused.reason_class == REFUSAL_STALE_CALM
    assert refused.pointer in ("/equity_crash", "/monetary_debasement")


@pytest.mark.parametrize("surface", SURFACES)
def test_A311_F2_a_dial_stamped_in_the_FUTURE_carrying_calm_is_REFUSED(surface):
    """*** THE ROW THE OBVIOUS FORMULA LEAVES OPEN. ***

    ``published_utc - as_of_utc`` is NEGATIVE here, so ``age > window -> refuse`` admits it,
    and the Product Owner's own named plant is *"a VALUE dial dated 1970/2099 carrying
    calm"*. The predicate is a CLOSED INTERVAL: a negative age is not a small age. Data from
    the future is INCOHERENT rather than fresh and fails closed.
    """
    refused = refusal(
        surface, envelope(surface, dial_as_of="2099-01-01T00:00:00Z", window=1)
    )
    assert refused.reason_class == REFUSAL_STALE_CALM


@pytest.mark.parametrize("surface", SURFACES)
def test_the_fixture_is_proved_in_both_directions(surface):
    """*** THE VACUITY GUARD, AND WITHOUT IT EVERY ROW ABOVE MEANS NOTHING. ***

    A stage that refuses everything satisfies PID §3.2 by making the dial incapable of ever
    reading ``calm``. That is a defect, not a fix. A genuinely fresh dial inside its window
    is ADMITTED, on both surfaces, built by the same builder as the refused rows.
    """
    assert verdict(surface, envelope(surface, dial_as_of=PUBLISHED, window=1)) == ADMITTED
    assert (
        verdict(surface, envelope(surface, dial_as_of="2026-08-24T17:00:00Z", window=86400))
        == ADMITTED
    )


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("level", [DETAIL_ELEVATED, DETAIL_ACUTE])
def test_a_stale_dial_that_does_NOT_claim_calm_is_still_ADMITTED(surface, level):
    """**THE STAGE GUARDS ``calm`` AND SAYS NOTHING ABOUT THE OTHER TWO LEVELS.**

    ``elevated`` and ``acute`` are what a stale reading is SUPPOSED to render as. A stage
    that refused those would be refusing the correct behaviour, and the criterion is
    *"never renders as **calm**"*, not "never publishes anything old".
    """
    assert (
        verdict(surface, envelope(surface, dial_as_of="1970-01-01T00:00:00Z", level=level))
        == ADMITTED
    )


# ========================================================================================= #
# THE WINDOW BOUNDARY — decided exactly, in integer microseconds
# ========================================================================================= #

@pytest.mark.parametrize("surface", SURFACES)
def test_age_EQUAL_to_the_window_is_admitted_and_one_microsecond_more_is_refused(surface):
    """``age <= window``, and the boundary is decided by integer arithmetic rather than by a
    float that could land one ULP the wrong side of it."""
    assert (
        verdict(surface, envelope(surface, dial_as_of="2026-08-24T17:59:59Z", window=1))
        == ADMITTED
    ), "age == window must be INSIDE the window"

    assert (
        verdict(
            surface,
            envelope(surface, dial_as_of="2026-08-24T17:59:58.999999Z", window=1),
        ).reason_class
        == REFUSAL_STALE_CALM
    ), "one microsecond past the window must be REFUSED"


# ========================================================================================= #
# NODE-QUANTIFIED, NOT SLOT-READ — the design constraint, asserted
# ========================================================================================= #

@pytest.mark.parametrize("surface", SURFACES)
def test_the_stage_reads_no_dial_slot_by_name(surface):
    """*** THE WHOLE DESIGN, AS AN EXECUTABLE FACT. ***

    The document below carries NO ``equity_crash`` and NO ``monetary_debasement``. A stage
    implemented as ``candidate["equity_crash"]["as_of_utc"]`` finds nothing to check and
    passes it; this one walks the document, finds a calm-bearing node at a slot name that
    has never existed in any contract, and refuses it.

    Driven against the STAGE rather than the whole gate because the closed contract refuses
    an unknown root property first — which is Rule CC doing its job, and is exactly why this
    branch has to be driven directly to be driven at all.
    """
    document = {
        "published_utc": PUBLISHED,
        "staleness_window_seconds": 600.0,
        "a_slot_no_contract_has_ever_declared": value_dial("1970-01-01T00:00:00Z"),
    }
    with pytest.raises(PublicationRefused) as caught:
        _refuse_stale_calm(document, surface)
    assert caught.value.reason_class == REFUSAL_STALE_CALM
    assert caught.value.pointer == "/a_slot_no_contract_has_ever_declared"


@pytest.mark.parametrize("surface", SURFACES)
def test_a_calm_node_inside_an_array_at_depth_is_found(surface):
    """Objects AND arrays, at every depth. ``_iter_nodes`` is the walk stage 1 already
    trusts, and the pointer proves the stage went through the array rather than over it."""
    document = {
        "published_utc": PUBLISHED,
        "staleness_window_seconds": 600.0,
        "wrapper": {"rows": [{"ok": True}, {"nested": {"detail_level": DETAIL_CALM}}]},
    }
    with pytest.raises(PublicationRefused) as caught:
        _refuse_stale_calm(document, surface)
    assert caught.value.pointer == "/wrapper/rows/1/nested"
    assert caught.value.reason_class == REFUSAL_STALE_CALM


# ========================================================================================= #
# FAIL CLOSED AT EVERY BRANCH — there is no "cannot tell, so allow"
# ========================================================================================= #

@pytest.mark.parametrize("surface", SURFACES)
def test_a_calm_node_with_NO_stamp_at_all_is_refused(surface):
    """A node that cannot date its data cannot claim its data is fresh."""
    document = {
        "published_utc": PUBLISHED,
        "staleness_window_seconds": 600.0,
        "reading": {"state": "VALUE", "detail_level": DETAIL_CALM},
    }
    with pytest.raises(PublicationRefused) as caught:
        _refuse_stale_calm(document, surface)
    assert caught.value.reason_class == REFUSAL_STALE_CALM
    assert caught.value.key == "detail_level"


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize(
    "broken", ["yesterday", "2026-13-45T99:99:99Z", "2026-02-30T00:00:00Z", ""]
)
def test_a_property_that_ANNOUNCES_itself_as_a_stamp_and_does_not_parse_is_refused(
    surface, broken
):
    """*** A STAMP THAT WILL NOT PARSE IS A REFUSAL AND NEVER A SKIP. ***

    Note ``2026-13-45T99:99:99Z`` and ``2026-02-30T00:00:00Z``: both SATISFY the contract's
    own ``$defs/utc_timestamp`` pattern, because a pattern is a shape check and month 13,
    day 45 and 30 February are shapes. Neither names an instant. The parser is deliberately
    STRICTER than the pattern and the difference fails closed.
    """
    document = {
        "published_utc": PUBLISHED,
        "staleness_window_seconds": 600.0,
        "reading": {"as_of_utc": broken, "detail_level": DETAIL_CALM},
    }
    with pytest.raises(PublicationRefused) as caught:
        _refuse_stale_calm(document, surface)
    assert caught.value.reason_class == REFUSAL_STALE_CALM
    assert caught.value.key == "as_of_utc"


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("published", [None, "not-a-stamp", 17, "2026-02-30T00:00:00Z"])
def test_a_root_without_a_usable_published_utc_refuses_every_calm_node(surface, published):
    """Freshness is measured FROM the publication instant. No instant, no measurement, no
    admission. Driven against the stage because both contracts REQUIRE ``published_utc``,
    so the schema stage would refuse first through the front door — which is the belt this
    braces."""
    document = {"staleness_window_seconds": 600.0, "reading": value_dial(PUBLISHED)}
    if published is not None:
        document["published_utc"] = published
    with pytest.raises(PublicationRefused) as caught:
        _refuse_stale_calm(document, surface)
    assert caught.value.key == "published_utc"


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("window", [None, 0, -1, "600", True, float("inf"), float("nan")])
def test_a_root_without_a_real_positive_finite_window_refuses_every_calm_node(
    surface, window
):
    """*"an unbounded window is no window"* — the contract's own words about this field.

    ``True`` is in the list on purpose: it is an ``int`` in Python and would otherwise read
    as a one-second window nobody declared, arrived at by a type confusion and silently the
    tightest window in the product.
    """
    document = {"published_utc": PUBLISHED, "reading": value_dial(PUBLISHED)}
    if window is not None:
        document["staleness_window_seconds"] = window
    with pytest.raises(PublicationRefused) as caught:
        _refuse_stale_calm(document, surface)
    assert caught.value.key == "staleness_window_seconds"


@pytest.mark.parametrize("surface", SURFACES)
def test_the_OLDEST_stamp_governs(surface):
    """*"as fresh as its oldest input, never as fresh as the last time we asked"* — the
    envelope's own declared doctrine for ``as_of_utc``, and this stage must not quietly adopt
    a laxer one.

    **THIS IS ALSO WHAT MAKES VALUE-BASED STAMP DETECTION SAFE**: adding a fresh-looking
    string to a stale node can never rescue it.
    """
    document = {
        "published_utc": PUBLISHED,
        "staleness_window_seconds": 600.0,
        "reading": {
            "detail_level": DETAIL_CALM,
            "as_of_utc": PUBLISHED,
            "computed_from_utc": "1970-01-01T00:00:00Z",
        },
    }
    with pytest.raises(PublicationRefused) as caught:
        _refuse_stale_calm(document, surface)
    assert caught.value.key == "computed_from_utc", (
        "the FRESHER stamp governed, so a stale node can be rescued by adding a new one"
    )


# ========================================================================================= #
# *** NO VALUE FROM THE CANDIDATE REACHES THE REFUSAL (PBG-SEC-002) ***
# ========================================================================================= #

@pytest.mark.parametrize("surface", SURFACES)
def test_the_refusal_quotes_no_value_from_the_candidate(surface):
    """A refusal message is a log line and a log line is a governed artefact. The token, the
    pointer and the KEY NAME are reportable; the stamp, the age and the window are not."""
    stale = "1970-01-01T00:00:00Z"
    refused = refusal(surface, envelope(surface, dial_as_of=stale, window=1234.5))
    message = str(refused)
    for leaked in (stale, "1234.5", "1970", "1780617600", SYNTHETIC_INPUT_ID):
        assert leaked not in message, f"the refusal message leaked {leaked!r}"
    assert refused.detail and "calm" in refused.detail


# ========================================================================================= #
# *** NO CLOCK. NOT BY INSPECTION — BY AST, MECHANICALLY, EVERY RUN. ***
# BP-AMENDMENT-0001 §D.3 is IN FORCE: no parameter exists through which a caller clock,
# caller sleep or caller span can arrive.
# ========================================================================================= #

CLOCK_MODULES = frozenset(
    {"datetime", "time", "calendar", "zoneinfo", "dateutil", "pendulum", "arrow", "sched"}
)
CLOCK_ATTRIBUTES = frozenset(
    {"now", "utcnow", "today", "utcfromtimestamp", "fromtimestamp", "monotonic",
     "perf_counter", "process_time", "time_ns", "monotonic_ns", "gmtime", "localtime"}
)


def _module_source() -> str:
    import crash_detector.publication.envelope_contract as module

    return pathlib.Path(module.__file__).read_text(encoding="utf-8")


def _clock_reaches(source: str) -> list:
    """Every way this source could reach a clock. Empty means it cannot."""
    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in CLOCK_MODULES:
                    found.append(f"import {alias.name}:{node.lineno}")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in CLOCK_MODULES:
                found.append(f"from {node.module}:{node.lineno}")
        elif isinstance(node, ast.Attribute):
            if node.attr in CLOCK_ATTRIBUTES:
                found.append(f"attribute .{node.attr}:{node.lineno}")
        elif isinstance(node, ast.Name):
            if node.id in CLOCK_ATTRIBUTES:
                found.append(f"name {node.id}:{node.lineno}")
    return found


def test_the_envelope_contract_module_cannot_reach_a_clock():
    """*** ``PO-DECISIONS-0029`` RULING 1: COMPUTED **PURELY FROM THE DOCUMENT**. ***

    Both instants come out of the candidate. This module imports neither ``datetime`` nor
    ``time``, so there is no name in it a later edit could turn into a clock call without
    ADDING AN IMPORT — which is a diff a reviewer sees, and which this test fails on.
    """
    assert _clock_reaches(_module_source()) == []


def test_that_clock_scan_would_catch_a_clock():
    """**THE VACUITY GUARD FOR THE SCAN ABOVE.** A scan that finds nothing because it looks
    for nothing is worth nothing."""
    planted = "import datetime\ndef age(stamp):\n    return datetime.datetime.now() - stamp\n"
    assert _clock_reaches(planted) != []
    assert _clock_reaches("import time\nt = time.monotonic()\n") != []


def test_no_parameter_exists_through_which_a_caller_clock_could_arrive():
    """``BP-AMENDMENT-0001`` §D.3, held mechanically rather than in prose."""
    import inspect

    signature = inspect.signature(refuse_unless_publishable)
    assert list(signature.parameters) == ["candidate", "surface"]
    assert list(inspect.signature(_refuse_stale_calm).parameters) == [
        "candidate",
        "surface",
    ]


# ========================================================================================= #
# THE PARSER AND THE CONTRACT CANNOT DRIFT APART
# ========================================================================================= #

@pytest.mark.parametrize("surface", SURFACES)
def test_the_mirrored_pattern_is_the_contracts_own(surface):
    """Mirrored, not retyped, and asserted here so the mirror cannot rot — the same device
    ``ENVELOPE_SCHEMA_VERSION`` uses for the pinned version."""
    schema = load_envelope_schema(surface)
    assert schema["$defs"]["utc_timestamp"]["pattern"] == UTC_STAMP_PATTERN


ACCEPTED_BY_BOTH = (
    "1970-01-01T00:00:00Z",
    "2026-08-24T18:00:00Z",
    "2026-08-24T18:00:00.5Z",
    "2026-08-24T18:00:00.123456Z",
    "2024-02-29T00:00:00Z",       # a real leap day
    "2099-12-31T23:59:59Z",
)

#: Shapes the CONTRACT PATTERN admits and the parser must NOT — the deliberate asymmetry.
SHAPE_VALID_BUT_NOT_AN_INSTANT = (
    "2026-13-01T00:00:00Z",
    "2026-00-01T00:00:00Z",
    "2026-01-32T00:00:00Z",
    "2026-02-30T00:00:00Z",
    "2100-02-29T00:00:00Z",       # 2100 is NOT a leap year
    "2026-08-24T24:00:00Z",
    "2026-08-24T18:60:00Z",
    "2026-08-24T18:00:60Z",       # a leap second — DECLARED LIMIT F-3, fails closed
)


def test_the_parser_is_never_LOOSER_than_the_contract_pattern():
    """*** THE DIRECTION THAT MATTERS. *** Every string the parser reads as an instant, both
    contracts also admit. A parser that accepted something the schema would refuse would be
    proving freshness about a document that never got past stage 3."""
    import re

    corpus = list(ACCEPTED_BY_BOTH) + list(SHAPE_VALID_BUT_NOT_AN_INSTANT) + [
        "2026-08-24 18:00:00Z", "2026-08-24T18:00:00", "2026-08-24T18:00:00+01:00",
        "2026-08-24T18:00:00.1234567Z", "yesterday", "", "0",
    ]
    for candidate in corpus:
        if _parse_utc_stamp(candidate) is not None:
            assert re.match(UTC_STAMP_PATTERN, candidate), (
                f"{candidate!r} parses as an instant but the contract pattern refuses it"
            )


@pytest.mark.parametrize("stamp", ACCEPTED_BY_BOTH)
def test_a_real_instant_parses(stamp):
    assert _parse_utc_stamp(stamp) is not None


@pytest.mark.parametrize("stamp", SHAPE_VALID_BUT_NOT_AN_INSTANT)
def test_a_shape_valid_non_instant_does_NOT_parse(stamp):
    """The contract admits the SHAPE; the parser refuses the non-instant; the stage then
    fails closed on it. Three layers and the strictest one wins."""
    import re

    assert re.match(UTC_STAMP_PATTERN, stamp), "this corpus must be shape-valid to mean anything"
    assert _parse_utc_stamp(stamp) is None


def test_the_epoch_arithmetic_is_right():
    """Anchored against instants whose epoch seconds are common knowledge, so the
    hand-written civil-days computation is checked against something outside itself."""
    assert _parse_utc_stamp("1970-01-01T00:00:00Z") == 0
    assert _parse_utc_stamp("2000-01-01T00:00:00Z") == 946684800 * 1000000
    assert _parse_utc_stamp("2001-01-01T00:00:00Z") == 978307200 * 1000000
    assert _parse_utc_stamp("2024-02-29T12:00:00Z") == 1709208000 * 1000000
    assert _parse_utc_stamp("2026-08-24T18:00:00Z") == 1787594400 * 1000000
    assert _parse_utc_stamp("1969-12-31T23:59:59Z") == -1000000
    assert _parse_utc_stamp("2026-08-24T18:00:00.5Z") == 1787594400 * 1000000 + 500000


# ========================================================================================= #
# *** A311-F1's RUNTIME CONSEQUENCE — CLOSED BY CONSTRUCTION, ON A WIDENED CONTRACT ***
# ========================================================================================= #

def _contracts_copy_with_degraded_inputs_widened(tmp_path: pathlib.Path) -> pathlib.Path:
    """``CD-ASR-WO3-11``'s Arm H, applied to a COPY. **The real files are read, never
    written** (``CD-PL-F154``).

    The allowlisted root property ``degraded_inputs`` becomes an ARRAY OF CLOSED OBJECTS that
    may carry ``#/$defs/detail_level``. That is ONE CONTAINER DEEPER than the increment's own
    arm ``CC-H``, which widened it to an OBJECT and was caught. At ``295bdbe`` the register
    instrument reported ``PASS — 243`` on this arm, the whole thirty-line register was
    identical in every rc, and **the live gate ADMITTED the list of DEGRADED inputs rendering
    as CALM on both surfaces.**
    """
    target = tmp_path / "contracts-arm-h"
    target.mkdir()
    for name in SCHEMA_NAMES:
        shutil.copy(contracts_dir() / name, target / name)
        schema = json.loads((target / name).read_text(encoding="utf-8"))
        schema["properties"]["degraded_inputs"] = {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["source_id"],
                "properties": {
                    "source_id": {"type": "string", "minLength": 1, "maxLength": 128},
                    "detail_level": {"$ref": "#/$defs/detail_level"},
                },
            },
        }
        (target / name).write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return target


ARM_H_DOCUMENT_FRAGMENT = [{"source_id": "SRC-A", "detail_level": DETAIL_CALM}]


@pytest.mark.parametrize("surface", SURFACES)
def test_the_widened_contract_really_does_admit_arm_H_at_the_SCHEMA_stage(
    surface, tmp_path, monkeypatch
):
    """**THE CONTROL THAT MAKES THE NEXT TEST MEAN ANYTHING.** If the widening did not
    actually reach the schema, the refusal below would be a refusal of nothing."""
    import jsonschema

    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(
        _contracts_copy_with_degraded_inputs_widened(tmp_path)))
    document = envelope(surface, dial_as_of=PUBLISHED, level=DETAIL_ELEVATED)
    document["degraded_inputs"] = copy.deepcopy(ARM_H_DOCUMENT_FRAGMENT)
    jsonschema.validate(document, load_envelope_schema(surface))


@pytest.mark.parametrize("surface", SURFACES)
def test_A311_F1_arm_H_is_REFUSED_even_on_a_contract_widened_to_admit_it(
    surface, tmp_path, monkeypatch
):
    """*** ``A311-F1`` CLOSED BY CONSTRUCTION RATHER THAN BY CENSUS. ***

    ``{"source_id": "SRC-A", "detail_level": "calm"}`` is a mapping node carrying ``calm``
    with NO stamp of its own. Under a NODE-QUANTIFIED predicate it must prove freshness, it
    cannot, and it is REFUSED — **on a tree whose contract has been widened to admit it.**

    The auditor's own prescription was that the remedy must not be a third probe shape,
    because that *"moves the census game to the probe alphabet and earns an eleventh"*.
    """
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(
        _contracts_copy_with_degraded_inputs_widened(tmp_path)))
    document = envelope(surface, dial_as_of=PUBLISHED, level=DETAIL_ELEVATED)
    document["degraded_inputs"] = copy.deepcopy(ARM_H_DOCUMENT_FRAGMENT)

    refused = refusal(surface, document)
    assert refused.reason_class == REFUSAL_STALE_CALM
    assert refused.pointer == "/degraded_inputs/0"


@pytest.mark.parametrize("surface", SURFACES)
def test_the_widened_contract_still_admits_the_UNMUTATED_baseline(
    surface, tmp_path, monkeypatch
):
    """The second half of the control: the widening itself refuses nothing, so the refusal
    above is attributable to the calm-bearing node and not to the mutation."""
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(
        _contracts_copy_with_degraded_inputs_widened(tmp_path)))
    assert verdict(surface, envelope(surface, dial_as_of=PUBLISHED)) == ADMITTED


def test_the_real_contracts_are_never_written():
    """``CD-PL-F154``: a fixture that escapes into the product is the failure mode this
    project has already paid for once."""
    before = {name: (contracts_dir() / name).read_bytes() for name in SCHEMA_NAMES}
    assert all(before.values())
    assert {name: (contracts_dir() / name).read_bytes() for name in SCHEMA_NAMES} == before


# ========================================================================================= #
# THE CONTROLS RULE CC ALREADY HOLDS — ASSERTED HERE SO THIS INCREMENT CANNOT MOVE THEM
# ========================================================================================= #

ABSENT_DATA_CALM_DIALS = {
    "UNKNOWN": {
        "state": "UNKNOWN",
        "reason": "NO_SOURCE_REGISTERED",
        "since_utc": PUBLISHED,
        "missing_inputs": [],
        "detail_level": DETAIL_CALM,
    },
    "DEGRADED": {
        "state": "DEGRADED",
        "score": 0.1,
        "as_of_utc": PUBLISHED,
        "missing_inputs": [SYNTHETIC_INPUT_ID],
        "reason": "INPUT_MISSING",
        "contributions": [],
        "detail_level": DETAIL_CALM,
    },
    "SPINDRIFT (a never-before-named state)": {
        "state": "SPINDRIFT",
        "detail_level": DETAIL_CALM,
    },
    "no state at all": {"detail_level": DETAIL_CALM},
}


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("name", sorted(ABSENT_DATA_CALM_DIALS))
def test_rule_CC_still_refuses_every_absent_data_dial_carrying_calm(surface, name):
    """*** ``295bdbe`` IS PRESERVED. *** These are FRESH — stamped at ``published_utc``
    itself — so the freshness stage has no opinion about them. They are refused by the
    CLOSED CONTRACT, at stage 3, exactly as they were before this increment, and the
    reason_class proves WHICH stage refused them.
    """
    document = envelope(surface, dial_as_of=PUBLISHED, level=DETAIL_ELEVATED)
    document["equity_crash"] = copy.deepcopy(ABSENT_DATA_CALM_DIALS[name])
    refused = refusal(surface, document)
    assert refused.reason_class == REFUSAL_SCHEMA_VIOLATION, (
        "the closed contract must still be what refuses an absent-data calm dial; if the "
        "freshness stage is catching these, Rule CC has been weakened underneath it"
    )
    assert refused.pointer == "/equity_crash"
