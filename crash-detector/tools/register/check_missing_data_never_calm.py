#!/usr/bin/env python3
"""CD-RT-001-MISSING-DATA-NEVER-CALM — the LIVE GATE refuses a calm missing-data dial.

    python3 tools/register/check_missing_data_never_calm.py --root <subject tree>

CRITERION: `CD-AC-001` — *"Missing or stale input never renders as calm."* — and `PID §3.2`,
which is CONSTITUTIONAL in the same words. Authority: `PO-DECISIONS-0026` **ruling 9**:

    "The calm-over-unknown refusal currently holds only in `tests/`, and `tests/` do not feed
     the gate — a register-wired instrument PASSES identically on a tree where the fix is
     fully reverted. ... the guarantee must be carried by a live instrument, not a memorial
     in tests."

===========================================================================================
**WHY THIS INSTRUMENT EXISTS, IN ONE PARAGRAPH.** WO-3 increment 16A-FIX narrowed the
`DEGRADED` and `UNKNOWN` branches of both envelope contracts to `#/$defs/absent_data_detail_level`,
which does not contain `calm`. That closed a RED (`CD-ASR-WO3-03`) and an independent seat
proved it behaviourally. **But nothing the register reads would have noticed if it were
undone.** Reproduced by the Project Lead at increment 16B's dispatch: on a tree with all four
`$ref`s restored to `#/$defs/detail_level`, **every runnable register instrument still exits
0**, and the only failures anywhere are nine tests in `tests/test_detail_level.py` — a file no
register `execute:` line names. A memorial, not a guard. This file is the guard.
===========================================================================================

**IT IS BEHAVIOURAL AND NOT STRUCTURAL, AND THAT IS THE WHOLE DESIGN.** It does not read the
schemas as documents, does not look for the string `absent_data_detail_level`, and does not
assert that any `$ref` points anywhere. It builds candidate envelopes and puts them through
`crash_detector.publication.envelope_contract.refuse_unless_publishable` — **the function the
product itself calls before it writes anything** (`src/crash_detector/publication/publish.py`
lines 276-277) — and records what the gate actually did. A structural read of schema keys is
precisely what let this class of defect through three times on this project (`CD-PL-F169`,
`CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`): a check that reads the `$ref` TARGET NAME and never
opens the target passes a tree where `calm` has been put back inside the target's own enum.

Register instruments on this project ARE permitted to import the application — MEASURED, four
already do: `check_exact_type_admission`, `check_engine_no_witness_reach`,
`check_no_numeric_default`, `check_judgement_path_doors`. (`CD-RT-014`'s "the probe must not
import the application" rule binds `tools/probe/external_probe.py` and nothing else: an
EXTERNAL probe must be external. It does not bind a register check.)

===========================================================================================
WHAT IS ASSERTED — AND THE ADMITTING ROWS MATTER AS MUCH AS THE REFUSING ONES
===========================================================================================

The proposition, on **both** surfaces and at **both** dial slots:

    UNKNOWN  dial · detail_level "calm"      ->  MUST REFUSE
    DEGRADED dial · detail_level "calm"      ->  MUST REFUSE
    UNKNOWN  dial · detail_level "elevated"  ->  MUST ADMIT
    UNKNOWN  dial · detail_level "acute"     ->  MUST ADMIT
    DEGRADED dial · detail_level "elevated"  ->  MUST ADMIT
    DEGRADED dial · detail_level "acute"     ->  MUST ADMIT
    VALUE    dial · detail_level "calm"      ->  MUST ADMIT   *** THE VACUITY ARM ***
    VALUE    dial · detail_level "elevated"  ->  MUST ADMIT
    VALUE    dial · detail_level "acute"     ->  MUST ADMIT

*** **THE `MUST ADMIT` ROWS ARE NOT DECORATION.** An instrument that only checked "calm is
refused on an UNKNOWN dial" is satisfied by a contract that refuses everything, and — the case
this project's history says gets missed — by a contract in which NO dial can ever read `calm`
at all, on any branch. `calm` on a real number backed by real inputs is the entire reason
`calm` exists (PID §4: *"calm = dial + one line"*). A guard that cannot tell "the forbidden
thing is impossible" from "everything is impossible" is not guarding PID §3.2, it is enforcing
silence. **`CD-CALM-VACUITY-000` below asserts that this file's own expectation table still
contains the VALUE/calm admitting row**, so the vacuity arm cannot be quietly deleted from the
instrument that exists to carry it. ***

 CD-CALM-VACUITY-000  **THE INSTRUMENT'S OWN TABLE IS NOT DEGENERATE.** The table must contain
                      at least one `MUST REFUSE` row and at least one `MUST ADMIT` row whose
                      level is `calm` (the VALUE/calm row). A table of all-refusals would make
                      every arm below satisfiable by a contract that publishes nothing.

 CD-CALM-GATE-001     **THE GATE REFUSED, WHERE IT MUST REFUSE.** `refuse_unless_publishable`
                      raised `PublicationRefused` for a `calm` on an absent-data branch.

 CD-CALM-GATE-002     **THE GATE ADMITTED, WHERE IT MUST ADMIT.** It returned `None`. An
                      envelope this product must be able to publish is still publishable.

 CD-CALM-REASON-003   **AND IT REFUSED FOR THE RIGHT REASON, AT THE RIGHT PLACE.** The refusal
                      is `SCHEMA_VIOLATION` and its JSON pointer names the dial slot that was
                      mutated. *"The right outcome from the wrong layer"* is this project's
                      most-repeated defect (`CD-PL-F74`): an envelope refused because it was
                      malformed somewhere else would satisfy a weaker check while proving
                      nothing at all about `calm`.

 CD-CALM-PAIRED-004   **AND THE REFUSAL IS CAUSED BY THE LEVEL AND BY NOTHING ELSE.** For every
                      refusing row the instrument diffs the refused candidate against the
                      ADMITTED candidate of the same state at the same slot on the same
                      surface, and asserts they differ at EXACTLY ONE JSON pointer, which is
                      `/<slot>/detail_level`. Same document, one token moved, opposite outcome.
                      This is what makes CD-CALM-GATE-001 a measurement rather than a hope.

 CD-CALM-PRODUCER-005 **AND THE PRODUCT CANNOT EVEN FORM THE INTENT.** `DetailPolicy` refuses
                      construction with `absent_data_level="calm"` (`DetailPolicyIncoherent`),
                      admits `elevated` and `acute`, and `detail_level_for` returns the policy's
                      absent level — never `calm` — for an `Unknown` reading. The contract half
                      above is what the gate refuses to ACCEPT; this half is what the product
                      refuses to PRODUCE. Both arms, refusing and admitting.

===========================================================================================
DECLARED LIMITS — CD-RULE-004, IN THE FIRST SCREEN, AND SAID THE SAME WAY IN THE REGISTER
ENTRY (`required-tests.yaml`) AND IN THE EXECUTION CONTRACT
(`contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`). A REGISTER ENTRY MAY NOT CLAIM
MORE THAN ITS GUARD DELIVERS.
===========================================================================================

 1  **IT JUDGES THE CONTRACT THE GATE ACTUALLY LOADS, WHICH IS CONFIGURABLE.**
    `envelope_contract.contracts_dir()` honours `$CD_CONTRACTS_DIR`, so the live gate can be
    pointed at contracts that are not the repository's while the repository's are intact.
    **THIS IS A REAL ROUTE AND IT IS THE ONE THIS INSTRUMENT'S C5 ARM DEMONSTRATES.**
    EXECUTABLE EXAMPLE:
      mkdir /tmp/widened && cp contracts/*.json /tmp/widened/
      python3 - <<'X'  # widen the UNKNOWN branch in /tmp/widened only
      import json;p='/tmp/widened/public_envelope.schema.json';d=json.load(open(p))
      d['$defs']['dial_reading_unknown']['properties']['detail_level']={'$ref':'#/$defs/detail_level'}
      json.dump(d,open(p,'w'))
      X
      CD_CONTRACTS_DIR=/tmp/widened python3 -c "..."   # the gate ADMITS a calm UNKNOWN dial
    **WHAT THIS CHECK DOES ABOUT IT:** it refuses (exit 3) unless the contracts the gate
    resolves are `<root>/contracts`, and it PRINTS the resolved paths and their SHA-256 at
    every run (`CD-PL-F98` — read the tree line every time; a contrast run against the wrong
    tree is indistinguishable from a fix that does nothing). **IT DOES NOT PREVENT THE ROUTE.**
    A deployment that sets `$CD_CONTRACTS_DIR` to a widened copy is refused by NOTHING in this
    repository, and that is **NOT PROVED TO BE CARRIED ANYWHERE.**
 2  **IT PROVES NOTHING ABOUT A `VALUE` READING THAT SHOULD NOT HAVE BEEN A `VALUE`.** The
    whole subject here is a dial that DECLARES its data absent. A dial whose inputs were
    missing but which was constructed as `VALUE` with a fabricated `score` renders `calm`
    legitimately as far as this contract is concerned, and this check admits it — row
    `VALUE/calm` above says so out loud. THE CARRIER IS THE SIBLING ENTRY: that class is
    `CD-RT-001-AST-NO-NUMERIC-DEFAULT` (provenance of the magnitude) together with
    `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` (the runtime post-condition
    `refuse_a_number_without_its_inputs`). **THIS CHECK IS ONE OF THREE GUARDS ON CD-AC-001
    AND NEVER A SOLE GUARD.**
 3  **IT SAYS NOTHING ABOUT STALENESS.** `CD-AC-001`'s words are *"missing OR STALE"*. This
    instrument drives the ABSENCE half only. Nothing here reads `staleness_window_seconds`,
    `as_of_utc` age, or any liveness/relevance quantity. The stale half is `CD-AC-009`
    (`CD-RT-009-REGIME-AWARE-STALENESS`) and, as a product model, is `PO-DECISIONS-0026`
    ruling 5, which is a LATER increment and is not evidenced here.
 4  **IT IS NOT A CENSUS OF SURFACES.** It drives the two envelope surfaces that
    `EnvelopeSurface` declares, at the two dial slots the contracts declare, ENUMERATED FROM
    THE APPLICATION (`EnvelopeSurface`, and the dial slots read from the contract's own
    `properties`) rather than typed in — so a third surface or a third dial added tomorrow is
    driven on the day it is added. But a rendering path that does not go through
    `refuse_unless_publishable` at all is outside it. MEASURED at this commit: the only callers
    of `refuse_unless_publishable` in `src/` are `publication/publish.py` lines 276-277, and
    they call it on BOTH surfaces before any write. A future serving layer that renders a dial
    without publishing an envelope is **NOT PROVED TO BE CARRIED ANYWHERE** — the rendering
    layer is later WO work.
 5  **IT IMPORTS THE SUBJECT TREE AND THEREFORE INHERITS IT.** It is a runtime check because
    *"refused"* is a runtime claim and every escape on this project's record passed a static
    checker. The cost is `--root`'s honesty: it prints the resolved `crash_detector.__file__`
    it imported and the SHA-256 of both contracts it judged.
 6  **IT NEEDS `jsonschema`**, because the gate does. Unlike the stdlib-only static checks in
    this directory it cannot run in an environment where the application's own runtime
    dependencies are absent. If `jsonschema` is missing it exits 3 with the reason — never a
    pass and never a skip (`PBG-CI-002`).

EXIT: 0 clean · 1 violation, with the cell and the observed outcome · 2 usage ·
3 precondition not met. Never a skip, for any reason (`PBG-CI-002`).
"""

