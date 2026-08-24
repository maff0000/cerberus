# WO-3 INCREMENT 16E — PLANT SET

**Increment:** `16E-CONTROL-ROW` · **Dispatch:** `CD-D-182` · **Seat:** `CD-ENG-WO3-13`
**Authority:** `PO-DECISIONS-0030` rulings 1, 2, 3
**Content tip these figures were measured at:** `ed7263a31d371b8d4b7a0be8939e226870548963`
**Base (content) preserved:** `0e80a09af9661a9e7e6bb73193fbe56133fcff29` — **nothing under `src/`
changed and nothing was reverted.**

---

## What this plant set exists to measure

**`A312-F1`: the stale half of `CD-AC-001` was TRUE at the tip and UNGUARDED at the tip.** On a
tree with the entire fourth refusal stage deleted, **all thirty register `execute:` lines produced
a per-line rc list `diff`-IDENTICAL to the clean tip.** This set re-runs that exact measurement at
the new tip. **The acceptance test is that the `diff` is NO LONGER EMPTY, and that the rows which
move are the new ones.**

**IT REUSES `plants/WO3-INC16D/`'s `D1`-`D4` AND `H1`-`H4` PATCHES UNMODIFIED.** Re-cutting the
plants for the increment that answers them would be marking one's own paper: the arms that produced
the AMBER are the arms this row must be measured against, byte for byte.

## Files

