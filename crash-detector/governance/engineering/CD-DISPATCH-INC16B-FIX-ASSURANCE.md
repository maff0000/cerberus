# CD-DISPATCH-INC16B-FIX-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `CD-ASR-WO3-05`'s `AMBER` at `ca85d8e` and its findings F1/F2/F3/F6 ·
`CD-DISPATCH-INC16B-FIX-ENGINEER` (`0e87fa8` on `main`) · `PO-DECISIONS-0026` ruling 9 ·
`PBG-SOD-001` and `PBG-SOD-004`, both non-waivable · `CD-D-181`
**seat identity:** `CD-ASR-WO3-06` — **FRESH.** **Never `CD-ENG-WO3-06` (which built the fix)**,
**never `CD-ASR-WO3-05` (which found the holes — a seat does not rule on the repair of its own
finding, `PBG-SOD-004`)**, never `CD-ENG-WO3-01`…`-05`, never `CD-ASR-WO3-01`…`-04`, never any
`CD-ENG-WO2R3-*` or `CD-ENG-COORD*`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **expected return:** `PASS` / `AMBER` / `RED` with the next
safe gate named.

---

## 1. THE TARGET

```
branch    wo-3
tip       64cd5b2122f8ae1f7310a81379757d9cc297ff40   <- YOUR TARGET (content tip af3825c)
prior     cbb81d1  (16B — assured AMBER at ca85d8e)
base      be0b355  (FROZEN — must still be exactly this when you finish)
the AMBER ca85d8e on branch asr-wo3-05-verdict — BL-20260824T104431Z-A305.yaml (READ IT IN FULL)
```

**MUTATION PROHIBITED** except `/tmp` scratch trees, your own `git archive` extractions, and your
own verdict artefact on a branch of your own (suggested `asr-wo3-06-verdict`). **Get your own tree.
Do not work in `/srv/crash-detector-wo3`, `/srv/crash-detector`, or any existing `*-audit*`
worktree.**

---

## 2. WHAT IS ALREADY ESTABLISHED — DO NOT SPEND YOUR BUDGET RE-CONFIRMING IT

**The Project Lead reproduced all of the following independently, from its own extractions, against
the fix:**

```
my own E3 shape (4th oneOf branch, marker property, no new root key)
      was  PASS 67/0 and INVISIBLE TO THE WHOLE REGISTER
      now  FAIL — 6 violations: 4x CD-CALM-GATE-001 + 2x CD-CALM-BRANCHES-006
my own required-dropped shape
      was  PASS 67/0        now  FAIL — 8 violations
C10 CONTROL (symmetric fourth level)  PASS — 158 assertions, 0 violations
clean worktree                        PASS — 144 assertions, 0 violations   (was 67)
C1 FAIL 8 · C2 FAIL 2 · C3 FAIL 8 · C4 FAIL 4   — every count unchanged from 16B
pytest tests/ -q                      2007 passed
register  pid.content_hash MATCHES · 18 criteria · GATE: SHUT · latest_admitted_run (null)
scope     zero paths on all twelve protected prefixes; one commit identity CD-ENG-WO3-06
```

**Confirming a confirmation is not assurance.** The three holes `CD-ASR-WO3-05` found are closed and
two seats have measured that. **Your job is the shapes nobody has brought yet.**

---

## 3. WHERE TO ATTACK

### 3.1 — *** THE PRIMARY ATTACK: DEFEAT THE NEW DENY-BY-DEFAULT BRANCH ALLOWLIST ***

FX1 added two things: drive every `oneOf` branch whose `properties.state.const` is an absent-data
state, **and** fail on any branch not on a declared allowlist (`CD-CALM-BRANCHES-006`). **That
second half is the whole defence, and a deny-by-default rule is only as good as its recogniser.**

**The question is not "does it catch a fourth branch?" — it does. It is: WHAT IS A BRANCH, AND WHAT
COUNTS AS ITS STATE?** Bring shapes where the answer is not the obvious one:

* a branch whose state is written `{"enum": ["UNKNOWN"]}` rather than `{"const": "UNKNOWN"}`
* a branch with **no** `properties.state` at all, or with `state` supplied via `allOf`
* a permissive branch reached through **nested composition** — `allOf`, `anyOf`, a `$ref` to a
  `$ref` — rather than as a direct member of the top-level `oneOf` array
