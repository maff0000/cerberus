#!/usr/bin/env bash
# P-H — THE REACHABILITY CRITERION (ITEM 2) UNDER ITS OWN REQUIRED CONTRASTS.
#
# PO-DECISIONS-0012 ruling 2 replaced the doors membership clause with REACHABILITY. This
# increment's dispatch names two contrasts as REQUIRED, not optional:
#
#   1. THE RENAME TEST, APPLIED TO THE NEW CRITERION ITSELF. "An instrument that replaces one
#      name heuristic with a subtler name heuristic has changed the header text and not the
#      code path."
#   2. ESCAPE 4 ARM 4 MUST STILL BE CAUGHT. "IF YOUR REACHABILITY CRITERION EXEMPTS `guarded`,
#      YOU MUST DEMONSTRATE THAT IT STILL CATCHES ESCAPE 4 ARM 4 — a function-local `def` bound
#      into a module dict. THAT IS A REQUIRED CONTRAST. If it cannot be built, your criterion
#      is wrong."
#
# **EVERY ARM RUNS ITS OWN TREE'S OWN COPY OF THE INSTRUMENT** (CD-PL-F98): a contrast run with
# the wrong tree on the path is indistinguishable from a fix that does nothing, and this
# project has already been bitten by exactly that. Each arm prints the instrument it ran.
#
#   bash variants/WO-2R3/P-H-the-reachability-criterion-under-attack.sh
#
# Exits 0 whatever it measures. IT IS AN INSTRUMENT THAT REPORTS; the carriers are in tests/.

set -u

BASE_SHA=9f7b7640f692442e22a47ecac3d4a643057729d5
HERE=$(git rev-parse --show-toplevel)
WORK=$(mktemp -d /tmp/cd-P-H-XXXXXX)
trap 'rm -rf "$WORK"' EXIT

# ------------------------------------------------------------------ the two trees
# OLD = the base, carrying the NAME-PREFIX clause.
# NEW = this working tree, carrying the REACHABILITY clause.
git -C "$HERE" archive "$BASE_SHA" | tar -x -C "$WORK" --one-top-level=old
# `--cached --others --exclude-standard` AND NOT `ls-files` ALONE. **THE FIRST VERSION OF THIS
# HARNESS USED BARE `git ls-files`, WHICH LISTS ONLY TRACKED FILES, SO THE NEW AND UNCOMMITTED
# `tools/register/declared_nets.py` WAS NEVER COPIED AND EVERY "NEW" ARM EXITED 1 ON AN
# ImportError.** Four arms reported exit=1 and would have read, in a summary table, as "the new
# criterion fails everything". That is CD-ENG-WO2R3-F12 exactly — two arms exiting 1 for
# different reasons look identical — and it is recorded here rather than only fixed.
mkdir -p "$WORK/new"
git -C "$HERE" ls-files -z --cached --others --exclude-standard \
  | xargs -0 tar -c -C "$HERE" | tar -x -C "$WORK/new"

# ------------------------------------------------------------------ the mutations
rename_the_local() {   # $1 = tree.  `guarded` -> `_guarded`. TWO LINES. Nothing else.
  sed -i 's/^    def guarded($/    def _guarded(/; s/^    return guarded$/    return _guarded/' \
    "$1/src/crash_detector/engine/evaluate.py"
}

plant_escape_4_arm_4() {  # $1 = tree.  $2 = the local's name.
  # A function-local `def` BOUND INTO A MODULE DICT — the fourth Assurance seat's ESCAPE 4
  # ARM 4, demonstrated live by that seat as `POLICY["decide"]` accepting unestablished
  # arguments. Planted into a RULE 1 package so it is on a judgement path.
  cat >> "$1/src/crash_detector/engine/evaluate.py" <<PLANT


POLICY: dict = {}


def _install_policy():
    def $2(spec, usable, now_utc):
        return Unknown(reason="planted", since_utc=now_utc, missing_inputs=())

    POLICY["decide"] = $2
PLANT
}

