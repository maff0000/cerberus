#!/bin/sh
# ================================================================================================= #
# PLANT-COORD-06 — **THE WRITE-SCOPE HALF OF THE CLAIM, RACED.** `CD-ASR-WO2R3-06-F04`.
#
# `PO-DECISIONS-0021` ruling 3(a) states the invariant as *"no two live seats share a TASK **or a
# WRITE SCOPE**"*. Increment 12 delivered the TASK conjunct with `O_EXCL` and MEASURED it — 6400
# concurrent attempts, 200 rounds, 0 double-takes — and then delivered the WRITE SCOPE conjunct with
# a directory read followed fifty lines later by the write. **THE ONE PREDICATE THE WHOLE INCREMENT
# EXISTS TO ENFORCE WAS THE ONE PREDICATE NEVER RACED**, and when the ninth Assurance seat finally
# raced it, 193 of 200 rounds put TWO SEATS ON ONE WRITE SCOPE, both `VERDICT: CLAIMED`, both rc=0.
#
#   ARM 1  BASELINE REFUSES — N rounds of TWO CONCURRENT CLAIMANTS, DIFFERENT task ids, IDENTICAL
#                             write scope. **EXACTLY ONE WINNER EVERY ROUND. ZERO DOUBLE-TAKES.**
#   ARM 2  VIOLATED ADMITS  — ONE named mutation: the `flock` call inside `registry.critical_section`
#                             is replaced by `pass`, so the mutex is never taken and check-then-take
#                             is a TOCTOU window again. **THE DOUBLE-TAKES COME BACK**, and the bad
#                             state is DEMONSTRATED ON DISK: two claim files, two different seats,
#                             one write scope — and the increment's own detector called to say so.
#   ARM 3  NON-VACUITY      — TWO CONCURRENT CLAIMANTS ON **DISJOINT** SCOPES. **BOTH WIN. BOTH
#                             RECORDS ARE LIVE AT ONCE.** *** A DESIGN THAT SERIALISED ALL CLAIMS
#                             THROUGH ONE GLOBAL LOCK WOULD PASS ARM 1 AND FAIL THE INCREMENT: the
#                             invariant is NON-OVERLAP, NOT one-writer-at-a-time. THIS ARM IS THE
#                             ONE THAT TELLS THOSE TWO DESIGNS APART. ***
# ================================================================================================= #
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${PLANT_SCRATCH:=/tmp/cd-eng-coord-fix-01/plants}"
: "${SOURCE_ROOT:=/srv/crash-detector-inc13}"
export PLANT_SCRATCH SOURCE_ROOT
. "$HERE/lib.sh"
plant_banner "PLANT-COORD-06"
PATCH="$HERE/PLANT-COORD-06.mutation.patch"
ROUNDS="${ROUNDS:-40}"
mkdir -p "$SANDBOX/src/contended" "$SANDBOX/src/alpha" "$SANDBOX/src/bravo"

# ------------------------------------------------------------------------------------------------
# THE RACER. Two concurrent `claim.py` processes, started from a process pool so that they overlap.
# It prints ONLY counts and the verbatim first double-take, and it makes no judgement.
#
# `CD-PL-F131`: no exit code is read from the end of a pipeline anywhere in this file.
# ------------------------------------------------------------------------------------------------
cat > "$PLANT_WORK/race.py" <<'PYEOF'
import multiprocessing as mp, os, subprocess, sys, glob

TREE = sys.argv[1]
ROUNDS = int(sys.argv[2])
SCOPE_A = sys.argv[3]
SCOPE_B = sys.argv[4]
CLAIMS = os.path.join(TREE, "governance/coordination/claims")
CLAIM_PY = os.path.join(TREE, "tools/coordination/claim.py")

def claimer(args):
    task, seat, scope = args
    r = subprocess.run(
        [sys.executable, "-B", CLAIM_PY, "--root", TREE, "claim",
         "--task", task, "--seat", seat, "--write-scope", scope,
         "--block", "0400-0499", "--dispatch", "PLANT-COORD-06"],
        capture_output=True, text=True)
    verdict = [l for l in r.stdout.splitlines() if l.startswith("VERDICT")]
    return (task, r.returncode, verdict[0] if verdict else "(no VERDICT line)")

def round_once(n):
    for f in glob.glob(os.path.join(CLAIMS, "*.claim.yaml")):
        os.unlink(f)
    jobs = [(f"P06-{n}-A", "SEAT-ALPHA", SCOPE_A), (f"P06-{n}-B", "SEAT-BRAVO", SCOPE_B)]
    with mp.Pool(2) as pool:
        res = pool.map(claimer, jobs)
    return [t for (t, rc, _) in res if rc == 0], res

if __name__ == "__main__":
    two = one = zero = 0
    first_two = None
    for n in range(ROUNDS):
        wins, res = round_once(n)
        if len(wins) == 2:
            two += 1
            if first_two is None:
                first_two = res
        elif len(wins) == 1:
            one += 1
        else:
            zero += 1
    print(f"ROUNDS={ROUNDS} concurrency=2 scope_A={SCOPE_A!r} scope_B={SCOPE_B!r}")
    print(f"  exactly-one-winner : {one}")
    print(f"  ZERO winners       : {zero}")
    print(f"  TWO WINNERS        : {two}")
    if first_two:
        print("  first two-winner round, verbatim:")
        for t, rc, line in first_two:
            print(f"      task={t} rc={rc}  {line}")
    print(f"  RESULT_ONE={one} RESULT_ZERO={zero} RESULT_TWO={two}")
PYEOF

