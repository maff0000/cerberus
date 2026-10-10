# CD-D-187 — ASSURANCE DISPATCH, WO-3 INCREMENT 16G

**Dispatch id:** CD-D-187
**Issued at:** 2026-08-25T06:38:03Z, by `PROJECT_LEAD_SEAT_09`
**Seat:** `CD-ASR-WO3-15` — **A FRESH ASSURANCE IDENTITY.**
**Role source:** `pbg/roles/assurance-engineer.md`. Read it. Reading it does not grant the role;
**this dispatch grants it** (`PBG-BOOT-001`, `PBG-BOOT-002`).
**Authority record:** `CD-AUTH-0001`, via `PO-DECISIONS-0032`.

> **YOU ARE NOT `CD-ASR-WO3-14` AND YOU ARE NOT `CD-ENG-WO3-15`** (`PBG-SOD-001`, non-waivable).
> `CD-ASR-WO3-14` raised the findings this increment repairs and **may not grade their repair**.
> `CD-ENG-WO3-15` built it.

---

## 1. TARGET

| | |
|---|---|
| Content tip | **`0cf8411`** (`0cf84117148c40d31f997bd1dc8aa0f730823fef`) |
| Entry tip | `90c3dc3` |
| Branch / worktree | `wo-3` / `/srv/crash-detector-wo3` |
| Base it must be graded against | `c475b8e` (content `7ac11c9`) |
| Runtime | **THERE IS NONE.** No container, no deployed instance. Every claim is about bytes at a commit and the behaviour of those bytes under `python3` on this host. **MAKE NO `LIVE` CLAIM.** |

**YOU ARE READ-ONLY.** Mutation is prohibited except explicitly safe diagnostic artefacts under
`/tmp/`. **Do not fix anything. Do not write a line that would fix it** (`PBG-SOD-004`). If you find a
repair, describe the PROPERTY in words and leave the line unwritten.

**Use a throwaway worktree under `/tmp/` for every probe. Do not disturb the lane. `wo-2r3` is FROZEN
at `be0b355` — verify it, do not touch it.**

---

## 2. WHAT THE INCREMENT CLAIMS

Four findings from the banked 16F verdict
(`git show af4ac85:governance/engineering/build-log/BL-20260824T234541Z-A314.yaml`), each **true
whatever `Q41` was ruled**:

- **`CD-ASR-F14-02`** — `DECLARED LIMIT 9`'s closing reassurance is false in the reassuring direction
  in all its `CD-RULE-004` places. Claimed superseded (never edited) in **four** sites, with arm `Z7`
  named.
- **`CD-ASR-F14-03`** — `CD-CHOKE-003`'s stated scope ("the judging path") was wider than its
  implemented scope. Claimed closed: it now reads `refuse_unless_publishable`'s own handlers.
- **`CD-ASR-F14-04`** — the word `CLOSED`, deleted by edit from `required-tests.yaml` alone. Claimed
  restored by disclosed supersession.
- **`CD-ASR-F14-05`** — the `122` figure that does not reproduce. Claimed corrected to a measured `97`.

**`CD-ASR-F14-01` WAS DELIBERATELY NOT ADDRESSED.** `PO-DECISIONS-0032` ruling 3 records the
insider-source-weakening full guarantee as **owed later-hardening, not a product blocker**. **DO NOT
GRADE THIS INCREMENT AGAINST IT.** Grading a seat against work its dispatch forbade would be a
mis-grade. You may of course confirm it was genuinely not reopened.

---

## 3. WHAT THE PROJECT LEAD ALREADY RAN — RE-RUN IT, DO NOT TRUST IT

Stated so you can attack it rather than repeat it. **All of it is a hypothesis until it is yours**
(`CD-PL-F193`).

```
NEW instrument (0cf8411)  +  CLEAN tree   ->  PASS — 11 assertions, 0 violations   rc=0
NEW instrument (0cf8411)  +  Z5-patched   ->  FAIL — 1 violation(s)                rc=1
OLD instrument (c475b8e)  +  Z5-patched   ->  PASS — 11 assertions, 0 violations   rc=0
```

Also measured: `src/` **0 paths**, `pbg/` 0, `tests/` 0, both `contracts/*.json` sha256-identical,
`wo-2r3` unmoved, three-place agreement on `CLOSED` restored, and `122` still present **once per place
as a verbatim quotation inside its own supersession** (which is correct, not a miss).

---

## 4. WHERE TO PRESS HARDEST

Ranked. **This is where the Project Lead thinks this increment is weakest, and it is not where the
Engineer thinks it is.**

