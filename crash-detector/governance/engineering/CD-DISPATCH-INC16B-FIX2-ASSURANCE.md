# CD-DISPATCH-INC16B-FIX2-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `CD-ASR-WO3-06`'s `AMBER` at `c7471dc` and its F1/F2 ·
`CD-DISPATCH-INC16B-FIX2-ENGINEER` (`fe5eac6` on `main`) · `PO-DECISIONS-0026` rulings 9 and 5 ·
`PBG-SOD-001` / `PBG-SOD-004`, non-waivable · `CD-D-181`
**seat identity:** `CD-ASR-WO3-07` — **FRESH.** **Never `CD-ENG-WO3-07` (which built the fix)**,
**never `CD-ASR-WO3-06` (which found F1 and F2 — a seat does not rule on the repair of its own
finding)**, never `CD-ENG-WO3-01`…`-06`, never `CD-ASR-WO3-01`…`-05`, never any `CD-ENG-WO2R3-*`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **expected return:** `PASS` / `AMBER` / `RED` with the next
safe gate named.

---

## 1. THE TARGET

```
branch    wo-3
tip       ba4523ef9f587358418221e330a176bec745b9ad   <- YOUR TARGET (content tip e01b8f5)
prior     64cd5b2  (16B-FIX — assured AMBER at c7471dc)
base      be0b355  (FROZEN — must still be exactly this when you finish)
the AMBER c7471dc on branch asr-wo3-06-verdict — BL-20260824T114609Z-A306.yaml (READ IT IN FULL)
```

**MUTATION PROHIBITED** except `/tmp` scratch trees, your own extractions, and your own verdict
artefact on a branch of your own (suggested `asr-wo3-07-verdict`). **Get your own tree. Do not work
in `/srv/crash-detector-wo3`, `/srv/crash-detector`, or any existing `*-audit*` worktree.**

---

## 2. ALREADY ESTABLISHED — DO NOT RE-CONFIRM IT

**The Project Lead reproduced the following independently, with its own plants (not the Engineer's
patches) and its own extractions:**

```
the 16C liveness quantity, written as an optional third root property
      was  PASS — 144/0  while the gate ADMITTED a dead feed rendering as calm
      now  FAIL — 2 violations, CD-CALM-SLOTS-007
the conditional-branch shape (widened branch + optional marker + closed `else`)
      was  PASS — 144/0  while the gate ADMITTED calm on an UNKNOWN dial
      now  FAIL — 32 violations: 20x CD-CALM-BRANCHES-006 + 12x CD-CALM-PAIRED-004
C10 CONTROL   PASS — 158 assertions, 0 violations      C6 regression   FAIL — 6
clean tree    PASS — 144 assertions, 0 violations      pytest          2007 passed
tests/test_detail_level.py   52 passed;  its diff is 48 insertions / 0 deletions — docstring only
register      pid.content_hash MATCHES · 18 criteria · GATE: SHUT · latest_admitted_run (null)
scope         zero paths on eleven protected prefixes; ONE identity, CD-ENG-WO3-07
```

**Both escapes `CD-ASR-WO3-06` found are closed and two seats have measured that. Confirming a
confirmation is not assurance.**

---

## 3. WHERE TO ATTACK

### 3.1 — *** START WHERE THE BUILDER TOLD YOU TO ***

`CD-ENG-WO3-07`'s own **F03** says: *the filler fallback is the one thing no prescription asked for
— **attack it first***. **A seat pointing at the part of its own work nobody specified is the
highest-value lead you will get today, and it is the part with no auditor's prescription behind it
and no reviewer's eyes on it yet.**

Find it, understand what it does when a candidate cannot be built from a branch, and ask: **can a
tree be constructed in which the fallback produces a document that is REFUSED for a reason unrelated
to `detail_level`, so a MUST-REFUSE row passes for the wrong reason?** That is the shape
`CD-ASR-WO3-05` had to check by hand at 16B and it is now behind an extra layer of machinery.

### 3.2 — DID THE DENY-BY-DEFAULT RULES OVERSHOOT?

FX5 and FX6 both widen what the instrument refuses to judge. **Two seats have now made the same
mistake in the opposite direction — a claim larger than the code — so check this direction too:**

* **F02, the builder's own:** a **legitimate** conditional branch now turns the instrument red,
  priced as `DECLARED LIMIT 10`. **Is that price honestly stated, and is it the right price?** The
  Project Lead ruled for deny-by-default on the ground that the clean tree carries no conditional
  keyword inside any branch. **Verify that ground still holds at your target, and say what happens
  the day it does not.**
* **FX6's looser form:** the Project Lead ruled that declaring a `state` is enough. **Does it fire
  on anything legitimate?** Try root properties that are plainly not dials but declare a `state`.
  **A guard that fires on correct trees gets disabled, and then it guards nothing.**
* **C15/C10 must still pass.** Verify from your own extraction, and check the assertion count did
  not move for a reason nobody explained.

### 3.3 — WHAT IS STILL SILENT, AND IS IT HONESTLY DECLARED?

The builder declared **F04: a dial discriminating on a key not named `state` is still silent**
(`DECLARED LIMIT 12`). **Build that tree. Measure it. Then judge whether the declaration is honestly
drawn or whether it is the next `CD-ASR-WO3-06` F2** — a pattern recogniser wearing
deny-by-default's clothes, one level further in. **That finding is the direct descendant of the last
two audits and it is the most likely place for a third.**

And ask the question that has paid off twice: **what does `DECLARED_STATES` still buy, and what does
it still cost?** It is the one axis not derived from the contract.

