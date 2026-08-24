# CD-DISPATCH-INC16A-REGISTRY-CARRIER-ENGINEER

**role source:** `pbg/roles/engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `PO-DECISIONS-0025` rulings 2 (architecture portability, BINDING), 5 (`Q28` +
`Q29`) and 6 (increment 16, sequential single-seat, bounded) · scope
`governance/engineering/WO-3-SCOPE.md` §3 **Group A**, §5, §7
**seat identity:** `CD-ENG-WO3-03` — **FRESH.** Never `CD-ENG-WO3-01`, never `CD-ENG-WO3-02`, never
`CD-ASR-WO3-01`, never `CD-ASR-WO3-02`, never any `CD-ENG-WO2R3-*` or `CD-ENG-COORD*`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **increment:** 16A · **expected return:**
`READY_FOR_ASSURANCE`

---

## 0. READ THIS SECTION BEFORE ANY OTHER. **YOU REGISTER NO INDICATOR. NOT ONE ROW.**

`PO-DECISIONS-0025` released the Matt hold and ratified the source set. **AND THE RATIFIED
ARTEFACT'S CONTENT CANNOT BE READ FROM THIS PROJECT.** The Project Lead measured that at
`BL-20260824T070245Z-0157` and raised it as `Q30`:

```
grep -rl 'indicator_dial_mapping|architecture_portability|as_built:v1.0'  (repo, excl .git)
  -> governance/decisions/PO-DECISIONS-0025.md   AND NOTHING ELSE
grep -rl 'DRTSCILM|NDFI|SLOOS|private credit' --include=*.md --include=*.yaml
  -> governance/decisions/PO-DECISIONS-0025.md   AND NOTHING ELSE
/srv/trinity-self-mirror  -> no crash_detector namespace; state/current.json stamped 2026-08-15
no `trinity` / `fabric` resolver on PATH
```

**SO INCREMENT 16 IS SPLIT. YOU ARE 16A: EVERYTHING THE RULING BINDS THAT IS *NOT* THE MAPPING'S
CONTENT. 16B IS THE ROWS AND IT WAITS FOR THE PRODUCT AUTHORITY.**

*** **THE THREE PROHIBITIONS, AND THEY ARE ABSOLUTE:** ***

1. **YOU REGISTER NO SOURCE — not one row, not a placeholder, not a default, and NOT A TEST
   FIXTURE** (`WO-3-SCOPE` §5.1; `CD-PL-F154` is what happened last time a fixture escaped onto a
   real branch). **Every fixture you write uses obviously-synthetic identifiers** — `PLANT_SYNTH_A`,
   `PLANT_SYNTH_B` — **and you add a check that no synthetic identifier can appear in the shipped
   registry data file.** A test that used `CREDIT_HY_OAS` or `DRTSCILM` as a fixture id would be
   exactly the defect.
2. **YOU DO NOT ACCEPT A COMPUTING `MappingKind` MEMBER.** `WO-3-SCOPE` §5.2: acceptance of the
   first computing member RE-RUNS the `*extra` guard measurement at the then-current head, and that
   measurement is **owed BEFORE the member is accepted**. 16A adds no computing member, so the
   measurement is **not due and must not be quietly spent**. If you find yourself needing one, STOP
   and say so.
3. **YOU DO NOT READ THE INDICATOR LIST OFF ANYTHING.** `PBG-PID-003` and `WO-3-SCOPE` §7.4 by
   name. `/srv/argus/` is on this host and it is **evidence of another product's implementation, not
   authorised intent** — and it does not carry dial bindings, polarities or `x3/x2/x1` tiers anyway.
   **Do not open it. If you do, say so in your return.**

---

## 1. THE LANE, AND WHERE YOU START

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       116c01f  (increment 15 — publication/heartbeat/probe/staleness/health; ASSURED AMBER,
                    BANKED, NOT ACCEPTED)
base      be0b355  (FROZEN — READ-ONLY TO YOU. Build forward; never amend, rebase or move it.)
main      8611685  (carries PID v1.1.1 — you CARRY it, see D1)
```

**WRITABLE SCOPE:** `/srv/crash-detector-wo3` on branch `wo-3` only —
`src/crash_detector/**`, `tests/**`, `contracts/**`, `db/migrations/**`, `deploy/**`, `docs/**`,
`required-tests.yaml`, `PID.md` (carriage only, see D1), and `governance/engineering/build-log/**`
for your own return record.

