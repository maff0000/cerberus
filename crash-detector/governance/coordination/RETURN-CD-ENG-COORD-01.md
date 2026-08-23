# RETURN — `CD-ENG-COORD-01`, INCREMENT 12, THE COORDINATION DISCIPLINE

**`PBG-CONT-007`: a sub-agent result that exists only in conversation is not project state.** This
file is the record. It is committed on `inc12-coordination` and it is what survives losing the
context that produced it.

**I BUILD; I DO NOT GRADE (`PBG-SOD-001`, non-waivable).** Nothing here is a verdict.

| | |
|---|---|
| seat | `CD-ENG-COORD-01` — FRESH, none of `CD-ENG-WO2R3-01..09`, none of the Assurance/meta seats |
| dispatch | `CD-DISPATCH-INC12-COORDINATION-ENGINEER` |
| authority | `PO-DECISIONS-0021`, commit `e6f9802`, authored by Matt Scott and by NO seat |
| baseline | `e6f980252854d6a79efaf42d4fddb998f19d8540` (`git rev-parse` + `git cat-file -t` -> `commit`) |
| branch | `inc12-coordination`, worktree `/srv/crash-detector-inc12` |
| return | **`READY_FOR_ASSURANCE`** |
| build log | `BL-20260823T142725Z-0300` — block `0300`-`0399` per `CD-D-175`, bounded at both ends |

---

# 1. THE THREE-ARM RESULT TABLE — ALL FOUR PLANTS, EVERY COMMAND, EVERY `rc`

**`CD-PL-F131`, MECHANISED.** `lib.sh`'s `run_rc` runs each command WITH NO PIPE and captures `$?`
on the very next line. Reading an exit code from the end of a pipeline recorded a failing vacuity
arm as PASSING on this project and then recurred in the Project Lead's own shell two hours later.
Nothing below reads an rc through a pipe.

