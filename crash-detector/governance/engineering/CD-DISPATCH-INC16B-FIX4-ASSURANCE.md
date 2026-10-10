# CD-DISPATCH-INC16B-FIX4-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `CD-ASR-WO3-08`'s `AMBER` at `3174753` and its F1/F2 ·
`CD-DISPATCH-INC16B-FIX4-ENGINEER` (`9a3a1f7` on `main`) · `PO-DECISIONS-0026` rulings 9 and 10 ·
`PBG-SOD-001` / `PBG-SOD-004`, non-waivable
**seat identity:** `CD-ASR-WO3-09` — **FRESH.** **Never `CD-ENG-WO3-09` (which built the fix)**,
**never `CD-ASR-WO3-08` (which found F1)**, never `CD-ENG-WO3-01`…`-08`, never `CD-ASR-WO3-01`…`-07`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **expected return:** `PASS` / `AMBER` / `RED`.

---

## 1. THE TARGET

```
branch    wo-3
tip       dd4040773958da5a63d533fdcb6e61b0d410cf85   <- YOUR TARGET (content tip 4e6f7c4)
prior     4d797e6  (16B-FIX-3 — assured AMBER at 3174753)
base      be0b355  (FROZEN)
the AMBER 3174753 on branch asr-wo3-08-verdict — BL-20260824T134814Z-A308.yaml — READ IT IN FULL
the return governance/engineering/build-log/BL-20260824T142722Z-16B4.yaml on the lane — READ IT TOO
```

**MUTATION PROHIBITED** except `/tmp` trees, your own extractions, and your own verdict on your own
branch (suggested `asr-wo3-09-verdict`). **Get your own tree.**

---

## 2. ESTABLISHED — DO NOT RE-CONFIRM

Reproduced by the Project Lead from its own plants at your target:

```
its own patternProperties plant   was PASS — 144/0 with the gate ADMITTING a dead feed as calm
                                  on BOTH surfaces;  now FAIL — 2 (CD-CALM-SLOTS-007)
a spelling the PL INVENTED — `propertys`, a one-letter typo of `properties`, appearing NOWHERE
                                  in the instrument —  FAIL — 2
C28/C10 CONTROL   PASS — 158        clean worktree   PASS — 144, exit 0
scope   both envelope schemas BYTE-UNTOUCHED; zero protected paths; ONE identity
```

*** **THE FALSIFIER PASSED INDEPENDENTLY. The class fix catches spellings that are not on any list,
including one nobody in the chain has ever written down. That is the first time in five rounds that
has been true, and it is why this verdict matters.** ***

---

## 3. WHERE TO ATTACK

### 3.1 — *** `_INERT_KEYWORDS`, BECAUSE THE BUILDER SENT YOU THERE ***

The inversion is sound **only if the set of keywords declared inert is genuinely inert.** The seat's
own `DECLARED LIMIT 15`: ***"`_INERT_KEYWORDS` is a READING of the spec, not a measurement. If one
member can carry a subschema or name a property, the inversion has a hole exactly that size — in
the safe-looking direction."*** **The seat said it would send you here first. Go.**

Take the list member by member. **Can any of them carry a subschema, name a property, or otherwise
introduce a `state`?** `contentSchema` and `propertyNames` are the shapes to think hardest about,
and `$defs`/`$anchor`/`$comment`/`title`/`format` deserve a moment each. **One member that is not
inert is the fifth escape, and it will look exactly like the previous four.**

### 3.2 — THE `True` SHORT-CIRCUIT AND THE BRANCH/ROOT DISAGREEMENT

The seat declares two more limits honestly: **the `True` short-circuit is "reasoned, not proved"**,
and **FX12 is at the root-property recogniser only — nobody has proved it agrees with the branch
side.** Two recognisers with different notions of "readable" in one file is one edit from a hole.
**Measure the disagreement: is there a shape the branch side reads and the root side denies, or
vice versa?**

### 3.3 — GRADE THE FALSIFIER ITSELF

`C27` is the ruling's own falsifier and the seat reports it passing on four never-named spellings —
including `propertyDependencies` (a post-2020-12 proposal), an `x-` vendor keyword, an invented
`slotShape`, and the `propertys` typo — each `grep -c` **0** in the instrument. **Verify at least
two yourself, invent a fifth of your own, and say whether the deny class really is the complement of
a finite written set or whether that is a description of the code rather than a property of it.**

**And check the seat's honesty about `$recursiveRef`: it discarded that probe because it makes the
contract an invalid schema — "fail-closed for the wrong reason". Was discarding it right?**

### 3.4 — THE FALSE-POSITIVE TAIL, WHICH IS NOW REAL

**Six benign root properties are newly red, including an ordinary custom `x-` annotation**, priced
as `DECLARED LIMIT 14`. The Project Lead's standing ruling — a false positive costs one seat one
look, a false negative costs the constitution — **holds, and is not a licence to be careless about
the count.** **Is the tail honestly measured and honestly bounded, or is it larger than eight?**
**And does it fire on anything a real 16C contract would plausibly carry?**

