# CD-DISPATCH-INC16B-FIX2-ENGINEER

**role source:** `pbg/roles/engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `CD-ASR-WO3-06`'s `AMBER` at `c7471dc`
(`BL-20260824T114609Z-A306.yaml`, branch `asr-wo3-06-verdict`), findings **F1** and **F2** ·
`CD-PL-F188` (two `CD-RULE-004` places owed) · reproduced by the Project Lead at
`BL-20260824T115318Z-0166` · `PO-DECISIONS-0026` rulings 9 and 5
**seat identity:** `CD-ENG-WO3-07` — **FRESH.** **Never `CD-ENG-WO3-06` (which built what you are
repairing)**, **never `CD-ASR-WO3-06` (which found F1 and F2 — `PBG-SOD-004`)**, never
`CD-ENG-WO3-01`…`-05`, never `CD-ASR-WO3-01`…`-05`, never any `CD-ENG-WO2R3-*` / `CD-ENG-COORD*`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **increment:** 16B-FIX-2 · **expected return:**
`READY_FOR_ASSURANCE`

---

## 0. WHY THIS EXISTS, AND WHY IT BLOCKS THE NEXT INCREMENT

The instrument is good and getting better: an independent seat brought **four** shapes at the branch
recogniser and **it failed closed on all four**. Two escapes remain, and **one of them is the next
increment.**

*** **`PO-DECISIONS-0026` RULING 5 IS THREE QUANTITIES, THE MIDDLE ONE A LIVENESS / DEAD-FEED
SIGNAL. WRITTEN THE OBVIOUS WAY — AS A THIRD ROOT PROPERTY — IT WALKS STRAIGHT THROUGH THIS GUARD.
THE PROJECT LEAD BUILT THAT INCREMENT'S SCHEMA CHANGE AND MEASURED IT: THE LIVE GATE **ADMITS A DEAD
FEED RENDERING AS CALM** ON BOTH SURFACES, AND THE INSTRUMENT REPORTS `PASS — 144 assertions, 0
violations`.** *** `CD-AC-001`'s own words are *"missing **or stale** input never renders as calm"*.
**So 16C cannot be dispatched until you are done. That is the ordering constraint and the auditor
named it before the Project Lead did.**

---

## 1. THE LANE

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       64cd5b2  (16B-FIX — assured AMBER at c7471dc, banked, NOT accepted; content tip af3825c)
base      be0b355  (FROZEN — READ-ONLY)
verdict   c7471dc on branch asr-wo3-06-verdict — BL-20260824T114609Z-A306.yaml
```

**READ `BL-20260824T114609Z-A306.yaml` IN FULL FIRST.** Both findings carry a **prescription the
auditor deliberately left unwritten**, in the auditor's own words, with the trees and the commands.
This dispatch does not replace it.

**WRITABLE SCOPE:**

* `tools/register/check_missing_data_never_calm.py`
* `contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`
* **`contracts/execution/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.md`** — *newly granted, see FX8*
* `required-tests.yaml` — the `CD-AC-001` block only
* **`tests/test_detail_level.py` — MODULE DOCSTRING ONLY (see FX8). No assertion may change; the
  file must still report `52 passed`.**
* `plants/WO3-INC16B/**` — adding arms; **C1–C10 are not to be edited**
* `governance/engineering/build-log/**` — your own return record

**PROTECTED — ZERO PATHS, PROVED BY COMMAND:** `pbg/**` · `BLUEPRINT.md` · `PID.md` ·
`governance/decisions/**` · `governance/mapping/**` · **both envelope schemas** · `src/**` ·
`deploy/**` · `db/**` · `tests/**` **except the one docstring** · `tools/**` except your one file ·
`evidence/**` · everything at `be0b355`.

---

## 2. FX5 — F1: A BRANCH WHOSE SHAPE IS CONDITIONAL IS A BRANCH YOU HAVE NOT DRIVEN

