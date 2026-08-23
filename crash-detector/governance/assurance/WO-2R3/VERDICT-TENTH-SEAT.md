# VERDICT — THE TENTH ASSURANCE SEAT

**`actor_id: CD-ASR-WO2R3-07`** · dispatch `CD-DISPATCH-WO2R3-ASSURANCE-10` · authority `CD-AUTH-0001`
· product authority basis `PO-DECISIONS-0022` ruling 5, commit `d60b8b9`

---

## VERDICT: **AMBER**

**CONFIDENCE: HIGH on what I measured. The scope of what I did NOT measure is stated in §9 and it is
not small.**

**BOTH NAMED ACCEPTANCE COMMANDS PASS, INDEPENDENTLY RE-TAKEN, WITH LIVE CONTRAST ARMS. THE FIVE
ITEMS RULING 5 NAMED ARE NOT ALL FIXED. `F09` IS THE ONE THAT IS NOT, AND IT IS NOT CLOSED IN THE
DIRECTION THAT MATTERS MOST.**

This is **AMBER and not RED** because the two acceptance commands are genuinely green against the
authentic target, the `F08` correction holds *as a class* and not as an instance, and `F05`+`F11`
are fixed with a contrast arm that fires. It is **AMBER and not PASS** because one of the five named
items (`F09`) remains reachable by a single command, because the gatekeeper and the detector
disagree about a state both are supposed to govern, and because the `CD-RULE-004` three-place sweep
— the increment's own headline correction — is incomplete in the very row it was raised against.

**THIS IS NOT A DEDICATED PARALLELISM GATE. SEE §8. I DO NOT DECLARE PARALLELISM SAFE.**

---

## 1. AUTHENTIC TARGET

| | |
|---|---|
| **SHA graded** | `b165dd99a22a9a65b8e743274cec02ed7010dc22` |
| resolved by | `git rev-parse b165dd99a22a9a65b8e743274cec02ed7010dc22` → `b165dd99a22a9a65b8e743274cec02ed7010dc22`; `git cat-file -t` → `commit` |
| worktree | `/srv/crash-detector` |
| `main` observed at boot | `9aeaf335178534f6c7c829667d2c8055206873ae` — **FOUR commits past my target, not three** |
| runtime | `Python 3.11.2 (main, Apr 28 2025, 14:11:48) [GCC 12.2.0]`, `Linux dell-debian 6.1.0-40-amd64`, user `root` |
| filesystem | `stat -f -c %T /srv/crash-detector` → `ext2/ext3`; `/tmp` → `ext2/ext3` (**measured in my own sandbox, not taken from the dispatch**) |
| my scratch | `/tmp/cd-asr-wo2r3-07/` |
| UTC at start | `date -u` → `Sun 23 Aug 16:48:10 UTC 2026` |

### 1.1 The record advanced past my target — measured, not trusted

The dispatch pre-declared three commits. **I measured four.** The dispatch's own instruction was to
run the command rather than trust the sentence, and the extra commit is the dispatch's own
`CD-RULE-007` follow-up, written after the sentence was composed. No harm; recorded because the
dispatch asked to be checked.

```
$ git diff b165dd99a22a9a65b8e743274cec02ed7010dc22..HEAD --stat
 .../dispatch/CD-DISPATCH-WO2R3-ASSURANCE-10.yaml   | 224 +++++++++++++++++++++
 governance/engineering/ACTIVE_WORK.yaml            |  20 +-
 .../build-log/BL-20260823T163840Z-0147.yaml        | 162 +++++++++++++++
 .../build-log/BL-20260823T164224Z-0148.yaml        |  75 +++++++
 4 files changed, 476 insertions(+), 5 deletions(-)
```

**The claim that nothing under `tools/` or `governance/coordination/` moved is CONFIRMED BY TREE
HASH, which is stronger than the diff:**

```
$ git rev-parse b165dd9:tools 9aeaf33:tools
08b67ad5e4033cdefa885315f3ecae54719920ef
08b67ad5e4033cdefa885315f3ecae54719920ef
$ git rev-parse b165dd9:governance/coordination 9aeaf33:governance/coordination
59058d0bac9f5b3d0ab5565aab0c6176a5b196bd
59058d0bac9f5b3d0ab5565aab0c6176a5b196bd
```

### 1.2 Boot — and a framework limitation found in the act of booting

`PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot` returned `Verdict: AMBER`,
`continuity_state CONTINUITY_MATCH/RESUME_AMBER`, `observed_sha 9aeaf33...`, `current_phase GATE`.

**It also printed `assigned_role PROJECT_LEAD`. I am not the Project Lead.**

```
$ PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot --help
usage: pbg boot [-h]
options:
  -h, --help  show this help message and exit
```

`pbg boot` takes **no role argument**; `pbg --help` describes it as *"boot the application Project
Lead"*. There is no Assurance boot path in the framework. **`PBG-BOOT-002` (non-waivable) says no
agent self-assigns a role — and the only boot instrument in the tree assigns one, unconditionally,
to whoever runs it.** That is `CD-ASR-WO2R3-07-F11` below. My role comes from the dispatch and the
authority record, not from that output, and I record the contradiction rather than let a
`PROJECT_LEAD` line stand unchallenged in my own boot evidence.

---

## 2. ACCEPTANCE COMMAND 1 — `race_scope.py`, BOTH ARMS

### 2.1 The banked harness — hash verified before it was trusted

```
$ sha256sum governance/assurance/WO-2R3/evidence/CD-ASR-WO2R3-06/race_scope.py
13800ffaa1722f4b02fb1a4fbac100865f885d9f897431502a5b03c9ad84b5e5  ...race_scope.py
$ wc -l -c ...race_scope.py
  66 2695 ...race_scope.py
```

**Matches the dispatch's claimed hash exactly, at 66 lines and 2695 bytes.** The second banked
artefact is `race_launch.sh`, sha256 `7c723a431096e00b01acec75a5cf5c89fd767de877dd4e4b794c56008df36cd7`.
Both were banked at `d34ba8f` by `PROJECT_LEAD_SEAT_01 <project-lead-seat-01@seats.crash-detector.invalid>`
— **the accountable identity, not the `pl@x` fixture identity of `CD-PL-F154`.**

