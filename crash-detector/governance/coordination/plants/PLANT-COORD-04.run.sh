#!/bin/sh
# ================================================================================================= #
# PLANT-COORD-04 — THE LAUNCH LEASE. `PO-DECISIONS-0021` ruling 3(d), increment 12 ITEM 4.
#
#   ARM 1  BASELINE REFUSES — `launch.sh` for a task/scope overlapping a LIVE lease exits non-zero
#                             **AND THE SEAT PROCESS NEVER STARTS. THE NON-START IS PROVED, NOT
#                             INFERRED FROM AN EXIT CODE** — the would-be seat's only job is to
#                             create a sentinel file, and the plant looks for it.
#   ARM 2  VIOLATED ADMITS  — liveness always returns False (the silent-stale-reap bug). The
#                             overlapping launch is ADMITTED **WHILE THE FIRST SESSION IS STILL
#                             ALIVE** — `PO-DECISIONS-0021` ruling 2, reproduced on demand.
#   ARM 3  NON-VACUITY      — A DISJOINT SECOND LAUNCH STARTS AND RUNS ALONGSIDE THE FIRST, BOTH
#                             LEASES LIVE. **THIS IS THE ARM THE WHOLE RULING TURNS ON.**
# ================================================================================================= #
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$HERE/lib.sh"
plant_banner "PLANT-COORD-04"
PATCH="$HERE/PLANT-COORD-04.mutation.patch"
LAUNCH="$SANDBOX/tools/coordination/launch.sh"
LEASE="$SANDBOX/tools/coordination/lease.py"
SENT="$PLANT_WORK/sentinels"
mkdir -p "$SENT"

# The "seat" that a launch would start. It records that it STARTED, then lives for a while so that
# its lease is measurably LIVE while the next launch is attempted.
cat > "$PLANT_WORK/fake-seat.sh" <<EOF
#!/bin/sh
touch "$SENT/\$1.started"
sleep "\$2"
EOF
chmod +x "$PLANT_WORK/fake-seat.sh"

