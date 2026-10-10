# CD-DISPATCH-INC16B-FIX3-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `CD-ASR-WO3-07`'s `AMBER` at `b4a15d6` and its F1/F2 ·
`CD-DISPATCH-INC16B-FIX3-ENGINEER` (`f73a7b6` on `main`) · `PO-DECISIONS-0026` ruling 9 ·
`PBG-SOD-001` / `PBG-SOD-004`, non-waivable
**seat identity:** `CD-ASR-WO3-08` — **FRESH.** **Never `CD-ENG-WO3-08` (which built the fix)**,
**never `CD-ASR-WO3-07` (which found F1 and F2)**, never `CD-ENG-WO3-01`…`-07`, never
`CD-ASR-WO3-01`…`-06`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **expected return:** `PASS` / `AMBER` / `RED` with the next
safe gate named.

---

## 1. THE TARGET

```
branch    wo-3
tip       4d797e694ffaaa0ea66f503a4d0a9c558e5ba08b   <- YOUR TARGET (content tip 3c44843)
prior     ba4523e  (16B-FIX-2 — assured AMBER at b4a15d6)
base      be0b355  (FROZEN — must still be exactly this when you finish)
the AMBER b4a15d6 on branch asr-wo3-07-verdict — BL-20260824T124330Z-A307.yaml (READ IT IN FULL)
the return governance/engineering/build-log/BL-20260824T131846Z-16B3.yaml on the lane (READ IT TOO)
```

**MUTATION PROHIBITED** except `/tmp` scratch trees, your own extractions, and your own verdict on
your own branch (suggested `asr-wo3-08-verdict`). **Get your own tree; do not work in
`/srv/crash-detector-wo3`, `/srv/crash-detector`, or any existing `*-audit*` worktree.**

---

## 2. ALREADY ESTABLISHED — DO NOT RE-CONFIRM

Reproduced by the Project Lead from its own plants and extractions at your target:

```
its own $ref-sibling conditional plant   was PASS — 144/0 with the gate ADMITTING calm on both
                                         surfaces;  now FAIL — 32 (40x BRANCHES-006 + 12x PAIRED-004)
C10/C21 CONTROL   PASS — 158 assertions, 0 violations
C14 (the 16C liveness arm)   FAIL — 2
clean worktree    PASS — 144 assertions, 0 violations
scope   zero paths on eleven protected prefixes; ONE identity, CD-ENG-WO3-08
```

---

## 3. WHERE TO ATTACK

### 3.1 — *** START WHERE THE BUILDER TOLD YOU TO — `REF_INERT_SIBLINGS` ***

The seat chose **deny-by-default at the resolver**: a `$ref` node carrying **asserting** siblings is
reported. **What makes a sibling "inert" is a TYPED-IN LIST OF NINE KEYWORDS, and the seat says only
`description` is exercised by any tree it built.** Its own **F03**: *a keyword wrongly INCLUDED in
that list is a false negative* — **attack `default`, `readOnly`/`writeOnly` and `examples` first.**

**That list is a blacklist's mirror image and it is the new soft spot. Every previous audit on this
row found the guard one position over from where it was looking. Look at the list, not the guard.**

Then `_synthesise` — the seat says it **still resolves without denying**, and that *"my
justification there is an argument, not a measurement."* **Measure it.**

### 3.2 — GRADE THE SEAT'S TECHNICAL OVERRIDE, BECAUSE IT OVERRODE THE DISPATCH

The dispatch ordered *"make `_deref` spec-correct — the target merged with its siblings"* and
offered deny-by-default as the fallback. **The seat took deny-by-default and argued the ORDERED
remedy is WRONG:** that `$ref` + siblings is a **conjunction**, not a merge, and that
`additionalProperties` / `unevaluated*` are evaluated against their own schema object's annotations,
so **a merged object can admit documents neither schema admits** — meaning a merge could only ever
*weaken* the instrument silently, which is exactly the defect being fixed.

*** **THAT ARGUMENT IS EITHER RIGHT OR IT IS A VERY WELL-DRESSED SHORTCUT, AND NOBODY HAS GRADED IT.
GRADE IT.** *** If it is right, say so plainly — the Project Lead's dispatch was wrong on the
mechanism and that belongs on the record. **If it is not right, this is a `RED`.**

### 3.3 — DID DENY-BY-DEFAULT OVERSHOOT?

The seat reports the public contract already carries **four `$ref` nodes with a `description`
sibling**, so a naive deny would have turned the **clean tree red**. **Verify that, then push:**

* legitimate `$ref` siblings a future contract author would plausibly write
* does the deny fire inside `$defs` members that are not branches at all?
* `C21`/`C10` must still `PASS — 158`, and **C1–C17 must all still bite** — verify from your own
  extractions with `git apply`'s exit code recorded, and **do not take the MANIFEST's word for its
  own column.**