1. **`F16G-03` — THE CONTROL ASSERTS NOTHING ON A CLEAN TREE.** The new pass adds **zero** assertions
   at clean; the count stays 11. The Engineer declared this itself as `DECLARED LIMIT 8(a)` and named
   the stronger form it chose not to build. **A control whose only witness is a failing arm is guarded
   by the arm's continued existence.** Attack it: can you weaken the gate's handlers in a way the new
   `CD-CHOKE-003` does not see? The `Z5` shape re-raises conditionally — **try the shapes it does
   not.** Nested `try`, a handler in a helper the gate calls, `except` with a bare `return`, a
   `finally` that swallows, a handler that re-raises a *different* exception, a `contextlib`
   suppressor.
2. **ITEM 1's REPLACEMENT WORDING.** *** **THIS ROW HAS BEEN SUPERSEDED SEVEN TIMES FOR SENTENCES THAT
   WERE FALSE IN THE REASSURING DIRECTION. THE EIGHTH REPLACEMENT IS THE MOST LIKELY PLACE FOR AN
   EIGHTH.** *** The new claim is that `CD-CHOKE-005` catches a `return`/`continue`/`break`
   **lexically inside `_refuse_stale_calm`**, and that neither row reads the functions the stage
   depends on. **IS THAT TRUE?** Build the counterexample. And check the wording does not let a reader
   see `Z7` sitting at `PASS` and conclude the class is closed.
3. **DID THE SUPERSESSIONS ACTUALLY SUPERSEDE?** `PBG-CONT-003` is non-waivable and **this increment is
   about a record that was edited rather than superseded.** Verify by diff that no prior wording was
   deleted anywhere — that every correction quotes what it corrects. **A silent re-edit committed while
   fixing a silent re-edit is the finding of this increment, and it would be a `RED`.**
4. **THE FOURTH SITE.** The Engineer reports the row-level `scope:` summary is a fourth site in a
   "three-place" rule, and that a plain `grep` found only two of four because of differential
   line-wrapping. **DO THE FULL-BODY NORMALISED COMPARISON `CD-ASR-WO3-14` RETURNED `UNSUPPORTED` ON
   (`CD-ASR-F14-M2`).** If you also cannot, **return `UNSUPPORTED` — AN `UNSUPPORTED` IS NOT A `PASS`**
   (`PBG-FWK-003`).
5. **THE `97`.** Measure it yourself at `a9e19c3` in your own worktree. Three seats now say 97. **If
   you get a fourth answer, that is a finding and you must not round to the consensus.**
6. **VACUITY, BOTH DIRECTIONS.** The clean tree must still pass, and the arms must genuinely bite.
   Confirm `Z5CTRL` — the legitimate re-raising `try` — is **NOT** flagged. A control that fails on
   correct code is worse than no control.

---

## 5. HOW TO GRADE

- **`PASS` / `AMBER` / `RED`, with the next safe gate**, per your role contract.
- **GRADE THE CONDITION, NOT THE EFFORT.** `CD-ASR-WO3-14`'s reasoning for its `RED` is the standard:
  a universal that is refuted by construction is refuted, however good the seat's work was.
- **STATE THE CASE AGAINST YOUR OWN VERDICT** in the entry, as this project's audit seats do.
- **EVERY FIGURE CARRIES ITS COMMAND AND THE `rc` TAKEN FROM THAT COMMAND.** Take `rc` from the
  command, **not from a pipe** — `F16G-01` is exactly that mistake, self-raised.
- **SAY PLAINLY WHAT YOU DID NOT DO** and why. That section is not optional on this project.
- **A VERDICT IS NOT AN ACCEPTANCE** (`PBG-AUTH-003`). You do not release anything, register any
  indicator row, move any lane pointer, or merge.
- Commit your verdict on your own branch under your own seat identity — **env vars, not
  `git -c user.name=`, which does not work on this host**:
  ```
  GIT_AUTHOR_NAME=CD-ASR-WO3-15 GIT_AUTHOR_EMAIL=cd-asr-wo3-15@seats.crash-detector.invalid \
  GIT_COMMITTER_NAME=CD-ASR-WO3-15 GIT_COMMITTER_EMAIL=cd-asr-wo3-15@seats.crash-detector.invalid \
  git commit ...
  ```
  Verify with `git log -1 --format=%an` afterwards. Use quoted heredocs (`<<'EOF'`) or write files
  directly — unquoted heredocs silently eat backticked words on this host.

## 6. WHAT AN HONEST `PASS` WOULD REQUIRE

All four items genuinely repaired; every supersession a real supersession with the prior wording
readable; the new `CD-CHOKE-003` biting `Z5` and **not** biting `Z5CTRL`; the old instrument confirmed
blind to `Z5`; ITEM 1's replacement wording **true of the class it quantifies over**; `src/` unmoved;
and `F16G-03` either shown to be narrower than the Engineer feared **or** carried as a named `AMBER`
condition.

**IF THE REPLACEMENT SENTENCE IS FALSE IN THE REASSURING DIRECTION AGAIN, THAT IS A `RED` AND YOU
SHOULD SAY SO WITHOUT SOFTENING IT.**
