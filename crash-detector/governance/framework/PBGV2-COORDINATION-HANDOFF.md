# PBGv2 COORDINATION HANDOFF — the whole coordination residual set, catalogued for the framework track

**authority:** `PO-DECISIONS-0023` rulings 1, 2, 3, 4 (Product Owner (Trinity), 2026-08-23)
**written at:** boundary `BL-20260823T171737Z-0150`, by `PROJECT_LEAD_SEAT_01`
**base SHA:** `2b5946c1510100d74b3a8cae4c864f2c54de695c` (`main`)
**status:** REFERENCE-OUT. Nothing in this document is graded, closed, fixed or accepted here.

---

## 0. WHAT THIS DOCUMENT IS, AND THE THING IT IS NOT

`PO-DECISIONS-0023` ruling 1 parks the coordination discipline at `AMBER` and decouples it to the
PBGv2 framework track, with all residuals travelling **WHOLE**. This document is the crash
detector's side of that handoff: **the complete, enumerated residual set with a disposition against
every identifier.**

**IT IS NOT THE FRAMEWORK BACKLOG, AND IT DOES NOT MINT A FRAMEWORK ID.** That is stated because it
was **MEASURED, not assumed**:

```
find pbg -iname '*backlog*' -o -iname '*IMP*'   ->  pbg/skills/core/bounded-implementation.md  (a skill, not a backlog)
grep -rn 'IMP-015' pbg/                          ->  0 hits
git ls-files | grep -i backlog                   ->  0 hits
```

**THE RECEIVING BACKLOG IS NOT IN THIS REPOSITORY.** This is the same measured fact as `Q13`
(*"`IMP-023` DOES NOT EXIST IN THIS REPOSITORY"*), and it has the same consequence: a seat here
that wrote `IMP-0xx` beside these items would be **inventing an identifier in a register it cannot
read**. The precedent for how this is done correctly is `CD-FWK-005`, which was **harvested to the
framework backlog by the Product Owner and given `IMP-015` there, not here**. The same route is
owed for this set. **This document is the payload; the Product Owner carries it across.**

Nothing under `pbg/` was modified to produce it (`PBG-FWK-013`).

---

## 1. THE METHOD, AND WHY THE METHOD IS ITSELF THE POINT

`CD-PL-F102` and `CD-PL-F86` are the same recorded finding twice: **a sweep defined by a LIST, where
the thing that broke was outside the list.** Its remedy — *enumerate the registers, do not name the
ones you remember* — was **recorded twice and built neither time.**

A catalogue assembled by transcribing ruling 1's sentence would be that finding for the third time.
So this catalogue was built the other way:

1. every finding identifier was extracted **mechanically** from each source register
   (`grep -oE 'CD-ASR-WO2R3-0[67]-F[0-9]{2}' <verdict> | sort -u`);
2. **every extracted identifier gets a row**, including the ones ruling 1 does not name;
3. rows that do **not** travel are marked `EXCLUDED` **with the reason stated**, never dropped
   silently.

**THE CONSEQUENCE IS THAT THIS SET IS LARGER THAN RULING 1'S SENTENCE, AND THAT IS DELIBERATE.**
Ruling 1's own word is **WHOLE**. Where this document travels an item ruling 1 did not name, it says
so in the row. Where it excludes one, it says why. **The Product Owner can strike any row in one
sentence; nothing here is a widening of a ruling, it is an enumeration under one.**

### 1.1 Registers enumerated

| # | Register | Identifiers found |
|---|----------|-------------------|
| R1 | `governance/assurance/WO-2R3/VERDICT-NINTH-SEAT.md` (`CD-ASR-WO2R3-06`) | `F01`–`F14`, 14 |
| R2 | `governance/assurance/WO-2R3/VERDICT-TENTH-SEAT.md` (`CD-ASR-WO2R3-07`) | `F01`–`F11`, 11 |
| R3 | `BL-20260823T163840Z-0147` — Project Lead findings at the increment-13 merge | `CD-PL-F154`, `F155`, `F156`, 3 |
| R4 | `BL-20260823T163840Z-0147` — `CD-ENG-COORD-FIX-01`'s own return | 6 findings, 4 against itself |
| R5 | `ACTIVE_WORK.yaml` open questions | `Q11` (carriage) |

### 1.2 A NUMBERING COLLISION, DECLARED AS A READING SO IT CAN BE OVERTURNED IN ONE SENTENCE

