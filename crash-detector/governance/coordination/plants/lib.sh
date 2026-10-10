#!/bin/sh
# ================================================================================================= #
# PLANT HARNESS — shared by all four increment-12 plants.
#
# THE EVIDENCE STANDARD THIS ENFORCES (`CD-ENG-WO2R3-F12`, `CD-D-079`, `CD-RULE-009`, `CD-PL-F131`):
#
#   A PLANT IS EVIDENCE WHEN IT APPLIES, CONTRASTS, AND FAILS AT THE LAYER ITS PROPOSITION NAMES —
#   never merely when it exits non-zero. Every claim that something is refused requires the
#   counterfactual arm. A refusal with no contrast is indistinguishable from a probe that never ran.
#
# AND AT THIS INCREMENT THERE IS A THIRD ARM, AND IT IS THE ONE THE PRODUCT OWNER WILL LOOK AT:
#
#   ARM 3, NON-VACUITY: with the control INTACT, THE DISJOINT ATTEMPT IS ADMITTED AND PROCEEDS IN
#   PARALLEL. A control that refuses both the overlapping and the disjoint case has not implemented
#   `PO-DECISIONS-0021` ruling 3 — it has BANNED CONCURRENCY, which the ruling explicitly rejects.
#
# `CD-PL-F131`, MECHANISED: `run_rc` runs a command with NO PIPE and captures `$?` ON THE VERY NEXT
# LINE. Reading an exit code from the end of a pipeline recorded a FAILING VACUITY ARM AS PASSING on
# this project, and then RECURRED in the Project Lead's own shell two hours later while it was
# measuring its own finding about itself. Nothing in these runners pipes a command whose rc matters.
#
# `CD-PL-F128`: the sandbox is a fresh clone under /tmp/cd-eng-coord-01/ — THIS SEAT'S SCRATCH AND NO
# OTHER SEAT'S. The real worktree is NEVER mutated by a plant.
# ================================================================================================= #

# ================================================================================================= #
# TWO DEFAULTS, OVERRIDABLE FROM THE ENVIRONMENT — added by `CD-ENG-COORD-FIX-01` at increment 13.
#
# `CD-PL-F128` requires a plant's sandbox to be THE RUNNING SEAT'S OWN SCRATCH AND NO OTHER SEAT'S,
# and increment 12 hard-coded `CD-ENG-COORD-01`'s. A second seat running these plants would have
# written into a first seat's scratch — the coordination defect, inside the coordination plants.
# `SOURCE_ROOT` was already overridable and its default still names increment 12's worktree, which
# is the correct default for the four plants that shipped with it: they measure THAT tree.
#
# **THIS IS A STRICTLY ADDITIVE CHANGE. With neither variable set, every value is exactly what
# increment 12 wrote, so PLANT-COORD-01..04 behave identically.** It is declared here rather than
# left to be discovered, because it is a write by one seat into another seat's artefact.
# ================================================================================================= #
PLANT_SCRATCH="${PLANT_SCRATCH:-/tmp/cd-eng-coord-01/plants}"

_ARMS_TOTAL=0
_ARMS_PASSED=0
LAST_RC=""
LAST_OUT=""

# run_rc <label> <command...>  -- runs, captures rc IMMEDIATELY, stores output in LAST_OUT.
run_rc() {
    _label="$1"; shift
    _outfile="$PLANT_WORK/out.$$"
    echo "    \$ $*"
    "$@" > "$_outfile" 2>&1
    LAST_RC=$?
    echo "    rc=$LAST_RC   [$_label]"
    LAST_OUT=$(cat "$_outfile")
    rm -f "$_outfile"
}

show_out() {
    echo "$LAST_OUT" | sed 's/^/      | /' | grep -vE '^\s*\| *$' | head -"${1:-14}"
}

# arm <n> <name> <expected: PASS|FAIL> <what it proves>
arm_result() {
    _n="$1"; _name="$2"; _expected_rc_class="$3"; _ok="$4"
    _ARMS_TOTAL=$((_ARMS_TOTAL + 1))
    if [ "$_ok" = "1" ]; then
        _ARMS_PASSED=$((_ARMS_PASSED + 1))
        echo "  ARM $_n  $_name : CONTRASTED AS REQUIRED ($_expected_rc_class)"
    else
        echo "  ARM $_n  $_name : *** DID NOT CONTRAST *** (expected $_expected_rc_class)"
    fi
}

