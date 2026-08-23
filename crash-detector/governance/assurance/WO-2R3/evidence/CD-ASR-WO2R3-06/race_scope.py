"""
CD-ASR-WO2R3-06 / T6 + PART_B(2) — DOES THE CLAIM REGISTRY ACTUALLY DELIVER WHAT
PO-DECISIONS-0021 RULING 3(a) ASKS FOR?

The Engineer raced `os.open(O_CREAT|O_EXCL)` on ONE PATH: 6400 attempts, 200 wins, 0 double-takes.
That measures TASK-ID collision. It does NOT measure SCOPE collision.

claim.py cmd_claim:
    line 135-158   read every live claim, test scope overlap, refuse if it overlaps   <-- CHECK
    line 187       registry.write_exclusive(path, payload)                            <-- USE

Two seats with DIFFERENT task_ids and OVERLAPPING write scopes take DIFFERENT filenames, so O_EXCL
never fires. The only thing standing between them is the read at 135 and the write at 187 — a
TOCTOU window. THIS RACES THAT WINDOW.

INVARIANT UNDER TEST: of two concurrent claimants on THE SAME write scope, AT MOST ONE is CLAIMED.
"""
import multiprocessing as mp, os, subprocess, sys, shutil, glob

TREE = "/tmp/cd-asr-wo2r3-06/race/tree"
CLAIMS = os.path.join(TREE, "governance/coordination/claims")
CLAIM_PY = os.path.join(TREE, "tools/coordination/claim.py")
SCOPE = "src/contended/**"

def claimer(args):
    task, seat, barrier_unused = args
    r = subprocess.run(
        [sys.executable, "-B", CLAIM_PY, "--root", TREE, "claim",
         "--task", task, "--seat", seat,
         "--write-scope", SCOPE, "--block", "0900-0999", "--dispatch", "RACE"],
        capture_output=True, text=True)
    return (task, r.returncode, r.stdout.strip().splitlines()[0] if r.stdout.strip() else "")

def round_once(n):
    for f in glob.glob(os.path.join(CLAIMS, "*.claim.yaml")):
        os.unlink(f)
    jobs = [(f"RACE-{n}-A", "SEAT-ALPHA", None), (f"RACE-{n}-B", "SEAT-BRAVO", None)]
    with mp.Pool(2) as pool:
        res = pool.map(claimer, jobs)
    wins = [t for (t, rc, _) in res if rc == 0]
    return wins, res

if __name__ == "__main__":
    ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    double = 0
    zero = 0
    one = 0
    first_double = None
    for n in range(ROUNDS):
        wins, res = round_once(n)
        if len(wins) == 2:
            double += 1
            if first_double is None:
                first_double = res
        elif len(wins) == 1:
            one += 1
        else:
            zero += 1
    print(f"ROUNDS={ROUNDS}  concurrency=2  DIFFERENT task_ids, IDENTICAL write_scope={SCOPE!r}")
    print(f"  exactly-one-winner (CORRECT) : {one}")
    print(f"  ZERO winners                 : {zero}")
    print(f"  *** TWO WINNERS (DOUBLE-TAKE ON ONE SCOPE) *** : {double}")
    if first_double:
        print("  first double-take, verbatim:")
        for t, rc, line in first_double:
            print(f"      task={t} rc={rc}  {line}")