Ruling 1 names its items **unqualified** — *"F01, F02, F09 + its false-record sibling (HIGH), F10,
F12, F13, F14"*. **TWO REGISTERS USE THE SAME BARE NUMBERS AND THEY MEAN DIFFERENT THINGS.** This
seat's reading, and the evidence for it:

| Ruling 1 says | This seat reads it as | Why |
|---|---|---|
| `F01` | `CD-ASR-WO2R3-07-F01` (tenth seat) | ruling 1's own gloss is *"F01 order-dependence"*, which is the tenth seat's heading verbatim. `CD-ASR-WO2R3-06-F01` is *"two of the three tiers are not built"* — a **perimeter** finding, not coordination. |
| `F02` | `CD-ASR-WO2R3-07-F02` (tenth seat) | ruling 1's gloss is *"F09's sibling … `lease.py` writes 'A SESSION DIED HOLDING THIS LEASE' over a LIVE session"*, which is the tenth seat's `F02` verbatim. `CD-ASR-WO2R3-06-F02` is the `RESISTED`-tier sentence, **already actioned by Act 1 of `PO-DECISIONS-0022` at `88e43db`**. |
| `F09`, `F10`, `F12`, `F13`, `F14` | `CD-ASR-WO2R3-06-*` (ninth seat) | `BL-...-0149`'s standing line reads *"`F10`, `F12`, `F13`, `F14` STILL OPEN — outside ruling 5's named five"*, and ruling 5's five are ninth-seat IDs. |

**UNDER THIS READING `F02` AND *"F09's false-record sibling"* ARE THE SAME OBJECT**, which is why
ruling 1's list appears to name it twice. **IF THAT READING IS WRONG, THE COST IS ONE ROW**, because
both candidate referents are dispositioned in §3 and §4 either way. **NO ITEM IS LOST TO THE
AMBIGUITY, WHICH IS THE ONLY PROPERTY THIS SEAT COULD GUARANTEE WITHOUT ASKING.**

---

## 2. THE HIGH SET — WHAT THE FRAMEWORK BUILD FIXES FIRST

Ruling 3 is explicit: *"a lying instrument is documented as HIGH so the framework build fixes it
first, per the estate's own doctrine."* These four are that set.

### H1 · `CD-ASR-WO2R3-07-F02` — **HIGH** — AN INSTRUMENT THAT MANUFACTURES A FALSE DURABLE RECORD

**This is ruling 3's named item and the reason coordination is parked rather than pushed.**

`lease.py reap --force` abandons a lease whose holder is **alive**, from any process, **with no
`--seat` and no identity argument of any kind — there is no identity argument to omit; it does not
exist in the parser.** Replicated end-to-end by the Project Lead against a genuinely live PID:

```
lease.py reap --lease L1 --reason "I want this scope" --force
  -> VERDICT: REAPED — lease=L1 state=ABANDONED (ALIVE)      rc=0
governance/coordination/leases/L1.lease.yaml
  reap_disclosure: A SESSION DIED HOLDING THIS LEASE. ...
kill -0 <holder>  -> STILL RUNNING
```

**THE INSTRUMENT PRINTS `(ALIVE)` IN THE SAME VERDICT LINE IN WHICH IT REAPS, AND THEN WRITES
`A SESSION DIED HOLDING THIS LEASE` INTO THE FILE THAT SURVIVES.** The transient string is true and
the persistent one is false, **and the persistent one is the one a later seat, a later audit or a
cold boot reads.** It is not an undeclared limit. It is an instrument that **manufactures a false
record of why a scope became free** — a worse class than the one `F09` named. `--force` appears in
no docstring, no command list, and none of the eleven declared limits. The freed scope was then
**taken** by a second seat, rc=0, with no authority check at any step.

### H2 · `CD-ASR-WO2R3-06-F09` — **HIGH — NOT CLOSED** (ruling 3)

`check_lease_held.py` can be turned green retroactively, in one command, by the party it grades.
Increment 13 fixed **the named instrument and not its sibling**. **RULING 3 IS THE DISPOSITION: NOT
CLOSED.** No seat may record otherwise. It travels open, paired with H1.

### H3 · `CD-ASR-WO2R3-07-F01` — **HIGH** — THE GATEKEEPER ADMITS WHAT THE DETECTOR REFUSES

