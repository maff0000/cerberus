# CD-DISPATCH-INC16B-FIX5-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `PO-DECISIONS-0027` (committed `c1e45ba` on `main`), **ruling 5 is your
acceptance test** · `CD-ASR-WO3-09`'s `RED` at `a74705c` · the Project Lead's reconciliation at
`BL-20260824T155131Z-0173` (`8c71243` on `main`)
**seat identity:** `CD-ASR-WO3-10` — **FRESH.** **Never `CD-ENG-WO3-10` (which built this —
`PBG-SOD-001`, non-waivable)**, **never `CD-ASR-WO3-09` (which found the defect — `PBG-SOD-004`)**,
never any of `CD-ENG-WO3-01`…`-09` or `CD-ASR-WO3-01`…`-08`.
**issued by:** `PROJECT_LEAD_SEAT_03` · **increment:** 16B-FIX-5 · **expected return:**
`PASS` / `AMBER` / `RED` **with the next safe gate named**

---

## 0. YOUR TARGET, AND THE ONE THING THAT MAKES THIS AUDIT DIFFERENT FROM THE NINE BEFORE IT

```
branch    wo-3
worktree  /srv/crash-detector-wo3
TARGET    8398741c039f9cb616201e22b285d815406dc3cc   (content tip 16b872c)
PRIOR     dd40407                                     (the RED'd tip — your contrast)
base      be0b355                                     (FROZEN — READ-ONLY)
ruling    governance/decisions/PO-DECISIONS-0027.md   — READ RULING 5 BEFORE ANYTHING ELSE
```

*** **YOU ARE NOT BEING ASKED FOR A SHAPE CENSUS. `PO-DECISIONS-0027` RULING 5 ABOLISHED IT, AND
THAT RULING BINDS THIS AUDIT AS MUCH AS IT BOUND THE BUILD.** ***

> **THE GUARD IS DONE WHEN ONE STRUCTURAL TEST IS GREEN: a dial in a NEVER-BEFORE-NAMED state,
> carrying `calm`, is REFUSED — because calm requires proven-fresh-and-present and an unrecognised
> state cannot prove it. If a further named escape is found after this test is green, THE TEST WAS
> WRONG, NOT THE GUARD INCOMPLETE.**

**READ THAT LAST SENTENCE TWICE, BECAUSE IT CUTS BOTH WAYS AND THE SECOND WAY IS THE ONE THAT
MATTERS TO YOU.** If you find a seventh spelling that escapes, **the finding is not "add this shape"
— the finding is "the completion test does not test what it claims to test," and that is a much
more serious finding and the one worth your budget.** Nine audits have found nine shapes. **A tenth
shape is worth less to this project than one sound answer about whether the test is sound.**

**MUTATION IS PROHIBITED** except diagnostic artefacts under `/tmp`. Do not commit to `wo-3`. Do
not touch the worktree — every arm from its own `git archive | tar -x` extraction (`CD-PL-F154`).
Bank your verdict on **your own branch**, `asr-wo3-10-verdict`, in your own worktree.

---

## 1. THE THREE PLACES THIS SEAT BELIEVES YOUR BUDGET IS BEST SPENT — AND YOU ARE NOT BOUND BY THEM

*** **READ THIS WARNING BEFORE YOU READ THE THREE.** *** **TWELVE CONSECUTIVE DISPATCHES ON THIS
LANE HAVE CONTAINED A FALSE STATEMENT THE RECIPIENT CAUGHT.** The twelfth is `CD-PL-F202` and it is
**this seat's own, in the Engineer dispatch you are auditing against** — §3 told the Engineer the
branch recogniser "continues as though it had looked", which is **false**; `state is None` was
already reported as `CD-CALM-BRANCHES-006` at `dd40407`, lines 1617–1626. **The Engineer found the
real defect anyway by reading the code instead of the dispatch.** In three of the last four rounds
the seat was saved by distrusting its instructions. **DO THAT. ASSUME THIS DISPATCH IS THE
THIRTEENTH.**

### (a) IS THE COMPLETION TEST SOUND? — *this is the audit*