* the union restructured from `oneOf` to `anyOf`, or the discriminated union moved up a level
* a branch that IS on the allowlist by name but whose **definition** has been widened underneath it
  (does the allowlist bind a name, or a shape?)

*** **IF THE ALLOWLIST RECOGNISES BRANCHES BY A PATTERN RATHER THAN BY DENY-BY-DEFAULT
UNRECOGNISABILITY, IT IS A BLACKLIST WITH BETTER MANNERS, AND THIS ESTATE HAS PAID FOR THE
WHACK-A-MOLE GAME REPEATEDLY (`PO-DECISIONS-0026` ruling 10 exists because of it).** ***

Do the same to **FX3's slot-set assertion** (`CD-CALM-SLOTS-007`): can a dial-bearing root property
hide from it — behind `allOf: [{"$ref": "#/$defs/dial_reading"}]`, behind a `$ref` to a `$ref`,
behind a property whose value is an inline copy of `dial_reading` rather than a `$ref` at all?

### 3.2 — **`DECLARED LIMIT 8` AND THE 16C COLLISION — THE FORWARD RISK NOBODY HAS PRICED**

The seat declared, deliberately, that **the dial-state vocabulary (`ABSENT_STATES`) is typed into
the instrument rather than derived from the contract.** Every other axis — surfaces, slots, levels,
and now branches — is derived. **This one is not.**

*** **AND THE NEXT INCREMENT IS 16C, WHICH IS `PO-DECISIONS-0026` RULING 5: THREE QUANTITIES, ONE OF
THEM A LIVENESS/DEAD-FEED SIGNAL. `CD-AC-001`'s OWN WORDS ARE "MISSING **OR STALE** INPUT NEVER
RENDERS AS CALM."** *** So ask directly, and this is the question the Project Lead most wants
answered:

* If a **new absent-data state** arrives — a `STALE` reading state, or an existing state
  reclassified as absent-data — **is it driven, or is it silently unexercised until someone
  remembers to edit a tuple?**
* Measure it: **add such a state to both contracts and see what the instrument does.** Does it fail
  closed (unrecognised branch → `CD-CALM-BRANCHES-006`), or does it pass?
* **Is limit 8 honestly drawn, and is "deliberately" a good enough reason?** The seat gave one.
  Weigh it.

**If a plausible 16C change lands a new absent-data state and this instrument passes it in silence,
say so plainly — that is a finding worth more than anything else you could return today.**

### 3.3 — DID THE FIX WEAKEN ANYTHING? (assertions went 67 → 144)

* Take the **16B** instrument (at `cbb81d1`) and the **16B-FIX** instrument (at your target) and ask
  whether **every** proposition the old one asserted is still asserted. A rewrite that grows a count
  while quietly dropping a row is exactly the defect `CD-ASR-WO3-05` found in 16B itself — **the
  register-wired instrument was strictly weaker than the pytest file it superseded, and nobody
  noticed because the assertion count looked healthy.**
* **Make it fail on a tree that is legitimately fine.** `CD-ASR-WO3-05`'s F5 already established the
  instrument is stronger than PID §3.2 on one axis (a tree admitting only `acute` fails it) and that
  this is *declared*. **Find a second such axis, and say whether it too is declared.**

### 3.4 — THE TWO SUPERSEDED SENTENCES

FX2 and FX3 corrected two governed artefacts that said something measurably false. **Verify the
corrections are true now**, in every place `CD-RULE-004` requires them, and that the supersession
form was used — *what it said, that it was false, what is true instead* — rather than deletion
(`PBG-CONT-003`).

