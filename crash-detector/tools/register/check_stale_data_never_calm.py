#!/usr/bin/env python3
"""CD-RT-001-STALE-DATA-NEVER-CALM — the LIVE GATE refuses a STALE calm dial.

    python3 tools/register/check_stale_data_never_calm.py --root <subject tree>

CRITERION: `CD-AC-001` — *"Missing **or stale** input never renders as calm."* — and `PID §3.2`,
which is CONSTITUTIONAL in the same words. Authority: `PO-DECISIONS-0030` **ruling 1**:

    "Q35(a) — YES, the fourth refusal stage gets its OWN Required Test Register row, and it
     lands BEFORE 16C. This is ruling 9's principle (a constitutional guarantee is carried by a
     REGISTER-WIRED instrument, never test-only) applied to the freshness stage: the guarantee
     is proven today, but proven in tests is not proven in the register. Register-wire it — its
     own row, a negative control the gate reads, failing if stale-carrying-calm is ever
     admitted."

===========================================================================================
**WHY THIS INSTRUMENT EXISTS, IN ONE PARAGRAPH.** WO-3 increment `16D-GATE-FRESHNESS` added a
FOURTH REFUSAL STAGE to `refuse_unless_publishable` (`REFUSAL_STALE_CALM`), which compares the
root's `published_utc` against each calm-bearing node's own OLDEST stamp against the root's
declared `staleness_window_seconds`, computed purely from the document. An independent auditor
set out to break it and could not. **But nothing the register read would have noticed if it
were deleted.** MEASURED by `CD-ASR-WO3-12` (`A312-F1`), reproduced independently by
`PROJECT_LEAD_SEAT_06`, and reproduced a THIRD time by this seat before a line of this file was
written: on a tree with the entire fourth stage removed (`plants/WO3-INC16D/
D1-THE-FOURTH-STAGE-REMOVED.patch`, `git apply` rc=0 TAKEN AND CHECKED), **all thirty of the
register's `execute:` lines exit with a per-line rc list that is `diff`-IDENTICAL to the clean
tip — `TOTAL lines=30 rc0=19 nonzero=11` on both** — while the live gate ADMITS a dial stamped
`1970-01-01` carrying `calm` on BOTH surfaces. The only witness that moved was
`tests/test_envelope_freshness.py` (14 failed, 78 passed), a file **no `execute:` line named**,
against **41 distinct `tests/test_*.py` paths the register DOES name.** A memorial, not a
guard. `required-tests.yaml` line ~242 already carries a memorial about a file in this exact
position. This file is the guard.
===========================================================================================

**IT IS BEHAVIOURAL AND NOT STRUCTURAL, AND THAT IS THE WHOLE DESIGN.** It does not read the
stage's source text, does not grep for `REFUSAL_STALE_CALM`, and does not assert that any
function is called from anywhere. It builds candidate envelopes and puts them through
`crash_detector.publication.envelope_contract.refuse_unless_publishable` — **the function the
product itself calls before it writes anything** (`src/crash_detector/publication/publish.py`
lines 276-277, on both surfaces) — and records what the gate actually did. A structural read is
precisely what let this class of defect through repeatedly on this project (`CD-PL-F169`,
`CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`).

Register instruments on this project ARE permitted to import the application — MEASURED, five
already do: `check_exact_type_admission`, `check_engine_no_witness_reach`,
`check_no_numeric_default`, `check_judgement_path_doors` and the sibling row's
`check_missing_data_never_calm`. (`CD-RT-014`'s *"the probe must not import the application"*
rule binds `tools/probe/external_probe.py` and nothing else.)

===========================================================================================
WHAT IS ASSERTED — AND THE ADMITTING ROWS CARRY EQUAL WEIGHT
===========================================================================================

*** THE VACUITY DIRECTION IS EQUALLY A VIOLATION OF THIS ROW, AND IT IS THE HALF THIS
PROJECT'S HISTORY SAYS GETS MISSED. *** A freshness stage that refused EVERYTHING would satisfy
PID §3.2 vacuously by making the dial incapable of ever reading `calm`, and `calm` on a fresh
reading backed by real inputs is the entire reason `calm` exists (PID §4). So every refusing
row here is PAIRED with an admitting one, in the same run, on the same tree, from the same
builder:

    LIMB A — THE LIVE GATE, THROUGH THE FRONT DOOR (`refuse_unless_publishable`), on every
    surface `EnvelopeSurface` declares, at every CANONICAL DIAL SLOT the contract declares:

        calm dial stamped far in the past            ->  MUST REFUSE  [STALE_CALM]
        calm dial stamped in the FUTURE              ->  MUST REFUSE  [STALE_CALM]
        calm dial exactly ONE MICROSECOND past the
          declared window                            ->  MUST REFUSE  [STALE_CALM]
        calm dial aged EXACTLY the declared window   ->  MUST ADMIT   *** VACUITY ***
        calm dial well inside the window             ->  MUST ADMIT   *** VACUITY ***
        STALE dial rendering `elevated`              ->  MUST ADMIT   *** VACUITY ***
        STALE dial rendering `acute`                 ->  MUST ADMIT   *** VACUITY ***

    LIMB B — THE STAGE ITSELF, DRIVEN DIRECTLY, for the propositions the CLOSED CONTRACT makes
    UNREACHABLE through the front door. **THIS IS NOT A CONVENIENCE AND IT IS DECLARED LIMIT 3.**
    On the shipped contracts the ONLY node that can carry `detail_level: "calm"` is a canonical
    dial slot in its `VALUE` branch — MEASURED: `#/$defs/contribution` is closed and declares no
    `detail_level`, `degraded_inputs` is `#/$defs/source_id_list` (an array of plain strings),
    and the root declares `additionalProperties: false`. So a document that puts a calm node
    anywhere ELSE is refused at STAGE 3 as `SCHEMA_VIOLATION` and never reaches stage 4 at all.
    An instrument that only used the front door therefore **could not tell the node walk apart
    from an implementation that reads the two dial slots by name** — which is the exact
    implementation `plants/WO3-INC16D/D3-SLOT-READING-INSTEAD-OF-NODE-WALK.patch` plants, and
    the exact defect class that lost eleven consecutive audit rounds on this row. Limb B drives
    `_refuse_stale_calm` directly, exactly as `tests/test_envelope_freshness.py` already does
    and for the reason that file already states.

        a calm node at a NON-DIAL root property     ->  MUST REFUSE at ITS OWN pointer
        a calm node TWO CONTAINERS DEEP in an array ->  MUST REFUSE at ITS OWN pointer
        a calm node inside a dial's `contributions` ->  MUST REFUSE at ITS OWN pointer
        the same three positions, FRESH             ->  MUST NOT REFUSE  *** VACUITY ***
        a calm node whose OLDEST stamp is stale and
          which carries two FRESHER siblings        ->  MUST REFUSE, naming the OLDEST key
        a calm node whose stamps are ALL fresh      ->  MUST NOT REFUSE  *** VACUITY ***
        a calm node with NO stamp at all            ->  MUST REFUSE  (fail closed)
        a calm node with a `*_utc` that will not
          parse, beside a fresh stamp               ->  MUST REFUSE  (fail closed)
        a root with no usable `published_utc`       ->  MUST REFUSE  (fail closed)
        a root with no usable window (absent, zero,
          negative, boolean, string, non-finite)    ->  MUST REFUSE  (fail closed)
        a root with a usable window and a fresh
          calm node                                 ->  MUST NOT REFUSE  *** VACUITY ***

===========================================================================================
*** THE DECLARED SCOPE OF THIS GUARD — READ THIS BEFORE READING A CLEAN RUN ***
`PO-DECISIONS-0030` ruling 2. Said identically here, in
`contracts/execution/CD-RT-001-STALE-DATA-NEVER-CALM.md` and in `required-tests.yaml`
(`CD-RULE-004`, three places).
===========================================================================================

**THE GATE ENFORCES DOCUMENT-INTERNAL FRESHNESS AND NOTHING WIDER.** What it computes is
`published_utc` MINUS the calm-bearing node's oldest stamp, against the window THE SAME
DOCUMENT declares. That is a claim about the document's INTERNAL COHERENCE — *a dial cannot be
older than its declared window relative to its own declared publication instant* — and it is
not a claim about ACTUAL freshness.

**IT CANNOT CATCH A SOURCE THAT CONSISTENTLY LIES ABOUT ITS OWN STAMP.** A feed that stamps
every reading `now()` regardless of the true age of the data underneath it is internally
consistent and PASSES THIS GATE. So is a uniformly time-shifted envelope: MEASURED by
`CD-ASR-WO3-12` (`A312-F3`) at the target tip with an ordinary 600-second window,
`as_of_utc` = `published_utc` = `1970-01-01T00:00:00Z` is **ADMITTED on both surfaces**. A
replayed envelope, a stopped publisher, a stuck detector clock and a backfill run all produce
exactly that document. **Nothing in a document can prove that about itself.**

*** THAT IS NOT "OUTSIDE ENFORCEMENT" AND IT IS NOT "PERMANENTLY UNENFORCEABLE". THE PRODUCT
AUTHORITY RULED THE OPPOSITE, AND THIS PARAGRAPH IS THE RULING AND NOT THIS SEAT'S OPINION. ***
Source honesty is the SAME CLASS as the `A311-F1` forgery and it has the SAME answer, already
ruled in the THREE-TIER PERIMETER (`PO-DECISIONS-0018`/`0019`, `BLUEPRINT §17` `CD-BP-005`):

  · **PREVENTION** — what is DOCUMENT-INTERNAL is prevented AT THE GATE. That is this stage,
    and that is what this row guards.
  · **DETECTION** — a source that lies about its own freshness is caught ONE TIER OUT, by
    **WITNESS DIVERGENCE + PROVENANCE, `CD-AC-018`**, where a source's CLAIMED freshness is
    corroborated against independent witnesses and DIVERGENCE IS THE ALARM.
  · **WHEN IT IS OWED: AT WO-3**, when real sources and their witnesses land. It is not
    deferred indefinitely and it is not written off.

**AND THE HONESTY OBLIGATION THAT CREATES FOR 16C, RECORDED HERE AND DELIBERATELY NOT BUILT
HERE.** 16C's detector-side liveness marking carries the obligation that the stamps it produces
are **PROVENANCE-BACKED AND WITNESS-CORROBORATABLE**. **16C IS NOT IN THIS INCREMENT.** There
is no `feed_liveness` slot here, no dead-feed detector, and no liveness marking: this file
records the obligation and builds none of it.

**A DECLARED LIMIT THAT SAYS "WE CANNOT DO THIS" WHERE THE TRUTH IS "THIS IS DONE AT THE NEXT
TIER, AT WO-3" IS A FALSE RESIDUAL**, and four sentences on the sibling row have already been
superseded for being false in exactly that reassuring direction.

===========================================================================================
DECLARED LIMITS — THIS ROW'S OWN SEQUENCE, 1 TO 8
===========================================================================================
**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE** (the convention the sibling row
`CD-RT-001-MISSING-DATA-NEVER-CALM` states in all three of its places, whose own sequence runs
1-20). These eight are `CD-RT-001-STALE-DATA-NEVER-CALM`'s and they are said identically in
this header, in `contracts/execution/CD-RT-001-STALE-DATA-NEVER-CALM.md` and in
`required-tests.yaml`. **Quote the row id with the number.**

  1. **IT JUDGES THE CONTRACT THE GATE ACTUALLY LOADS, WHICH IS CONFIGURABLE.**
     `envelope_contract.contracts_dir()` honours `$CD_CONTRACTS_DIR`, so the live gate can be
     pointed at a widened copy while this repository's contracts are byte-intact.
     **WHAT THIS CHECK DOES ABOUT IT:** it exits `3` unless the contracts the gate resolves are
     `<root>/contracts`, and prints their SHA-256 at every run (`CD-PL-F98`). **IT DOES NOT
     PREVENT THE ROUTE. NOT PROVED TO BE CARRIED ANYWHERE.** EXECUTABLE:
       `CD_CONTRACTS_DIR=/tmp/anything python3 tools/register/check_stale_data_never_calm.py --root .`
     -> `PRECONDITION_NOT_MET`, exit 3, never a pass and never a skip.

  2. **THE ENVELOPE ROOT SKELETON IS BUILT FROM THE CONTRACT'S OWN `required` LIST, AND THE
     DIAL FROM ITS OWN BRANCH — BUT THE VALUE VOCABULARY IS A CLOSED WRITTEN LIST.** Each
     property is filled with the FIRST of `SYNTHETIC_VALUES` that the property's OWN subschema
     accepts, decided by `jsonschema` — the same library the gate validates with — and NEVER by
     the property's NAME. A required property that none of them satisfies makes this check
     REPORT (`CD-STALE-BUILD-008`) and exit 1. **DENY BY DEFAULT, so it is not an escape; it IS
     a maintenance cost.** EXECUTABLE: add a required root property with
     `{"type": "string", "pattern": "^ZZZ"}` to either contract and this instrument goes RED.

  3. **LIMB B DRIVES `_refuse_stale_calm` DIRECTLY AND THEREFORE PROVES NOTHING ABOUT WHETHER
     THE GATE CALLS IT.** That is LIMB A's job and only LIMB A's. The two limbs are separable
     and each is separately defeatable: MEASURED, `D1` (the whole stage unreachable from the
     gate) costs LIMB A and costs LIMB B **nothing**, and `D3` (the slot-reading
     implementation) costs LIMB B and costs LIMB A **nothing**. **A REPORT OF THIS ROW THAT
     QUOTES ONE LIMB IS HALF A REPORT.** And limb B is NAME-COUPLED to a private symbol,
     `_refuse_stale_calm`: renaming it makes this instrument exit `3`, deliberately, because a
     check that cannot find its authentic target must fail and never wave through
     (`PBG-CI-002`). That coupling is the same trade `DECLARED LIMIT 12` of the sibling row
     prices and it is ACCEPTED for the same reason.

  4. **IT PROVES NOTHING ABOUT A `VALUE` READING THAT SHOULD NOT HAVE BEEN A `VALUE`, AND
     NOTHING ABOUT THE MISSING HALF.** A dial whose inputs were missing but which was
     constructed as `VALUE` with a fabricated score and a fresh stamp renders calm legitimately
     as far as THIS row is concerned, and this check ADMITS IT — the vacuity rows say so out
     loud, and they must. **THE CARRIERS ARE THE THREE SIBLING ENTRIES ON `CD-AC-001`:**
     `CD-RT-001-AST-NO-NUMERIC-DEFAULT` (the provenance of the magnitude),
     `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` (the runtime post-condition) and
     `CD-RT-001-MISSING-DATA-NEVER-CALM` (the MISSING half at the gate, including `RULE CC`).
     **THIS IS ONE OF FOUR GUARDS ON `CD-AC-001` AND NEVER A SOLE GUARD.**

  5. **IT DOES NOT RE-DERIVE THE ROOT PARTITION.** It drives the CANONICAL DIAL SLOTS — root
     properties spelled literally `{"$ref": "#/$defs/dial_reading"}` — and if the contract
     declares none it exits `3` rather than reporting clean. Whether some OTHER root property
     could carry a dial at all is `RULE CC`'s question and it is asserted on the SIBLING row
     (`CD-CALM-ROOT-008`), not here. **A root property this row does not drive is not a
     property this row says anything about.**

  6. **IT IS A CLAIM ABOUT DOCUMENTS THE GATE SEES.** A rendering path that never calls
     `refuse_unless_publishable` is outside this check entirely. MEASURED at this commit: the
     only callers in `src/` are `publication/publish.py` lines 276-277, on both surfaces,
     before any write. **A FUTURE SERVING LAYER THAT RENDERS A DIAL WITHOUT PUBLISHING AN
     ENVELOPE IS NOT PROVED TO BE CARRIED ANYWHERE.**

  7. **IT NEEDS `jsonschema`, BECAUSE THE GATE DOES.** If `jsonschema` is absent it exits `3`
     with the reason — never a pass and never a skip (`PBG-CI-002`).

  8. **THE DECLARED SCOPE ABOVE IS THIS ROW'S LARGEST LIMIT AND IT IS STATED IN FULL RATHER
     THAN CROSS-REFERENCED.** The gate is DOCUMENT-INTERNAL. A source that consistently lies
     about its own stamp passes it, and a uniformly time-shifted envelope passes it —
     `as_of_utc` = `published_utc` = `1970-01-01T00:00:00Z` with an ordinary 600-second window
     is ADMITTED, MEASURED, and this instrument's own `CD-STALE-SCOPE-009` assertion **DRIVES
     THAT DOCUMENT AND REQUIRES IT TO BE ADMITTED**, so the limit cannot go stale in the
     reassuring direction while the code changes underneath it. Closing that class needs a
     comparand from OUTSIDE the document, which is the DETECTION tier — `CD-AC-018`, witness
     divergence + provenance — **OWED AT WO-3**. It is enforced one tier out and it is not
     unenforceable.

===========================================================================================
FOR THE AUDITOR
===========================================================================================
Do not read a clean run of this check as proof that no stale reading can ever render as calm.
It proves that the LIVE PUBLICATION GATE refuses a DOCUMENT-INTERNALLY stale calm node, on both
surfaces, at every canonical dial slot AND at every position in the document the walk reaches,
while still admitting everything the product must be able to publish. **The arm to weigh it
against is the vacuity set**: an instrument that refused everything would be enforcing silence
rather than holding PID §3.2. **The four arms to weigh it with are
`plants/WO3-INC16E/MANIFEST.md`'s `D1`-`D4`**, each a measured tree with its rc and its
violation count.
"""

