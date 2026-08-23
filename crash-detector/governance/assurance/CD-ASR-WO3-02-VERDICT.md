# CD-ASR-WO3-02 — ASSURANCE VERDICT ON INCREMENT 15 (GROUP C — PUBLICATION AND HEALTH SURFACE)

**seat:** `CD-ASR-WO3-02` (fresh identity; **NOT** `CD-ENG-WO3-01`, `CD-ENG-WO3-02` or
`CD-ASR-WO3-01` — `PBG-SOD-001`, non-waivable. This seat implemented nothing in the target.)
**target:** `116c01f4584c62a244910ac6676c030735596896` · branch `wo-3` · prior assured tip `9b09d2a`
· base `be0b355` (frozen)
**dispatch:** `governance/engineering/CD-DISPATCH-INC15-ASSURANCE.md`
**authority:** `PO-DECISIONS-0024` rulings 2 and 3 · boundary `BL-20260823T190920Z-0155`
**persisted by:** this seat, under the narrow one-file write grant in dispatch §2 (the remedy for
`CD-PL-F163`). **This is the only file this seat wrote outside `/tmp`.**

---

## VERDICT: **`AMBER`** — scoped

**confidence:** HIGH on everything I ran · the AMBER is for what the RECORD claims, not for a
bypass or a regression.

**Nothing is bypassed. Nothing is regressed. Group C is substantially built and I reproduced the
load-bearing halves of it myself.** The AMBER is carried by nine findings, of which the two that
matter are **overstatements in `BL-...-0155`**, and three of which are places where I **got a value
out of the health surface**.

**method:** my own `git archive 116c01f | tar -x -C /tmp/asr02/subject` and
`git archive 9b09d2a | tar -x -C /tmp/asr02/base14`. **The Engineer's worktree
`/srv/crash-detector-wo3` was never read as the subject.** Ten plants re-applied by me in ten
further pristine extractions. The probe run against a real socket I started and killed myself.
**Mutation of the target: NONE.** All scratch under `/tmp/asr02/`.

---

## SCOPE — WHAT I EXAMINED, WHAT I DID NOT

**EXAMINED:** the twelve items of dispatch §3 and the four of §4; the six new `src/` modules read in
full; both closed envelope schemas; the external probe; the ten plants; the register at base and
tip; the git history of `BL-...-0152/0153/0154/0155`.

**NOT EXAMINED, AND STATED AS UNVERIFIED RATHER THAN ASSUMED:**

- **No live PostgreSQL exists on this lane.** Every database claim in this verdict is measured
  against a recording double — mine and the Engineer's. **Transaction atomicity, the `alert.event`
  CHECK constraints as executed, and the append-only GRANT posture are `UNSUPPORTED` for a running
  instance.** The `db/` SQL is unchanged from `be0b355` (0 lines), so the grants are whatever they
  were; I read them, I did not exercise them.
- **The container set is not built.** No deployed health surface, no served bytes, no scheduled
  probe. `CD-AC-014`'s "externally observable" is verified as a *program that produces the right
  verdict*, not as *a host observing a running detector*.
- **The private/public boundary machinery itself** (`envelope_contract.py`, `classification.py`) is
  pre-existing and unchanged at this increment; I used it, I did not re-audit it.

---

## 1. INCREMENT 14 IS NOT REGRESSED — **PASS, AND BY THE STRONGEST AVAILABLE FORM**

I ran the register verifier from **both** pristine extractions and diffed the two reports with only
the extraction path normalised:

```
cd /tmp/asr02/base14  && PYTHONPATH=pbg/tools python3 -B -m pbg.cli required-tests verify   -> EXIT 2
cd /tmp/asr02/subject && PYTHONPATH=pbg/tools python3 -B -m pbg.cli required-tests verify   -> EXIT 2
diff <normalised base> <normalised tip>                                    -> IDENTICAL REPORTS
```

Head of the tip report, verbatim:

```
pbg required-tests verify — /tmp/asr02/subject/required-tests.yaml
  pid.ref               PID.md
  pid.content_hash      MATCHES
  latest_admitted_run   (null)
  ...
GATE: SHUT
PID_ACCEPTANCE_SATISFIED: NOT DERIVED
```

`grep -cE "^  \[[MA]\] CD-AC-"` → **18 at base, 18 at tip.** All 18 `UNDECIDABLE`.
`latest_admitted_run` **still null.** `pid.content_hash` **MATCHES.** Gate **SHUT**.

> **The reports are byte-identical.** That is stronger than "still 18": it means no criterion's
> status, reason, or blocking negative-control text moved in either direction.

Instrument identity re-established independently: `git rev-parse 116c01f:pbg be0b355:pbg main:pbg
9b09d2a:pbg` → `e4ee93cbd87329683678bb1403ec76c8346ded73` **four times**.

---

## 2. REGISTER EDIT NARROWNESS — **PASS**

```
git diff --shortstat 9b09d2a..116c01f -- required-tests.yaml   -> 1 file changed, 85 insertions(+), 5 deletions(-)
git diff 9b09d2a..116c01f -- required-tests.yaml | grep -cE "CD-AC-002|CD-AC-005"   -> 0
diff <(git show 9b09d2a:required-tests.yaml | grep "^- criterion_id:") \
     <(git show 116c01f:required-tests.yaml | grep "^- criterion_id:")   -> CRITERION LIST IDENTICAL
diff <(git show 9b09d2a:… | grep -E "^\s+(execute|execution_contract|evidence_ref|test_id):") \
     <(git show 116c01f:… | …)                                          -> IDENTICAL
```

