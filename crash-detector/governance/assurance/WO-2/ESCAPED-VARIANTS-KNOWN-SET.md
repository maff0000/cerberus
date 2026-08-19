# THE KNOWN SET — the ten variants that escaped at the WO-2 gate

**Compiled by:** PROJECT_LEAD_SEAT_01 from `governance/assurance/WO-2/BL-ASR-WO2-01.yaml`
(CD-ASR-WO2-01, AMBER, target `66681b2`). Compiled 2026-08-19.
**Nothing here is new information.** Every route below is transcribed from the auditor's own entry.
This file exists so that two different seats can be held to two different obligations against the
same list.

## What this list IS, for the WO-2R Engineer (`CD-ENG-WO2R-01`)

**Your minimum proof obligation.** For each finding you close, every escape below that belongs to it
must be **executed against your closure and shown to be refused** — refused by execution, not by a
grep exiting non-zero. These are *necessary* and *not sufficient*: the Product Owner's ruling also
requires **at least two new variants of your own** per finding, attacking the same class by a route
that is not on this list.

## What this list IS, for the WO-2R Assurance seat (`CD-ASR-WO2-02`)

**Your exclusion set.** These ten are now the Engineer's known set and **prove nothing about the
class**. A guard that refuses exactly these ten and nothing else has been fitted to a list. Your
variants must be **FRESH** — devised without reference to this list except to avoid duplicating it.
Re-running these is permitted as a regression check and is **not** evidence for any verdict.

## Counting, and one honest gap in the source record

The auditor ran **24** variants: 2 for CD-AC-001, 2 for CD-AC-002, 9 for CD-AC-003, 4 for CD-AC-005,
7 for CD-AC-012. **14 were caught. 10 escaped.** Of the ten, **8** are the substance of findings
CD-ASR-F01..F07 (F01 carries two variants) and **2** landed inside a boundary
`CD-RT-012-NO-EXECUTION-INTERFACE` had already declared in writing, and were judged fair.

**Only one of those two fair escapes is individually described in the source record** (E09 below).
The second is attested in aggregate — "the escapes in the source-scanning check all landed inside its
WRITTEN declared limit" — but is not itemised. It is recorded here as **E10, ROUTE NOT ITEMISED IN
THE SOURCE RECORD**, and is not fabricated into a specific route. This is a gap in the evidence
trail, not in the deliverable, and it is disclosed rather than smoothed over.

---

## E01 — CD-AC-002 / CD-ASR-F01 variant 1: inter-procedural fold via an allowlisted path

* **Target proposition:** no code path combines the two dials.
* **Route:** `src/crash_detector/serving/banner.py` defines
  `_fold(left: float, right: float) -> float: return (left + right) / 2.0` and
  `banner_figure(dials): return _fold(dials.equity.value.score, dials.monetary.value.score)`.
* **Why it escaped:** the call expression holds both dial markers but contains **no arithmetic**, so
  RULE 1 does not fire. The arithmetic sits one call away inside `_fold`, whose parameters are
  annotated `float` and carry no dial flavour. RULE 2 would have caught the co-occurrence, but
  `src/crash_detector/serving` **is allowlisted for RULE 2 by design**.
* **Observed:** `check_no_blend.py` exit 0 (1032 assertions); `test_scores.py` + `test_dialset.py`
  96 passed; `check_schema_closed.py` exit 0. **Then executed: returned 0.5 from equity 0.9 and
  monetary 0.1.**

## E02 — CD-AC-002 / CD-ASR-F01 variant 2: getattr over string slots, no allowlisted path needed

* **Route:** `src/crash_detector/publication/summary.py` defines `_SLOTS = ("equity", "monetary")`
  and `magnitudes = [getattr(dials, slot).value.score for slot in _SLOTS]`,
  `return sum(magnitudes) / len(magnitudes)`.
* **Why it escaped:** **no dial marker appears in any expression.** The slot names are plain strings;
  the check's marker set holds only `equity_crash` and `monetary_debasement`, so nothing is ever
  flavoured and no rule fires. Stronger than E01 because it needs no allowlisted path.
