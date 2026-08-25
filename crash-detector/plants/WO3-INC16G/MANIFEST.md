# WO-3 INCREMENT 16G — PLANT SET

**Increment:** `16G-TRUE-REGARDLESS` · **Dispatch:** `CD-D-186` · **Seat:** `CD-ENG-WO3-15`
**Authority:** `CD-AUTH-0001`, carried through `PO-DECISIONS-0032` (commit `c734cb1`)
**Base:** `c475b8e75004a14481f39e63d09e86da3898195b` (content tip `7ac11c9`)
**Content preserved:** **nothing under `src/` changed.** `git diff --name-only c475b8e -- src/` ->
**0 paths**, and that is this increment's DECLARED STOP, not a side effect.

---

## What this plant set exists to measure

Two of the four `16G` items rest on a claim about what the two register rows DO NOT SEE. **A
CLAIM ABOUT A BLIND SPOT IS WORTHLESS UNLESS THE BLIND SPOT IS EXECUTABLE**, so both are arms
here, and the guard change has a control as well as a biting arm.

| arm | what it does | why it is here |
|---|---|---|
| `Z5` | `try/except PublicationRefused` around the freshness stage **INSIDE `refuse_unless_publishable`**, re-raising only when `config_snapshot_id != "BYPASS"` | `CD-ASR-F14-03`. **THE ARM THAT MUST BITE** after `CD-CHOKE-003` is widened to read the gate's own handlers |
| `Z5CTRL` | the SAME `try` shape whose handler ends in a bare `raise` | **THE VACUITY DIRECTION.** A control that failed on every `try` in the gate would be refusing a legitimate shape, not catching a swallow. This arm must STAY `PASS` |
| `Z7` | a `return` at the top of `_iter_nodes`, the SHARED DOCUMENT WALK | `CD-ASR-F14-02`. **THE COUNTEREXAMPLE THAT FALSIFIES `DECLARED LIMIT 9`'s CLOSING SENTENCE.** It is NOT fixed here and is NOT meant to be — `PO-DECISIONS-0032` ruling 3 records the class as owed later-hardening |

**`Z7` IS AN ARM THAT THIS INCREMENT DELIBERATELY LEAVES PASSING.** It is carried so the
superseded limit has something an auditor can execute, in the same way every other `DECLARED
LIMIT` on these two rows carries an `EXECUTABLE:` line. Reading it as unfinished work is the
misreading this paragraph exists to prevent.

## The arms are LIVE BYPASSES, not inert text

`CD-PL-F74`: a row that moves on an arm which does not actually publish anything is not
evidence. `eng15_probe.py` drives the live gate on both surfaces, and counts MUST-ADMIT refusals
separately so a refused baseline cannot be mistaken for a caught bypass.

```
python3 -B plants/WO3-INC16G/eng15_probe.py <tree>

CLEAN    ROWS=14  MUST-ADMIT ROWS REFUSED=0  STALE-CALM ADMISSIONS=0
Z5CTRL   ROWS=14  MUST-ADMIT ROWS REFUSED=0  STALE-CALM ADMISSIONS=0
Z5       ROWS=14  MUST-ADMIT ROWS REFUSED=0  STALE-CALM ADMISSIONS=2   <-- BOTH SURFACES
Z7       ROWS=14  MUST-ADMIT ROWS REFUSED=0  STALE-CALM ADMISSIONS=2   <-- BOTH SURFACES
```

**WHY A SECOND PROBE AND NOT `plants/WO3-INC16F/eng14_probe.py`.** That probe is sound and this
seat ran it; it simply cannot see these arms. It builds every document with
`config_snapshot_id = "SYNTHETIC-ENG14-PROBE-NOT-A-CONFIG"` and every dial with `score = 0.01`,
and these arms trigger on `"BYPASS"` and `0.1234`. **A PROBE THAT DOES NOT CARRY THE TRIGGER
MEASURES A DOCUMENT THE ARM DECLINED TO ATTACK AND WOULD REPORT ZERO ADMISSIONS ON A LIVE
BYPASS.**