plant_banner() {
    PLANT_NAME="$1"
    PLANT_WORK="$PLANT_SCRATCH/$PLANT_NAME"
    SOURCE_ROOT="${SOURCE_ROOT:-/srv/crash-detector-inc12}"
    rm -rf "$PLANT_WORK"
    mkdir -p "$PLANT_WORK"
    git clone -q --no-hardlinks "$SOURCE_ROOT" "$PLANT_WORK/tree"
    CLONE_RC=$?
    SANDBOX="$PLANT_WORK/tree"
    echo "================================================================================"
    echo "$PLANT_NAME"
    echo "================================================================================"
    echo "  source worktree : $SOURCE_ROOT"
    echo "  source HEAD     : $(git -C "$SOURCE_ROOT" rev-parse HEAD)"
    echo "    produced by: git -C $SOURCE_ROOT rev-parse HEAD"
    echo "  SANDBOX (CD-PL-F98: EVERY PROBE PRINTS THE TREE IT RAN IN)"
    echo "                  : $SANDBOX  (clone rc=$CLONE_RC)"
    echo "  sandbox HEAD    : $(git -C "$SANDBOX" rev-parse HEAD)"
    echo "  utc             : $(date -u +%FT%TZ)   [CD-RULE-005]"
    # THE SANDBOX REGISTRY IS EMPTIED BEFORE ANY ARM RUNS, AND THIS IS DISCLOSED RATHER THAN DONE
    # QUIETLY. A plant that inherits live claims from the repository measures the repository's state
    # and not its own proposition. THIS SEAT LEARNED IT THE EXPENSIVE WAY: PLANT-COORD-01 arm 3
    # first reported DID NOT CONTRAST, and the cause was two smoke-test claim records this seat had
    # committed by accident, against which the control was CORRECTLY refusing. The instrument was
    # right and the plant was wrong. The records were removed from the repository and the plants
    # now start from an empty registry so the arms measure only what they set up.
    _pre=$(ls "$SANDBOX"/governance/coordination/claims/*.claim.yaml 2>/dev/null | wc -l)
    _prel=$(ls "$SANDBOX"/governance/coordination/leases/*.lease.yaml 2>/dev/null | wc -l)
    rm -f "$SANDBOX"/governance/coordination/claims/*.claim.yaml
    rm -f "$SANDBOX"/governance/coordination/leases/*.lease.yaml
    echo "  registry reset  : cleared $_pre inherited claim record(s), $_prel inherited lease record(s)"
    echo "                    IN THE SANDBOX ONLY. The source worktree is never touched by a plant."
    echo ""
}

apply_mutation() {
    _patch="$1"
    echo "  -- APPLYING THE NAMED MUTATION: $_patch"
    git -C "$SANDBOX" apply --verbose "$_patch" 2>&1 | sed 's/^/     /'
    APPLY_RC=${PIPESTATUS:-0}
    # POSIX sh has no PIPESTATUS; re-apply-check by asking git whether it is applied in reverse.
    git -C "$SANDBOX" apply --reverse --check "$_patch"
    APPLY_RC=$?
    echo "     mutation is applied (git apply --reverse --check rc=$APPLY_RC; 0 means APPLIED)"
    if [ "$APPLY_RC" -ne 0 ]; then
        echo "     *** THE MUTATION DID NOT APPLY. ARM 2 IS NOT EVIDENCE. ***"
        return 1
    fi
    return 0
}

revert_mutation() {
    _patch="$1"
    git -C "$SANDBOX" apply --reverse "$_patch"
    REVERT_RC=$?
    echo "  -- MUTATION REVERTED (git apply --reverse rc=$REVERT_RC)"
}

plant_summary() {
    echo ""
    echo "  ARMS: $_ARMS_PASSED / $_ARMS_TOTAL contrasted as required"
    echo "    produced by: sh $0"
    if [ "$_ARMS_PASSED" -eq "$_ARMS_TOTAL" ]; then
        echo "  PLANT VERDICT: LIVE — the control refuses the overlap, the mutation admits it, and"
        echo "                 THE DISJOINT CASE PROCEEDS IN PARALLEL."
        return 0
    fi
    echo "  PLANT VERDICT: *** NOT A CONTRAST *** — one or more arms did not behave as the"
    echo "                 proposition requires. A PLANT THAT PASSES BOTH ARMS IS DEAD AND IS WORSE"
    echo "                 THAN NO PLANT. This is reported, not hidden."
    return 1
}
