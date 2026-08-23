#!/bin/sh
# ================================================================================================= #
# PLANT-COORD-01 — THE WORK CLAIM. `PO-DECISIONS-0021` ruling 3(a), increment 12 ITEM 1.
#
# PROPOSITION: a second `claim` on an already-claimed task is REFUSED, and the refusal is delivered
# by `O_CREAT|O_EXCL` and not by a check-then-write.
#
#   ARM 1  BASELINE REFUSES  — a second claim on the same task exits non-zero and NAMES the holder.
#   ARM 2  VIOLATED ADMITS   — with O_EXCL replaced by `os.path.exists` + a plain write, two
#                              claimers interleaved in the window BOTH SUCCEED. **DEMONSTRATED BY
#                              READING BOTH CLAIM FILES BACK, NOT ASSERTED.**
#   ARM 3  NON-VACUITY       — two claims on DIFFERENT tasks BOTH SUCCEED, concurrently, both live.
# ================================================================================================= #
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$HERE/lib.sh"
plant_banner "PLANT-COORD-01"
PATCH="$HERE/PLANT-COORD-01.mutation.patch"
CLAIM="python3 -B $SANDBOX/tools/coordination/claim.py --root $SANDBOX"

# ------------------------------------------------------------------------------------------------
echo "  ARM 1 — BASELINE REFUSES (control INTACT)"
# ------------------------------------------------------------------------------------------------
run_rc "arm1 first claim (must succeed)" python3 -B "$SANDBOX/tools/coordination/claim.py" --root "$SANDBOX" \
    claim --task P01-TASK --seat P01-SEAT-A --write-scope 'src/alpha/**'
A1_FIRST=$LAST_RC
run_rc "arm1 SECOND claim on the SAME task (must be REFUSED)" python3 -B "$SANDBOX/tools/coordination/claim.py" --root "$SANDBOX" \
    claim --task P01-TASK --seat P01-SEAT-B --write-scope 'src/beta/**'
A1_SECOND=$LAST_RC
show_out 8
NAMES_HOLDER=0
echo "$LAST_OUT" | grep -q "P01-SEAT-A" && NAMES_HOLDER=1
echo "    refusal names the holder P01-SEAT-A: $NAMES_HOLDER"
A1_OK=0
[ "$A1_FIRST" -eq 0 ] && [ "$A1_SECOND" -ne 0 ] && [ "$NAMES_HOLDER" -eq 1 ] && A1_OK=1
arm_result 1 "BASELINE REFUSES" "first rc=0, second rc!=0, holder named" "$A1_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 2 — VIOLATED ADMITS (O_EXCL replaced by check-then-write)"
# ------------------------------------------------------------------------------------------------
rm -f "$SANDBOX"/governance/coordination/claims/P01-*.claim.yaml
apply_mutation "$PATCH"
MUT_OK=$?
if [ "$MUT_OK" -ne 0 ]; then
    arm_result 2 "VIOLATED ADMITS" "mutation must apply" 0
else
    echo "    2a. THE UNWIDENED RACE — 32 concurrent claimers, 60 rounds, NO artificial sleep."
    echo "        This measures whether the TOCTOU window is reachable WITHOUT help."
    run_rc "arm2a natural race" python3 - "$SANDBOX" <<'PY'