**The branch SET is closed. The branch SHAPE is not.** `_dial_from_branch` reads a branch's
`required` and `properties` **and nothing else** — never `if`/`then`/`else`, `allOf`, `anyOf`,
`oneOf`, `not`, `dependentSchemas`. So it builds **exactly one document per branch**, and a branch
whose admissible shape is *conditional* has variants it never constructs.

**Auditor tree `X2`, measured:** `dial_reading_unknown` keeps its name, its `state.const`, its
`required` list and `additionalProperties: false`; `properties.detail_level` is widened; the
narrowing is relocated into `"if": {"required": ["render_hint"]}` with an `"else"` carrying a fully
closed copy. Result: instrument **`PASS — 144 assertions, 0 violations`**, the live gate **ADMITTED
on both surfaces**, the control (same dial, no marker) still REFUSED, and **exactly one of the 30
`execute:` lines moves.**

*** **AND THE IDENTITY OF THAT ONE SURVIVING CATCHER IS THE FINDING'S SHARPEST EDGE: it is
`tests/test_detail_level.py`, and the five assertions that fail are all LITERAL-NAME STRUCTURAL
READS. `test_missing_data_never_renders_as_calm_THROUGH_THE_LIVE_GATE` — the behavioural arm, the
acceptance property — PASSES ON `X2`. So on that tree the behavioural guarantee is carried by
nothing behavioural: it is carried by a `$ref`-name equality in a pytest file. THAT IS EXACTLY THE
"MEMORIAL IN TESTS" RULING 9 SAID THE GUARANTEE MUST NOT BE LEFT IN.** ***

**And two open items on this row point in opposite directions, which nobody had noticed:**
`CD-ASR-WO3-05` F6 and `DECLARED LIMIT 12` both record that name coupling as a *cost*, and one of
F6's named remedies is to follow the `$ref` instead of matching its target's name. **Adopt that
remedy and `X2` becomes invisible to the entire register.** *(The Project Lead's FX4 ruling already
declined that remedy — this is now a second, independent reason it was the right call, and you
should say so if you agree.)*

