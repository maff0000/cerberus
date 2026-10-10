# CD-DISPATCH-INC16A-FIX-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `CD-ASR-WO3-03`'s `RED` at `b7f0439` · `PO-DECISIONS-0025` ruling 5 ·
`PBG-SOD-001` and `PBG-SOD-004`, both non-waivable · `CD-D-180`
**seat identity:** `CD-ASR-WO3-04` — **FRESH.** Never `CD-ENG-WO3-03` (built the defect), never
`CD-ENG-WO3-04` (fixed it), never `CD-ASR-WO3-03` (found it), never `CD-ENG-WO3-01`/`-02`, never
`CD-ASR-WO3-01`/`-02`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **expected return:** `PASS` / `AMBER` / `RED` with the next
safe gate named.

---

## 1. THE TARGET

```
branch    wo-3
tip       b9283b99f66285e8be575eb56e2d30ed52735be8    <- YOUR TARGET (code tip 3a08646)
prior     53f639a  (increment 16A — assured RED by CD-ASR-WO3-03)
base      be0b355  (FROZEN — must still be exactly this when you finish)
the RED   b7f0439 on branch asr-wo3-03-verdict — governance/engineering/build-log/BL-20260824T083556Z-A303.yaml
```

**MUTATION PROHIBITED** except `/tmp` scratch trees, `git archive` extractions, and **your own
verdict artefact**, for which you have a narrow write grant on a branch of your own. **Get your own
tree** — `git worktree add --detach` or a WHOLE-tree `git archive` extraction. Do not work in
`/srv/crash-detector-wo3`, `/srv/crash-detector-wo3-audit` or `/srv/crash-detector`.

---

## 2. WHAT YOU ARE AUDITING

