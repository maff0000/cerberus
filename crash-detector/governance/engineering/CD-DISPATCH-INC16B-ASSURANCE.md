# CD-DISPATCH-INC16B-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `PO-DECISIONS-0026` ruling 9 (the constitutional fix must be REGISTER-WIRED,
not test-only) and ruling 7 (16B, sequential single-seat) · `CD-DISPATCH-INC16B-ENGINEER`
(committed `3b4ef01` on `main`) · `PBG-SOD-001` and `PBG-SOD-004`, both non-waivable · `CD-D-181`
**seat identity:** `CD-ASR-WO3-05` — **FRESH.** **Never `CD-ENG-WO3-05` (which built what you are
auditing)**, never `CD-ENG-WO3-01`/`-02`/`-03`/`-04`, never `CD-ASR-WO3-01`/`-02`/`-03`/`-04`,
never any `CD-ENG-WO2R3-*` or `CD-ENG-COORD*`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **expected return:** `PASS` / `AMBER` / `RED` with the next
safe gate named.

---

## 1. THE TARGET

```
branch    wo-3
tip       cbb81d15dd1ca105c922c15d61d91fc7673e7249    <- YOUR TARGET (code tip dc609f7)
prior     20fd1e1  (Project Lead record act) / b9283b9 (16A-FIX, assured AMBER at 3464956)
base      be0b355  (FROZEN — must still be exactly this when you finish)
the AMBER 3464956 on branch asr-wo3-04-verdict — its F2 is what 16B answers
ruling    governance/decisions/PO-DECISIONS-0026.md  (in the lane at 20fd1e1)
```

**MUTATION PROHIBITED** except `/tmp` scratch trees, `git archive` extractions, and **your own
verdict artefact**, for which you have a narrow write grant on a branch of your own. **Get your own
tree** — `git worktree add --detach` or a WHOLE-tree `git archive` extraction. **Do not work in
`/srv/crash-detector-wo3`, `/srv/crash-detector`, or any existing `*-audit*` worktree.**

---

## 2. WHAT WAS BUILT, AND WHAT IT CLAIMS

16A-FIX narrowed both envelope contracts so `DEGRADED` and `UNKNOWN` cannot carry `calm`. An
independent seat proved that behaviourally and returned `AMBER`. **Its finding F2 was that the
narrowing is guarded only by `tests/`, and that a register-wired instrument passes identically on a
fully reverted tree.** The Project Lead reproduced F2 and widened it: **all fourteen register
instruments pass on the reverted tree, and the nine failures are all in `tests/test_detail_level.py`,
which none of the register's 29 `execute:` lines named.**

16B's answer, at your target:

* **`tools/register/check_missing_data_never_calm.py`** — a new instrument that imports the
  application and drives `refuse_unless_publishable` itself, on both surfaces at both dial slots.
