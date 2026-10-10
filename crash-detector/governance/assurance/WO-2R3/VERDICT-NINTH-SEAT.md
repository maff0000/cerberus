# VERDICT — NINTH ASSURANCE SEAT — CD-ASR-WO2R3-06

    actor_id:   CD-ASR-WO2R3-06
    dispatch:   CD-DISPATCH-WO2R3-ASSURANCE-09
    role:       ASSURANCE_ENGINEER (assigned by dispatch; PBG-BOOT-002 — not self-assigned)
    started:    2026-08-23T14:53:14Z   # `date -u`
    status:     IN PROGRESS — written incrementally per dispatch how_you_work

## 0. TARGETS, RESOLVED AND NOT TRANSCRIBED (CD-PL-F36)

```
cd /srv/crash-detector-wo2r3-audit9 && git rev-parse HEAD && git cat-file -t $(git rev-parse HEAD) && git status --porcelain | wc -l
  -> be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5   commit   0
cd /srv/crash-detector-audit9-main && git rev-parse HEAD && git cat-file -t $(git rev-parse HEAD) && git status --porcelain | wc -l
  -> 4f3f4ceed22b089aaf7226e0d73922152cb2819c   commit   0
```

Both targets resolve to real commits. Both porcelain **0**, independently measured by me, not taken
from the dispatch.

FREEZE OF TREE 1 VERIFIED against the eighth seat's own worktree, not against the dispatch sentence:
```
cd /srv/crash-detector-wo2r3-audit8 && git rev-parse HEAD
  -> be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
```
Identical. The eighth gate's target and mine are the same object. **Freeze upheld.**

## 0.1 DISPATCH INTEGRITY — the check CD-PL-F143 existed because nobody ran it

My `main` target `4f3f4ce` does NOT contain my own dispatch (the Engineer's `F06`, applied to me as
the dispatch itself warned):
```
git -C /srv/crash-detector cat-file -p 4f3f4ce:governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-09.yaml
  -> fatal: path ... exists on disk, but not in '4f3f4ce'
```
So I read it from `/srv/crash-detector` and pinned it:
```
sha256sum /srv/crash-detector/governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-09.yaml
  -> 1a46ea7094937dcfa93b2d520bd52450b91f5a57624ab1417d86b13b444fab93
git -C /srv/crash-detector show 1699f03:governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-09.yaml | sha256sum
  -> 1a46ea7094937dcfa93b2d520bd52450b91f5a57624ab1417d86b13b444fab93
```
The working-tree copy I read is **byte-identical to the committed object at `1699f03`**. Pinned copy
kept at `/tmp/cd-asr-wo2r3-06/dispatch-at-start.yaml` for re-diff at the end.

## 0.2 `git log 4f3f4ce..main` AT THE START (reported per dispatch, re-run at the end)

```
git -C /srv/crash-detector log --oneline 4f3f4ce..main
  -> 1699f03 [CRASH-DETECTOR] CD-DISPATCH-WO2R3-ASSURANCE-09 ISSUED ...
git -C /srv/crash-detector log --numstat --format='COMMIT %h' 4f3f4ce..main
  -> 335 0 governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-09.yaml   (ONE file, additions only)
```
**ONE commit, ONE file, inside the write scope the dispatch promised.** Author and committer both
`PROJECT_LEAD_SEAT_01 <project-lead-seat-01@seats.crash-detector.invalid>`. The `returns_to` promise
holds at the start of my audit.

---
# PART A — THE CORRECTED THREE-TIER PERIMETER

## A.1 What the three tiers ACTUALLY are, measured (dispatch PART_A question 2, answered wider)

The dispatch asks whether the **DETECTED** half is "a control or a promise". The honest answer is
larger than the question and I record it as such:

| Tier | Blueprint claim | BUILT AT `be0b355`? | Evidence |
|---|---|---|---|
| PREVENTED | exact-type admission, refuses the forged SUBCLASS `F2` and every accident | **YES** | `src/crash_detector/admission.py` `_Exactly.refusal` → `is_exactly` (identity, not `==`) |
| RESISTED | a CONSTRUCTION-PROVENANCE door at admission | **NO — NOT BUILT** | measured below |
| DETECTED | witness divergence + provenance at the publication boundary | **NO — NOT BUILT** | scheduled `CD-AC-018`, WO-3/WO-4 |

MEASURED, on the product lane, printing its tree (CD-PL-F98):
```
cd /srv/crash-detector-wo2r3-audit9 && git rev-parse HEAD   # be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
grep -rn "WeakSet\|WeakKeyDictionary" --include=*.py .      # NO MATCHES
grep -rn "CD-AC-017\|CD-AC-018\|construction-provenance" . --include=*.py --include=*.md --include=*.yaml | grep -v '^./pbg/'
                                                            # NO MATCHES
```
The only `__weakref__` occurrences in the product (`dials/reading.py:159`,
`dials/magnitude.py:270`, `dials/provenance.py:284`, `serving/dial_presentation.py:176`) are members
of `TOLERATED_INTERPRETER_MACHINERY` frozensets in the *structural-surface* checks. **There is no
object-identity provenance registry of any kind in this product.**

**`CD-AC-017` and `CD-AC-018` do not appear anywhere on the product lane at all.** The Blueprint's
own text concedes the mechanism is unbuilt: *"the mechanism is specified as the discriminator, not
the implementation."*

