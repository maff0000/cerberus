#!/bin/sh
# ================================================================================================= #
# PLANT-COORD-07 — **THE CARRIER THAT CORRUPTED ITS OWN INPUT, AND THE DEPTH RULE THAT HID IT.**
#                  `CD-ASR-WO2R3-06-F05` + `CD-ASR-WO2R3-06-F11`. They COMPOUND, so they are
#                  planted together.
#
# **WHY THIS PLANT EXISTS AND WHY ITS SCOPE FORMS ARE CHOSEN THE WAY THEY ARE.**
# `PLANT-COORD-04` was 3/3 LIVE over a deliverable that was broken for every glob matching a real
# path, because it exercised exactly two scope forms: a LITERAL with no glob, and a glob matching
# NOTHING on disk. **THE ONLY TWO FORMS THAT CANNOT TRIGGER THE DEFECT.** That is the strongest
# instance in the whole ninth audit of a plant proving its own chosen instance, and this plant is
# built against that failure: **IT EXERCISES A GLOB MATCHING >=2 REAL PATHS AND A GLOB MATCHING
# EXACTLY 1**, which are the two regimes F05 actually has, plus the parent-path form F11 names.
#
#   ARM 1  BASELINE REFUSES — with the fix intact:
#            (a) a glob matching >=2 real paths is carried to `lease.py` VERBATIM and the launch
#                SUCCEEDS. At increment 12 this was an argparse error reported to the operator as
#                `LEASE REFUSED (rc=2)` — **commissioning that carrier would have refused every
#                real launch and told the operator there was a conflict.**
#            (b) a SECOND seat overlapping that scope IS REFUSED and never execs.
#            (c) a glob matching EXACTLY 1 real path is carried VERBATIM — the silent-narrowing
#                regime — and the second seat on a sibling file is REFUSED.
#            (d) F11: a seat holding a PARENT path and a seat holding a file BENEATH it are
#                REFUSED. At increment 12 the algebra called a directory DISJOINT FROM ITS OWN
#                CONTENTS.
#   ARM 2  VIOLATED ADMITS  — ONE named mutation puts back increment 12's two mechanisms: `set -f`
#                is dropped (pathname expansion returns) and the lease arguments are expanded
#                UNQUOTED (field splitting returns). **BOTH REGIMES ARE THEN DEMONSTRATED ON DISK:**
#                the exactly-1 glob is SILENTLY NARROWED in the lease record and the overlapping
#                second seat is ADMITTED WHILE THE FIRST IS ALIVE — a FALSE GREEN manufactured by
#                the binding itself — and the >=2 glob produces the rc=2 argparse failure dressed
#                as a refusal.
#   ARM 3  NON-VACUITY      — a genuinely DISJOINT launch STARTS AND RUNS ALONGSIDE THE FIRST, both
#                leases live. The fix did not turn the carrier into a serialiser.
# ================================================================================================= #
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${PLANT_SCRATCH:=/tmp/cd-eng-coord-fix-01/plants}"
: "${SOURCE_ROOT:=/srv/crash-detector-inc13}"
export PLANT_SCRATCH SOURCE_ROOT
. "$HERE/lib.sh"
plant_banner "PLANT-COORD-07"
PATCH="$HERE/PLANT-COORD-07.mutation.patch"
LAUNCH="$SANDBOX/tools/coordination/launch.sh"
LEASES="$SANDBOX/governance/coordination/leases"
SENT="$PLANT_WORK/sentinels"
mkdir -p "$SENT"