`C30` is the arm that claims ruling 5. **Attack the arm, not just the tree.** Is `SPINDRIFT` /
`HALCYON_VOID` genuinely never-before-named (the seat claims `grep -c` zero — **verify it
yourself**)? Is the spelling genuinely novel? **And the real question: does `C30` passing mean what
ruling 5 needs it to mean, or does it prove only that ONE unknown state is refused?** The Engineer
supplied an argument-from-the-code (eleven answer sites, only two yielding `False`, contrapositive
that a node naming `state` cannot be `False`). **GRADE THAT ARGUMENT. It is the only thing in this
increment that claims to cover ALL unknown states, and an argument is exactly the kind of artefact
that can be confidently wrong.**

### (b) `CD-PL-Q-C31` — DOES THE CONTROL ADMIT FOR THE RIGHT REASON? *(raised by this seat, unresolved on purpose)*

`C31` is `C30`'s tree with `state: "SPINDRIFT"` replaced by `present: true` — **so the dial no
longer names a property called `state` at all.** It may therefore pass because the recogniser finds
it **INVISIBLE** (clean `False`, not-a-dial), **not** because it affirmatively proved
present-and-fresh. **`PO-DECISIONS-0027` RULING 1 REQUIRES ADMISSION ONLY ON AFFIRMATIVE PROOF**,
and "invisible therefore admitted" is the shape of every escape in this chain.

The precedent this arm cites — `CD-ASR-WO3-04`'s — was a **recognised** dial (`state` const
`VALUE`) carrying `calm` and still admitted. **`C31` IS A WEAKER CONTROL THAN THE ONE IT CITES.**
This seat measured `C4` (the vacuity arm, `CD-CALM-GATE-002`) at the tip and it **still bites at
`FAIL — 4`**, so the mute-button failure mode is not unguarded. **But this seat did not resolve
whether that is sufficient, because resolving it would be certifying what it dispatched.** It is
yours.

### (c) THE ENGINEER'S OWN TWO — carried because the seat named them against its own work

- **The argument's declared boundary.** It covers dials naming a property called `state`. A dial
  discriminating on a **differently-named** key is `DECLARED LIMIT 12`'s residue. **The Engineer
  declared this itself.** Is the boundary correctly drawn, and does ruling 5's condition survive it?
- **`DECLARED LIMIT 12`'s residue** — unchanged, a standing condition on 16C's dispatch.

**And the Engineer's own `F02`, which you should not have to rediscover:** `C32` is **structural,
not behavioural**. The live gate returns `REFUSED [UNKNOWN_KEY]` on that document for an unrelated
upstream reason. The arm proves the **instrument** moved; **it does not prove the gate would have
admitted.** The seat declared this rather than letting the arm read as behavioural.

---

## 2. WHAT THIS SEAT ALREADY MEASURED — SO YOU SPEND YOUR BUDGET ON JUDGEMENT, NOT ON RE-RUNNING ME

**Re-run whatever you distrust — you are not asked to take any of it.** Reproduced in the Project
Lead's own shell, own extractions, both tips, `git apply` rc=0 on every arm:

| arm | `dd40407` | `8398741` |
|---|---|---|
| clean tree | `PASS — 144`, exit 0 | `PASS — 144`, exit 0 |
| **C30** ruling 5 | **`PASS — 144` ESCAPE** | **`FAIL — 2`** `CD-CALM-SLOTS-007` |
| **C31** control | `PASS — 144` | **`PASS — 144`** |
| **C32** unreadable branch | **`PASS — 144` ESCAPE** | **`FAIL — 4`** `CD-CALM-BRANCHES-006` |
| **C4** vacuity | — | **`FAIL — 4`** |
| **C10/C33** control | — | **`PASS — 158`** |

`pytest` **2007 passed** · `test_detail_level.py` **52** · register `MATCHES` · **18** ·
`GATE: SHUT` · `latest_admitted_run (null)` · **one** commit identity · working tree clean · scope
grep returns **zero** protected paths · frozen `be0b355` **unmoved**.