run_arm() {  # $1 = label.  $2 = tree
  local out exit_code subjects verdict
  out=$(cd "$2" && PYTHONPATH=src python3 -B tools/register/check_judgement_path_doors.py --root . 2>&1)
  exit_code=$?
  subjects=$(printf '%s' "$out" | sed -n 's/.*SUBJECTS ENUMERATED: \([0-9]*\)\..*/\1/p' | head -1)
  verdict=$(printf '%s' "$out" | grep -o 'PASS — [0-9]* assertions, 0 violations\|FAIL — [0-9]* violation(s)' | head -1)
  printf '%-34s exit=%s  subjects=%-4s %s\n' "$1" "$exit_code" "${subjects:-?}" "$verdict"
  # PRINT THE VIOLATION'S LOCATION AND RULE TOGETHER. An earlier version printed the rule
  # alone, and reading which callable was flagged meant INFERRING it from the subject count —
  # exactly the kind of inference this project punishes. Paste, do not deduce.
  printf '%s' "$out" | grep -A1 '^VIOLATION' | grep -v '^--$' \
    | paste - - | sed 's/^/                                   /'
  printf '                                   instrument: %s\n' \
    "$(cd "$2" && sha256sum tools/register/check_judgement_path_doors.py | cut -c1-16) $2/tools/register/check_judgement_path_doors.py"
}

echo "======================================================================================"
echo " P-H — THE REACHABILITY CRITERION UNDER ITS OWN REQUIRED CONTRASTS"
echo " OLD tree = $BASE_SHA (NAME-PREFIX clause)"
echo " NEW tree = $HERE working tree (REACHABILITY clause)"
echo "======================================================================================"
echo
echo '--- CONTRAST 1: THE RENAME TEST. guarded -> _guarded, TWO LINES, NOTHING ELSE. ---'
echo "    THE OLD CLAUSE'S VERDICT MOVED ON THIS RENAME. THAT IS WHY THIS INCREMENT EXISTS."
echo
cp -a "$WORK/old" "$WORK/old-renamed"; rename_the_local "$WORK/old-renamed"
cp -a "$WORK/new" "$WORK/new-renamed"; rename_the_local "$WORK/new-renamed"
run_arm "OLD clause, guarded"      "$WORK/old"
run_arm "OLD clause, _guarded"     "$WORK/old-renamed"
run_arm "NEW clause, guarded"      "$WORK/new"
run_arm "NEW clause, _guarded"     "$WORK/new-renamed"

echo
echo "--- CONTRAST 2: ESCAPE 4 ARM 4 — a function-local def bound into a MODULE DICT. ---"
echo "    ARM (a) the local is PUBLIC-named. ARM (b) the local is PRIVATE-named."
echo "    ARM (b) IS THE ONE THAT DECIDES WHETHER THE CRITERION IS STRUCTURAL:"
echo "    a name-prefix clause CANNOT SEE IT, whatever else it does."
echo
for spelling in decide _decide; do
  cp -a "$WORK/old" "$WORK/old-e4$spelling"; plant_escape_4_arm_4 "$WORK/old-e4$spelling" "$spelling"
  cp -a "$WORK/new" "$WORK/new-e4$spelling"; plant_escape_4_arm_4 "$WORK/new-e4$spelling" "$spelling"
  run_arm "OLD clause + POLICY[$spelling]"  "$WORK/old-e4$spelling"
  run_arm "NEW clause + POLICY[$spelling]"  "$WORK/new-e4$spelling"
done

echo
echo "--- CONTRAST 3: THE NETS REGISTER, ASSERTED IN BOTH DIRECTIONS. ---"
echo "    (a) DELETE the declaration -> the found net must become UNCLASSIFIED_INTERCEPTOR."
echo "    (b) DELETE the post-condition CALL from the net's body, leaving the declaration"
echo "        alone -> NET_POST_CONDITION_NOT_CALLED. This is the arm that proves the"
echo "        declaration is DATA CHECKED AGAINST THE CODE and not a label."
echo
cp -a "$WORK/new" "$WORK/new-nodecl"
python3 - "$WORK/new-nodecl/tools/register/declared_nets.py" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
s = re.sub(r'DECLARED_NETS: "tuple\[DeclaredNet, \.\.\.\]" = \(.*?\n\)\n',
           'DECLARED_NETS: "tuple[DeclaredNet, ...]" = ()\n', s, flags=re.S)
open(p, "w").write(s)
PY
run_arm "NEW clause, declaration DELETED" "$WORK/new-nodecl"

cp -a "$WORK/new" "$WORK/new-nocall"
sed -i 's/^        refuse_a_number_without_its_inputs(spec, usable, reading)$/        pass  # THE GUARD REMOVED, THE PAPERWORK LEFT/' \
  "$WORK/new-nocall/src/crash_detector/engine/evaluate.py"
run_arm "NEW clause, guard call DELETED"  "$WORK/new-nocall"

echo
echo "======================================================================================"
echo ' Read the rule: lines, not only the exit codes: two arms exiting 1 for DIFFERENT'
echo ' reasons look identical in a summary table and prove nothing (CD-ENG-WO2R3-F12).'
echo "======================================================================================"
exit 0
