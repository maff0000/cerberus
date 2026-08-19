# Execution contract — CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES

**CD-AC-005** · WITNESS UNAVAILABLE is not WITNESS AGREES · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

An absent panel row and a panel row older than its staleness window both resolve to UNAVAILABLE, and no input resolves absence to AGREES — **including an input that is only a configured staleness window**.

## Command

```
PYTHONPATH=src python3 -m pytest tests/test_witness_panel.py tests/test_witness_resolver.py tests/test_staleness.py -q
```

`tests/test_staleness.py` joined the declared command when `CD-ASR-F06` was closed at
increment 5. The structure that carries the proposition now lives in a module of its own
(`src/crash_detector/staleness.py`), and a guard that does not run over its own subject is
not a guard.

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

`tests/test_witness_panel.py` proves the TYPE cannot express the confusion — `Unavailable` is a distinct constructor with no field a later edit could read as agreement, and `Agrees` cannot be constructed at all without the freshness evidence that justifies it. `tests/test_witness_resolver.py` proves the serving-layer RESOLVER maps the explicit absence, the silent one and the stale one onto UNAVAILABLE. `tests/test_staleness.py` proves the two invariants those rest on: no window above the derived ceiling can be constructed, and freshness evidence cannot be made for a stale or future-dated observation under any window that can be constructed.

## Why it is asserted this way

Three halves are needed, and the third was learned the expensive way.

A type that cannot express agreement-from-absence is worth nothing if the resolver defaults a missing row before the type ever sees it, and a resolver that maps absence correctly is worth nothing if the type has a field somebody can set. **And both are worth nothing if the window itself can be configured wide enough that nothing is ever stale**, which is exactly what `CD-ASR-F06` measured: `staleness_window_seconds=1e18` with a row ten years old, no source edit, `WITNESS AGREES`.

## What changed at increment 5, and why it is a class closure

The bounded window is the smaller half. The load-bearing half is that **`Agrees` now requires
`FreshnessEvidence`, and constructing that evidence *is* the age comparison** — the age is
derived inside the constructor from the observation's own timestamp, never accepted as an
argument, and the evidence is bound to the agreement's own `as_of_utc`. So agreement cannot
be reached by a route that never compares anything: an exception handler, a fallback branch,
a fast path, a default argument or a caller of a private helper all need the same value, and
the value cannot be made for a stale observation.

The admission door is shared with the dial path deliberately. `crash_detector.engine` performs
its own age comparison against the window in the `ConfigSnapshot`; both now admit through
`StalenessWindow` and `_latest_usable_ok` takes one rather than a float. Two guarded
comparison sites are an enumeration; one place a usable window can come into existence is a
closure.

### The ceiling is derived and was not chosen (`CD-RULE-003`)

`STALENESS_WINDOW_CEILING_SECONDS = 900.0`, from **`PID.md` §5**, the ratified property table,
marked *RATIFIED 2026-08-18 — CD-D-003 resolved*: "pipeline/publication failure independently
detectable ≤ **15 minutes**". A staleness window wider than the detectability budget renders a
dead feed as fresh for longer than the product permits a failure to go undetected.

**It is a ceiling and not an operating window.** A window of exactly 900 s consumes the whole
budget and leaves nothing for the detection and the alerting. The operating window is
`BLUEPRINT.md` §7, `CD-AC-009`, `window_for(regime) -> seconds`, **owed at WO-3**. No tighter
number is imposed here, because none is derivable from ratified text and choosing one that
looks prudent is the invention `CD-RULE-003` forbids.

**A window above the ceiling is refused, not clamped.** A clamped window is a wrong window that
looks like a right one — the same argument `ScoreOutOfRange` makes about clamped scores.

## Preconditions

* `python3` 3.11 or later with `pytest` available on the interpreter, and
  `jsonschema` for the modules that read the envelope contracts. Nothing else, and no
  install step.
* `PYTHONPATH=src` is part of the command line, not an environment the auditor is expected
  to have arranged. The package is importable from the source tree with no install.