`claim.py` never tests **this** claim's READ scope against a live claim's WRITE scope, so
`CD-PL-F134`'s guard is **order-dependent**. Same two claims, opposite verdicts, **the only variable
being arrival order**:

```
ORDER A (writer first):  both CLAIMED   ->  check_scope_disjoint.py: VIOLATION WRITE/READ, REFUSED
ORDER B (reader first):  second claim REFUSED at the gate
```

It is the ninth seat's `F04` signature in a different pairing — *the state the CLAIM instrument
produced is a state the DISJOINTNESS instrument calls a VIOLATION*. `F04` was closed for
`WRITE × WRITE`; **the asymmetric `WRITE × READ` half — which is `CD-PL-F134`, the incident the check
was named after — is still open on the gatekeeper side.**

**RULING 4 IS THE DISPOSITION ON ATTRIBUTION: NOT SPENT ON.** Whether it is increment-13 defect or
increment-12 residue changes nothing now that coordination is parked. **It travels as residue and
the framework build owns it.** `Q21` is answered and closed by ruling 4.

### H4 · `CD-PL-F154` — **HIGH** — THE ACCOUNTABLE SEAT'S IDENTITY MINTED AS A TEST FIXTURE, UNDETECTED

`CD-ENG-COORD-FIX-01` copied its worktree with `cp -a`, carrying the `.git` **gitlink**, so five
commits **deliberately minted as `PROJECT_LEAD_SEAT_01` for a `--identity` test fixture** landed on
the real `inc13-coordination-fix` branch. **The mechanism is not "a seat forgot its identity" — it is
"a seat deliberately minted the accountable seat's identity for a test, and nothing in this
repository noticed when it landed on a real branch."**

Residue on the branch **MEASURED ZERO**; the Engineer caught it, disclosed it and reverted it.
**NO INSTRUMENT DID. THAT IS THE FINDING**, and it is `PO-DECISIONS-0021` ruling 2's incident in
miniature, **occurring inside the increment built to prevent it.**

### H5 · `CD-ASR-WO2R3-06-F14` — **HIGH** — THE MERGE CONTROL'S ONLY LIVE RECORD IS `EVIDENCE_NOT_INDEPENDENT`

`merge_reconcile.py` measures containment against the `write_scope` **read out of the claim record —
a ruler the graded seat authored** — and compares `%an` against `seat_actor_id` from that same
self-authored record. Non-overlap compares zero pairs when there is one seat. **The claim post-dates
the work.** Travels with H6 below, which is its operational half.

### H6 · `CD-ASR-WO2R3-06-F10` — **HIGH** — TWO INSTRUMENTS, ONE STATED DOCTRINE, OPPOSITE CODE

`F09`/`F10` `--range` semantics and the dead-holder policy split. The ninth seat's own summary line:
**a control that can be argued with is not a control.**

### H7 · `CD-ASR-WO2R3-06-F11` — **HIGH, FIXED, TRAVELS AS EVIDENCE NOT AS DEBT**