**`CD-PL-F98`: every probe prints the tree it ran in.** Each plant clones the source worktree into
`/tmp/cd-eng-coord-01/plants/<name>/tree` — **this seat's scratch and no other seat's
(`CD-PL-F128`)** — and prints the source worktree, the source HEAD, the sandbox path and the
sandbox HEAD before any arm runs. **THE SANDBOX IS A CLONE, SO IT CARRIES THE COMMITTED TREE AND
NOT THE WORKING TREE** (`CD-RULE-008`'s principle: the working tree is not the record). The real
worktree is never mutated by a plant.

## Summary

| plant | proposition | arms | verdict |
|---|---|---|---|
| `PLANT-COORD-01` | a second claim on a claimed task is refused, by `O_EXCL` and not check-then-write | 3/3 | **LIVE** |
| `PLANT-COORD-02` | overlapping scopes refused, disjoint admitted, write-vs-READ refused | 4/4 | **LIVE** |
| `PLANT-COORD-03` | a merge touching one artefact twice is refused; disjoint merges integrate | 3/3 | **LIVE** |
| `PLANT-COORD-04` | an overlapping launch never starts; a disjoint launch runs alongside | 3/3 | **LIVE** |

**13 OF 13 ARMS CONTRASTED. NO ARM WAS DECLARED `NOT-A-CONTRAST`.**

**AND THREE OF THEM FAILED FIRST**, which is the part worth reading — see section 5.

## Raw arm output, as executed

```
### PLANT-COORD-01
  ARM 1 — BASELINE REFUSES (control INTACT)
    $ python3 -B $SANDBOX/tools/coordination/claim.py --root $SANDBOX claim --task P01-TASK --seat P01-SEAT-A --write-scope src/alpha/**
    rc=0   [arm1 first claim (must succeed)]
    $ python3 -B $SANDBOX/tools/coordination/claim.py --root $SANDBOX claim --task P01-TASK --seat P01-SEAT-B --write-scope src/beta/**
    rc=1   [arm1 SECOND claim on the SAME task (must be REFUSED)]
  ARM 1  BASELINE REFUSES : CONTRASTED AS REQUIRED (first rc=0, second rc!=0, holder named)
  ARM 2 — VIOLATED ADMITS (O_EXCL replaced by check-then-write)
    $ python3 - $SANDBOX
    rc=0   [arm2a natural race]
      | rounds=12 procs=16 total_wins=13 expected_if_atomic=12
        *** first execution it produced total_wins=13 against expected 12 — a natural
        claimer A rc=0   claimer B rc=0
  ARM 2  VIOLATED ADMITS : CONTRASTED AS REQUIRED (BOTH claimers rc=0 on ONE task)
  ARM 3 — NON-VACUITY: THE DISJOINT CASE IS ADMITTED AND PROCEEDS IN PARALLEL
    concurrent disjoint claim X rc=0   concurrent disjoint claim Y rc=0
    $ python3 -B $SANDBOX/tools/coordination/claim.py --root $SANDBOX list
    rc=0   [arm3 both claims LIVE simultaneously]
    live P01-DISJOINT claims present simultaneously = 2
  ARM 3  NON-VACUITY ADMITS : CONTRASTED AS REQUIRED (both rc=0 AND both live at once)
  ARMS: 3 / 3 contrasted as required

### PLANT-COORD-02
  ARM 1 — BASELINE REFUSES (control INTACT): two live claims, OVERLAPPING write scopes
    $ python3 -B $SANDBOX/tools/coordination/check_scope_disjoint.py --root $SANDBOX
    rc=1   [arm1 check_scope_disjoint over the overlapping pair]
    names seat A=1  seat B=1  overlapping path=1
  ARM 1  BASELINE REFUSES : CONTRASTED AS REQUIRED (rc!=0 and both seats and the path named)
  ARM 2 — VIOLATED ADMITS: overlaps() compares first segment only and fails OPEN
    $ python3 -B $SANDBOX/tools/coordination/check_scope_disjoint.py --root $SANDBOX
    rc=0   [arm2 same registry, MUTATED algebra (undecidable form must fail closed; it will not)]
  ARM 2  VIOLATED ADMITS : CONTRASTED AS REQUIRED (rc=0 where the intact control refuses)
    $ python3 -B $SANDBOX/tools/coordination/check_scope_disjoint.py --root $SANDBOX
    rc=1   [arm2 contrast: intact control on the same registry]
    intact rc=1 (non-zero = fails closed on the undecidable form, as designed)
    two concurrent disjoint claims taken through claim.py: rc=0 and rc=0
    $ python3 -B $SANDBOX/tools/coordination/check_scope_disjoint.py --root $SANDBOX
    rc=0   [arm3a check_scope_disjoint over the disjoint pair]
  ARM 3  NON-VACUITY ADMITS (disjoint) : CONTRASTED AS REQUIRED (both claims taken AND check rc=0)
    $ python3 -B $SANDBOX/tools/coordination/check_scope_disjoint.py --root $SANDBOX
    rc=1   [arm3b check_scope_disjoint: write-vs-READ must be REFUSED]
    refusal cites CD-PL-F134: 1
  ARM 4  ASYMMETRIC WRITE-vs-READ REFUSES : CONTRASTED AS REQUIRED (rc!=0 and CD-PL-F134 cited)
  ARMS: 4 / 4 contrasted as required

### PLANT-COORD-03
    set-up ok: P03-SEAT-A tip 5f89c6fb6bfc659e8ee17c8235cb43b186e30d1c != BASE
    set-up ok: P03-SEAT-B tip f544c3b97a959aed8717a3c8d8d6137a7b7f8105 != BASE
  ARM 1 — BASELINE REFUSES: both seats touched src/shared/contended.txt
    $ python3 -B $SANDBOX/tools/coordination/merge_reconcile.py --root $SANDBOX --base d9b20d26acbb5fbeda5b4f16f379f5ab86e6886f --claim P03-A --claim P03-B --tip P03-A=5f89c6fb6bfc659e8ee17c8235cb43b186e30d1c --tip P03-B=f544c3b97a959aed8717a3c8d8d6137a7b7f8105
    rc=1   [arm1 merge_reconcile over the contended pair]
    names seat A=1 seat B=1 artefact=1
  ARM 1  BASELINE REFUSES : CONTRASTED AS REQUIRED (rc!=0, artefact and both seats named)
  ARM 2 — VIOLATED ADMITS: the pairwise-intersection assertion is dropped
    $ python3 -B $SANDBOX/tools/coordination/merge_reconcile.py --root $SANDBOX --base d9b20d26acbb5fbeda5b4f16f379f5ab86e6886f --claim P03-A --claim P03-B --tip P03-A=5f89c6fb6bfc659e8ee17c8235cb43b186e30d1c --tip P03-B=f544c3b97a959aed8717a3c8d8d6137a7b7f8105
    rc=0   [arm2 merge_reconcile, intersection assertion removed]
    *** WORK SILENTLY LOST BELONGS TO: P03-SEAT-A ***
  ARM 2  VIOLATED ADMITS : CONTRASTED AS REQUIRED (rc=0 AND a named seat's work is lost)
  ARM 3 — NON-VACUITY: DISJOINT TOUCHED-PATH SETS ARE ADMITTED AND BOTH ARE INTEGRATED
    set-up ok: P03-SEAT-X tip 13ff73f9543ba8849e50eeb59e65f78f04db8b05 != BASE
    set-up ok: P03-SEAT-Y tip 0a197d3f8990f77f9d1449a552d93da89ff9e286 != BASE
    $ python3 -B $SANDBOX/tools/coordination/merge_reconcile.py --root $SANDBOX --base d9b20d26acbb5fbeda5b4f16f379f5ab86e6886f --claim P03-X --claim P03-Y --tip P03-X=13ff73f9543ba8849e50eeb59e65f78f04db8b05 --tip P03-Y=0a197d3f8990f77f9d1449a552d93da89ff9e286 --emit
    rc=0   [arm3 merge_reconcile over the DISJOINT pair]
    seat X's change present in the merged result = 1
    seat Y's change present in the merged result = 1
    merge records emitted = 1   (ls governance/coordination/merges/ | wc -l)
  ARM 3  NON-VACUITY ADMITS : CONTRASTED AS REQUIRED (rc=0 AND both seats' changes present AND record emitted)
  ARMS: 3 / 3 contrasted as required

### PLANT-COORD-04
  ARM 1 — BASELINE REFUSES, AND THE SEAT NEVER STARTS
    $ python3 -B $SANDBOX/tools/coordination/lease.py --root $SANDBOX list
    rc=0   [arm1 lease list (the first lease must read LIVE)]
    $ sh $SANDBOX/tools/coordination/launch.sh --lease L-SECOND --seat P04-SEAT-SECOND --task P04-TASK-TWO --write-scope src/contended/module.py -- /tmp/cd-eng-coord-01/plants/PLANT-COORD-04/fake-seat.sh second 2
    rc=1   [arm1 OVERLAPPING second launch (must be REFUSED, must not exec)]
    *** DID THE SECOND SEAT PROCESS START? NO ***
  ARM 1  BASELINE REFUSES + SEAT NEVER STARTS : CONTRASTED AS REQUIRED (rc!=0 AND no sentinel)
  ARM 2 — VIOLATED ADMITS: liveness always returns False (the silent-stale-reap bug)
    $ sh $SANDBOX/tools/coordination/launch.sh --lease L-SECOND --seat P04-SEAT-SECOND --task P04-TASK-TWO --write-scope src/contended/module.py -- /tmp/cd-eng-coord-01/plants/PLANT-COORD-04/fake-seat.sh second 2
    rc=0   [arm2 SAME overlapping launch, mutated liveness]
    second seat STARTED: YES
    *** AND THE FIRST SESSION IS STILL ALIVE: YES (kill -0 1390216) ***
  ARM 2  VIOLATED ADMITS WHILE FIRST IS ALIVE : CONTRASTED AS REQUIRED (rc=0 AND second started AND first alive)
  ARM 3 — NON-VACUITY: A DISJOINT SECOND LAUNCH STARTS AND RUNS ALONGSIDE THE FIRST
    $ sh $SANDBOX/tools/coordination/launch.sh --lease L-DISJOINT --seat P04-SEAT-DISJOINT --task P04-TASK-BRAVO --write-scope docs/bravo/** -- fake-seat second 25   [backgrounded]
    lease acquisition for the disjoint launch: 1 acquired, 0 refused
    disjoint second seat STARTED: YES
    first session STILL ALIVE and UNDISTURBED: YES (kill -0 1390422)
    $ python3 -B $SANDBOX/tools/coordination/lease.py --root $SANDBOX list
    rc=0   [arm3 both leases live at once (BOTH PROCESSES STILL RUNNING)]
    leases reading LIVE simultaneously = 2
  ARM 3  NON-VACUITY: DISJOINT LAUNCHES RUN IN PARALLEL : CONTRASTED AS REQUIRED (admitted AND second started AND first alive AND 2 live leases)
  ARMS: 3 / 3 contrasted as required

```

---

# 2. PER-ITEM: WHAT WAS BUILT AND WHAT WAS NOT

| item | built | **NOT built / declared short** |
|---|---|---|
| **1** work-claim registry | `claim.py` + `registry.py`. A DIRECTORY, one file per claim, `os.open(O_CREAT\|O_EXCL\|O_WRONLY)`; `FileExistsError` **IS** the refusal. `claim` / `release` (holder only) / `list` / `status` / `reap`. Reap is EXPLICIT, writes the reason and the evidence of death into the file, sets `ABANDONED`, deletes nothing. **`claim` NEVER reaps.** | Task-ID SYNONYMY — two names for one job — is **NOT PROVED TO BE CARRIED ANYWHERE**. Work done with no claim at all is invisible to it. |
| **2(a)** scope algebra | `scope.py`. Decides literals, recursive `p/**`, and single-segment `*`/`?` globs by **EXACT product-automaton emptiness**. Fails closed on `**` mid-pattern, character classes, braces. Refuses `..`, absolute paths, empty entries at parse time. Decides case collisions conservatively. 27 unit cases, 0 failures. | Symlink aliasing is not decided textually; it is carried by `check_scope_disjoint.py` **and that hand-off is MEASURED (PLANT-COORD-02 arm 3b), not asserted.** |
| **2(b)** live disjointness | `check_scope_disjoint.py`. Pairwise WRITE×WRITE **and WRITE×READ in both cross-seat directions** (`CD-PL-F134`). | Deliberately does NOT refuse READ×READ — refusing it would ban parallel audits, the exact vacuity ruling 3 rejects. Reads DECLARATIONS, not what was touched. |
| **2(c)** per-seat id blocks | `BUILD-LOG-ID-BLOCKS.yaml` + `check_build_log_blocks.py`: block overlap, out-of-block entry, **and duplicate id** (the third is not in the dispatch and is required by "no shared sequence"). | Cross-branch collisions need two `--ref` values and **nothing runs the two-ref form automatically**. `IMP-023` **NOT CLOSED AND NOT CLAIMED CLOSED** — the register entry does not exist in this repository (`Q13`). |
| **2(d)** no shared record write | `check_no_shared_record_write.py`, **both directions**. Prospective arm called by `claim.py` before every take; retrospective arm over a commit range, identity from the git author. | **CANNOT DISTINGUISH TWO CONCURRENT SESSIONS OF THE SAME ACCOUNTABLE SEAT FROM ONE.** `CD-RULE-002` gives one identity to a ROLE. This is the second meta-assurance seat's §7.2 — the true root cause — and it is **NOT PROVED TO BE CARRIED ANYWHERE**. |
| **2(e)** pointer atomicity | `check_build_log_pointer_atomic.py`, three classes, run backward over real history. | Does not decide whether the entry named is the *right* one; does not decide the other two continuity pointer fields; does not decide SCHEMA validity — **`5f09627` is NOT caught and is named.** |
| **3** merge reconciliation | `merge_reconcile.py`: containment, non-overlap, identity. Emits a record to `governance/coordination/merges/`. | **MEASURES PATHS, NOT BYTES.** Over-refuses disjoint regions of one file. Does not catch bytes written through an undeclared path. **DOES NOT PERFORM THE MERGE AND CANNOT PREVENT ONE.** |
| **4(i)** driver binding | `lease.py` + `launch.sh`. Acquires the lease FIRST and **refuses to `exec`**. Liveness MEASURED. Explicit `reap` only. | **BINDS ONLY LAUNCHES THAT GO THROUGH IT. The operator's wrapper is not in this repository** and nothing goes through `launch.sh` today (`Q12`). |
| **4(ii)** hand binding | `check_lease_held.py` built and working — run over this branch it refuses 31 uncovered governed paths. | *** **NOT PROVED TO BE CARRIED ANYWHERE.** *** See section 4. |
| **5** four plants | Four checked-in `git apply`-able mutation patches + four runners, 13 arms. | **NO PLANT for `CD-CT-004`, `-005`, `-006`, `-009`.** Each contract states why in its §4, and each reason is recorded as **AN ARGUMENT AND NOT A PROOF**. |
| **6** three places | `required-tests.yaml` **CREATED** (measured: `main` at `e6f9802` has run records under `governance/assurance/` and **no register**) + nine execution contracts. Every row `closes_class: false`. | Nothing verifies that the three places actually agree. A fourth instrument could; it was not built. |

---

# 3. ITEM 2(e) — THE BACKWARD RUN. **DERIVED, NOT COPIED.**

```
python3 -B tools/coordination/check_build_log_pointer_atomic.py --rev e6f980252854d6a79efaf42d4fddb998f19d8540
rc=1
```

| | at `e6f9802` (my baseline) | at `main` tip `76c1de1` |
|---|---|---|
| commits examined | **204** | 208 |
| applications of the discipline | **93** | 95 |
| violating commits | **9** | 9 |
| `POINTER_NOT_MOVED` | 3 | 3 |
| `POINTER_DANGLING` | 1 | 1 |
| `POINTER_STALE` | 7 | 7 |
| failing positions | **[30, 76, 85, 90, 91, 92]** | [30, 76, 85, 90, 91, 92] |

**The record says: "4 failures in 91 applications at positions 76, 85, 90 and 91."**

**THE RECORD'S FOUR POSITIONS ARE REPRODUCED EXACTLY BY AN INSTRUMENT THAT DID NOT KNOW THEM.** That
is independent corroboration of the record's identification. **THE COUNTS DIFFER AND THE
INSTRUMENT'S NUMBERS ARE OFFERED AS THE FINDING:** 93 applications not 91, 9 violating commits not
4 — because this instrument counts three classes where the record counted the narrower one, and
checks every commit for a broken pointer rather than only commits that added an entry. **TWO
POSITIONS THE RECORD DOES NOT CARRY ARE FOUND: 30 AND 92.**

Violating commits, named:

```
44a56ecdd917  PROJECT_LEAD_SEAT_01   POINTER_DANGLING
8e9456f2592d  PROJECT_LEAD_SEAT_01   POINTER_NOT_MOVED
61e9558e8548  Matt Scott             POINTER_STALE
00ef57e69ae1  PROJECT_LEAD_SEAT_01   POINTER_STALE
a31c79978dfd  PROJECT_LEAD_SEAT_01   POINTER_STALE
cd79952df1d0  PROJECT_LEAD_SEAT_01   POINTER_NOT_MOVED,POINTER_STALE
f401d484bb77  PROJECT_LEAD_SEAT_01   POINTER_STALE
bdf85da5ad89  PROJECT_LEAD_SEAT_01   POINTER_NOT_MOVED,POINTER_STALE
c6ee53e04eca  PROJECT_LEAD_SEAT_01   POINTER_STALE
```

**FOUR OF THE FIVE NAMED `RESUME_BLOCKED` COMMITS ARE CAUGHT** (`a31c799`, `cd79952`, `bdf85da`,
`c6ee53e`). **`5f09627` IS NOT**, and that is declared rather than hidden: its failure was a SCHEMA
violation (`CD-PL-F148`), which this instrument states it does not decide. `pbg boot` is the layer
that catches the fifth and that hand-off is measured, not asserted.

**MY FIRST DRAFT CAUGHT ONLY TWO OF THE FIVE.** It checked `POINTER_NOT_MOVED` and
`POINTER_DANGLING` and missed `a31c799`, `c6ee53e` and `5f09627`, because each of those moved the
pointer to a REAL entry that was no longer the LATEST. `POINTER_STALE` exists because the backward
run disagreed with the record and I chased the disagreement instead of smoothing it. **A
GREEN-LOOKING NEAR-MISS WOULD HAVE SHIPPED.**

**`T23` answered by example:** this instrument sweeps backward, counts, names — **and repairs
nothing and renumbers nothing.** That is the worked example, not the answer; the answer is Product
Authority's.

---

# 4. THE `CD-RULE-006` DECLARATION FOR ITEM 4(ii), IN ITS REQUIRED WORDS

> *** **`tools/coordination/check_lease_held.py` IS NOT PROVED TO BE CARRIED ANYWHERE.** ***

Not "carried by the pre-commit hook". Not "carried by the Project Lead's boundary discipline". Not
"carried by the dispatch". **NOWHERE.** Nothing in this repository invokes it automatically.

**THE MEASUREMENT BEHIND THE WORDS, TAKEN BY THIS SEAT AND NOT READ FROM THE DISPATCH:**

```
git config core.hooksPath
rc=0
-> pbg/tools/hooks

grep -n "governance/authority" pbg/tools/hooks/pre-commit
rc=0
-> 44:STAGED=$(git diff --cached --name-only --diff-filter=ACMR | grep '^governance/authority/' || true)
```

followed by `[ -n "$STAGED" ] || exit 0`. The one automatic pre-write carrier in this repository
greps one directory and waves everything else through, and `pbg/` is pinned read-only to every seat
(`PBG-FWK-013`).

**I DID NOT EDIT `pbg/`.** `git status` shows zero modifications under `pbg/` on this branch.
Extending that hook would have been editing the framework to make a control pass — a bypass, not a
fix. The dispatch disclosed the trap in advance and I did not walk into it.

**SO DELIVERABLE 3(d) LANDS HALF-CARRIED BY CONSTRUCTION.** The driver half is real machinery whose
refusal-to-`exec` is proved by a sentinel file in `PLANT-COORD-04` arm 1. The hand half is a check
nothing runs. **IT MUST NOT BE READ AS A BINDING.** `Q11` / `Q12`, and neither is mine to close.

The check does work when invoked, and here is it run against my own branch:

```
python3 -B tools/coordination/check_lease_held.py --range e6f9802..HEAD --identity CD-ENG-COORD-01
rc=1
governed_paths = 31
uncovered_governed_paths = 31
live_leases = 0
VERDICT: REFUSED — 31 governed path(s) not covered by a live lease held by 'CD-ENG-COORD-01'
```

**I WROTE 31 GOVERNED PATHS WITHOUT HOLDING A LEASE AND NOTHING STOPPED ME.** That is the honest
demonstration of the gap, and it is a better one than any plant.

---

# 5. EVERY FINDING I RAISE — INCLUDING AGAINST THIS DISPATCH AND AGAINST MY OWN WORK

## `CD-ENG-COORD-01-F01` — HIGH — **AGAINST THE DELIVERABLES AS RULED**

**ITEM 2(d) AND ITEM 2(e) ARE JOINTLY UNSATISFIABLE FOR ANY SEAT THAT IS NOT THE ACCOUNTABLE SEAT,
AND THIS INCREMENT IS THE PROOF.**

* ITEM 2(d) refuses a non-accountable seat's write to `governance/engineering/ACTIVE_WORK.yaml`.
* ITEM 2(e) refuses any commit that ADDS a build-log entry without moving `last_build_log_entry` in
  `ACTIVE_WORK.yaml` **in that same commit**.

My dispatch requires me to write a Build Log entry in block `0300`-`0399`, and forbids me
`ACTIVE_WORK.yaml`. **SO THE COMMIT CARRYING MY OWN BUILD LOG ENTRY VIOLATES MY OWN ITEM 2(e) CHECK,
BY CONSTRUCTION, AND THERE IS NO COMPLIANT ACTION AVAILABLE TO ME.**

This is not a bug in either instrument. Both do exactly what ruling 3(b) and `CD-PL-F132` ask. **THE
RULING'S OWN DELIVERABLE (b) — "its OWN record files ... no shared `ACTIVE_WORK.yaml` edit" —
IMPLIES THAT `CD-PL-F132`'S ONE-SHARED-POINTER RULE CANNOT SURVIVE UNCHANGED INTO A PARALLEL
WORLD.** Three resolutions exist and **NONE IS MINE TO CHOOSE** (`PBG-AUTH-005`):

1. the pointer rule binds the accountable seat's branch only, and seat branches are checked at merge;
2. each seat gets its own continuity pointer file and the accountable seat's points at the merge;
3. the pointer check exempts commits authored by a non-accountable seat.

**I BUILT NEITHER A WORKAROUND NOR AN EXEMPTION.** I wrote the entry, I did not touch
`ACTIVE_WORK.yaml`, and I am reporting that the check refuses my own commit. **A SILENT EXEMPTION
WOULD HAVE BEEN THE `CD-PL-F132` SHAPE ARRIVING INSIDE ITS OWN FIX.**

## `CD-ENG-COORD-01-F02` — MEDIUM — **AGAINST THIS DISPATCH, ITEM 4**

The dispatch specifies: *"Liveness is `/proc/<pid>` **plus a cmdline match**"*.

**BUILT LITERALLY, IT DECLARES EVERY SUCCESSFULLY LAUNCHED SEAT DEAD ONE MOMENT AFTER IT STARTS.**
`launch.sh` acquires the lease and then `exec`s the seat; `exec` keeps the process and **replaces
its command line**. The fingerprint recorded at acquire time never matches the cmdline a moment
later. `PLANT-COORD-04` arms 1 and 3 both failed on it, and the measured evidence is in the record:

```
Liveness(live=False, reason='CMDLINE_MISMATCH', ...
  "/proc/1384381/cmdline = 'sleep 30', record says 'sh .../launch.sh --lease L-DBG ...'")
```

**THAT IS `CD-PL-F143`'S EXACT FAILURE MODE — A SEAT DECLARED DEAD WHILE IT WAS ALIVE — BUILT INTO
THE CONTROL.** A lease that declares its own holder dead the instant the launch succeeds is not
conservative; it is inoperative, and worse, it silently permits the overlapping second launch.

**THE DISPATCH'S INTENT IS HONOURED BY A STRICTLY STRONGER TEST.** Its stated reason is "a bare PID
check is wrong the moment the OS recycles the number". `/proc/<pid>/stat` field 22 — process start
time — answers that better than a cmdline match: a recycled PID **cannot** reproduce the original
start time, whereas a recycled PID running a similar wrapper **can** reproduce a cmdline prefix. So
start time is authoritative where recorded, cmdline drift is RECORDED rather than treated as death,
and records lacking a start time fall back to cmdline and report `degraded=True`.

I obeyed intent over letter and said why, which is what the dispatch asked for.

## `CD-ENG-COORD-01-F03` — HIGH — **AGAINST THE RECORD, `CD-RULE-002` (PRODUCT AUTHORITY, NON-RELAXABLE)**

**AGENT-SEAT WORK PRODUCTS ARE COMMITTED UNDER A HUMAN IDENTITY, AT SCALE, LONG AFTER THE RULE
FORBADE IT.**

```
for f in $(git ls-tree --name-only main governance/engineering/build-log/); do
    git log --diff-filter=A --format='%an' main -- "$f" | tail -1; done | sort | uniq -c
rc=0
->  68 PROJECT_LEAD_SEAT_01
->  27 Matt Scott
```

**27 Build Log entries on `main` were added by commits authored `Matt Scott`** — including the
thirteen consecutive Project Lead boundary entries **`0111` through `0123`**, every one of them
committed on 2026-08-23.

```
python3 -B tools/coordination/check_no_shared_record_write.py --range <root>..e6f9802
rc=1
commits_examined = 203
shared_record_violations = 34        # all 34 author='Matt Scott'
```

**34 of `main`'s 203 commits wrote `governance/engineering/ACTIVE_WORK.yaml` under that identity.**
By commit date: 2 on 08-18, 14 on 08-19, 2 on 08-20, **16 today**. `CD-RULE-002` took effect
2026-08-19, so **32 of the 34 post-date it.**

And the sharpest instance:

```
git log --diff-filter=A --format='%H|%an <%ae>|%cn <%ce>' main -- .../BL-20260823T065550Z-0123.yaml
rc=0
-> 44c5ef5...|Matt Scott <rogue@cerberus.local>|NoustAI-PDA <pda@noustai.com>
```

**BOTH OF THOSE ARE THE IDENTITIES `CD-RULE-002` NAMES VERBATIM AS ITS OWN MEASURED FAILURE
(`CD-PL-F56`)**, appearing four days after the rule took effect.

`CD-RULE-002`'s stated enforcement is *"the Project Lead runs a **git log author audit at every
boundary** — every commit on the lane must resolve to a seat identity from the table above, and none
to a human. An audit that finds a human identity is **a boundary failure, not a cosmetic one**."*
Either that audit was not run over these, or it was run and did not catch them.

**THE NARROW SCOPE OF THIS FINDING, STATED SO IT IS NOT OVER-READ:** the Product Owner authoring
`governance/decisions/PO-DECISIONS-*.md` under his own name is CORRECT and this finding does not
touch it — `PO-DECISIONS-0021` at `e6f9802` is authored by Matt Scott and by no seat, exactly as it
should be. **THIS FINDING IS ABOUT AGENT-SEAT WORK PRODUCTS — BOUNDARY BUILD LOG ENTRIES AND
`ACTIVE_WORK.yaml` — CARRYING A HUMAN'S NAME.**

**A CAVEAT I OWE:** `git log --diff-filter=A ... | tail -1` attributes an entry to the OLDEST commit
that added that path on that ref. A cherry-pick or a re-add would re-attribute. I verified three
entries directly against `git log` and they agreed; I did not verify all 27.

## `CD-ENG-COORD-01-F04` — MEDIUM — **AGAINST THE DISPATCH'S STATED ALLOCATION, ITEM 2(c)**

The dispatch states `0200`-`0299` is "the WO-2R3 lane" and told me to verify each allocation myself.
Verifying found: **`0200`-`0299` IS ENTIRELY UNUSED — ZERO ENTRIES ON EITHER BRANCH.** The lane's
actually-exhausted block is `0060`-`0099` (40/40 present on `wo-2r3`, 0 on `main`). Not a defect in
the allocation — a defect in its description, and it is the kind that gets copied forward.

## `CD-ENG-COORD-01-F05` — MEDIUM — **AGAINST THE EXISTING RECORD, "no shared sequence"**

**15 BUILD LOG ID NUMBERS ARE CARRIED BY MORE THAN ONE DISTINCT ENTRY.** 14 across `main`/`wo-2r3`
and the duplicate `0136` inside `main` alone. Derived twice by independent methods that agreed
(a `comm`-based derivation gave 18 shared ids minus 4 shared filenames = 14; the instrument gave 15
including the within-`main` duplicate). **NOT REPAIRED, NOT RENUMBERED, DISCLOSED** — `PBG-CONT-003`
is non-waivable and the declared stop is not triggered.

## `CD-ENG-COORD-01-F06` — LOW — **CONTINUITY, AGAINST MY OWN BASELINE**

**`e6f9802` DOES NOT CONTAIN MY OWN DISPATCH, NOR `BL-...-0139` WHICH ISSUED ME.** Both arrived at
`82c8f06`, after the baseline the dispatch names. **AN ASSURANCE SEAT CLONING THIS BRANCH ALONE
CANNOT READ THE AUTHORITY FOR THE WORK IT IS GRADING.**

The dispatch file itself was verified **unchanged** since I read it:

```
git show main:governance/dispatch/CD-DISPATCH-INC12-COORDINATION-ENGINEER.yaml | sha256sum
-> 58536e2af0a89195e139f6d45211e0cd5db81450048b74e0a1df7cc22c7fe9f4
sha256sum /srv/crash-detector/governance/dispatch/CD-DISPATCH-INC12-COORDINATION-ENGINEER.yaml
-> 58536e2af0a89195e139f6d45211e0cd5db81450048b74e0a1df7cc22c7fe9f4
diff <committed> <on-disk>
rc=0
```

**MY CONTRACT WAS NOT REWRITTEN UNDER ME.**

## `CD-ENG-COORD-01-F07` — INFORMATIONAL — **AGAINST MY OWN PRACTICE**

I committed two smoke-test claim records (`DEMO-A`, `DEMO-D`) into
`governance/coordination/claims/` in my first commit. They were cloned into a plant sandbox and
`PLANT-COORD-01` arm 3 reported `DID NOT CONTRAST`. **THE INSTRUMENT WAS RIGHT AND MY PLANT WAS
WRONG** — it was correctly refusing a genuine scope overlap against a live claim. Removed in a later
commit; plants now clear the sandbox registry and **disclose in their own output that they do**.

---

# 6. THE THREE TIMES MY OWN WORK FAILED FIRST — BECAUSE THIS IS THE EVIDENCE THAT THE ARMS ARE REAL

**A PLANT THAT PASSES ON THE FIRST RUN OF EVERY ARM IS A PLANT NOBODY SHOULD TRUST.** Mine did not.

1. **`PLANT-COORD-01` arm 3 failed** — cause: my own committed smoke-test claims. Instrument right,
   plant wrong. (`F07`)
2. **`PLANT-COORD-02` arm 2 failed** — my mutation neutralised only the `a`-side undecidable branch,
   so the fail-open regression did not actually take effect. The mutation was rebuilt.
3. **`PLANT-COORD-03` arm 1 failed** — seat B's `printf` silently failed (the checkout had removed
   the directory), its commit never happened, and **the arm passed on an EMPTY diff.** I added
   `assert_tip_moved`, which exits 3 with `THIS PLANT IS NOT EVIDENCE` rather than measuring nothing.
