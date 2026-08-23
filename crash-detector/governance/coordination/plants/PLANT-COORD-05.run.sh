#!/bin/sh
# ================================================================================================= #
# PLANT-COORD-05 — **THE F08 BOTH-ARMS TEST.**
#
# *** THIS FILE IS ONE OF THE TENTH GATE'S TWO NAMED ACCEPTANCE COMMANDS ***
# (`PO-DECISIONS-0022` ruling 5: *"the F08 both-arms test and a re-run of race_scope.py are the
# tenth gate's two named acceptance commands"*).
#
# **THE SEAT THAT WROTE IT IS THE SEAT IT GRADES, AND THAT IS DISCLOSED, NOT HIDDEN.** The dispatch
# handed this test to the Engineer deliberately and told it so as a RISK. **THE TENTH ASSURANCE SEAT
# SHOULD ATTACK THIS FILE BEFORE IT TRUSTS IT.** So it is written to be attacked:
#
#   * NO skips. NO `try/except: pass`. NO arm that can quietly not run.
#   * It FAILS LOUDLY if the tree is not what it expects — the sandbox, the presence of the four
#     skip lines in the mutation's target, and the mutation's own application are all VERIFIED and
#     each one aborts the arm it belongs to rather than passing it.
#   * Every arm asserts the EXIT CODE and the VERDICT TEXT, captured with no pipe (`CD-PL-F131`).
#   * The registry is emptied before any arm runs, and that is disclosed in the banner.
#
# THE PROPOSITION UNDER TEST, IN THE PRODUCT OWNER'S OWN WORDS:
#   *"the control must FLAG two live claims on one scope regardless of identity"*.
#
#   ARM 1  BASELINE REFUSES — TWO LIVE CLAIMS, **ONE SEAT ID**, IDENTICAL WRITE SCOPE.
#                             `check_scope_disjoint.py` must exit NON-ZERO and must NAME the pair.
#                             **THIS IS THE FOUNDING INCIDENT: two Project Lead sessions on `main`,
#                             both committing as `PROJECT_LEAD_SEAT_01`, neither aware of the other
#                             (VERDICT-META-ASSURANCE-01-SECOND-SEAT §1.1). AT INCREMENT 12 THIS
#                             EXACT INPUT PRINTED `CONCURRENT WORK PROCEEDS` AND EXITED 0.**
#   ARM 1b THE ASYMMETRIC HALF — same one seat id, A.write vs B.read. Also REFUSED (CD-PL-F134
#                             does not stop applying because the two claims share a name).
#   ARM 2  VIOLATED ADMITS  — the four skip lines are RESTORED by `git apply` from a CHECKED-IN
#                             PATCH FILE, and the SAME input is ADMITTED with rc=0. **THIS IS THE
#                             ARM THAT PROVES THE FIX IS WHAT IS DOING THE WORK** and not some
#                             other property of the tree.
#   ARM 3  NON-VACUITY      — TWO DISJOINT CLAIMS UNDER THE SAME ONE SEAT ID ARE STILL ADMITTED,
#                             rc=0. **A CONTROL THAT NOW REFUSES BOTH THE OVERLAPPING AND THE
#                             DISJOINT CASE HAS NOT FIXED F08 — IT HAS BANNED CONCURRENCY**, which
#                             `PO-DECISIONS-0021` ruling 3 rejects and `PO-DECISIONS-0022` ruling 1
#                             preserves as the goal.
#   ARM 4  NON-VACUITY, THE OTHER EXEMPTION — READ x READ under one seat id is STILL ADMITTED, and
#                             so is a single claim whose own write scope overlaps its own read
#                             scope. **These are the two neighbours of the skip that had to
#                             SURVIVE.** An F08 fix that took them out with the skip would ban
#                             every parallel audit and ban a seat reading what it is about to
#                             write.
# ================================================================================================= #
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${PLANT_SCRATCH:=/tmp/cd-eng-coord-fix-01/plants}"
: "${SOURCE_ROOT:=/srv/crash-detector-inc13}"
export PLANT_SCRATCH SOURCE_ROOT
. "$HERE/lib.sh"
plant_banner "PLANT-COORD-05"
PATCH="$HERE/PLANT-COORD-05.mutation.patch"
CHECK="$SANDBOX/tools/coordination/check_scope_disjoint.py"
CLAIMS="$SANDBOX/governance/coordination/claims"

# ------------------------------------------------------------------------------------------------
# PRECONDITION — FAIL LOUDLY IF THE TREE IS NOT WHAT THIS TEST EXPECTS.
# A test that runs against the wrong tree and passes is worse than a test that does not run.
# ------------------------------------------------------------------------------------------------
echo "  PRECONDITIONS (this test REFUSES to grade a tree it cannot identify)"
if [ ! -f "$CHECK" ]; then
    echo "    *** $CHECK DOES NOT EXIST. ABORTING — NOTHING BELOW WOULD BE EVIDENCE. ***"
    exit 2
