# EV-SCOPE-RACE-MEASUREMENT — THE WRITE-SCOPE CONJUNCT, RACED

> **Produced by `CD-ENG-COORD-FIX-01` at increment 13, under `CD-DISPATCH-INC13-COORDINATION-FIX-ENGINEER`.**
>
> **THIS IS AN ENGINEER'S OWN MEASUREMENT AND IT IS NOT ASSURANCE** (`PBG-SOD-001`, non-waivable).
> It records commands and their verbatim output. **IT DECLARES NO PASS.** The tenth Assurance seat
> runs the acceptance command itself and grades it; this seat does not and may not.

---

## 1. WHY THIS FILE EXISTS AND WHAT ITS SIBLING DOES NOT COVER

`governance/coordination/evidence/EV-ATOMICITY-MEASUREMENT.md` measures `os.open(O_CREAT|O_EXCL)`
on ONE PATH: 6400 attempts, 200 rounds, 0 double-takes. **THAT MEASURES TASK-ID COLLISION AND IT IS
SOUND.** `CD-ASR-WO2R3-06` named its limit exactly: *"it raced the SYSCALL, not the INSTRUMENT"*.

`PO-DECISIONS-0021` ruling 3 states the invariant with two conjuncts: *"no two live seats share a
TASK **or a WRITE SCOPE**"*. `O_EXCL` excludes on the FILENAME and the filename is the TASK ID. Two
seats with DIFFERENT task ids and IDENTICAL write scopes take DIFFERENT filenames, **so `O_EXCL`
never fires and never could**. Between them stood a directory read (the scope check) and, fifty
lines later, the write — a TOCTOU window.

**THE ONE PREDICATE THE WHOLE INCREMENT EXISTS TO ENFORCE WAS THE ONE PREDICATE NEVER RACED.**

---

## 2. THE HARNESS — THE NINTH ASSURANCE SEAT'S OWN, NOT THIS SEAT'S

`governance/assurance/WO-2R3/evidence/CD-ASR-WO2R3-06/race_scope.py`, banked verbatim by the
Project Lead at `480da0f`.

```
sha256sum governance/assurance/WO-2R3/evidence/CD-ASR-WO2R3-06/race_scope.py
13800ffaa1722f4b02fb1a4fbac100865f885d9f897431502a5b03c9ad84b5e5
```

That is byte-for-byte the value recorded in the increment-13 dispatch. **THE BANKED COPY WAS NOT
EDITED BY THIS SEAT**, and `git status` over it in `/srv/crash-detector` is empty. It was CLONED to
this seat's scratch and exactly ONE line was re-pointed, which the dispatch permits in terms:

```
diff <banked> /tmp/cd-eng-coord-fix-01/race/race_scope.py
20c20
< TREE = "/tmp/cd-asr-wo2r3-06/race/tree"
---
> TREE = "/tmp/cd-eng-coord-fix-01/race/tree"
```

**NO ASSERTION, NO ROUND COUNT, NO CONCURRENCY AND NO SCOPE WAS CHANGED.** The harness's own
invariant is unaltered: *"of two concurrent claimants on THE SAME write scope, AT MOST ONE is
CLAIMED"*.

---

## 3. ARM 1 — THE FIXED TREE

```
$ cd /tmp/cd-eng-coord-fix-01/race && python3 race_scope.py 200
ROUNDS=200  concurrency=2  DIFFERENT task_ids, IDENTICAL write_scope='src/contended/**'
  exactly-one-winner (CORRECT) : 200
  ZERO winners                 : 0
  *** TWO WINNERS (DOUBLE-TAKE ON ONE SCOPE) *** : 0
```

Sandbox: a `git clone --no-hardlinks` of `/srv/crash-detector-inc13` at
`112410bb4cea564d9db4405f2510c4cd33800ef0`.

## 4. ARM 2 — THE COUNTERFACTUAL. **THE SAME HARNESS, THE UNFIXED BASELINE.**

**AN ACCEPTANCE COMMAND THAT PASSES PROVES NOTHING UNTIL IT IS SHOWN THAT IT CAN FAIL**
(`PBG-ASSURE-017`, `CD-D-079`). Same machine, same harness, same scope, same round count; the only
variable is the tree.

```
$ git clone --no-hardlinks /srv/crash-detector-inc13 <tree> && git -C <tree> checkout 480da0f...
$ python3 race_scope.py 200     # against 480da0f, THE DISPATCHED BASELINE, UNFIXED
ROUNDS=200  concurrency=2  DIFFERENT task_ids, IDENTICAL write_scope='src/contended/**'
  exactly-one-winner (CORRECT) : 6
  ZERO winners                 : 0
  *** TWO WINNERS (DOUBLE-TAKE ON ONE SCOPE) *** : 194
  first double-take, verbatim:
      task=RACE-0-A rc=0  [TREE] worktree=... head=480da0f49bb265ce782004c5d925febb94314c56 ...
      task=RACE-0-B rc=0  [TREE] worktree=... head=480da0f49bb265ce782004c5d925febb94314c56 ...
```