**PROTECTED — ZERO PATHS TOUCHED, AND YOUR RETURN MUST PROVE IT BY COMMAND:**
`pbg/**` (pinned, read-only, non-waivable) · `BLUEPRINT.md` (`CD-D-115` — you may not amend it;
if 16A needs a Blueprint change, STOP and say so) · `governance/decisions/**` · anything at or
reachable only from `be0b355` · the other worktrees.

**Increment 15 left the register computing (18 criteria, all `UNDECIDABLE`) and 1882 tests passing.
DO NOT REGRESS EITHER. §7 makes both a hard check on your return.**

---

## 2. THE FOUR DELIVERABLES

| # | Deliverable | Authority |
|---|---|---|
| **D1** | **PID v1.1.1 CARRIED onto the lane, and the register RE-PINNED to it** | `PO-DECISIONS-0025` r5 (`Q28`) |
| **D2** | **`detail_level` attaches PER-DIAL, and the guard that was enforced against the wrong option is FIXED** | `PO-DECISIONS-0025` r5 (`Q29`); `CD-PL-F169` |
| **D3** | **The architecture portability constraint MADE TESTABLE — read as DATA, not asserted in prose** | `PO-DECISIONS-0025` r2 (BINDING) |
| **D4** | **The indicator mapping's REGISTRY-DATA CARRIER, with its refusals, shipping ZERO rows** | `PO-DECISIONS-0025` r1/r2/r6; `WO-3-SCOPE` §7.1 |

---

## 3. D1 — THE PID CARRIAGE AND THE RE-PIN. **A CONSEQUENCE, NOT A DISCOVERY.**

The Project Lead executed the `Q28` record act on `main` at `8611685`: `PID.md` §6's `CD-AC-017`
paragraph moves `NEW_REQUIREMENT` -> `DERIVES`, and the document is now **v1.1.1**.

```
main:PID.md   sha256  08baf51ca5a34b4e15be11b4ffe3e4e5ac271291247ace7e8fcabb7b0e8dab9f
lane:PID.md   sha256  538e30f3bf4f1803a89a11ae7b3781febba3752aeb516914e80db6ed15f9621f  (v1.1.0)
required-tests.yaml:76  content_hash: sha256:538e30f3bf4f1803…                          (STALE)
```

*** **THE STALE PIN IS ARITHMETIC AND IT WAS WRITTEN DOWN BEFORE THE EDIT, AT
`BL-20260824T070245Z-0157`. IT IS NOT A REGRESSION AND YOU MUST NOT RECORD IT AS ONE.** *** This is
the same discipline `P3` was given at `BL-20260823T173018Z-0151`, and `CD-PL-F157` is why the
carriage comes first: the register resolves `pid.ref` **relative to its own directory**, so
re-pinning before carrying would pin the hash of a document the lane does not have.

**DO, IN THIS ORDER:**

1. **CARRY, DO NOT RETYPE.** `git show main:PID.md > PID.md` in the lane, then prove carriage by
   command: `git show main:PID.md | cmp - PID.md` must exit **0**, and `sha256sum PID.md` must
   print `08baf51c…`. **A byte-identical carriage, verified by hash, exactly as `D0` was at
   increment 14.**
2. **RE-PIN** `required-tests.yaml`'s `pid.content_hash` to `sha256:08baf51c…`, read from
   `sha256sum` and **never transcribed** (`CD-PL-F36`).
3. **UPDATE THE REGISTER'S OWN DIVERGENCE NOTE.** `required-tests.yaml` around line 3453 records
   *"DIVERGENCE DECLARED RATHER THAN RECONCILED: PID.md line 122 still reads NEW_REQUIREMENT…"*.
   **That divergence is now CLOSED at the PID end.** Rewrite the note to say so and to name
   `PO-DECISIONS-0025` ruling 5 — **do not delete the history of it**; the note earned its place by
   declaring rather than tidying, and a future reader must see that it was closed and by whom.