> **FINDING `CD-ASR-WO2R3-06-F01` — HIGH.**
> **TWO OF THE THREE TIERS OF THE CORRECTED PERIMETER ARE NOT BUILT.** The perimeter is not
> "a control with a promised half"; it is **one tier of three implemented**. The dispatch names the
> DETECTED tier as the load-bearing half that does not exist. That is true, and `RESISTED` — the tier
> the whole v0.4.0 correction was written to introduce, and the tier that carries `F1`, the class
> every prior gate died on — **is equally unbuilt and is not disclosed with the same clarity.**
> §17 states RESISTED in the present indicative (*"a CONSTRUCTION-PROVENANCE door ... which the
> auditor measured separates genuine from F1 forgery in-process at admission time"*) while §16's
> parenthetical concedes it is a specification. **A reader of the risk row alone would believe a
> control exists.** This is `CD-RULE-004` applied to the Blueprint: the register/board claims more
> than the artefact carries.

## A.2 `T2` — I LOCATED THE DOOR, BUILT IT, AND DEFEATED IT WITHOUT PAYING THE DECLARED PRICE

The dispatch orders: *"Is the construction-provenance door real, and is 'defeatable only by locating
and mutating a module-private structure' TRUE? Locate it. Mutate it. Report what it cost you."*

The door is not real, so I **built it to specification** in my own scratch — in BOTH forms: **Form A**,
the `id()`-keyed set, which is the only form the Blueprint says is available (because `__slots__`
omits `__weakref__`); and **Form B**, the `WeakSet`, built anyway by paying the price the Blueprint
says is too high, so the claim is tested in its *strongest* form and not only its weakest.

```
python3 -B /tmp/cd-asr-wo2r3-06/t2/probe_resisted_tier.py       # python 3.11.2
python3 -B /tmp/cd-asr-wo2r3-06/t2/probe_id_reuse_rate.py
```

**CONTROL 0 — the door does exactly what the prior auditor measured.** Both forms REFUSE the literal
`F1` route (`cls.__new__(cls)` + `object.__setattr__`) and ADMIT a genuine object. The prior
measurement is **reproduced and is not disputed.**

**AND IT IS THE WRONG QUESTION, WHICH IS WHY IT PASSES.**

| Attack | Form A | Form B (`WeakSet`) | Module-private structure located or mutated? |
|---|---|---|---|
| `F1` literal (`cls.__new__` + `setattr`) | REFUSED | REFUSED | no |
| **ATTACK 1 — public declared door, THEN `object.__setattr__`** | **ADMITTED** | **ADMITTED** | **NO** |
| **ATTACK 2 — `id()` reuse** | **ADMITTED** | n/a | **NO** |
| ATTACK 4 — mutate the registry (the *conceded* defeat) | ADMITTED | ADMITTED | yes — **1 line** |

**ATTACK 1, and this is the finding.** The discriminator asks *"did this object leave a declared
door?"*. An actor already executing in-process simply **walks in the front door** to obtain an object
with **genuine** provenance, and then forges its value:
```python
m = declared_door(frozenset({"stress"}), 0.01)   # genuine. registered. public API.
object.__setattr__(m, "quantity", 99.0)          # forged value.
admit(m)                                          # -> ADMITTED
```
Result measured: `ADMITTED  DialMagnitude(frozenset({'stress'}), 99.0)` on **both forms**. Zero
knowledge of any module-private name. Zero package lines beyond the public API. **The provenance is
authentic and the value is forged, and the door cannot tell, because provenance of CONSTRUCTION is
not integrity of VALUE.**

**ATTACK 2.** Form A keys on `id()`. CPython recycles addresses off the type free-list immediately:
```
TRIALS=10000  ADMITTED_FORGERIES_VIA_ID_REUSE=9999  RATE=0.9999
```
An object that **never went through any door** inherits a dead genuine object's provenance, at a
**99.99% rate, on the first allocation**, with zero module-private knowledge. Form A additionally
cannot ever evict (it holds integers, not references), so it is an unbounded leak *and* that leak is
the precondition for its own defeat.

> **FINDING `CD-ASR-WO2R3-06-F02` — HIGH. THE LOAD-BEARING SENTENCE OF THE `RESISTED` TIER IS FALSE
> AS MEASURED.**
> BLUEPRINT §17 `CD-BP-005` states the construction-provenance door is *"defeatable ONLY by locating
> and mutating a module-private structure (a difference IN KIND from F1's zero-knowledge,
> zero-package-line cost against exact type)"*.
> **THREE DEFEATS ADMIT A FORGED VALUE WITHOUT LOCATING OR MUTATING ANY MODULE-PRIVATE STRUCTURE**,
> two of them against the `WeakSet` form the text treats as the strong one. Their cost is
> **zero-knowledge and zero-package-line — precisely the cost the sentence says they do not have.**
> There is therefore **no difference IN KIND**, and the word `RESISTED` is not earned by the
> mechanism as specified.
> Note the cost of the *conceded* defeat (ATTACK 4) is **one line**. The sentence draws a
> kind-boundary between a one-line attack and a two-line attack.

> **FINDING `CD-ASR-WO2R3-06-F03` — HIGH, AND IT IS AGAINST THE MEASUREMENT, NOT THE MECHANISM.**
> **`GUARD_THE_INSTANCE_NOT_THE_CLASS`, AND IT IS THE SAME MISTAKE `PO-DECISIONS-0011` RULING 2
> ALREADY HARVESTED A RULE FROM.** The measurement the Product Owner rested the v0.4.0 correction on
> varied exactly one axis: **the construction route**. It never varied the axis that matters —
> **what happens to the value AFTER a genuine construction.** My CONTROL 0 reproduces the auditor's
> result exactly; ATTACK 1 varies the untested axis and the door falls immediately.
> PO-DECISIONS-0011 ruling 2 is the Product Owner recording that it accepted contrast evidence
> *"without asking which axis it varied"*, and harvesting *"a rule that binds seats binds their
> Product Owner."* **The retraction at PO-DECISIONS-0019 was accepted on evidence that varies one
> axis, and the rule the Product Owner wrote against itself was not applied.**
> The Product Owner's stated reason for the retraction — *"ADMISSION WAS NEVER TESTED"* — was
> correct. **Admission has now been tested. It does not hold.**

**WHAT THIS DOES NOT SAY.** It does not say construction-provenance is worthless: it genuinely
refuses the literal `F1` route and would raise the cost of a naive attack. It says the tier is
**mis-named and over-claimed**, that the sentence asserting the cost boundary is **false as
measured**, and that a mechanism scheduled at WO-3 on the strength of a one-axis measurement will
arrive already defeated unless the specification changes.


---
# PART B — INCREMENT 12

## B.1 `T8` — ALL FOUR COORDINATION PLANTS RE-APPLIED BY ME. 13/13 ARMS LIVE.

Authentic-target check FIRST, because the plants clone the **Engineer's** worktree and not my target:
```
git -C /srv/crash-detector merge-base --is-ancestor 59cb3c1 4f3f4ce ; echo $?    -> 0
git -C /srv/crash-detector diff --stat 59cb3c1 4f3f4ce -- tools/coordination governance/coordination
   -> (empty)
```
**The coordination machinery is byte-identical at `59cb3c1` and at my target `4f3f4ce`.** Running the
plants against `/srv/crash-detector-inc12` is therefore authentic for this target and I do not have
to accept a substitute (`PBG-ASSURE-001`). I verified this rather than assuming it.

```
cd /srv/crash-detector-audit9-main/governance/coordination/plants
for p in 01 02 03 04; do SOURCE_ROOT=/srv/crash-detector-inc12 sh ./PLANT-COORD-$p.run.sh; echo "rc=$?"; done
```
| Plant | arms | runner rc | verdict |
|---|---|---|---|
| PLANT-COORD-01 | 3/3 | 0 | LIVE |
| PLANT-COORD-02 | 4/4 | 0 | LIVE |
| PLANT-COORD-03 | 3/3 | 0 | LIVE |
| PLANT-COORD-04 | 3/3 | 0 | LIVE |

**13/13, reproducing the Project Lead's figure digit for digit on my own run.** Every runner printed
`source HEAD : 59cb3c1da6c4c7480d2af3f1fe8b0c5c815d4b53` and its sandbox path (`CD-PL-F98` honoured
by the harness itself). The ARM 3 assertions are **effect-checked, not rc-checked** — PLANT-COORD-03
performs the merge and greps both seats' bytes out of the result; PLANT-COORD-04 asserts two live
leases and the first process still alive. **This is good plant construction and I say so.**

## B.2 `CD-PL-F151` UPHELD — AND IT IS WORSE THAN THE PROJECT LEAD RECORDED

```
git -C /srv/crash-detector archive 4f3f4ce | tar -x -C /tmp/cd-asr-wo2r3-06/archive-src
SOURCE_ROOT=/tmp/cd-asr-wo2r3-06/archive-src sh ./PLANT-COORD-02.run.sh ; echo $?
  -> source HEAD : <EMPTY>
  -> clone rc=128
  -> ARMS: 0 / 4 contrasted as required
  -> PLANT VERDICT: *** NOT A CONTRAST ***
  -> runner rc=1
```
The Project Lead recorded `ARMS 1/3`. **On PLANT-COORD-02 it is `0/4`.** An auditor following this
project's own established pristine-tree method records a **totally** false negative on a LIVE plant.
`PLANT_SCRATCH="/tmp/cd-eng-coord-01/plants"` at `lib.sh:26` is a bare assignment, **not**
`${PLANT_SCRATCH:-...}`, so it cannot be overridden from the environment — I verified that too. The
finding is upheld and extended.

## B.3 *** `CD-ASR-WO2R3-06-F04` — HIGH. THE CLAIM REGISTRY IS NOT ATOMIC OVER THE THING THE RULING ASKS IT TO BE ATOMIC OVER. ***

`PO-DECISIONS-0021` ruling 3 states the invariant in terms: **"no two live seats share a TASK or a
WRITE SCOPE."** The registry is atomic over **TASK**. It is **not** atomic over **WRITE SCOPE**, and
the difference is a TOCTOU window in `claim.py`:

```
tools/coordination/claim.py:135-158   for other in live_claims(root): ... scope_mod.overlaps(...)   <-- CHECK (a directory read)
tools/coordination/claim.py:187       registry.write_exclusive(path, payload)                       <-- USE  (O_EXCL)
```
`O_EXCL` makes the **filename** — the task id — exclusive. Two seats with **different task ids** and
**identical write scopes** take **different filenames**, so `O_EXCL` never fires, and the only thing
between them is the read at 135 and the write at 187.

**RACED, NOT REASONED ABOUT** (`/tmp/cd-asr-wo2r3-06/race/race_scope.py`, sandbox clone at
`59cb3c1`, `stat -f -c %T` -> `ext2/ext3`, two concurrent processes, 200 rounds, different task ids,
**identical** `write_scope: src/contended/**`):
```
cd /tmp/cd-asr-wo2r3-06/race && python3 -B race_scope.py 200
  ROUNDS=200  concurrency=2  DIFFERENT task_ids, IDENTICAL write_scope='src/contended/**'
    exactly-one-winner (CORRECT) :   7
    ZERO winners                 :   0
    *** TWO WINNERS (DOUBLE-TAKE ON ONE SCOPE) *** : 193
```
**193 of 200 rounds put TWO seats on ONE write scope, both `VERDICT: CLAIMED`, both rc=0.**

VERIFIED BY THE RESULT AND NOT BY THE EXIT CODE — both records exist on disk simultaneously:
```
governance/coordination/claims/RACE-500-A.claim.yaml : seat_actor_id: SEAT-ALPHA  write_scope: - src/contended/**  state: CLAIMED
governance/coordination/claims/RACE-500-B.claim.yaml : seat_actor_id: SEAT-BRAVO  write_scope: - src/contended/**  state: CLAIMED
```
**AND THE INCREMENT'S OWN DETECTOR AGREES WITH ME**, which is what makes this a defect and not a
disagreement about intent:
```
python3 -B tools/coordination/check_scope_disjoint.py --root .
  VIOLATION WRITE/WRITE  seat SEAT-ALPHA (task RACE-500-A) x seat SEAT-BRAVO (task RACE-500-B)
  VERDICT: REFUSED — 1 scope violation(s) among 2 live claim(s)      rc=1
```
The state the *claim* instrument produced is a state the *disjointness* instrument calls a
**VIOLATION**. Deliverable 3(a) — *"a task is atomically claimed before it is worked"* — holds.
**Ruling 3's actual invariant, the WRITE SCOPE half, does not.**

### WHY THE EXISTING EVIDENCE DID NOT CATCH THIS — and it is `T6` exactly

`EV-ATOMICITY-MEASUREMENT.md` raced a **standalone `os.open` probe on one path**
(`/tmp/cd-eng-coord-01/fsprobe/race.py`), not `claim.py`. `6400 attempts / 200 wins / 0 double-takes`
is a true statement **about `O_EXCL`** and I reproduce no dispute with it. It is evidence about the
**syscall**, not about the **instrument**, and the instrument is where the check-then-use lives.
`PLANT-COORD-01` arm 1 races the **same** task id (`O_EXCL`'s case). `PLANT-COORD-02` arm 1 exercises
overlapping scopes **sequentially**. **NOTHING IN INCREMENT 12 RACES THE SCOPE CHECK.** The one
predicate the whole increment exists to enforce is the one predicate never raced.

> This is `PO-DECISIONS-0011` ruling 2 for the third time in this verdict: **the evidence varies the
> axis it was built to vary and not the axis the claim needs.**

### WHAT THE DECLARED LIMITS DO AND DO NOT SAY — `CD-RULE-004` applied

`claim.py`'s limit block is unusually honest, and it still does not cover this:
* `L1 DECIDES: mutual exclusion on a TASK ID ... MEASURED at 6400 concurrent attempts` — true.
* `L2 DECIDES: refusal of a claim whose write_scope overlaps a live claim's` — **stated flatly, with
  no concurrency qualifier at all.** It is true single-threaded and false under concurrency.
* `L3/L4/L5/L6` cover task-id synonymy, unclaimed work, network filesystems and hand-edited files.
  **None of them is this.**

**`L2` IS THE DEFECT.** `CD-RULE-004` permits an instrument to declare its class instead of closing
it; the dispatch's own fourth edge says **"A DECLARED LIMIT IS NOT A LICENCE."** Here there is not
even a declaration: `L2` asserts the property **unconditionally**, in the instrument whose entire
purpose is concurrency, and the header immediately above it teaches the reader that
`if os.path.exists(p): refuse` followed by a write is *"the defect, not the control"* — which is
**precisely the shape of lines 135-187**. The module names the anti-pattern and then contains it.


## B.4 *** `CD-ASR-WO2R3-06-F05` — HIGH. `launch.sh` MANGLES THE WRITE SCOPE AND MANUFACTURES A FALSE GREEN. ***

`tools/coordination/launch.sh` is ITEM 4(i), the **driver half of the launch lease** that
`PO-DECISIONS-0021` ruling 3(d) ordered. It accumulates scope arguments into a string and expands it
**unquoted**:
```
launch.sh:52   --write-scope) LEASE_ARGS="$LEASE_ARGS --write-scope $2"; shift 2 ;;
launch.sh:71   python3 -B "$ROOT/tools/coordination/lease.py" ... --pid "$$" $LEASE_ARGS
                                                                              ^^^^^^^^^^^ unquoted
```
Unquoted expansion in POSIX `sh` performs field splitting **and pathname expansion**. A write scope
is a glob. **The shell therefore expands the seat's declared scope against the filesystem before
`lease.py` ever sees it.** Two regimes, both wrong:

**(i) glob matches ≥2 paths -> HARD FAILURE REPORTED AS A REFUSAL.**
```
cd /tmp/cd-asr-wo2r3-06/race/tree
sh tools/coordination/launch.sh --lease X2 --seat S2 --task T2 --write-scope 'tools/coordination/*' --dry-run -- true
  -> lease.py: error: unrecognized arguments: tools/coordination/check_build_log_pointer_atomic.py ... (13 paths)
  -> launch.sh: LEASE REFUSED (rc=2). NOTHING IS LAUNCHED.
```
An argparse error is printed to the operator as **`LEASE REFUSED`**, indistinguishable from a
genuine scope collision. **Commissioning this carrier would refuse every real launch and tell the
operator there was a conflict.**

**(ii) glob matches exactly 1 path -> SILENT SCOPE NARROWING -> FALSE GREEN. THIS IS THE DANGEROUS ONE.**
Both arms, one variable (`CD-D-079`):

*ARM 1 — through `launch.sh`.* Seat A intends the `docs/alpha` subtree and types `docs/alpha/*`:
```
sh tools/coordination/launch.sh --lease LA --seat SEAT-A --task TASK-A --write-scope 'docs/alpha/*' --dry-run -- true
  -> VERDICT: LEASE ACQUIRED — THE LAUNCH MAY PROCEED     rc=0
  -> the lease record says:  write_scope = ['docs/alpha/only.md']      <-- NOT WHAT WAS TYPED
python3 -B tools/coordination/lease.py --root . acquire --lease LB --seat SEAT-B --task TASK-B --pid <live> --write-scope 'docs/alpha/other.md'
  -> VERDICT: LEASE ACQUIRED — THE LAUNCH MAY PROCEED     rc=0
```
**TWO SEATS HOLD LIVE LEASES OVER ONE SUBTREE.**

*ARM 2 — counterfactual, the identical request against the UNMANGLED scope:*
```
lease.py acquire --lease LA2 --seat SEAT-A --write-scope 'docs/alpha/**'         -> rc=0
lease.py acquire --lease LB2 --seat SEAT-B --write-scope 'docs/alpha/other.md'
  -> VERDICT: LAUNCH REFUSED — WRITE_WRITE_OVERLAP
     docs/alpha/other.md <> docs/alpha/**  OVERLAP: 'docs/alpha/**' is a recursive prefix
                                                          rc=1
```
**SAME REQUEST. OPPOSITE VERDICTS. THE ONLY VARIABLE IS WHETHER THE SCOPE PASSED THROUGH
`launch.sh`.** The algebra is correct; the carrier corrupts its input before it arrives. Confirmed
directly against `scope.py`:
```
python3 -c "import sys;sys.path.insert(0,'tools/coordination');import scope as s;print(s.overlaps(['docs/**'],['docs/gamma/**']));print(s.overlaps(['docs/alpha','docs/beta'],['docs/gamma/**']))"
  -> (True,  ["... OVERLAP: 'docs/**' is a recursive prefix of 'docs/gamma/**'"])
  -> (False, [])
```

### WHY `PLANT-COORD-04` DID NOT CATCH IT — `GUARD_THE_INSTANCE_NOT_THE_CLASS`, IN THE PLANT

```
grep -n 'write-scope' governance/coordination/plants/PLANT-COORD-04.run.sh
  :66,:93   --write-scope 'src/contended/module.py'   <- a LITERAL, no glob
  :126      --write-scope 'docs/bravo/**'             <- a glob matching NOTHING on disk
```
**The only two scope forms the plant exercises are precisely the two that cannot trigger the
defect.** The plant is 3/3 LIVE and the deliverable it certifies is broken for every glob that
matches a real path. This is the strongest instance in this audit of the theme the role contract
names: a plant that proves its own chosen instance.

> `CD-ASR-WO2R3-06-F05` is not a portability nit. `launch.sh` is the **one** artefact in increment 12
> whose entire purpose is to be commissioned by the operator's wrapper (`Q12`). It is the join
> between the built half and the unbuilt half of ruling 3(d). **It does not work.**

## B.5 WHAT IS GENUINELY GOOD, MEASURED AND SAID PLAINLY

An unscoped RED is as useless as an unscoped PASS. These held under attack:

* **`scope.py`'s algebra is correct** on every form I put to it, including recursive-prefix
  detection, and it printed the right answer even when its caller fed it corrupted input.
* **`liveness.py`'s substitute for the cmdline match is stronger, not merely different** (Engineer
  `F02`). Measured verbatim on my own run: `liveness=LIVE (/proc/1518408 exists and
  /proc/1518408/stat field 22 == 28361564, so PID recycling is EXCLUDED; cmdline DRIFTED from 'sh
  tools/coordination/launch.sh ...' to 'sleep 300' — expected after exec(), NOT treated as death)`.
  It handles the exact `exec` case that made the dispatch's original rule declare every live seat
  dead, **and** it closes PID recycling, which a cmdline match does not. **F02's remedy is sound and
  I find for it.**
* **The plants' ARM 3 assertions check EFFECTS, not exit codes** — PLANT-COORD-03 greps both seats'
  bytes out of the merged worktree; PLANT-COORD-04 asserts two live leases with the first process
  still running. That is the right construction.
* **`claim.py` and `lease.py` fail closed** on a missing `ACCOUNTABLE-SEAT.yaml`
  (`PRECONDITION_NOT_MET`) and refuse rather than sanitise a bad identifier (`safe_identifier`).
* **`EV-ATOMICITY-MEASUREMENT.md` §4 is a model of an honest limit section** — it states in advance
  that 6400 attempts rules out a broken implementation and not a rare one. My finding `F04` is not
  that this document overclaims; it is that **it measures the syscall and the record then cites it
  for the instrument.**

## B.6 `T9` — I TRIED TO OBTAIN A FAKE GREEN `ARM 3` AND COULD NOT. THIS IS A PASS.

The dispatch: *"Try to make a fake ARM 3 pass. If a control could refuse the disjoint case and still
show a green ARM 3, the whole ruling is unimplemented and nobody would know."*

**METHOD — a mutation test on the ARM, not on the control.** I cloned the source into my own scratch
and committed a mutation that makes the control **BAN CONCURRENCY** — refuse *every* pair, including
the disjoint one — which is precisely what `PO-DECISIONS-0021` ruling 3 rejects. Then I ran the
authentic, unmodified plants against it.

**MUTATION 1** — `scope.py: overlaps()` returns `(True, [...])` unconditionally
(`/tmp/cd-asr-wo2r3-06/t9/src`, HEAD `e7ece793c9be864cd8aa55eeaedcfb6b1b5530f9`):
```
SOURCE_ROOT=/tmp/cd-asr-wo2r3-06/t9/src sh ./PLANT-COORD-0N.run.sh
```
| Plant | ARM 3 | verdict |
|---|---|---|
| 01 | **DID NOT CONTRAST** | NOT A CONTRAST 0/3 |
| 02 | **DID NOT CONTRAST** | NOT A CONTRAST 1/4 |
| 03 | CONTRASTED (still green) | LIVE 3/3 |
| 04 | **DID NOT CONTRAST** | NOT A CONTRAST 2/3 |

Plant 03 stayed green — and **that is correct, not a hole.** I verified the mutation was off-target
rather than reporting it as a finding: `merge_reconcile.py:168` decides non-overlap by
`set(a["touched_paths"]) & set(b["touched_paths"])`, a plain set intersection, and touches
`scope_mod.patterns_overlap` only for the CONTAINMENT assertion at `:116`. `overlaps()` is never on
its non-overlap path. **My mutation did not reach it.**

**MUTATION 2 — ON-TARGET FOR PLANT 03.** `merge_reconcile.py:174` changed from `for p in inter:` to
`for p in (inter or ["<T9B-MUTATION>"])`, so the merge gate refuses the **disjoint** pair too
(`/tmp/cd-asr-wo2r3-06/t9b/src`, HEAD `3fa48df95a9d7f0815840f36167ea09177313fa0`):
```
ARM 1  BASELINE REFUSES   : CONTRASTED AS REQUIRED
ARM 2  VIOLATED ADMITS    : *** DID NOT CONTRAST ***
ARM 3  NON-VACUITY ADMITS : *** DID NOT CONTRAST ***
ARMS: 1 / 3      PLANT VERDICT: *** NOT A CONTRAST ***
```

> **`T9` VERDICT: PASS, with confidence.** **ALL FOUR ARM 3s WENT RED AGAINST A CONTROL THAT BANS
> CONCURRENCY, EACH AGAINST ITS OWN TARGET.** The non-vacuity arm is genuinely non-vacuous. I could
> not manufacture a fake green. `PO-DECISIONS-0021` ruling 3's rejection of "ban concurrency" **is
> implemented and is detectable**, and the third arm is the best single piece of engineering in
> increment 12.

## B.7 `T10` — THE PROJECT LEAD SAID "CONSISTENT WITH" AND REFUSED TO WRITE "CONFIRMED". **I CONFIRM IT.**

Measured on my target, at my target's SHA:
```
cd /srv/crash-detector-audit9-main
python3 -B tools/coordination/check_build_log_blocks.py --root . --table --entries ; echo $?
  -> entries_examined = 98   distinct_ids = 97   entry_violations = 67
  -> VERDICT: REFUSED — 67 violation(s)                                   rc=1
grep -E '^\s+VIOLATION ' <log> | awk '{print $2}' | sort | uniq -c
  ->  27 UNALLOCATED_AUTHOR   39 OUT_OF_BLOCK   1 DUPLICATE       (27+39+1 = 67)
```
**The composition is exactly as the Project Lead described it: 27 + 39 + 1 = 67. CONFIRMED.**

And independently of the instrument, with my own `git` commands, because an instrument confirming
the record it was built from is not independent evidence (`PBG-EVID-001`):
```
git -C /srv/crash-detector log 4f3f4ce --diff-filter=A --format='%H|%an' --name-only -- governance/engineering/build-log/ | awk -F'|' '/\|/{a=$2;next} /\.yaml$/{print a}' | sort | uniq -c
  ->  70 PROJECT_LEAD_SEAT_01    27 Matt Scott    1 CD-ENG-COORD-01
git -C /srv/crash-detector log 4f3f4ce --format='%an' -- governance/engineering/ACTIVE_WORK.yaml | sort | uniq -c
  -> 108 PROJECT_LEAD_SEAT_01    34 Matt Scott
git -C /srv/crash-detector log -1 --format='author=%an <%ae>  committer=%cn <%ce>' 44c5ef5
  -> author=Matt Scott <rogue@cerberus.local>  committer=NoustAI-PDA <pda@noustai.com>
python3 -B tools/coordination/check_no_shared_record_write.py --root . --range e6f9802
  -> VERDICT: REFUSED (retrospective) — 34 commit(s) ...                  rc=1
```
> **THE ENGINEER'S `F03` IS CONFIRMED BY TWO INDEPENDENT METHODS. 27 Build Log entries and 34
> `ACTIVE_WORK.yaml` commits on `main` carry a HUMAN author identity, and `44c5ef5` carries BOTH of
> the exact identities `CD-RULE-002` names verbatim as its own measured failure.** `CD-RULE-002` is
> sourced to the **Product Authority** and is **non-relaxable by any seat**. `Q16` is real and it is
> the Product Owner's. I do not rule on it; I remove the word "consistent" from in front of it.

## B.8 `T7` — THE INHERITED-CLAIM MECHANISM, FOUND INSIDE THIS DISPATCH

> **FINDING `CD-ASR-WO2R3-06-F06` — MEDIUM, AGAINST THE DISPATCH (`T12`).**
> The dispatch places instruments 5-12 under the heading
> **`ON_MAIN_AT_4f3f4ce_AND_THESE_THE_PROJECT_LEAD_DID_RUN_TODAY`** — an explicit claim that these
> figures belong to `4f3f4ce`. **Two of their operands do not.**
>
> ```
> for s in 59cb3c1 6c58725 4f3f4ce main; do echo "$s $(git rev-list --count $s) commits \
>   $(git ls-tree -r --name-only $s -- governance/engineering/build-log/ | grep -c '\.yaml$') entries"; done
>   59cb3c1  214 commits  94 entries
>   6c58725  219 commits  96 entries
>   4f3f4ce  222 commits  98 entries      <-- MY TARGET
>   main     225 commits  99 entries
> ```
> * dispatch: *"`67 violation(s)` over **96** entries examined"* -> **98 at `4f3f4ce`.** `96` is the
>   figure at `6c58725`, three commits earlier.
> * dispatch: *"34 OF `main`'s **208** COMMITS"* -> **222 at `4f3f4ce`.** `208` predates even
>   `59cb3c1`.
> * The *violation* counts (67, 34, 27) survive re-measurement unchanged and I confirm them.
>
> **This is `T7` — the mechanism the dispatch itself names as unswept — occurring inside the
> dispatch that names it, in the one section that claims to be freshly measured.** The Project Lead
> disclosed the inheritance of the **lane** figures three times and did not apply the same test to
> the **main** figures it believed it had just measured. **The denominators travelled; only the
> numerators were re-run.** The materiality is low (no verdict turns on it) and the class is exactly
> the one that has now been found by accident three times in two days.

## B.9 `CD-PL-F134` RECURRED UNDER ME — AND THE THING THAT MADE IT SAFE IS NOT THE THING THE RECORD CREDITS

`main` moved **twice** while I was reading, both after my start (`date -u` -> `2026-08-23T14:53:14Z`):
```
git -C /srv/crash-detector log --format='%H %cd %s' --date=iso-strict 4f3f4ce..main
  1699f03  2026-08-23T15:52:31+01:00  CD-DISPATCH-WO2R3-ASSURANCE-09 ISSUED ...
  96ce27e  2026-08-23T15:58:53+01:00  BL-20260823T145640Z-0143 ...
  b3e9825  2026-08-23T15:59:38+01:00  CD-RULE-007 follow-up ...
```
Files touched: `governance/dispatch/…-09.yaml`, `governance/engineering/build-log/BL-…-0143.yaml`,
`governance/engineering/ACTIVE_WORK.yaml`. **All three are inside the write scope the dispatch
promised. The promise was kept.** `BL-0143` pre-declares the move, gives the risk argument
(`PBG-CONT-002` vs `CD-PL-F134`), and concedes in advance that a finding would be upheld.

> **FINDING `CD-ASR-WO2R3-06-F07` — LOW, AND IT IS A CORRECTION OF THE REASONING, NOT OF THE ACT.**
> `BL-0143` credits `CD-PL-F134`'s **second remedy branch** — *"the seat should be told the range in
> advance"* — for making this safe. **That is not what made it safe.** Being told is words; what
> actually held is a **mechanism**: my two targets are **detached pinned worktrees**, so they could
> not move whatever `main` did, and I measured that they did not:
> ```
> git -C /srv/crash-detector-wo2r3-audit9 rev-parse HEAD -> be0b355…  porcelain 0   (start AND end)
> git -C /srv/crash-detector-audit9-main  rev-parse HEAD -> 4f3f4ce…  porcelain 0   (start AND end)
> diff /tmp/cd-asr-wo2r3-06/dispatch-at-start.yaml <live dispatch>   -> rc=0
> ```
> `CD-RULE-006` requires a residue declaration to **name a layer MEASURED to hold it**. The layer
> that held `CD-PL-F134` at this gate is **the pinned worktree**, and it is measurable, and nobody
> wrote it down. `BL-0143`'s own residue paragraph says the carrier is *"NOT PROVED TO BE CARRIED
> ANYWHERE"* — **it under-reports its own strongest control.** The right correction is not more
> prose: it is to record the pinned worktree as the carrier and then note that **nothing forces the
> next dispatch to use one.**
>
> The act itself I grade **acceptable and well-reasoned**. The unavailability of the first remedy
> branch is real: continuity bookkeeping for a dispatch cannot close before the dispatch exists.

## B.10 *** `T5` — DO THE NINE INSTRUMENTS AGREE WITH THE AUTHORITY THEY GUARD? ***
### *** ANSWER: `CD-PL-F153` IS NOT THE EXCEPTION. IT IS THE PATTERN. ***

The dispatch named this *"probably the highest-yield target at this gate"* and it was right.
**Every finding below I reproduced myself, with both arms where a refusal is claimed (`CD-D-079`).**

### *** `CD-ASR-WO2R3-06-F08` — CRITICAL. `check_scope_disjoint.py` IS BLIND TO THE EXACT INCIDENT THAT CAUSED INCREMENT 12. ***

```
tools/coordination/check_scope_disjoint.py:96-100
            sa, sb = a.get("seat_actor_id"), b.get("seat_actor_id")
            if sa == sb:
                lines.append("note     seat=%s holds two claims (%s, %s) — not a cross-seat pair, "
                             "not examined" % (sa, a.get("task_id"), b.get("task_id")))
                continue
```
**BOTH ARMS, MEASURED, ONE VARIABLE — the seat id, and nothing else:**
```
# ARM 1: two live claims, ONE seat id, IDENTICAL write_scope governance/engineering/ACTIVE_WORK.yaml
python3 -B tools/coordination/check_scope_disjoint.py --root .
   note     seat=PROJECT_LEAD_SEAT_01 holds two claims (PL-A, PL-B) — not a cross-seat pair, not examined
   live_claims = 2 ; scope_violations = 0
   VERDICT: ADMITTED — 2 live claim(s), pairwise disjoint. CONCURRENT WORK PROCEEDS.        rc=0

# ARM 2: change PL-B's seat id to PROJECT_LEAD_SEAT_02. Nothing else changes.
   VIOLATION WRITE/WRITE  seat PROJECT_LEAD_SEAT_01 (task PL-A) x seat PROJECT_LEAD_SEAT_02 (task PL-B)
   VERDICT: REFUSED — 1 scope violation(s) among 2 live claim(s)                            rc=1
```

**READ WHAT ARM 1 IS.** Two live sessions, **one identity**, both holding the **same** shared record
file. That is, verbatim, `VERDICT-META-ASSURANCE-01-SECOND-SEAT` §1.1: *"TWO PROJECT LEAD SESSIONS
ALIVE SIMULTANEOUSLY ON `main`, BOTH WITH COMMIT AUTHORITY, **BOTH COMMITTING AS
`PROJECT_LEAD_SEAT_01`**, NEITHER AWARE OF THE OTHER"* — and it is `PO-DECISIONS-0021` ruling 2,
the incident the Product Owner **owned as its own error** and which this entire increment exists to
prevent.

> **THE INSTRUMENT BUILT TO DETECT THE INCIDENT PRINTS `CONCURRENT WORK PROCEEDS` FOR THE INCIDENT,
> AND EXITS 0.** The one property that made the incident invisible — a shared identity — is the exact
> property that switches the check off. **The skip is declared NOWHERE**: not in `L1`-`L6`, not in
> `CD-CT-003`, not in `required-tests.yaml`. `CD-RULE-004` prohibits precisely this — *"a guard that
> catches a chosen instance while its register entry claims the class."*
> **This is `GUARD_THE_INSTANCE_NOT_THE_CLASS` at the exact centre of the remedy.**

### `CD-ASR-WO2R3-06-F09` — HIGH. `check_lease_held.py` CAN BE TURNED GREEN RETROACTIVELY, IN ONE COMMAND, BY THE PARTY IT GRADES.

`--range` grades **historical** writes against leases live **now** (`check_lease_held.py:99`), and
`lease.py`'s `--pid` is unauthenticated. Both arms:
```
python3 -B tools/coordination/check_lease_held.py --root . --range HEAD~2..HEAD --identity PROJECT_LEAD_SEAT_01
  -> VERDICT: REFUSED — 6 governed path(s) not covered by a live lease           rc=1

python3 -B tools/coordination/lease.py --root . acquire --lease RETRO --seat PROJECT_LEAD_SEAT_01 \
        --task ANY --write-scope 'governance/**' --write-scope 'tools/**' --write-scope 'src/**' --pid 1
  -> VERDICT: LEASE ACQUIRED                                                     rc=0

python3 -B tools/coordination/check_lease_held.py --root . --range HEAD~2..HEAD --identity PROJECT_LEAD_SEAT_01
  -> uncovered_governed_paths = 0
  -> VERDICT: ADMITTED — every governed path is covered by a live lease          rc=0
```
**SAME COMMITS. SAME HISTORY. NOTHING REWRITTEN. RED TO GREEN IN ONE COMMAND.** `--pid 1` is `init`,
which is always alive, so the lease is immortal. The contract is named
`CD-CT-009-LEASE-HELD-AT-WRITE`; **`--range` does not measure time-of-write at all.**
This is `CONTROL_BYPASS` and `CAPABILITY_VERSUS_AUTHORITY` in one command.

### `CD-ASR-WO2R3-06-F10` — HIGH. TWO INSTRUMENTS, ONE STATED DOCTRINE, OPPOSITE CODE.

`lease.py:41-43`, its own docstring: *"**A STALE LEASE IS REAPED BY AN EXPLICIT `reap` COMMAND THAT
WRITES WHY. NEVER SILENTLY BY `acquire`.** Silent reaping on acquire is exactly `PLANT-COORD-04` arm
2 — the mutation that reproduces `PO-DECISIONS-0021` ruling 2 on demand."*
Measured:
```
lease.py acquire --lease LDEAD --seat SA --task SHARED --write-scope 'src/**' --pid <exited pid>  -> ACQUIRED
lease.py acquire --lease LNEW  --seat SB --task SHARED --write-scope 'src/**' --pid 1             -> ACQUIRED
grep -E 'lease_id:|task_id:|state:' governance/coordination/leases/*.lease.yaml
  LDEAD  task_id: SHARED  state: CLAIMED
  LNEW   task_id: SHARED  state: CLAIMED
```
**TWO `CLAIMED` LEASES ON ONE TASK AND ONE SCOPE, NO REAP RECORD, NO DISCLOSURE.** It does not
*delete* the stale record, so the letter of the docstring survives; it **admits straight past it**,
which is the effect the docstring forbids and which its own `PLANT-COORD-04` arm 2 exists to
reproduce. Meanwhile `claim.py:195` implements the **opposite** policy in terms: *"a DEAD holder is
still a refusal here."* **Two instruments in one increment, one doctrine, contradictory behaviour.**

### `CD-ASR-WO2R3-06-F11` — HIGH. THE SCOPE ALGEBRA CALLS A DIRECTORY DISJOINT FROM ITS OWN CONTENTS.

```
python3 -c "import sys;sys.path.insert(0,'tools/coordination');import scope as s;print(s.overlaps(['tools/coordination'],['tools/coordination/scope.py'])[0])"
  -> False        # DISJOINT
  overlaps(['a/*'],           ['a/b/c'])                                        -> False
  overlaps(['governance/*'],  ['governance/coordination/ACCOUNTABLE-SEAT.yaml']) -> False
```
The depth rule (`scope.py:299-306`) returns DISJOINT whenever the shorter pattern is non-recursive,
**without asking whether it names a directory.** `claim.py:90` partially compensates by refusing a
bare existing-directory literal — **but only the literal**: the guard is
`if not p.recursive and not any(ch in "".join(p.segments) for ch in "*?[]{}")`, which **exempts every
wildcard form of the same hazard**, and `lease.py` has no such guard at all. So `governance/*` is
accepted on the launch path and is disjoint from everything beneath it.
**This is the mechanism that turns my `F05` (`launch.sh` scope mangling) from an annoyance into a
silent false green: the mangled scope is not merely narrower — it is `DISJOINT FROM ITS OWN SUBTREE`.**

### `CD-ASR-WO2R3-06-F12` — MEDIUM. TWO INSTRUMENTS ARE BLIND TO MERGE COMMITS, AND A MERGE IS WHERE `CD-D-178` PUTS THE POINTER.

`check_no_shared_record_write.py:89` and `check_build_log_pointer_atomic.py:127,137` both read
touched paths with `git show --pretty=format: --name-only <sha>`, which **prints nothing for a merge
commit**. Measured on the increment's own merge:
```
M=6c58725dec4dcd7e918f9b8f4f89b6da963f9c38 ; git cat-file -t $M -> commit
git show --pretty=format: --name-only $M | grep -c .   -> 0
git diff --name-only $M^1 $M | wc -l                   -> 44
```
**The merge that landed increment 12 changed 44 paths and these instruments see zero.** Consequences:
`POINTER_NOT_MOVED` is **structurally unreachable on any merge commit** — and `CD-D-178`'s whole
content is *"the merge commit moves the pointer."* `6c58725` is the textbook `POINTER_NOT_MOVED`
case (`CD-PL-F150`); the instrument reported it under `POINTER_STALE`, **the one class `CD-PL-F153`
proves is a false-positive generator.** It caught the right commit for the wrong reason, and the
record banks that as the instrument's one live catch.

### `CD-ASR-WO2R3-06-F13` — MEDIUM. `assert_atomic_or_refuse` FAILS **OPEN**, INCLUDING ON "UNKNOWN".

`registry.py:67-75` is documented as *"REFUSE rather than assume the atomicity property travels."*
It refuses a **hardcoded nine-element denylist** and proceeds on everything else:
```
REFUSED_FILESYSTEMS = ['9p','afs','ceph','cifs','fuseblk','gfs2','nfs','nfs4','smb2']
  fs_type='UNKNOWN'    -> PROCEEDS      fs_type='vfat'       -> PROCEEDS
  fs_type='exfat'      -> PROCEEDS      fs_type='overlay'    -> PROCEEDS
  fs_type='fuse.sshfs' -> PROCEEDS      fs_type='nfs4'       -> REFUSED
```
`fs_type()` returns the literal string `"UNKNOWN"` when `stat` yields nothing — **the one case where
nothing is established is the case that proceeds.** `CD-RULE-003` is *"derive or fail closed"*;
this derives nothing and fails open. `vfat`/`exfat` are additionally case-insensitive, which
independently invalidates `scope.py`'s case reasoning on the same volume.

### THE T5 TALLY

| # | Instrument | Agrees with its authority? |
|---|---|---|
| 1 | `claim.py` | **NO** — `F04`, scope check is TOCTOU; `L2` states the property unconditionally |
| 2 | `scope.py` | **NO** — `F11`, directory disjoint from its contents; automaton itself is sound |
| 3 | `check_scope_disjoint.py` | **NO** — `F08`, blind to the founding incident, undeclared |
| 4 | `check_build_log_blocks.py` | partially — figures confirmed (`T10`); one-block-per-holder and no `status` handling |
| 5 | `check_build_log_pointer_atomic.py` | **NO** — `CD-PL-F153` (known) + `F12` merge blindness (new) |
| 6 | `check_no_shared_record_write.py` | **NO** — `F12`, merge-blind; prospective and retrospective arms use different comparison |
| 7 | `merge_reconcile.py` | **NO** — its ruler is the claim record the graded seat authored (`EVIDENCE_NOT_INDEPENDENT`) |
| 8 | `lease.py` + `launch.sh` | **NO** — `F05`, `F09`, `F10` |
| 9 | `liveness.py` | **YES** — sound; `F02`'s remedy is genuinely stronger |

> **ONE OF NINE IS CLEAN.** The dispatch's fourth edge — *"A DECLARED LIMIT IS NOT A LICENCE"* — was
> the right test and it does not go far enough: **in `F08`, `F09`, `F10`, `F11`, `F12` and `F13`
> there is no declared limit at all.** The three `CD-RULE-004` places (header, contract, register)
> **agree with each other and disagree with the code.** That is the third thing `CD-RULE-004`
> explicitly prohibits, and it is present six times over.

### `CD-ASR-WO2R3-06-F14` — HIGH. `merge_reconcile.py`'s ONLY LIVE RECORD IS `EVIDENCE_NOT_INDEPENDENT`, AND THE CLAIM POST-DATES THE WORK.

`merge_reconcile.py` assertion 1 (CONTAINMENT) measures touched paths **against the `write_scope`
read out of the claim record** (`:75-82`, `:141`) — a ruler the graded seat authored. Assertion 3
(IDENTITY) compares `%an` against `seat_actor_id` **from that same self-authored record** (`:182`).
Assertion 2 (NON_OVERLAP) compares zero pairs when there is one seat. The single emitted record:
```
governance/coordination/merges/2026-08-23T143221Z-MERGE-INC12-COORDINATION-DISCIPLINE.yaml
git log -1 --format='%an %h' 59cb3c1 -- governance/coordination/claims/  -> CD-ENG-COORD-01 291b26d
git log -1 --format='%an %h' 59cb3c1 -- governance/coordination/merges/  -> CD-ENG-COORD-01 291b26d
```
**The instrument, the ruler, the subject, the verdict and the commit banking it are one seat in one
commit.** `PBG-EVID-001`: *"a manifest that vouches for itself ... is not evidence."*

**AND THE CLAIM DID NOT GATE THE WORK — IT DOCUMENTED IT.** Measured:
```
claimed_utc: 2026-08-23T14:32:21Z
git log --format='%h %aI' 59cb3c1 -10   (converted with date -u)
  e58fc03 14:00:46Z  52051b5 14:05:56Z  47edbcb 14:09:27Z  db1940b 14:12:33Z  d0163ca 14:22:34Z
  d9b20d2 14:23:27Z  99840a4 14:27:25Z  8d4f6e7 14:32:04Z  | 291b26d 14:33:21Z  59cb3c1 14:33:50Z
  -> BEFORE the claim: 8   AFTER the claim: 2
```
**8 of the 10 commits predate their own claim, by up to 32 minutes.** The claim was taken **17
seconds after the eighth commit.** `PO-DECISIONS-0021` ruling 3(a) requires *"a task is atomically
claimed **before it is worked**"*. On the only occasion the registry has ever been used, it was not.
`CD-CT-007`'s `last_run_verdict: LIVE — 3/3 arms contrasted` rests on this record.
*The Engineer disclosed that non-overlap is trivial with one seat. It did not disclose that
containment's ruler is self-declared, or that the claim post-dates the work.*

## B.11 `PART_B` QUESTION 4 — NINE CONTROLS AND ZERO CARRIERS. WHAT IS THAT WORTH?

The dispatch: *"Do not grade it as zero out of reflex and do not grade it as nine."*

Measured, myself:
```
git -C /srv/crash-detector-audit9-main config --get core.hooksPath   -> pbg/tools/hooks
git -C /srv/crash-detector diff --stat 59cb3c1 4f3f4ce -- pbg/       -> (empty; pbg/ untouched, 0 paths)
```
**I grade it at ONE, not nine and not zero, and the one is `liveness.py`.**

The reasoning is not about carriers. It is that **a control's value is capped by its correctness, and
carriage multiplies whatever is there.** Of the nine, one (`liveness.py`) is sound; one
(`check_build_log_blocks.py`) is materially useful and produced `T10`'s confirmed figures; the other
seven each admit or refuse the wrong thing in a way no declared limit covers. **Commissioning these
seven would not have prevented `PO-DECISIONS-0021` ruling 2's incident** — `F08` proves the
disjointness check is blind to it by construction, and `F09` proves the lease check can be made to
agree with anything afterwards.

> **THE ENGINEER'S SENTENCE — "THE CONTROLS EXIST AND NOTHING RUNS THEM" — IS TRUE AND IT IS THE
> SECOND-MOST-SERIOUS THING ABOUT INCREMENT 12.** The most serious is that **if something did run
> them, the founding incident would still pass.** The carrier gap is recoverable in an afternoon;
> `F08`, `F04`, `F09` and `F10` are design corrections. **Fixing the carriage first would ship a
> green board over the original defect — the sixth false green in the Product Owner's own phrase.**

This is a finding **for** the Engineer's honesty on `Q12` and **against** treating carriage as the
remaining work.

---
# CRITERION GRADES

| Criterion | Prior standing | **MY GRADE** | Basis |
|---|---|---|---|
| `CD-AC-002` | AMBER | **AMBER — SUSTAINED, not moved** | PREVENTED tier is real and non-vacuous (`is_exactly`, identity not `==`); suite 1726/0; `CD-RT-012` PASS 68549 assertions; sweep PASS. **No evidence to move it up:** `CD-AC-017` is ruled *"load-bearing ... not one defence among several"* and has **no register row and no implementation**; `CD-ASR-WO2R3-04-F01` is open and no seat claims it closed. |
| `CD-AC-005` | RED | **RED — SUSTAINED, on new and independent grounds** | Sealing count re-derived by me = **ZERO** (99 examined, 51 sealed-against-declared-routes, **87 of 99 forged**, 44 of the 51 forged, 7 vacuous, **0 refused the constructor**). 6 `DEFECT_OPEN` tier-1 sites, 3 `CARRIER_ONLY`, `CD-F-0001`..`0004` all open. **And now `F02`: the RESISTED tier written to answer `F1` is falsified as specified.** |
| `CD-AC-017` | new, 3/4 form | **UNSUPPORTED as a criterion; its SPECIFICATION is REFUTED** | No register row anywhere (`grep CD-AC-017 required-tests.yaml` -> nothing); absent from the product lane entirely; and `F02` defeats the specified discriminator three ways at zero-knowledge cost. **It cannot be verified at WO-3 as written.** |
| `CD-AC-018` | new, 3/4 form | **NOT_EVALUATED — recorded explicitly, never left silent** | Not built; scheduled WO-3/WO-4; no register row. A plan, honestly labelled as one in §16 and **not** in §17. |
| Increment 12 | banked, not accepted | **RED** | `F04`, `F05`, `F08`, `F09`, `F10`, `F11`, `F12`, `F13`, `F14`. |
| Three-tier perimeter | the gate the PO named | **RED** | `F01` (2 of 3 tiers unbuilt), `F02` (the RESISTED sentence false as measured), `F03` (the measurement varied one axis). |

## WHAT I DID NOT EXAMINE, AND WHY — narrowed scope belongs in the verdict, not a footnote

* **The 14 WO-2R3 product plants (`T8`, first half).** I re-applied the **four coordination** plants
  and not the fourteen lane plants. The lane is frozen, unchanged since the eighth gate (verified),
  and the eighth seat applied them. **This is less than dispatched and I say so.** The plant-drift
  carrier `PO-DECISIONS-0017` ruling 1 ordered still does not exist; this is still done by hand.
* **`T14` — `CD-PL-F149`'s 11 unread `ROADMAP.md` mentions.** Not reached.
* **`T13` — `CD-D-174`..`CD-D-180`.** Reached only through their consequences. One thing I did see
  and pass on rather than establish: `CD-D-174` appears to be **minted twice** — once as the Product
  Owner's re-verification obligation (`PO-DECISIONS-0019` ruling 4, LOGGED AND NOT BUILT) and again
  as an increment-12 branch decision now recorded DISCHARGED. **I did not verify this myself and do
  not bank it; I flag it as the `CD-PL-F145` class recurring at the decision layer, where the block
  checker does not look.**
* **`CD-D-105`/Section D scoping (`T11` of the standing invitations).** Not attacked.
* **The `1726/0` suite composition.** I ran it (`1726 passed, rc=0`) and did not audit which tests
  those are. A PASS I cannot account for is a finding **I did not look for**.
* **`pbg/` itself.** Read-only to me and outside my dispatch.

---
# `git log 4f3f4ce..main` — RUN AT THE END, AS ORDERED, AND IT IS **NOT** EMPTY

```
git log --format='%h %an %cI %s' 4f3f4ce..main
b3e9825 PROJECT_LEAD_SEAT_01 2026-08-23T15:59:38+01:00  CD-RULE-007 follow-up — continuity_record_commit resolved to 96ce27e ...
96ce27e PROJECT_LEAD_SEAT_01 2026-08-23T15:58:53+01:00  BL-20260823T145640Z-0143 — THE NINTH FRESH ASSURANCE SEAT IS ISSUED AND OUT ...
1699f03 PROJECT_LEAD_SEAT_01 2026-08-23T15:52:31+01:00  CD-DISPATCH-WO2R3-ASSURANCE-09 ISSUED ...
COUNT=3
   1   1  governance/engineering/ACTIVE_WORK.yaml
  32   3  governance/engineering/ACTIVE_WORK.yaml
 109   0  governance/engineering/build-log/BL-20260823T145640Z-0143.yaml
 335   0  governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-09.yaml
```
**THREE COMMITS. FOUR FILE-WRITES. ALL THREE INSIDE THE DECLARED WRITE SCOPE**
(`ACTIVE_WORK.yaml` · block `0100`-`0199` · `governance/dispatch/`). **NO INSTRUMENT, NO CONTRACT,
NO PLANT, NO GRADE, NOT ONE BYTE OF EITHER TARGET TREE.** The `returns_to` promise was **kept**.
See `CD-ASR-WO2R3-06-F07` for the one correction I make to how it is reasoned about.

## MY OWN ACCOUNTABILITY (`PBG-RT-001` — mutation judged by effect, not by command label)
```
git -C /srv/crash-detector-wo2r3-audit9 rev-parse HEAD -> be0b355…  porcelain 0   (start AND end)
git -C /srv/crash-detector-audit9-main  rev-parse HEAD -> 4f3f4ce…  porcelain 0   (start AND end)
diff /tmp/cd-asr-wo2r3-06/dispatch-at-start.yaml <live dispatch>                  -> rc=0
```
**I mutated neither target.** All probes, races, mutation tests and sandbox clones live under
`/tmp/cd-asr-wo2r3-06/`. **ONE FORCED EXCEPTION, DISCLOSED**: the four authentic plants write into
`/tmp/cd-eng-coord-01/plants/` because `PLANT_SCRATCH` is a bare assignment at `lib.sh:26` and
cannot be overridden from the environment (`CD-PL-F151`; I verified the non-overridability). Each
runner `rm -rf`s its own subdirectory first — **verified, not taken.** I read no other seat's
scratch.

---
# ============================ VERDICT ============================

```
target      TREE 1  be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5  (product, wo-2r3, porcelain 0)
            TREE 2  4f3f4ceed22b089aaf7226e0d73922152cb2819c  (governance + increment 12, main, porcelain 0)

VERDICT     *** RED ***

confidence  HIGH on every finding marked HIGH or CRITICAL. Each was reproduced by me, on the
            authentic target, with a counterfactual arm where a refusal is claimed (CD-D-079).
            MODERATE on F06 and F07, which are material but not gate-moving.
```

**RED ON BOTH HALVES, FOR DIFFERENT REASONS, AND THE SECOND IS THE SERIOUS ONE.**

**PART A — THE PERIMETER IS RED.** Not because it is dishonest — the v0.4.0/v0.4.1 correction is the
most candid document in this record and the Product Owner's retraction was right. It is RED because
**two of its three tiers are unbuilt, and the sentence carrying the middle tier is false as
measured.** The construction-provenance door is defeated by walking in the front door and forging the
value afterwards — on **both** implementations, at **zero-knowledge, zero-package-line** cost,
which is precisely the cost the Blueprint says such a defeat does not have. **The Product Owner's own
reason for the retraction, *"ADMISSION WAS NEVER TESTED"*, was correct. Admission has now been
tested. It does not hold as specified.**

**PART B — INCREMENT 12 IS RED, AND THIS IS THE ONE THAT MATTERS OPERATIONALLY.**
`PO-DECISIONS-0021` ruling 3 states the invariant: **"no two live seats share a TASK or a WRITE
SCOPE."** Measured on the authentic target:

* **The TASK half holds.** `O_EXCL` is atomic and I do not dispute the Engineer's 6400-attempt
  measurement.
* **The WRITE SCOPE half does not.** 193 of 200 concurrent rounds put two seats on one scope (`F04`).
* **The instrument that would detect it is blind to the founding incident by construction** — two
  live claims under **one seat id** on **one scope** return `CONCURRENT WORK PROCEEDS`, rc=0
  (`F08`). That is `PO-DECISIONS-0021` ruling 2's incident **exactly**.
* **The launch binding corrupts its own input** and silently records a scope disjoint from the
  subtree the operator asked for (`F05` + `F11`).
* **The lease check can be turned from REFUSED to ADMITTED over unchanged history by one command**
  (`F09`).
* **The only live use of the registry post-dates 8 of the 10 commits it governs, and its verdict was
  written, run, ruled and banked by one seat in one commit** (`F14`).

**One of the nine instruments — `liveness.py` — agrees with the authority it guards.**

## CONTINUATION IMPLICATION — stated separately, because what is TRUE and what is SAFE are different calculations

**THE SYSTEM IS SAFE TO LEAVE RUNNING. I concur with the standing position and re-derive it rather
than inherit it:** every product finding requires an actor **already executing in-process**; nothing
is remotely reachable; the detector is **ADVISORY (`D1`)** and **no money moves on it (`D2`)**;
`be0b355` is frozen and unchanged. **The WO-2 gate stays SHUT and nothing I found opens it.**

**AND ONE THING IS NOT SAFE, AND IT IS THE NEXT THING IN THE SEQUENCE.**
`PO-DECISIONS-0021` ruling 6 orders: *"increment 12 -> the NINTH gate -> **parallel disjoint
remediation where scopes allow, which is faster and now safe.**"*

> *** **"NOW SAFE" IS NOT ESTABLISHED AND MY MEASUREMENTS ARE AGAINST IT. PARALLEL DISJOINT
> REMEDIATION MUST NOT PROCEED ON THIS MACHINERY.** *** Two seats launched concurrently on one scope
> will both be admitted (`F04`), under one identity will not be detected (`F08`), through
> `launch.sh` will hold leases that are disjoint from the subtree they meant (`F05`+`F11`), and the
> after-the-fact check will agree with whoever runs it last (`F09`). **Running parallel seats on
> this machinery is more dangerous than running them on nothing, because the board would be green.**
> Sequential single-seat operation — what the project does today — remains safe.

## NEXT SAFE GATE

**THE NEXT SAFE GATE IS A PRODUCT OWNER RULING, AND NOT AN ENGINEER DISPATCH.** Three of these are
reserved to the Product Authority and none is mine to decide (`PBG-AUTH-003`):

1. **`PO` ruling on the `RESISTED` tier given `F02`/`F03`.** `CD-AC-017` is ruled *"load-bearing"*.
   Its specified mechanism is refuted. Either the specification changes before WO-3 or `CD-AC-017`
   is scheduled to fail. **This is Blueprint text and `CD-D-115` protects it from every seat.**
2. **`PO` ruling on `Q16`** — `CD-RULE-002` is Product-Authority-sourced and **non-relaxable**, and
   `F03` is **confirmed** by two independent methods (27 / 34 / `44c5ef5`). No seat may rule on it.
3. **`PO` ruling on ruling 6's sequence**, given that *"now safe"* is refuted.

**THEN, AND ONLY THEN, a bounded remediation dispatch — SEQUENTIAL, SINGLE-SEAT — in this order,
because the order is load-bearing:**

| # | Fix | Why first |
|---|---|---|
| 1 | `F08` same-seat skip in `check_scope_disjoint.py` | it is 4 lines and it is the founding incident |
| 2 | `F04` TOCTOU — take the claim file first, validate scope after, release on conflict | correctness before carriage |
| 3 | `F05` quote `$LEASE_ARGS` (use `"$@"`), and `F11` directory-vs-contents in `scope.py` | they compound into a silent false green |
| 4 | `F09`/`F10` `--range` semantics and the dead-holder policy split | a control that can be argued with is not a control |
| 5 | `F12` `git show` -> `git diff <sha>^1 <sha>` in both merge-blind instruments | `CD-D-178` puts the pointer on a merge |
| 6 | `F13` invert `REFUSED_FILESYSTEMS` to an allowlist | `CD-RULE-003`, derive or fail closed |
| 7 | **ONLY THEN** the carriage (`Q11`/`Q12`) | **carrying these controls today would ship a green board over the original defect** |

**AND THE ONE THING THAT MUST NOT HAPPEN: no seat should fix these and also certify them
(`PBG-SOD-001`, `PBG-SOD-004`). A tenth Assurance seat, fresh, re-runs the race in `race_scope.py`
and the both-arms test in `F08` against the repaired tree. Those two commands are the gate.**

## ONE LAST THING, AND IT IS NOT A FINDING

Increment 12 was built in **33 minutes** by a fresh seat that raised **seven findings against its own
work**, including one that its own instrument caught it committing (`F07`), predicted its own
violation in advance and did not exempt itself (`F01`). The plants' third arm defeated every attempt
I made to fake it. **That is not the conduct of a seat papering anything over.** The defects I found
are the defects of a control system built quickly and never raced. **Nothing in this verdict should
be read as a finding against the Engineer's honesty, and the Project Lead's four findings against
itself and its pre-declaration at `BL-0143` are the same species. THE RECORD ON THIS PROJECT IS
UNUSUALLY TRUTHFUL. THAT IS EXACTLY WHY THE MEASUREMENTS ABOVE ARE WORTH TAKING SERIOUSLY.**

```
CD-ASR-WO2R3-06        finished 2026-08-23T15:15:24Z   (date -u +%FT%TZ)
```