### 2.2 Only the `TREE` line was changed, proved in both directions

```
$ diff <(sed 's/^TREE = .*/X/' banked) <(sed 's/^TREE = .*/X/' mine)   → rc=0, no output
$ diff banked mine
20c20
< TREE = "/tmp/cd-asr-wo2r3-06/race/tree"
---
> TREE = "/tmp/cd-asr-wo2r3-07/race/repaired"
```

### 2.3 THE FIRST RUN WAS A DEAD PROBE, AND THE CONTRAST ARM IS WHAT CAUGHT IT

**I record this because it is the single best evidence in this document that `CD-D-079` is a real
rule and not a slogan.** My first attempt built both trees with `git archive | tar -x`. Both arms
returned:

```
  exactly-one-winner (CORRECT) : 0
  ZERO winners                 : 200
  *** TWO WINNERS (DOUBLE-TAKE ON ONE SCOPE) *** : 0
```

A **zero on the repaired tree** — the exact figure the gate wants. **It was worthless.** The
contrast arm returned zero too, and a contrast that cannot fail is not a contrast. Diagnosis:

```
$ python3 -B race/repaired/tools/coordination/claim.py --root race/repaired claim --task DIAG-1 ...
[TREE] not a git worktree (git rev-parse --show-toplevel failed rc=128 ...)
VERDICT: REFUSED — git rev-parse HEAD failed rc=128: fatal: not a git repository
rc=2
```

`git archive` output is not a git repository, so `resolve_sha` refused and **every claim failed
closed**. The instrument behaved correctly; my probe was broken. **Had I run only the repaired arm I
would have banked a false green, and it would have looked exactly like the real one.**

### 2.4 The re-run, on authentic git checkouts of both SHAs

Both trees rebuilt with `git clone` + `git checkout` at the exact SHAs. Blobs differ, and the
contrast varies the intended axis:

```
$ diff -u unfixed/claim.py repaired/claim.py | grep -E 'critical_section|write_exclusive|for other'
-    for other in live_claims(root):
-        registry.write_exclusive(path, payload)
+    with registry.critical_section(root, registry.CLAIMS_DIR):
+        for other in live_claims(root):
+            registry.write_exclusive(path, payload)
```

`480da0f` is a true ancestor of `b165dd9` (`git merge-base --is-ancestor` → `YES_ANCESTOR`).

**REPAIRED ARM — `b165dd9`:**
```
$ python3 -B /tmp/cd-asr-wo2r3-07/race_repaired.py 200
ROUNDS=200  concurrency=2  DIFFERENT task_ids, IDENTICAL write_scope='src/contended/**'
  exactly-one-winner (CORRECT) : 200
  ZERO winners                 : 0
  *** TWO WINNERS (DOUBLE-TAKE ON ONE SCOPE) *** : 0
real 0m25.286s     rc=0
```

**CONTRAST ARM — `480da0f`, UNFIXED:**
```
$ python3 -B /tmp/cd-asr-wo2r3-07/race_unfixed.py 200
  exactly-one-winner (CORRECT) : 4
  ZERO winners                 : 0
  *** TWO WINNERS (DOUBLE-TAKE ON ONE SCOPE) *** : 196
  first double-take, verbatim:
      task=RACE-0-A rc=0  [TREE] ... head=480da0f49bb265ce782004c5d925febb94314c56
      task=RACE-0-B rc=0  [TREE] ... head=480da0f49bb265ce782004c5d925febb94314c56
real 0m25.225s     rc=0
```

**ACCEPTANCE COMMAND 1: PASS.** My figure is **196**, the fourth number after the ninth seat's 193,
the Engineer's 194 and the Project Lead's 195. The dispatch pre-declared that a fourth number is the
expected shape of a scheduling-dependent race and not a discrepancy, and that is what I observe. The
Project Lead's `195 → 0` is **CONFIRMED as a measurement**, not carried as a claim.

---

## 3. ACCEPTANCE COMMAND 2 — `PLANT-COORD-05`, AND AN ATTACK ON IT

### 3.1 Run against the authentic target, in my own scratch

I did **not** point `SOURCE_ROOT` at `/srv/crash-detector`, because the plant clones `SOURCE_ROOT`
and grades whatever HEAD it finds — which is `9aeaf33`, not my target. I pinned a source root at
`b165dd9`. `PLANT_SCRATCH` was set to my own scratch and never to `/tmp/cd-eng-coord-01/plants`.

```
$ PLANT_SCRATCH=/tmp/cd-asr-wo2r3-07/plants \
  SOURCE_ROOT=/tmp/cd-asr-wo2r3-07/srcroot-b165dd9 \
  sh governance/coordination/plants/PLANT-COORD-05.run.sh
  sandbox HEAD    : b165dd99a22a9a65b8e743274cec02ed7010dc22
  ARM 1  SAME-IDENTITY OVERLAP IS REFUSED AND NAMED : CONTRASTED AS REQUIRED
  ARM 1b SAME-IDENTITY WRITE x READ IS REFUSED      : CONTRASTED AS REQUIRED
  ARM 2  RESTORING THE SKIP ADMITS THE INCIDENT     : CONTRASTED AS REQUIRED
  ARM 3  SAME-IDENTITY DISJOINT PAIR STILL PROCEEDS : CONTRASTED AS REQUIRED
  ARM 4  BOTH SURVIVING EXEMPTIONS STILL ADMIT      : CONTRASTED AS REQUIRED
  ARMS: 5 / 5 contrasted as required
  PLANT VERDICT: LIVE
rc=0
```

**ACCEPTANCE COMMAND 2: PASS at the authentic SHA.** The Project Lead's `5/5 LIVE` is **CONFIRMED as
a measurement.**

### 3.2 THE ENGINEER INVITED AN ATTACK ON ITS OWN TEST. I TOOK IT.

The dispatch asks whether arms 3, 4a and 4b **actually** separate a fix from a concurrency ban, *or
only appear to*. **The plant contains no mutation that would answer that** — its only mutation arm
is arm 2. So I supplied the missing counterfactual.

**WRONG-FIX A — the plausible over-correction: `F08` "fixed" by banning same-identity multi-claim
outright.** Injected into `check_scope_disjoint.py`, committed, plant run against it:

```
  sandbox HEAD    : ca519685fc7c0cf9431a7b08c23b9ed4d192de0c
  ARM 1  : CONTRASTED AS REQUIRED
  ARM 1b : CONTRASTED AS REQUIRED
  ARM 2  : CONTRASTED AS REQUIRED
  ARM 3  SAME-IDENTITY DISJOINT PAIR STILL PROCEEDS : *** DID NOT CONTRAST ***
  ARM 4  BOTH SURVIVING EXEMPTIONS STILL ADMIT      : *** DID NOT CONTRAST ***
  ARMS: 3 / 5      PLANT VERDICT: *** NOT A CONTRAST ***      rc=1
```

**ARMS 3 AND 4 HAVE REAL DISCRIMINATING POWER. MEASURED, NOT ASSERTED.** A control that banned
concurrency would be caught. This is the strongest single result in the increment and it is to the
Engineer's credit.

**WRONG-FIX B — behaviour identical, prose removed.** I set the founding-incident string to `""` and
changed nothing else. Detection logic byte-identical:

```
  ARM 1  : *** DID NOT CONTRAST ***    (rc=1, REFUSED correct; lines naming it = 0)
  ARM 1b, 2, 3, 4 : CONTRASTED AS REQUIRED
  ARMS: 4 / 5      PLANT VERDICT: *** NOT A CONTRAST ***
```

**Arm 1 fails on an instrument whose behaviour is correct.** It grades a `print` string as well as a
verdict. That is defensible — ruling 5 asks the control to *flag*, and naming is part of flagging,
and the arm's own header says so — but it means a pure message refactor turns the tenth gate's
acceptance command RED with no behavioural regression. **It is the Engineer's own diagnosed `F06`
error class — asserting on something ADJACENT to the proposition — living in arm 1 of the acceptance
command.** See `F06` below.

### 3.3 The word "contrasted" is doing work it has not earned

`plant_summary` prints `ARMS: 5 / 5 contrasted as required` and `arm_result` labels every passing
arm `CONTRASTED AS REQUIRED`. **Only arms 1 and 2 form a contrast pair** — same input, mutation
applied, opposite verdicts. Arms 1b, 3, 4a and 4b are **single-run assertions on the intact tree**
with no counterfactual in the file. They are not vacuous — I proved that in §3.2 — but **the plant
does not itself demonstrate it, and its summary line asserts that it does.** See `F05` below.

### 3.4 `PLANT-COORD-06` arm 2 — the flakiness the Engineer raised against itself

The Engineer reported arm 2 as flaky by construction. **I could not reproduce it.**

```
$ 20 consecutive runs, PLANT_SCRATCH and SOURCE_ROOT pinned to mine
run 1..20   rc=0   ARMS: 3 / 3   0 arms-failed
   grep -c 'rc=0  ARMS: 3 / 3' → 20     total runs → 20     runs with any failure → 0
```

**20/20, zero failures.** This does **not** refute the Engineer's finding — it reported a
27/40 reproduction rate for a defect under different conditions, and a non-reproduction on one host
in 20 runs is weak evidence. **I report the negative result as a negative result and leave `F06`
standing as the Engineer's own.**

---

## 4. THE SEVEN PLANTS NOBODY RE-RAN — THE `T7` CLAIM, NOW MEASURED

The dispatch flagged the Engineer's *"8 plants, 27 arms, all contrasted"* as an inherited claim of
exactly the `T7` shape. **I re-ran all seven at the authentic target.**

```
PLANT-COORD-01  rc=0  ARMS: 3 / 3  LIVE     PLANT-COORD-06  rc=0  ARMS: 3 / 3  LIVE
PLANT-COORD-02  rc=0  ARMS: 4 / 4  LIVE     PLANT-COORD-07  rc=0  ARMS: 3 / 3  LIVE
PLANT-COORD-03  rc=0  ARMS: 3 / 3  LIVE     PLANT-COORD-08  rc=0  ARMS: 3 / 3  LIVE
PLANT-COORD-04  rc=0  ARMS: 3 / 3  LIVE
(+ PLANT-COORD-05: 5 / 5 LIVE)
```
All sandbox HEADs printed `b165dd99a22a9a65b8e743274cec02ed7010dc22`.
**3+4+3+3+5+3+3+3 = 27 arms across 8 plants, all LIVE. THE ENGINEER'S CLAIM IS CONFIRMED AS A
MEASUREMENT.** The `T7` carry is discharged. The §3.3 qualification about what "contrasted" means
applies to these too and I did not attack each one's arms individually.

---

## 5. FINDINGS

### `CD-ASR-WO2R3-07-F01` — **HIGH** — the gatekeeper ADMITS a state the detector REFUSES, and `CD-PL-F134`'s guard is ORDER-DEPENDENT

`claim.py` `cmd_claim` tests this claim's **write** scope against every live claim's write scope and
read scope. **It never tests this claim's READ scope against a live claim's WRITE scope.**
`check_scope_disjoint.py` tests both directions. The two instruments therefore disagree about the
same registry.