# ------------------------------------------------------------------------------------------------
# REAL PATHS ON DISK. **THE DEFECT ONLY EXISTS WHEN THE GLOB MATCHES SOMETHING**, which is exactly
# why PLANT-COORD-04 could not see it.
# ------------------------------------------------------------------------------------------------
# *** EVERY LAUNCH IN THIS PLANT RUNS WITH cwd = THE SANDBOX, AND THAT IS LOAD-BEARING. ***
# PATHNAME EXPANSION IS RELATIVE TO THE CURRENT WORKING DIRECTORY. A glob evaluated somewhere the
# matching files do not exist matches NOTHING and is left untouched by the shell — so a plant that
# invokes `launch.sh` from outside the tree CANNOT trigger F05 in either regime and would report
# ARM 1 as a pass while measuring nothing at all.
#
# **THE FIRST EXECUTION OF THIS PLANT DID EXACTLY THAT.** ARM 2 reported `*** DID NOT CONTRAST ***`
# — the mutation was applied, the defect was restored, and the scope still arrived verbatim. The
# plant was wrong, not the mutation. It is recorded here rather than quietly corrected, because
# **THIS IS THE PROJECT'S OWN WORST HABIT — A PLANT THAT PROVES ITS OWN CHOSEN INSTANCE — CAUGHT
# INSIDE THE PLANT WRITTEN TO PUNISH IT**, and the only reason it was caught is that arm 2 is a
# real counterfactual and refused to pass.
cd "$SANDBOX" || { echo "  *** CANNOT ENTER THE SANDBOX. ABORTING. ***"; exit 2; }
echo "  cwd for every launch below: $(pwd)   [CD-PL-F98]"
mkdir -p "$SANDBOX/docs/alpha" "$SANDBOX/docs/beta/deep" "$SANDBOX/docs/bravo"
: > "$SANDBOX/docs/alpha/only.md"
: > "$SANDBOX/docs/alpha/other.md"
: > "$SANDBOX/docs/alpha/third.md"
: > "$SANDBOX/docs/beta/deep/file.md"
echo "  SCOPE FORMS THIS PLANT EXERCISES, AND WHAT EACH ONE MATCHES ON DISK:"
echo "    'docs/alpha/*'      matches $(ls -1 "$SANDBOX"/docs/alpha/* | wc -l) real path(s)   <- the >=2 regime"
echo "    'docs/alpha/on*.md' matches $(ls -1 "$SANDBOX"/docs/alpha/on*.md | wc -l) real path(s)   <- the EXACTLY-1 regime, THE DANGEROUS ONE"
echo "    'docs/beta'         is a real DIRECTORY containing docs/beta/deep/file.md   <- F11"
echo "      produced by: ls -1 <sandbox>/docs/alpha/* | wc -l ; ls -1 <sandbox>/docs/alpha/on*.md | wc -l"
echo ""

cat > "$PLANT_WORK/fake-seat.sh" <<EOF
#!/bin/sh
touch "$SENT/\$1.started"
sleep "\$2"
EOF
chmod +x "$PLANT_WORK/fake-seat.sh"