* The working directory is the root of the subject tree the auditor extracted.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | every test in the named modules passed. |
| `1` | at least one test failed — the failing assertion and its module are named in the output. |
| `2` · `3` · `4` | interrupted, internal error, or usage/collection error. None of these is a pass, and none may be read as one. |

No test in these modules may skip. A conditional skip is a hole with a comment in it, and
a suite that can skip its way to green is not evidence.

## Declared limit (`CD-RULE-004`)

Stated identically here, in the header of `src/crash_detector/staleness.py`, and in
`required-tests.yaml`. Each hand-off names a layer that was **measured**, or says **NOT PROVED
TO BE CARRIED ANYWHERE** (`CD-RULE-006`).

1. **THE CEILING BOUNDS THE WINDOW; IT DOES NOT ESTABLISH WHAT THE WINDOW SHOULD BE.** Any
   window from `0.001` to `900.0` seconds is admissible, and a deployment configuring `899.0`
   has a window this guard does not question. The operating window is `BLUEPRINT` §7's
   `window_for(regime)`, **owed at WO-3** (`CD-AC-009`). **NOT PROVED TO BE CARRIED ANYWHERE**,
   and deliberately: deciding the operating window here would be inventing a product quantity.
2. **CLOCK TRUST IS NOT ESTABLISHED.** `FreshnessEvidence` judges an age against the
   `observed_at_utc` it is handed, and `now_utc` is an argument everywhere on the freshness path
   by design so a historical evaluation replays exactly (`BLUEPRINT` §7). **MEASURED:**
   `resolve_panel(row_dated_2016, now_utc=2016-08-21T12:00:10Z, staleness_window_seconds=600.0)`
   returns `Agrees` and renders `WITNESS AGREES`. **NOT PROVED TO BE CARRIED ANYWHERE.**
   Pre-existing and project-wide, not introduced by this closure.