**BUILD — the auditor's prescription, written deny-by-default because enumerating conditional
shapes is a larger piece of work than this row should absorb:** in `_dial_from_branch`, **before
building**, test the resolved branch for any of `if` / `then` / `else` / `allOf` / `anyOf` /
`oneOf` / `not` / `dependentSchemas` / `dependentRequired` / `unevaluatedProperties`; where any is
present, **return the branch as UNBUILDABLE so it is reported** — *"a branch whose shape is
conditional is a branch this check cannot say it has driven"*, which is the sentence `DECLARED
LIMIT 9` already writes for a property it cannot synthesise. **The auditor verified the clean tree
carries none of those keywords inside any branch, so this costs nothing today and turns `X2` red.**

**The stronger form — one candidate per satisfiable combination of optional markers — is a design
question the auditor correctly refused to decide. PROJECT LEAD RULING: DO NOT BUILD IT. Deny by
default now; if a legitimate conditional branch is ever needed, that is the increment that prices
it.**

---

## 3. FX6 — F2: `CD-CALM-SLOTS-007` IS A PATTERN RECOGNISER WEARING DENY-BY-DEFAULT'S CLOTHES

`_dial_bearing` asks whether a root property's `state` `const`/`enum` **intersects
`DECLARED_STATES`**. If it does not, it returns **`False` — not `None`, not undecidable.** So a root
property that is a dial in every respect the product cares about, but whose state vocabulary is
**new**, is classified *not a dial* and is **silent**.

**The pair that proves it is the vocabulary and not the shape** — both optional root properties,
identical bodies:

```
B6  state {"const": "NO_DATA"}              -> instrument PASS 144/0 ; gate ADMITS calm
B5  state {"enum": ["UNKNOWN","STALE"]}     -> instrument FAIL — 2 violations (SLOTS-007)
```

**The only difference between a caught tree and an uncaught one is whether the new dial reuses an
old state NAME.** That is guard-the-instance-not-the-class, and **`PO-DECISIONS-0026` ruling 10
exists because this estate has paid for that game repeatedly.**

**And the Project Lead reproduced the 16C form of it (`B4`) independently:** an optional root
`feed_liveness`, states `["LIVE","STALE"]`, full `detail_level` vocabulary —

```
control (no liveness quantity)  ADMITTED   <- the tree is not broken
feed_liveness STALE + "calm"    *** ADMITTED on PUBLIC and PRIVATE ***
instrument                      PASS — 144 assertions, 0 violations
```

**BUILD — the auditor's prescription:** in `_dial_bearing`, a resolved subschema that **declares** a
`state` property whose `const`/`enum` does **not** intersect `DECLARED_STATES` must return **`None`
(UNDECIDABLE)** rather than falling through to `False`. *"I cannot classify this state vocabulary"*
is precisely the case `DECLARED LIMIT 8` says must stop the check, **and the `undecidable` limb of
`CD-CALM-SLOTS-007` already exists to report it with the right words.**

**The auditor offered a tighter variant (require both a `state` and a `detail_level` property) and
left the choice to the Project Lead. RULED: TAKE THE LOOSER, LOUDER FORM — `state`-declaring is
enough.** A false positive here costs one seat one look at one contract; a false negative costs the
constitution. **If you find the loose form fires on something legitimate in the clean tree, stop and
say so — that measurement would change the ruling.**

---

## 4. FX7 — `DECLARED LIMIT 4`'s CORRECTION IS FALSE IN THE SAME WAY, IN THE SAME THREE PLACES

16B-FIX superseded limit 4 and **the replacement sentence is also bigger than the code.** It claims
`CD-CALM-SLOTS-007` *"enumerates every root property that constrains a dial `state` under ANY
spelling and FAILS … if that set is not exactly the driven set, or if any root property's shape
cannot be decided at all."* **`B6` is a root property that constrains a dial `state` — to the single
value `NO_DATA` — its shape is decidable, it is not in the driven set, and the check did not fail.**

**BUILD:** re-correct it **by supersession, in all three `CD-RULE-004` places** (the instrument
header, the `required-tests.yaml` comment, `contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`).
*** **THE FORM WAS IMPECCABLE LAST TIME AND THE AUDITOR SAID SO — what failed was that the new claim
was still larger than the code. So this time: WRITE THE SENTENCE LAST, after FX6 is measured, and
make it describe what you measured rather than what you intended.** ***

---

## 5. FX8 — CLOSE `CD-PL-F188`: THE TWO OWED `CD-RULE-004` PLACES

`DECLARED LIMIT 12` (the `D3` name-coupling declaration) landed in **one** of its three places. Your
predecessor could not reach the other two — **it declared the shortfall instead of widening its own
scope, which was correct** — and this dispatch grants them:

* `contracts/execution/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.md` — the declaration in full
* `tests/test_detail_level.py` — **module docstring ONLY.** *(The FX4 ruling protects that file's
  assertions, not its prose. `52 passed` must be unchanged and no assertion may move.)*

**Also, and the auditor is the only one who noticed:** `DECLARED LIMIT 12` **has no counterpart 10
or 11 anywhere**, and the sibling row's limit list runs 1–9, so a reader cannot verify the numbering
is consistent between two rows sharing one file. **Fix the numbering or declare why it is what it
is. Do not leave a reader unable to check.**

---

## 6. YOUR CONTRAST SET

Added under `plants/WO3-INC16B/`, **C1–C10 untouched**, established MANIFEST form with **`git
apply`'s own exit code as its own column**, **every arm from its own pristine extraction, never the
worktree** (`CD-PL-F154`):

| # | Arm | Must |
|---|---|---|
| **C11** | the conditional-branch tree (auditor `X2`) | **FAIL** |
| **C12** | its careless precursor (`X1`, bare `else`) | **FAIL** |
| **C13** | the new-state-vocabulary root dial (auditor `B6`, `NO_DATA`) | **FAIL** |
| **C14** | **the 16C liveness quantity (auditor `B4` / the PL's reproduction)** | **FAIL** |
| **C15** | *(CONTROL — MUST STILL PASS)* the symmetric fourth level, i.e. C10 re-run | **PASS** |

**AND RE-RUN C1–C10 UNCHANGED.** `C10` at `PASS — 158 assertions, 0 violations` and `C6` at
`FAIL — 6` (4× `GATE-001` + 2× `BRANCHES-006`) are the two that would show a regression first.
**A fix that quietly stops an existing arm from biting is a regression, and your predecessor's first
generation of arms silently failed to apply and all five falsely read `PASS` — the exit-code column
caught it. Trust the column, not the outcome.**

---

## 7. WHAT IS NOT IN THIS INCREMENT

**Do not implement 16C.** You are making the guard able to *see* a liveness quantity; you are not
adding one. **No new root property, no new dial state, no schema edit of any kind** — both envelope
schemas are protected and your plants live in `/tmp` extractions.

Also out: `CD-PL-F180` / the contract-bytes route (16D, re-scoped to the bytes) and the instrument's
**exit 3**, which two auditors have now ruled correct · `STALENESS_WINDOW_CEILING_SECONDS` (16C) ·
the no-blend structural closure, host-coupling, version discrimination (16D) · registering any
indicator row (16E) · anything under `pbg/`.

---

## 8. YOUR RETURN

**BOOT FIRST**; the inherited `RED` (`ACTIVE_WORK.yaml`, blob `ce0803c3`, verified by four seats) is
the frozen base's — **diagnose, do not repair.**

Each item backed by a command whose output you paste:

1. **C11–C14 each FAILING**, with violation codes; **C15 PASSING**.
2. **C1–C10 re-run and unchanged** — `C6` and `C10` called out explicitly.
3. Clean worktree exit **0**, with the new assertion count.
4. `pytest tests/ -q` — **no regression from 2007**; `tests/test_detail_level.py` still **52 passed**.
5. Register: `pid.content_hash MATCHES` · **18** criteria · `GATE: SHUT` · `latest_admitted_run (null)`.
6. **The re-superseded limit 4, quoted in all three places** — what it said, that it was false, what
   is true instead — **written after FX6 was measured.**
7. `DECLARED LIMIT 12` in all three places, and the numbering resolved.
8. Scope proof by command over every protected path; **`tests/test_detail_level.py` diff shown in
   full to prove it is docstring-only.**
9. **ONE identity**, `git log --format='%an' 64cd5b2..HEAD | sort -u`.
10. **Your declared limits**, including any new one your fix introduces.
11. **Your findings against this dispatch.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ENG-WO3-07 GIT_AUTHOR_EMAIL=cd-eng-wo3-07@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-07 GIT_COMMITTER_EMAIL=cd-eng-wo3-07@seats.crash-detector.invalid \
git commit -m "..."
```

**COMMIT AT EVERY BOUNDARY** (`PBG-CONT-007`). **YOU DO NOT CERTIFY YOUR OWN WORK** — a fresh
Assurance seat follows (`PBG-SOD-001`, non-waivable).

**STOP AND RETURN if:** a fix needs a file outside §1 · FX6's looser form fires on something
legitimate in the clean tree · FX5's deny-by-default turns any *existing* arm or the clean tree red ·
**or you find any statement in this dispatch to be false.** *** **FIVE CONSECUTIVE DISPATCHES ON
THIS LANE HAVE CONTAINED A FALSE STATEMENT A SEAT CAUGHT — AND THE LAST ONE, `CD-PL-F190`,
MISDESCRIBED THE VERY MECHANISM IT ORDERED THE SEAT TO ATTACK. ASSUME THIS ONE DOES TOO.** ***