* **Observed:** same three guards green. **Then executed: returned the blended 0.5.**
* **Root cause (auditor's words):** flavour propagation is **intra-procedural** by design and purely
  **static**, so `getattr` with a non-marker string literal **erases the flavour entirely**.

## E03 — CD-AC-001 / CD-ASR-F02: a numeric attribute on `Unknown`

* **Target proposition:** absence never renders as a number.
* **Route:** add a plain property to the `Unknown` reading — `magnitude -> 0.0`. No dunder, no
  annotation, no default.
* **Why it escaped:** `tests/test_reading.py` checks only that no name from `ARITHMETIC_DUNDERS`
  appears in `vars(Unknown)`. **Nothing asserts that `Unknown`'s attribute surface is CLOSED**, so
  any non-dunder numeric member is invisible.
* **Observed:** `check_no_numeric_default.py` exit 0; `pytest tests/test_reading.py
  tests/test_evaluate.py` 49 passed, exit 0. **Then read back at runtime: `Unknown(...).magnitude`
  is `0.0`.** REPLICATED INDEPENDENTLY BY THE PROJECT LEAD.
* **In scope by the register's own words:** its `negative_control` for
  `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` names this route — "`Unknown` given any attribute or coercion
  that yields a float".

## E04 — CD-AC-001 / CD-ASR-F03: numeric default as a module-level constant

* **Route:** replace the `missing_required` branch of `_evaluate_dial` to return
  `Value(value=<ScoreType>(score=QUIET_MAGNITUDE, ...))` where `QUIET_MAGNITUDE = 0.0` is a
  module-level constant.
* **Why it escaped the AST guard:** no `float | None`, no `.get(key, 0)`, no `or 0`, no bare
  `except` — **none of the routes the check enumerates is present.** The check enumerates spellings.
* **Observed:** `check_no_numeric_default.py` exit 0, zero violations. A dial that did not get its
  inputs now reads `0.0` — the exact failure PID §3.2 forbids.
* **Partially contained:** CAUGHT by the criterion's *second* test (`pytest tests/test_reading.py
  tests/test_evaluate.py` exits 1, 9 failures). The finding is against the declared `scope: CLASS` of
  `CD-RT-001-AST-NO-NUMERIC-DEFAULT`, not against the criterion.

## E05 — CD-AC-012 / CD-ASR-F04: broker reachable by IP literal

* **Target proposition:** a broker host added to any container's egress allowlist is a violation.
* **Route:** add `198.51.100.24` to the `cd-collectors` egress allowlist **in place of a hostname**.
* **Why it escaped:** the check recognises brokers **by NAME**, and an IP literal has no name to
  recognise. The same slot carrying `api.ibkr.com` exits 1.
* **Observed:** `check_egress_no_broker.py` exit 0.
* **Not covered by any declared limit** — unlike `CD-RT-012-NO-EXECUTION-INTERFACE`, this check has
  no written boundary. **This is the whole of the CD-AC-012 AMBER.**

## E06 — CD-AC-003 / CD-ASR-F05: the engine container's own entrypoint is outside the walk root

* **Target proposition:** the engine container cannot reach witness data.
* **Route:** append `from crash_detector.witness.panel import Agrees` to
  `deploy/entrypoints/cd_engine.py` — **the module that IS the engine container's process.**
* **Why it escaped:** `check_engine_no_witness_reach.py` roots its walk at
  `src/crash_detector/engine/` and scans only `src/crash_detector/`. The guard's subject is the
  engine **PACKAGE**; the criterion's subject is the engine **CONTAINER**.
* **Observed:** exit 0.
* **Mitigation that does hold:** importing witness **types** is not reaching witness **data**. The
  live-catalogue arm proved cd_engine holds no privilege on schema `witness` by any of seven routes
  and that PostgreSQL refuses it in a real session.

## E07 — CD-AC-005 / CD-ASR-F06: an unbounded-above staleness window

* **Target proposition:** there is no input whatever — missing, stale, malformed or defaulted — from
  which the serving layer produces AGREES.
* **Route:** `staleness_window_seconds=1e18`, with a panel row **10 years old** and marked AGREES.
* **Why it escaped:** `_require_usable_window` refuses non-finite and non-positive windows and
  accepts **any finite positive number**.
* **Observed by direct execution:** resolves to `Agrees`, renders `WITNESS AGREES`. With a window of
  `60.0` the same row correctly resolves to `Unavailable` / `WITNESS UNAVAILABLE`. **Needs no source
  edit** — configuration alone.
* **To the deliverable's credit:** the docstring identifies the hazard — "no window and a very large
  window both mean nothing is ever stale". Infinity and zero were guarded; `1e18` was not. A
  half-closed door, not an unnoticed one.

## E08 — CD-AC-005 / CD-ASR-F07: an exception handler resolving to agreement

* **Route:** wrap the age computation in `try/except Exception: return Agrees(...)`.
* **Why it escaped:** undetected by `pytest tests/test_witness_panel.py
  tests/test_witness_resolver.py` (exit 0).
* **The auditor's own honest qualification, which must be carried forward:** **IT COULD NOT MAKE THE
  HANDLER FIRE.** `PanelRow.__post_init__` normalises `as_of_utc` through `ensure_utc`, so
  `age_seconds` does not raise on any constructible row. The planted handler is **dead code** and no
  behaviour changed, which is *why* the tests pass. A declared-class route is undetected; a live
  bypass was **not** demonstrated. Recorded LOW for that reason.
* **The register's own `negative_control` names "an exception handler" as part of the class.**

## E09 — CD-AC-012, JUDGED FAIR: order ticket outside the five scanned roots

* **Route:** an order ticket placed in `scripts/`.
* **Why it escaped:** it landed **squarely inside stated boundary 5** of
  `CD-RT-012-NO-EXECUTION-INTERFACE`, which names the five scanned roots and the two suffixes and
  says in terms that "an order interface delivered as a shell script, a compose command, a CI job or
  a dependency's own code is outside this check entirely".
* **Disposition:** **NOT A DEFECT.** The auditor examined whether the limit was honestly drawn and
  answered **YES — honestly drawn, and drawn conservatively.** No WO-2R work is owed against it.
* **Bounded further by an observation the declaration does not claim:** all six application
  Dockerfiles COPY exactly two paths, `src/` and `deploy/entrypoints/`, both inside the five scanned
  roots — so source outside them **cannot reach a shipped image**. The limit is smaller in practice
  than its text admits.

## E10 — CD-AC-012, JUDGED FAIR: ROUTE NOT ITEMISED IN THE SOURCE RECORD

* **What the record says:** the second fair escape is attested only in aggregate — the auditor states
  that "the escapes in the source-scanning check all landed inside its WRITTEN declared limit", and
  separately that the euphemism boundary (1) "is genuinely unbounded and always will be".
* **What is therefore known:** it was against `CD-RT-012-NO-EXECUTION-INTERFACE`, and it fell inside
  a written boundary of that check's declared limit.
* **What is NOT known:** the specific route, file and command.
* **Disposition:** **NO WO-2R WORK IS OWED against E10**, on the same reasoning as E09 — it is inside
  a declared limit the auditor judged honestly drawn. It is recorded because a count that does not
  reconcile is a defect in the evidence trail whether or not it is a defect in the code. **The
  WO-2R Assurance dispatch is asked to itemise it if its own probing rediscovers it.**

---

## Cross-reference: guards the auditor PROVED bite the class

Recorded so WO-2R does not "harden" something already proved, and so the Assurance re-dispatch knows
where the deliverable is strong. Fourteen variants were caught. Notably:

* **CD-AC-003 live catalogue, all seven routes** — role membership, grant to PUBLIC, default
  privilege, ownership, SUPERUSER, function privilege, and an UPDATE/DELETE probe. All caught, each
  named with its own route. The check also opens a real session as `cd_engine` and makes PostgreSQL
  itself refuse. **The strongest artefact in the deliverable.**
* **CD-AC-003 code graph, dynamic import** — `importlib.import_module("crash_detector" + ".witness" +
  ".panel")` caught, and caught **for the right reason**: the check fails closed on *any* dynamic
  import, literal or computed.
* **CD-AC-012 signature shape (L2)** — a wholly neutrally-named order ticket (`Item`,
  `enqueue(instrument, size, direction, limit, destination)`, module `dispatchq`, no execution
  vocabulary anywhere) caught **on its field set**. L2 genuinely reads no names.
* **CD-AC-012 lockfile token rule** — `quantum-order-router==0.3.1`, absent from the 61-name
  denylist, caught on its execution token. A named broker SDK in `requirements.lock` **alone** also
  caught (this **narrows** CD-PL-F43 — see CD-ASR-N01: the check *does* read `requirements.lock`;
  what is owed is the negative-control evidence, not the coverage).
* **CD-AC-012 egress, both halves** — a NON-broker egress host on `cd-engine`
  (`files.pythonhosted.org`) caught under CD-EGRESS-001.
* **CD-AC-005 rendering and malformed input** — mapping `Unavailable` to `WITNESS_AGREES_TEXT`
  caught; a reachable malformed row resolving to `Agrees(0.0)` caught.
* **CD-AC-001 behavioural backstop** — E03's route was caught by the criterion's **second** test.
  Two tests over one proposition earned their keep.

## Also carried forward to the WO-2R Assurance seat

**CD-ASR-N02 (LOW) — the live grant-matrix check is cluster-state dependent and does not declare it.**
PostgreSQL role attributes and memberships are **CLUSTER-wide, not database-scoped**. The first
auditor discovered this the hard way: a `GRANT cd_witness TO cd_engine` planted in one variant
persisted into every later variant on the same cluster and produced violations in trees that did not
carry it. It re-ran everything from a fully reset cluster and re-confirmed the clean baseline at 138
assertions / 0 violations before the re-runs, and discarded the contaminated results rather than
reporting them.

**It fails LOUD, not silent** — inherited state produces EXTRA violations, never a false clean — so
it is not a bypass. But **reset the cluster between variants**, or you will see violations that are
not in the tree.