3. **`object.__setattr__` WALKS PAST FROZEN**, here as on every frozen value in Python and in
   this repository.

   *Amended at increment 6, `CD-PL-F65` / `CD-D-058`, and the previous text is why.* This
   boundary read *"Both values use `__slots__`, so an undeclared attribute cannot be injected"*.
   That is **true of the two values it was written about** and it was **reassuring about a third
   value it never named**. Incomplete, not false — the `CD-PL-F62` shape, claiming no carrier
   that does not exist — and the correction is carried in the text rather than made silently
   (`PBG-CONT-003`).

   **The two slotted values.** `StalenessWindow` and `FreshnessEvidence` are both
   `@dataclass(frozen=True, slots=True)`, so an **undeclared** attribute cannot be injected —
   **MEASURED:** `object.__setattr__(window, "ceiling", 1e18)` raises `AttributeError:
   'StalenessWindow' object has no attribute 'ceiling'`, and so does `"smuggled"`. Overwriting a
   **declared** slot on an already-constructed value is not preventable at the Python level —
   **MEASURED:** `object.__setattr__(window, "seconds", 1e18)` sticks and `window.seconds` then
   reads `1e+18`; `object.__setattr__(evidence, "as_of_utc", <2016-08-21>)` makes its derived
   `age_seconds` read `315360000.0`.

   **`Agrees` is not one of them, and the `__slots__` half does not hold there.**
   `crash_detector.witness.panel.Agrees` is `@dataclass(frozen=True)` with **no** `slots=True`.
   It carries a `__dict__`, so on `Agrees` even the undeclared-attribute protection is **absent**
   — **MEASURED:** `object.__setattr__(agrees, "smuggled", 1e18)` **sticks** and
   `agrees.smuggled` reads `1e+18`, where the identical write on `StalenessWindow` raises. An
   auditor reading the old sentence would have carried the slotted guarantee across to the value
   that actually renders the panel, and it is not there.

   **And the route reaches the Product Owner's own forbidden sentence.** Stated plainly rather
   than left to be inferred from *"not preventable at the Python level"* — **MEASURED (`PL-W5`)**,
   on a *lawfully* constructed fresh `Agrees` followed by **one** post-construction write:

   ```python
   row = PanelRow(state="AGREES", as_of_utc=NOW, published_utc=NOW,
                  measures={"divergence_measure": 0.01})
   a = resolve_panel(row, now_utc=NOW, staleness_window_seconds=600.0)
   object.__setattr__(a, "as_of_utc", datetime(2016, 8, 21, 12, 0, tzinfo=utc))
   render_panel(a)          # -> 'WITNESS AGREES'
   ```

   That is **`WITNESS AGREES` on a decade-old timestamp**. `render_panel` dispatches on **type**
   and re-validates nothing, so once a value of type `Agrees` exists no later layer looks at it
   again. Carrying the forgery down into the evidence makes it internally consistent too —
   **MEASURED:** adding `object.__setattr__(a.freshness, "as_of_utc", <2016-08-21>)` and
   `object.__setattr__(a.freshness.window, "seconds", 1e18)` gives `a.freshness.age_seconds ==
   315360000.0` (3650 days), `a.freshness.window.covers(315360000.0) is True`, and
   `render_panel(a)` still `'WITNESS AGREES'`.

   **NOT PROVED TO BE CARRIED ANYWHERE.** No layer was measured refusing a forged `Agrees`.

   **The three routes that are refused, unchanged:** the decade-old row itself resolves to
   `Unavailable` / `WITNESS UNAVAILABLE`; `StalenessWindow(seconds=1e18)` raises
   `StalenessWindowOutOfRange`; `Agrees(...)` built with evidence for a different instant raises
   `AgreementWithoutFreshnessEvidence`. The `object.__setattr__` residue is available only to
   code that has already chosen to write past the language's own frozen guarantee. It is the same
   residue declared as boundary B of `src/crash_detector/dials/magnitude.py`; it is a property of
   the language, not of this design.

   **What this boundary is not — CORRECTED AT WO-2R2 INCREMENT 2, and the previous text is why.**
   It read:

   > *"it is not a route from ordinary input, and every route measured that goes through a
   > CONSTRUCTOR is refused. **Three measured, and three is the denominator, not a proof that a
   > fourth does not exist**"*

   **THE FOURTH EXISTED.** `CD-ASR-WO2-02` found it: variant `ASR2-005-A`, a `datetime` subclass
   overriding `__rsub__` and `astimezone`, which goes through **every** constructor on the path —
   `PanelRow.__post_init__`, `resolve_panel`, `StalenessWindow.__post_init__`,
   `FreshnessEvidence.__post_init__` — and reaches `Agrees`. A row dated 2016-08-21 read at
   2026-08-19 with a 600 s window rendered `WITNESS AGREES` while this very test exited `0` with
   152 passed. The hedge was honest and it did its job; what it could not do was say what the
   denominator **was**. The old sentence is quoted rather than removed (`PBG-CONT-003`).

   **THE DENOMINATOR IS NOW STATED, WITH THE METHOD BY WHICH IT WAS TAKEN.** The class was
   re-stated at the Product Owner's altitude — *any judgement this system makes that delegates its
   deciding operation to an object the system did not construct* — and swept mechanically rather
   than by reading the modules that looked relevant:

   * **Method.** Parse every module of `src/crash_detector`; compute the transitive intra-package
     **import closure** of the six modules that host a judgement about staleness, agreement or
     reading-ness; enumerate every AST node in that closure at which an operation could be
     executed by an object the module did not construct, in two tiers — *admission* (`isinstance`,
     `issubclass`, `hasattr`, `getattr`) and *the deciding operation* (comparison, membership,
     arithmetic, ordering calls, coercion calls, set operations, truthiness, identity). The
     closure is taken over **modules**, not functions, so it is over-inclusive by construction.
   * **Denominator: 16 subject modules, 402 sites.** Tier 1 — 30 distinct sites, 33 occurrences
     (`ISINSTANCE` 24, `ISSUBCLASS` 0, `DUCK` 9). Tier 2 — 369 occurrences (`TRUTHINESS` 103,
     `COERCION` 101, `IDENTITY` 47, `COMPARE` 36, `ORDERING` 30, `MEMBERSHIP` 26, `ARITH` 18,
     `SETOP` 8). Every tier-1 site carries a written disposition and every subject module carries
     one for tier 2, asserted **by set equality in both directions**.

   **EXECUTABLE EXAMPLE**, from the root of a tree the auditor extracted itself:

   ```
   python3 -B tools/sweep/delegated_judgement_sweep.py --root . --list
       -> exit 0, "402 sites enumerated over 16 modules"
   cp <ASR2-005-A> src/crash_detector/serving/panel_feed.py   # then its driver
       -> Unavailable(reason='PANEL_ROW_STALE') -> 'WITNESS UNAVAILABLE'
       -> and the plain-datetime CONTROL arm renders the SAME string
   ```

   **CARRIER MEASURED (`CD-RULE-006`).** `crash_detector.own_terms`, measured refusing the variant
   on pristine extractions rather than nominated: at `50fc231` `ASR2-005-A` renders `WITNESS
   AGREES` while its control renders `WITNESS UNAVAILABLE`; at the closure **both arms render
   `WITNESS UNAVAILABLE`**, and the auditor's finding *was* that divergence. A counterfactual
   extraction with one line changed — the descriptor read replaced by `getattr` — renders `WITNESS
   AGREES` again, so the line that carries it is **identified**, not merely nominated.

   **WHAT REMAINS OUTSIDE THE DENOMINATOR, and it is not nothing:**

   * **19 names of the package are outside the import closure** and were not swept; every run
     prints them. That none of them decides staleness, agreement or reading-ness is a claim about
     **this SHA**, made by reading them, and it is the claim to attack.
   * **The sweep did not see the auditor's own variant file.** With `ASR2-005-A` present as
     `src/crash_detector/serving/panel_feed.py` the sweep still reports 402 sites, because that
     module imports none of the six entry modules. Disclosed rather than left to be discovered:
     **the sweep counts and does not guard**, and what refuses that variant is the re-construction
     at the door, which needs no module to be in any set.
   * **The sweep's own four boundaries**, in its header: static and intra-procedural, so every
     `ESTABLISHED` disposition is a **claim by the engineering seat** and not something the tool
     verified; it sees only operators written literally, so `operator.__lt__` produces no site;
     its subject set is an import closure; and a disposition keyed by expression text does not
     survive a rename. For a **mis-declared** disposition: **NOT PROVED TO BE CARRIED ANYWHERE** —
     it is invisible to the tool by construction.
   * **Four places are declared OPEN or OUT OF BOUND rather than closed**, named in
     `tools/sweep/declared_dispositions.py`: the injected `ContributionModel`
     (`crash_detector.engine.model` — ruled closed by **construction** at Blueprint §7 in WO-3 by
     `PO-DECISIONS-0003`, and deliberately **not** closed by a guard here), `SourceRecord`'s
     `cadence_seconds` int subclass, `FetchFailed.http_status` and `Malformed.instance_path`.
     Each says why, and each is **NOT PROVED TO BE CARRIED ANYWHERE**.
   * **And boundary 5 below**, which is a route to `WITNESS AGREES` on a stale row that this
     closure does **not** close.

   **`Agrees` is deliberately not slotted by this amendment** (`CD-D-058` — an instruction obeyed,
   not an oversight). Slotting it would close the undeclared-attribute half — the `"smuggled"`
   write above — and leave the declared-slot half wide open, and the declared-slot half **is** the
   whole of `PL-W5`: the write that reaches `WITNESS AGREES` overwrites the declared field
   `as_of_utc`. A change that closes the measured-harmless half and reads like a closure of the
   other is the `CD-PL-F54` shape, which has already sent one increment back. Increment 6 writes
   no logic.