## The row verdicts, BOTH DIRECTIONS, same harness, same host

`run_arms.sh` takes the instrument tree as `INSTRUMENTS=`, so BEFORE and AFTER are **the same
arms measured twice** and not two different experiments.

```
INSTRUMENTS=/tmp/inc16g/before OUT=/tmp/wo3-inc16g-BEFORE \
    bash plants/WO3-INC16G/run_arms.sh c475b8e      # /tmp/inc16g/before is a worktree at c475b8e
OUT=/tmp/wo3-inc16g-AFTER  bash plants/WO3-INC16G/run_arms.sh c475b8e

              CD-RT-001-PUBLICATION-CHOKEPOINT
              BEFORE (instrument at c475b8e)     AFTER (this tip)
  CLEAN       PASS — 11 assertions   rc=0        PASS — 11 assertions   rc=0
  Z5CTRL      PASS — 11 assertions   rc=0        PASS — 12 assertions   rc=0
  Z5          PASS — 11 assertions   rc=0        FAIL — 1 violation(s)  rc=1   <-- IT MOVES
  Z7          PASS — 11 assertions   rc=0        PASS — 11 assertions   rc=0   <-- DECLARED

              CD-RT-001-STALE-DATA-NEVER-CALM — UNMOVED ON EVERY ARM, BOTH DIRECTIONS
  all four    PASS — 142088 assertions, 0 violations   rc=0
```

**READ THE `Z5CTRL` ROW: `11 -> 12` ASSERTIONS.** That is the new assertion being MADE and
PASSING. Without it, `Z5` going `FAIL` would be consistent with a check that refuses any `try`
in the gate at all, and `CLEAN` staying at `11` would be consistent with dead code.

**AND READ THE `CLEAN` ROW: `11 -> 11`.** On a gate that wraps nothing the new pass contributes
ZERO assertions, which is `DECLARED LIMIT 8(a)` and is stated in the limit rather than left to
be found. It prints a NOTE carrying the count including `0`, so a clean run still shows it ran:

```
note: refuse_unless_publishable: 0 `try` statement(s) enclose its 4 stage call(s), carrying
      0 except handler(s) — CD-CHOKE-003 read the GATE'S OWN handlers, not only the chokepoint's
```

## No regression on the arms that already existed

Every `16F` arm that attacks the structural row, re-run under BOTH instruments, **rc taken from
the command and never from a pipe** (`CD-ENG-F02`'s defect class — which this seat fell into on
its first pass at this very table and re-ran; see `CD-ENG-F16G-01`):

```
C1 C2 C3 C4 C5 D1CTRL W5G N8   BEFORE rc=1 FAIL — 1 violation(s)   AFTER rc=1 FAIL — 1 violation(s)
C6                             BEFORE rc=1 FAIL — 2 violation(s)   AFTER rc=1 FAIL — 2 violation(s)
```

Nine arms, last line byte-identical on all nine.

## Files

| file | what it is |
|---|---|
| `run_arms.sh <sha> [repo]` | one pristine `git archive \| tar -x` extraction per arm; patch read from an **ABSOLUTE path outside every extraction**; `git apply` rc **taken into a variable and checked**; the arm **ABORTED LOUDLY** on any non-zero, and the inserted marker **grep-confirmed present in the extracted tree** before any instrument runs. `INSTRUMENTS=` selects which tree the checkers are read from. |
| `eng15_probe.py <tree>` | the live gate, 7 document shapes x 2 surfaces, carrying BOTH arms' triggers. Prints the resolved `crash_detector.__file__` so a reader can see which tree produced the table. |
| `Z5-...patch` `Z5CTRL-...patch` `Z7-...patch` | the three arms, authored from the LANE's pristine bytes with each anchor **asserted UNIQUE before a byte was replaced**. |

The whole-register per-line pass is `plants/WO3-INC16F/run_register.sh <tree>`, run unmodified by
this seat: **33 lines, rc0=22, nonzero=11 on the clean lane, `diff`-identical to the same script
on a pristine `c475b8e` extraction** once the moved YAML line numbers are normalised away.