from __future__ import annotations

import copy
import hashlib
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-001-STALE-DATA-NEVER-CALM"

MUST_REFUSE = "MUST REFUSE"
MUST_ADMIT = "MUST ADMIT"

#: The level the criterion names. PID §3.2, verbatim: "Missing OR STALE data must never render
#: as calm." Judged by VALUE against the contract's own vocabulary, never by the name of the
#: `$def` it comes from (`CD-PL-F169`, `CD-ASR-WO3-02` F06/F07).
CALM = "calm"

#: The canonical dial slot spelling. A root property whose value is LITERALLY this mapping.
CANONICAL_DIAL_REF = {"$ref": "#/$defs/dial_reading"}

#: The document's declared publication instant. Every stamp below is expressed relative to it,
#: and NOTHING here reads a clock — neither this file nor the stage it drives (the stage's own
#: no-clock guarantee is `BP-AMENDMENT-0001` §D.3 and is asserted by
#: `tests/test_envelope_freshness.py`, not here).
PUBLISHED = "2026-08-24T18:00:00Z"

#: The declared window, in seconds, and the stamps that sit exactly on and just past its edge.
WINDOW_SECONDS = 600.0
STAMP_FRESH = "2026-08-24T17:59:30Z"            # 30s old — well inside
STAMP_ON_THE_EDGE = "2026-08-24T17:50:00Z"      # exactly 600s old — the CLOSED interval
STAMP_ONE_MICROSECOND_PAST = "2026-08-24T17:49:59.999999Z"   # 600.000001s old
STAMP_ANCIENT = "1970-01-01T00:00:00Z"          # fifty-six years old
STAMP_FUTURE = "2099-01-01T00:00:00Z"           # stamped AFTER publication: incoherent
STAMP_SECOND_FRESH = "2026-08-24T17:59:45Z"
STAMP_THIRD_FRESH = "2026-08-24T17:59:50Z"