### 3.5 — THE USUAL, AND IT HAS CAUGHT THINGS EVERY ROUND

Nothing dropped (the seat claims the clean-tree output is **byte-identical before and after but for
the path string** — verify). `C1`–`C21` re-run from **your own** extractions with `git apply`'s exit
code; **do not take the MANIFEST's word for its own column.** `C28` `PASS — 158`. Register `MATCHES`
/ **18** / `SHUT` / `null`; `be0b355` unmoved; `evidence/` unwritten; `pytest` **2007** and
`test_detail_level.py` **52**. FX13 (`_SUBSCHEMA_KEYWORDS` named as the wrong constant) and FX14
(**re-measured by the seat: 108 combinations, 11 hits for the true clause and 0 for the false one**,
superseded in four places) — **are the new sentences finally no bigger than the code? Three on this
row have already failed that test.**

---

## 4. THE DECISION YOUR VERDICT GATES

**16C is held.** `CD-ASR-WO3-07` judged it releasable with two conditions; **`CD-ASR-WO3-08`
WITHDREW that judgement** after arm `FINAL` — 16C landed honestly — produced a green instrument and
an admitted `calm`.

*** **SO ANSWER, IN THESE WORDS: WOULD THIS GUARD SEE 16C GO WRONG? And answer the sharper form the
builder itself raised: it measured that `$dynamicRef` (C24) and the over-cap `$ref` chain (C25)
landed with THE ENTIRE THIRTY-LINE REGISTER GREEN — `PASS — 292` and `PASS — 452` — while the gate
admitted a dead feed as `calm`. TWO CLEAN ESCAPES SURVIVED EVERY OTHER INSTRUMENT IN THE REPOSITORY
AT THE PRIOR TIP. VERIFY THAT THEY DO NOT NOW, AND SAY WHETHER ANYTHING ELSE STILL DOES.** ***

If you return clean, **name the conditions you would attach to 16C's dispatch** — you are the seat
best placed to write them.

---

## 5. OUT OF SCOPE

`CD-PL-F180` / contract-bytes and **exit 3** (four auditors) · `DECLARED LIMIT 12`'s
differently-named discriminator (judged honestly drawn) · `REF_INERT_SIBLINGS` (**proved an empty
class — do not spend budget there**) · `STALENESS_WINDOW_CEILING_SECONDS` and 16C · no-blend,
host-coupling, version (16D) · indicator registration (16E) · `pbg/` (report, do not repair). The
boot `RED` (blob `ce0803c3`) is the frozen base's — nine seats. **Diagnose and leave it.**

---

## 6. FINDINGS ALREADY ON THE RECORD AGAINST THE PROJECT LEAD

`CD-PL-F197`: the previous dispatch **ordered a mechanism that was technically wrong**, an Engineer
refused it, and an independent auditor found for the Engineer. `CD-PL-F198`: the dispatch before
that **aimed its primary attack at a provably empty class.** **Ten consecutive dispatches on this
lane have contained a false statement a seat caught. Assume this one does too and grade it as you
grade the code.**

**And the builder has already reported one against itself AND against the audit** (its F01): A308's
claim that the register moves only one line **does not survive 16C paying its friction** —
`patternProperties` is caught by `check_schema_closed` rule 2 once the allowlist is paid. **It
narrowed its own dispatch's headline sentence from five keywords to two, on measurement. Check that
narrowing.**

---

## 7. YOUR RETURN

`PASS` / `AMBER` / `RED` naming the exact SHA, the next safe gate, and: (1) verdict and gate;
(2) every probe with command and output; (3) **§3.1 answered — `_INERT_KEYWORDS` member by member**;
(4) **§3.3 answered — your own invented spelling**; (5) **§4 answered in its own words, including
the C24/C25 whole-register check**; (6) every shape it did not catch and every correct tree you made
it fail on; (7) `be0b355` unmoved, register `MATCHES` / **18** / `SHUT` / `null`, `evidence/`
unwritten; (8) **your findings against this dispatch**; (9) **if clean, the conditions you would
attach to 16C's dispatch.**

**You did not build this and YOU MAY NOT REPAIR IT.** Prescription written, line left unwritten.

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ASR-WO3-09 GIT_AUTHOR_EMAIL=cd-asr-wo3-09@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ASR-WO3-09 GIT_COMMITTER_EMAIL=cd-asr-wo3-09@seats.crash-detector.invalid \
git commit -m "..."
```

**Bank your verdict as a Build Log entry on your own branch** (`PBG-CONT-007`).

*** **THE STANDARD: FOUR SUCCESSIVE SEATS IN YOUR CHAIR BROKE THEIR TARGET. THIS IS THE FIRST ROUND
WHERE THE FIX CATCHES SPELLINGS THAT ARE ON NO LIST. IF YOU CANNOT BREAK IT, SAY SO PLAINLY AND SAY
HOW HARD YOU TRIED — A CLEAN VERDICT HONESTLY EARNED IS WHAT RELEASES 16C, AND A DISHONEST ONE
PUBLISHES A DEAD FEED AS CALM.** ***
