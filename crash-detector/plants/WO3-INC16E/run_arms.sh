#!/usr/bin/env bash
# WO-3 INCREMENT 16E — the arm runner. Written and run by CD-ENG-WO3-13.
#
# *** WHAT THIS MEASURES: whether the NEW register row CD-RT-001-STALE-DATA-NEVER-CALM MOVES on
# a tree where the fourth refusal stage is absent or weakened. At 0e80a09 NOTHING IN THE
# REGISTER MOVED ON ANY OF D1-D4 (A312-F1). ***
#
# Each arm gets its OWN pristine `git archive <sha> | tar -x` extraction under /tmp. THE LANE
# WORKTREE IS NEVER MUTATED (CD-PL-F154).
#
# *** rc IS TAKEN FROM `git apply` AND IT IS CHECKED. ***
# CD-ASR-WO3-11 disclosed against itself that its arm runner read each patch FROM THE EXTRACTED
# TREE, where the patch did not exist at the older tip; `git apply` returned 128 and the
# instrument then ran on an UNPATCHED tree, MEASURING NOTHING WHILE LOOKING LIKE A RESULT. So:
# the patches are read from an ABSOLUTE path in the REPOSITORY, outside every extraction, and
# any apply rc other than 0 ABORTS THE ARM LOUDLY instead of being run past.
#
# *** AND THE PROBE IS THIS SEAT'S OWN AND TAKES THE TREE AS AN ARGUMENT. ***
# plants/WO3-INC16D/probe_16d.py hard-codes /srv/crash-detector-wo3/src and would measure THE
# LANE on every arm no matter which tree was named.
#
# usage:  plants/WO3-INC16E/run_arms.sh <sha> <label> [repo]
set -u
SHA="$1"
LABEL="$2"
REPO="${3:-/srv/crash-detector-wo3}"
PATCHES="$REPO/plants/WO3-INC16D"          # the D1-D4 patches, unmodified, from 16D
PROBE="$REPO/plants/WO3-INC16E/eng13_probe.py"
WORK="/tmp/eng16e/arms/$LABEL"

declare -A PATCHFILE=(
  [D1]=D1-THE-FOURTH-STAGE-REMOVED.patch
  [D2]=D2-NAIVE-AGE-GREATER-THAN-WINDOW.patch
  [D3]=D3-SLOT-READING-INSTEAD-OF-NODE-WALK.patch
  [D4]=D4-NEWEST-STAMP-GOVERNS.patch
  [H1]=H1-ARM-H-DEGRADED-INPUTS-ARRAY-OF-CLOSED-OBJECTS.patch
  [H2]=H2-ARRAY-OF-OPEN-OBJECTS-CAPABLE-BY-OPENNESS.patch
  [H3]=H3-ARRAY-OF-ARRAYS-TWO-CONTAINERS-DEEPER.patch
  [H4]=H4-UNDECIDABLE-LIMB-B-ALLOF-ON-REGIME.patch
)

rm -rf "$WORK"; mkdir -p "$WORK"

echo "############################################################################"
echo "# 16E ARMS AT $LABEL ($SHA)   patches from $PATCHES"
echo "############################################################################"

run_arm () {
  local arm="$1"
  local dir="$WORK/$arm"
  mkdir -p "$dir"
  ( cd "$REPO" && git archive "$SHA" ) | tar -x -C "$dir"

  if [ "$arm" = "CTRL" ]; then
    echo "--- ARM $arm @ $LABEL : NO PATCH (the vacuity control — an arm set with no clean arm"
    echo "                        cannot tell 'the plant did it' from 'everything is broken')"
  else
    ( cd "$dir" && git apply --unsafe-paths --directory=. "$PATCHES/${PATCHFILE[$arm]}" 2>&1 )
    local applyrc=$?          # *** RC FROM `git apply` ***
    echo "--- ARM $arm @ $LABEL : git apply rc=$applyrc"
    if [ "$applyrc" -ne 0 ]; then
      echo "    *** PATCH DID NOT APPLY. NOTHING BELOW WOULD MEASURE THIS ARM. ARM ABORTED. ***"
      return
    fi
  fi

  local newrow newrc
  newrow=$( cd "$dir" && python3 -B tools/register/check_stale_data_never_calm.py --root . 2>&1 )
  newrc=$?
  echo "    NEW ROW  CD-RT-001-STALE-DATA-NEVER-CALM  exit=$newrc :: $(printf '%s' "$newrow" | tail -1)"
  printf '%s' "$newrow" | grep -E '^    rule:' | sort | uniq -c | sed 's/^/      /'

  local sib sibrc
  sib=$( cd "$dir" && python3 -B tools/register/check_missing_data_never_calm.py --root . 2>&1 )
  sibrc=$?
  echo "    SIBLING  CD-RT-001-MISSING-DATA-NEVER-CALM exit=$sibrc :: $(printf '%s' "$sib" | tail -1)"

  local wit witrc
  wit=$( cd "$dir" && PYTHONPATH=src python3 -B -m pytest tests/test_envelope_freshness.py -q 2>&1 )
  witrc=$?
  echo "    WITNESS  tests/test_envelope_freshness.py  exit=$witrc :: $(printf '%s' "$wit" | tail -1)"

  echo "    LIVE GATE (this seat's own probe, tree passed as argv[1]):"
  ( cd "$dir" && python3 -B "$PROBE" "$dir" 2>&1 | sed 's/^/      /' )
}

for arm in CTRL D1 D2 D3 D4 H1 H2 H3 H4; do
  run_arm "$arm"
done