#: Deliberately unmistakable, for the same reason the sibling row's are: a grep for one of these
#: lands HERE and nowhere near a source registry. **NOTHING IN THIS FILE REGISTERS A SOURCE**
#: (`Q25`, `CD-PL-F154`): nothing constructs a `SourceRecord`, imports
#: `crash_detector.source_registry`, or names `raw.source_registry`.
SYNTHETIC_INPUT_ID = "SYNTHETIC-STALE-REGISTER-CHECK-NOT-A-SOURCE"
SYNTHETIC_TEXT = "SYNTHETIC-STALE-REGISTER-CHECK-NOT-A-VALUE"

#: Synthetic and meaningless as a number. The dial has no ratified scale (`Q25` holds it).
SYNTHETIC_SCORE = 0.01

#: *** THE DECLARED VALUE VOCABULARY, A CLOSED LIST ON PURPOSE (RULE F), AND THE SAME DEVICE
#: `check_missing_data_never_calm.SYNTHETIC_VALUES` uses. *** Every property of the root and of
#: the calm-bearing branch is filled with the FIRST of these that the property's OWN subschema
#: ACCEPTS — decided by `jsonschema` and never by the property's NAME. A required property none
#: of them satisfies is REPORTED (`CD-STALE-BUILD-008`), never skipped. Order is the only thing
#: tuned: the plain string precedes the timestamp so a free-text property gets text and a
#: `pattern`-constrained one gets the timestamp.
SYNTHETIC_VALUES = (
    SYNTHETIC_TEXT,             # a bounded, non-empty, unpatterned string
    STAMP_FRESH,                # a UTC timestamp string
    SYNTHETIC_SCORE,            # a number
    [SYNTHETIC_INPUT_ID],       # a non-empty array of id-shaped strings
    [],                         # an empty array
    {},                         # an empty object
    True,                       # a boolean
    None,                       # null
)

#: A string that is shaped like nothing and parses as no instant. Used to prove a property that
#: ANNOUNCES itself as a stamp by name and does not read as one is a REFUSAL and never a skip.
NOT_A_STAMP = "SYNTHETIC-STALE-REGISTER-CHECK-NOT-AN-INSTANT"

#: Windows that are not windows. Each MUST make a calm-bearing node refuse, because an
#: unbounded, absent, reversed or type-confused window is no window. `True` is in the list on
#: purpose: it is an `int` in Python and would otherwise read as a one-second window nobody
#: declared, arrived at by a type confusion.
UNUSABLE_WINDOWS = (
    ("ABSENT", None),
    ("ZERO", 0),
    ("NEGATIVE", -1.0),
    ("BOOLEAN-TRUE", True),
    ("STRING", "600"),
    ("NOT-FINITE", float("inf")),
    ("NOT-A-NUMBER", float("nan")),
)

#: Values of `published_utc` from which no age can be computed. Each MUST refuse every
#: calm-bearing node in the document rather than be assumed fresh.
UNUSABLE_PUBLISHED = (
    ("ABSENT", None),
    ("UNPARSABLE", NOT_A_STAMP),
    ("SHAPE-VALID-NON-INSTANT", "2026-13-45T99:99:99Z"),
)

#: Only these keys may sit beside a `$ref` without changing what the node admits — every one is
#: a pure ANNOTATION in 2020-12. Carried from the sibling row's resolver, where the reasoning is
#: written in full (`DECLARED LIMIT 13`): in 2020-12 keywords SIBLING to `$ref` ARE APPLIED, so
#: a resolver that discards them silently is judging a schema the gate does not enforce.
REF_INERT_SIBLINGS = frozenset({
    "$ref", "$comment", "title", "description",
    "default", "deprecated", "readOnly", "writeOnly", "examples",
})

#: How many `$ref` hops :func:`_resolve` follows before giving up. Reaching it returns `None`,
#: which every caller treats as UNRECOGNISED — never as "nothing to see".
REF_CHAIN_CAP = 32


# ------------------------------------------------------------------------------------------ #
# Schema plumbing. Small, deliberate duplicates of the sibling row's helpers: every check in
# `tools/register/` is a STANDALONE script (see `_support.__doc__`), and an auditor extracting a
# tree runs this file on its own.
# ------------------------------------------------------------------------------------------ #

def _fragment(schema: dict, subschema: dict) -> dict:
    """``subschema`` as a standalone document, so its local ``#/$defs/...`` refs still resolve."""
    fragment = dict(subschema)
    fragment.setdefault("$schema", schema.get("$schema")
                        or "https://json-schema.org/draft/2020-12/schema")
    fragment.setdefault("$defs", schema.get("$defs") or {})
    return fragment