4. **THE PUBLISHED ENVELOPE'S `staleness_window_seconds` FIELD IS NOT ADMITTED THROUGH THIS
   DOOR.** The envelope carries the window that *was* applied as a plain number validated by the
   JSON Schema, so a hand-built envelope declaring an inadmissible window is a
   publication-provenance question rather than a staleness one. **NOT PROVED TO BE CARRIED
   ANYWHERE.**
5. **A `tzinfo` IS A SUPPLIED OBJECT, AND IT IS THE LAST PLACE A SUPPLIED OBJECT'S METHOD STILL
   RUNS INSIDE A FRESHNESS COMPUTATION.** *Added at WO-2R2 increment 2.* **MEASURED OPEN.**

   Since that increment every timestamp is **rebuilt** by `crash_detector.own_terms.own_instant`
   from the supplied object's own primitive fields, so no method of `type(value)` runs. But the
   **UTC offset** comes from `datetime.utcoffset(value)`, whose base implementation asks
   `value.tzinfo` — and a `tzinfo` cannot be refused without refusing `zoneinfo`, `pytz` and
   `pandas`, all of which supply their own.

   **MEASURED** (variant `CD-ENG-WO2R2-V10`, on pristine extractions of **both** `50fc231` and the
   closure, with identical results):

   ```python
   stale_by_22h = datetime(2026, 8, 18, 14, tzinfo=SkewedZone(-22))
   row = PanelRow(state="AGREES", as_of_utc=stale_by_22h, published_utc=stale_by_22h,
                  measures={"divergence_measure": 0.01})
   resolve_panel(row, now_utc=NOW_2026_08_19T12Z, staleness_window_seconds=600.0)
   # -> Agrees -> 'WITNESS AGREES', on a row whose stated wall clock is 22 HOURS OLD
   ```

   **THE BOUND IS CARRIED BY THE CPYTHON INTERPRETER AND WAS MEASURED, not assumed:**
   `call_utcoffset` refuses any return that is not a `timedelta` and any magnitude of a day or
   more — `timedelta(days=1)` raises `ValueError: offset must be a timedelta strictly between
   -timedelta(hours=24) and timedelta(hours=24)`. So this route can move an instant by at most 24
   hours, which is **96x the 900-second ceiling** derived from PID §5.

   **BEYOND THAT BOUND, NOT PROVED TO BE CARRIED ANYWHERE.** It is the same fact as boundary 2 —
   clock trust is not established and is not claimed — reached through the offset rather than
   through `now_utc`, and it is a statement about the **data** a caller supplied rather than about
   **code** a caller supplied. It is **not introduced by the WO-2R2 closure**: it is measured
   identically at the audited base. It is written down because the closure made it the **last**
   such route, and a residue that is now the only one of its kind should be findable without
   re-deriving it.

Do not read a clean run of this test as proof that every freshness decision in a deployment is
sound. Read it as proof of exactly three things: that no window wider than the ratified
detectability budget can be applied; that agreement cannot exist without the comparison that
justifies it; and — since WO-2R2 increment 2 — that the values that comparison is made of are
objects this system constructed, so the answer is not the supplied timestamp's to give. It is
**not** proof about boundary 5, which is open and measured open, and it is **not** proof about the
routes listed as outside the denominator in boundary 3.

## Negative control

A missing or stale panel row defaulted to Agrees — whether by a default argument, a fallback branch, a truthiness test that treats absence as agreement, or a field added to the Unavailable constructor that a later edit could read as agreement; **or a configured staleness window wide enough to make staleness meaningless**, which needs no source edit at all and is the `CD-ASR-F06` route.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO2-0001`**.
That record does not exist yet. It is the run the **independent Assurance
seat** will produce — a distinct actor from the one that wrote this test. Until it exists
the validator computes `UNDECIDABLE` for this test and the gate stays shut, which is
correct: this seat may declare which run must evidence its guard, and may not supply it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