* **`required-tests.yaml`** — a new test row `CD-RT-001-MISSING-DATA-NEVER-CALM` under `CD-AC-001`,
  and `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s declared command **grown additively** by
  `tests/test_detail_level.py`.
* **`contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`** — its execution contract.
* **`plants/WO3-INC16B/`** — five contrast arms, C1–C5.

**READ, THEN DISTRUST:** the seat's `BL-20260824T102127Z-16BI.yaml` on the lane, this dispatch's
sibling `CD-DISPATCH-INC16B-ENGINEER`, and the Project Lead's reconciliation banked alongside this
dispatch. **The Engineer raised six findings including four against its own dispatch, and the
Project Lead confirmed one of them was a defect in the dispatch's own measurement (F01, §5 below).
A seat that argues well is not thereby correct.**

**DO NOT SPEND YOUR BUDGET RE-RUNNING C1–C4.** The Project Lead already reproduced all four
independently, from its own extractions, and they behave exactly as the seat reported —
C1 `FAIL` 8×`GATE-001`, C2 `FAIL` 2×`GATE-001`, C3 `FAIL` 8×`GATE-001`, **C4 `FAIL` 4×`GATE-002`
with `GATE-001` firing zero times**, clean arm exit 0 at 67 assertions. **Confirming a
confirmation is not assurance. Attack what nobody has attacked.**

---

## 3. WHERE TO ATTACK — IN THIS ORDER, AND THE ORDER IS THE POINT

### 3.1 — *** THE PRIMARY ATTACK: IS THE INSTRUMENT JUDGING THE PRODUCT, OR A DOCUMENT OF ITS OWN INVENTION? ***

The instrument **builds its own candidate envelopes** and feeds them to the gate. **That is the
whole increment's load-bearing assumption and nobody has tested it.**

*** **IF THE CANDIDATE ENVELOPE IT CONSTRUCTS IS NOT THE SHAPE THIS PRODUCT ACTUALLY PUBLISHES,
THEN EVERY REFUSAL IT RECORDS IS A REFUSAL OF A DOCUMENT NO CODE PRODUCES, AND THE INSTRUMENT IS
A VERY WELL-EVIDENCED GUARD ON NOTHING.** *** This is the same defect class as the one 16B exists to
close, rebuilt one level up — and this project has recorded it four times already (`CD-PL-F169`,
`CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`, `CD-ASR-WO3-04` F2).

Specifically:

* Compare the instrument's candidate against what `src/crash_detector/publication/publish.py` and
  the envelope builders actually emit. **Does a field, a required key, or a `oneOf` discriminator
  differ?** A candidate that fails schema validation *for an unrelated reason* would be "REFUSED" and
  scored as a pass by a naive assertion. **Check that each of the 8 refusals is refused for the
  RIGHT reason** — the seat claims the sole differing JSON pointer is `/<slot>/detail_level`. Verify
  that claim yourself, on both surfaces, at both slots.
* **Can you construct a real envelope, produced by the product's own code path rather than by the
  instrument, that carries `calm` on an absent-data branch and is ADMITTED?** If you can, that is a
  `RED` and the increment has not delivered.

### 3.2 — CAN YOU MAKE THE INSTRUMENT PASS ON A TREE WHERE CALM-OVER-UNKNOWN IS ADMITTED?

C1–C4 are the Engineer's own four shapes, and a guard tested only against the shapes its author
imagined is a blacklist with better manners. **Bring shapes the author did not.** Suggestions, not a
list to work down:

* a **third** missing-data state, or a new branch in the `oneOf`, that carries the full vocabulary
* `absent_data_detail_level` redefined as `{"type": "string"}` with no enum at all
* the `$ref` pointed at a *new* `$defs` member that happens to contain `calm`
* `additionalProperties` or the branch discriminator relaxed so the `UNKNOWN` branch is never the
  one selected, and a permissive branch validates instead
* the narrowing intact on both contracts but a **third** contract file introduced and loaded
* `detail_level` made optional on an absent-data branch — **absence of the field is not `calm`, but
  it is a renderer deciding for itself, which is the second decision site the module exists to
  prevent.** Does the instrument care? Should it?

### 3.3 — AND THE OTHER DIRECTION: CAN YOU MAKE IT FAIL ON A TREE THAT IS FINE?

A guard that fires on correct trees gets disabled, and then it guards nothing. Try legitimate
variation: reordered `$defs`, a renamed-but-equivalent absent-data type, an `enum` written
`["acute","elevated"]`, a third *legitimate* level added under a PID amendment.

### 3.4 — **F03 / C5: THE ROUTE THAT IS OPEN AND IS NOT CLOSED BY THIS INCREMENT**

**The Project Lead reproduced this independently and it is real.** With both repository contracts
**byte-identical to their committed blobs** (`46f3a1b7…`, `304a9bf1…`, confirmed against
`git rev-parse HEAD:<path>`), setting `$CD_CONTRACTS_DIR` to a widened copy makes the live gate
**ADMIT a calm `UNKNOWN` dial on both surfaces.** The instrument exits 3 (`PRECONDITION_NOT_MET`)
rather than passing — it refuses to judge a tree it is not looking at — but **it does not close the
route, and neither does anything else in the repository.**

This is recorded as **`CD-PL-F180`**, scheduled into **16D** (where `CD_CONTRACTS_DIR` is already
the subject under `PO-DECISIONS-0026` ruling 6), and it is **NOT** a defect in 16B's delivery.
**Your job on it is to say whether the Project Lead's scheduling is right and whether the declared
limit is honestly drawn** — and in particular:

* **Is exit 3 the right behaviour, or is it a guard that can be switched off by an environment
  variable and told to call it a precondition?** Argue it either way, but argue it.
* **Are there OTHER routes to the same place?** The seat named `$CD_CONTRACTS_DIR` and "the package
  imported from outside `--root`". **Look for a third.** Is the contracts directory writable by the
  running service? Is there a route that does not need an environment variable at all?

### 3.5 — THE REGISTER WIRING, WHICH IS THE RULING'S ACTUAL SUBJECT

* Run the new row's `execute:` line **verbatim, from a pristine `git archive` extraction you made
  yourself**, working directory at that tree's root. **Not from the Engineer's worktree.** Does it
  run? Does it need `jsonschema`, and is that dependency declared where this project declares
  dependencies? The seat disclosed the stdlib-only departure — **is it a defect or is it fine?**
* `pid.content_hash` still `MATCHES` · **18** criteria and not 19 · `latest_admitted_run` still
  `null` · `GATE: SHUT`. **Any of those moved is a `RED`.**
* `evidence/required-tests/runs/` — **the seat must not have written there.** Verify it did not.
* **D3:** does adding `tests/test_detail_level.py` to `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s command
  misstate what that entry evidences? That entry is `scope: CLASS` and carries a *runtime* property.
  The seat judged it did not misstate it. **You may disagree, and the dispatch invited that.**

