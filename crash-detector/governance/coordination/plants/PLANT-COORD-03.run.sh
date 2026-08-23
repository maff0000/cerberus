#!/bin/sh
# ================================================================================================= #
# PLANT-COORD-03 — MERGE NON-OVERLAP. `PO-DECISIONS-0021` ruling 3(c), increment 12 ITEM 3.
#
#   ARM 1  BASELINE REFUSES — two seat branches that BOTH touched one file -> `merge_reconcile.py`
#                             non-zero, NAMING THE ARTEFACT AND BOTH SEATS.
#   ARM 2  VIOLATED ADMITS  — pairwise-intersection assertion dropped -> the merge is ADMITTED and
#                             ONE SEAT'S WORK IS SILENTLY CLOBBERED. **SHOW WHICH.**
#   ARM 3  NON-VACUITY      — two seat branches with genuinely disjoint touched-path sets -> exit 0,
#                             BOTH INTEGRATED, BOTH SETS OF CHANGES PRESENT IN THE RESULT.
#                             **THE RESULT IS VERIFIED, NOT THE EXIT CODE.**
# ================================================================================================= #
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$HERE/lib.sh"
plant_banner "PLANT-COORD-03"
PATCH="$HERE/PLANT-COORD-03.mutation.patch"
MR="$SANDBOX/tools/coordination/merge_reconcile.py"
G="git -C $SANDBOX"

seat_env() { # seat_env <seat>
    export GIT_AUTHOR_NAME="$1" GIT_COMMITTER_NAME="$1"
    export GIT_AUTHOR_EMAIL="$(echo "$1" | tr 'A-Z' 'a-z')@seats.crash-detector.invalid"
    export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
}

BASE=$($G rev-parse HEAD)
$G cat-file -t "$BASE" > /dev/null
echo "  BASE = $BASE   (git rev-parse HEAD ; git cat-file -t -> commit)  [CD-PL-F36]"

# Two seat branches, both editing THE SAME artefact.
mkdir -p "$SANDBOX/src/shared"
$G checkout -q -b p03-seat-a "$BASE"
seat_env P03-SEAT-A
printf 'alpha wrote this line\n' > "$SANDBOX/src/shared/contended.txt"
$G add -A src/shared >/dev/null; $G commit -q -m "P03 seat A edits the contended artefact"
TIP_A=$($G rev-parse HEAD)

$G checkout -q -b p03-seat-b "$BASE"
seat_env P03-SEAT-B
mkdir -p "$SANDBOX/src/shared"
printf 'bravo wrote this line\n' > "$SANDBOX/src/shared/contended.txt"
$G add -A src/shared >/dev/null; $G commit -q -m "P03 seat B edits the SAME contended artefact"
TIP_B=$($G rev-parse HEAD)
$G checkout -q inc12-coordination


# ------------------------------------------------------------------------------------------------
# SET-UP GUARD. A tip that equals the base means the seat branch HAS NO COMMIT, and every assertion
# in this plant would then pass on an EMPTY diff — a green obtained by measuring nothing. THAT
# EXACT FAILURE HAPPENED WHILE BUILDING THIS PLANT: seat B's `printf` silently failed because
# `git checkout` had removed the directory, its commit never happened, and ARM 1 reported PASS on a
# contended artefact. The arm summary caught it. THIS GUARD MAKES IT LOUD INSTEAD OF SUBTLE.
# ------------------------------------------------------------------------------------------------
assert_tip_moved() { # assert_tip_moved <label> <tip>
    if [ "$2" = "$BASE" ]; then
        echo "  *** SET-UP FAILED: $1 tip == BASE. The seat branch has no commit and every"
        echo "  *** assertion would pass on an empty diff. THIS PLANT IS NOT EVIDENCE. ***"
        exit 3
    fi
    echo "    set-up ok: $1 tip $2 != BASE"
}
assert_tip_moved P03-SEAT-A "$TIP_A"
assert_tip_moved P03-SEAT-B "$TIP_B"

# Their claims. Written directly: the point of this plant is the AFTER-THE-FACT check.
mkc() { printf 'record_type: WORK_CLAIM\ntask_id: %s\nseat_actor_id: %s\npid: %d\nclaimed_utc: %s\nwrite_scope:\n- %s\nread_scope: []\nstate: CLAIMED\n' \
    "$1" "$2" "$$" "$(date -u +%FT%TZ)" "$3" > "$SANDBOX/governance/coordination/claims/$1.claim.yaml"; }
mkc P03-A P03-SEAT-A 'src/shared/**'
mkc P03-B P03-SEAT-B 'src/shared/**'

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 1 — BASELINE REFUSES: both seats touched src/shared/contended.txt"
# ------------------------------------------------------------------------------------------------
run_rc "arm1 merge_reconcile over the contended pair" python3 -B "$MR" --root "$SANDBOX" \
    --base "$BASE" --claim P03-A --claim P03-B --tip "P03-A=$TIP_A" --tip "P03-B=$TIP_B"
A1_RC=$LAST_RC
echo "$LAST_OUT" | grep -E 'ASSERTION|FINDING|VERDICT' | sed 's/^/      | /'
N_A=0; N_B=0; N_P=0
echo "$LAST_OUT" | grep -q 'P03-SEAT-A' && N_A=1
echo "$LAST_OUT" | grep -q 'P03-SEAT-B' && N_B=1
echo "$LAST_OUT" | grep -q 'src/shared/contended.txt' && N_P=1
echo "    names seat A=$N_A seat B=$N_B artefact=$N_P"
A1_OK=0
[ "$A1_RC" -ne 0 ] && [ "$N_A" -eq 1 ] && [ "$N_B" -eq 1 ] && [ "$N_P" -eq 1 ] && A1_OK=1
arm_result 1 "BASELINE REFUSES" "rc!=0, artefact and both seats named" "$A1_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 2 — VIOLATED ADMITS: the pairwise-intersection assertion is dropped"
# ------------------------------------------------------------------------------------------------
apply_mutation "$PATCH"
if [ $? -ne 0 ]; then
    arm_result 2 "VIOLATED ADMITS" "mutation must apply" 0