**No row added, removed or renumbered. Not one `execute`, `execution_contract`, `evidence_ref` or
`test_id` line changed anywhere in the file.** The whole edit is three
`negative_control.violation` block scalars, on `CD-AC-008`, `CD-AC-009` and `CD-AC-014`. The
Project Lead's "used less permission than it was given" account is **confirmed by measurement**.

**The §7.6 non-resolving-path trap could not be sprung by this increment — but see `F09`: two rows
already carry one.**

---

## 3. C1 — TWO ENVELOPES, EACH AGAINST ITS OWN CLOSED SCHEMA, BOTH BEFORE EITHER WRITE — **PASS**

Two genuinely distinct closed schemas:

```
public   sha256:00511ad6bf72bfab  additionalProperties: False  (no `classification`)
private  sha256:45cabd8a34c18f11  additionalProperties: False  (`classification` required)
```

**Order measured with MY OWN recording double, not the project's fakes' assertions:**

```
happy path      -> ['publication.public_envelope', 'publication.private_envelope',
                    'publication.heartbeat', 'COMMIT']   heartbeat_written = True
PRIVATE broken  -> refused surface EnvelopeSurface.PRIVATE
                   statements issued: ['alert.event', 'COMMIT']
```

**A broken PRIVATE envelope issues no statement against `publication.public_envelope` at all.**
That is "both before either", not "each before its own". The source confirms it structurally: both
`refuse_unless_publishable` calls sit in a `try` block that precedes the single
`with connection.cursor()`.

The refusal alert is written **and committed** before the refusal is re-raised, and a failure to
write the alert chains onto the original refusal rather than replacing it — `Q26`'s "durable rows
first" honoured.

---

## 4. C2 — THE HEARTBEAT WRITER EXISTS · CADENCE ≠ AGE — **PARTIAL. SEE `F01` AND `F02`.**

The writer exists (`HEARTBEAT_INSERT`, issued inside the same cursor block as both envelopes). The
`0 matches` baseline is confirmed: `grep -rn heartbeat src/ --include=*.py` at `9b09d2a` → **exit 1,
zero matches**, while `db/migrations/0005_publication.sql` has carried the table since WO-2.

**The dispatch told me to verify the no-age-parameter claim by introspection AND THEN TRY TO DEFEAT
IT. I did both. The introspection half is weaker than recorded and the defeat succeeded through the
one parameter that exists.** Full measurement in `F02`.

**The closure/module-level route the dispatch asked me to hunt DOES NOT EXIST** — refuted:
`evaluate_cadence.__closure__` is `None`, `__defaults__`/`__kwdefaults__` are `None`, and the module
holds no mutable state. **That half of the challenge comes back clean.**

---

## 5. C3 — THE PROBE IS OUTSIDE THE CONTAINER SET AND OUTLIVES WHAT IT WATCHES — **PASS**

Structure, by AST rather than grep:

```
imports: ['__future__','argparse','datetime','json','sys','urllib.error','urllib.request']
crash_detector imported: NO  (the 2 textual hits are the module docstring and one comment)
psycopg / DSN / PGPASSWORD: 1 each, ALL inside the module docstring
compose.yaml services (parsed, not grepped):
  cd-collectors cd-engine cd-private cd-public cd-review cd-store cd-witness   -> 'probe' is NOT one
```

**The live arm, run by me.** I started my own `http.server` on `127.0.0.1:8731`, copied
`external_probe.py` alone into `/tmp/asr02/probe_test/`, and ran it with **`PYTHONPATH` unset**:

```
socket UP
$ env -u PYTHONPATH python3 external_probe.py --health-url http://127.0.0.1:8731/health
HEALTHY: live, not degraded, last publication 0.8s ago
EXIT=0

--- I KILLED THE SERVER ---
socket DOWN: ConnectionRefusedError [Errno 111] Connection refused

$ env -u PYTHONPATH python3 external_probe.py --health-url http://127.0.0.1:8731/health
UNREACHABLE: nothing answered at http://127.0.0.1:8731/health: URLError
EXIT=2
```

And the discrimination that matters, which I added and the Engineer did not claim — a surface that
**answers** with a failure is not the same as one that is **gone**:

```
$ … --health-url http://127.0.0.1:8732/health   (server answering HTTP 500)
DEGRADED: the health surface answered HTTP 500
EXIT=1
```

> **The probe survived the thing it was watching and returned a verdict. `PBG-EVID-001` discharged
> by demonstration.** The claim in `BL-...-0155` about this is accurate and I reproduced it from
> scratch.

**UNVERIFIED:** no host is measured running this probe on a schedule. The Engineer says so; I
confirm the gap and confirm it is disclosed.

---

## 6. C4 — REGIME-AWARE STALENESS — **PASS**

**The criterion, executed:** one age, one instant, one constructor, one argument different.

```
ONE age 300.0s, regime=CALM,   window=600.0s -> ADMITTED (age=300.0s)
ONE age 300.0s, regime=STRESS, window=120.0s -> REFUSED FreshnessNotEstablished:
   "the observation is 300.0 seconds old and the applied staleness window is 120.0 seconds, so it is STALE"
```

Construction refusals, all measured:

```
{CALM:600, STRESS:600}            -> StalenessPolicyIncoherent  (the window made constant)
{CALM:120, STRESS:600}            -> StalenessPolicyIncoherent  (the comparison inverted)
{CALM:600}                        -> StalenessPolicyIncoherent  (a regime with no window)
{CALM:600,STRESS:120,PANIC:10}    -> StalenessPolicyIncoherent  (deny by default)
{CALM:1000, STRESS:120}           -> StalenessWindowOutOfRange   <-- THE PID §5 CEILING, ARRIVING
                                                                     THROUGH THE PRE-EXISTING DOOR
```

Module-level constructed policies reachable from `crash_detector.regime`: **`[]` — none.** A caller
that cannot state a policy gets an error, not a prudent default.

> **`CD-PL-F165` — the Project Lead's dispatch assertion "C4 is an extension, not a greenfield" —
> is REFUTED, and I refute it independently.** At `9b09d2a`, `grep -rn regime src/ --include=*.py`
> → **6 lines** (5 in `staleness.py`, 1 in `engine/config.py`). An AST pass for `Name`/`Attribute`/
> `arg`/`def` nodes containing `regime` returns **NOTHING**. The single non-docstring hit is a
> module-level documentation string constant. **No mechanism existed to extend.** The Engineer's
> `F01` is correct. The Project Lead's *surviving* claim — that the seat went **through** the
> `StalenessWindow` door rather than building a second mechanism beside it — is **confirmed**: the
> 900 s ceiling refuses `{CALM: 1000}` from inside `RegimeStalenessPolicy.__post_init__`, and that
> refusal is raised by `StalenessWindow`'s constructor, not restated in `regime.py`.

**NOT ESTABLISHED, and the module says so:** no consumer. `window_for` has no caller anywhere in
`src/`. The relation is enforced on a policy nothing applies.

---

## 7. C5 — THE HEALTH SURFACE — **I GOT VALUES OUT OF IT. SEE `F03`, `F04`, `F05`.**

The dispatch called this the highest-yield place to attack and it was. **The KEY axis is genuinely
closed and every attack on it failed** — that part is real work and it holds:

```
extra key 'equity_crash_score'         -> REFUSED  [UNKNOWN_KEY] at /equity_crash_score
nested {'equity_crash': {'score':…}}   -> REFUSED  [UNKNOWN_KEY] at /last_evaluation_utc/equity_crash
regime="0.87"                          -> REFUSED  [UNDECLARED_REGIME]
undeclared degradation class           -> REFUSED  [UNDECLARED_DEGRADED_CLASS]
private-classified / secret-bearing    -> REFUSED, naming the classifying token, at every depth
live=0.87                              -> neutralised by bool() — served as true, no value leaks
```

**The VALUE axis is not closed for the two fields nobody wrote a vocabulary for.** Measurements in
`F03`. Degraded state IS explained by class and never by value — `DEGRADED_CLASSES` is closed and
the flag is derived from the classes so the two cannot disagree. That specific requirement holds.

---

## 8. C6 / `Q26` — NO EXTERNAL PUSH EXISTS — **PASS, UNQUALIFIED**

AST over every `.py` under `src/`, walking **all** `Import`/`ImportFrom` nodes at every depth
(so function-local imports are included):

```
NETWORK-CAPABLE IMPORTS IN src/: NONE — zero
```

against a denylist of `urllib, socket, http, https, smtplib, requests, httpx, aiohttp, ftplib,
telnetlib, asyncio, ssl, xmlrpc, webbrowser, poplib, imaplib`. There are **27 textual matches** for
those words in `src/` and **0 of them are imports** — every one is prose saying nothing opens a
socket. Not disabled, not flagged: **not present.**

```
git diff --stat be0b355..116c01f -- deploy/ db/    -> (empty: 0 changed lines)
```

`deploy/egress-destinations.yaml` **unmodified**. `tools/register/check_egress_no_broker.py` → PASS,
69 assertions.

**`alert.event` is append-only and no route was opened.** Every SQL string constant in `src/`
enumerated by AST: the only statements touching `alert.event` are one `INSERT` and one `SELECT`.
`grep -rniE "(update|delete|truncate|drop).*alert" src/ tools/` → **NONE**. Migration 6's
"no UPDATE or DELETE grant for any role" is unchanged (0 lines in `db/`). *(Grants are read, not
exercised — see SCOPE.)*

---

## 9. NO SOURCE REGISTERED — **PASS. THE DISCLOSURE IS HONEST.**

`INSERT INTO raw.source_registry` appears **exactly once** in the tree outside the build log:
`tests/test_publication_layer.py:405`, and it is an argument to `ast.parse(...)` inside
`test_that_scan_would_catch_a_real_registration` — the vacuity guard for the no-source scan.

**VERIFIED PARSED AND NEVER EXECUTED:** `ast.parse` returns an AST and executes nothing; the file
contains **no `exec(`, `eval(`, `compile(`, `connect(` or `psycopg`** (grep → NONE); the parsed
result is only walked for `ast.Constant` nodes and counted. The sibling `SourceRecord(source_id='x')`
is the same construction. `SourceRecord(` constructed anywhere in `src/ tools/ deploy/ contracts/`:
**0**. `db/` unchanged from `be0b355`.

> The Engineer volunteering this before an auditor could trip over it is the correct habit and I
> record that it cost me nothing to clear.

---

## 10. NO BLENDING · NO ROUTE FROM `Unavailable` TO `Agrees` — **PASS**

Every pre-existing register checker re-run by me over the tip tree:

```
check_no_blend.py                                 PASS — 8413 assertions, 0 violations (52 files)
check_schema_closed.py                            PASS — 242 assertions
check_exact_type_admission.py                     PASS — 36
check_judgement_path_doors.py                     PASS — 72
check_constructor_field_establishment.py          PASS — 101
check_sealed_against_forged_establishment.py      PASS
delegated_judgement_sweep.py                      exit 0
check_no_execution_interface.py                   PASS — 74552 assertions
check_egress_no_broker.py                         PASS — 69
```

**No route from `Unavailable` to `Agrees` was introduced, because no increment-15 module touches a
witness disposition at all.** `grep` for `Agrees|Diverges|Unavailable|disposition|witness` across
the six new modules returns only two prose lines in `health.py` and one in `detail_level.py`, plus
the constant `RAISED_BY_WITNESS = "cd_witness"`. `publish_cycle` treats the envelopes as opaque
mappings judged by the pre-existing closed schemas. **The publication layer is where I was told to
look for an absent witness rendered as agreement, and it is not there.**

`health.py` carries `DEGRADED_WITNESS_UNAVAILABLE` as its own degradation class, which is the
opposite of the failure mode.

---

## 11. CONTAINMENT — **PASS**

```
git log --format="%an <%ae>" 9b09d2a..116c01f | sort -u
  -> CD-ENG-WO3-02 <cd-eng-wo3-02@seats.crash-detector.invalid>     EXACTLY ONE, all 8 commits
git -C /srv/crash-detector-wo3 status --porcelain                    -> (empty)
git -C /srv/crash-detector-wo3 rev-parse HEAD                        -> 116c01f…  AGREES
git rev-parse wo-2r3                                                 -> be0b355…  STILL FROZEN
git rev-parse 116c01f:pbg be0b355:pbg main:pbg 9b09d2a:pbg           -> e4ee93cb… x4
git diff --name-only 9b09d2a..116c01f -- pbg/ PID.md BLUEPRINT.md \
    governance/decisions/ ACTIVE_WORK.yaml deploy/ db/ contracts/    -> (empty: 0 paths)
git diff --shortstat 9b09d2a..116c01f                                -> 27 files, 5370 ins, 5 del
```

Size matches the boundary exactly.

---

## 12. THE TEN PLANTS ARE NON-VACUOUS — **PASS. THE ENGINEER'S REASONING SURVIVES THE TEST.**

I re-applied all ten in **ten separate pristine `git archive 116c01f | tar -x` extractions**, and
ran a clean arm from an eleventh. **`git apply` exit code recorded as its own column.**

Clean arms, from an untouched extraction:

```
test_publication_layer.py   EXIT=0   21 passed
test_cadence_breach.py      EXIT=0   27 passed
test_regime_staleness.py    EXIT=0   25 passed
test_health_surface.py      EXIT=0   37 passed
test_no_external_push.py    EXIT=0   15 passed
test_detail_level.py        EXIT=0   31 passed
```

Violated arms — **`git apply` 0 and exit 1 on all ten**, and the failing test names:

| plant | apply | clean | violated | failing tests I observed |
|---|---|---|---|---|
| P1 | 0 | 0 | 1 | `test_a_PRIVATE_envelope_violating_its_schema_also_writes_NO_PUBLIC_ENVELOPE`, `test_each_envelope_is_judged_against_ITS_OWN_contract`, `test_a_secret_bearing_key_is_refused_on_BOTH_surfaces` |
| P2 | 0 | 0 | 1 | `test_a_private_classified_key_on_the_public_surface_is_refused`, `test_the_same_key_nested_inside_a_dial_is_refused_too` |
| P3 | 0 | 0 | 1 | `test_publication_halted_is_a_breach`, `test_the_halt_is_detected_by_the_OPEN_interval_and_not_by_any_closed_one`, `test_detection_happens_within_one_publication_cycle_of_the_breach`, `test_a_breach_writes_a_durable_alert_row_first` |
| P4 | 0 | 0 | 1 | `test_evaluate_cadence_CANNOT_BE_GIVEN_the_age_of_a_number` |
| P5 | 0 | 0 | 1 | `test_a_constant_window_is_refused`, `test_an_inverted_window_is_refused` |
| P6 | 0 | 0 | 1 | `test_the_five_observables_are_independently_readable`, `test_a_dial_value_on_the_health_surface_is_refused` |
| P7 | 0 | 0 | 1 | `test_the_application_tree_imports_nothing_outside_the_declared_surface` |
| P8 | 0 | 0 | 1 | `test_the_probe_imports_nothing_from_the_application`, `test_the_probe_runs_without_the_application_package_importable` |
| P9 | 0 | 0 | 1 | `test_a_policy_that_renders_absent_data_as_calm_is_REFUSED` |
| P10 | 0 | 0 | 1 | `test_a_degraded_reading_never_renders_as_calm_even_with_a_tiny_score` |

> *** **THE ENGINEER'S ADDED COLUMN IS VINDICATED, AND ITS REASONING IS THE RIGHT REASONING.** ***
> The names I observed **match the manifest exactly, plant for plant**. **Every failure carries the
> plant's own proposition.** There were **zero `ERROR` lines and zero collection failures** in any
> arm, and the pass counts stayed high in all ten — so **no arm failed for an incidental reason**,
> which is precisely the vacuity class the seat named and closed unprompted:
> *"exit 1 proves the command failed, not that it failed for the planted reason — a plant that broke
> an import would look identical."* **I tested that reasoning as instructed and it holds on all ten.**
>
> Three of the ten (`P3`, `P4`, `P5`, plus `P6`/`P8`) ran under the register's **own declared
> commands**, which I read out of `required-tests.yaml` at the tip rather than from the manifest.