### 3.6 — IS THE DECLARED LIMIT HONESTLY DRAWN? (`CD-RULE-004`)

The seat declared **eight** limits, including *"it says nothing about staleness, which is half of
`CD-AC-001`'s own words, so the criterion is still only half-guarded by live instruments."* **That
is a real admission and it deserves testing, not applause.** Find a limit it did not declare. A
variant landing outside a declared boundary is a finding **against the declaration** — *was the
limit honestly drawn?* — and that is the standard this project has used since WO-2.

---

## 4. WHAT IS NOT YOURS

Ruled items 2–6 of `PO-DECISIONS-0026` ruling 7 are 16C–16E and are **out of scope**: the
three-quantity staleness model and `STALENESS_WINDOW_CEILING_SECONDS`, the structural closure of
the no-blend guard, the host-coupling defaults, the version discrimination, and registering any
indicator row. **You may note anything you see. Do not grade it.** `pbg/` is read-only and outside
scope, including any framework defect you find — report, do not repair.

**The boot `RED` from `ACTIVE_WORK.yaml:36` (`continuity_record_commit: PENDING`) is inherited
byte-for-byte from the frozen base** — the Engineer measured `git diff --stat be0b355 20fd1e1` on
that file as empty. **Verify that claim, then leave it alone.**

---

## 5. THE ONE THING THE PROJECT LEAD ALREADY GOT WRONG, DISCLOSED SO YOU DO NOT INHERIT IT

`CD-DISPATCH-INC16B-ENGINEER` §4 D2 said *"all 18 criteria are UNDECIDABLE for exactly this
reason"* (a missing run record). **The Engineer's F01 said 16, not 18, and the Engineer was right.**
Confirmed by the Project Lead: 16 criteria are UNDECIDABLE solely because
`negative_control.evidence_ref` does not resolve; **`CD-AC-017` and `CD-AC-018` are UNDECIDABLE
because their `execution_contract` does not resolve**, and would stay UNDECIDABLE with every run
record in existence. Recorded as **`CD-PL-F181`**, against the Project Lead.

**Two of the last three dispatches on this lane contained a false statement that a seat caught.
Assume this one does too and go looking.**

---

## 6. YOUR RETURN

A `PASS` / `AMBER` / `RED` verdict **naming the exact SHA you audited**, with:

1. Your verdict and **the next safe gate**.
2. Every probe you ran, **with the command and its output pasted** — including the ones that found
   nothing. A probe that found nothing is evidence; a probe you did not run is not.
3. **§3.1 answered explicitly**: is the instrument judging the product's real document shape?
4. Every shape you brought that the instrument did **not** catch, and every correct tree you made it
   fail on. **If you found none, say how hard you tried and what you tried.**
5. Your reading on **§3.4** — the scheduling of `CD-PL-F180` into 16D, and whether exit 3 is right.
6. `be0b355` still exactly `be0b355`; the register still `MATCHES` / 18 / `SHUT` / `null`.
7. **Your findings against this dispatch.**

**You did not build this and you may not repair it** (`PBG-SOD-001`, `PBG-SOD-004`, both
non-waivable). **You may diagnose, reproduce, trace, test and prescribe. You may not fix.** If a
one-line change would close a finding, **write the prescription and leave the line unwritten.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ASR-WO3-05 GIT_AUTHOR_EMAIL=cd-asr-wo3-05@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ASR-WO3-05 GIT_COMMITTER_EMAIL=cd-asr-wo3-05@seats.crash-detector.invalid \
git commit -m "..."
```

**A verdict that exists only in conversation is not project state (`PBG-CONT-007`).** Bank it as a
Build Log entry on your own branch.

*** **AND THE STANDARD, PLAINLY: `PASS` MEANS YOU ATTACKED THIS AND COULD NOT BREAK IT. IT DOES NOT
MEAN YOU READ IT AND IT LOOKED RIGHT. THE LAST FOUR TIMES A SEAT ON THIS LANE READ SOMETHING AND IT
LOOKED RIGHT, IT WAS NOT.** ***