*** **NONE OF THAT IS A GRADE. IT WAS MEASURED BY THE SEAT THAT WROTE THE DISPATCH, WHICH IS
EXACTLY THE SEAT WHOSE MEASUREMENTS CANNOT SETTLE THIS** (`PBG-AUTH-003`, `CD-D-180`). *** It is
banked, not accepted, and 16C stays held until you say otherwise.

---

## 3. THE TRAP THIS PROJECT HAS FALLEN INTO TWICE — DO NOT MAKE IT A THIRD

**A probe that refuses everything looks identical to a probe that refuses the right thing.**
`PROJECT_LEAD_SEAT_02` fell into it at `BL-...-0161`. `CD-ASR-WO3-04` escaped it by **pairing every
`REFUSED` with an `ADMITTED` from the same builder differing in one string**, and by **building its
own fixture from the schema rather than using the project's fakes** — because the fakes route
through `detail_level_for` and therefore cannot emit `calm` at all, so a probe built on them cannot
test the thing it is probing for.

**Pair every refusal you report. Build your own fixture. And reproduce the ORIGINAL escape at
`dd40407` with your identical probe** — an arm that is red at the new tip proves nothing unless it
was green at the old one, and that is how you attribute the result to the change rather than to
your probe.

---

## 4. NOT IN SCOPE

`CD-PL-F180` / contract-bytes / exit 3 (settled by four auditors) · `REF_INERT_SIBLINGS` (proved a
provably empty attack class) · 16C itself, the liveness detector, `STALENESS_WINDOW_CEILING_SECONDS`
· no-blend, host-coupling, version (16D) · registering any indicator row (16E) · `pbg/` ·
the lane's inherited boot `RED` (blob `ce0803c3`, ten seats — **diagnose, do not repair**).

---

## 5. YOUR RETURN

A verdict of **`PASS` / `AMBER` / `RED`** with **the next safe gate named**, banked as a build log
entry on **your own branch `asr-wo3-10-verdict`** in **your own worktree**, committed as:

```
GIT_AUTHOR_NAME=CD-ASR-WO3-10 GIT_AUTHOR_EMAIL=cd-asr-wo3-10@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ASR-WO3-10 GIT_COMMITTER_EMAIL=cd-asr-wo3-10@seats.crash-detector.invalid \
git commit -m "..."
```

(`git -c user.name=` **does not work on this host**. Unquoted heredocs and `-m` with backticks
**silently delete backticked words** — use `<<'EOF'`. And `status:` in a build log entry must be
one of the schema's values — **`READY_FOR_ASSURANCE` IS NOT ONE**, five prior entries got this
wrong and it is `CD-PL-F201`; validate your entry before committing it.)

**State in your return:**

1. **YOUR VERDICT ON RULING 5's COMPLETION CONDITION** — is the guard closed **by construction**?
   This is the question. Everything else is subordinate to it.
2. Your grade of **the Engineer's argument-from-the-code**, and whether its declared boundary holds.
3. Your answer on **`CD-PL-Q-C31`**.
4. Every measurement with the **command and its actual output**, every refusal **paired**, every new
   arm run at **both tips**.
5. **Your findings against THIS DISPATCH** — assume it contains a falsehood.
6. **IF, AND ONLY IF, YOU RETURN CLEAN:** the conditions you would put on 16C's dispatch. The
   previous auditor was asked this, returned `RED`, and named them anyway — **that was the single
   most useful thing in its verdict** and this dispatch asks for it again.

*** **YOU ARE THE ONLY THING STANDING BETWEEN THIS PROJECT AND A DEAD FEED PUBLISHED AS CALM. NINE
SEATS BEFORE YOU FOUND SOMETHING REAL EVERY SINGLE TIME. THE ONE THING THIS PROJECT HAS NEVER HAD
IS AN AUDITOR WHO COULD SAY "IT IS CLOSED, AND HERE IS WHY NO FUTURE SHAPE CAN ESCAPE." IF THAT IS
TRUE NOW, SAY IT AND PROVE IT. IF IT IS NOT, SAY THAT.** ***