start_first() { # start_first <lease> <task> <scope>
    rm -f "$SENT"/*.started
    sh "$LAUNCH" --lease "$1" --seat P07-FIRST --task "$2" --write-scope "$3" \
        -- "$PLANT_WORK/fake-seat.sh" first 25 > "$PLANT_WORK/first.log" 2>&1 &
    FIRST_PID=$!
    _n=0
    while [ ! -f "$SENT/first.started" ] && [ $_n -lt 75 ]; do sleep 0.2; _n=$((_n+1)); done
    FIRST_STARTED=NO
    [ -f "$SENT/first.started" ] && FIRST_STARTED=YES
    echo "    first seat started: $FIRST_STARTED   process alive: $(kill -0 $FIRST_PID 2>/dev/null && echo YES || echo NO)  pid=$FIRST_PID"
}
stop_first() {
    kill $FIRST_PID 2>/dev/null
    wait $FIRST_PID 2>/dev/null
    rm -f "$LEASES"/*.lease.yaml
}
recorded_scope() { # recorded_scope <lease-id>  -- what the LEASE RECORD ON DISK actually says
    sed -n '/^write_scope:/,/^[a-z_]*:/p' "$LEASES/$1.lease.yaml" 2>/dev/null | grep '^- ' | sed 's/^- //'
}

# ------------------------------------------------------------------------------------------------
echo "  ARM 1 — BASELINE: THE SCOPE SURVIVES THE CARRIER, AND THE OVERLAP IS REFUSED"
# ------------------------------------------------------------------------------------------------
echo "   (1a) a glob matching >=2 real paths must be carried VERBATIM and the launch must SUCCEED"
rm -f "$LEASES"/*.lease.yaml
start_first L07-A P07-TASK-A 'docs/alpha/*'
REC=$(recorded_scope L07-A)
echo "    write_scope RECORDED IN THE LEASE ON DISK: '$REC'"
echo "      produced by: sed -n '/^write_scope:/,/^[a-z_]*:/p' $LEASES/L07-A.lease.yaml"
A1A_OK=0
[ "$REC" = 'docs/alpha/*' ] && [ "$FIRST_STARTED" = "YES" ] && A1A_OK=1
echo "    verbatim? $([ "$REC" = 'docs/alpha/*' ] && echo YES || echo 'NO — THE CARRIER CORRUPTED IT')"

echo "   (1b) a SECOND seat overlapping it must be REFUSED and must never exec"
rm -f "$SENT/second.started"
run_rc "arm1b overlapping second launch" \
    sh "$LAUNCH" --lease L07-B --seat P07-SECOND --task P07-TASK-B \
       --write-scope 'docs/alpha/other.md' -- "$PLANT_WORK/fake-seat.sh" second 2
A1B_RC=$LAST_RC
echo "$LAST_OUT" | grep -E 'VERDICT|WRITE_WRITE|OVERLAP' | head -4 | sed 's/^/      | /'
STARTED=NO; [ -f "$SENT/second.started" ] && STARTED=YES
echo "    second seat process started? $STARTED   (produced by: test -f $SENT/second.started)"
A1B_OK=0
[ "$A1B_RC" -ne 0 ] && [ "$STARTED" = "NO" ] && A1B_OK=1
stop_first

echo "   (1c) THE EXACTLY-1 REGIME — the one that produced the SILENT FALSE GREEN"
rm -f "$LEASES"/*.lease.yaml
start_first L07-C P07-TASK-C 'docs/alpha/on*.md'
REC2=$(recorded_scope L07-C)
echo "    write_scope RECORDED ON DISK: '$REC2'   (increment 12 recorded 'docs/alpha/only.md' here)"
rm -f "$SENT/second.started"
run_rc "arm1c second seat on the file that glob matches" \
    sh "$LAUNCH" --lease L07-D --seat P07-SECOND --task P07-TASK-D \
       --write-scope 'docs/alpha/only.md' -- "$PLANT_WORK/fake-seat.sh" second 2
A1C_RC=$LAST_RC
echo "$LAST_OUT" | grep -E 'VERDICT|OVERLAP' | head -3 | sed 's/^/      | /'
STARTED=NO; [ -f "$SENT/second.started" ] && STARTED=YES
A1C_OK=0
[ "$REC2" = 'docs/alpha/on*.md' ] && [ "$A1C_RC" -ne 0 ] && [ "$STARTED" = "NO" ] && A1C_OK=1
stop_first

echo "   (1d) F11 — a PARENT path and a file BENEATH it are NOT disjoint"
rm -f "$LEASES"/*.lease.yaml
start_first L07-E P07-TASK-E 'docs/beta'
rm -f "$SENT/second.started"
run_rc "arm1d second seat on a file INSIDE the parent the first seat holds" \
    sh "$LAUNCH" --lease L07-F --seat P07-SECOND --task P07-TASK-F \
       --write-scope 'docs/beta/deep/file.md' -- "$PLANT_WORK/fake-seat.sh" second 2
A1D_RC=$LAST_RC
echo "$LAST_OUT" | grep -E 'VERDICT|PARENT_PATH' | head -3 | sed 's/^/      | /'
PARENT_NAMED=$(echo "$LAST_OUT" | grep -c 'PARENT_PATH')
STARTED=NO; [ -f "$SENT/second.started" ] && STARTED=YES
A1D_OK=0
[ "$A1D_RC" -ne 0 ] && [ "$STARTED" = "NO" ] && [ "$PARENT_NAMED" -ge 1 ] && A1D_OK=1
stop_first

A1_OK=0
[ "$A1A_OK" = "1" ] && [ "$A1B_OK" = "1" ] && [ "$A1C_OK" = "1" ] && [ "$A1D_OK" = "1" ] && A1_OK=1
arm_result 1 "SCOPE CARRIED VERBATIM (BOTH GLOB REGIMES) + OVERLAP AND PARENT REFUSED" \
    "1a=$A1A_OK 1b=$A1B_OK 1c=$A1C_OK 1d=$A1D_OK all 1" "$A1_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 2 — VIOLATED ADMITS: increment 12's two mechanisms restored (no set -f, unquoted \$*)"
# ------------------------------------------------------------------------------------------------
apply_mutation "$PATCH"
if [ $? -ne 0 ]; then
    arm_result 2 "VIOLATED ADMITS" "mutation must apply" 0
    A2_OK=0
else
    echo "   (2a) THE EXACTLY-1 REGIME — SILENT NARROWING, THEN A FALSE GREEN"
    rm -f "$LEASES"/*.lease.yaml
    start_first L07-C P07-TASK-C 'docs/alpha/on*.md'
    REC3=$(recorded_scope L07-C)
    echo "    write_scope RECORDED ON DISK: '$REC3'"
    echo "    *** THE SEAT TYPED 'docs/alpha/on*.md'. THE RECORD SAYS '$REC3'."
    echo "    *** NOTHING ERRORED. THAT IS THE SILENT NARROWING. ***"
    rm -f "$SENT/second.started"
    run_rc "arm2a second seat on a SIBLING file, first seat STILL ALIVE" \
        sh "$LAUNCH" --lease L07-D --seat P07-SECOND --task P07-TASK-D \
           --write-scope 'docs/alpha/other.md' -- "$PLANT_WORK/fake-seat.sh" second 3
    A2A_RC=$LAST_RC
    echo "$LAST_OUT" | grep -E 'VERDICT' | head -2 | sed 's/^/      | /'
    _n=0
    while [ ! -f "$SENT/second.started" ] && [ $_n -lt 25 ]; do sleep 0.2; _n=$((_n+1)); done
    STARTED2=NO; [ -f "$SENT/second.started" ] && STARTED2=YES
    FIRST_ALIVE=$(kill -0 $FIRST_PID 2>/dev/null && echo YES || echo NO)
    echo "    second seat STARTED: $STARTED2      first seat STILL ALIVE: $FIRST_ALIVE"
    echo "    live lease records on disk = $(ls -1 "$LEASES"/*.lease.yaml 2>/dev/null | wc -l)"
    echo "    *** TWO SEATS ON docs/alpha, BOTH RUNNING, NEITHER REFUSED. SAME REQUEST AS ARM 1c,"
    echo "    *** OPPOSITE VERDICT, AND THE ONLY VARIABLE IS THIS PATCH. ***"
    A2A_OK=0
    [ "$REC3" != 'docs/alpha/on*.md' ] && [ "$A2A_RC" -eq 0 ] && [ "$STARTED2" = "YES" ] \
        && [ "$FIRST_ALIVE" = "YES" ] && A2A_OK=1
    stop_first

    echo "   (2b) THE >=2 REGIME — A HARD FAILURE DRESSED AS A REFUSAL"
    rm -f "$LEASES"/*.lease.yaml
    run_rc "arm2b a glob matching 3 real paths, through the mutated carrier" \
        sh "$LAUNCH" --lease L07-G --seat P07-FIRST --task P07-TASK-G \
           --write-scope 'docs/alpha/*' --dry-run -- "$PLANT_WORK/fake-seat.sh" first 1
    A2B_RC=$LAST_RC
    echo "$LAST_OUT" | grep -E 'unrecognized|LEASE REFUSED|error' | head -3 | sed 's/^/      | /'
    echo "    rc=$A2B_RC — and the operator sees 'LEASE REFUSED', indistinguishable from a"
    echo "    genuine scope collision. THE LAUNCH WAS NEVER EVEN REFUSED BY THE CONTROL."
    A2B_OK=0
    [ "$A2B_RC" -ne 0 ] && A2B_OK=1

    A2_OK=0
    [ "$A2A_OK" = "1" ] && [ "$A2B_OK" = "1" ] && A2_OK=1
    arm_result 2 "BOTH F05 REGIMES REPRODUCED ON DEMAND" "2a=$A2A_OK 2b=$A2B_OK" "$A2_OK"
    revert_mutation "$PATCH"
fi

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3 — NON-VACUITY: A DISJOINT LAUNCH STILL STARTS AND RUNS ALONGSIDE THE FIRST"
# ------------------------------------------------------------------------------------------------
rm -f "$LEASES"/*.lease.yaml
start_first L07-H P07-TASK-H 'docs/alpha/*'
rm -f "$SENT/second.started"
sh "$LAUNCH" --lease L07-I --seat P07-DISJOINT --task P07-TASK-I \
   --write-scope 'docs/bravo/**' -- "$PLANT_WORK/fake-seat.sh" second 25 > "$PLANT_WORK/second.log" 2>&1 &
SECOND_PID=$!
_n=0
while [ ! -f "$SENT/second.started" ] && [ $_n -lt 75 ]; do sleep 0.2; _n=$((_n+1)); done
STARTED3=NO; [ -f "$SENT/second.started" ] && STARTED3=YES
REFUSED3=$(grep -c 'LEASE REFUSED' "$PLANT_WORK/second.log")
FIRST_ALIVE3=$(kill -0 $FIRST_PID 2>/dev/null && echo YES || echo NO)
echo "    disjoint second seat STARTED: $STARTED3   refusals in its log: $REFUSED3"
echo "    first seat STILL ALIVE AND UNDISTURBED: $FIRST_ALIVE3 (kill -0 $FIRST_PID)"
run_rc "arm3 both leases live at once, both processes still running" \
    python3 -B "$SANDBOX/tools/coordination/lease.py" --root "$SANDBOX" list
BOTH=$(echo "$LAST_OUT" | grep -c 'liveness=LIVE')
echo "    leases reading LIVE simultaneously = $BOTH"
echo "      produced by: lease.py list | grep -c 'liveness=LIVE'"
echo "$LAST_OUT" | grep -E '^   lease=' | sed 's/^/      | /'
A3_OK=0
[ "$STARTED3" = "YES" ] && [ "$REFUSED3" -eq 0 ] && [ "$FIRST_ALIVE3" = "YES" ] && [ "$BOTH" -ge 2 ] && A3_OK=1
arm_result 3 "DISJOINT LAUNCHES STILL RUN IN PARALLEL" \
    "started AND not refused AND first alive AND 2 live leases" "$A3_OK"
kill $SECOND_PID 2>/dev/null; wait $SECOND_PID 2>/dev/null
stop_first

plant_summary
exit $?