from __future__ import annotations

import hashlib
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-001-MISSING-DATA-NEVER-CALM"

MUST_REFUSE = "MUST REFUSE"
MUST_ADMIT = "MUST ADMIT"

#: The prohibited level. PID §3.2, verbatim: "Missing data must never render as calm."
CALM = "calm"

#: The two absent-data states. UNKNOWN declares no score at all; DEGRADED carries a value AND
#: its damage with at least one named missing input. Those are exactly the missing-data states,
#: and they are exactly the two branches 16A-FIX narrowed.
ABSENT_STATES = ("UNKNOWN", "DEGRADED")

#: *** DELIBERATELY UNMISTAKABLE, AND NOT AN INGREDIENT. *** `Q25` holds the ingredient set with
#: the Product Authority and `CD-PL-F154` is what happens when a fixture escapes. The VALUE
#: branch requires `inputs_used` with `minItems: 1`, so this string exists only to satisfy that
#: cardinality inside this process. Nothing in this file constructs a `SourceRecord`, imports
#: `crash_detector.source_registry`, or emits a statement naming `raw.source_registry`. A grep
#: for this token lands here and nowhere near a registry.
SYNTHETIC_INPUT_ID = "SYNTHETIC-REGISTER-CHECK-NOT-A-SOURCE"