### 3.4 — NOTHING DROPPED, AND THE COUNT THAT DID NOT MOVE

Clean-tree assertions stayed at **144** while FX9 and FX10 were added; the seat says FX9's union
check deliberately rides the existing `check.asserted(4)` site. **Verify no proposition was lost.**
That exact defect was found at 16B, where the count looked healthy and the coverage had shrunk.

### 3.5 — FX10 AND FX11

`FX10`: does a root property **declaring** a `state` key reach the undecidable limb **whatever** the
subschema's shape? Try shapes past `true` — `false`, an array, a string, `null`. `FX11`: the
superseded sentences (limits 10 and 12, plus new 13) — **is the new wording finally no bigger than
the code?** Two replacement sentences on this row have already been false in the same way as the
sentences they replaced. **Assume a third.**

---

## 4. WHAT IS NOT YOURS

`CD-PL-F180` / the contract-bytes route and the instrument's **exit 3** (settled by three auditors) ·
`DECLARED LIMIT 12`'s differently-named discriminator, **judged honestly drawn by `CD-ASR-WO3-07`
and carried as a condition on 16C's dispatch** · `STALENESS_WINDOW_CEILING_SECONDS` and the
three-quantity model (16C) · no-blend, host-coupling, version discrimination (16D) · registering any
indicator row (16E) · `pbg/` (report, do not repair). The boot `RED` (blob `ce0803c3`) is the frozen
base's — **seven seats have verified it. Diagnose and leave it.**

---

## 5. THE DECISION YOUR VERDICT GATES

**16C is held behind this increment.** `CD-ASR-WO3-07` judged it **releasable with two conditions**,
now binding on its dispatch: (1) 16C's dispatch must **name** the requirement that the liveness
discriminator be a property literally called `state` with an **object** subschema; (2) **16C must
not be accepted on a green instrument alone.**

*** **SO ANSWER, IN THESE WORDS: WOULD THIS GUARD SEE 16C GO WRONG? Your predecessor's answer was
"qualified yes, one keystroke wide." SAY WHETHER THAT IS STILL TRUE, AND HOW WIDE THE KEYSTROKE IS
NOW.** ***

---

## 6. ONE FALSE STATEMENT ALREADY FOUND, DISCLOSED

**`CD-PL-F196`, against the Project Lead, confirmed by the seat.** The 16B-FIX-3 dispatch §0 said
both findings were *"one-line class errors … your whole job is to write those two lines."* **False
for F1**: a one-line resolver deny would have turned the clean tree red, because the public contract
carries four `$ref` nodes with a `description` sibling. **`FX10` genuinely was one line; `FX9` was
not.** The seat continued on the `CD-PL-F192` precedent — the falsehood was about the *size* of the
work, not the prescription — and said so. **That judgement is CONFIRMED.**

**Eight consecutive dispatches on this lane have contained a false statement a seat caught. Assume
this one does too, and grade it as you grade the code.**

---

## 7. YOUR RETURN

`PASS` / `AMBER` / `RED` naming the exact SHA, the next safe gate, and:

1. Verdict and next safe gate.
2. Every probe with command and output pasted — including those that found nothing.
3. **§3.1 answered**: `REF_INERT_SIBLINGS` attacked keyword by keyword; `_synthesise` measured.
4. **§3.2 answered**: is the seat's rejection of the merge remedy correct?
5. **§5 answered in its own words.**
6. Every shape it did not catch; every correct tree you made it fail on.
7. `be0b355` unmoved; register `MATCHES` / **18** / `SHUT` / `null`; `evidence/` unwritten.
8. **Your findings against this dispatch.**

**You did not build this and YOU MAY NOT REPAIR IT.** Diagnose, reproduce, trace, test, prescribe —
**prescription written, line left unwritten.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ASR-WO3-08 GIT_AUTHOR_EMAIL=cd-asr-wo3-08@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ASR-WO3-08 GIT_COMMITTER_EMAIL=cd-asr-wo3-08@seats.crash-detector.invalid \
git commit -m "..."
```

**Bank your verdict as a Build Log entry on your own branch** (`PBG-CONT-007`).

*** **THE STANDARD: `PASS` MEANS YOU ATTACKED THIS AND COULD NOT BREAK IT. THE LAST THREE SEATS IN
YOUR CHAIR EACH BROKE THEIR TARGET, AND EACH ESCAPE WAS MORE EXOTIC THAN THE LAST. IF YOU CANNOT
BREAK IT, SAY SO PLAINLY AND SAY HOW HARD YOU TRIED — A CLEAN VERDICT HONESTLY EARNED IS WHAT
RELEASES 16C.** ***