| file | what it is |
|---|---|
| `run_register.sh <tree>` | runs EVERY `execute:` line the register declares in the named tree. rc **TAKEN FROM THE COMMAND**, never from a pipe (`CD-ENG-F02`'s defect class). The line count is **not hard-coded** — it is whatever that tree's register declares. **This script is the acceptance test.** |
| `run_arms.sh <sha> <label> [repo]` | one pristine `git archive \| tar -x` extraction per arm, patch read from an **ABSOLUTE path outside every extraction**, `git apply` rc **taken and checked**, arm **ABORTED LOUDLY** on any non-zero. Runs the new row, the sibling row, the pytest witness and the live-gate probe on each arm. |
| `eng13_probe.py <tree>` | this seat's own live-gate probe. **It takes the tree as `argv[1]`.** |

### *** THE TWO METHOD TRAPS THIS SET EXISTS NOT TO FALL INTO ***

1. **`CD-ASR-WO3-11` disclosed against itself** that its arm runner read each patch **from inside
   the extracted tree**, where it did not exist at the older tip; `git apply` returned **128**, and
   the instrument then ran on an **UNPATCHED** tree — **measuring nothing while looking like a
   result.** Here the patches are read from `$REPO/plants/WO3-INC16D/`, outside every extraction,
   and every `git apply` rc is taken into a variable and checked.

2. **`plants/WO3-INC16D/probe_16d.py` HARD-CODES `sys.path.insert(0,
   "/srv/crash-detector-wo3/src")`** and therefore measures **THE LANE** whichever tree it is
   pointed at. Reusing it on a patched extraction produces a clean result that means nothing and
   reads like a refutation. `eng13_probe.py` takes the tree as `argv[1]` and prints the resolved
   `crash_detector.__file__` on its last line so a reader can see which tree produced the table.

---

## *** THE ACCEPTANCE TEST — THE PER-LINE REGISTER rc DIFF ON `D1` ***

`run_register.sh` on a pristine extraction of `ed7263a`, and on a pristine extraction of `ed7263a`
carrying `D1-THE-FOURTH-STAGE-REMOVED.patch` (`git apply` **rc=0, TAKEN AND CHECKED**):

```
CLEAN: TOTAL lines=32 rc0=21 nonzero=11
D1   : TOTAL lines=32 rc0=19 nonzero=13

$ diff <(grep '^LINE' reg_new_clean.txt) <(grep '^LINE' reg_new_d1.txt)
4,5c4,5
< LINE 04 rc=0 yaml:1488 :: python3 tools/register/check_stale_data_never_calm.py --root .
< LINE 05 rc=0 yaml:1613 :: PYTHONPATH=src python3 -m pytest tests/test_envelope_freshness.py -q
---
> LINE 04 rc=1 yaml:1488 :: python3 tools/register/check_stale_data_never_calm.py --root .
> LINE 05 rc=1 yaml:1613 :: PYTHONPATH=src python3 -m pytest tests/test_envelope_freshness.py -q
diff rc=1
```

**THE DIFF IS NO LONGER EMPTY. EXACTLY TWO LINES MOVE AND BOTH OF THEM ARE THE NEW ONES. EVERY
OTHER LINE IS UNCHANGED**, so nothing that was already guarded moved and nothing that was already
non-zero became zero.

**FOR CONTRAST, THE SAME COMMAND AT THE BASE, RUN BY THIS SEAT AND NOT RELAYED:**

```
BASE CLEAN (ef3c960): TOTAL lines=30 rc0=19 nonzero=11
BASE + D1           : TOTAL lines=30 rc0=19 nonzero=11
diff of the per-line rc lists: EMPTY   <<< A312-F1, REPRODUCED IN THIS SEAT'S OWN SHELL >>>
```

## The four `D` arms at `ed7263a`, each from its own pristine extraction

| arm | `git apply` | NEW ROW `CD-RT-001-STALE-DATA-NEVER-CALM` | witness `tests/test_envelope_freshness.py` | sibling `CD-RT-001-MISSING-DATA-NEVER-CALM` | register lines that move |
|---|---|---|---|---|---|
| `CTRL` | no patch | `PASS — 97 assertions, 0 violations`, exit `0` | `92 passed`, exit `0` | `PASS — 260`, exit `0` | — |
| `D1` the whole stage removed | rc=0 | **`FAIL — 12 violation(s)`, exit `1`** — 12x `CD-STALE-GATE-001` | **`14 failed, 78 passed`**, exit `1` | `PASS — 260`, exit `0` | **04, 05** |
| `D2` naive `age > window` | rc=0 | **`FAIL — 4 violation(s)`, exit `1`** — 4x `CD-STALE-GATE-001` | **`2 failed, 90 passed`**, exit `1` | `PASS — 260`, exit `0` | **04, 05** |
| `D3` the forbidden slot-read | rc=0 | **`FAIL — 12 violation(s)`, exit `1`** — 6x `CD-STALE-NODES-004`, 4x `CD-STALE-CLOSED-006`, 2x `CD-STALE-OLDEST-005` | **`40 failed, 52 passed`**, exit `1` | `PASS — 260`, exit `0` | **04, 05**, and `07` (see below) |
| `D4` newest-stamp governs | rc=0 | **`FAIL — 2 violation(s)`, exit `1`** — 2x `CD-STALE-OLDEST-005` | **`2 failed, 90 passed`**, exit `1` | `PASS — 260`, exit `0` | **04, 05** |

**THE NEW ROW CATCHES ALL FOUR. IT IS SAID THAT WAY BECAUSE IT WAS MEASURED THAT WAY, AND THE
DISPATCH WAS EXPLICIT THAT SAYING HONESTLY THAT A ROW MISSES ONE WOULD BE WORTH MORE THAN CLAIMING
OTHERWISE.**

### *** AND ONE THING THIS ROW MUST NOT TAKE CREDIT FOR — `D3` WAS NEVER FULLY UNGUARDED ***

**MEASURED AT THE BASE TIP `ef3c960`, BEFORE THIS INCREMENT:** `D3` already moved **one** register
line — `LINE 05 python3 tools/register/check_no_blend.py --root .`, rc 0 -> 1. `D2` and `D4` moved
nothing; `D1` moved nothing. So the sentence *"all four arms leave the whole register unmoved"* is
**TRUE OF `D1`, `D2` AND `D4` AND FALSE OF `D3`**, and no inherited record claims otherwise —
`A312-F1`'s sentence about `D2`/`D3`/`D4` is specifically that they *"each leave the register at
`PASS — 260`, exit 0"*, which is about `LINE 03` and is true.

**AND `check_no_blend` IS NOT A GUARD ON THIS CLASS.** It fires on `D3` **for a different
criterion and by accident of spelling**: `D3` writes `for slot in ("equity_crash",
"monetary_debasement")` and `check_no_blend` reports RULE 1 / RULE 2 of `CD-AC-002` — *"one
expression consumes both dials"*. A slot-reading implementation that read **one** dial, or read the
two in **separate expressions**, would not trip it at all. The catch that is about **freshness** is
`CD-STALE-NODES-004`'s.

## The four `H` arms at `ed7263a` — the row that must NOT move, and does not

| arm | `git apply` | NEW ROW | sibling |
|---|---|---|---|
| `H1` `degraded_inputs` widened to an array of closed objects | rc=0 | `PASS — 97`, exit `0` | **`FAIL — 2`, exit `1`** |
| `H2` array of open objects, capable by openness | rc=0 | `PASS — 97`, exit `0` | **`FAIL — 2`, exit `1`** |
| `H3` array of arrays, two containers deeper | rc=0 | `PASS — 97`, exit `0` | **`FAIL — 2`, exit `1`** |
| `H4` undecidable limb (b), `allOf` on `regime` | rc=0 | `PASS — 97`, exit `0` | **`FAIL — 2`, exit `1`** |

**NEITHER ROW COVERS THE OTHER, AND THAT IS THE POINT OF HAVING BOTH.** The `H` arms widen the
CONTRACT so a non-dial root property could carry `calm`; the sibling row's `_can_carry_detail_level`
catches every one of them and this row catches none, because this row is about AGE. The `D` arms
weaken the AGE COMPARISON; this row catches every one of them and the sibling catches none. **A
report that quotes one row is half a report.**

## The vacuity arms — measured on every tree above, both surfaces

```
                                     ARM CTRL @ ed7263a
STALE-1970-CALM      MUST REFUSE     PUBLIC=REFUSED [STALE_CALM] at /equity_crash   PRIVATE=REFUSED [STALE_CALM] at /equity_crash
FUTURE-2099-CALM     MUST REFUSE     PUBLIC=REFUSED [STALE_CALM] at /equity_crash   PRIVATE=REFUSED [STALE_CALM] at /equity_crash
BOUNDARY-600s-CALM   MUST ADMIT      PUBLIC=ADMITTED                                PRIVATE=ADMITTED
BOUNDARY-600s+1us    MUST REFUSE     PUBLIC=REFUSED [STALE_CALM] at /equity_crash   PRIVATE=REFUSED [STALE_CALM] at /equity_crash
FRESH-CALM           MUST ADMIT      PUBLIC=ADMITTED                                PRIVATE=ADMITTED
STALE-1970-ELEVATED  MUST ADMIT      PUBLIC=ADMITTED                                PRIVATE=ADMITTED
STALE-1970-ACUTE     MUST ADMIT      PUBLIC=ADMITTED                                PRIVATE=ADMITTED
```

*** THE VACUOUS DIRECTION IS EQUALLY A VIOLATION OF THIS ROW AND IT IS THE HALF THIS PROJECT'S
HISTORY SAYS GETS MISSED. *** **FRESH-CALM IS STILL ADMITTED ON BOTH SURFACES AND
`1970` + `elevated` IS STILL ADMITTED ON BOTH SURFACES**, at the clean tip and on every `H` arm.
The instrument asserts both itself (`CD-STALE-GATE-001`'s MUST-ADMIT rows) and asserts that its own
table still contains them (`CD-STALE-VACUITY-000`), so the admitting arms cannot be quietly deleted
from the instrument that exists to carry them.

## Reproducing all of it

```bash
git archive ed7263a | tar -x -C /tmp/x_clean
plants/WO3-INC16E/run_register.sh /tmp/x_clean

git archive ed7263a | tar -x -C /tmp/x_d1
( cd /tmp/x_d1 && git apply --unsafe-paths --directory=. \
    /srv/crash-detector-wo3/plants/WO3-INC16D/D1-THE-FOURTH-STAGE-REMOVED.patch ) ; echo "rc=$?"
plants/WO3-INC16E/run_register.sh /tmp/x_d1

diff <(grep '^LINE' <clean output>) <(grep '^LINE' <d1 output>)   # MUST NOT be empty

plants/WO3-INC16E/run_arms.sh ed7263a NEWTIP        # all nine arms
```

**No figure in this file is inherited. Every one was produced by the commands above, in this seat's
own shell, on its own extractions** (`CD-PL-F193`).