4. **RE-RUN THE VERIFIER AND RECORD WHAT IT COMPUTES, NOT WHAT YOU EXPECT.** Report
   `pid.content_hash` (MATCHES / MISMATCH), the criteria count, how many are `UNDECIDABLE`, and the
   `GATE` line. **THE GATE WILL ALMOST CERTAINLY STILL READ `SHUT` AND THAT IS THE CORRECT
   OUTCOME** — `latest_admitted_run` is `null` and **you cannot change that** (`PBG-SOD-001`: the
   admitted run is the Assurance seat's to produce). `UNDECIDABLE` is not a pass and must not be
   recorded as progress toward one.
5. **CONTRAST ARM, because a pin that "matches" proves nothing if the check cannot fail:** revert
   the pin in a scratch copy and show the verifier prints `MISMATCH`. Increment 14 established that
   this arm is reachable; show it still is.

**DECLARED CHECK: the census must be UNCHANGED.** The Project Lead measured it after the edit with
the instrument's own function — `derive_pid_census` -> **17**, `CD-AC-017 in census: True`,
`CD-AC-018 in census: False`, `CD-AC-004 in census: True`. **RE-DERIVE IT YOURSELF ON THE CARRIED
FILE.** If it is not 17, or if any of those three answers differs, **the record act changed more
than prose and you STOP and say so.**

---

## 4. D2 — `Q29` IS RULED: `detail_level` ATTACHES **PER DIAL**

`PO-DECISIONS-0025` ruling 5: *"detail_level attaches PER-DIAL."* The mechanism already exists and
is already the right shape — `detail_level_for(reading, *, dial_slot, policy)`, one reading and one
dial slot, with **no variant that takes both dials**, deliberately, because a level derived from
both readings is the `CD-AC-002` shape reached one step sideways. **THE RULING RATIFIES THE SHAPE
THE ENGINEER BUILT. WHAT IS OWED IS THE WIRING.**

**D2.1 — WIRE IT.** `detail_level` goes into `$defs.dial_reading` in **both** closed envelope
schemas (`contracts/public_envelope.schema.json`, `contracts/private_envelope.schema.json`),
**inside the dial object and NOT at envelope top level.** `additionalProperties: false` holds at the
parent **and inside every branch** of the `VALUE | DEGRADED | UNKNOWN` union, so the key must be
admitted in each branch it is to appear in. **The `schema_version` bump is not optional** — the
module's own docstring names the allowlist edit and the bump as *"exactly the friction intended"*.
Pay it once, deliberately, and record it.

**D2.2 — `UNKNOWN` MUST CARRY A LEVEL TOO, AND THAT IS THE POINT.** `PID` §3.2 is constitutional:
*"Missing data must never render as calm."* `detail_level_for` returns `policy.absent_data_level`
for both `Degraded` and `Unknown`, and `DetailPolicy` **refuses construction** when
`absent_data_level` is `calm`. **With zero registered sources every dial reads `UNKNOWN` today, so
in practice this is the ONLY branch that will be exercised in production until 16B lands — and it
is the branch that carries the constitutional guarantee. Make it work first and prove it.**

**D2.3 — THE POLICY'S THRESHOLDS COME FROM THE ENVIRONMENT, NOT FROM A LITERAL IN CODE.** `D3`
binds this: no hardcoded configuration. And say the true thing about them in your declared limit:
**the thresholds are unexercised while every reading is `UNKNOWN`, and they mean nothing until a
dial has a ratified scale (`Q25`/`CD-D-005`).** Do not invent a scale. Do not let an env default
imply one — if a threshold variable is unset, decide deliberately between a refusal and a documented
default, and **state which you chose and why**.

**D2.4 — FIX THE GUARD THAT WAS POINTING THE WRONG WAY. THIS IS `CD-PL-F169` AND IT IS AN
ASSURANCE FINDING AGAINST THE PROJECT LEAD'S OWN RECORD.** `tests/test_detail_level.py`'s
`test_detail_level_is_NOT_on_either_closed_envelope_schema` asserts only

```
assert "detail_level" not in schema["properties"]
assert "detail_level" not in schema["required"]
```

— **top level only. A PER-DIAL attachment PASSES IT UNTOUCHED.** The auditor's words, adopted: the
guard *"is enforced against the rejected option and unenforced against the proposed one."* **REPLACE
IT** with a test that asserts all three of:

* `detail_level` is **absent at envelope top level** in both schemas — the `CD-AC-002` hazard, still
  live, still guarded;
* `detail_level` is **present in `$defs.dial_reading`** in both schemas;
* it is **admitted in every branch of the union**, `UNKNOWN` included.

**AND PROVE IT NON-VACUOUS BY CONTRAST, ON A MUTATED COPY, NOT ON THE REAL FILE:** a copy with
`detail_level` moved to top level must make the test **FAIL**; a copy with it removed from
`dial_reading` must make the test **FAIL**. **A guard whose failing arm was never observed is a
guard nobody has tested.**

**D2.5 — AND THE ONE THING YOU MUST NOT DO:** do not add any function, helper, comprehension or
dict-build that takes both dials' readings and returns one level, one number or one ordering.
`CD-AC-002` is not about the word "blend"; it is about the existence of the function.

---

## 5. D3 — THE PORTABILITY CONSTRAINT, **MEASURED AS DATA AND NOT ASSERTED IN PROSE**

`PO-DECISIONS-0025` ruling 2 is **BINDING**: independent container; SQL **+ Redis** in movable named
volumes; **ALL config via env**; cut-and-paste dev (dell) -> prod (cloud); *"the deploy audit
verifies cut-and-paste reproducibility before go-live."*

**START FROM THE GOOD NEWS, MEASURED BY THE PROJECT LEAD AT THIS BOUNDARY: `deploy/compose.yaml`
IS ALREADY LARGELY COMPLIANT AND YOU ARE NOT REWRITING IT.** One named volume `cd-store-data`;
images by digest; every service's config as `${CD_…:?…}` or `${CD_…:-default}` so an unset variable
is a **refusal** rather than a silent empty string; secrets **by env-var NAME only**; one bind mount
and it is **relative** (`../contracts`), not `/srv/...`; no ARGUS reference anywhere.
**VERIFY THAT YOURSELF — do not take it from this dispatch — and then close the gap, which is that
NONE OF IT IS CHECKED BY ANYTHING.**

**BUILD THE CHECK. It reads `deploy/compose.yaml` AS YAML DATA — never by regex over prose — and
REFUSES:**

| Refusal | Why |
|---|---|
| any **absolute host path** as a bind source (`/srv/…`, `/home/…`, `/mnt/…`, or any path escaping the repository) | a dell path in the file is the cut-and-paste failing |
| any **durable data outside a named volume** | a bind-mounted database directory does not travel |
| any **hostname or IP literal** other than the declared loopback publication binds | `CD-HOLD-005` keeps those two, deliberately; anything else is a host baked in |
| any **`argus`/`ARGUS` reference** in any form | `PO-DECISIONS-0025` r2: no ARGUS coupling |
| any **config value that is a literal where it should be an env reference** | ruling 2: ALL config via env |
| any **secret-looking value** (as opposed to an env-var NAME) | `PBG-SEC-002`, non-waivable |

**EVERY ARM PLANTED AND CONTRASTED.** For each refusal: a **clean** arm over the real file exiting
**0**, and a **violated** arm over a **mutated copy** exiting **non-zero** — *"the same declared
command exiting 0 on the clean subject and non-zero on the violated one"* (`required_evidence`). **A
clean arm that fails proves only that the harness is broken, and a broken harness detects nothing.**
**Mutate a COPY. Never plant in the real file** — that is how `CD-PL-F154` happened.

*** **AND ONE THING YOU MUST NOT SILENTLY DECIDE: THERE IS NO REDIS IN THIS DESIGN AT ALL.** ***
`grep -rin redis src/ deploy/ db/ contracts/` returns **nothing**. The ruling's architecture
sentence names Redis; `BLUEPRINT` §2's container set does not contain it, and it has no declared
purpose, no role in the grant matrix, and no egress posture. **DO NOT ADD IT** — a service with no
declared purpose is worse than an absent one, and adding one to `BLUEPRINT` §2 is a Product Owner
act (`CD-D-115`). **DO NOT QUIETLY OMIT IT EITHER.** It is raised as `Q31`; your job is to make the
SQL half testable and to **state Redis's absence in your return as an open question, not as a
finished state.**

---

## 6. D4 — THE REGISTRY-DATA CARRIER. **THE MAPPING IS DATA. SHIP IT EMPTY.**

`PO-DECISIONS-0025` r2: *"The mapping lives as REGISTRY DATA, portable by construction."* Today
`SourceRecord` carries `source_id`, `adapter_id`, `cadence_seconds`, `criticality`, `stands_for` —
and **NOT** the four fields the ruling adds: **dial binding, polarity, provisional tier, staleness
window**, nor the **provenance** that `CD-D-005` requires. **D4 IS THAT CARRIER.**

**D4.1 — THE RECORD.** Extend `source_registry.py` (or add a companion module beside it — your
call, `PBG-AUTH-005`, and justify it) so one registered indicator carries, in addition to what it
carries today:

* **`dial_bindings`** — one entry per bound dial, each entry carrying **the dial** and **its own
  polarity**. *** **A `BOTH` INDICATOR IS TWO BINDINGS WITH TWO POLARITIES, NEVER ONE BLENDED
  BINDING.** *** `PO-DECISIONS-0025` r7: two dials NEVER blended.
* **`provisional_tier`** — `x3 | x2 | x1`, and **the type must carry the word PROVISIONAL**, because
  ruling 3 says these are starting values calibrated by backtest and **trusted on no assertion**. A
  bare float named `weight` would launder a provisional number into an authoritative one.
* **`staleness_window`** — declared **per indicator, never global** (`PO-PRODUCT-0001` R2). Reuse
  `staleness.py`'s existing `StalenessWindow`; **do not build a second mechanism beside it** — read
  what is there first (596 lines, and `regime` already appears in it).
* **`provenance`** — the `CD-D-005` authority trail: which ruling admitted this row, which mapping
  artefact and version it came from. **An unexplained mapping cannot be admitted** (doctrine §3.6);
  `stands_for` is *"the admission ticket, not documentation."*
* **`wiring_state`** — `WIRED | PENDING`. SLOOS's NDFI leg is manual-quarterly and will be `PENDING`
  for real. **`PENDING` MUST NEVER RENDER AS GREEN OR CALM** (ruling 4) — make that a refusal, not a
  convention.

**HOLD THE EXISTING DISCIPLINE, WHICH IS NOT NEGOTIABLE ON THIS LANE:** `@establishes(...)`,
`__slots__` (sealed, `PO-DECISIONS-0016` r2), `own_str` re-establishment before any value is
compared or hashed, and **exact type and never `isinstance`** on every enum and numeric limb.
`source_registry.py:174-200` records why in measured detail: **an `enum` CPython refuses to
SUBCLASS can still be WORN, because `isinstance` consults `__class__`** — and that exact forgery was
**live and admitted** at `ids_with` until increment 10. **Your new enums are new doors of the same
kind. Plant the `__class__`-property forgery against every one of them and show it REFUSED.**

**D4.2 — THE REFUSALS, EACH WITH BOTH ARMS.** Registration is refused when: a binding names two
dials at once, or two bindings are collapsed into one score; a bound dial has **no** polarity; the
staleness window is missing, zero or negative; the tier is outside `{x3, x2, x1}`; provenance is
absent or empty; a `PENDING` row is asked to render as a value. **And the admitting arm for each,
because a carrier that refuses everything satisfies every invariant vacuously** — the third-arm
discipline increments 12 and 13 established.

**D4.3 — WIDE WINDOWS ARE NOT A BUG.** Ruling 6: private credit stress takes a **WIDE** staleness
window *"because its latency IS the point — absence reads Unknown, never calm."* If
`staleness.py`'s `StalenessWindowOutOfRange` has an upper bound that would refuse a quarterly or
multi-month window, **say so and do not widen the bound on your own inference** — report it, because
a bound chosen for a market feed being applied to a quarterly survey is a real finding either way.

**D4.4 — THE DATA FILE SHIPS WITH ZERO ROWS, AND THAT IS THE DELIVERABLE.** A portable registry
data file, loaded by a loader, validated by the refusals above, **containing no indicator**. Its
header states that the rows are `Q30` and names what is owed. `EMPTY_SOURCE_REGISTRY` is the
precedent and its docstring is the model: *"WO-2 REGISTERS ZERO SOURCES, and that is the
deliverable, not a gap."*

**D4.5 — *** AND THE CARRIER MUST BE CALLED. THIS IS THE FOURTH-TIME-NAMED PATTERN AND YOU ARE THE
SEAT THAT DOES NOT REPEAT IT. *** ** `CD-PL-F170`, and the headline increment 12 returned: **"THE
CONTROLS EXIST AND NOTHING RUNS THEM."** `CD-PL-F167` is the live instance — `publish_cycle` has a
writer and **zero callers**. **DO NOT ADD A FIFTH.** The loader must be reached from the path that
already runs: `ConfigSnapshot` carries the `SourceRegistry` today, so the mapping travels in the
same snapshot and is exercised by the same dial evaluation. **Prove it end to end: with the shipped
zero-row file, every dial reads `UNKNOWN` and `detail_level` renders `absent_data_level` — never
`calm`.** If you write a function this increment that nothing calls, **name it yourself in your
return before an auditor does.**

---

## 7. WHAT IS *NOT* IN 16A, AND WHY — **SO YOU DO NOT HELPFULLY BUILD IT**

| Not in scope | Why |
|---|---|
| **any indicator row** | `Q30`. 16B. |
| **the `src/` entrypoint / the caller for `publish_cycle` (`CD-PL-F167`)** | *** **DELIBERATE, AND THE REASON IS A LIVE DEFECT.** *** The increment-15 auditor found the health surface's **value axis OPEN** — a dial magnitude, a source name and a witness verdict all ride through an ALLOWED key and pass `refuse_unless_health_safe`. **It is not a live breach today ONLY because nothing serves it, and it BLOCKS THE MOMENT ANY TRANSPORT IS WRITTEN.** The two residuals are wired together and **neither may land alone**. Writing the caller in 16A would open the breach. |
| **`CD-AC-017` / `CD-AC-018`** | increments 17 and 18, and both need real registered sources. |
| **backtest weight calibration** | its own later increment (ruling 3). |
| **Redis** | `Q31`. See §5. |
| **any `BLUEPRINT.md` edit** | `CD-D-115`. STOP and say so instead. |
| **any `pbg/` edit** | pinned, read-only, non-waivable. Including `CD-PL-F171` (`pbg log validate` returns a green about nothing) — **reported, not repaired, and not yours.** |
| **the coordination discipline** | PARKED. No WO-3 increment may reach for it or quietly fix a residual inside it. |

---

## 8. YOUR RETURN — `READY_FOR_ASSURANCE`, AND WHAT MUST BE IN IT

**BOOT FIRST** (`PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot`) and **declare the verdict you
actually get, including a `RED`.** Increment 14's Engineer booted `RED` on an inherited
`continuity_record_commit: PENDING` outside its scope and **said so rather than netting it off
against a clean result.** Do that.

**REQUIRED IN THE RETURN:**

1. **Every claim about code measured by a command whose output you paste.** *** `CD-PL-F170` names
   this pattern **four times** on this project — `F158`, `F161`, `F165`, `F168` — always the same
   shape: **a partial measurement promoted to a confident statement about code and placed in a
   binding record.** The measurements held up; **the summarising sentences ran ahead of them.** One
   of the four was a seat printing `args` and never reading `kwonlyargs`. *** **Read the whole
   signature. Read the whole file. Then write the sentence.**
2. **Test counts and results, before and after**, with the command. **No regression from 1882.**
3. **The register verifier's output, whole** — pin status, count, `UNDECIDABLE` count, `GATE` line —
   **and the contrast arm.**
4. **Every plant with BOTH arms shown**, clean exiting 0 and violated exiting non-zero, and the
   third admitting arm wherever a refusal could be vacuous.
5. **A scope proof by command:** `pbg/` at **0 paths touched**, `BLUEPRINT.md` at **0**,
   `governance/decisions/` at **0**, `git rev-parse wo-2r3` -> `be0b355…` **UNMOVED**, porcelain
   clean, **ONE commit identity** (`CD-ENG-WO3-03` and no other — `CD-RULE-002`, and `CD-PL-F154` is
   what happens when that slips).
6. **A grep proving no indicator was registered**: no real series identifier, no real indicator
   name, no `DRTSCILM`, no `NDFI`, in `src/`, `tests/`, `contracts/` or any data file. **And state
   whether you opened `/srv/argus/` at all.**
7. **YOUR DECLARED LIMITS (`CD-RULE-004`)** — what you did **not** verify, what rests on a double
   rather than a live PostgreSQL, and what you believe is true but did not measure. **The record has
   been damaged four times by confident sentences and never once by a declared limit.**
8. **FINDINGS AGAINST THIS DISPATCH.** The last four seats each found real errors in their own
   instructions and **three of them were right and the Project Lead was wrong** (`CD-PL-F160`,
   `CD-PL-F161`, `CD-PL-F168`). **If a deliverable here is wrong, unbuildable, or would break
   something, REFUSE IT AND SAY WHY. That is the return this dispatch wants most.**

**YOU DO NOT CERTIFY YOUR OWN WORK.** A separate fresh Assurance seat goes over your tip
(`PBG-SOD-001`, non-waivable). **Your own test runs are implementation evidence, never assurance.**

**COMMIT AT EVERY BOUNDARY.** A result that exists only in your conversation is not project state
(`PBG-CONT-007`).

**STOP AND RETURN — do not improvise — if:** a deliverable requires naming an indicator, a dial
binding, a polarity or a tier · a deliverable requires a `BLUEPRINT` amendment · the census is not
17 after the carriage · you cannot make a plant's clean arm pass · you find that any statement in
this dispatch is false.