**`CD-ENG-WO3-06`'s own F03 says `DECLARED LIMIT 12` (the FX4 name-coupling declaration) landed in
ONE of its three places**, because the other two are `contracts/execution/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.md`
(granted neither writable nor protected — **a gap in the Project Lead's dispatch**) and `tests/**`
(protected by the ruling itself). **The seat declared the shortfall rather than widening its own
scope, which is the right order. Grade whether declaring it was sufficient.**

### 3.5 — THE ARM THAT FALSELY READ `PASS`, DISCLOSED BY THE SEAT ITSELF

The seat's **first** generation of C6–C10 did not apply (`git apply` rc=1) and **all five arms
falsely read `PASS`**. The MANIFEST's `git apply` exit-code column caught it on the first run —
**the fifth recorded instance of `CD-ENG-WO2R3-06-F06`, inside the very increment whose house rule
exists to catch it.** The seat recorded it rather than quietly regenerating.

**Verify the arms in the tree now genuinely apply and genuinely bite, from YOUR OWN extractions,
with `git apply`'s exit code recorded.** Do not take the MANIFEST's word for its own column.

---

## 4. WHAT IS NOT YOURS

`CD-PL-F180` / the writable-contract-bytes route — **ruled into 16D and re-scoped to the contract
BYTES the gate loads at publish time, adopting `CD-ASR-WO3-05`'s correction.** Exit 3 is settled.
**Note anything you see; do not grade it.** Also out of scope: staleness and
`STALENESS_WINDOW_CEILING_SECONDS` (16C — **except as §3.2's forward question**), the no-blend
structural closure, host-coupling, version discrimination (16D), and registering any indicator row
from `governance/mapping/indicator_mapping.yaml` (16E). `pbg/` is read-only — report, do not repair.

The boot `RED` (`ACTIVE_WORK.yaml:36`, `continuity_record_commit: PENDING`) is inherited
byte-for-byte from `be0b355` — blob `ce0803c3`, verified by three seats now. **Diagnose and leave
it.**

---

## 5. TWO FALSE STATEMENTS ALREADY FOUND, DISCLOSED SO YOU DO NOT INHERIT THEM

1. **Against the Project Lead (`CD-PL-F187`, confirmed).** `CD-DISPATCH-INC16B-FIX-ENGINEER` §4 said
   the field-absent row *"needs a stated exception"* for the one-pointer diff. **False, and the seat
   measured it:** `_differing_pointers` is a symmetric difference of pointer sets, so a candidate
   omitting the key differs from its admitted pair at exactly that one pointer. All 8 rows pair
   cleanly with no exception written. **The error came from the auditor's prescription and the
   Project Lead carried it into a binding record without executing it.**
2. **Against the audit (`CD-ENG-WO3-06` F02).** `BL-20260824T104431Z-A305` says *"18 lines exit 0;
   the 12 non-zero"* but enumerates eleven. The seat measured **19 rc=0, 11 non-zero**, reconciling
   with the auditor's enumeration and with neither of its counts. **Substantive findings unaffected
   — and note the Project Lead made the same class of error at `CD-PL-F185`.** **Re-derive this
   census yourself; two seats have now got it wrong.**

**Every dispatch on this lane in the last four has contained a false statement a seat caught. Assume
this one does too.**

---

## 6. YOUR RETURN

`PASS` / `AMBER` / `RED` naming the exact SHA, with the next safe gate, and:

1. Your verdict and the next safe gate.
2. Every probe with its command and output pasted — including the ones that found nothing.
3. **§3.1 answered**: what is a branch, what is a slot, and can either hide?
4. **§3.2 answered explicitly**: what happens when a new absent-data state arrives, measured.
5. Every shape the instrument did not catch; every correct tree you made it fail on.
6. `be0b355` unmoved; register `MATCHES` / **18** / `SHUT` / `null`; `evidence/` unwritten.
7. **Your findings against this dispatch**, including your own re-derived `execute:`-line census.

**You did not build this and YOU MAY NOT REPAIR IT** (`PBG-SOD-001`, `PBG-SOD-004`). Diagnose,
reproduce, trace, test, prescribe. **If a one-line change would close a finding, write the
prescription and leave the line unwritten.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ASR-WO3-06 GIT_AUTHOR_EMAIL=cd-asr-wo3-06@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ASR-WO3-06 GIT_COMMITTER_EMAIL=cd-asr-wo3-06@seats.crash-detector.invalid \
git commit -m "..."
```

**Bank your verdict as a Build Log entry on your own branch** (`PBG-CONT-007`) — a verdict that
exists only in conversation is not project state.

*** **THE STANDARD: `PASS` MEANS YOU ATTACKED THIS AND COULD NOT BREAK IT. THE PREVIOUS SEAT IN
YOUR CHAIR BROKE ITS TARGET THREE WAYS, AND ONE OF THOSE BREAKS WAS INVISIBLE TO EVERY INSTRUMENT
THE PROJECT OWNS. THAT IS THE BAR.** ***
