# CD-DISPATCH-INC16B-FIX5-ENGINEER

**role source:** `pbg/roles/engineer.md` — reading it does not grant the role (`PBG-BOOT-001`),
**this dispatch does**.
**authority record:** `CD-ASR-WO3-09`'s `RED` at `a74705c` (`BL-20260824T144449Z-A309.yaml`, branch
`asr-wo3-09-verdict`) · **`PO-DECISIONS-0027`** (committed `c1e45ba`, `governance/decisions/`),
**rulings 1, 5 and 6** · `PO-DECISIONS-0026` ruling 10
**seat identity:** `CD-ENG-WO3-10` — **FRESH.** **Never `CD-ENG-WO3-09` (which built what you are
correcting)**, **never `CD-ASR-WO3-09` (which found the defect — `PBG-SOD-004`)**, never
`CD-ENG-WO3-01`…`-08`, never `CD-ASR-WO3-01`…`-08`.
**issued by:** `PROJECT_LEAD_SEAT_03` · **increment:** 16B-FIX-5 · **expected return:**
`READY_FOR_ASSURANCE`

---

## 0. READ THIS FIRST: YOU ARE NOT REPAIRING A FAILURE. YOU ARE FINISHING A FIX THAT WORKS.

**The `RED` you are acting on is a `RED` the Product Owner has ruled a VALIDATION.** `FX12`, the
class inversion your predecessor built, is **kept**. It is not reverted, not narrowed, and not
suspected. Measured by the auditor, on the record:

```
THE FALSIFIER PASSED     spellings on NO LIST are caught — an invented `propertys` typo,
                         the auditor's `zzSlotUnion` and `dependentRequiredSchemas`;
                         all three `grep -c` ZERO in the instrument
C24 / C25 CLOSED         the two escapes that survived the ENTIRE 30-line register GREEN
31 OF 33 INERT MEMBERS   tested by the auditor and found sound
NOTHING CORRECT BROKEN   C16 PASS 144 · C10/C28 PASS 158 · C1-C21 all still bite
```

**FIVE ROUNDS OF SPELLING PATCHES NEVER ACHIEVED THAT AND THE CLASS INVERSION DID.**

The defect is **one sentence wide**, and `PO-DECISIONS-0027` ruling 6 names it:

> *** **THE DENY CLASS IS A TRUE COMPLEMENT OF A FINITE WRITTEN SET OVER KEY NAMES, AND IT NEVER
> QUANTIFIES OVER WHAT A READABLE KEY'S VALUE ASSERTS.** ***

**The quantifier is right. The alphabet is wrong.** That is the whole of your first item, and
`PO-DECISIONS-0027` ruling 6 calls it *"the last structural step"*.

*** **AND RULING 5 IS BINDING ON HOW YOU WILL BE GRADED, SO READ IT BEFORE YOU WRITE A LINE.** ***
The Product Owner has **abolished the shape census**. You are not graded on how many named shapes
you close. You are graded on **ONE structural completion condition**, stated in §5 below. A fix that
closes the enum/const shape and cannot prove the completion condition **has not finished this
increment**, and a fix that proves the completion condition is **done even though the auditor will
attack it again** — ruling 5, verbatim: *"If a further named escape is found after this test is
green, the test was wrong, not the guard incomplete."*

---

