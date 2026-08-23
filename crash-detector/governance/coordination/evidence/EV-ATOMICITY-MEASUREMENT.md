# EV-ATOMICITY-MEASUREMENT — is `O_CREAT|O_EXCL` actually atomic on THIS filesystem?

**Seat:** `CD-ENG-COORD-01` · **taken:** `2026-08-23T13:51:03Z` (`date -u +%FT%TZ`, `CD-RULE-005`)
**Tree:** `/srv/crash-detector-inc12`, branch `inc12-coordination`, head
`e6f980252854d6a79efaf42d4fddb998f19d8540` (`git rev-parse HEAD`; `git cat-file -t` -> `commit`).

## Why this file exists

`CD-DISPATCH-INC12-COORDINATION-ENGINEER` carries a DECLARED STOP:

> **IF THE ATOMIC CLAIM CANNOT BE MADE ATOMIC ON THIS FILESYSTEM** (measure it — `stat -f -c %T .`
> and an actual concurrent race, not an assumption) — stop and return the measurement. **A registry
> whose atomicity is assumed is worse than none.**

The whole of ITEM 1 rests on one property of one syscall. **Every escape on this project's record
passed a static checker.** So it was raced, not read about.

## 1. The filesystem

```
stat -f -c %T /srv/crash-detector-inc12
```

-> `ext2/ext3`   (`statfs` magic name; the mount is ext4, which reports under this name)

## 2. The race — 32 concurrent processes, 200 independent rounds

Probe (`/tmp/cd-eng-coord-01/fsprobe/race.py`, this seat's own scratch and no other seat's):

```python
def worker(args):
    path, n = args
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.write(fd, str(n).encode()); os.close(fd); return 1
    except FileExistsError:
        return 0
```

Each round: a **fresh path**, a `multiprocessing.Pool` of 32 **separate processes** all calling
`os.open` on that one path. A win is a return of 1. The invariant under test is
`total_successes == rounds` — exactly one winner per path, never two.

```
python3 /tmp/cd-eng-coord-01/fsprobe/race.py /srv/crash-detector-inc12/.tmp-fsprobe 32 200
rc=$?
```

**Result, verbatim:**

```
rounds=200 procs_per_round=32 total_successes=200 expected=200
EXCL_RACE_rc=0
```

* attempts = **6400** (`200 rounds x 32 processes`)
* wins = **200**
* double-takes = **0**

## 3. Verdict

**`O_CREAT|O_EXCL` IS ATOMIC ON THIS FILESYSTEM AT THIS SHA. THE DECLARED STOP IS NOT TRIGGERED.**

## 4. What this measurement does NOT establish — read this before citing it

1. **It is a measurement of THIS filesystem.** `O_EXCL` is documented as not atomic over NFS
   before NFSv3. `registry.assert_atomic_or_refuse()` therefore **re-measures `stat -f -c %T` on
   every single run** and REFUSES on a network filesystem rather than carrying this result forward
   as a property of the code. The measurement does not travel; the re-measurement does.
2. **6400 attempts is not a proof.** A race that fails one time in ten million would not appear
   here. What this rules out is a *broken* implementation, not a *rare* one. The claim made is
   "measured atomic at this scale", and no stronger claim is made anywhere in the increment.
3. **It says nothing about a claim file edited by hand,** or deleted, or written by a process that
   never used this registry. The filesystem is the lock only for actors that ask it for the lock.
4. **It says nothing about two seats doing the same work under two different task ids.** That is
   the registry's declared residue (`CD-RULE-006`) and it is stated in `claim.py`'s limit block.

## 5. A separate measurement taken at the same time — case sensitivity

`tools/coordination/scope.py` fails closed on case collisions on the assumption that a
case-insensitive filesystem may exist. Measured rather than assumed:

```
python3 -c "import os; open('/tmp/cd-eng-coord-01/CaSeProbe','w').close(); print(os.path.exists('/tmp/cd-eng-coord-01/caseprobe'))"
```

-> `False`. **This host is case-SENSITIVE.** The `CASE_COLLISION` refusal is therefore
*conservative here* — it refuses a pair that this filesystem would in fact keep distinct. That is
the fail-closed direction and it is recorded as a deliberate cost, not as a discovered property:
a scope declaration is a portable governance artefact and the next host is not measured.
