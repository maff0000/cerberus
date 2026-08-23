#!/usr/bin/env bash
# P-L — IS `CARRIER_ONLY.callable` ACTUALLY MACHINE-CHECKED, OR ONLY SAID TO BE?
#
# `governance/engineering/CD-THE-FIFTEEN-AND-THE-REDRAFT.md` §3 gives the Category B field as
#
#     `callable` | the enumerated carrier callers — tests/test_admission.py,
#                  tests/test_judgement_path_doors.py, tests/test_collector_runner.py.
#                  **MACHINE-CHECKED by `_carrier_only_violations`: callers under src/ are
#                  ENUMERATED, not claimed, and the build breaks the day somebody adds an
#                  import.**
#
# `_carrier_only_violations` matches that field against CALL EXPRESSIONS BY NAME. **A LIST OF
# FILE PATHS MATCHES NO CALL EXPRESSION.** This probe plants a REAL product caller of
# `admission_faults` inside a swept module and then asks the same instrument the same question
# twice, changing exactly one thing: what the `callable` field holds.
#
# **TWO TREES, EACH RUNNING ITS OWN COPY OF THE INSTRUMENT, EACH PRINTING ITS OWN PATH**
# (CD-PL-F98 — two arms that resolve the same tree print identical output and prove nothing).
#
# AN INSTRUMENT THAT REPORTS, NOT A CARRIER (CD-RULE-006). It exits 0 whatever it measures. The
# carrier is `tests/test_the_fifteen.py::test_a_product_caller_of_a_CARRIER_ONLY_callable_
# BREAKS_THE_BUILD` and its paired vacuity arm.
#
#     bash variants/WO-2R3/P-L-is-the-CARRIER-ONLY-callable-field-machine-checked.sh

set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$(mktemp -d /tmp/cd-P-L-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

SITE_KEY='("crash_detector.admission", "admission_faults", "DUCK", "getattr(door, FAULTS_ATTRIBUTE, ())")'

for ARM in the-callables-NAME the-documents-FILE-LIST; do
    TREE="$WORK/$ARM"
    mkdir -p "$TREE"
    cp -r "$ROOT/src" "$ROOT/tools" "$ROOT/governance" "$TREE/"

    # ONE VARIABLE HELD CONSTANT ACROSS BOTH ARMS: a real product caller, in a swept module.
    cat >> "$TREE/src/crash_detector/engine/evaluate.py" <<'PLANT'


def _planted_product_caller(door):
    """PLANTED BY P-L. A module under src/ calling a callable declared CARRIER_ONLY."""
    return admission_faults(door)
PLANT

    if [ "$ARM" = "the-callables-NAME" ]; then
        FIELD='"admission_faults"'
    else
        FIELD='"the enumerated carrier callers - tests/test_admission.py, tests/test_judgement_path_doors.py, tests/test_collector_runner.py"'
    fi

    # Rewrite `callable` on EVERY row naming admission_faults — the Category B tier-1 row and
    # its tier-2 companion. Rewriting one and leaving the other would let the other one answer.
    cat >> "$TREE/tools/sweep/declared_dispositions.py" <<PATCH


for _key, _value in list(DECLARED_ADMISSIONS.items()):
    if _value[0] == "CARRIER_ONLY" and _value[1].get("callable") == "admission_faults":
        DECLARED_ADMISSIONS[_key] = ("CARRIER_ONLY", {
            "callable": $FIELD,
            "why_it_is_not_product_judgement": "held constant across both arms",
        })
PATCH

    echo "=============================================================================="
    echo "ARM: $ARM"
    echo "  instrument: $TREE/tools/sweep/delegated_judgement_sweep.py"
    echo "  callable field: $FIELD"
    OUT="$(python3 -B "$TREE/tools/sweep/delegated_judgement_sweep.py" --root "$TREE" 2>&1)"
    CODE=$?
    echo "  exit: $CODE"
    if echo "$OUT" | grep -q CARRIER_ONLY_HAS_A_PRODUCT_CALLER; then
        echo "  >>> THE CHECK FIRED:"
        echo "$OUT" | grep CARRIER_ONLY_HAS_A_PRODUCT_CALLER | sed 's/^/      /'
    else
        echo "  >>> *** THE CHECK DID NOT FIRE. THE FIELD IS NOT BEING CHECKED. ***"
    fi
    echo "$OUT" | grep 'CD-CLASS-2-SWEEP' | sed 's/^/      /'
done
echo "=============================================================================="
echo "READ IT AS THIS: the two arms differ in NOTHING but what the \`callable\` field holds."
echo "The claim 'MACHINE-CHECKED' is true of one spelling of that field and FALSE of the other,"
echo "and the instrument reports no difference between them — it simply finds no match."
exit 0
