#!/bin/sh
# ================================================================================================= #
# PLANT-COORD-02 — DISJOINT SCOPE. `PO-DECISIONS-0021` ruling 3(b), increment 12 ITEM 2(a)/2(b).
#
#   ARM 1  BASELINE REFUSES — two live claims with OVERLAPPING write scopes ->
#                             `check_scope_disjoint.py` non-zero, NAMING BOTH SEATS AND THE PATH.
#   ARM 2  VIOLATED ADMITS  — `overlaps()` mutated to compare only the FIRST path segment and to
#                             fail OPEN on undecidable forms. The overlap is ADMITTED, exit 0.
#   ARM 3  NON-VACUITY      — (a) two live claims with genuinely disjoint scopes -> exit 0;
#                             (b) THE ASYMMETRIC PAIR: seat A WRITES what seat B declared it would
#                                 READ -> REFUSED. (CD-PL-F134)
# ================================================================================================= #
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$HERE/lib.sh"
plant_banner "PLANT-COORD-02"
PATCH="$HERE/PLANT-COORD-02.mutation.patch"
CL="$SANDBOX/tools/coordination/claim.py"
CK="$SANDBOX/tools/coordination/check_scope_disjoint.py"

mkclaim() { # mkclaim <task> <seat> <writescope> [readscope]
    if [ -n "$4" ]; then
        python3 -B "$CL" --root "$SANDBOX" claim --task "$1" --seat "$2" --write-scope "$3" --read-scope "$4" > /dev/null 2>&1
    else
        python3 -B "$CL" --root "$SANDBOX" claim --task "$1" --seat "$2" --write-scope "$3" > /dev/null 2>&1
    fi
    return $?
}

# The claim command itself refuses an overlapping claim (that is ITEM 1 working), so to get TWO
# OVERLAPPING LIVE CLAIMS into the registry for ARM 1 the second one is written DIRECTLY. That is
# deliberate and disclosed: it models a claim file that arrived by any route other than `claim.py`
# — a hand edit, a restored backup, a merge — which is exactly the case a STANDING check exists for.
forge_claim() { # forge_claim <task> <seat> <writescope> [readscope]
    _f="$SANDBOX/governance/coordination/claims/$1.claim.yaml"
    printf 'record_type: WORK_CLAIM\ntask_id: %s\nseat_actor_id: %s\npid: %d\nhostname: plant\nclaimed_utc: %s\nwrite_scope:\n- %s\n' \
        "$1" "$2" "$$" "$(date -u +%FT%TZ)" "$3" > "$_f"
    if [ -n "$4" ]; then printf 'read_scope:\n- %s\n' "$4" >> "$_f"; else printf 'read_scope: []\n' >> "$_f"; fi
    printf 'state: CLAIMED\n' >> "$_f"
}

# ------------------------------------------------------------------------------------------------
echo "  ARM 1 — BASELINE REFUSES (control INTACT): two live claims, OVERLAPPING write scopes"
# ------------------------------------------------------------------------------------------------
forge_claim P02-A P02-SEAT-A 'src/shared/**'
forge_claim P02-B P02-SEAT-B 'src/shared/module.py'
run_rc "arm1 check_scope_disjoint over the overlapping pair" python3 -B "$CK" --root "$SANDBOX"
A1_RC=$LAST_RC
show_out 10
NAMES_A=0; NAMES_B=0; NAMES_PATH=0
echo "$LAST_OUT" | grep -q 'P02-SEAT-A' && NAMES_A=1
echo "$LAST_OUT" | grep -q 'P02-SEAT-B' && NAMES_B=1
echo "$LAST_OUT" | grep -q 'src/shared' && NAMES_PATH=1
echo "    names seat A=$NAMES_A  seat B=$NAMES_B  overlapping path=$NAMES_PATH"
A1_OK=0
[ "$A1_RC" -ne 0 ] && [ "$NAMES_A" -eq 1 ] && [ "$NAMES_B" -eq 1 ] && [ "$NAMES_PATH" -eq 1 ] && A1_OK=1
arm_result 1 "BASELINE REFUSES" "rc!=0 and both seats and the path named" "$A1_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 2 — VIOLATED ADMITS: overlaps() compares first segment only and fails OPEN"
# ------------------------------------------------------------------------------------------------
apply_mutation "$PATCH"
if [ $? -ne 0 ]; then
    arm_result 2 "VIOLATED ADMITS" "mutation must apply" 0
