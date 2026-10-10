# CD-DISPATCH-INC16B-FIX-ENGINEER

**role source:** `pbg/roles/engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `CD-ASR-WO3-05`'s `AMBER` verdict at `ca85d8e`
(`BL-20260824T104431Z-A305.yaml`, branch `asr-wo3-05-verdict`), findings **F1, F2, F3, F6** ·
reproduced independently by the Project Lead at `BL-20260824T105209Z-0164` ·
`PO-DECISIONS-0026` ruling 9
**seat identity:** `CD-ENG-WO3-06` — **FRESH.** **Never `CD-ENG-WO3-05` (which built the
instrument you are repairing)**, **never `CD-ASR-WO3-05` (which found the holes — `PBG-SOD-004`)**,
never `CD-ENG-WO3-01`/`-02`/`-03`/`-04`, never `CD-ASR-WO3-01`/`-02`/`-03`/`-04`, never any
`CD-ENG-WO2R3-*` or `CD-ENG-COORD*`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **increment:** 16B-FIX · **expected return:**
`READY_FOR_ASSURANCE`

---

## 0. WHAT THIS IS, IN ONE PARAGRAPH

16B built a register-wired instrument for the constitutional clause, and **it works** — the register
now moves on four regression shapes it was blind to before. **Then an independent seat broke it
three ways, and one of those breaks is invisible to the entire register.** You are closing exactly
those three, plus one declaration the Project Lead has ruled on. **You are not redesigning the
instrument.** Its architecture — drive the live gate, enumerate the vocabulary from the contract
rather than typing it in — was validated by measurement and you keep it. **Every one of your fixes
has already been prescribed by the auditor, in the auditor's own words, with the line deliberately
left unwritten. Your job is to write those lines and prove they bite.**

---

## 1. THE LANE

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       cbb81d1  (increment 16B — assured AMBER at ca85d8e, banked, NOT accepted)
base      be0b355  (FROZEN — READ-ONLY. Build forward; never amend, rebase or move it.)
verdict   ca85d8e on branch asr-wo3-05-verdict — governance/engineering/build-log/BL-20260824T104431Z-A305.yaml
ruling    governance/decisions/PO-DECISIONS-0026.md (in the lane)
```

**READ `BL-20260824T104431Z-A305.yaml` IN FULL BEFORE YOU WRITE ANYTHING.** It carries every tree,
every command and every prescription. This dispatch summarises it; **it does not replace it.**

**WRITABLE SCOPE:**