**Measured. Ordering A — reader claims first (`CD-PL-F134`'s literal incident order):**
```
-- reader claims:   VERDICT: CLAIMED
-- writer claims second:
VERDICT: CLAIM REFUSED — WRITE/READ SCOPE OVERLAP (CD-PL-F134)
   src/shared/**  <>  src/shared/**   OVERLAP: identical depth and every segment intersects
rc=1
```
**Ordering B — writer claims first, reader second:**
```
-- writer claims:   VERDICT: CLAIMED
-- reader claims second:   VERDICT: CLAIMED      rc=0
```
**And then the detector, on that very registry, zero seconds later:**
```
$ python3 -B tools/coordination/check_scope_disjoint.py --root .
   VIOLATION WRITE/READ (CD-PL-F134) [cross-seat]  seat SEAT-BRAVO (task T-WRITER) WRITES
   what seat SEAT-ALPHA (task T-READER) declared it would READ
scope_violations = 1
VERDICT: REFUSED — 1 scope violation(s) among 2 live claim(s)      rc=1
```

**The preventive control admits a state its own detective control calls a violation.** This is
`F08`'s shape — two instruments in one tree disagreeing about one population — in the opposite
direction. `F08` was the detector being laxer than the gatekeeper; this is the gatekeeper being
laxer than the detector, and the increment aligned the **identity** axis while leaving the
**direction** axis unaligned.

`GUARD_THE_INSTANCE_NOT_THE_CLASS`: the guard catches the ordering the reported incident happened to
have, and not its class. **`claim.py`'s docstring cites `CD-PL-F134` — *"a live reader's material
must not move under it"* — as the justification for a check that carries only one of `F134`'s two
orderings.** `L2` is literally true of the code, so this is not a false declaration; but there is no
`DOES NOT DECIDE` entry for the uncovered direction, and a limit stated only as what it *decides*
leaves the reader to infer the gap.

**This session is the live instance.** A long-lived Project Lead writes `governance/`; an Assurance
seat is dispatched to read `governance/` while it is live. That is ordering B exactly, and under
this machinery the Assurance seat is ADMITTED.

### `CD-ASR-WO2R3-07-F02` — **HIGH** — `F09` IS NOT CLOSED. The lease is still flippable by one command, and the record it leaves behind is FALSE

`F09` is one of the five items ruling 5 named. The `--pid` arm **is** closed (see §7). **The
reap/release arm is not, and it was not examined by anyone.**

**Measured end to end.** A genuinely live process (`sleep 600`, pid 1850261, `ps` evidence taken),
leased by `SEAT-ALPHA`, verified `state=CLAIMED liveness=LIVE`:

```
$ python3 -B tools/coordination/lease.py --root . reap --lease L1 --reason "taking it" --force
VERDICT: REAPED — lease=L1 state=ABANDONED (ALIVE)
rc=0
```

**`(ALIVE)`. The instrument printed its own liveness verdict in its own success line and reaped
anyway.** No `--seat`. No `--by`. **`reap` takes no identity argument at all** — any actor that can
write the leases directory can reap any lease.

The victim was still running afterwards (`ps` → `1850261 S sleep 600`, `*** VICTIM IS STILL ALIVE ***`),
and the record now reads:

```
state: ABANDONED
reap_reason: taking it
reap_disclosure: A SESSION DIED HOLDING THIS LEASE. The record is retained, not deleted,
```

**A false statement, written by the instrument, about a process that did not die.** And unlike its
sibling, it is not marked:

```
$ grep -n 'reap_forced_over_a_live_holder' tools/coordination/claim.py tools/coordination/lease.py
tools/coordination/claim.py:326:        rec["reap_forced_over_a_live_holder"] = True
   (lease.py: no match)
```

`claim.py` records a forced reap over a live holder. `lease.py` does not. **The class was fixed in
the instrument the finding named and not in its sibling** — the exact anti-pattern `lease.py`'s own
comment at lines 272–275 says this increment exists to remove.

**And the scope is then free:**
```
$ lease.py acquire --lease L2 --seat SEAT-BRAVO --task T1 --write-scope 'src/alpha/**'
VERDICT: LEASE ACQUIRED — THE LAUNCH MAY PROCEED      rc=0
```
**One command hands a live seat's work to a different seat, and the audit trail says the first seat
died.** That is two seats on one scope — the founding-incident harm — reachable in one step.

**The `release` arm is the same defect, weaker:**
```
$ lease.py release --lease L9 --seat SEAT-VICTIM      VERDICT: RELEASED — lease=L9   rc=0
-- victim still alive?   1855239 sleep 300   *** STILL ALIVE, LEASE RELEASED ***
```
Guarded only by string equality against an unauthenticated `--seat` the caller types.

**AND IT IS UNDECLARED.** No entry in `lease.py`'s eleven `LIMITS` mentions `reap`, `--force` or
`release` authority (verified by `sed -n '60,96p' | grep -iE 'reap|force|release'` — the single hit
is *"released before this command returns"*, about the critical section). `--force` carries no
`help=` string, and the module docstring's own command list at line 11 reads
`lease.py reap --lease ID --reason R` — **omitting the flag that defeats its only guard.**

**The ninth seat established that an undeclared skip is a defect. This is an undeclared bypass, and
it is in one of the five items the ruling said was being fixed.**

### `CD-ASR-WO2R3-07-F03` — **MEDIUM** — the `CD-RULE-004` three-place sweep is INCOMPLETE in the row it was raised against

The dispatch handed me this as UNDONE. **The declared-limit prose does agree on identity across all
three places** — code `LIMITS`, contract §2, register `declared_limit` all say *"AT ANY IDENTITY,
INCLUDING TWO CLAIMS HELD BY ONE SEAT ID"*. **That part of the correction landed and it is the part
that matters most.** The rest of the row did not:

```
CONTRACT header  | **plant** | governance/coordination/plants/PLANT-COORD-02.run.sh |   <- WRONG PLANT
                 | **arms**  | 4 |
                 | last run  | LIVE — 4/4 arms contrasted (shares PLANT-COORD-02 ...) |
REGISTER row     plant: governance/coordination/plants/PLANT-COORD-05.run.sh          <- the real one
                 arms_at_increment_13: 5
                 arms: 4
                 last_run_verdict: 'LIVE — 4/4 arms contrasted (shares PLANT-COORD-02 ...)'
MEASURED         PLANT-COORD-05 printed  ARMS: 5 / 5
```

Four disagreements: the contract header names `PLANT-COORD-02` where the register names
`PLANT-COORD-05`; arm counts read 4 / 4 / 5 / 4 across the two files; and **both places carry a
stale `last_run_verdict` of `4/4` for a plant that runs 5 arms.** The register's own preamble
prohibits exactly this: *"A REGISTER ENTRY MAY NOT CLAIM MORE THAN ITS GUARD DELIVERS."* Here it
claims **less**, and names the wrong guard.

Separately, the register's `declared_limit` **drops** the `Q11` non-invocation disclosure that both
other places carry:
```
register declared_limit  grep -c 'NOT INVOKED'                    → 0
code LIMITS              grep -c 'IT IS NOT INVOKED BY ANYTHING'  → 1
contract §2              grep -c 'NOT INVOKED BY ANYTHING'        → 1
```

### `CD-ASR-WO2R3-07-F04` — **MEDIUM** — a live, present-tense residual claim that disjointness is cross-seat-only

`governance/coordination/RETURN-CD-ENG-COORD-01.md:155`, unamended by increment 13, in the same
directory as the contracts:

> `| **2(b)** live disjointness | check_scope_disjoint.py. Pairwise WRITE×WRITE **and WRITE×READ in both cross-seat directions** (CD-PL-F134). | ...`

Present tense, unqualified, and **false of the code at `b165dd9`** — the check is now at any
identity. Every other `cross-seat` / `same-seat` occurrence in the tree that I examined is either a
quotation of the removed skip in order to explain it, the mutation patch that must contain it by
construction, the plant that greps for its absence, or the output label `kind`. **This one is a live
claim.** It is not one of the three `CD-RULE-004` places, which is why it survived the sweep — and
that is the point: the sweep was scoped to three places and the false statement is in a fourth.

### `CD-ASR-WO2R3-07-F05` — **MEDIUM** — `5 / 5 contrasted as required` overstates what the plant demonstrates

See §3.3. Only arm 1/arm 2 is a contrast pair. Arms 1b, 3, 4a, 4b are single-run assertions carrying
the label `CONTRASTED AS REQUIRED`. **Partially discharged by me**: I built the missing mutation and
arms 3/4 do discriminate (§3.2). The finding is that **the artefact asserts a property it does not
itself establish**, and the Project Lead banked `5/5 arms LIVE` as the acceptance figure on the
strength of that word.

### `CD-ASR-WO2R3-07-F06` — **MEDIUM** — the acceptance command's arm 1 grades a `print` string

See §3.2, wrong-fix B. An instrument with byte-identical detection logic and a removed message fails
arm 1. Defensible as a *flagging* requirement, and declared in the arm's header — **but it means the
tenth gate's named acceptance command can go RED on a message refactor**, and it is the Engineer's
own `F06` error class (asserting on something adjacent to the proposition) inside the test that
grades the fix.

### `CD-ASR-WO2R3-07-F07` — **MEDIUM/HIGH, and it is a design question, not a discipline failure** — the merge control is UNRUNNABLE in the mode the Product Owner just made standing

`CD-PL-F155` is **confirmed by measurement**:
```
$ grep -n 'add_argument("--claim"' tools/coordination/merge_reconcile.py
207:    ap.add_argument("--claim", action="append", required=True, dest="claims")
$ python3 -B tools/coordination/merge_reconcile.py --base 480da0f
merge_reconcile.py: error: the following arguments are required: --claim
rc=2
```

**I grade the substitution, as asked.** The Project Lead's decision **not** to fabricate a claim so
the instrument would run is **correct and non-negotiable** — constructing state so a control appears
to pass when the authentic target was not verified is non-waivable, and it declined to do it. It
disclosed the substitute *as* a substitute and measured the three assertions directly. **That is the
right call and I endorse it.**

**But the consequence is larger than the Project Lead framed it.** `CD-D-181` / `PO-DECISIONS-0022`
made sequential single-seat the **standing** mode. A sequential single-seat increment takes no
claim. Therefore `CD-CT-007`'s instrument **cannot run on the standing mode of work at all** — not
for this increment, and not for the next one either. It is not that one merge missed its control;
it is that **the merge control is now dead for the way this project has been ordered to work.**
That is a Product Authority / design question and I route it up rather than grade it as a lapse.

### `CD-ASR-WO2R3-07-F08` — **MEDIUM** — the atomicity guard is a DENYLIST that FAILS OPEN

```
$ sed -n '103,120p' tools/coordination/registry.py
REFUSED_FILESYSTEMS = {"nfs", "nfs4", "smb2", "cifs", "fuseblk", "9p", "afs", "ceph", "gfs2"}
def fs_type(path): ...  return out.stdout.strip() or "UNKNOWN"
def assert_atomic_or_refuse(path):
    t = fs_type(path)
    if t.lower() in REFUSED_FILESYSTEMS: raise RuntimeError(...)
    return t
```

**Measured, with a contrast arm:**
```
assert_atomic_or_refuse with fs_type=UNKNOWN -> UNKNOWN
  ^ IT RETURNED. It did NOT refuse. The take proceeds on an unmeasured filesystem.
CONTRAST ARM, fs_type=nfs4 -> REFUSED: ATOMICITY_NOT_ESTABLISHED ...
```

If `stat` is missing, fails, or reports a filesystem not on the list of nine, **the registry proceeds
on an assumption** — and its own docstring says *"A registry whose atomicity is assumed is worse
than none — refusing."* It does not refuse. It is also a **denylist**, in a tree where `lease.py:76`
declares `CD-RULE-003, never a denylist` as the standard it holds itself to for the `--pid` guard.
The one guard is derived; the other is enumerated. Low exploitability here (`ext2/ext3` measured),
but it is the `PORTABILITY` theme: this control's correctness depends on the host.

### `CD-ASR-WO2R3-07-F09` — **LOW** — `--dry-run` strands a live lease over a dead pid

`launch.sh --dry-run` exits 0 **holding** the lease, and does not `exec`. The leased pid is the
`launch.sh` shell, which then exits. The result is a `CLAIMED` lease naming a dead process, blocking
the scope until someone explicitly reaps it. Disclosed in the script's own output line
(*"the lease is held and the command is NOT exec'd"*), so it is declared, not hidden — but a
declared limit is not a licence (`CD-D-129` clause ii, fourth edge).

### `CD-ASR-WO2R3-07-F10` — **LOW** — `lib.sh` reads a pipeline exit status in the file that forbids it

`apply_mutation` runs `git apply ... | sed` and then `APPLY_RC=${PIPESTATUS:-0}` — POSIX `sh` has no
`PIPESTATUS`, so this is unconditionally `0`. **Harmless**, because the next two lines overwrite it
with a real `git apply --reverse --check` rc, and the code comments say so. Recorded because the
file's own header states *"Nothing in these runners pipes a command whose rc matters"* — and this is
that pattern, surviving as dead code, in the harness that certifies the acceptance command.

### `CD-ASR-WO2R3-07-F11` — **MEDIUM, against the FRAMEWORK and against the DISPATCH** — there is no Assurance boot, so the boot instrument assigned me a role

See §1.2. `pbg boot` takes no role argument and boots *"the application Project Lead"*. My dispatch
and `CLAUDE.md` both instruct an Assurance seat to run it. The output declares
`assigned_role PROJECT_LEAD` for a seat that is not the Project Lead. **`PBG-BOOT-002` is
non-waivable and says no agent self-assigns a role — and the framework's only boot path assigns one
to every caller.** No harm occurred: my role came from the dispatch, and I am recording the
contradiction rather than acting on the output. **This is a `pbg/` defect and `pbg/` is read-only to
me (`PBG-FWK-013`); it is reported, not repaired.**

---

## 6. THE STANDING INVITATIONS — WHAT I ATTACKED AND FAILED TO BREAK

**An absence of findings from an invited attack is worth less than a finding, so I state precisely
what I tried and what refuted me.**

### 6.1 The Project Lead's amendment of a protected file (`88e43db`) — **ATTACKED, AND MY ATTACK WAS WRONG**

I ran `git diff d60b8b9..88e43db -- BLUEPRINT.md` and grepped the §17 `RESISTED` cell's normative
phrases against `PO-DECISIONS-0022`. **I got three apparent hits — phrases in the Blueprint that
were not in the PO's file — and I was about to raise a HIGH finding that the Project Lead authored
product meaning the Product Owner did not write.**

**It was a false positive in my own probe.** The PO's ruling-2 text is a markdown blockquote,
line-wrapped with `> ` prefixes, so every phrase spanning a line break failed a single-line `grep -F`.
Re-run with blockquote markers stripped and whitespace normalised:

```
  PO=1  BLUEPRINT=2   <- 'shown to bind post-admission mutation'
  PO=1  BLUEPRINT=2   <- 'as the load-bearing defence, with admission-provenance as defence-in-depth, not the primary'
  PO=1  BLUEPRINT=1   <- 'Verified at WO-3 when real sources land'
```

The §17 cell between its anchors is **character-identical to the PO blockquote** apart from a
hyphenated line-break artefact (`construction- provenance`). **The amendment carries the Product
Owner's own bytes. `CD-D-115` was not breached. The finding I was reaching for does not exist**, and
I record the near-miss because it is the same class of error the dispatch warns about — reading two
facts and asserting a relation without running the arm that separates them (`CD-RULE-009`).

The Project Lead's authored bytes (version bump, status paragraph, §19 row, scheduling clause) are
declared as its own in the file itself, and `THE TIER IS NOT WITHDRAWN` is a re-cased restatement of
the PO's own line 36. Not normative authorship.

### 6.2 The banked `/tmp` artefacts (`d34ba8f`) — verified, no finding

Hash matches exactly (§2.1). Banked under the accountable seat identity. **A gate command that lived
only in `/tmp` is now project state, which is `PBG-CONT-007` correctly applied.**

### 6.3 `F08` as a CLASS, not an instance — **attacked, holds**

The sharpest available attack on an `F08` fix is that only the instrument the finding named was
fixed. **It was not.** Same identity, same scope, different task/lease:

```
lease.py : lease 1 ACQUIRED ; lease 2 → VERDICT: LAUNCH REFUSED — WRITE_WRITE_OVERLAP   rc=1
claim.py : claim 1 CLAIMED  ; claim 2 → VERDICT: CLAIM REFUSED — WRITE/WRITE SCOPE OVERLAP  rc=1
check_scope_disjoint.py : PLANT-COORD-05 arm 1, REFUSED and NAMED
```

**All three instruments refuse the same-identity overlap. The identity discriminator is gone from
the class and not just from the reported site.** This is the single strongest result of the
increment.

### 6.4 `F05` + `F11` — **attacked with the arm that separates, genuinely fixed**

The seat types `--write-scope 'src/*'` with three real directories on disk.

**FIXED, `b165dd9`:**
```
launch.sh: passing 2 lease argument word(s) to lease.py, unsplit and unexpanded
RECEIVED write_scope = ['src/*']
VERDICT: LEASE ACQUIRED      record's own bytes:  write_scope:  - src/*
```
**CONTRAST ARM, UNFIXED `480da0f`:**
```
lease.py: error: unrecognized arguments: src/bravo src/charlie
launch.sh: LEASE REFUSED (rc=2). NOTHING IS LAUNCHED.        rc=2
```
**The carrier is caught expanding the seat's declared scope against the filesystem.** Handing the
same glob straight to `lease.py` with no carrier yields `['src/*']` identically — so the carrier is
now transparent, which is the property `F05` demanded. **PASS.**

### 6.5 `F09`'s `--pid` half — closed, and the immortal lease is refused by derivation

```
$ lease.py acquire ... --pid 1
VERDICT: REFUSED — PID_NOT_AUTHENTICATED: --pid 1 is in session 1 and this process is in
session 1861019. ... **THIS IS THE `--pid 1` BYPASS (CD-ASR-WO2R3-06-F09)** ... REFUSED BY
DERIVATION (os.getsid), NOT BY A DENYLIST (CD-RULE-003).      rc=2
```
And an operator cannot smuggle `--pid` through the carrier — `launch.sh` refuses with `usage`,
**rc=2 measured with no pipe**, and **no lease record is created** (`ls | grep -c LZ` → `0`).
**This half of `F09` is properly closed.** `F02` above is the other half.

### 6.6 The dispatch itself, and `F05`'s `CONTROL_NOT_SATISFIABLE` concession

The dispatch invited me to say whether the Project Lead gave away too much by pre-accepting
`CONTROL_NOT_SATISFIABLE` for full `--pid` authentication. **It did not.** The residue is real
(`os.getsid` is a session bound, a sibling pid in the caller's own session passes), it is derived
rather than enumerated, it is written into every lease record's own bytes as
`pid_authenticated: false`, and the concession is narrower than the finding. **No finding against
the dispatch on that clause.** My finding against the dispatch is `F11` (§5).

---

## 7. THE FIVE ITEMS, GRADED

| # | Item | Verdict |
|---|---|---|
| 1 | **`F08`** — same-identity/same-scope hole | **PASS.** Skip removed, replaced by a label; holds across all three instruments (§6.3); both acceptance arms green (§3.1) |
| 2 | **The FALSE `L1` declaration** | **AMBER.** The identity prose is now true in all three places — but the row is not swept (`F03`) and a fourth place still asserts the old claim (`F04`) |
| 3 | **`F04`** — write-scope enforcement made binding | **PASS on the race, AMBER on the design.** 200/0/0 vs 4/0/196 (§2.4); the critical section is correctly scoped to the decision and does not serialise. **But the gatekeeper still admits a state the detector refuses (`F01`)** |
| 4 | **`F05`+`F11`** — carrier corrupting its own input | **PASS**, with a contrast arm that fires (§6.4) |
| 5 | **`F09`** — lease flippable by one command | **FAIL on the reap/release arm (`F02`), PASS on the `--pid` arm (§6.5).** One command, no identity, takes a lease from a holder measured ALIVE and records that it died |

**Four of five items are materially delivered. The fifth is half-delivered and the undelivered half
is still a one-command bypass.**

### 7.1 Do the items left open (`F10`, `F12`, `F13`, `F14`) make the five that were fixed unsound?

**No — with one qualification.** I did not grade them and I do not grade the increment down for
their absence. The qualification is `Q11`: **every instrument in this tree prints `IT IS NOT INVOKED
BY ANYTHING`, and that is true.** `check_scope_disjoint.py` on the real tree returns
`rc=0, 0 live claim(s)` — a vacuous green, declared as one. **The `F08` correction is correct and
nothing runs it.** Ruling 4 inverted the priority — correctness before carriage — and on that
ordering the increment did the right work in the right order. **But "correct" is now true of four
items and not of the fifth, and none of it is carried.** No seat here may close `Q11`; I report it.

---

## 8. THE QUESTION THE PRODUCT OWNER IS WAITING ON

> Ruling 1 gates parallelism on *"the fixed machinery passes a dedicated gate"*. **Is this that gate,
> or is this only a gate on five fixes?**

**THIS IS ONLY A GATE ON FIVE FIXES. THE PROJECT LEAD IS RIGHT AND I AGREE WITH IT INDEPENDENTLY.**

And on the evidence I took, it does not pass even as that — one of the five is open (`F02`).

**I DO NOT DECLARE PARALLELISM SAFE. THAT IS MATT'S CALL WITH THIS EVIDENCE IN FRONT OF HIM, AND THE
PRODUCT OWNER'S STATED POSITION IS SEQUENTIAL-UNTIL-GREEN.**

### What a DEDICATED PARALLELISM GATE would have to measure that this one did not

1. **TWO SEATS ACTUALLY RUNNING AT ONCE.** Everything in this gate is single-seat. The race harness
   forks two `claim.py` *processes*; it does not run two *seats*. **No arm of this increment
   measured two live agents doing real work concurrently.** That is the proposition and it was
   never put to the machinery.
2. **CARRIAGE — `Q11`.** A control nothing invokes cannot make anything safe. Under sequential
   working a human runs the instrument; under parallelism nobody does. **Parallelism is precisely
   the mode in which `Q11` stops being a deferred question and becomes the whole question.**
3. **THE UNCLAIMED ACTOR.** Every instrument is blind to work done with no claim at all (`L7`,
   declared). Nothing forces a seat to claim before it writes. Under parallelism the binding is
   load-bearing; today it is `NOT PROVED TO BE CARRIED ANYWHERE`.
4. **THE GATEKEEPER/DETECTOR DISAGREEMENT (`F01`).** Two controls that disagree about one registry
   are not one control. Under parallelism the admitting one runs at claim time and the refusing one
   runs never.
5. **THE ONE-COMMAND LEASE FLIP (`F02`).** Under parallelism this is the re-entry route for the
   founding incident: one command frees a live seat's scope and the record says it died.
6. **`CD-RULE-002` AND THE TWO-SESSION PROBLEM.** `check_no_shared_record_write.py` declares it
   **cannot distinguish two concurrent sessions of the same accountable seat from one**, and that is
   `NOT PROVED TO BE CARRIED ANYWHERE`. **The founding incident was two Project Lead sessions under
   one identity.** Until identity is per-session, the machinery cannot see the incident it was built
   for — `check_scope_disjoint.py` now flags the *claims*, which is real progress, but only if the
   sessions took claims.
7. **A FALSIFICATION ARM AT THE SYSTEM LEVEL.** Every plant mutates one instrument. A parallelism
   gate needs a counterfactual in which two genuinely concurrent seats collide and the machinery is
   shown to stop them — and a mutated arm in which it is shown to fail to.

**Items 1, 2 and 6 are the ones I would not proceed without.**

---

## 9. WHAT I DID NOT EXAMINE, AND WHAT I COULD NOT

**Narrowing scope silently is prohibited, so this list is explicit.**

- **I did not attack the arms of `PLANT-COORD-01`–`04` and `06`–`08` individually.** I re-ran them
  and they are LIVE at the authentic SHA (§4), but the §3.3 finding about what "contrasted" means
  applies to them too and I built no counterfactual mutations for them.
- **I did not grade `F10`, `F12`, `F13`, `F14`** (out of reach per dispatch). §7.1 answers only
  whether their absence makes the five unsound.
- **I did not grade `check_lease_held.py`, `check_build_log_blocks.py`,
  `check_no_shared_record_write.py` or `check_build_log_pointer_atomic.py` against their own
  propositions.** I confirmed `CD-PL-F156`'s figures were not re-derived by me and I take them as
  the Project Lead's measurement, **not as mine.**
- **`CD-PL-F156`'s question — is a declared-but-still-counted limit a defect? — I did not resolve.**
  I record my view: **yes, when the verdict line refuses on it.** `L4` declaring an ordering limit
  and the `VERDICT` line counting it anyway is two instruments in one file, and the Product Owner
  should rule. I am not a party to it, but I did not measure it, so this is opinion and I label it
  as opinion.
- **I could not reproduce `PLANT-COORD-06` arm 2's flakiness** in 16 runs (§3.4). `UNSUPPORTED` for
  that check; the Engineer's `F06` stands on its own evidence.
- **I did not examine the Section D scoping, the `CD-D-105` closure, or the widened-class /
  reclassified-door / sealed-class chain.** Open invitations, not taken, for time. **Said plainly
  rather than implied.**
- **I did not verify `CD-PL-F154`'s reflog claim myself.** I confirmed the *banking* commit `d34ba8f`
  carries the accountable identity, which is a different fact.
- **The `wo-2r3` lane at `be0b355`, `/srv/crash-detector-inc12` and `-inc13`: untouched.**

---

## 10. STANDING — NOTHING MOVED SILENTLY

`CD-AC-005` **RED** · `CD-AC-002` **AMBER, NOT CLOSED** · WO-2 gate **SHUT** ·
`CD-ASR-WO2R3-04-F01` **NOT CLOSED** · six `DEFECT_OPEN` tier-1 sites ·
`CD-F-0001`–`CD-F-0004` **ALL OPEN**.

**I moved none of them.** Nothing I measured bears on any of them; my scope was the coordination
machinery, not the detector's type perimeter. `CD-ASR-WO2R3-06-F09` **does not close** and my `F02`
is the reason.

### Mutation boundary — honoured

```
$ git status --porcelain -- tools/ governance/coordination/ BLUEPRINT.md PID.md governance/decisions/
   (empty)
$ git rev-parse HEAD → 9aeaf335178534f6c7c829667d2c8055206873ae
```
No commit, no reset, no checkout, no merge, no worktree in the real tree. `ACTIVE_WORK.yaml`
untouched. `/srv/crash-detector-inc12` and `-inc13` untouched. All mutation confined to
`/tmp/cd-asr-wo2r3-07/`. `PLANT_SCRATCH` was set to my own scratch on every plant invocation and
never defaulted into `/tmp/cd-eng-coord-01/plants`. **This verdict document is my only write.**

---

## 11. WHAT IS GENUINELY GOOD

**An unscoped RED is as useless as an unscoped PASS, and this is AMBER, so the same duty applies.**

- **The `F08` fix is the real thing.** Not a deletion dressed up: the skip is gone, the pair loop
  examines every distinct pair at any identity, the two neighbouring exemptions survived
  deliberately and are declared as *pairing* and *single-record* exemptions rather than identity
  ones — **and I proved by mutation that a control which took them out with the skip would be
  caught** (§3.2). That distinction is subtle, it was got right, and getting it wrong would have
  banned concurrency while looking like a fix.
- **`F05`+`F11` is fixed structurally, not patched.** `set -f`, positional parameters, no `eval`,
  and a receiving-side echo so the carrier's corruption becomes visible at the point it happens. The
  contrast arm catches the old carrier red-handed (§6.4).
- **The instruments fail closed and say so loudly.** My own broken tree produced
  `VERDICT: REFUSED — git rev-parse HEAD failed`, not a false green. Every probe printed the tree it
  ran in. **The `[TREE]` banner is why I could tell my first race was worthless.**
- **`--pid 1`, the immortal lease, is refused BY DERIVATION and the refusal explains itself** —
  including naming the finding it closes and stating that it is not a denylist.
- **The Engineer raised four findings against its own work, superseded its own return to do it, and
  told the next seat to attack its own test first.** I attacked it as instructed and arms 3/4 held.
  **That invitation is why this gate has evidence instead of a claim.**
- **The Project Lead disclosed the substitution rather than manufacturing a claim to make
  `merge_reconcile.py` pass.** That was the whole temptation and it declined it. My `F07` widens the
  consequence; it does not fault the choice.
- **The dispatch told me the Project Lead's figures before I measured, and told me they were claims.**
  I got a different number on the race (196) and the disagreement cost nothing, because nobody had
  adjusted anybody. **That is the inherited-claim mechanism working as designed for once.**

---

## 12. CONTINUATION IMPLICATION, AND THE NEXT SAFE GATE

**What is true and what is safe to do next are different calculations.**

**TRUE:** four of five named items are delivered and measured; both named acceptance commands pass
against the authentic target with live contrast arms; the fifth item is half-open with a one-command
bypass; three prose/record defects survive the `CD-RULE-004` sweep; none of the machinery is
invoked by anything.

**SAFE:** the target is **safe to leave standing on `main`**. Nothing I found is a regression, the
tree is internally consistent enough to build on, and `b165dd9` is better than `480da0f` by every
measurement I took. **It is NOT safe to treat this gate as the parallelism precondition**, and
**`CD-ASR-WO2R3-06-F09` must not be recorded as closed.**

### NEXT SAFE GATE

**A PRODUCT OWNER RULING, AND NOT AN ENGINEER DISPATCH.** The ninth seat's sentence applies again,
for a different reason: the decisions in front of this project are no longer implementation
questions.

**NEXT ACTOR: THE PRODUCT OWNER (Trinity), preparing for Matt as final authority.**

Four things need a ruling before any further build:

1. **`F02` — is `F09` closed or not?** It was named as fixed by ruling 5 and it is not. **A seat
   must not record it closed on this verdict.** Whether the reap/release arm is a sixth item, a
   re-opening of the fifth, or accepted-and-declared is a Product Authority call.
2. **`F01` — the gatekeeper/detector disagreement.** Whether `claim.py` should carry both `F134`
   directions, or whether the asymmetry is accepted and declared, is a design ruling with a
   parallelism consequence.
3. **`F07` — the merge control is unrunnable in the standing mode.** Sequential single-seat is now
   standing; `merge_reconcile.py` requires `--claim`. Either the mode gets a claim, or the
   instrument gets a sequential mode, or `CD-CT-007` is declared inapplicable — and each is a
   Product Authority choice, not an Engineer's.
4. **§8 — parallelism.** My evidence says this is not the dedicated gate ruling 1 requires, and I
   have named the seven things such a gate would have to measure. **Items 1, 2 and 6 of that list
   are the ones I would not proceed without.**

`F03`, `F04`, `F05`, `F06`, `F08`, `F09`, `F10` are ordinary remediation and can be folded into a
bounded Engineer dispatch **after** the rulings above, by a seat that is not me (`PBG-SOD-004` — I
found them, I do not fix them). **`F11` is a `pbg/` defect: read-only to every seat here, and a
separate bounded dispatch if the framework owner wants it.**

---

**`PBG-AUTH-003`: this is a verdict and an input to acceptance. IT IS NOT AN ACCEPTANCE.**

*`CD-ASR-WO2R3-07`, tenth Assurance seat, over `b165dd99a22a9a65b8e743274cec02ed7010dc22`.
Every figure in this document was taken by me on the tree named in §1, in my own scratch at
`/tmp/cd-asr-wo2r3-07/`, and no figure was carried forward from any earlier boundary.*