### 3.4 — DID ANYTHING GET DROPPED?

Assertions stayed at **144** on the clean tree while two new rules were added. **That is not
suspicious on its face — the new rules are refusals, which fire on planted trees rather than clean
ones — but verify it rather than assuming it.** Every proposition the 16B-FIX instrument asserted
must still be asserted. **`CD-ASR-WO3-05` found exactly this defect at 16B, where the count looked
healthy and the coverage had shrunk.**

### 3.5 — THE UNORDERED ARMS AND THE DECLINED ONE

The builder **added C16 and C17 beyond the five ordered** and **declined C15's literal
byte-duplicate shape**, running C10's patch from its own extraction instead — both declared (F05,
F06). **Verify the arms genuinely apply and genuinely bite, from YOUR OWN extractions, with
`git apply`'s exit code recorded.** A predecessor's first generation silently failed to apply and
all five falsely read `PASS`. **Do not take the MANIFEST's word for its own column.**

---

## 4. WHAT IS NOT YOURS

`CD-PL-F180` / the contract-bytes route (16D, re-scoped to the bytes) and the instrument's **exit
3**, both settled by two auditors · `STALENESS_WINDOW_CEILING_SECONDS` and the three-quantity model
(16C — **held behind this increment; see §5**) · the no-blend structural closure, host-coupling,
version discrimination (16D) · registering any indicator row (16E) · `pbg/` (report, do not repair).

The boot `RED` (`ACTIVE_WORK.yaml`, blob `ce0803c3`) is the frozen base's — **five seats have now
verified it. Diagnose and leave it.**

---

## 5. THE DECISION YOUR VERDICT GATES

*** **16C IS HELD BEHIND THIS INCREMENT.** `PO-DECISIONS-0026` ruling 5's liveness quantity, written
the obvious way, was admitted rendering as `calm` by a gate whose constitutional instrument reported
clean. **Your verdict is what releases it.** So the question behind every probe you run is not "is
this instrument tidy" — it is: *** **WOULD THIS GUARD SEE 16C GO WRONG?** *** Answer that
explicitly.

---

## 6. TWO FALSE STATEMENTS ALREADY FOUND — DISCLOSED SO YOU DO NOT INHERIT THEM

1. **Against the Project Lead (`CD-PL-F192`, CONFIRMED by the PL's own measurement).** The 16B-FIX-2
   dispatch §5 said `DECLARED LIMIT 12` *"has no counterpart 10 or 11 anywhere"*. **False.**
   `grep -n` puts `DECLARED LIMITS 10 AND 11` at `required-tests.yaml:307` and `DECLARED LIMIT 12`
   at `:345` — **same file, same block scalar, 38 lines apart.** The claim originated in
   `CD-ASR-WO3-06` (v) and the Project Lead carried it into a binding record **without executing
   it — for the third time today** (`CD-PL-F187`, `CD-PL-F190`, and now this). **The seat corrected
   the premise rather than accepting it, and fixed the real defect underneath: nothing anywhere said
   that limit numbers are PER-ROW, which is what made a bare "DECLARED LIMIT 12" ambiguous.**
   **PROJECT LEAD RULING: the seat's decision to continue rather than stop is CONFIRMED** — the
   falsehood was confined to FX8's rationale, touched nothing in FX5/FX6/FX7, and the ordered
   corrective action discharged identically either way. **Stopping would have left a constitutional
   escape open over a numbering footnote.**
2. **`CD-ASR-WO3-06` (v) is the origin of that false claim.** **An audit finding is not
   self-certifying either.** Grade this dispatch the same way.

**Six consecutive dispatches on this lane have contained a false statement a seat caught. Assume
this one does too.**

---

## 7. YOUR RETURN

`PASS` / `AMBER` / `RED` naming the exact SHA, with the next safe gate, and:

1. Verdict and next safe gate.
2. Every probe with command and output pasted — including those that found nothing.
3. **§3.1 answered**: the filler fallback, attacked.
4. **§3.3 answered**: the not-named-`state` dial, built and measured; is `DECLARED LIMIT 12`
   honestly drawn?
5. **§5 answered explicitly: would this guard see 16C go wrong?**
6. Every shape it did not catch; every correct tree you made it fail on.
7. `be0b355` unmoved; register `MATCHES` / **18** / `SHUT` / `null`; `evidence/` unwritten.
8. **Your findings against this dispatch.**

**You did not build this and YOU MAY NOT REPAIR IT** (`PBG-SOD-001`, `PBG-SOD-004`). Diagnose,
reproduce, trace, test, prescribe. **If a one-line change would close a finding, write the
prescription and leave the line unwritten.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ASR-WO3-07 GIT_AUTHOR_EMAIL=cd-asr-wo3-07@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ASR-WO3-07 GIT_COMMITTER_EMAIL=cd-asr-wo3-07@seats.crash-detector.invalid \
git commit -m "..."
```

**Bank your verdict as a Build Log entry on your own branch** (`PBG-CONT-007`).

*** **THE STANDARD: `PASS` MEANS YOU ATTACKED THIS AND COULD NOT BREAK IT. THE LAST TWO SEATS IN
YOUR CHAIR EACH BROKE THEIR TARGET, AND ONE OF THOSE BREAKS WAS THE NEXT INCREMENT. THAT IS THE
BAR — AND IF YOU CANNOT BREAK IT, SAY SO PLAINLY AND SAY HOW HARD YOU TRIED, BECAUSE A CLEAN
VERDICT HONESTLY EARNED IS WHAT RELEASES 16C.** ***