4. **`PLANT-COORD-04` arms 1 and 3 failed** — and that one was a real defect in the shipped
   instrument, not in the plant. It became `F02`.

**AND ONE MORE, WHICH IS THE ONE I WOULD MOST WANT AN AUDITOR TO SEE:** the scope algebra
contradicted two of my own hand-written test expectations (`BL-*-03??.yaml` vs `BL-*-02??.yaml`, and
`x*y` vs `y*x`). **THE AUTOMATON WAS RIGHT BOTH TIMES AND I WAS WRONG.** Both cases are retained in
`test_scope.py` with the corrected expectation and a note saying so.

Also honestly reported: **`PLANT-COORD-01` arm 2a is NON-DETERMINISTIC.** The unwidened TOCTOU race
produced `total_wins=13` against an expected 12 on its first execution — a natural double-take with
no artificial sleep — and `12/12` on later runs. **THE WINDOW IS REACHABLE UNAIDED BUT NOT RELIABLY,
WHICH IS PRECISELY WHY A RACE DEFECT SURVIVES TESTING.** 2a is not the arm's pass criterion; the
widened, deterministic 2b is.

---

# 7. RECONCILING `CD-D-177` — THE PROJECT LEAD'S OWN DECLARED SCOPE

`CD-D-177` declared, before I launched, that the Project Lead would write only
`ACTIVE_WORK.yaml`, its own `0100`-`0199` block, and `governance/dispatch/`, and would "touch no
path in the Engineer's scope". It also recorded its own weakness: **a declaration is exactly what
ruling 4 calls "a prediction, not a carrier"**, and told me to raise it if breached.