# ------------------------------------------------------------------------------------------------
echo "  ARM 1 — BASELINE REFUSES: $ROUNDS ROUNDS, TWO CONCURRENT CLAIMANTS, ONE WRITE SCOPE"
# ------------------------------------------------------------------------------------------------
run_rc "arm1 identical write scope, different task ids" \
    python3 -B "$PLANT_WORK/race.py" "$SANDBOX" "$ROUNDS" 'src/contended/**' 'src/contended/**'
show_out 10
A1_TWO=$(echo "$LAST_OUT"  | sed -n 's/.*RESULT_TWO=\([0-9]*\).*/\1/p')
A1_ONE=$(echo "$LAST_OUT"  | sed -n 's/.*RESULT_ONE=\([0-9]*\).*/\1/p')
echo "    double-takes = $A1_TWO   exactly-one-winner = $A1_ONE   (of $ROUNDS rounds)"
A1_OK=0
[ "$LAST_RC" -eq 0 ] && [ "$A1_TWO" = "0" ] && [ "$A1_ONE" = "$ROUNDS" ] && A1_OK=1
arm_result 1 "ZERO DOUBLE-TAKES ON ONE WRITE SCOPE" "two=0 AND one=$ROUNDS" "$A1_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 2 — VIOLATED ADMITS: the flock inside registry.critical_section becomes \`pass\`"
# ------------------------------------------------------------------------------------------------
apply_mutation "$PATCH"
if [ $? -ne 0 ]; then
    arm_result 2 "VIOLATED ADMITS" "mutation must apply" 0
    A2_OK=0
else
    run_rc "arm2 THE SAME RACE, with the mutex not taken" \
        python3 -B "$PLANT_WORK/race.py" "$SANDBOX" "$ROUNDS" 'src/contended/**' 'src/contended/**'
    show_out 12
    A2_TWO=$(echo "$LAST_OUT" | sed -n 's/.*RESULT_TWO=\([0-9]*\).*/\1/p')
    echo "    double-takes = $A2_TWO  of $ROUNDS rounds"
    echo "    *** AND THE BAD STATE IS DEMONSTRATED ON DISK, NOT ASSERTED: ***"
    ls -1 "$SANDBOX"/governance/coordination/claims/*.claim.yaml 2>/dev/null | sed 's/^/      | /'
    echo "      claim records on disk = $(ls -1 "$SANDBOX"/governance/coordination/claims/*.claim.yaml 2>/dev/null | wc -l)"
    echo "        produced by: ls -1 <sandbox>/governance/coordination/claims/*.claim.yaml | wc -l"
    grep -H 'seat_actor_id\|^- src' "$SANDBOX"/governance/coordination/claims/*.claim.yaml 2>/dev/null | sed 's#.*/claims/#      | #'
    run_rc "arm2 the increment's OWN detector, on the state the race produced" \
        python3 -B "$SANDBOX/tools/coordination/check_scope_disjoint.py" --root "$SANDBOX"
    echo "$LAST_OUT" | grep -E 'VIOLATION|VERDICT' | sed 's/^/      | /'
    DETECTED=$LAST_RC
    echo "    detector rc=$DETECTED (1 = it calls this state a violation)"
    A2_OK=0
    [ "$A2_TWO" != "0" ] && [ "$DETECTED" -eq 1 ] && A2_OK=1
    arm_result 2 "MUTEX REMOVED -> DOUBLE-TAKES RETURN" "two>0 AND detector refuses" "$A2_OK"
    revert_mutation "$PATCH"
fi

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3 — NON-VACUITY: TWO CONCURRENT CLAIMANTS ON **DISJOINT** SCOPES MUST **BOTH** WIN."
echo "          THIS IS THE ARM THAT TELLS A NON-OVERLAP CONTROL APART FROM A SERIALISING ONE."
# ------------------------------------------------------------------------------------------------
run_rc "arm3 DISJOINT write scopes, raced concurrently" \
    python3 -B "$PLANT_WORK/race.py" "$SANDBOX" "$ROUNDS" 'src/alpha/**' 'src/bravo/**'
show_out 8
A3_TWO=$(echo "$LAST_OUT" | sed -n 's/.*RESULT_TWO=\([0-9]*\).*/\1/p')
A3_ONE=$(echo "$LAST_OUT" | sed -n 's/.*RESULT_ONE=\([0-9]*\).*/\1/p')
echo "    BOTH-WON rounds = $A3_TWO   only-one-won rounds = $A3_ONE   (of $ROUNDS)"
echo "    *** IF THIS NUMBER WERE NOT $ROUNDS, THE FIX WOULD HAVE BANNED CONCURRENCY AND THE ITEM"
echo "    *** WOULD BE FAILED, NOT CONSERVATIVE. ***"
echo "    and both records are live SIMULTANEOUSLY, from the registry's own mouth:"
run_rc "arm3 the two disjoint claims, both live" \
    python3 -B "$SANDBOX/tools/coordination/check_scope_disjoint.py" --root "$SANDBOX"
echo "$LAST_OUT" | grep -E 'ok  |VERDICT' | sed 's/^/      | /'
BOTH_LIVE=$LAST_RC
A3_OK=0
[ "$A3_TWO" = "$ROUNDS" ] && [ "$A3_ONE" = "0" ] && [ "$BOTH_LIVE" -eq 0 ] && A3_OK=1
arm_result 3 "DISJOINT CLAIMS ARE STILL TAKEN CONCURRENTLY" "both won in all $ROUNDS rounds" "$A3_OK"

plant_summary
exit $?