else
    # With the mutation the FIRST-SEGMENT comparison makes 'src' vs 'src' look overlapping, so the
    # discriminating case is the one where the FIRST SEGMENTS DIFFER but the real overlap is deeper,
    # and the case where an UNDECIDABLE form must fail closed. Both are set up here.
    rm -f "$SANDBOX"/governance/coordination/claims/*.claim.yaml
    forge_claim P02-U P02-SEAT-U 'src/[ab]/thing.py'
    forge_claim P02-V P02-SEAT-V 'src/a/thing.py'
    run_rc "arm2 same registry, MUTATED algebra (undecidable form must fail closed; it will not)" \
        python3 -B "$CK" --root "$SANDBOX"
    A2_RC=$LAST_RC
    show_out 8
    echo "    THE UNDECIDABLE CHARACTER CLASS 'src/[ab]/thing.py' IS NOW READ AS DISJOINT FROM"
    echo "    'src/a/thing.py'. TWO SEATS ARE ADMITTED ONTO ONE FILE."
    A2_OK=0
    [ "$A2_RC" -eq 0 ] && A2_OK=1
    arm_result 2 "VIOLATED ADMITS" "rc=0 where the intact control refuses" "$A2_OK"

    echo "    -- and the SAME pair against the INTACT control, for the contrast:"
    revert_mutation "$PATCH"
    run_rc "arm2 contrast: intact control on the same registry" python3 -B "$CK" --root "$SANDBOX"
    echo "    intact rc=$LAST_RC (non-zero = fails closed on the undecidable form, as designed)"
fi

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3a — NON-VACUITY: GENUINELY DISJOINT SCOPES ARE ADMITTED"
# ------------------------------------------------------------------------------------------------
rm -f "$SANDBOX"/governance/coordination/claims/*.claim.yaml
mkclaim P02-X P02-SEAT-X 'src/xray/**'
X_RC=$?
mkclaim P02-Y P02-SEAT-Y 'docs/yankee/**'
Y_RC=$?
echo "    two concurrent disjoint claims taken through claim.py: rc=$X_RC and rc=$Y_RC"
run_rc "arm3a check_scope_disjoint over the disjoint pair" python3 -B "$CK" --root "$SANDBOX"
A3A_RC=$LAST_RC
show_out 8
A3A_OK=0
[ "$X_RC" -eq 0 ] && [ "$Y_RC" -eq 0 ] && [ "$A3A_RC" -eq 0 ] && A3A_OK=1
arm_result 3 "NON-VACUITY ADMITS (disjoint)" "both claims taken AND check rc=0" "$A3A_OK"

# ------------------------------------------------------------------------------------------------
echo ""
echo "  ARM 3b — THE ASYMMETRIC PAIR (CD-PL-F134): A WRITES WHAT B DECLARED IT WOULD READ"
# ------------------------------------------------------------------------------------------------
rm -f "$SANDBOX"/governance/coordination/claims/*.claim.yaml
forge_claim P02-R P02-SEAT-READER 'governance/scratch/**' 'governance/engineering/**'
forge_claim P02-W P02-SEAT-WRITER 'governance/engineering/ACTIVE_WORK.yaml'
run_rc "arm3b check_scope_disjoint: write-vs-READ must be REFUSED" python3 -B "$CK" --root "$SANDBOX"
A3B_RC=$LAST_RC
show_out 10
SAYS_F134=0
echo "$LAST_OUT" | grep -q 'CD-PL-F134' && SAYS_F134=1
echo "    refusal cites CD-PL-F134: $SAYS_F134"
echo "    NOTE: the WRITE/WRITE pair here is DISJOINT (governance/scratch/** vs ACTIVE_WORK.yaml)."
echo "    A SYMMETRIC-ONLY CHECK WOULD HAVE PASSED THIS CLEANLY. That is the whole point."
A3B_OK=0
[ "$A3B_RC" -ne 0 ] && [ "$SAYS_F134" -eq 1 ] && A3B_OK=1
arm_result 4 "ASYMMETRIC WRITE-vs-READ REFUSES" "rc!=0 and CD-PL-F134 cited" "$A3B_OK"

plant_summary
exit $?
