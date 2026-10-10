#!/usr/bin/env bash
# WO-3 INCREMENT 16D — the arm runner. Written and run by CD-ENG-WO3-12.
#
# Each arm gets its OWN pristine `git archive <sha> | tar -x` extraction under /tmp. THE
# WORKTREE IS NEVER MUTATED (CD-PL-F154).
#
# *** rc IS TAKEN FROM `git apply` AND IT IS CHECKED. ***
# CD-ASR-WO3-11 disclosed against itself that its first arm runner read each patch FROM THE
# EXTRACTED TREE, where the patch did not exist at the older tip; `git apply` returned 128 and
# the instrument then ran on an UNPATCHED tree, measuring NOTHING while looking like a result.
# THAT IS CD-ENG-F02's DEFECT CLASS, COMMITTED INSIDE THE AUDIT OF THE INCREMENT THAT EXISTS TO
# CLOSE IT. So: the patches are read from an ABSOLUTE path in the REPOSITORY, outside every
# extraction, and any apply rc other than 0 ABORTS THE ARM LOUDLY instead of being run past.
#
# usage:  plants/WO3-INC16D/run_arms.sh <sha> <label> [repo]
set -u
SHA="$1"
LABEL="$2"
REPO="${3:-/srv/crash-detector-wo3}"
PATCHES="$REPO/plants/WO3-INC16D"
PROBE="$PATCHES/probe_arm.py"
WORK="/tmp/eng16d/arms/$LABEL"

declare -A PATCHFILE=(
  [H1]=H1-ARM-H-DEGRADED-INPUTS-ARRAY-OF-CLOSED-OBJECTS.patch
  [H2]=H2-ARRAY-OF-OPEN-OBJECTS-CAPABLE-BY-OPENNESS.patch
  [H3]=H3-ARRAY-OF-ARRAYS-TWO-CONTAINERS-DEEPER.patch
  [H4]=H4-UNDECIDABLE-LIMB-B-ALLOF-ON-REGIME.patch
  [D1]=D1-THE-FOURTH-STAGE-REMOVED.patch
  [D2]=D2-NAIVE-AGE-GREATER-THAN-WINDOW.patch
  [D3]=D3-SLOT-READING-INSTEAD-OF-NODE-WALK.patch
  [D4]=D4-NEWEST-STAMP-GOVERNS.patch
)

rm -rf "$WORK"; mkdir -p "$WORK"

echo "############################################################################"
echo "# ARMS AT $LABEL ($SHA)   patches from $PATCHES"
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

  local inst instrc
  inst=$( cd "$dir" && PYTHONPATH=src python3 -B tools/register/check_missing_data_never_calm.py --root . 2>&1 )
  instrc=$?
  echo "    INSTRUMENT exit=$instrc :: $(printf '%s' "$inst" | tail -1)"
  printf '%s' "$inst" | grep -E 'LIMB \(b\)' | head -4 | cut -c1-200 | sed 's/^/      /'

  echo "    LIVE GATE:"
  ( cd "$dir" && python3 -B "$PROBE" 2>&1 | sed 's/^/      /' )

  echo "    FRESHNESS TESTS:"
  ( cd "$dir" && PYTHONPATH=src python3 -m pytest tests/test_envelope_freshness.py -q 2>&1 | tail -2 | sed 's/^/      /' )
}

for arm in CTRL H1 H2 H3 H4 D1 D2 D3 D4; do
  run_arm "$arm"
done