**MEASURED:**

```
git rev-parse main    ->  76c1de1f7d7a20d47e5d19ec933c4e38c77c89e5   (cat-file -t -> commit)
git rev-list --count e6f9802..main   ->  4
git diff --name-only e6f9802..main
->  governance/dispatch/CD-DISPATCH-INC12-COORDINATION-ENGINEER.yaml
    governance/engineering/ACTIVE_WORK.yaml
    governance/engineering/build-log/BL-20260823T134132Z-0139.yaml
    governance/engineering/build-log/BL-20260823T135313Z-0140.yaml
```

All four commits authored `PROJECT_LEAD_SEAT_01`. **`main` DID MOVE WHILE I WAS LIVE — AND EVERY
PATH IS INSIDE THE DECLARED SCOPE AND NOT ONE IS IN MINE. `CD-D-177` HELD. `CD-PL-F134` DID NOT
HAPPEN A THIRD TIME**, and I say so as plainly as I would have said the opposite.

**ONE THING WORTH A DECISION RATHER THAN A GOOD OUTCOME:** `CD-D-177` places
`governance/dispatch/` in the Project Lead's *live* write scope, and my own contract lives there.
The same dispatch says *"NOBODY REWRITES A LIVE CONTRACT, IN EITHER DIRECTION."* **THE AUTHORITY TO
DO THE FORBIDDEN THING WAS DECLARED, EVEN THOUGH THE THING WAS NOT DONE.** That is worth closing by
ruling, not by the next seat also happening to behave.