**Suite, from my own extractions:** `1882 passed in 61.25s` at the tip; `1726 passed` at `9b09d2a`.
**+156, exactly as returned.** Per `PBG-ASSURE-001` I treated this as evidence about the suite and
went on to read what four of the load-bearing tests actually assert — which produced `F06` and `F07`.

---

# FINDINGS

## `CD-ASR-WO3-02-F01` — **MEDIUM** — `BL-...-0155` OVERSTATES THE HEARTBEAT RESULT

**Raised against:** `PROJECT_LEAD_SEAT_01`, `BL-20260823T190920Z-0155` header.

The record says, in its most emphatic typography:

> *"`publication.heartbeat` WAS A TABLE NOTHING WROTE … IT NOW HAS A WRITER. **THE 'CONTROLS EXIST
> AND NOTHING RUNS THEM' SHAPE IS CLOSED FOR THIS ONE TABLE.**"*

**MEASURED:**

```
grep -rn "publish_cycle" src/ tools/ deploy/ (excluding publish.py)   -> (empty) NO CALLER
grep -rn "if __name__"  src/ --include=*.py                           -> (empty) NO ENTRYPOINT
pyproject.toml console_scripts / entry_points                         -> none declared
```

The same holds for `evaluate_cadence`, `state_document`, `recent_alerts`, `RegimeStalenessPolicy`
and `detail_level_for`: **every public entry point of increment 15 has zero callers outside its own
defining module and the test suite.** Only `raise_alert` (called by `publish.py`) and
`health_document` (called by `state_document`) have an in-package caller.

**A writer exists. No write occurs.** Nothing in this repository can cause a row to appear in
`publication.heartbeat`, for the same reason nothing could before: there is no process. The shape
moved one hop closer; it is not closed. The Engineer's own `publish.py` declared limit 1 is honest
about this ("this is the publication layer, not the envelope builder … the builder is owed with the
source set"); **the boundary's compression of it into "the shape is closed" is not.**

**This is the finding the dispatch said this project values most: the record claims more than was
measured.**

## `CD-ASR-WO3-02-F02` — **MEDIUM** — `BL-...-0155` OVERSTATES C2, AND I DEFEATED THE CLAIM

**Raised against:** `PROJECT_LEAD_SEAT_01`, `BL-...-0155` header and `C2_cadence_is_not_age`.

The record says:

> *"`evaluate_cadence(heartbeats_utc)` **TAKES ONLY HEARTBEAT TIMESTAMPS**, SO THERE IS NO PARAMETER
> THROUGH WHICH AN AGE COULD ARRIVE. CADENCE CANNOT BE CONFUSED WITH STALENESS **BY CONSTRUCTION**,
> NOT BY A TEST THAT COULD BE DELETED."*

**MEASURED BY INTROSPECTION:**

```
evaluate_cadence(heartbeats_utc: 'Sequence[datetime]', *, now_utc: 'datetime', budget: 'CadenceBudget')
PARAM NAMES: ['heartbeats_utc', 'now_utc', 'budget']          <-- THREE, not one
__closure__: None   __defaults__: None   __kwdefaults__: None
```

`budget` is gated by **exact nominal type** (`if type(budget) is not CadenceBudget: raise TypeError`
— confirmed: passing `60.0` raises). **`heartbeats_utc` is gated by nothing.** It is
`Sequence[datetime]`, and a reading's `as_of_utc` **is** a `datetime`.

**THE DEFEAT, RUN:**

```
b = CadenceBudget(publication_interval_seconds=60.0, missed_cycles_allowed=1)   # threshold 120.0s
A) real heartbeat 30s ago                     -> breached=False  open=30.0
C) ONLY a reading's as_of_utc (5000s old)
   passed in the heartbeat set                -> breached=True   open=5000.0
B) healthy heartbeat + that reading instant   -> breached=True   worst=4970.0  count=2
E) a datetime SUBCLASS as a heartbeat         -> ADMITTED         open=7200.0
D) now_utc supplied from data, not a clock    -> breached=True   open=1030.0
```

> **Arm C is the age of a number producing a cadence verdict, arriving through the one parameter
> that exists. Arm B is a healthy publisher reported BREACHED because a stale reading's timestamp
> was passed alongside the heartbeats.**

**What is true:** there is no *dedicated* age parameter, and **no closure or module-level route
exists** — that half of the dispatch's challenge I attacked and **refuted**. `P4` correctly catches
the widening of the signature.

**What is not true:** that the confusion is prevented *by construction*. It is prevented by
*parameter naming*. The module applies this project's own nominal-type discipline (`StalenessWindow`,
`CadenceBudget`, `DialSlot`) to the parameter that **could not** have been confused, and withholds
it from the one that **could**. A `HeartbeatInstant` newtype — the idiom already used five times in
this codebase — would have made the record's sentence literally true.

**Note in the Engineer's favour:** its own docstring says the narrower and correct thing — *"there is
no parameter here for the age of a number … no reading, no envelope, no `as_of_utc`, no dial."* **The
overstatement is the boundary's, not the module's.**

## `CD-ASR-WO3-02-F03` — **MEDIUM** — I GOT VALUES OUT OF THE HEALTH SURFACE

**Raised against:** `CD-ENG-WO3-02`, `src/crash_detector/health.py`.