SYNTHETIC_CONFIG_SNAPSHOT_ID = "SYNTHETIC-REGISTER-CHECK-NOT-A-CONFIG"

AS_OF_UTC = "2026-08-23T12:00:00Z"
PUBLISHED_UTC = "2026-08-23T12:00:05Z"

#: The same instant as :data:`AS_OF_UTC`, PARSED FROM IT rather than written out a second time,
#: so the wire string a dial document carries and the ``datetime`` the producer arm's reading
#: carries cannot drift apart.
NOW = datetime.strptime(AS_OF_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

#: SYNTHETIC AND MEANINGLESS AS A NUMBER. The dial has no ratified scale (`Q25` holds it). It is
#: below any plausible calm boundary ON PURPOSE: an implementation that read the magnitude and
#: ignored the state would call this DEGRADED reading `calm`, which is the exact prohibited
#: rendering. Nothing here declares a threshold or a scale.
SYNTHETIC_SCORE = 0.01


def _dial(state: str, level: str) -> dict:
    """One dial reading in ``state`` carrying ``level``. Built as the wire document."""
    if state == "UNKNOWN":
        return {
            "state": "UNKNOWN",
            "reason": "NO_SOURCE_REGISTERED",
            "since_utc": AS_OF_UTC,
            "missing_inputs": [],
            "detail_level": level,
        }
    if state == "DEGRADED":
        return {
            "state": "DEGRADED",
            "score": SYNTHETIC_SCORE,
            "as_of_utc": AS_OF_UTC,
            "missing_inputs": [SYNTHETIC_INPUT_ID],
            "reason": "INPUT_MISSING",
            "contributions": [],
            "detail_level": level,
        }
    if state == "VALUE":
        return {
            "state": "VALUE",
            "score": SYNTHETIC_SCORE,
            "as_of_utc": AS_OF_UTC,
            "inputs_used": [SYNTHETIC_INPUT_ID],
            "contributions": [],
            "detail_level": level,
        }
    raise ValueError(f"no such dial state: {state!r}")


def _envelope(surface_value: str, slots: tuple, slot: str, state: str, level: str) -> dict:
    """A conforming envelope with ONE slot moved to ``state``/``level`` and nothing else.

    Every other slot is left at the shipped WO-2 state — UNKNOWN, `elevated` — so the ONLY
    thing that varies across the whole matrix is the one dial under test. That is what makes
    `CD-CALM-PAIRED-004`'s one-pointer diff possible.
    """
    envelope = {
        "schema_version": None,  # filled by the caller from the application's own constant
        "as_of_utc": AS_OF_UTC,
        "published_utc": PUBLISHED_UTC,
        "regime": "CALM",
        "staleness_window_seconds": 600.0,
        "inputs_used": [],
        "degraded_inputs": [],
        "config_snapshot_id": SYNTHETIC_CONFIG_SNAPSHOT_ID,
    }
    for name in slots:
        envelope[name] = _dial("UNKNOWN", "elevated")
    if surface_value == "private":
        envelope["classification"] = "PRIVATE"
    envelope[slot] = _dial(state, level)
    return envelope


def _pointers(node, pointer: str = "") -> dict:
    """Every LEAF of a JSON document, keyed by RFC 6901 pointer. Used only for the diff."""
    out: dict = {}
    if isinstance(node, dict):
        for key, value in node.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            out.update(_pointers(value, f"{pointer}/{token}"))
    elif isinstance(node, list):
        if not node:
            out[pointer] = "[]"
        for index, value in enumerate(node):
            out.update(_pointers(value, f"{pointer}/{index}"))
    else:
        out[pointer] = node
    return out


def _differing_pointers(left: dict, right: dict) -> list:
    a, b = _pointers(left), _pointers(right)
    return sorted(set(a) ^ set(b)) + sorted(k for k in set(a) & set(b) if a[k] != b[k])


def _expectations(levels: tuple) -> tuple:
    """The proposition table: ``(state, level, expectation)``, built from the FULL vocabulary.

    `levels` is read from the contract's own `#/$defs/detail_level` enum rather than typed in,
    so a fourth level added to the vocabulary is driven on the day it is added instead of being
    silently unexercised. The RULE is what is written here and it is written once:

      * an ABSENT-DATA state carrying `calm` MUST BE REFUSED;
      * everything else in the vocabulary MUST BE ADMITTED, including `calm` on a VALUE.
    """
    rows = []
    for state in ("VALUE",) + ABSENT_STATES:
        for level in levels:
            refuse = state in ABSENT_STATES and level == CALM
            rows.append((state, level, MUST_REFUSE if refuse else MUST_ADMIT))
    return tuple(rows)


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
        from crash_detector.dials.dialset import DIAL_IDS
        from crash_detector.dials.reading import Unknown
        from crash_detector.publication.detail_level import (
            DetailPolicy,
            DetailPolicyIncoherent,
            detail_level_for,
        )
        from crash_detector.publication.envelope_contract import (
            ENVELOPE_SCHEMA_VERSION,
            EnvelopeSurface,
            PublicationRefused,
            REFUSAL_SCHEMA_VIOLATION,
            contracts_dir,
            load_envelope_schema,
            refuse_unless_publishable,
            schema_path_for,
        )
    except Exception as exc:  # pragma: no cover - a tree that will not import
        return check.refuse(
            f"the subject tree at {src} did not import: {type(exc).__name__}: {exc}. If this "
            "is a missing `jsonschema`, that is DECLARED LIMIT 6: this check drives the live "
            "gate and the live gate validates with jsonschema."
        )

    package_dir = pathlib.Path(crash_detector.__file__).resolve().parent
    # CD-PL-F98 — READ THE TREE LINE EVERY TIME. A contrast run against the wrong tree is
    # indistinguishable from a fix that does nothing.
    check.note(f"imported crash_detector from: {package_dir / '__init__.py'}")
    check.note(f"python: {sys.version.split()[0]}")
    check.note(f"ENVELOPE_SCHEMA_VERSION as the application declares it: {ENVELOPE_SCHEMA_VERSION}")

    # ---- DECLARED LIMIT 1, ENFORCED AS A PRECONDITION -------------------------------- #
    # The gate reads $CD_CONTRACTS_DIR. If it resolves anywhere but the subject tree, this
    # check would be judging documents that are not the subject's, and its clean exit would be
    # a statement about somebody else's files. Non-zero with the reason; never a pass.
    resolved = contracts_dir().resolve()
    if resolved != (root / "contracts").resolve():
        return check.refuse(
            f"the live gate resolves its contracts to {resolved}, which is NOT "
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

    # ---- THE SUBJECT SET, ENUMERATED FROM THE APPLICATION AND THE CONTRACT ------------ #
    # Dial slots are the top-level properties that $ref the dial_reading union, read from the
    # contract itself. Typing them in would mean a third dial added tomorrow is never driven.
    slots_by_surface = {}
    for surface, schema in schemas.items():
        found = tuple(
            sorted(
                name
                for name, sub in (schema.get("properties") or {}).items()
                if isinstance(sub, dict) and sub.get("$ref") == "#/$defs/dial_reading"
            )
        )
        slots_by_surface[surface] = found
        check.note(f"{surface.value} dial slots enumerated from the contract: {list(found)}")
        if not found:
            return check.refuse(
                f"the {surface.value} contract declares no property referencing "
                "'#/$defs/dial_reading'. There is no dial to drive, so a clean exit would "
                "mean 'I looked at nothing'."
            )

    vocabulary = tuple((schemas[EnvelopeSurface.PUBLIC].get("$defs") or {})
                       .get("detail_level", {}).get("enum") or ())
    if not vocabulary:
        return check.refuse(
            "the public contract declares no '#/$defs/detail_level' enum, so this check "
            "cannot enumerate the vocabulary it must drive."
        )
    check.note(f"detail_level vocabulary enumerated from the contract: {list(vocabulary)}")

    table = _expectations(vocabulary)

    # ---- CD-CALM-VACUITY-000 — THE TABLE ITSELF IS NOT DEGENERATE -------------------- #
    here = pathlib.Path(__file__)
    check.asserted(2)
    if not any(expectation == MUST_REFUSE for _, _, expectation in table):
        check.violation(
            here, 0, "CD-CALM-VACUITY-000",
            "this check's own proposition table contains no MUST REFUSE row. It would then "
            "assert nothing about PID §3.2 at all.",
        )
    if not any(
        state == "VALUE" and level == CALM and expectation == MUST_ADMIT
        for state, level, expectation in table
    ):
        check.violation(
            here, 0, "CD-CALM-VACUITY-000",
            "*** THIS CHECK'S OWN VACUITY ARM IS GONE. *** The table no longer requires that a "
            "VALUE dial carrying 'calm' is ADMITTED, so every remaining arm would be satisfied "
            "by a contract in which no dial can ever read calm on any branch. That is not PID "
            "§3.2 held, it is silence enforced, and it is the failure mode this instrument was "
            "written to be incapable of.",
        )

    # ---- THE MATRIX ------------------------------------------------------------------- #
    admitted_reference: dict = {}
    cells = 0

    for surface in EnvelopeSurface:
        slots = slots_by_surface[surface]
        for slot in slots:
            for state, level, expectation in table:
                candidate = _envelope(surface.value, slots, slot, state, level)
                candidate["schema_version"] = ENVELOPE_SCHEMA_VERSION
                label = f"{surface.value}/{slot}/{state}/{level}"
                cells += 1

                check.asserted()
                try:
                    returned = refuse_unless_publishable(candidate, surface=surface)
                except PublicationRefused as refused:
                    if expectation is MUST_ADMIT:
                        check.violation(
                            here, 0, "CD-CALM-GATE-002",
                            f"{label}: {expectation} — but the gate REFUSED it "
                            f"[{refused.reason_class}] at {refused.pointer or '<root>'}. "
                            + (
                                "*** A VALUE dial backed by real inputs can no longer render "
                                "as calm. PID §4 makes calm the base case — 'calm = dial + one "
                                "line' — and a contract that cannot express it is not holding "
                                "PID §3.2, it is enforcing silence. ***"
                                if state == "VALUE" and level == CALM
                                else "This is a state the product must be able to publish. A "
                                "guard that refuses it has not closed a hole, it has closed "
                                "the product."
                            ),
                        )
                        continue
                    # It refused, as it must. Now: for the right reason, at the right place?
                    check.asserted(2)
                    if refused.reason_class != REFUSAL_SCHEMA_VIOLATION:
                        check.violation(
                            here, 0, "CD-CALM-REASON-003",
                            f"{label}: refused, but as {refused.reason_class} and not as "
                            f"{REFUSAL_SCHEMA_VIOLATION}. The right outcome from the wrong "
                            "layer is this project's most-repeated defect (CD-PL-F74): a "
                            "candidate refused for an unrelated malformation proves nothing "
                            "about calm.",
                        )
                    if refused.pointer != f"/{slot}":
                        check.violation(
                            here, 0, "CD-CALM-REASON-003",
                            f"{label}: refused at pointer {refused.pointer or '<root>'!r}, "
                            f"which does not name the mutated dial slot '/{slot}'. The "
                            "refusal is not located at the thing under test.",
                        )
                    check.note(
                        f"{label}: REFUSED [{refused.reason_class}] at "
                        f"{refused.pointer or '<root>'}"
                    )
                except Exception as other:
                    check.violation(
                        here, 0, "CD-CALM-REASON-003",
                        f"{label}: the gate raised {type(other).__name__}: "
                        f"{str(other).splitlines()[0][:160]}. That is neither an admission nor "
                        "a declared refusal. A refusal that arrives as a crash is not a "
                        "refusal, and a check cannot read it as one.",
                    )
                else:
                    if expectation is MUST_REFUSE:
                        check.violation(
                            here, 0, "CD-CALM-GATE-001",
                            f"{label}: *** THE LIVE GATE ADMITTED A {state} DIAL RENDERING AS "
                            "CALM. *** PID §3.2 is constitutional and its words are 'Missing "
                            "data must never render as calm'. With zero registered sources "
                            "every dial reads UNKNOWN, so this is not an edge case — it is the "
                            "only state this product can currently publish. "
                            f"refuse_unless_publishable returned {returned!r} and nothing "
                            "stopped the write.",
                        )
                        continue
                    admitted_reference[(surface, slot, state)] = candidate
                    check.note(f"{label}: ADMITTED")

    # ---- CD-CALM-PAIRED-004 — ONE TOKEN MOVED, OPPOSITE OUTCOME ---------------------- #
    # The refusal must be caused by the LEVEL. Diff each refused candidate against an ADMITTED
    # candidate of the SAME state at the SAME slot on the SAME surface and require exactly one
    # differing pointer, which must be the detail_level of that dial.
    for surface in EnvelopeSurface:
        for slot in slots_by_surface[surface]:
            for state, level, expectation in table:
                if expectation is not MUST_REFUSE:
                    continue
                reference = admitted_reference.get((surface, slot, state))
                label = f"{surface.value}/{slot}/{state}/{level}"
                check.asserted()
                if reference is None:
                    check.violation(
                        here, 0, "CD-CALM-PAIRED-004",
                        f"{label}: NO ADMITTED CANDIDATE of the same state exists to pair the "
                        "refusal against, so the refusal cannot be attributed to the level "
                        f"rather than to the {state} shape itself. If every {state} dial is "
                        "refused whatever it carries, this arm is vacuous — which is exactly "
                        "what this assertion exists to detect.",
                    )
                    continue
                refused_candidate = _envelope(surface.value, slots_by_surface[surface], slot,
                                              state, level)
                refused_candidate["schema_version"] = ENVELOPE_SCHEMA_VERSION
                differing = _differing_pointers(refused_candidate, reference)
                if differing != [f"/{slot}/detail_level"]:
                    check.violation(
                        here, 0, "CD-CALM-PAIRED-004",
                        f"{label}: the refused candidate and its admitted pair differ at "
                        f"{differing!r}, not at exactly ['/{slot}/detail_level']. The two "
                        "documents must be identical apart from the one token under test, or "
                        "the opposite outcomes cannot be attributed to it.",
                    )
                else:
                    check.note(
                        f"{label}: PAIRED against "
                        f"{reference[slot]['detail_level']!r} — sole difference "
                        f"/{slot}/detail_level"
                    )

    # ---- CD-CALM-PRODUCER-005 — THE PRODUCT CANNOT FORM THE INTENT EITHER ------------ #
    # The contract half above is what the gate refuses to ACCEPT. This is what the product
    # refuses to PRODUCE. Both arms, refusing and admitting, because a constructor that refused
    # every policy would be vacuous in the same way a contract that refuses everything is.
    check.asserted()
    try:
        policy = DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=CALM)
    except DetailPolicyIncoherent as refused:
        check.note(f"PRODUCER: DetailPolicy(absent_data_level='calm') REFUSED "
                   f"{type(refused).__name__}")
    except Exception as other:
        check.violation(
            here, 0, "CD-CALM-PRODUCER-005",
            f"DetailPolicy(absent_data_level='calm') raised {type(other).__name__} and not "
            "the declared DetailPolicyIncoherent (CD-PL-F74).",
        )
    else:
        check.violation(
            here, 0, "CD-CALM-PRODUCER-005",
            "DetailPolicy(absent_data_level='calm') was CONSTRUCTED. The product can now form "
            f"a policy that renders missing data as calm; it returned {policy!r}.",
        )

    absent_levels = tuple(level for level in vocabulary if level != CALM)
    if not absent_levels:
        return check.refuse(
            "the vocabulary contains no level other than 'calm', so the admitting arm of "
            "CD-CALM-PRODUCER-005 cannot be driven and this check would be vacuous."
        )
    for level in absent_levels:
        check.asserted(2)
        try:
            policy = DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=level)
        except Exception as exc:
            check.violation(
                here, 0, "CD-CALM-PRODUCER-005",
                f"DetailPolicy(absent_data_level={level!r}) was REFUSED "
                f"({type(exc).__name__}: {str(exc).splitlines()[0][:120]}). A constructor that "
                "refuses every policy is vacuous, and the product would have no level left to "
                "render an absence with.",
            )
            continue
        try:
            produced = detail_level_for(
                Unknown(reason="NO_SOURCE_REGISTERED", since_utc=NOW, missing_inputs=()),
                dial_slot=DIAL_IDS[0],
                policy=policy,
            )
        except Exception as exc:
            check.violation(
                here, 0, "CD-CALM-PRODUCER-005",
                f"detail_level_for(Unknown, policy.absent_data_level={level!r}) raised "
                f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}.",
            )
            continue
        if produced == CALM or produced != level:
            check.violation(
                here, 0, "CD-CALM-PRODUCER-005",
                f"detail_level_for(Unknown) returned {produced!r} for a policy whose "
                f"absent_data_level is {level!r}. The level an absence renders with must be "
                "the policy's absent level and must never be 'calm'.",
            )
        else:
            check.note(f"PRODUCER: detail_level_for(Unknown) -> {produced!r} (policy {level!r})")

    check.note(
        "DECLARED LIMIT, PRINTED AT EVERY RUN: this check drives the ABSENCE half of CD-AC-001 "
        "only. It says nothing about staleness, nothing about a fabricated VALUE that should "
        "have been an absence, and it does not prevent $CD_CONTRACTS_DIR being pointed at a "
        "widened copy of the contracts — it refuses to run when it is. It is ONE OF THREE "
        "guards on CD-AC-001 and never a sole guard."
    )

    return check.done(
        f"{cells} gate cells ({len(list(EnvelopeSurface))} surfaces x dial slots x "
        f"{len(table)} state/level rows) driven in-process through "
        f"refuse_unless_publishable against {package_dir}, plus the producer arms"
    )


if __name__ == "__main__":
    raise SystemExit(main())