def _resolve(schema: dict, node, depth: int = 0):
    """Follow a chain of LOCAL ``#/...`` refs. Returns ``(resolved, dropped)``.

    ``dropped`` names every hop that carried an ASSERTING key beside its ``$ref``, so a caller
    can refuse rather than silently judge a node the chain rewrote.
    """
    dropped: list = []
    while isinstance(node, dict) and "$ref" in node:
        if depth >= REF_CHAIN_CAP:
            return None, dropped
        ref = node["$ref"]
        asserting = sorted(key for key in node if key not in REF_INERT_SIBLINGS)
        if asserting:
            dropped.append((depth, ref if isinstance(ref, str) else repr(ref), asserting))
        if not isinstance(ref, str) or not ref.startswith("#/"):
            return None, dropped
        cursor = schema
        for token in ref[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(cursor, dict) or token not in cursor:
                return None, dropped
            cursor = cursor[token]
        node, depth = cursor, depth + 1
    return (node if isinstance(node, dict) else None), dropped


def _deref(schema: dict, node, depth: int = 0):
    """The resolved node only, for callers with no siblings to lose."""
    return _resolve(schema, node, depth)[0]


def _accepts(schema: dict, subschema, validator, value) -> bool:
    """Does ``subschema`` accept ``value``? Decided by `jsonschema`, never by a property NAME."""
    if not isinstance(subschema, dict):
        return False
    try:
        return bool(validator(_fragment(schema, subschema)).is_valid(value))
    except Exception:  # pragma: no cover - a subschema jsonschema cannot compile
        return False


def _synthesise(schema: dict, subschema, validator):
    """A value the property's OWN subschema accepts.

    Returns ``(value, True)`` on success and ``(None, False)`` on failure, so a legitimate
    ``null`` is never confused with an unbuildable property.
    """
    if not isinstance(subschema, dict):
        return None, False
    resolved = _deref(schema, subschema)
    candidates: list = []
    if isinstance(resolved, dict):
        if "const" in resolved:
            candidates.append(resolved["const"])
        if isinstance(resolved.get("enum"), list):
            candidates.extend(resolved["enum"])
    candidates.extend(SYNTHETIC_VALUES)
    try:
        checker = validator(_fragment(schema, subschema))
    except Exception:  # pragma: no cover
        return None, False
    for candidate in candidates:
        try:
            if checker.is_valid(candidate):
                return candidate, True
        except Exception:  # pragma: no cover
            continue
    return None, False


def _canonical_dial_slots(schema: dict) -> list:
    """Root properties spelled LITERALLY ``{"$ref": "#/$defs/dial_reading"}``. Sorted."""
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []
    return sorted(
        name for name, sub in properties.items()
        if isinstance(sub, dict) and sub == CANONICAL_DIAL_REF
    )


def _calm_bearing_branch(schema: dict, validator):
    """The ``#/$defs/dial_reading.oneOf`` branch whose ``detail_level`` ADMITS ``calm``.

    Returns ``(label, branch, dropped)`` or ``(None, None, dropped)``. The branch is identified
    by WHAT ITS OWN SUBSCHEMA ACCEPTS and never by the name of the ``$def`` it lives in — a
    structural read of `$ref` target names is what let this class through three times here.
    """
    union, dropped = _resolve(schema, (schema.get("$defs") or {}).get("dial_reading"))
    if not isinstance(union, dict):
        return None, None, dropped
    branches = union.get("oneOf")
    if not isinstance(branches, list):
        return None, None, dropped
    for index, entry in enumerate(branches):
        resolved, entry_dropped = _resolve(schema, entry)
        dropped = dropped + entry_dropped
        if not isinstance(resolved, dict):
            continue
        properties = resolved.get("properties")
        if not isinstance(properties, dict):
            continue
        if _accepts(schema, properties.get("detail_level"), validator, CALM):
            state = properties.get("state")
            label = (state.get("const") if isinstance(state, dict) else None) or f"[{index}]"
            return str(label), resolved, dropped
    return None, None, dropped


def _stamp_properties(schema: dict, branch: dict, validator) -> list:
    """Properties of ``branch`` that are STAMP-SHAPED, decided behaviourally.

    A property is stamp-shaped when its own subschema ACCEPTS a UTC instant string and REJECTS
    a string that is not one. **NEVER BY NAME:** the contracts spell the stamp ``as_of_utc`` on
    two branches and ``since_utc`` on a third, so a fixed property name would already be wrong,
    and a contract that spells it a fourth way tomorrow would make a name-reading instrument
    silently stop finding stamps — which is *admitting*, not refusing.
    """
    properties = branch.get("properties")
    if not isinstance(properties, dict):
        return []
    return sorted(
        name for name, sub in properties.items()
        if _accepts(schema, sub, validator, STAMP_FRESH)
        and not _accepts(schema, sub, validator, NOT_A_STAMP)
    )


def _pointer_tokens(node, pointer: str = ""):
    """``(node, pointer)`` for every node in a document, root first. RFC 6901 escaping."""
    yield node, pointer
    if isinstance(node, dict):
        for key, value in node.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            yield from _pointer_tokens(value, f"{pointer}/{token}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _pointer_tokens(value, f"{pointer}/{index}")


def _differing_pointers(left, right) -> list:
    """Every JSON pointer at which two documents differ — by value OR by presence."""
    left_map = {pointer: node for node, pointer in _pointer_tokens(left)
                if not isinstance(node, (dict, list))}
    right_map = {pointer: node for node, pointer in _pointer_tokens(right)
                 if not isinstance(node, (dict, list))}
    differing = set(left_map) ^ set(right_map)
    for pointer in set(left_map) & set(right_map):
        if left_map[pointer] != right_map[pointer]:
            differing.add(pointer)
    return sorted(differing)


def main(argv=None) -> int:
    args = parse_root(CHECK_ID, __doc__.splitlines()[0])
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code
    check = Check(CHECK_ID, root)

    src = root / "src"
    if not (src / "crash_detector" / "__init__.py").is_file():
        return check.refuse(
            f"{src}/crash_detector/__init__.py does not exist, so there is no gate to drive. "
            "'REFUSED' is a RUNTIME claim and this check will not make it against a tree it "
            "could not load."
        )

    sys.path.insert(0, str(src))
    for name in [
        m for m in sys.modules if m == "crash_detector" or m.startswith("crash_detector.")
    ]:
        del sys.modules[name]

    try:
        import crash_detector  # noqa: F401
        from crash_detector.publication.envelope_contract import (
            ENVELOPE_SCHEMA_VERSION,
            EnvelopeSurface,
            PublicationRefused,
            REFUSAL_STALE_CALM,
            contracts_dir,
            load_envelope_schema,
            refuse_unless_publishable,
            schema_path_for,
        )
    except Exception as exc:
        return check.refuse(
            f"the subject tree at {src} did not import: {type(exc).__name__}: {exc}. If this "
            "is a missing `jsonschema`, that is DECLARED LIMIT 7: this check drives the live "
            "gate and the live gate validates with jsonschema."
        )

    # ---- THE STAGE ITSELF, FOR LIMB B — DECLARED LIMIT 3 ----------------------------- #
    # A check that cannot find its authentic target FAILS. It does not fall back to limb A and
    # report clean on half the propositions (`PBG-CI-002`, `PBG-EVID-002`).
    try:
        from crash_detector.publication.envelope_contract import _refuse_stale_calm
    except Exception as exc:
        return check.refuse(
            f"`crash_detector.publication.envelope_contract._refuse_stale_calm` did not import "
            f"({type(exc).__name__}: {exc}). LIMB B drives the fourth refusal stage directly, "
            "because the CLOSED contracts make every calm-bearing position except a canonical "
            "dial slot unreachable through the front door, and an instrument that only used "
            "the front door could not tell the NODE WALK apart from an implementation that "
            "reads the two dial slots BY NAME. This is DECLARED LIMIT 3's name coupling, and "
            "it fails loudly rather than quietly measuring less."
        )

    try:
        import jsonschema  # noqa: F401
        from jsonschema.validators import validator_for
    except Exception as exc:
        return check.refuse(
            f"`jsonschema` did not import ({type(exc).__name__}: {exc}). DECLARED LIMIT 7: this "
            "check drives the live gate, the live gate validates with jsonschema, and a "
            "behavioural check cannot be more stdlib-only than the behaviour it drives."
        )

    package_dir = pathlib.Path(crash_detector.__file__).resolve().parent
    # CD-PL-F98 — READ THE TREE LINE EVERY TIME. A contrast run against the wrong tree is
    # indistinguishable from a fix that does nothing.
    check.note(f"imported crash_detector from: {package_dir / '__init__.py'}")
    check.note(f"python: {sys.version.split()[0]}")
    check.note(f"ENVELOPE_SCHEMA_VERSION as the application declares it: {ENVELOPE_SCHEMA_VERSION}")
    check.note(f"the refusal token this row requires: {REFUSAL_STALE_CALM!r}")

    # ---- DECLARED LIMIT 1, ENFORCED AS A PRECONDITION -------------------------------- #
    resolved_contracts = contracts_dir().resolve()
    if resolved_contracts != (root / "contracts").resolve():
        return check.refuse(
            f"the live gate resolves its contracts to {resolved_contracts}, which is NOT "
            f"{(root / 'contracts').resolve()}. $CD_CONTRACTS_DIR is set, or the package was "
            "imported from outside --root. This check judges the contract the gate ACTUALLY "
            "LOADS, so it will not report on a tree it is not looking at (DECLARED LIMIT 1)."
        )

    schemas = {}
    for surface in EnvelopeSurface:
        path = schema_path_for(surface)
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            return check.refuse(f"cannot read {path}: {type(exc).__name__}: {exc}")
        check.note(f"judging {surface.value} contract {path} sha256:{digest}")
        try:
            schemas[surface] = load_envelope_schema(surface)
        except Exception as exc:
            return check.refuse(
                f"the {surface.value} contract is not loadable by the gate: "
                f"{type(exc).__name__}: {exc}. The candidate would never be judged, so this "
                "check has nothing to measure."
            )

    here = pathlib.Path(__file__)

    # ---- CD-STALE-VACUITY-000 — THE ADMITTING ROWS CANNOT BE QUIETLY DELETED --------- #
    # The sibling row learned this the expensive way: an instrument that only checked "the bad
    # thing is refused" is satisfied by a tree on which NOTHING can be published. This assertion
    # is about THIS FILE'S OWN TABLE, so the vacuity arms cannot be removed from the instrument
    # that exists to carry them.
    check.asserted()
    gate_table = (
        ("ANCIENT", STAMP_ANCIENT, CALM, MUST_REFUSE),
        ("FUTURE", STAMP_FUTURE, CALM, MUST_REFUSE),
        ("ONE-MICROSECOND-PAST-THE-WINDOW", STAMP_ONE_MICROSECOND_PAST, CALM, MUST_REFUSE),
        ("EXACTLY-THE-WINDOW", STAMP_ON_THE_EDGE, CALM, MUST_ADMIT),
        ("WELL-INSIDE-THE-WINDOW", STAMP_FRESH, CALM, MUST_ADMIT),
        ("ANCIENT-BUT-NOT-CALM", STAMP_ANCIENT, None, MUST_ADMIT),
    )
    admitting = [row for row in gate_table if row[3] is MUST_ADMIT]
    refusing = [row for row in gate_table if row[3] is MUST_REFUSE]
    missing_directions = []
    if not any(row[2] == CALM for row in admitting):
        missing_directions.append("a FRESH CALM dial that must still be ADMITTED")
    if not any(row[1] == STAMP_ON_THE_EDGE for row in admitting):
        missing_directions.append("the CLOSED-INTERVAL boundary row (age EXACTLY the window)")
    if not any(row[2] is None for row in admitting):
        missing_directions.append("a STALE NON-CALM dial that must still be ADMITTED")
    if not refusing:
        missing_directions.append("any refusing row at all")
    if missing_directions:
        check.violation(
            here, 0, "CD-STALE-VACUITY-000",
            "this instrument's OWN proposition table has lost "
            f"{missing_directions!r}. A row that refuses everything is not a row on which "
            "CD-AC-001 holds — it is a row on which the product can no longer publish a calm "
            "reading at all, and PID §4 makes calm the base case. The admitting arms carry "
            "equal weight and may not be deleted from the instrument that exists to carry them.",
        )
    else:
        check.note(
            f"VACUITY GUARD: the table declares {len(refusing)} MUST-REFUSE and "
            f"{len(admitting)} MUST-ADMIT rows, including the fresh-calm row, the "
            "closed-interval boundary row and the stale-but-not-calm row."
        )

    # ---- THE SUBJECT SET, ENUMERATED FROM THE APPLICATION AND THE CONTRACTS ---------- #
    slots_by_surface = {}
    branch_by_surface = {}
    stamps_by_surface = {}
    for surface in EnvelopeSurface:
        schema = schemas[surface]
        validator = validator_for(schema)
        slots = _canonical_dial_slots(schema)
        if not slots:
            return check.refuse(
                f"the {surface.value} contract declares NO canonical dial slot "
                f"({CANONICAL_DIAL_REF!r}) at its root, so there is no calm-bearing dial to "
                "age and this check would be measuring nothing. DECLARED LIMIT 5."
            )
        label, branch, dropped = _calm_bearing_branch(schema, validator)
        if branch is None:
            return check.refuse(
                f"no branch of the {surface.value} contract's #/$defs/dial_reading.oneOf has a "
                "detail_level that admits 'calm', so no document this contract accepts can "
                "carry a calm dial and this check cannot drive its own subject. That is either "
                "a contract in which calm is unrepresentable — which is the VACUOUS direction "
                "and a defect in itself (PID §4 makes calm the base case) — or a union this "
                "check cannot read."
            )
        if dropped:
            check.asserted()
            check.violation(
                here, 0, "CD-STALE-BUILD-008",
                f"{surface.value}: a $ref on the way to the calm-bearing branch carries an "
                f"ASSERTING sibling ({dropped!r}). In JSON Schema 2020-12 a keyword beside a "
                "$ref IS APPLIED, so the branch this check would drive is NOT the branch the "
                "gate enforces. Reported rather than resolved: a resolver that discards "
                "siblings can only ever WEAKEN this instrument, silently.",
            )
        stamps = _stamp_properties(schema, branch, validator)
        if not stamps:
            return check.refuse(
                f"the {surface.value} contract's calm-bearing branch {label!r} declares NO "
                "stamp-shaped property (one whose own subschema accepts a UTC instant and "
                "rejects a non-instant), so a calm dial on this contract cannot date its own "
                "data and there is nothing for this check to age. A branch that requires no "
                "timestamp cannot prove freshness — the sibling row asserts that structurally "
                "as CD-CALM-CANON-009; this row refuses to measure without one."
            )
        slots_by_surface[surface] = slots
        branch_by_surface[surface] = (label, branch)
        stamps_by_surface[surface] = stamps
        check.note(
            f"{surface.value}: dial slots {slots!r} · calm-bearing branch {label!r} · "
            f"stamp-shaped properties {stamps!r} (decided by what each subschema ACCEPTS, "
            "never by name)"
        )

    # ---- THE BUILDERS ---------------------------------------------------------------- #
    def build_dial(surface, level, stamp):
        """One dial from the calm-bearing branch's OWN required + properties."""
        schema = schemas[surface]
        validator = validator_for(schema)
        _label, branch = branch_by_surface[surface]
        properties = branch.get("properties") or {}
        required = branch.get("required") or []
        dial = {}
        unbuildable = []
        for name in required:
            sub = properties.get(name)
            value, built = _synthesise(schema, sub, validator)
            if not built:
                unbuildable.append(name)
                continue
            dial[str(name)] = copy.deepcopy(value)
        for name in stamps_by_surface[surface]:
            if name in dial:
                dial[name] = stamp
        if level is not None:
            dial["detail_level"] = level
        return dial, unbuildable

    def build_root(surface, dials, window=WINDOW_SECONDS, published=PUBLISHED):
        """The envelope root from the contract's OWN required list."""
        schema = schemas[surface]
        validator = validator_for(schema)
        properties = schema.get("properties") or {}
        required = schema.get("required") or []
        document = {}
        unbuildable = []
        for name in required:
            if name in dials:
                document[str(name)] = copy.deepcopy(dials[name])
                continue
            value, built = _synthesise(schema, properties.get(name), validator)
            if not built:
                unbuildable.append(name)
                continue
            document[str(name)] = copy.deepcopy(value)
        if published is None:
            document.pop("published_utc", None)
        else:
            document["published_utc"] = published
        if window is None:
            document.pop("staleness_window_seconds", None)
        else:
            document["staleness_window_seconds"] = window
        return document, unbuildable

    def verdict(surface, document):
        """What the LIVE GATE did. Never a boolean: the reason class is load-bearing."""
        try:
            refuse_unless_publishable(copy.deepcopy(document), surface=surface)
        except PublicationRefused as exc:
            return exc
        except Exception as other:
            return other
        return None

    # ================================================================================== #
    # LIMB A — THE LIVE GATE, THROUGH THE FRONT DOOR.
    # This is the limb `D1` (the whole stage unreachable from the gate) and `D2` (the naive
    # `age > window`) are measured against.
    # ================================================================================== #
    cells = 0
    for surface in EnvelopeSurface:
        slots = slots_by_surface[surface]
        branch_label, _branch = branch_by_surface[surface]
        stamps = stamps_by_surface[surface]

        fresh_dial, unbuildable = build_dial(surface, CALM, STAMP_FRESH)
        if unbuildable:
            check.asserted()
            check.violation(
                here, 0, "CD-STALE-BUILD-008",
                f"{surface.value}/{branch_label}: this check could not build a value for the "
                f"required propert(ies) {unbuildable!r} out of its declared closed vocabulary, "
                "so the calm-bearing dial was never constructed and NOTHING below measured it. "
                "DENY BY DEFAULT (DECLARED LIMIT 2): reported and non-zero, never skipped.",
            )
            continue

        for slot_under_test in slots:
            dials = {slot: copy.deepcopy(fresh_dial) for slot in slots}
            baseline, root_unbuildable = build_root(surface, dials)
            if root_unbuildable:
                check.asserted()
                check.violation(
                    here, 0, "CD-STALE-BUILD-008",
                    f"{surface.value}: this check could not build a value for the required "
                    f"root propert(ies) {root_unbuildable!r}, so no candidate envelope was "
                    "constructed. DENY BY DEFAULT (DECLARED LIMIT 2).",
                )
                continue

            # The baseline must be publishable, or every refusal below is attributable to the
            # skeleton rather than to the stamp under test. FAIL CLOSED, LOUDLY.
            check.asserted()
            cells += 1
            baseline_outcome = verdict(surface, baseline)
            if baseline_outcome is not None:
                check.violation(
                    here, 0, "CD-STALE-GATE-001",
                    f"{surface.value}/{slot_under_test}/BASELINE-FRESH-CALM: the gate REFUSED "
                    f"the all-fresh calm baseline ({baseline_outcome!r}). *** THIS IS THE "
                    "VACUOUS DIRECTION AND IT IS EQUALLY A VIOLATION OF THIS ROW. *** A tree "
                    "on which the product cannot publish a genuinely fresh calm reading is not "
                    "a tree on which CD-AC-001 holds; it is a tree that has stopped being able "
                    "to say anything. It also means every refusal this run reports is "
                    "attributable to the document skeleton and not to the stamp under test.",
                )
                continue
            check.note(f"{surface.value}/{slot_under_test}/BASELINE-FRESH-CALM: ADMITTED")

            for row_label, stamp, level, expectation in gate_table:
                candidate = copy.deepcopy(baseline)
                mutated, unbuildable_row = build_dial(
                    surface, CALM if level is None else level, stamp
                )
                if unbuildable_row:
                    check.asserted()
                    check.violation(
                        here, 0, "CD-STALE-BUILD-008",
                        f"{surface.value}/{slot_under_test}/{row_label}: unbuildable "
                        f"{unbuildable_row!r} (DECLARED LIMIT 2).",
                    )
                    continue
                if level is None:
                    # The stale-but-not-calm vacuity row: pick a declared level that is NOT
                    # calm, out of the branch's own detail_level subschema, never typed in.
                    schema = schemas[surface]
                    validator = validator_for(schema)
                    _lab, branch = branch_by_surface[surface]
                    sub = (branch.get("properties") or {}).get("detail_level")
                    resolved = _deref(schema, sub)
                    vocabulary = []
                    if isinstance(resolved, dict) and isinstance(resolved.get("enum"), list):
                        vocabulary = [v for v in resolved["enum"] if v != CALM]
                    if not vocabulary:
                        check.asserted()
                        check.violation(
                            here, 0, "CD-STALE-VACUITY-000",
                            f"{surface.value}/{slot_under_test}: the calm-bearing branch's "
                            "detail_level vocabulary contains NOTHING BUT 'calm', so this row "
                            "cannot drive a stale reading that renders at its TRUE level. A "
                            "contract in which the only thing a present dial can say is 'calm' "
                            "leaves the product no way to report a stale reading honestly.",
                        )
                        continue
                    mutated["detail_level"] = vocabulary[0]
                candidate[slot_under_test] = mutated

                label = f"{surface.value}/{slot_under_test}/{row_label}"
                check.asserted()
                cells += 1
                outcome = verdict(surface, candidate)

                if expectation is MUST_ADMIT:
                    if outcome is None:
                        check.note(f"{label}: ADMITTED")
                        continue
                    what = (
                        "*** THE VACUOUS DIRECTION, AND IT IS EQUALLY A VIOLATION OF THIS "
                        "ROW. *** "
                    )
                    if row_label == "EXACTLY-THE-WINDOW":
                        what += (
                            "A reading aged EXACTLY the declared window is INSIDE it: the "
                            "predicate is a CLOSED interval, and a stage that refuses the "
                            "boundary is refusing a reading the declared rule admits. "
                        )
                    elif level is None:
                        what += (
                            "The stage guards `calm` and ONLY `calm` — that is the criterion's "
                            "own scope, 'never renders as CALM'. A stale reading rendering at "
                            "its TRUE level is the product working correctly, and refusing it "
                            "removes the product's only honest way to report a stale dial. "
                        )
                    else:
                        what += (
                            "A genuinely fresh calm reading must still publish. PID §4 makes "
                            "calm the base case, and an instrument satisfied by a contract "
                            "that refuses everything guards nothing. "
                        )
                    check.violation(
                        here, 0, "CD-STALE-GATE-001",
                        f"{label}: {what}The gate REFUSED it: {outcome!r}.",
                    )
                    continue

                # MUST REFUSE.
                if outcome is None:
                    if row_label == "FUTURE":
                        what = (
                            "*** THE LIVE GATE ADMITTED A CALM DIAL STAMPED AFTER THE ENVELOPE "
                            "WAS PUBLISHED. *** Data from the future is INCOHERENT rather than "
                            "fresh, and a NEGATIVE AGE IS NOT A SMALL AGE. This is exactly "
                            "what the obvious `age > window` formula leaves open, and it is "
                            "arm D2 of plants/WO3-INC16E/."
                        )
                    elif row_label == "ONE-MICROSECOND-PAST-THE-WINDOW":
                        what = (
                            "*** THE LIVE GATE ADMITTED A CALM DIAL ONE MICROSECOND PAST THE "
                            "WINDOW THE DOCUMENT ITSELF DECLARES. *** The boundary is decided "
                            "in integer microseconds precisely so it is not a float one ULP "
                            "the wrong side of the edge."
                        )
                    else:
                        what = (
                            "*** THE LIVE GATE ADMITTED A STALE DIAL RENDERING AS CALM. *** "
                            "PID §3.2 is constitutional and its words are 'Missing OR STALE "
                            "data must never render as calm'. The reading is older than the "
                            "staleness window THE DOCUMENT ITSELF DECLARES, and the repair is "
                            "to render it at its true level — never to widen the window."
                        )
                    check.violation(
                        here, 0, "CD-STALE-GATE-001",
                        f"{label}: {what} refuse_unless_publishable returned None and nothing "
                        "stopped the write.",
                    )
                    continue

                # ---- CD-STALE-REASON-002 — THE RIGHT OUTCOME FROM THE RIGHT LAYER ---- #
                # `CD-PL-F74` is this project's most-repeated defect: the right outcome
                # arriving from the wrong layer. A candidate refused as SCHEMA_VIOLATION
                # proves the skeleton is wrong, not that the freshness stage works.
                check.asserted()
                if not isinstance(outcome, PublicationRefused):
                    check.violation(
                        here, 0, "CD-STALE-REASON-002",
                        f"{label}: the gate raised {type(outcome).__name__} and not the "
                        f"declared PublicationRefused: {outcome!r}. An unexpected exception is "
                        "not a refusal (CD-PL-F74).",
                    )
                    continue
                expected_pointer = f"/{slot_under_test}"
                if (outcome.reason_class != REFUSAL_STALE_CALM
                        or outcome.pointer != expected_pointer):
                    check.violation(
                        here, 0, "CD-STALE-REASON-002",
                        f"{label}: REFUSED with reason_class {outcome.reason_class!r} at "
                        f"{outcome.pointer!r}, and this row requires {REFUSAL_STALE_CALM!r} at "
                        f"{expected_pointer!r}. A refusal from ANOTHER layer — a schema "
                        "violation caused by this check's own skeleton, for instance — would "
                        "otherwise be counted as the freshness stage working, which is the "
                        "right outcome from the wrong layer (CD-PL-F74).",
                    )
                    continue
                check.note(
                    f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer} "
                    f"key {outcome.key!r}"
                )

                # ---- CD-STALE-PAIRED-003 — ONE TOKEN MOVED, OPPOSITE OUTCOME --------- #
                # The refusal must be caused by the STAMP. The refused candidate and the
                # ADMITTED baseline must be the same document apart from the stamp(s) of the
                # slot under test.
                #
                # *** THE GUARD BELOW WAS WRITTEN INVERTED IN THIS FILE'S FIRST DRAFT AND THIS
                # WHOLE LIMB WAS DEAD. RAISED BY THIS SEAT AGAINST ITS OWN WORK AS
                # `CD-ENG-F16E-01` AND CAUGHT ON THE FIRST RUN, because the run printed not one
                # `PAIRED` note. It read `if level is not None: continue`, and every MUST-REFUSE
                # row carries `level = CALM`, so it skipped every one of them; the only row with
                # `level is None` is the stale-but-not-calm VACUITY row, which is `MUST_ADMIT`
                # and has already `continue`d above. **A DEAD ASSERTION DETECTS NOTHING WHILE
                # LOOKING LIKE COVERAGE**, in a file whose entire subject is a guarantee nobody
                # ran. Fixed, and RECORDED rather than quietly corrected.
                if level is None:
                    continue
                check.asserted()
                differing = _differing_pointers(candidate, baseline)
                expected = sorted(f"/{slot_under_test}/{key}" for key in stamps)
                if differing != expected:
                    check.violation(
                        here, 0, "CD-STALE-PAIRED-003",
                        f"{label}: the refused candidate and its ADMITTED pair differ at "
                        f"{differing!r}, not at exactly {expected!r}. The two documents must "
                        "be identical apart from the stamp under test, or the opposite "
                        "outcomes cannot be attributed to it.",
                    )
                else:
                    check.note(f"{label}: PAIRED — sole difference {expected!r}")

    # ================================================================================== #
    # LIMB B — THE STAGE ITSELF. DECLARED LIMIT 3.
    # This is the limb `D3` (the forbidden slot-read) and `D4` (newest-governs) are measured
    # against, and it is where the FAIL-CLOSED branches live.
    # ================================================================================== #
    def stage_outcome(surface, document):
        try:
            _refuse_stale_calm(copy.deepcopy(document), surface)
        except PublicationRefused as exc:
            return exc
        except Exception as other:
            return other
        return None

    NON_DIAL_ROOT = "synthetic_16e_probe"

    for surface in EnvelopeSurface:
        slots = slots_by_surface[surface]
        stamps = stamps_by_surface[surface]
        fresh_dial, unbuildable = build_dial(surface, CALM, STAMP_FRESH)
        if unbuildable:
            continue
        dials = {slot: copy.deepcopy(fresh_dial) for slot in slots}
        base_document, root_unbuildable = build_root(surface, dials)
        if root_unbuildable:
            continue

        # ---- CD-STALE-NODES-004 — IT QUANTIFIES OVER NODES, NOT OVER DIAL SLOTS ------ #
        # Every position here is one a slot-reading implementation cannot see. The paired
        # FRESH arm is what stops this becoming "refuse anything that is not a dial".
        first_slot = slots[0]
        positions = [
            (
                "NON-DIAL-ROOT-PROPERTY",
                lambda doc, node: doc.__setitem__(NON_DIAL_ROOT, node),
                f"/{NON_DIAL_ROOT}",
            ),
            (
                "TWO-CONTAINERS-DEEP-IN-AN-ARRAY",
                lambda doc, node: doc.__setitem__(NON_DIAL_ROOT, [[node]]),
                f"/{NON_DIAL_ROOT}/0/0",
            ),
            (
                "INSIDE-A-DIAL-S-OWN-ARRAY",
                lambda doc, node: doc[first_slot].__setitem__("contributions", [node]),
                f"/{first_slot}/contributions/0",
            ),
        ]
        for position_label, place, expected_pointer in positions:
            for arm_label, stamp, expectation in (
                ("STALE", STAMP_ANCIENT, MUST_REFUSE),
                ("FRESH", STAMP_FRESH, MUST_ADMIT),
            ):
                document = copy.deepcopy(base_document)
                place(document, {"detail_level": CALM, "planted_utc": stamp})
                label = f"{surface.value}/LIMB-B/{position_label}/{arm_label}"
                check.asserted()
                outcome = stage_outcome(surface, document)
                if expectation is MUST_ADMIT:
                    if outcome is None:
                        check.note(f"{label}: NOT REFUSED (correct — the node is fresh)")
                    else:
                        check.violation(
                            here, 0, "CD-STALE-NODES-004",
                            f"{label}: *** THE VACUOUS DIRECTION. *** A calm node at "
                            f"{expected_pointer} carrying a FRESH stamp was REFUSED "
                            f"({outcome!r}). The stage must refuse the STALE calm node and "
                            "nothing else; a stage that refuses a fresh one wherever it sits "
                            "is refusing position rather than age.",
                        )
                    continue
                if outcome is None:
                    check.violation(
                        here, 0, "CD-STALE-NODES-004",
                        f"{label}: *** A CALM-BEARING NODE AT {expected_pointer} CARRYING A "
                        "FIFTY-SIX-YEAR-OLD STAMP WAS NOT REFUSED. *** The stage must "
                        "quantify over NODES and never over the dial slots that happen to "
                        "exist today: 'does this node claim calm, and can it prove it earned "
                        "it?' — not 'is this one of the dials I know about?'. An "
                        "implementation that reads `candidate[\"equity_crash\"]` is silent on "
                        "the third slot a contract edit adds tomorrow, and that recogniser-"
                        "over-an-open-set is the defect class that lost eleven consecutive "
                        "audit rounds on this row. This is arm D3 of plants/WO3-INC16E/.",
                    )
                    continue
                if not isinstance(outcome, PublicationRefused):
                    check.violation(
                        here, 0, "CD-STALE-NODES-004",
                        f"{label}: the stage raised {type(outcome).__name__} and not "
                        f"PublicationRefused: {outcome!r} (CD-PL-F74).",
                    )
                    continue
                if (outcome.reason_class != REFUSAL_STALE_CALM
                        or outcome.pointer != expected_pointer):
                    check.violation(
                        here, 0, "CD-STALE-NODES-004",
                        f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer!r}, "
                        f"and this row requires {REFUSAL_STALE_CALM!r} at "
                        f"{expected_pointer!r}. The refusal must name the node that could not "
                        "prove its freshness, or a reader cannot act on it.",
                    )
                    continue
                check.note(f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer}")

        # ---- CD-STALE-OLDEST-005 — THE OLDEST STAMP GOVERNS -------------------------- #
        # Value-detection of stamps is only safe in the direction that matters BECAUSE the
        # oldest governs: adding a fresh-looking string to a node can never rescue it.
        oldest_arms = (
            (
                "STALE-BESIDE-TWO-FRESHER-SIBLINGS",
                {"detail_level": CALM, "a_planted_utc": STAMP_ANCIENT,
                 "b_planted_utc": STAMP_SECOND_FRESH, "c_planted_utc": STAMP_THIRD_FRESH},
                MUST_REFUSE, "a_planted_utc",
            ),
            (
                "ALL-THREE-STAMPS-FRESH",
                {"detail_level": CALM, "a_planted_utc": STAMP_FRESH,
                 "b_planted_utc": STAMP_SECOND_FRESH, "c_planted_utc": STAMP_THIRD_FRESH},
                MUST_ADMIT, None,
            ),
        )
        for arm_label, node, expectation, oldest_key in oldest_arms:
            document = copy.deepcopy(base_document)
            document[NON_DIAL_ROOT] = copy.deepcopy(node)
            label = f"{surface.value}/LIMB-B/OLDEST-GOVERNS/{arm_label}"
            check.asserted()
            outcome = stage_outcome(surface, document)
            if expectation is MUST_ADMIT:
                if outcome is None:
                    check.note(f"{label}: NOT REFUSED (correct — every stamp is fresh)")
                else:
                    check.violation(
                        here, 0, "CD-STALE-OLDEST-005",
                        f"{label}: *** THE VACUOUS DIRECTION. *** A calm node whose stamps are "
                        f"ALL fresh was REFUSED ({outcome!r}). 'The oldest governs' must not "
                        "degenerate into 'more than one stamp is suspicious'.",
                    )
                continue
            if not isinstance(outcome, PublicationRefused):
                check.violation(
                    here, 0, "CD-STALE-OLDEST-005",
                    f"{label}: *** A CALM NODE WHOSE OLDEST STAMP IS FIFTY-SIX YEARS OLD WAS "
                    f"NOT REFUSED ({outcome!r}). *** Two fresher siblings rescued it, so the "
                    "NEWEST stamp is governing. A node is only as fresh as its OLDEST readable "
                    "stamp — the envelope's own declared doctrine, 'as fresh as its oldest "
                    "input, never as fresh as the last time we asked'. If the newest governs, "
                    "adding one fresh-looking string to a stale node launders it, and stamps "
                    "are detected BY VALUE. This is arm D4 of plants/WO3-INC16E/.",
                )
                continue
            if outcome.key != oldest_key:
                check.violation(
                    here, 0, "CD-STALE-OLDEST-005",
                    f"{label}: REFUSED, but the refusal names key {outcome.key!r} and the "
                    f"OLDEST stamp on that node is {oldest_key!r}. The refusal must name the "
                    "stamp that governed, or the reader cannot tell WHICH stamp made the node "
                    "stale — and a refusal that names a fresher stamp is the newest-governs "
                    "bug reporting itself as the oldest-governs rule.",
                )
                continue
            check.note(
                f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer} naming the "
                f"OLDEST key {outcome.key!r}"
            )

        # ---- CD-STALE-CLOSED-006 — FAIL CLOSED AT EVERY BRANCH ----------------------- #
        # "Where a check cannot reach its authentic target it must fail, never wave through"
        # (Standards Baseline §16, PBG-CI-002). There is no "cannot tell, so allow" branch in
        # this stage, and this assertion is what stops one being added.
        closed_arms = [
            ("NO-STAMP-AT-ALL", {"detail_level": CALM}, WINDOW_SECONDS, PUBLISHED),
            (
                "A-PROPERTY-THAT-ANNOUNCES-ITSELF-AS-A-STAMP-AND-DOES-NOT-PARSE",
                {"detail_level": CALM, "planted_utc": STAMP_FRESH, "broken_utc": NOT_A_STAMP},
                WINDOW_SECONDS, PUBLISHED,
            ),
        ]
        for window_label, window_value in UNUSABLE_WINDOWS:
            closed_arms.append((
                f"WINDOW-{window_label}",
                {"detail_level": CALM, "planted_utc": STAMP_FRESH},
                window_value, PUBLISHED,
            ))
        for published_label, published_value in UNUSABLE_PUBLISHED:
            closed_arms.append((
                f"PUBLISHED-{published_label}",
                {"detail_level": CALM, "planted_utc": STAMP_FRESH},
                WINDOW_SECONDS, published_value,
            ))
        for arm_label, node, window_value, published_value in closed_arms:
            document, unbuildable_root = build_root(
                surface, dials, window=window_value, published=published_value
            )
            if unbuildable_root:
                continue
            if isinstance(window_value, float) and math.isnan(window_value):
                document["staleness_window_seconds"] = window_value
            document[NON_DIAL_ROOT] = copy.deepcopy(node)
            label = f"{surface.value}/LIMB-B/FAIL-CLOSED/{arm_label}"
            check.asserted()
            outcome = stage_outcome(surface, document)
            if isinstance(outcome, PublicationRefused) \
                    and outcome.reason_class == REFUSAL_STALE_CALM:
                check.note(
                    f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer} "
                    f"key {outcome.key!r}"
                )
                continue
            check.violation(
                here, 0, "CD-STALE-CLOSED-006",
                f"{label}: this arm removes the stage's ability to compute an age and the "
                f"stage did NOT refuse — it returned {outcome!r}. A node whose age CANNOT be "
                "computed has not proved it is fresh, and an unprovable freshness claim is "
                "REFUSED rather than assumed. There is no 'cannot tell, so allow' branch in "
                "this stage and this assertion exists so one cannot be added quietly "
                "(PBG-CI-002, Standards Baseline §16).",
            )

        # ---- CD-STALE-CLOSED-006, THE PAIRED NON-VACUITY ----------------------------- #
        document, unbuildable_root = build_root(surface, dials)
        if not unbuildable_root:
            document[NON_DIAL_ROOT] = {"detail_level": CALM, "planted_utc": STAMP_FRESH}
            label = f"{surface.value}/LIMB-B/FAIL-CLOSED/USABLE-WINDOW-AND-FRESH-NODE"
            check.asserted()
            outcome = stage_outcome(surface, document)
            if outcome is None:
                check.note(f"{label}: NOT REFUSED (correct — the arms above are not vacuous)")
            else:
                check.violation(
                    here, 0, "CD-STALE-CLOSED-006",
                    f"{label}: *** THE VACUOUS DIRECTION. *** With a real, finite, positive "
                    "window, a readable published_utc and a FRESH stamp, the stage still "
                    f"refused ({outcome!r}). Every fail-closed arm above is then satisfied by "
                    "a stage that refuses unconditionally, which detects nothing.",
                )

        # ---- CD-STALE-SCOPE-009 — THE DECLARED SCOPE, DRIVEN RATHER THAN ASSERTED ---- #
        # DECLARED LIMIT 8. The gate proves INTERNAL COHERENCE and never ACTUAL freshness, and
        # this row states that as its declared scope. A limit stated in prose goes stale in the
        # reassuring direction; this one is MEASURED at every run, so the day the product
        # closes the class this assertion goes RED and somebody must come and rewrite the
        # limit rather than discover it is obsolete.
        shifted_dial, unbuildable_shift = build_dial(surface, CALM, STAMP_ANCIENT)
        if not unbuildable_shift:
            shifted_dials = {slot: copy.deepcopy(shifted_dial) for slot in slots}
            shifted, unbuildable_root = build_root(
                surface, shifted_dials, window=WINDOW_SECONDS, published=STAMP_ANCIENT
            )
            if not unbuildable_root:
                shifted["as_of_utc"] = STAMP_ANCIENT
                label = f"{surface.value}/DECLARED-SCOPE/UNIFORMLY-TIME-SHIFTED-ENVELOPE"
                check.asserted()
                outcome = verdict(surface, shifted)
                if outcome is None:
                    check.note(
                        f"{label}: ADMITTED — and that is the DECLARED SCOPE of this guard, "
                        "measured rather than asserted. The gate enforces DOCUMENT-INTERNAL "
                        "freshness (published_utc minus the node's oldest stamp against the "
                        "declared window) and CANNOT catch a source that consistently LIES "
                        "about its own stamp. SOURCE HONESTY IS THE DETECTION TIER — witness "
                        "divergence + provenance, CD-AC-018 — ENFORCED ONE TIER OUT AND OWED "
                        "AT WO-3 (PO-DECISIONS-0030 ruling 2). It is NOT unenforceable."
                    )
                else:
                    check.violation(
                        here, 0, "CD-STALE-SCOPE-009",
                        f"{label}: this row's DECLARED SCOPE says a uniformly time-shifted "
                        "envelope — every stamp AND published_utc moved together — is ADMITTED, "
                        "because a document-internal comparison cannot see it. The gate "
                        f"REFUSED it instead ({outcome!r}). Either the product has closed that "
                        "class, in which case DECLARED LIMIT 8 is now FALSE and must be "
                        "rewritten in all three CD-RULE-004 places rather than left to go "
                        "stale in the reassuring direction; or something else refused this "
                        "document and the limit is being proved by the wrong layer (CD-PL-F74).",
                    )

    check.note(
        "DECLARED LIMIT, PRINTED AT EVERY RUN: this check drives the STALE half of CD-AC-001 "
        "only. It says nothing about MISSING data — that is the sibling row "
        "CD-RT-001-MISSING-DATA-NEVER-CALM and its RULE CC — nothing about a fabricated VALUE "
        "reading that should have been an absence, and it does not prevent $CD_CONTRACTS_DIR "
        "being pointed at a widened copy of the contracts: it refuses to run when it is. It is "
        "ONE OF FOUR guards on CD-AC-001 and never a sole guard."
    )
    check.note(
        "AND THE DECLARED SCOPE, PRINTED AT EVERY RUN (PO-DECISIONS-0030 ruling 2): the gate "
        "enforces DOCUMENT-INTERNAL freshness — published_utc minus a calm-bearing node's "
        "oldest stamp, against the window the same document declares. IT CANNOT CATCH A SOURCE "
        "THAT CONSISTENTLY LIES ABOUT ITS OWN STAMP: a feed that stamps every reading with the "
        "current instant regardless of the true age of the data is internally consistent and "
        "PASSES. THAT IS NOT RECORDED AS UNENFORCEABLE. It is the same class as the A311-F1 "
        "forgery and it has the same answer in the three-tier perimeter (PO-DECISIONS-0018/"
        "0019, BLUEPRINT §17 CD-BP-005): the gate is PREVENTION of what is document-internal; "
        "a lying source is caught by DETECTION — witness divergence + provenance, CD-AC-018 — "
        "ENFORCED ONE TIER OUT AND OWED AT WO-3, when real sources and their witnesses land. "
        "16C's detector-side liveness marking carries the resulting HONESTY OBLIGATION: stamps "
        "are PROVENANCE-BACKED and WITNESS-CORROBORATABLE. 16C IS NOT BUILT HERE."
    )

    return check.done(
        f"{cells} gate cells driven in-process through refuse_unless_publishable against "
        f"{package_dir} ({len(list(EnvelopeSurface))} surfaces x canonical dial slots x "
        f"{len(gate_table)} stamp rows), plus the fourth refusal stage driven directly at "
        "three calm-bearing positions the closed contract makes unreachable through the front "
        "door, the oldest-governs arms, the fail-closed arms and the declared-scope arm"
    )


if __name__ == "__main__":
    raise SystemExit(main())