```
health_document(last_publication_utc=0.8712345, …)
  -> {"last_publication_utc": 0.8712345, …}                              SERVED
health_document(last_publication_utc="source=ARGUS-SPX-FEED", …)
  -> {"last_publication_utc": "source=ARGUS-SPX-FEED", …}                SERVED  (a SOURCE NAME)
health_document(last_evaluation_utc=[0.87, "SPX", "witness=disagrees"], …)
  -> {"last_evaluation_utc": [0.87, "SPX", "witness=disagrees"], …}      SERVED  (a dial value, a
                                                                          ticker and a witness
                                                                          reading, in one list)
```

`last_publication_utc` and `last_evaluation_utc` receive **no type check, no format check and no
vocabulary**, and a **list's elements are never classified** — `iter_keys` visits keys only, so an
array riding on a declared key is opaque to both of the module's refusals.

**And the module's own DECLARED LIMIT 1 names the wrong field.** It offers `regime="0.87"` as the
residue, then says `regime` is closed by `REGIME_ORDER` — which is true and which I measured
(refused, `[UNDECLARED_REGIME]`). **The two fields that are genuinely open are not named in the
limit and are not constrained by any test:** `grep "last_publication_utc" tests/test_health_surface.py`
shows it only ever supplied via `_iso(...)`, never adversarially.

**Severity is MEDIUM, not HIGH**, and I want the reason on the record: a caller must deliberately
supply the value, there is no caller (`F01`), and there is no transport. This is a latent defect in
a document builder, not a leaking endpoint. **But `CD-AC-006` on an unauthenticated surface is this
project's most protected criterion and "explain it with a class, never with a value" is the module's
own headline — the value axis deserves the same closure the key axis got.**

## `CD-ASR-WO3-02-F04` — **LOW** — `state_document` DOES NOT VOCABULARY-CHECK ITS OWN ALERT PROJECTION

**Raised against:** `CD-ENG-WO3-02`, `health.py::_projected_alert`.

```
state_document(alerts=[(0.87, "equity_crash=0.87", "witness:ARGUS disagrees", "x", "y")], …)
  -> "alerts": [{"event_class": "0.87",
                 "severity": "equity_crash=0.87",
                 "raised_utc": "witness:ARGUS disagrees"}]                SERVED
```

`ALERT_EVENT_CLASSES` and `ALERT_SEVERITIES` exist in the sibling module and are enforced at the
**write** door (`raise_alert` — verified: an undeclared class raises `AlertRefused`). They are not
applied at the **read** door. In the intended wiring the rows come from `recent_alerts` over a table
carrying CHECK constraints, so this is latent — **but the module argues at length that
`degraded_classes` must be a closed vocabulary "because free text is where a number eventually gets
written", and then leaves its own `alerts` block open.** Two lines would close it.

*The `subject_ref` drop is correct and I verified it: `_projected_alert` reads `row[0:3]` positionally
and `recent_alerts` selects `raised_by` and `subject_ref` at positions 3–4, so they cannot arrive.*

## `CD-ASR-WO3-02-F05` — **MEDIUM** — THE "CLOSED ALLOWLIST" IS A CALLER-SUPPLIED ARGUMENT

**Raised against:** `CD-ENG-WO3-02`, `health.py::refuse_unless_health_safe`.

```
refuse_unless_health_safe({"score": 0.9}, allowed_keys=("score",))   -> returns cleanly. ADMITTED.
```

The docstring says *"**THE CLOSED ALLOWLIST.** `HEALTH_KEYS` is total."* It is total **by default**.
`allowed_keys` is a public keyword on a function in `__all__`, so widening the surface is a
one-argument call rather than an allowlist edit somebody reviews.

**This is `GUARD_THE_INSTANCE_NOT_THE_CLASS`:** `P6` plants a key into `HEALTH_KEYS` and is caught;
the identical violation introduced via `allowed_keys` is invisible to `P6` and to every test.
Contrast the envelope door, which binds surface → schema and admits no override. `STATE_KEYS` needs
one extension point, not an open parameter — an `EnvelopeSurface`-style enum would give the same
capability without the hole.

## `CD-ASR-WO3-02-F06` — **MEDIUM** — THE TEST CITED AS *ENFORCING* `detail_level`'s ABSENCE DOES NOT GUARD THE ATTACHMENT THE SEAT RECOMMENDED

**Raised against:** `PROJECT_LEAD_SEAT_01` (`BL-...-0155` `Q29.how_the_decision_is_kept_visible`) and
`CD-ENG-WO3-02` (`tests/test_detail_level.py:271`).

The record says:

> *"**A TEST ASSERTS `detail_level` IS ABSENT FROM BOTH SCHEMAS.** SO THE OMISSION IS **ENFORCED**
> RATHER THAN MERELY CURRENT, AND ADDING IT LATER IS A DELIBERATE ALLOWLIST EDIT WITH A
> `schema_version` BUMP."*

The test asserts exactly two things, both at the **top level**:

```python
assert "detail_level" not in schema["properties"], name
assert "detail_level" not in schema["required"], name
```

**MEASURED — I attached `detail_level` inside `$defs/dial_reading`, which is the PER-DIAL attachment
the seat itself recommends:**

```
assertion `detail_level not in schema['properties']` -> True
assertion `detail_level not in schema['required']`   -> True
=> TEST STILL PASSES
```

**The omission is enforced against the option the seat rejected and unenforced against the option it
proposed.** A `json.dumps(schema)` substring check, or a recursive walk, closes it.

## `CD-ASR-WO3-02-F07` — **MEDIUM** — `test_no_function_in_the_module_takes_two_readings` DOES NOT ASSERT ITS OWN TITLE