else
    run_rc "arm2 merge_reconcile, intersection assertion removed" python3 -B "$MR" --root "$SANDBOX" \
        --base "$BASE" --claim P03-A --claim P03-B --tip "P03-A=$TIP_A" --tip "P03-B=$TIP_B"
    A2_RC=$LAST_RC
    echo "$LAST_OUT" | grep -E 'ASSERTION|VERDICT' | sed 's/^/      | /'
    echo "    -- AND NOW THE MERGE THE INSTRUMENT JUST ADMITTED, PERFORMED FOR REAL --"
    $G checkout -q -b p03-merge "$TIP_A"
    seat_env P03-ACCOUNTABLE
    $G merge -q --no-edit -X theirs p03-seat-b > /dev/null 2>&1
    MERGE_RC=$?
    echo "    git merge -X theirs rc=$MERGE_RC"
    echo "    CONTENTS OF THE CONTENDED ARTEFACT AFTER THE ADMITTED MERGE:"
    sed 's/^/        /' "$SANDBOX/src/shared/contended.txt"
    LOST=""
    grep -q 'alpha wrote this line' "$SANDBOX/src/shared/contended.txt" || LOST="P03-SEAT-A"
    grep -q 'bravo wrote this line' "$SANDBOX/src/shared/contended.txt" || LOST="$LOST P03-SEAT-B"
    echo "    *** WORK SILENTLY LOST BELONGS TO: ${LOST:-<none>} ***"
    echo "    The instrument printed ASSERTION 2 NON-OVERLAP : PASS and did not look."
    $G checkout -q inc12-coordination
    A2_OK=0
    [ "$A2_RC" -eq 0 ] && [ -n "$LOST" ] && A2_OK=1
    arm_result 2 "VIOLATED ADMITS" "rc=0 AND a named seat's work is lost" "$A2_OK"
    revert_mutation "$PATCH"
fi

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3 — NON-VACUITY: DISJOINT TOUCHED-PATH SETS ARE ADMITTED AND BOTH ARE INTEGRATED"
# ------------------------------------------------------------------------------------------------
rm -f "$SANDBOX"/governance/coordination/claims/*.claim.yaml
mkdir -p "$SANDBOX/src/xray" "$SANDBOX/src/yankee"
$G checkout -q -b p03-seat-x "$BASE"
seat_env P03-SEAT-X
mkdir -p "$SANDBOX/src/xray"
printf 'xray own file\n' > "$SANDBOX/src/xray/x.txt"
$G add -A src/xray >/dev/null; $G commit -q -m "P03 seat X, its own lane"
TIP_X=$($G rev-parse HEAD)
$G checkout -q -b p03-seat-y "$BASE"
seat_env P03-SEAT-Y
mkdir -p "$SANDBOX/src/yankee"
printf 'yankee own file\n' > "$SANDBOX/src/yankee/y.txt"
$G add -A src/yankee >/dev/null; $G commit -q -m "P03 seat Y, its own lane"
TIP_Y=$($G rev-parse HEAD)
$G checkout -q inc12-coordination
assert_tip_moved P03-SEAT-X "$TIP_X"
assert_tip_moved P03-SEAT-Y "$TIP_Y"
mkc P03-X P03-SEAT-X 'src/xray/**'
mkc P03-Y P03-SEAT-Y 'src/yankee/**'

run_rc "arm3 merge_reconcile over the DISJOINT pair" python3 -B "$MR" --root "$SANDBOX" \
    --base "$BASE" --claim P03-X --claim P03-Y --tip "P03-X=$TIP_X" --tip "P03-Y=$TIP_Y" --emit
A3_RC=$LAST_RC
echo "$LAST_OUT" | grep -E 'ASSERTION|intersection|RECORD EMITTED|VERDICT' | sed 's/^/      | /'

echo "    -- VERIFYING THE RESULT AND NOT THE EXIT CODE: perform the merge, then look --"
$G checkout -q -b p03-merge-ok "$TIP_X"
seat_env P03-ACCOUNTABLE
$G merge -q --no-edit p03-seat-y > /dev/null 2>&1
M2_RC=$?
echo "    git merge rc=$M2_RC"
HAVE_X=0; HAVE_Y=0
[ -f "$SANDBOX/src/xray/x.txt" ] && grep -q 'xray own file' "$SANDBOX/src/xray/x.txt" && HAVE_X=1
[ -f "$SANDBOX/src/yankee/y.txt" ] && grep -q 'yankee own file' "$SANDBOX/src/yankee/y.txt" && HAVE_Y=1
echo "    seat X's change present in the merged result = $HAVE_X"
echo "    seat Y's change present in the merged result = $HAVE_Y"
$G checkout -q inc12-coordination
EMITTED=$(ls "$SANDBOX/governance/coordination/merges/" 2>/dev/null | wc -l)
echo "    merge records emitted = $EMITTED   (ls governance/coordination/merges/ | wc -l)"
A3_OK=0
[ "$A3_RC" -eq 0 ] && [ "$HAVE_X" -eq 1 ] && [ "$HAVE_Y" -eq 1 ] && [ "$EMITTED" -ge 1 ] && A3_OK=1
arm_result 3 "NON-VACUITY ADMITS" "rc=0 AND both seats' changes present AND record emitted" "$A3_OK"

plant_summary
exit $?