start_first() { # start_first <task> <scope> [readscope]
    rm -f "$SENT"/*.started
    if [ -n "$3" ]; then
        sh "$LAUNCH" --lease L-FIRST --seat P04-SEAT-FIRST --task "$1" --write-scope "$2" \
            --read-scope "$3" -- "$PLANT_WORK/fake-seat.sh" first 25 > "$PLANT_WORK/first.log" 2>&1 &
    else
        sh "$LAUNCH" --lease L-FIRST --seat P04-SEAT-FIRST --task "$1" --write-scope "$2" \
            -- "$PLANT_WORK/fake-seat.sh" first 25 > "$PLANT_WORK/first.log" 2>&1 &
    fi
    FIRST_PID=$!
    # wait for it to actually be up
    _n=0
    while [ ! -f "$SENT/first.started" ] && [ $_n -lt 60 ]; do sleep 0.2; _n=$((_n+1)); done
    echo "    first seat started sentinel present: $([ -f "$SENT/first.started" ] && echo YES || echo NO)"
    echo "    first seat process alive: $(kill -0 $FIRST_PID 2>/dev/null && echo YES || echo NO)  pid=$FIRST_PID"
}

stop_first() {
    kill $FIRST_PID 2>/dev/null
    wait $FIRST_PID 2>/dev/null
    rm -f "$SANDBOX"/governance/coordination/leases/*.lease.yaml
}

# ------------------------------------------------------------------------------------------------
echo "  ARM 1 — BASELINE REFUSES, AND THE SEAT NEVER STARTS"
# ------------------------------------------------------------------------------------------------
start_first P04-TASK-ONE 'src/contended/**'
run_rc "arm1 lease list (the first lease must read LIVE)" python3 -B "$LEASE" --root "$SANDBOX" list
echo "$LAST_OUT" | grep -E 'lease=|live_leases' | sed 's/^/      | /'

rm -f "$SENT/second.started"
run_rc "arm1 OVERLAPPING second launch (must be REFUSED, must not exec)" \
    sh "$LAUNCH" --lease L-SECOND --seat P04-SEAT-SECOND --task P04-TASK-TWO \
       --write-scope 'src/contended/module.py' -- "$PLANT_WORK/fake-seat.sh" second 2
A1_RC=$LAST_RC
show_out 12
STARTED=NO
[ -f "$SENT/second.started" ] && STARTED=YES
echo "    *** DID THE SECOND SEAT PROCESS START? $STARTED ***"
echo "        produced by: test -f $SENT/second.started"
echo "        (the would-be seat's FIRST action is to touch that file, so its absence is a"
echo "         positive proof of non-start and not an inference from the exit code)"
A1_OK=0
[ "$A1_RC" -ne 0 ] && [ "$STARTED" = "NO" ] && A1_OK=1
arm_result 1 "BASELINE REFUSES + SEAT NEVER STARTS" "rc!=0 AND no sentinel" "$A1_OK"
stop_first

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 2 — VIOLATED ADMITS: liveness always returns False (the silent-stale-reap bug)"
# ------------------------------------------------------------------------------------------------
apply_mutation "$PATCH"
if [ $? -ne 0 ]; then
    arm_result 2 "VIOLATED ADMITS" "mutation must apply" 0
else
    start_first P04-TASK-ONE 'src/contended/**'
    FIRST_STILL_ALIVE=$(kill -0 $FIRST_PID 2>/dev/null && echo YES || echo NO)
    rm -f "$SENT/second.started"
    run_rc "arm2 SAME overlapping launch, mutated liveness" \
        sh "$LAUNCH" --lease L-SECOND --seat P04-SEAT-SECOND --task P04-TASK-TWO \
           --write-scope 'src/contended/module.py' -- "$PLANT_WORK/fake-seat.sh" second 2
    A2_RC=$LAST_RC
    show_out 8
    _n=0
    while [ ! -f "$SENT/second.started" ] && [ $_n -lt 25 ]; do sleep 0.2; _n=$((_n+1)); done
    STARTED2=NO
    [ -f "$SENT/second.started" ] && STARTED2=YES
    FIRST_ALIVE_NOW=$(kill -0 $FIRST_PID 2>/dev/null && echo YES || echo NO)
    echo "    second seat STARTED: $STARTED2"
    echo "    *** AND THE FIRST SESSION IS STILL ALIVE: $FIRST_ALIVE_NOW (kill -0 $FIRST_PID) ***"
    echo "    THAT IS PO-DECISIONS-0021 RULING 2, REPRODUCED ON DEMAND: two sessions on one scope,"
    echo "    neither aware of the other, the record surviving only by accident."
    A2_OK=0
    [ "$A2_RC" -eq 0 ] && [ "$STARTED2" = "YES" ] && [ "$FIRST_ALIVE_NOW" = "YES" ] && A2_OK=1
    arm_result 2 "VIOLATED ADMITS WHILE FIRST IS ALIVE" "rc=0 AND second started AND first alive" "$A2_OK"
    stop_first
    revert_mutation "$PATCH"
fi

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3 — NON-VACUITY: A DISJOINT SECOND LAUNCH STARTS AND RUNS ALONGSIDE THE FIRST"
echo "          THIS IS THE ARM THE WHOLE RULING TURNS ON."
# ------------------------------------------------------------------------------------------------
rm -f "$SANDBOX"/governance/coordination/leases/*.lease.yaml
start_first P04-TASK-ALPHA 'src/alpha/**'
rm -f "$SENT/second.started"
run_rc "arm3 DISJOINT second launch (must be ADMITTED and must exec)" \
    sh "$LAUNCH" --lease L-DISJOINT --seat P04-SEAT-DISJOINT --task P04-TASK-BRAVO \
       --write-scope 'docs/bravo/**' -- "$PLANT_WORK/fake-seat.sh" second 8
A3_RC=$LAST_RC
show_out 8
STARTED3=NO
[ -f "$SENT/second.started" ] && STARTED3=YES
FIRST_ALIVE3=$(kill -0 $FIRST_PID 2>/dev/null && echo YES || echo NO)
echo "    disjoint second seat STARTED: $STARTED3"
echo "    first session STILL ALIVE and UNDISTURBED: $FIRST_ALIVE3 (kill -0 $FIRST_PID)"
run_rc "arm3 both leases live at once" python3 -B "$LEASE" --root "$SANDBOX" list
BOTH=$(echo "$LAST_OUT" | grep -c 'liveness=LIVE')
echo "    leases reading LIVE simultaneously = $BOTH"
echo "      produced by: lease.py list | grep -c 'liveness=LIVE'"
echo "$LAST_OUT" | grep -E 'lease=' | sed 's/^/      | /'
A3_OK=0
[ "$A3_RC" -eq 0 ] && [ "$STARTED3" = "YES" ] && [ "$FIRST_ALIVE3" = "YES" ] && [ "$BOTH" -ge 2 ] && A3_OK=1
arm_result 3 "NON-VACUITY: DISJOINT LAUNCHES RUN IN PARALLEL" \
    "rc=0 AND second started AND first alive AND 2 live leases" "$A3_OK"
stop_first

plant_summary
exit $?