The scope algebra called a directory disjoint from its own contents. Fixed in increment 13 and
**held under the tenth seat's attack** (`['src/*']` passes intact where the unfixed carrier expanded
it into three directories). It travels **only** so the framework build inherits the working fix and
its contrast arm, not to be re-fixed.

---

## 3. THE FULL CATALOGUE — EVERY ENUMERATED IDENTIFIER, WITH A DISPOSITION

### R1 · Ninth seat, `CD-ASR-WO2R3-06` (14 identifiers, all rows present)

| ID | Sev | Statement | Disposition |
|---|---|---|---|
| `F01` | HIGH | Two of the three tiers of the corrected perimeter are not built | **EXCLUDED — NOT COORDINATION.** It is a **PRODUCT** finding and it is the reason WO-3 exists. It stays on the crash detector's critical path (§5). |
| `F02` | HIGH | The `RESISTED` tier's load-bearing sentence is false as measured | **EXCLUDED — ALREADY ACTIONED** by Act 1 of `PO-DECISIONS-0022`, BLUEPRINT §17 corrected at `88e43db`. Product, not coordination. |
| `F03` | HIGH | `GUARD_THE_INSTANCE_NOT_THE_CLASS` — the measurement varied only the construction route | **EXCLUDED — NOT COORDINATION.** Product/perimeter. Load moved to the `DETECTED` tier; it is WO-3's problem. |
| `F04` | HIGH | The claim registry is not atomic over what the ruling asks | **TRAVELS.** Fixed in ruling 5's five for `WRITE × WRITE`; the `WRITE × READ` half is **H3**, open. |
| `F05` | HIGH | `launch.sh` mangles the write scope and manufactures a false green | **TRAVELS AS EVIDENCE.** Fixed; **held** under the tenth seat's attack. Not debt. |
| `F06` | MED | Dispatch `T12` — two operands do not belong to the SHA the heading claims | **TRAVELS.** Dispatch-hygiene, and it is a **carriage** instance: the figures were attributed by a seat, not by an instrument. Feeds `Q11`. |
| `F07` | LOW | A correction of `BL-0143`'s reasoning: *being told is words; what held was a mechanism* | **TRAVELS AS DOCTRINE.** No fix owed. It is the sentence the framework build should design to. |
| `F08` | **CRITICAL** | `check_scope_disjoint.py` was blind to the exact incident that caused increment 12 | **TRAVELS AS EVIDENCE — CLOSED WITH A FIRING CONTRAST.** 200 rounds / 0 double-takes repaired vs 195–196 unfixed, the tree the only variable, measured independently by four parties who did not adjust each other. **This is the genuine progress ruling 1 credits.** |
| `F09` | HIGH | `check_lease_held.py` turnable green retroactively by the party it grades | **TRAVELS OPEN — H2. RULING 3: NOT CLOSED.** |
| `F10` | HIGH | Two instruments, one stated doctrine, opposite code | **TRAVELS OPEN — H6.** Named by ruling 1. |
| `F11` | HIGH | The scope algebra calls a directory disjoint from its own contents | **TRAVELS AS EVIDENCE — H7.** Fixed and held. |
| `F12` | MED | Two instruments blind to merge commits, and a merge is where `CD-D-178` puts the pointer | **TRAVELS OPEN.** Named by ruling 1. `git show --pretty=format: --name-only <merge>` prints nothing. |
| `F13` | MED | `assert_atomic_or_refuse` fails **OPEN**, including on `"UNKNOWN"` | **TRAVELS OPEN.** Named by ruling 1. A nine-element denylist proceeding on everything else, in code documented as *"REFUSE rather than assume"*. |
| `F14` | HIGH | `merge_reconcile.py`'s only live record is `EVIDENCE_NOT_INDEPENDENT` | **TRAVELS OPEN — H5.** Named by ruling 1. |

### R2 · Tenth seat, `CD-ASR-WO2R3-07` (11 identifiers, all rows present)

| ID | Sev | Statement | Disposition |
|---|---|---|---|
| `F01` | HIGH | Gatekeeper admits what the detector refuses; `CD-PL-F134`'s guard is order-dependent | **TRAVELS OPEN — H3.** Named by ruling 1. Attribution not spent on (ruling 4). |
| `F02` | HIGH | `F09` is not closed; the lease is still flippable and the record it leaves is FALSE | **TRAVELS OPEN — H1.** Named by ruling 1. **Ruling 3 marks it HIGH and first.** |
| `F03` | MED | The `CD-RULE-004` three-place sweep is incomplete in the row it was raised against | **TRAVELS.** Beyond ruling 1's sentence; travels under *"WHOLE"*. |
| `F04` | MED | A live present-tense residual claim that disjointness is cross-seat-only | **TRAVELS.** Beyond ruling 1's sentence. A **false statement left standing in the record** — the class this estate treats as serious. |
| `F05` | MED | *"5/5 contrasted as required"* overstates what the plant demonstrates | **TRAVELS.** Beyond ruling 1's sentence. Overstatement in an acceptance claim. |
| `F06` | MED | The acceptance command's arm 1 grades a `print` string | **TRAVELS.** Beyond ruling 1's sentence. A control graded on stdout is a control graded on prose. |
| `F07` | MED/HIGH | The merge control is **UNRUNNABLE** in the mode the Product Owner just made standing | **TRAVELS OPEN.** Same object as `CD-PL-F155` (R3), reached independently by two parties. Ruling 1's *"F155"* carries it. |
| `F08` | MED | The atomicity guard is a DENYLIST that fails OPEN | **TRAVELS OPEN.** Same object as ninth-seat `F13`, confirmed by a second seat. |
| `F09` | LOW | `--dry-run` strands a live lease over a dead pid | **TRAVELS.** Beyond ruling 1's sentence. |
| `F10` | LOW | `lib.sh` reads a pipeline exit status in the file that forbids it | **TRAVELS.** Named by ruling 1 under the ninth-seat reading **and** present here; travels either way. |
| `F11` | MED | **There is no Assurance boot, so the boot instrument assigned me a role** | **TRAVELS — AND IT IS A FRAMEWORK DEFECT PROPER.** See §4. |

### R3 · Project Lead findings at the increment-13 merge

| ID | Sev | Statement | Disposition |
|---|---|---|---|
| `CD-PL-F154` | HIGH | Five commits deliberately minted as `PROJECT_LEAD_SEAT_01` landed on a real branch through a `cp -a` gitlink, and **no instrument noticed** | **TRAVELS OPEN — H4.** Named by ruling 1. Branch residue **MEASURED ZERO**. |
| `CD-PL-F155` | MED | `merge_reconcile.py` requires `--claim`; a sequential single-seat increment carries none, so **the control is unrunnable in the mandated mode** | **TRAVELS OPEN.** Named by ruling 1. *"A control whose applicability depends on a carrier nobody runs is available exactly when it is not needed."* |
| `CD-PL-F156` | MED | `CD-D-175` per-seat ID blocks vs `L3` `POINTER_STALE` — **the instrument declares the limit in `L4` and refuses on it anyway** | **TRAVELS OPEN.** Named by ruling 1. Quantified: of 25 violating commits, **4 are the real historical failure (`CD-PL-F132`, positions 76/85/90/91); positions 92 and 96–101 are `CD-D-175` meeting `L3`** and are not a discipline failure. **The framework build must not be handed the raw 25 as if all 25 were real.** |

### R4 · `CD-ENG-COORD-FIX-01`'s own return — six findings, four against itself

| ID | Statement | Disposition |
|---|---|---|
| `E-F01` | The `cp -a` gitlink escape | **= `CD-PL-F154`. TRAVELS AS H4.** Raised by the Engineer **against itself**. |
| `E-F02` | It also closed the identical TOCTOU in `lease.py`, **which no finding named**; declared in five places, and it observed `SCOPE_INSUFFICIENT` was available to it | **TRAVELS AS AN OPEN SCOPE QUESTION.** Ungraded here. A seat fixing what no finding named is scope drift **even when the fix is right**, and the framework build inherits the disclosure. |
| `E-F03` | The `CD-D-175` / `L3` contradiction | **= `CD-PL-F156`. TRAVELS.** |
| `E-F04` | `lease.py` lacks `claim.py`'s symlink / directory-literal validation | **TRAVELS OPEN. Declared, not fixed** — carried in the Engineer's own words. |
| `E-F05` | **Full `--pid` authentication is NOT SATISFIABLE on this platform** — a sibling pid in the caller's own session still passes; neither timestamp withstands forgery | **TRAVELS AS A STANDING CONSTRAINT, NOT AS A BUG.** The framework build must design **around** it, not promise past it. `--pid 1` is refused by derivation; that is the achievable half. |
| `E-F06` | `PLANT-COORD-06` arm 2 was **flaky by construction**; the seat's own diagnosis is that all three of its plant defects were the same error | **TRAVELS.** Raised **against itself**. Flakiness not reproduced in 20/20 runs by the tenth seat, **reported as a negative result and not as a refutation.** |

### R5 · The open question

| ID | Statement | Disposition |
|---|---|---|
| `Q11` | **THE CARRIAGE QUESTION. "The controls exist and nothing runs them."** Nine instruments, zero carriers — every one prints `IT IS NOT INVOKED BY ANYTHING` in its declared limit, **because the only automatic pre-write carrier in this repository lives inside the pinned `pbg/`.** | **TRAVELS OPEN, AND IT IS THE LOAD-BEARING ITEM OF THE WHOLE SET.** Named by ruling 1. The tenth seat names its carriage as one of three things a parallelism gate could not proceed without. `Q11` is **not fixable by this project by construction** (`PBG-FWK-013`) — which is precisely why decoupling it to the framework is the correct move and not an evasion. |

---

## 4. THE FRAMEWORK'S OWN DEFECT — `pbg boot` ROLE-BLINDNESS

**`pbg boot` TAKES NO ROLE ARGUMENT AND DECLARED A READ-ONLY ASSURANCE SEAT `PROJECT_LEAD`.**
(Tenth seat `CD-ASR-WO2R3-07-F11`, MEDIUM, raised against the framework **and** against its own
dispatch.) **Every seat this project has ever dispatched booted through that command**, including
this one — this boundary's own boot printed `assigned_role PROJECT_LEAD` and would have printed the
same for any seat.

It is **read-only to every seat here** (`PBG-FWK-013`), was **reported and not repaired**, and it
sits beside `CD-PL-F154`. **The two together say one thing, and it is the sentence increment 12
existed to falsify:**

> **THIS PROJECT'S IDENTITY DISCIPLINE IS CARRIED BY ATTENTION AND NOT BY MACHINERY.**

`PBG-BOOT-002` is non-waivable — *no agent self-assigns a role* — and **the boot instrument assigns
one.** That is not a contradiction this project may resolve. It is the framework's, and it goes at
the top of the framework build beside `Q11`.

---

## 5. WHAT DOES *NOT* TRAVEL, AND WHY IT MATTERS THAT IT IS SAID

Three ninth-seat HIGHs — `F01`, `F02`, `F03` — are **excluded from this handoff and remain the crash
detector's own**. They are the perimeter findings: the `DETECTED` tier is not built, and the load
that `RESISTED` was supposed to carry has been moved onto it. **They are WO-3's justification.**

**Saying this out loud is the guard against the failure mode this handoff could produce**: a
decouple that quietly carried the product's own open perimeter findings out of the product's
backlog would close `CD-AC-002`/`CD-AC-005` by relocation rather than by construction. **They do not
move. `CD-AC-005` stays RED, `CD-AC-002` stays AMBER and NOT CLOSED, and neither was touched at this
boundary.**

---

## 6. THE STARTING POINT THE FRAMEWORK INHERITS — RETAINED AND MEASURED

`PO-DECISIONS-0023` and this seat's dispatch both forbid deleting the coordination trees. They are
**retained, measured in `git worktree list` at this boundary**:

| Path | SHA | Branch |
|---|---|---|
| `/srv/crash-detector-inc12` | `59cb3c1` | `inc12-coordination` |
| `/srv/crash-detector-inc13` | `105db79` | `inc13-coordination-fix` |
| `/srv/crash-detector-audit9-main` | `4f3f4ce` | detached, the ninth seat's target |

Merged into `main`: increment 12 at `6c58725`, increment 13 at `b165dd9`. The nine instruments live
at `tools/coordination/`; their records at `governance/coordination/`; the eight plants and 27 arms
are runnable at `main`. **The verdicts are at `governance/assurance/WO-2R3/`, seven seats' documents,
none inside another.**

**THE FRAMEWORK BUILD STARTS FROM WORKING CODE WITH A KNOWN, MEASURED DEFECT LIST — NOT FROM A
BLANK PAGE.** That is what the two increments bought, and it is why parking is not discarding.

---

## 7. DECLARED LIMITS OF THIS DOCUMENT

1. **IT GRADES NOTHING.** No finding is closed, no severity is moved, no fix is proposed.
   `PBG-AUTH-003`. Severities are carried **as the raising seat set them**.
2. **IT MINTS NO FRAMEWORK ID**, because the receiving register is not readable from here (§0).
   Until the Product Owner carries these across, **this set has no identifier in the backlog that
   owns it**, and that gap is real and is stated rather than papered over.
3. **THE `F01`/`F02` NAMESPACE READING IN §1.2 IS A READING**, not a ruling. Both candidate
   referents are dispositioned, so no item is lost either way — but the mapping itself can be
   overturned in one sentence.
4. **`E-F01`–`E-F06` ARE THIS SEAT'S LABELS FOR THE ENGINEER'S SIX FINDINGS**, assigned here for
   citation. **They are not identifiers the Engineer minted**, and a later reader must not treat
   them as pre-existing.
5. **NO ITEM HERE WAS RE-MEASURED AT THIS BOUNDARY.** Every measurement quoted is carried from the
   boundary that took it (`BL-...-0147`, `BL-...-0149`, the ninth and tenth verdicts). **This is a
   catalogue, not a re-verification**, and calling it one would be the `CD-PL-F121` error.
6. **THE SET IS COMPLETE AGAINST THE FIVE REGISTERS IN §1.1 AND NOT AGAINST THE WHOLE RECORD.**
   Coordination residue may exist in earlier build-log entries that no verdict enumerated. **That is
   the residual `CD-PL-F102` risk and it is not zero here — it is bounded and named.**