* `tools/register/check_missing_data_never_calm.py`
* `contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`
* `required-tests.yaml` — **only** the `CD-AC-001` block (the new row's entry and comment, and
  `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s declared-limit comment for FX4)
* `plants/WO3-INC16B/**` — you are **adding** arms, not editing C1–C5
* `governance/engineering/build-log/**` — your own return record

**PROTECTED — ZERO PATHS, PROVED BY COMMAND ON RETURN:** `pbg/**` · `BLUEPRINT.md` · `PID.md` ·
`governance/decisions/**` · `governance/mapping/**` · **both envelope schemas — you are fixing the
instrument that judges them, not them** · `src/**` · `deploy/**` · `db/**` · `tests/**` (**see FX4:
the auditor's F6 is closed by a DECLARATION, not by editing a test**) · `tools/**` except your one
file · `evidence/**` (**writing there is forging your own assurance**) · everything at `be0b355`.

---

## 2. THE ROOT CAUSE, IN ONE SENTENCE, AND IT IS THE AUDITOR'S

*** **The instrument enumerates surfaces, slots and levels FROM THE CONTRACT — which is why it
survives a rename, a reorder and a symmetric fourth level — but it HARD-CODES THE DOCUMENT SHAPE,
so a branch or a slot it did not write is a branch or a slot it cannot drive.** ***

**Fix the root cause. Three symptom patches would leave the fourth shape open.**

---

## 3. FX1 — THE ONE THAT MATTERS: ENUMERATE THE `oneOf` BRANCH SET (auditor F1)

**REPRODUCED BY THE PROJECT LEAD, WITH ITS CONTROL.** Append a fourth branch
`dial_reading_unknown_hinted` to `#/$defs/dial_reading.oneOf` on both contracts — a copy of the
`UNKNOWN` branch whose `detail_level` points at the **full** `#/$defs/detail_level`, requiring a
marker property `render_hint` that is also added to the parent `dial_reading.properties` so the
parent closure admits it. **No new ROOT key**, so `check_schema_closed`'s root allowlist never
fires. Measured:

```
check_missing_data_never_calm.py --root .   ->  PASS — 67 assertions, 0 violations
check_schema_closed.py --root .             ->  PASS — 304 assertions, 0 violations
pytest tests/test_detail_level.py -q        ->  52 passed
(auditor, all 30 execute: lines)            ->  diff against clean is EMPTY

live gate, UNKNOWN + detail_level="calm" + render_hint="COMPACT":
        PUBLIC   *** ADMITTED — an UNKNOWN dial rendering as CALM ***
        PRIVATE  *** ADMITTED ***
CONTROL, identical probe on the CLEAN tree:
        PUBLIC   REFUSED [SCHEMA_VIOLATION] at /equity_crash: matches none of the …
        PRIVATE  REFUSED
```

*** **A TREE ON WHICH THIS PRODUCT PUBLISHES THE ONE DOCUMENT ITS CONSTITUTION FORBIDS, AND NOT ONE
LINE OF THE REGISTER MOVES.** THAT IS THE DEFECT CLASS 16B EXISTS TO CLOSE, REBUILT ONE LEVEL UP,
AND IT IS THE FIFTH RECORDED INSTANCE ON THIS PROJECT. ***

**BUILD (the auditor's prescription, and you may better it but not skip it):** after the slots are
enumerated, resolve `schema["$defs"]["dial_reading"]["oneOf"]`; **for every branch whose
`properties.state.const` is in `ABSENT_STATES`, build a minimal instance from THAT BRANCH'S OWN
`required` + `properties`** and assert `calm` is REFUSED and the admissible levels are ADMITTED.
**And add the structural half: assert the resolved branch set equals a declared allowlist, so a
branch nobody anticipated is a violation for being UNRECOGNISED rather than a silence.** That
deny-by-default shape is `RULE F`'s, already established on this project by
`check_no_numeric_default`.

---

## 4. FX2 — THE ROW STATES SOMETHING THAT IS NOT TRUE (auditor F2)

**REPRODUCED BY THE PROJECT LEAD.** Drop `detail_level` from the `required` list of
`dial_reading_unknown` and `dial_reading_degraded` on both contracts, leaving the `$ref` narrowing
fully intact:

```
check_missing_data_never_calm.py --root .   ->  PASS — 67 assertions, 0 violations
live gate  ->  ADMITS an UNKNOWN dial with NO detail_level key at all, both surfaces
```

**That mutation is a NAMED MEMBER of this row's own negative-control class**, in
`required-tests.yaml` and again in the execution contract, under a sentence that reads *"The
instrument fails on all of these."* **IT DOES NOT FAIL. A governed artefact says something
measurably false, and this project supersedes rather than deletes.**

*** **AND THE PART THAT SHOULD STING: THE INSTRUMENT IS STRICTLY WEAKER THAN THE MEMORIAL IT WAS
BUILT TO SUPERSEDE.** `tests/test_detail_level.py` has always asserted that a missing-data branch
carrying **no level** and one carrying an **off-vocabulary** value are both REFUSED, and
`CD-ASR-WO3-04`'s 30-row probe covered both. **Both rows were dropped when the property moved into
the register-wired instrument.** A replacement that quietly narrows what it checks is how a guard
becomes a certificate. ***

**BUILD:** add to `_expectations` a **field-absent** row (`level=None`, key omitted) and one
**off-vocabulary** row (e.g. `"banana"`), both `MUST REFUSE`, for every absent-data state on every
slot on both surfaces. `_dial()` already takes `level` and needs only to omit the key when it is
`None`. **`CD-CALM-PAIRED-004`'s one-pointer diff still holds for the off-vocabulary row; for the
absent row it needs a stated exception — state it, do not silently exempt it.** Then the
negative-control sentence becomes true, and **say in the record that it was false and now is not**.

---

## 5. FX3 — `DECLARED LIMIT 4` IS FALSE AS WRITTEN, IN ALL THREE PLACES (auditor F3)

It promises *"a third surface or a third dial added tomorrow is driven on the day it is added."*
The slot enumerator requires `sub.get("$ref") == "#/$defs/dial_reading"` **exactly**, so an
**optional** third slot spelled with any other `$ref` is invisible — auditor tree `E1`, instrument
`PASS 67/0`, gate ADMITS `credit_stress` carrying `calm` on both surfaces.

**The exposure is narrow and the auditor said so honestly** — `check_schema_closed` catches `E1`
(`UNDECLARED KEYS PRESENT: credit_stress`), and a *required* third slot in any spelling is caught by
the instrument itself. **THAT IS NOT THE POINT. THIS PROJECT GRADES THE DECLARATION.** A limit that
promises what the code does not do is the defect, whatever else happens to cover it.

**BUILD:** restate limit 4 truthfully — *"every top-level property whose value is literally
`{"$ref": "#/$defs/dial_reading"}`"* — **in all three places `CD-RULE-004` requires it** (the
instrument header, the `required-tests.yaml` comment, the execution contract), **and** add the
fail-closed assertion the auditor prescribed: the enumerated slot set must equal the contract's
dial-bearing root properties **under any spelling**, or the check fails. **Correct by supersession:
say what it said, that it was false, and what is true instead.**

## 5.1 — FX3 IS NOT AN INVITATION TO SUPPORT A THIRD DIAL

`PO-DECISIONS-0026` standing: **two dials, never blended.** You are making the enumerator honest
about what it drives, **not adding a third dial slot to anything.** If closing FX3 seems to require
a product decision about dial count, **stop and say so** — that is the Product Authority's.

---

## 6. FX4 — THE PROJECT LEAD'S RULING ON F6 (this one is a DECLARATION, not a code change)

The auditor measured that `D3`'s additive growth imported **name-coupled brittleness** into the
register: a pure refactor with zero behavioural change (`absent_data_detail_level` renamed, enum
reordered, `$defs` reversed) leaves the instrument at `PASS 67/0` — **which vindicates the
behavioural design** — but fails six assertions in `tests/test_detail_level.py`, which the register
now runs. It offered two ways out and correctly called it a Project Lead judgement.

*** **RULED: ACCEPT THE COUPLING AND DECLARE IT. DO NOT EDIT THE TESTS.** *** The reason is on the
record and you may contest it: **`absent_data_detail_level` is not an implementation detail on this
project — both contracts' own prose names it as the enforcement point for a constitutional clause.**
A rename that silently repoints it is exactly the change that *should* require someone to open the
register and think. **Loosening the assertion to follow the `$ref` would buy refactor comfort with
constitutional visibility, and that is the wrong trade at this criterion.**

**BUILD:** one declared-limit paragraph on `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s grown command,
recording that the command is now **name-coupled by design**, what a pure rename costs, and that
the cost is **priced and not accidental**. **If you think the ruling is wrong, say so in your
findings and follow it anyway.**

---

## 7. YOUR CONTRAST SET — THE AUDITOR'S TREES BECOME PERMANENT PLANTS

Under `plants/WO3-INC16B/`, **added alongside C1–C5, which you do not touch**, in the established
`MANIFEST.md` table form with **`git apply`'s own exit code as its own column** and **every arm from
its own pristine `git archive | tar -x` extraction, never the worktree** (`CD-PL-F154`):

| # | Arm | Your instrument MUST |
|---|---|---|
| **C6** | the 4th-`oneOf`-branch tree (auditor `E3`) | **FAIL** |
| **C7** | `detail_level` dropped from `required`, both absent branches (auditor `E2`) | **FAIL** |
| **C8** | an absent-data branch carrying an off-vocabulary level | **FAIL** |
| **C9** | the optional third slot with an unusual `$ref` (auditor `E1`) | **FAIL** |
| **C10** | *(control, MUST STILL PASS)* the symmetric fourth-level amendment (auditor `F3` tree): `critical` added to `DETAIL_ORDER` **and** to both enums | **PASS** |

**C10 IS NOT OPTIONAL AND IT IS NOT A FORMALITY.** The auditor measured the current instrument at
`PASS — 81 assertions, 0 violations` on that tree. **If your fix breaks C10, you have replaced a
vocabulary-driven table with a hard-coded one and thrown away the best property this instrument
has.**

**And re-run C1–C5 unchanged.** A fix that quietly stops an existing arm from biting is a
regression, and this project has recorded a plant silently ceasing to apply before
(`CD-ENG-WO2R3-06-F06`).

---

## 8. WHAT IS NOT IN THIS INCREMENT

**Auditor F4 / `CD-PL-F180` — the contract bytes.** The auditor found a **third** route to an
admitted calm-over-unknown needing **no environment variable**: `load_envelope_schema` re-reads the
contract on every call with no cache, and the deployed files are writable by the service account, so
an in-place rewrite flips `REFUSED → ADMITTED` mid-process with `DECLARED LIMIT 1`'s precondition
satisfied. **PROJECT LEAD RULING: that is `16D`, and the auditor's correction is adopted — 16D is
scoped to THE CONTRACT BYTES THE GATE LOADS AT PUBLISH TIME, not to `$CD_CONTRACTS_DIR`.** The
auditor also ruled, both limbs argued, that **exit 3 is the right behaviour** for your instrument
and that the scheduling is right. **DO NOT TRY TO CLOSE IT HERE. Do not change exit 3.**

Also not yours: the three-quantity staleness model and `STALENESS_WINDOW_CEILING_SECONDS` (16C) ·
the structural closure of the no-blend guard, the host-coupling defaults and the version
discrimination (16D) · **registering any indicator row from `governance/mapping/indicator_mapping.yaml`
(16E)** · `publish_cycle`'s missing caller · anything under `pbg/`.

**Note for your own orientation, not an action:** the auditor established that **there are no
envelope builders in `src/` and `publish_cycle` has zero callers**, so "the shape the product really
publishes" is *defined by the contracts and by nothing else* at this commit. That is why FX1 matters
so much: **the contract's `oneOf` branch set IS the published shape, so a branch you do not drive is
a shape you do not guard.**

---

## 9. YOUR RETURN

**BOOT FIRST** and declare the verdict, including the inherited `RED` from the frozen base's
`ACTIVE_WORK.yaml` — known, verified by two seats as byte-identical to `be0b355`, **diagnose and do
not repair.**

Required, each backed by a command whose output you paste:

1. **C6–C9 each FAILING**, with the violation codes, and **C10 PASSING**.
2. **C1–C5 re-run and unchanged.**
3. The instrument at exit **0** on the clean worktree, with its new assertion count.
4. `pytest tests/ -q` — **no regression from 2007**.
5. The register verifier: `pid.content_hash MATCHES` · **18** criteria · `GATE: SHUT` ·
   `latest_admitted_run (null)`.
6. **The superseded sentences, quoted**: the false negative-control clause (FX2) and the false
   limit 4 (FX3), each with what it said, that it was false, and what is true instead.
7. A scope proof by command over every protected path in §1.
8. **ONE commit identity**, `git log --format='%an' cbb81d1..HEAD | sort -u`.
9. **Your declared limits (`CD-RULE-004`)** — including any NEW limit your fix introduces.
10. **Your findings against this dispatch.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ENG-WO3-06 GIT_AUTHOR_EMAIL=cd-eng-wo3-06@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-06 GIT_COMMITTER_EMAIL=cd-eng-wo3-06@seats.crash-detector.invalid \
git commit -m "..."
```

**COMMIT AT EVERY BOUNDARY** (`PBG-CONT-007`). **YOU DO NOT CERTIFY YOUR OWN WORK** — a separate
fresh Assurance seat follows (`PBG-SOD-001`, non-waivable).

**STOP AND RETURN — do not improvise — if:** a fix needs a file outside §1 · FX1's branch
enumeration cannot be made to keep C10 passing · FX3 turns out to need a product decision on dial
count · you conclude the FX4 ruling is wrong in a way that changes what you must build · **or you
find any statement in this dispatch to be false.** *** **THE LAST TWO DISPATCHES ON THIS LANE EACH
CONTAINED A FALSE STATEMENT THAT A SEAT CAUGHT — `CD-PL-F181` AND `CD-PL-F185`, BOTH AGAINST THE
PROJECT LEAD, BOTH CONFIRMED. ASSUME THIS ONE DOES TOO.** ***