**194 OF 200 ROUNDS. THE NINTH ASSURANCE SEAT MEASURED 193 OF 200 ON THE SAME CODE.** The two
numbers are the same measurement of the same defect on a machine whose scheduling is not identical
between runs, and the small difference is reported rather than rounded to match.

**SO THE HARNESS IS NOT VACUOUS AND THE FIX IS WHAT CHANGED THE NUMBER: 194 -> 0.**

---

## 5. WHAT THE FIX IS, AND WHAT IT DELIBERATELY IS NOT

`registry.critical_section` — `fcntl.flock(LOCK_EX|LOCK_NB)` on `<registry-dir>/.registry.lock`,
with a 30s deadline after which it **RAISES and the caller REFUSES**.

**IT IS A MUTEX AROUND THE DECISION AND NOT AROUND THE WORK.** The payload — including both `git`
subprocesses — is built BEFORE the section is entered. Inside it there is a directory read, a pure
python scope decision and one `O_EXCL` create, and nothing that blocks. It is released before the
command returns.

**`flock` AND NOT AN `O_EXCL` LOCK FILE, FOR A MEASURED REASON.** A lock file leaks: a seat killed
by the operator's wrapper — which has happened on this project, and an entire Assurance audit
ceased to exist — leaves the file behind, every later claim deadlocks against a corpse, somebody
adds a stale-lock timeout, and **the timeout is the hole**. `flock` is released by the kernel when
the descriptor closes, including on `SIGKILL`. No stale state, so no reaping policy to get wrong.

### 5.1 THE TRAP THIS MEASUREMENT DOES NOT BY ITSELF ESCAPE

*** **A DESIGN THAT SERIALISED ALL CLAIMS THROUGH ONE GLOBAL LOCK WOULD PRODUCE SECTION 3'S NUMBERS
EXACTLY AND WOULD FAIL THE INCREMENT.** *** The invariant is NON-OVERLAP, not one-writer-at-a-time.
`race_scope.py` cannot tell the two designs apart, because every round it runs is an OVERLAPPING
pair. **SO THE NON-VACUITY ARM IS NOT OPTIONAL AND IT IS NOT IN THIS HARNESS:**

```
$ sh governance/coordination/plants/PLANT-COORD-06.run.sh      # ARM 3
ROUNDS=40 concurrency=2 scope_A='src/alpha/**' scope_B='src/bravo/**'
  exactly-one-winner : 0
  ZERO winners       : 0
  TWO WINNERS        : 40
    BOTH-WON rounds = 40   only-one-won rounds = 0   (of 40)
  VERDICT: ADMITTED — 2 live claim(s), pairwise disjoint. CONCURRENT WORK PROCEEDS.
```

**40 ROUNDS, TWO CONCURRENT CLAIMANTS ON DISJOINT SCOPES, BOTH WON EVERY TIME**, and the
increment's own detector confirms both records are live simultaneously. A serialising design scores
0 here. **READ SECTIONS 3 AND 5.1 TOGETHER OR NEITHER OF THEM MEANS WHAT IT APPEARS TO.**

---

## 6. THE SAME WINDOW IN `lease.py`, WHICH THE FINDING DID NOT NAME

`F04` was raised against `claim.py`. `lease.py` read every live lease and wrote its own record
afterwards, in the identical shape, with `O_EXCL` excluding only on the LEASE ID. **FIXING ONLY THE
INSTRUMENT THE FINDING NAMED WOULD BE `GUARD_THE_INSTANCE_NOT_THE_CLASS` (`CD-RULE-004`) — the
exact anti-pattern this increment exists to remove.** The class is fixed; it is declared here, in
`lease.py`'s own limit block, in `CD-CT-008`, in the register row and in the Build Log, and it is
**NOT** claimed as one of the five ordered items.

---

## 7. LIMITS OF THIS MEASUREMENT — READ BEFORE CREDITING IT

* **CONCURRENCY 2, ON ONE MACHINE, ON `ext2/ext3`.** `stat -f -c %T` on the claims directory
  returns `ext2/ext3`. `flock` carries the same network-filesystem caveat as `O_EXCL` and is
  covered by the same refusal (`assert_atomic_or_refuse` runs before the section is entered), but
  **NEITHER IS MEASURED ON A NETWORK FILESYSTEM HERE AND NEITHER IS CLAIMED TO HOLD THERE.**
* **`flock` IS ADVISORY.** It binds every process that goes through these instruments and NOTHING
  ELSE. A hand-written claim file defeats it exactly as it always defeated the registry.
* **200 ROUNDS IS NOT A PROOF.** It is 200 rounds. The window is now closed by construction rather
  than by timing, and that argument — not this count — is what should be attacked.
* **NOTHING RUNS ANY OF THIS AUTOMATICALLY.** `Q11`, routed to the framework with its priority
  inverted (`PO-DECISIONS-0022` ruling 4). **NOT PROVED TO BE CARRIED ANYWHERE.**