`16A-FIX` answers a `RED`: **an `UNKNOWN` dial carrying `detail_level: "calm"` was ADMITTED by
`refuse_unless_publishable` on both surfaces**, breaching PID §3.2 (*"Missing data must never render
as calm"*) — the only state this product can currently publish, since with zero registered sources
every dial is `UNKNOWN`.

The fix introduces `$defs/absent_data_detail_level` (`["elevated","acute"]`), referenced by both
`dial_reading_degraded` and `dial_reading_unknown`; `VALUE` keeps `calm`. Plus: a guard arm that
fails when the fix is reverted, a re-pointed constitutional test, a de-hardcoded fake, a superseded
`publish.py` limit, and three closed portability gaps.

**READ, THEN DISTRUST:** the seat's own `BL-20260824T091143Z-16AF` on the lane, the Project Lead's
reconciliation at `/srv/crash-detector/governance/engineering/build-log/BL-20260824T092106Z-0161.yaml`,
and the original `RED`. **Three seats agreeing is three seats, not a proof** — and `0161` records
**two** Project Lead measurements that were themselves wrong on first attempt today.

---

## 3. WHERE TO ATTACK — **BEHAVIOURAL FIRST, AND THAT ORDERING IS ITSELF A CORRECTION**

*** **`CD-PL-F176`: the previous assurance dispatch ranked the right target but put three
STRUCTURAL probes ahead of the behavioural one, and all three PASS. A seat working that list
top-down and stopping when three probes came back clean would have returned `PASS` over a live
constitutional breach.** *** **THIS DISPATCH PUTS THE END-TO-END ATTACK FIRST. IF YOU FIND THAT
ORDERING WRONG TOO, SAY SO.**

### 3.1 — **THE PROBE, END TO END, THROUGH THE LIVE GATE. BOTH ARMS.**

```
For an UNKNOWN dial and a DEGRADED dial, on BOTH surfaces:
  detail_level="calm"      MUST be REFUSED     <- the fix
  detail_level="elevated"  MUST be ADMITTED    <- THE ARM THAT MATTERS EQUALLY
  detail_level="acute"     MUST be ADMITTED
  detail_level="banana"    MUST be REFUSED     <- the probe is live
  detail_level REMOVED     MUST be REFUSED
```

*** **A CONTRACT THAT REFUSES EVERY `UNKNOWN` DIAL SATISFIES PID §3.2 VACUOUSLY WHILE BREAKING THE
ONLY STATE THIS PRODUCT CAN PUBLISH. "calm is refused" IS HALF AN ANSWER.** ***

**A TRAP, DISCLOSED BECAUSE THE PROJECT LEAD FELL INTO IT:** a hand-built `DEGRADED` dial with
`missing_inputs: []` is refused **for an unrelated reason** — the branch requires at least one named
missing input. **A malformed fixture and a working refusal are indistinguishable from the outside.
Read the branch's `required` list before you believe a `REFUSED`.**

Then go further than the probe: **is there any OTHER route to a published `calm` on missing data?**
The private surface, the review surface, `dial_presentation`, the health surface, an envelope built
by any test helper. **The fix is in the contract; ask whether the contract is the only door.**

### 3.2 — **DID THE NARROWING BREAK SOMETHING THAT LEGITIMATELY NEEDED `calm`?**

`DEGRADED` was narrowed on the reasoning that `detail_level_for`'s `on_degraded` returns
`policy.absent_data_level` identically to `on_unknown`. **VERIFY THAT BY READING THE FUNCTION, not
by trusting the sentence.** Is there any reading in which a `DEGRADED` dial — which carries a real
score *and* its damage — should legitimately render `calm`? **If yes, the fix is too wide and that is
its own finding.**

### 3.3 — **THE `schema_version` QUESTION, WHICH THE PROJECT LEAD DELIBERATELY DID NOT SETTLE**

Both contracts still pin `const: "1.1.0"`, set at 16A when `detail_level` was introduced. No bump
accompanied the narrowing. The Project Lead's reasoning, **offered to you for attack rather than as a
decision**: the schema's own rule concerns *widening*; this is a *narrowing*; and **1.1.0 has never
been emitted by anything, because `publish_cycle` has zero callers**.

*** **THAT ARGUMENT RESTS ON "NOTHING CONSUMES IT YET" — WHICH IS THE SAME PREMISE THAT MADE THE
ORIGINAL `RED` "NOT EXPLOITABLE TODAY". ATTACK IT.** *** Does anything pin, cache, record or assert
`1.1.0` — a test, a fixture, a migration, a stored envelope column, the register? **If a consumer
exists anywhere, a bump is owed and its absence is a finding.**

### 3.4 — **THE CORRECTED `CD-AC-002` GUARD**

`test_no_function_in_the_module_takes_two_readings` was **vacuous**: it bucketed `reading` and
`dial_slot` together against a ceiling of 2, so a function taking two readings passed. **THIS SAT ON
`CD-AC-002` — ONE OF THE TWO CRITERIA THE WHOLE PERIMETER TURNS ON — AND WAS FOUND ONLY BECAUSE THE
FIX DISPATCH ASKED FOR A TEST-NAME AUDIT.**

Plant your own two-reading function against the corrected guard. Then plant the shapes a corrected
guard might *still* miss: a function taking two readings **positionally with different names**; one
taking a tuple, list or dict of readings as a single parameter; a method on a class; a closure; a
`functools.partial`. **`CD-AC-002` is about the existence of the function, not the shape of its
signature.** And check the guard is not now over-tight — does it refuse a legitimate helper?

### 3.5 — **THE THREE PORTABILITY GAPS, AND THE TRAP THAT COMES WITH THEM**

Three subjects must now be refused: a dell path inside an env default `${VAR:-/srv/...}`; a real
hostname in `CD_STORE_HOST`; and the same dell path as a **bare literal**.

*** **`CD-PL-F177` IS DISCLOSED TO YOU BECAUSE IT IS THE EXACT TRAP: the Project Lead planted into
the `x-cd-python-service` YAML ANCHOR at line 296, whose `CD_CONTRACTS_DIR` is OVERRIDDEN at every
service that uses it — so the plant was SHADOWED, never reached a resolved service, and reported
`PASS — 0 violations`. A PLANT INTO AN OVERRIDDEN ANCHOR IS INDISTINGUISHABLE FROM A CONTROL THAT
FAILED TO FIRE.** *** **ASSERT THAT YOUR MUTATION APPLIED *AND* THAT IT APPLIED WHERE IT WOULD
BITE.** Re-planted at service level, all three exit 1 — reproduce that, and then ask **what the
checker still misses**.

**And the open question the Project Lead declined to answer:** *should* a dell path in an anchor
fragment that every service currently overrides be refused? It is dead config today and live the
moment one override is deleted. **An auditor's reasoned opinion is worth more here than either
seat's.**

---

## 4. WHAT MUST STILL BE TRUE — VERIFY, DO NOT ASSUME

**Run the tests at both ends yourself** — 1990 at `53f639a` and 2007 at the tip are claimed ·
register still `pid.content_hash MATCHES` / 18 criteria / `latest_admitted_run (null)` / `GATE:
SHUT`, and `PID.md` + `required-tests.yaml` **byte-identical across the range** (the fix seat was
forbidden to touch them precisely because re-staling the pin would have been easy and invisible) ·
`be0b355` unmoved · `pbg/` at zero paths **anywhere in the range**, not just net · **no source
registered** (grep real series identifiers; `SLOOS`/`NDFI` only as prose — **a data hit is a `RED`**)
· `CD-AC-002` still AMBER-not-closed and `CD-AC-005` still RED · **no `publish_cycle` caller and no
`src/` entrypoint** — the health surface's value axis is still open and blocks any transport.

**And sweep `53f639a..b9283b9` commit by commit for touched-and-reverted paths.** The 16A seat
self-disclosed one such breach; net-zero diffs pass every scope instrument this project owns. **Do
not assume the next seat was equally candid — measure it.**

---

## 5. YOUR RETURN

**BOOT FIRST**; declare the verdict you get, including a `RED` inherited from the frozen base's
`ACTIVE_WORK.yaml` — known, outside your scope, diagnose and do not repair.

`PASS` / `AMBER` / `RED`, with the next safe gate named. Every finding with its command and pasted
output and a stated confidence · both arms of every plant, plus the admitting arm wherever a refusal
could be vacuous · **your declared limits (`CD-RULE-004`)** — there is no live PostgreSQL, so
atomicity, the `CHECK` constraints as executed and the append-only `GRANT` posture are
**UNSUPPORTED** for a running instance; say what else you left · and **findings against this
dispatch**, including its §3 ordering. **Five of the last seven dispatches contained an error the
seat caught, and the seat was right every time.**

**A `PASS` IS NOT ACCEPTANCE** (`PBG-AUTH-003`, `CD-D-180`).

Commit your verdict (`PBG-CONT-007`), validated by direct call to `continuity.validate(...,
schema_dir=<root>/pbg/schemas)` — the `pbg log` CLI cannot validate this project's log
(`CD-PL-F171`, a framework defect, reported and not yours to repair). **And never transcribe a SHA
— `git rev-parse` it** (`CD-PL-F36`; the 16A-FIX seat self-reported fabricating a SHA tail into a
draft entry and caught it only because the validator said it was *declining to check that field*).

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ASR-WO3-04 GIT_AUTHOR_EMAIL=cd-asr-wo3-04@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ASR-WO3-04 GIT_COMMITTER_EMAIL=cd-asr-wo3-04@seats.crash-detector.invalid \
git commit -m "..."
```