---

# 8. WHAT I WAS MOST SUSPICIOUS OF, AS INSTRUCTED

The dispatch told me it was written by the seat whose practice was graded `RED` twice, about the fix
for its own defect, and asked whether any item is *"a restatement of the problem dressed as a
control"*.

**MY ANSWER: NO — WITH ONE EXCEPTION AND ONE STRUCTURAL LIMIT, BOTH ALREADY NAMED IN THE DISPATCH
ITSELF.**

* ITEMS 1, 2(a)-(e), 3 and 4(i) are **executables that refuse**, and each one is proved to refuse by
  a mutation that makes it stop refusing. None is a rule, a comment or a checklist. Ruling 4's
  standard — *"a comment, a rule, a checklist or a dispatch paragraph is not a deliverable; an
  executable that refuses is"* — is met by those items.
* **ITEM 4(ii) IS THE EXCEPTION, AND THE DISPATCH SAID SO BEFORE I STARTED.** It is a check nothing
  invokes. It is not dressed as a binding, in the instrument, in the register row, or in the
  contract, and the required words are written in all three places.
* **THE STRUCTURAL LIMIT IS THIS, AND IT IS THE ONE I WOULD PUT IN FRONT OF THE PRODUCT OWNER:**
  **NOT ONE OF THE NINE INSTRUMENTS IS INVOKED BY ANYTHING.** Every one runs when a seat decides to
  run it. The second meta-assurance seat's §7.3 named exactly this as *"the whole lesson of this
  docket"*: *"wherever it lives, it must be executed by something that is not a seat deciding to
  execute it."* **INCREMENT 12 BUILDS NINE CONTROLS AND ZERO CARRIERS**, because the only automatic
  carrier in this repository is inside `pbg/` and no seat may touch it. The machinery is real and it
  is unwired. **THAT IS `Q11`, IT NEEDS A BOUNDED FRAMEWORK DISPATCH FROM THE HUMAN, AND UNTIL IT
  LANDS THE HONEST DESCRIPTION OF THIS INCREMENT IS "THE CONTROLS EXIST AND NOTHING RUNS THEM."**

I do not think that makes increment 12 a restatement of the problem. A control that exists and is
unwired is strictly more than a paragraph, and every one of these can be run by an Assurance seat
today over real data. But it is one step short of what ruling 4 asks for, and the gap has a name, an
owner and a reason — which is better than the alternative on this project's record.