fi
SKIP_PRESENT=$(grep -c 'not a cross-seat pair, ' "$CHECK")
echo "    'not a cross-seat pair' skip lines present in the instrument under test: $SKIP_PRESENT"
echo "      produced by: grep -c 'not a cross-seat pair, ' $CHECK"
if [ "$SKIP_PRESENT" -ne 0 ]; then
    echo "    *** THE SKIP IS STILL IN THE BASELINE TREE. ARM 1 WOULD BE MEASURING THE DEFECT, NOT"
    echo "    *** THE FIX. ABORTING RATHER THAN REPORTING A PASS. ***"
    exit 2
fi
echo "    OK: the baseline instrument does not contain the skip. Arms 1/1b/3/4 grade the FIX."
echo ""

# write_claim <task> <seat> <write-scope-or-NONE> <read-scope-or-NONE>
write_claim() {
    _f="$CLAIMS/$1.claim.yaml"
    {
        echo "record_type: WORK_CLAIM"
        echo "task_id: $1"
        echo "seat_actor_id: $2"
        echo "state: CLAIMED"
        if [ "$3" = "NONE" ]; then echo "write_scope: []"; else
            echo "write_scope:"; echo "- $3"; fi
        if [ "$4" = "NONE" ]; then echo "read_scope: []"; else
            echo "read_scope:"; echo "- $4"; fi
    } > "$_f"
}

