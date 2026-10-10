#!/bin/sh
# ================================================================================================= #
# PLANT-COORD-08 — **A CONTROL THE GRADED PARTY COULD FLIP.** `CD-ASR-WO2R3-06-F09`.
#
# The ninth Assurance seat turned `check_lease_held.py --range` from RED to GREEN **retroactively,
# in one command, as the party being graded**, with the commits unchanged and nothing rewritten.
# Two separable root causes:
#
#   (a) `--range` graded HISTORICAL writes against leases live NOW. The contract is named
#       `CD-CT-009-LEASE-HELD-AT-WRITE` and the mode DID NOT MEASURE TIME-OF-WRITE AT ALL.
#   (b) `lease.py --pid` was UNAUTHENTICATED, and `--pid 1` is `init`, which is always alive, so
#       the lease was IMMORTAL.
#
#   ARM 1  BASELINE REFUSES — commits made with no lease are REFUSED; **THE RETRO LEASE IS THEN
#                             ACQUIRED AND THE VERDICT DOES NOT MOVE — not the verdict, not the
#                             count.** And `--pid 1` is refused at acquisition, by DERIVATION
#                             (os.getsid), not by a denylist.
#   ARM 2  VIOLATED ADMITS  — ONE named mutation disables the two time comparisons, restoring
#                             "grade a past write against a lease live now". **THE SAME RETRO
#                             LEASE THEN FLIPS THE SAME RANGE FROM REFUSED TO ADMITTED.**
#   ARM 3  NON-VACUITY      — a lease acquired **BEFORE** the write, covering it, still ADMITS.
#                             *** A TIME RULE THAT REFUSED HONEST HISTORY TOO WOULD HAVE MADE THE
#                             MODE USELESS RATHER THAN CORRECT. ***
# ================================================================================================= #
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${PLANT_SCRATCH:=/tmp/cd-eng-coord-fix-01/plants}"
: "${SOURCE_ROOT:=/srv/crash-detector-inc13}"
export PLANT_SCRATCH SOURCE_ROOT
. "$HERE/lib.sh"
plant_banner "PLANT-COORD-08"
PATCH="$HERE/PLANT-COORD-08.mutation.patch"
HELD="$SANDBOX/tools/coordination/check_lease_held.py"
LEASE="$SANDBOX/tools/coordination/lease.py"
LEASES="$SANDBOX/governance/coordination/leases"
IDENT=PROJECT_LEAD_SEAT_01

# The sandbox is an INDEPENDENT clone, so committing in it touches no other tree (CD-PL-F128).
GIT_AUTHOR_NAME=$IDENT;    GIT_AUTHOR_EMAIL=pl@plant.local
GIT_COMMITTER_NAME=$IDENT; GIT_COMMITTER_EMAIL=pl@plant.local
export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL

mkdir -p "$SANDBOX/src/graded"
rm -f "$LEASES"/*.lease.yaml
echo "  TWO GOVERNED COMMITS ARE MADE WITH NO LEASE HELD AT ALL:"
echo "one" > "$SANDBOX/src/graded/one.py"
git -C "$SANDBOX" add src/graded/one.py >/dev/null 2>&1
git -C "$SANDBOX" commit -q -m "P08 governed write 1" >/dev/null 2>&1
echo "two" > "$SANDBOX/src/graded/two.py"
git -C "$SANDBOX" add src/graded/two.py >/dev/null 2>&1
git -C "$SANDBOX" commit -q -m "P08 governed write 2" >/dev/null 2>&1
echo "    HEAD~2..HEAD = $(git -C "$SANDBOX" rev-parse HEAD~2 | cut -c1-12)..$(git -C "$SANDBOX" rev-parse HEAD | cut -c1-12)"
echo "      produced by: git -C <sandbox> rev-parse HEAD~2 HEAD"
echo "    committing identity = $IDENT   (the party this control grades)"
echo ""

uncovered_count() { echo "$LAST_OUT" | sed -n 's/^uncovered_governed_writes = \([0-9]*\)/\1/p'; }

# ------------------------------------------------------------------------------------------------
echo "  ARM 1 — BASELINE REFUSES, AND THE ONE-COMMAND FLIP DOES NOT MOVE IT"
# ------------------------------------------------------------------------------------------------
run_rc "arm1 --range with NO lease at all" \
    python3 -B "$HELD" --root "$SANDBOX" --range HEAD~2..HEAD --identity "$IDENT"
BEFORE_RC=$LAST_RC
BEFORE_N=$(uncovered_count)
echo "$LAST_OUT" | grep -E '^VERDICT' | sed 's/^/      | /'
echo "    rc=$BEFORE_RC  uncovered_governed_writes=$BEFORE_N"

echo "   (1a) THE `--pid 1` HALF: the immortal lease must be REFUSED AT ACQUISITION"
run_rc "arm1a lease.py acquire --pid 1 (init — always alive)" \
    python3 -B "$LEASE" --root "$SANDBOX" acquire --lease RETRO0 --seat "$IDENT" --task ANY \
        --write-scope 'governance/**' --pid 1
PID1_RC=$LAST_RC
echo "$LAST_OUT" | grep -E 'VERDICT|PID_NOT_AUTHENTICATED' | head -2 | sed 's/^/      | /'
echo "    rc=$PID1_RC (non-zero = the immortal lease was refused, by derivation not by a denylist)"
A1A_OK=0
[ "$PID1_RC" -ne 0 ] && A1A_OK=1

echo "   (1b) THE RETRO LEASE, ACQUIRED NOW WITH A SESSION-LEGAL PID, OVER EVERYTHING"
run_rc "arm1b the retroactive lease acquisition" \
    python3 -B "$LEASE" --root "$SANDBOX" acquire --lease RETRO --seat "$IDENT" --task ANY \
        --write-scope 'governance/**' --write-scope 'tools/**' --write-scope 'src/**' --pid $$
echo "$LAST_OUT" | grep -E '^VERDICT' | sed 's/^/      | /'
RETRO_RC=$LAST_RC

run_rc "arm1b THE SAME RANGE, RE-RUN, WITH THE RETRO LEASE LIVE" \
    python3 -B "$HELD" --root "$SANDBOX" --range HEAD~2..HEAD --identity "$IDENT"
AFTER_RC=$LAST_RC
AFTER_N=$(uncovered_count)
echo "$LAST_OUT" | grep -E 'NOT THE TIME' | head -2 | sed 's/^/      | /'
echo "$LAST_OUT" | grep -E '^VERDICT' | sed 's/^/      | /'
echo "    BEFORE: rc=$BEFORE_RC uncovered=$BEFORE_N       AFTER THE FLIP ATTEMPT: rc=$AFTER_RC uncovered=$AFTER_N"
echo "    *** THE VERDICT MUST NOT MOVE, AND NEITHER MUST THE COUNT. A CONTROL THAT MOVED EVEN"
echo "    *** PARTLY WOULD STILL BE ANSWERABLE BY THE PARTY IT GRADES. ***"
A1_OK=0
[ "$BEFORE_RC" -eq 1 ] && [ "$AFTER_RC" -eq 1 ] && [ "$RETRO_RC" -eq 0 ] \
    && [ -n "$BEFORE_N" ] && [ "$BEFORE_N" = "$AFTER_N" ] && [ "$A1A_OK" = "1" ] && A1_OK=1
arm_result 1 "THE RETRO FLIP MOVES NOTHING, AND --pid 1 IS REFUSED" \
    "rc 1->1 AND uncovered $BEFORE_N->$AFTER_N unchanged AND --pid 1 refused" "$A1_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 2 — VIOLATED ADMITS: the two time comparisons are disabled. THE SAME RETRO LEASE FLIPS IT."
# ------------------------------------------------------------------------------------------------
apply_mutation "$PATCH"
if [ $? -ne 0 ]; then
    arm_result 2 "VIOLATED ADMITS" "mutation must apply" 0
else
    run_rc "arm2 THE SAME RANGE, THE SAME LIVE RETRO LEASE, TIME NOT MEASURED" \
        python3 -B "$HELD" --root "$SANDBOX" --range HEAD~2..HEAD --identity "$IDENT"
    FLIP_RC=$LAST_RC
    FLIP_N=$(uncovered_count)
    echo "$LAST_OUT" | grep -E '^VERDICT' | sed 's/^/      | /'
    echo "    rc=$FLIP_RC  uncovered_governed_writes=$FLIP_N"
    echo "    *** SAME COMMITS. SAME HISTORY. NOTHING REWRITTEN. RED TO GREEN IN ONE COMMAND. ***"
    A2_OK=0
    [ "$FLIP_RC" -eq 0 ] && [ "$FLIP_N" = "0" ] && A2_OK=1
    arm_result 2 "TIME NOT MEASURED -> THE GRADED PARTY FLIPS ITS OWN CONTROL" "rc=0 AND uncovered=0" "$A2_OK"
    revert_mutation "$PATCH"
fi

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3 — NON-VACUITY: A LEASE ACQUIRED **BEFORE** THE WRITE STILL ADMITS IT."
echo "          A TIME RULE THAT REFUSED HONEST HISTORY WOULD BE USELESS, NOT CORRECT."
# ------------------------------------------------------------------------------------------------
rm -f "$LEASES"/*.lease.yaml
run_rc "arm3 an HONEST lease, acquired BEFORE any write" \
    python3 -B "$LEASE" --root "$SANDBOX" acquire --lease HONEST --seat "$IDENT" --task T-HONEST \
        --write-scope 'src/graded/**' --pid $$
echo "$LAST_OUT" | grep -E '^VERDICT' | sed 's/^/      | /'
echo "    the lease is acquired, then the plant WAITS so that the write is strictly later than the"
echo "    acquisition. CD-RULE-005's timestamp source is second-granular and BOTH interval edges"
echo "    are STRICT, so a same-second write is refused BY DESIGN — that cost is declared in the"
echo "    instrument's own limit block, and this arm respects it rather than hiding it."
sleep 2
echo "three" > "$SANDBOX/src/graded/three.py"
git -C "$SANDBOX" add src/graded/three.py >/dev/null 2>&1
git -C "$SANDBOX" commit -q -m "P08 governed write UNDER a live lease" >/dev/null 2>&1
run_rc "arm3 --range over the write that WAS covered at the time it happened" \
    python3 -B "$HELD" --root "$SANDBOX" --range HEAD~1..HEAD --identity "$IDENT"
A3_RC=$LAST_RC
A3_N=$(uncovered_count)
echo "$LAST_OUT" | grep -E 'covered   src|^VERDICT' | sed 's/^/      | /'
echo "    rc=$A3_RC  uncovered_governed_writes=$A3_N"
A3_OK=0
[ "$A3_RC" -eq 0 ] && [ "$A3_N" = "0" ] && A3_OK=1
arm_result 3 "AN HONEST LEASE STILL ADMITS THE WRITE IT COVERED" "rc=0 AND uncovered=0" "$A3_OK"

plant_summary
exit $?