**Raised against:** `CD-ENG-WO3-02`, `tests/test_detail_level.py:181`.

It asserts `len(reading_like) <= 2`, where `reading_like` counts parameter names containing
`"reading"` or `"dial_slot"`. **MEASURED:**

```
def envelope_detail_level(equity_reading, monetary_reading):
    reading_like = ['equity_reading', 'monetary_reading']
    assert len(reading_like) <= 2      -> True
    assert no banned name              -> True
    => TEST PASSES on a function consuming BOTH dials
```

The bound is 2 because `detail_level_for(reading, *, dial_slot=…)` has two matching names, so the
threshold was fitted to the current signature rather than to the proposition. Its docstring —
*"A level derived from BOTH dials is the `CD-AC-002` shape reached one step across"* — describes
exactly the thing it admits.

**The property itself is NOT unguarded:** `tools/register/check_no_blend.py` flags a single
expression consuming both dial types and I ran it (PASS, 8413 assertions, 52 files). **So this is a
test-quality finding, not a `CD-AC-002` breach.** It is reported because `PBG-ASSURE-001` requires me
to say what the suite actually asserts, and because this test is named in the module docstring as a
carrier of the anti-blend property.

## `CD-ASR-WO3-02-F08` — **LOW** — `publish._document` IS A SHALLOW COPY AND ITS DOCSTRING CLAIMS MORE

**Raised against:** `CD-ENG-WO3-02`, `publish.py:292`.

> *"A copy because the caller keeps a reference to what they passed in, and a mapping that is mutated
> between validation and serialisation is a document that was judged in one shape and stored in
> another."*

`dict(envelope)` shares every nested mapping and list with the caller, so the stated hazard is
unmitigated one level down. The window is synchronous and no in-process route exercises it, so the
risk is theoretical — **the rationale as written is simply wider than the code.**

## `CD-ASR-WO3-02-F09` — **LOW, PRE-EXISTING, NOT INTRODUCED BY THIS INCREMENT**

The dispatch told me to check that no `execution_contract` points at a non-existent file, because a
non-resolving path silently forces `UNDECIDABLE` and **skips negative-control evaluation**. **Two
rows already carry one:**

```
CD-AC-017  execution_contract 'contracts/execution/CD-RT-017-ADMISSION-BY-DECLARED-DOOR-PROVENANCE.md' does not resolve
CD-AC-018  execution_contract 'contracts/execution/CD-RT-018-PUBLICATION-BOUNDARY-RAISES-DIVERGENCE.md' does not resolve
```

**Identical at `9b09d2a` and at `116c01f`** (the reports are byte-identical), and no
`execution_contract` line changed in this increment. **This increment neither caused nor repaired
it.** It is reported because the trap the dispatch named is already sprung on two rows and, on those
two, the register is reporting a path fault rather than an evidence fault. Book it to the lane
residuals.

---

# GRADING THE PROJECT LEAD (dispatch §4)

**`Q29` / the Engineer's `F03` — IS STOPPING DEFENSIBLE?**
**YES — DEFENSIBLE, BUT THE STATED PRIMARY REASON IS THE WRONG ONE, AND THE ENFORCEMENT IS WEAKER
THAN RECORDED.**

*Genuinely unwired — verified:* no module in `src/` imports `detail_level`; `detail_level` is absent
from the `properties` and `required` of both schemas (it appears once in the **public** schema as
prose in its own `description`, listed under *"DELIBERATELY ABSENT AND OWED"* — I checked and it is
**not** a property); `test_the_module_declares_no_ready_made_policy` measures zero constructed
policies and I re-measured it. `publish.py` mentions it only in declared limit 2.

*The reasoning, graded:* the boundary leads with `reason_2` — that envelope-level attachment "would
require a function over BOTH dials, the `CD-AC-002` shape one step sideways". **That argument
justifies not doing the ENVELOPE-level attachment. It does not justify doing nothing** — and the
seat itself says so, by recommending **PER-DIAL**, which carries no blending hazard at all. **The
reason that actually holds is `reason_3`: the thresholds need a dial scale `Q25` holds, and
`CD-RULE-003` forbids the seat to invent one.** That is a real, hard block on a real PO question.

**So: a genuine Product Authority question, not an unfinished deliverable dressed as one.** With two
qualifications. **(a)** 290 lines of fully-tested policy were built ahead of the decision that
governs where it attaches — building the module first was a choice, not a constraint, and the
`Q29` framing slightly launders that. **(b)** The claim that the omission is *enforced* is true for
the rejected option and false for the recommended one — `F06`.

**`CD-PL-F165` — CONFIRMED, INDEPENDENTLY.** See §6. Six `regime` mentions at `9b09d2a`, every one
prose; an AST pass finds no identifier, parameter, attribute or definition. **"C4 is an extension,
not a greenfield" is refuted.** The Project Lead's self-diagnosis — *"a Project Lead characterising
code it has grepped but not read, and then putting the characterisation in a binding dispatch"* — is
accurate, and I note that **`F01` and `F02` of this verdict are the same error class committed one
step later: a code fact inferred from a partial reading and put in a binding RECORD rather than a
binding dispatch.** The remedy the PL named for itself (state survey results as observations, let
the next seat draw the conclusion) applies unchanged to boundary prose.

**`PBG-CONT-003` — HONOURED.** Each of the four entries was created in exactly one commit and never
touched again:

```
BL-...-0152  1 commit  4ba110f  numstat 188 0
BL-...-0153  1 commit  3bc96f0  numstat 237 0
BL-...-0154  1 commit  bf7f1c0  numstat 122 0
BL-...-0155  1 commit  990ed04  numstat 188 0
```

**Zero deletions on all four. Superseded, never edited** (`F158`→`F160`, `F163`, `F165` are all
supersessions). Clean.

**DOES `BL-...-0155` OVERSTATE ANYTHING? — YES, IN THREE PLACES.** `F01` (the heartbeat shape is not
closed), `F02` (cadence is not separated by construction), `F06` (the `detail_level` omission is not
enforced against the recommended attachment). **Everything else in that entry that I re-measured was
accurate, including several claims it would have been easy to fudge:** the 0-matches heartbeat
baseline, 27/5370/5, `1882` (I got `1882` and `1726`), one identity, `pbg` identical at four refs, 0
protected paths, 0 lines in `deploy/` and `db/`, the register narrowness including the `grep -c` of
0, and the ten-plant table down to the failing test names.

---

# CONTINUATION IMPLICATION

**What is true and what is safe to do next are different calculations here, and they diverge.**

**TRUE:** Group C is substantially built. C1, C3, C4 and C6 I verified against the authentic target
and they hold without qualification. C5's key axis holds and its value axis does not. C2's writer
exists and its separation property is real but narrower than recorded. Increment 14 is not
regressed — byte-identically so. No source is registered. No push channel exists. Nothing is
bypassed.

**SAFE:** leaving `wo-3` at `116c01f` is safe. It runs nothing (`F01`), reaches no network, and the
gate is `SHUT`. **What is NOT safe is carrying `BL-...-0155` forward as the account a cold agent
resumes from**, because that record tells a successor that the heartbeat table is now written and
that cadence cannot be confused with staleness — and a successor who believes the first will not
build the caller, and one who believes the second will not add the nominal type.

**A `PASS` here would have spent credibility that `F01` and `F02` need.**

---

# NEXT SAFE GATE

**`PO-DECISIONS-0025` — Product Authority disposition of `Q25` (the hinge — the source set) and
`Q29` (where `detail_level` attaches), at the Matt hold.**

Preconditions, in order, none of which this seat may perform (`PBG-SOD-004`, `PBG-AUTH-003`):

1. **A superseding Build Log entry correcting `F01` and `F02`** — superseding, never editing
   (`PBG-CONT-003`). This is the gating item: it is a record-accuracy defect and the record is what
   survives the context window.
2. **`F03`, `F04`, `F05` booked to the WO-3 lane residuals** as `CD-AC-006` value-axis work, to be
   closed **before** any transport is written for the health surface. Not urgent while there is no
   endpoint; **blocking the moment there is one.**
3. **`F06`, `F07` booked** as test-strengthening, and `F06` closed **as part of** whatever `Q29`
   rules — if the ruling is PER-DIAL, the enforcing test must be repaired in the same change or the
   guard silently ceases to exist.
4. **`F09`** booked to the residuals with the two pre-existing non-resolving `execution_contract`
   paths named.

**Increment 16 should not be dispatched before item 1.** Items 2–4 may run in parallel with it.

**A `PASS` is not an acceptance and an `AMBER` is not a rejection (`PBG-AUTH-003`). Acceptance is
Matt's and is not delegated by this verdict.**

---

## EVERY COMMAND THIS SEAT RAN — REPRODUCTION INDEX

```
git archive 116c01f | tar -x -C /tmp/asr02/subject
git archive 9b09d2a | tar -x -C /tmp/asr02/base14
PYTHONPATH=pbg/tools python3 -B -m pbg.cli required-tests verify        (both trees)
PYTHONPATH=pbg/tools python3 -B -m pbg.cli validate                     (tip; AMBER, pre-existing)
diff <normalised base report> <normalised tip report>
git diff --shortstat / --name-status / -U0  9b09d2a..116c01f [-- required-tests.yaml]
diff <(git show 9b09d2a:required-tests.yaml | grep …) <(git show 116c01f:… | grep …)
python3 (ast) — imports of every .py under src/, network denylist
python3 (ast) — SQL verbs in every string constant under src/
python3 (ast) — `regime` identifiers at 9b09d2a
python3 (ast) — external_probe.py imports; compose.yaml parsed with yaml.safe_load
PYTHONPATH=src python3 — inspect.signature/__closure__ of evaluate_cadence; five defeat arms
PYTHONPATH=src python3 — nine health-surface value/key attacks
PYTHONPATH=src python3 — RegimeStalenessPolicy: 1 admit arm, 5 refusal arms, FreshnessEvidence
PYTHONPATH=src python3 — publish_cycle against MY OWN recording double, 2 arms
env -u PYTHONPATH python3 external_probe.py   (live socket / killed socket / HTTP 500)
tools/register/*.py + tools/sweep/*.py --root .          (9 checkers)
git apply + PYTHONPATH=src python3 -m pytest   x10 plants in 10 pristine extractions + 1 clean
PYTHONPATH=src python3 -m pytest tests/ -q      (both trees)
git log --format / --numstat  on BL-...-0152/0153/0154/0155
git rev-parse wo-2r3, wo-3, {116c01f,be0b355,main,9b09d2a}:pbg
git -C /srv/crash-detector-wo3 status --porcelain / rev-parse HEAD
```

**MUTATION OF THE TARGET: NONE.** No lane commit, no branch move, no edit to `src/`, `tests/`,
`required-tests.yaml`, `pbg/`, or any governance file other than this one.