reset_claims() { rm -f "$CLAIMS"/*.claim.yaml; }

# assert_verdict <expected rc: 0|1> <expected VERDICT substring> -> sets ARM_OK
assert_verdict() {
    _want_rc="$1"; _want_txt="$2"
    ARM_OK=0
    _got_txt=$(echo "$LAST_OUT" | grep -c "$_want_txt")
    echo "    rc expected=$_want_rc actual=$LAST_RC ; lines matching '$_want_txt' = $_got_txt"
    if [ "$LAST_RC" -eq "$_want_rc" ] && [ "$_got_txt" -ge 1 ]; then ARM_OK=1; fi
}

# ------------------------------------------------------------------------------------------------
echo "  ARM 1 — BASELINE REFUSES: TWO LIVE CLAIMS, **ONE SEAT ID**, IDENTICAL WRITE SCOPE"
echo "          (this is PO-DECISIONS-0021 ruling 2's incident, in the registry's own terms)"
# ------------------------------------------------------------------------------------------------
reset_claims
write_claim PL-A PROJECT_LEAD_SEAT_01 'governance/engineering/ACTIVE_WORK.yaml' NONE
write_claim PL-B PROJECT_LEAD_SEAT_01 'governance/engineering/ACTIVE_WORK.yaml' NONE
echo "    two claim records written, both seat_actor_id=PROJECT_LEAD_SEAT_01, one write scope:"
echo "      $(ls "$CLAIMS" | tr '\n' ' ')"
run_rc "arm1 same-identity WRITE x WRITE on one scope" \
    python3 -B "$CHECK" --root "$SANDBOX"
show_out 8
assert_verdict 1 'VERDICT: REFUSED'
A1_OK=$ARM_OK
echo "    *** AND THE REFUSAL MUST NAME THE FOUNDING-INCIDENT SHAPE, NOT JUST EXIT 1: ***"
NAMED=$(echo "$LAST_OUT" | grep -c 'FOUNDING INCIDENT SHAPE')
echo "    lines naming it = $NAMED   (produced by: check_scope_disjoint.py | grep -c 'FOUNDING INCIDENT SHAPE')"
[ "$NAMED" -ge 1 ] || A1_OK=0
arm_result 1 "SAME-IDENTITY OVERLAP IS REFUSED AND NAMED" "rc=1 AND REFUSED AND named" "$A1_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 1b — THE ASYMMETRIC HALF UNDER ONE SEAT ID: A.write x B.read (CD-PL-F134)"
# ------------------------------------------------------------------------------------------------
reset_claims
write_claim PL-A PROJECT_LEAD_SEAT_01 'governance/engineering/ACTIVE_WORK.yaml' NONE
write_claim PL-B PROJECT_LEAD_SEAT_01 NONE 'governance/engineering/**'
run_rc "arm1b same-identity WRITE x READ across two distinct live claims" \
    python3 -B "$CHECK" --root "$SANDBOX"
show_out 6
assert_verdict 1 'VIOLATION WRITE/READ'
A1B_OK=$ARM_OK
arm_result 1b "SAME-IDENTITY WRITE x READ IS REFUSED" "rc=1 AND WRITE/READ violation" "$A1B_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 2 — VIOLATED ADMITS: THE FOUR SKIP LINES ARE RESTORED BY A CHECKED-IN PATCH."
echo "          THIS IS THE ARM THAT PROVES THE FIX IS WHAT IS DOING THE WORK."
# ------------------------------------------------------------------------------------------------
reset_claims
write_claim PL-A PROJECT_LEAD_SEAT_01 'governance/engineering/ACTIVE_WORK.yaml' NONE
write_claim PL-B PROJECT_LEAD_SEAT_01 'governance/engineering/ACTIVE_WORK.yaml' NONE
apply_mutation "$PATCH"
if [ $? -ne 0 ]; then
    arm_result 2 "VIOLATED ADMITS" "mutation must apply" 0
    A2_OK=0
else
    RESTORED=$(grep -c 'not a cross-seat pair, ' "$CHECK")
    echo "    skip lines now present in the mutated instrument: $RESTORED"
    echo "      produced by: grep -c 'not a cross-seat pair, ' $CHECK"
    run_rc "arm2 THE SAME INPUT, with increment 12's skip restored" \
        python3 -B "$CHECK" --root "$SANDBOX"
    show_out 8
    assert_verdict 0 'VERDICT: ADMITTED'
    A2_OK=$ARM_OK
    [ "$RESTORED" -ge 1 ] || A2_OK=0
    echo "    *** THAT IS INCREMENT 12: THE INSTRUMENT BUILT TO DETECT THE INCIDENT PRINTING"
    echo "    *** 'CONCURRENT WORK PROCEEDS' FOR THE INCIDENT, AND EXITING 0. ***"
    arm_result 2 "RESTORING THE SKIP ADMITS THE INCIDENT" "rc=0 AND ADMITTED" "$A2_OK"
    revert_mutation "$PATCH"
    STILL=$(grep -c 'not a cross-seat pair, ' "$CHECK")
    echo "    skip lines after revert: $STILL   (must be 0, or arms 3/4 below are not grading the fix)"
    if [ "$STILL" -ne 0 ]; then
        echo "    *** REVERT FAILED. ABORTING BEFORE ARMS 3 AND 4 RATHER THAN GRADING A MUTATED TREE. ***"
        exit 2
    fi
fi

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3 — NON-VACUITY: TWO **DISJOINT** CLAIMS UNDER THE SAME ONE SEAT ID ARE STILL ADMITTED."
echo "          A CONTROL THAT REFUSES THIS HAS BANNED CONCURRENCY, NOT FIXED F08."
# ------------------------------------------------------------------------------------------------
reset_claims
write_claim PL-A PROJECT_LEAD_SEAT_01 'governance/engineering/ACTIVE_WORK.yaml' NONE
write_claim PL-B PROJECT_LEAD_SEAT_01 'src/bravo/**' NONE
run_rc "arm3 same-identity, DISJOINT write scopes" \
    python3 -B "$CHECK" --root "$SANDBOX"
show_out 6
assert_verdict 0 'BOTH MAY PROCEED IN PARALLEL'
A3_OK=$ARM_OK
arm_result 3 "SAME-IDENTITY DISJOINT PAIR STILL PROCEEDS" "rc=0 AND both may proceed" "$A3_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 4 — NON-VACUITY, THE TWO EXEMPTIONS THAT HAD TO SURVIVE THE SKIP'S REMOVAL."
# ------------------------------------------------------------------------------------------------
echo "    (4a) READ x READ on ONE file, same seat id — MUST NOT REFUSE (parallel audits)"
reset_claims
write_claim PL-A PROJECT_LEAD_SEAT_01 'src/alpha/**' 'governance/**'
write_claim PL-B PROJECT_LEAD_SEAT_01 'src/bravo/**' 'governance/**'
run_rc "arm4a same-identity READ x READ on the same subtree" \
    python3 -B "$CHECK" --root "$SANDBOX"
show_out 5
assert_verdict 0 'VERDICT: ADMITTED'
A4A_OK=$ARM_OK

echo "    (4b) ONE claim whose OWN write scope overlaps its OWN read scope — MUST NOT REFUSE"
reset_claims
write_claim PL-A PROJECT_LEAD_SEAT_01 'governance/coordination/**' 'governance/**'
run_rc "arm4b a single claim reading what it is about to write" \
    python3 -B "$CHECK" --root "$SANDBOX"
show_out 5
assert_verdict 0 'VERDICT: ADMITTED'
A4B_OK=$ARM_OK

A4_OK=0
[ "$A4A_OK" = "1" ] && [ "$A4B_OK" = "1" ] && A4_OK=1
arm_result 4 "BOTH SURVIVING EXEMPTIONS STILL ADMIT" "rc=0 in 4a AND 4b" "$A4_OK"

plant_summary
exit $?