## 1. THE LANE

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       dd40407  (16B-FIX-4 — assured RED at a74705c, banked, NOT accepted; content tip 4e6f7c4)
base      be0b355  (FROZEN — READ-ONLY. Do not touch it, do not rebase onto it, do not check it out)
verdict   a74705c on branch asr-wo3-09-verdict — BL-20260824T144449Z-A309.yaml — READ IT IN FULL
ruling    governance/decisions/PO-DECISIONS-0027.md at c1e45ba on main — READ IT IN FULL
```

**WRITABLE SCOPE:** `tools/register/check_missing_data_never_calm.py` ·
`contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md` · `required-tests.yaml` (**`CD-AC-001`
block only**) · `plants/WO3-INC16B/**` (**adding** arms; **C1–C28 untouched**) ·
`governance/engineering/build-log/**` for your own return, on the lane.

**PROTECTED — ZERO PATHS, PROVED BY COMMAND:** `pbg/**` · `BLUEPRINT.md` · `PID.md` ·
`governance/decisions/**` · `governance/mapping/**` · **both envelope schemas** · `src/**` ·
`tests/**` · `deploy/**` · `db/**` · `tools/**` except your one file · `evidence/**` · `be0b355`.

**`CD-D-181` SEQUENTIAL-ONLY.** You are the only seat running. There is no parallel seat and you
must not spawn one.

---

## 2. FX15 — THE ALPHABET CORRECTION. THE PRESCRIPTION IS THE AUDITOR'S AND IT IS CARRIED VERBATIM.

**THE ESCAPE, REPRODUCED BY THE AUDITOR AND INDEPENDENTLY BY `PROJECT_LEAD_SEAT_02` ON ITS OWN
PLANT.** Declare the liveness dial as:

```
"feed_liveness_reading": {"enum": [ <a LIVE reading>, <a STALE reading whose detail_level is "calm"> ]}
```

with the root property `$ref`-ing it. **No applicator keyword anywhere.** Measured:

```
instrument            PASS — 144 assertions, 0 violations
live gate PUBLIC      *** ADMITTED — a DEAD FEED rendering as CALM ***
live gate PRIVATE     *** ADMITTED ***
```

**WHY IT ESCAPES, AND THE LINE NUMBERS ARE GIVEN SO YOU CAN CHECK THIS SEAT RATHER THAN BELIEVE
IT.** In `_dial_bearing`, the `declared` set is built at **lines 1240–1250** from **three keywords
only** — `properties` keys, the `required` list, `dependentRequired` values. `enum` and `const` are
members of `_INERT_KEYWORDS` (**line 1102**), therefore members of `_READABLE_KEYWORDS`
(**line 1123**), therefore the node at line 1216 has **no unreadable keyword**, therefore
`undecidable` stays `False`, therefore the walk returns a **clean `False`**: *not a dial*. **Silent.**

*** **`enum` AND `const` ARE CORRECTLY INERT AS APPLICATORS AND ARE NOT INERT AS PROPERTY
DECLARATIONS. THEY CARRY NO SUBSCHEMA — WHICH IS WHY THEY ARE ON THE INERT LIST AND WHY THEY BELONG
THERE — BUT THEIR VALUE NAMES PROPERTIES.** ***

**BUILD — and the direction is the auditor's MEASURED prescription, carried into this dispatch
verbatim by `PO-DECISIONS-0027` ruling 6:**

> **READ `enum` / `const` OBJECT VALUES INTO THE DECLARED SET. DO *NOT* MOVE THEM OUT OF
> `_INERT_KEYWORDS`** — the auditor **measured** that removing them **explodes the false-positive
> tail.

*** **THAT SECOND SENTENCE IS A PROHIBITION AND NOT A PREFERENCE.** *** Making `enum`/`const`
unreadable would make every schema in the tree that carries a plain `{"type": "string", "enum":
[...]}` undecidable, and the auditor priced it. **If you believe the measurement is wrong, STOP AND
RETURN — do not act on your disagreement.**

**THE LINE IS DELIBERATELY UNWRITTEN.** The auditor left it unwritten on `PBG-SOD-001` /
`PBG-SOD-004` grounds and this dispatch honours that. You are given the **defect**, the **bound**
and the **forbidden move**. **The implementation is yours and you own it.**

**Two things this seat could not settle by reading, and names as YOUR calls to make and to declare:**

- **Depth.** An `enum` member is an arbitrary JSON value and may nest — `{"enum": [{"a": {"state":
  ...}}]}`. Whether you collect names at the member's top level only, or walk the member, is a
  decision with a false-positive price. **Whichever you choose, DECLARE IT and price it.** The
  ruled direction when in doubt is unchanged and is the constitution's: *a false positive costs one
  seat one look at one contract; a false negative costs the constitution.*
- **`const`.** A `const` may be a non-object scalar, in which case it names nothing. Say so
  explicitly rather than leaving it inferred.

---

## 3. FX16 — A309-F2: THE BRANCH RECOGNISER HAS NO INVERSION AT ALL. THIS IS THE SAME DEFECT IN A SECOND PLACE.

**MEASURED BY THE AUDITOR, NOT SUSPECTED BY THIS SEAT.** `FX12` was applied at the **root-property**
recogniser only. `_branch_states` (**line 1301**) reads, at **lines 1322–1329**:

```
resolved["properties"]["state"]["const"]     — and NOTHING ELSE
```

No readability test. No `_READABLE_KEYWORDS`. No undecidable outcome — a branch it cannot read
yields `state = None` and the walk continues as though it had looked.

*** **TWO RECOGNISERS IN ONE FILE NOW DISAGREE ABOUT WHAT "READABLE" MEANS. THAT IS ONE EDIT FROM A
HOLE AND THE AUDITOR SAID SO IN TERMS.** ***

**BUILD:** the branch recogniser gets the **same inversion** as the root recogniser — a branch whose
keywords it cannot fully read is **UNDECIDABLE AND REPORTED**, never silently `state = None`. **The
two recognisers must end this increment agreeing on what "readable" means**, and you must state in
your return **how you proved they agree** — a shared constant, a shared helper, or an argued case.
**A comment asserting they agree is not a proof.**

**THIS SEAT DISCLOSES ITS OWN JUDGEMENT HERE RATHER THAN BURYING IT.** `PO-DECISIONS-0027` ruling 5
forbids a fix that *"adds a shape to a denylist"*. This item adds **no shape**; it applies the
**same class fix in a second location**, and the completion condition in §5 is **not provable while
one of the two recognisers has no inversion**. That reasoning is recorded at
`BL-20260824T150127Z-0172` and **the Product Authority may yet rule it out of scope.** If it does,
this item drops and §5 stands alone.

---

## 4. FX17 — `DECLARED LIMIT 14` IS A SAMPLE PRETENDING TO BE A CLASS (`CD-PL-F200`)

The declared false-positive tail **enumerates six shapes**. The auditor **found a seventh in a
minute**. A limit that lists instances of a class, in a file whose entire thesis is *guard the class
and not the instance*, is the same error the code just fixed, written in prose.

**BUILD:** restate `DECLARED LIMIT 14` so it **describes the class** — *what kind of schema goes
undecidable and why* — with the enumerated shapes demoted to **examples explicitly labelled
non-exhaustive**. **Write it LAST**, after the code is measured, so it describes what you built
rather than what you intended.

---

## 5. *** YOUR ACCEPTANCE GATE. THIS IS `PO-DECISIONS-0027` RULING 5 AND IT IS NOT A SHAPE COUNT. ***

> **A DIAL IN A NEVER-BEFORE-NAMED STATE, CARRYING `calm`, IS REFUSED — because `calm` requires
> proven-fresh-and-present, and an unrecognised state cannot prove it.**

**BUILD THE ARM THAT PROVES THIS, AND BUILD ITS CONTROL.** Arm **C30**:

- a state vocabulary **you invent**, appearing **nowhere** in `DECLARED_STATES`, **nowhere** in this
  instrument, and **nowhere** in arms `C1`–`C29` — `grep -c` it and **show the zero**;
- declared by a spelling **no audit in this chain has used**;
- carrying `detail_level: "calm"`;
- **MUST BE REFUSED.** Not `PASS`. A violation, reported, with its code.

And arm **C31**, the **CONTROL, and it is the arm that stops this being a blanket refusal**: the
**same tree**, from the **same builder**, **differing only in that the dial affirmatively presents
data that is PRESENT and FRESH** — **MUST BE ADMITTED.**

*** **C31 IS NOT OPTIONAL AND THE REASON IS ON THE RECORD.** *** `PROJECT_LEAD_SEAT_02` fell into
exactly this trap at `BL-...-0161`: a probe that refuses everything looks identical to a probe that
refuses the right thing. `CD-ASR-WO3-04` caught it by pairing every `REFUSED` with an `ADMITTED`
from the same builder differing in one string. **Do that. Every refusal in your return is paired or
it is not evidence.**

*** **AND THEN DO THE THING THE ARM CANNOT DO.** *** An arm proves **one** unknown state is
refused. Ruling 5 requires that **no** unknown state can be admitted. **ARGUE IT FROM THE CODE**:
name the lines, and show that the path from *"this node declares a state"* to *"calm is admitted"*
**cannot be traversed** without the state being affirmatively recognised as fresh-and-present.
**If you cannot make that argument, SAY SO AND RETURN — that is a real answer and it is worth more
than an arm that happens to go red.**

---

## 6. YOUR CONTRAST SET

Under `plants/WO3-INC16B/`, **C1–C28 untouched**, MANIFEST form with **`git apply`'s own exit code
as its own column**, every arm from its own **pristine extraction** (`CD-PL-F154`).

| # | Arm | Must |
|---|-----|------|
| **C29** | **the auditor's `enum`-of-literal-objects tree** (its `/tmp/armF`; PL-reproduced at `/tmp/enumesc`) | **FAIL** |
| **C29b** | the same escape spelled with **`const`** instead of `enum` | **FAIL** |
| **C30** | **RULING 5's COMPLETION TEST — a NEVER-BEFORE-NAMED state carrying `calm`** | **FAIL** |
| **C31** | **CONTROL — the same tree, present-and-fresh data** | **PASS** |
| **C32** | **A309-F2 — an unreadable `oneOf` BRANCH** (FX16's own arm) | **FAIL** |
| **C33** | *(CONTROL — MUST STILL PASS)* the symmetric fourth level (C10/C15/C21/C28) | **PASS** |

**RE-RUN C1–C28 UNCHANGED AND REPORT ANY MOVEMENT AS A DEFECT IN YOUR FIX**, not as noise.
`C10`/`C21`/`C28` at `PASS — 158`, `C14` at `FAIL — 2`, `C16` at `PASS — 144`, `C18`/`C19` at
`FAIL — 32`, `C20`/`C24`/`C25` at `FAIL — 2`.

---

## 7. NOT IN THIS INCREMENT

**Do not implement 16C** and make **no schema edit of any kind**. Out: `CD-PL-F180` / the
contract-bytes route and **exit 3** (settled by four auditors) · `DECLARED LIMIT 12`'s
differently-named discriminator (**judged honestly drawn; it is a disclosed condition on 16C's
dispatch, not your work**) · `REF_INERT_SIBLINGS` (**proved a provably empty attack class — do not
touch it**) · `STALENESS_WINDOW_CEILING_SECONDS` (16C) · the liveness/dead-feed detector itself
(16C) · no-blend, host-coupling, version (16D) · **registering any indicator row — not one row, not
a placeholder, not a test fixture** (16E) · any `publish_cycle` caller or `src/` entrypoint · `pbg/`.

**The memorial-in-tests removal (`PO-DECISIONS-0027` ruling 3) is 16C's, NOT yours.** Ruling 3
conditions it on the structural instrument carrying the behaviour, and that is what you are
finishing. **Leave the pytest literal-name assertion exactly where it is.**

---

## 8. YOUR RETURN

**BOOT FIRST**; the inherited `RED` on the frozen base (blob `ce0803c3`, nine seats) is **the base's
— diagnose, do not repair.**

1. **C29, C29b, C30, C32 each FAILING** with violation codes — **C30 called out explicitly and its
   invented vocabulary shown `grep -c` ZERO.**
2. **C31 and C33 PASSING**; **C1–C28 re-run and unchanged.**
3. **THE ARGUMENT FROM THE CODE** that ruling 5's condition holds by construction (§5), or a plain
   statement that you cannot make it.
4. Clean tree exit **0**, assertion count, and **the false-positive tail re-measured and re-priced**
   — it moves when the alphabet widens and you must say by how much.
5. `pytest tests/ -q` — no regression from **2007**; `test_detail_level.py` still **52**.
6. Register `MATCHES` · **18** · `GATE: SHUT` · `latest_admitted_run (null)`.
7. **How you proved the two recognisers agree on "readable"** (FX16), and **your depth and `const`
   decisions declared and priced** (FX15).
8. `DECLARED LIMIT 14` restated as a class, written last (FX17).
9. Scope proof by command; **ONE identity**, `git log --format='%an' dd40407..HEAD | sort -u`.
10. **Your declared limits**, including any new one. 11. **Your findings against this dispatch.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ENG-WO3-10 GIT_AUTHOR_EMAIL=cd-eng-wo3-10@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-10 GIT_COMMITTER_EMAIL=cd-eng-wo3-10@seats.crash-detector.invalid \
git commit -m "..."
```

**COMMIT AT EVERY BOUNDARY** (`PBG-CONT-007`). **YOU DO NOT CERTIFY YOUR OWN WORK** — a fresh
Assurance seat grades this against §5 and nothing you write here binds it.

**STOP AND RETURN if:** the alphabet correction turns the clean tree or any of `C1`–`C28` red · the
false-positive tail moves further than you are willing to price · you cannot make `C30` fail without
a list · you believe the auditor's `_INERT_KEYWORDS` measurement is wrong · **or you find any
statement in this dispatch to be false.**

*** **ELEVEN CONSECUTIVE DISPATCHES ON THIS LANE HAVE CONTAINED A FALSE STATEMENT A SEAT CAUGHT,
AND TWO OF THE LAST THREE AIMED THEIR PRIMARY ATTACK AT THE WRONG PLACE (`CD-PL-F198`,
`CD-PL-F199`). BOTH TIMES THE SEAT FOUND THE REAL DEFECT BY WORKING THE BUILDER'S OWN DECLARED
LIMIT RATHER THAN THE DISPATCH'S EXAMPLES. ASSUME THIS DISPATCH IS THE TWELFTH. THE LINE NUMBERS IN
§2 AND §3 ARE THIS SEAT'S OWN READING AND ARE THE MOST LIKELY THING IN HERE TO BE WRONG — CHECK
THEM. If the falsehood does not touch what you must build, continue and say so; `CD-PL-F192` is
precedent.** ***