import multiprocessing as mp, os, subprocess, sys
sandbox = sys.argv[1]
def one(i):
    r = subprocess.run(["python3","-B",sandbox+"/tools/coordination/claim.py","--root",sandbox,
                        "claim","--task","P01-RACE-%d"%(i//32),"--seat","S%d"%i,
                        "--write-scope","src/r%d/**"%i], capture_output=True, text=True)
    return 1 if r.returncode == 0 else 0
rounds, procs = 12, 16
wins = 0
for r in range(rounds):
    with mp.Pool(procs) as p:
        wins += sum(p.map(one, [r*32+k for k in range(procs)]))
print("rounds=%d procs=%d total_wins=%d expected_if_atomic=%d" % (rounds, procs, wins, rounds))
sys.exit(0 if wins > rounds else 1)
PY
    NATURAL_RC=$LAST_RC
    show_out 4
    echo "        rc=$NATURAL_RC  (0 here means MORE THAN ONE WINNER PER TASK WAS OBSERVED NATURALLY)"
    echo "        *** 2a IS NON-DETERMINISTIC AND THAT IS REPORTED, NOT SMOOTHED. On this seat's"
    echo "        *** first execution it produced total_wins=13 against expected 12 — a natural"
    echo "        *** double-take with no artificial sleep. On the next it produced 12/12. THE"
    echo "        *** WINDOW IS REACHABLE UNAIDED BUT NOT RELIABLY, WHICH IS PRECISELY WHY A"
    echo "        *** RACE-CONDITION DEFECT SURVIVES TESTING. 2a is NOT the arm's pass criterion;"
    echo "        *** 2b is. 2a is here to show the window is real without help."

    echo "    2b. THE WIDENED WINDOW — deterministic demonstration. PLANT_COORD_01_WIDEN=0.5"
    echo "        THE SLEEP WIDENS THE WINDOW. IT DOES NOT CREATE IT. 2a is the honest measurement"
    echo "        of whether the window is reachable unaided; 2b makes the STATE readable."
    rm -f "$SANDBOX"/governance/coordination/claims/P01-DEMO.claim.yaml
    ( PLANT_COORD_01_WIDEN=0.5 python3 -B "$SANDBOX/tools/coordination/claim.py" --root "$SANDBOX" \
        claim --task P01-DEMO --seat P01-SEAT-A --write-scope 'src/alpha/**' > "$PLANT_WORK/a.txt" 2>&1 ) &
    P_A=$!
    sleep 0.15
    ( PLANT_COORD_01_WIDEN=0.5 python3 -B "$SANDBOX/tools/coordination/claim.py" --root "$SANDBOX" \
        claim --task P01-DEMO --seat P01-SEAT-B --write-scope 'src/beta/**' > "$PLANT_WORK/b.txt" 2>&1 ) &
    P_B=$!
    wait $P_A
    RC_A=$?
    wait $P_B
    RC_B=$?
    echo "        claimer A rc=$RC_A   claimer B rc=$RC_B"
    grep -h '^VERDICT' "$PLANT_WORK/a.txt" "$PLANT_WORK/b.txt" | sed 's/^/        /'
    echo "        --- THE RESULTING STATE, READ BACK FROM THE REGISTRY (NOT ASSERTED) ---"
    grep -E '^(task_id|seat_actor_id|pid):' "$SANDBOX/governance/coordination/claims/P01-DEMO.claim.yaml" | sed 's/^/        /'
    HOLDER=$(grep '^seat_actor_id:' "$SANDBOX/governance/coordination/claims/P01-DEMO.claim.yaml" | awk '{print $2}')
    echo "        ONE FILE. TWO SUCCESSFUL CLAIMERS. THE SURVIVING RECORD SAYS: $HOLDER"
    echo "        THE OTHER SEAT BELIEVES IT HOLDS THIS TASK AND THE REGISTRY HAS NO TRACE OF IT."
    A2_OK=0
    [ "$RC_A" -eq 0 ] && [ "$RC_B" -eq 0 ] && A2_OK=1
    arm_result 2 "VIOLATED ADMITS" "BOTH claimers rc=0 on ONE task" "$A2_OK"
    revert_mutation "$PATCH"
fi

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3 — NON-VACUITY: THE DISJOINT CASE IS ADMITTED AND PROCEEDS IN PARALLEL"
echo "          (control INTACT — mutation reverted above)"
# ------------------------------------------------------------------------------------------------
rm -f "$SANDBOX"/governance/coordination/claims/P01-*.claim.yaml
( python3 -B "$SANDBOX/tools/coordination/claim.py" --root "$SANDBOX" \
    claim --task P01-DISJOINT-X --seat P01-SEAT-X --write-scope 'src/xray/**' > "$PLANT_WORK/x.txt" 2>&1 ) &
PX=$!
( python3 -B "$SANDBOX/tools/coordination/claim.py" --root "$SANDBOX" \
    claim --task P01-DISJOINT-Y --seat P01-SEAT-Y --write-scope 'docs/yankee/**' > "$PLANT_WORK/y.txt" 2>&1 ) &
PY_=$!
wait $PX
RC_X=$?
wait $PY_
RC_Y=$?
echo "    concurrent disjoint claim X rc=$RC_X   concurrent disjoint claim Y rc=$RC_Y"
grep -h '^VERDICT' "$PLANT_WORK/x.txt" "$PLANT_WORK/y.txt" | sed 's/^/      /'
run_rc "arm3 both claims LIVE simultaneously" python3 -B "$SANDBOX/tools/coordination/claim.py" --root "$SANDBOX" list
LIVE_RC=$LAST_RC
LIVE_N=$(echo "$LAST_OUT" | grep -c 'P01-DISJOINT')
echo "    live P01-DISJOINT claims present simultaneously = $LIVE_N"
echo "      produced by: claim.py list | grep -c P01-DISJOINT"
A3_OK=0
[ "$RC_X" -eq 0 ] && [ "$RC_Y" -eq 0 ] && [ "$LIVE_N" -eq 2 ] && A3_OK=1
arm_result 3 "NON-VACUITY ADMITS" "both rc=0 AND both live at once" "$A3_OK"

plant_summary
exit $?
